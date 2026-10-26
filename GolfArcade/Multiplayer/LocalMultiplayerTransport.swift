import Foundation
import Network

@MainActor
final class LocalMultiplayerTransport: MultiplayerTransport {
    struct DiscoveredLobby: Identifiable { var id: String; var name: String; var endpoint: NWEndpoint; var sport: String = "tennis"; var players: Int = 1 }
    let localID = UUID().uuidString
    var peers: [String] { Array(connections.keys) }
    var onData: ((Data, String) -> Void)?
    var onPeersChanged: (() -> Void)?
    var onError: ((Error) -> Void)?
    var onDiscovery: (([DiscoveredLobby]) -> Void)?
    private var listener: NWListener?
    private var browser: NWBrowser?
    private var connections: [String: NWConnection] = [:]
    private var pending: [UUID: NWConnection] = [:]
    private let queue = DispatchQueue(label: "MotionClub.multiplayer.local")
    private let service = "_motionparty._tcp"
    private var advertisedHost = "Friends"
    private var advertisedMetadata = ""
    private var registered = false
    private var pendingMetadata: (String,Int)?
    private var host = false
    private var generation = 0
    private var sending: Set<String> = []
    private var outbound: [String: [Data]] = [:]
    private var latest: [String: Data] = [:]
    /// `udp`: the host's datagram port (see "Datagrams" below); an older phone sends none and everything stays on TCP.
    private struct Hello: Codable { var id: String; var version: Int; var token: String; var reason: String?; var udp: UInt16? }
    // Datagrams (P3): the 30 Hz pose and the other unreliable packets (pings, heartbeats) go over UDP, so one lost packet is just
    // lost instead of stalling everything behind it on TCP. Lobby, hit and point messages stay on TCP. The host listens on a UDP port
    // (no Bonjour service of its own) and names it in its TCP hello; the guest sends a datagram hello (its id and the lobby secret)
    // every half second, which the host answers. A peer counts as reachable by datagram only while one has arrived from it in the
    // last `datagramQuiet` seconds; otherwise unreliable packets fall back to TCP (a network that blocks UDP still plays).
    private var udpListener: NWListener?
    private var udpPort: UInt16?
    private var datagrams: [String: NWConnection] = [:]
    private var unclaimed: [ObjectIdentifier: NWConnection] = [:]
    private var datagramHeard: [String: Double] = [:]
    static let datagramLimit = 1200, datagramQuiet = 1.5
    private enum Datagram: UInt8 { case hello = 1, packet = 2 }
    /// Diagnostics and tests: unreliable packets sent and received as datagrams.
    private(set) var datagramsSent = 0, datagramsReceived = 0
    /// Set during a match (MultiplayerService): a guest whose connection to the host breaks dials the same lobby again for
    /// MultiplayerTuning.reconnectSeconds before it reports the error (which ends its match). Wi-Fi blips and roaming survive this.
    var holdForReconnect = false
    private var joined: DiscoveredLobby?
    private var reconnectUntil: Double?
    private var token = ""
    var joinCode: String { Self.joinCode(for: token) }
    static func joinCode(for token: String) -> String {
        String(token.replacingOccurrences(of: "-", with: "").prefix(6)).uppercased()
    }

    static func advertisedName(_ name: String, token: String) -> String {
        var prefix = ""
        for character in name.replacingOccurrences(of: "~", with: " ") {
            if prefix.utf8.count + String(character).utf8.count > 26 { break }
            prefix.append(character)
        }
        return (prefix.isEmpty ? "Friends" : prefix) + "~" + token
    }

    /// iOS reports "the user said no to Local Network" as a waiting state with this DNS-SD error, not as a failure.
    /// (`nonisolated`: it is a pure check, called from Network.framework's state handlers, which run on the transport's own queue.)
    nonisolated static func isLocalNetworkDenied(_ error: NWError) -> Bool {
        if case .dns(let code) = error { return code == -65570 }
        return false
    }
    private func parameters() -> NWParameters {
        let tcp = NWProtocolTCP.Options(); tcp.noDelay = true
        // A phone that vanishes without closing the connection (Wi-Fi lost, app killed) is noticed in a few seconds instead of hours.
        tcp.enableKeepalive = true; tcp.keepaliveIdle = 2; tcp.keepaliveInterval = 1; tcp.keepaliveCount = 3
        // Peer-to-peer Wi-Fi (AWDL) for the listener, the browser and every connection: two phones find and reach each other with no
        // shared Wi-Fi network (only Wi-Fi turned on).
        let p = NWParameters(tls: nil, tcp: tcp); p.includePeerToPeer = true
        return p
    }
    private func datagramParameters() -> NWParameters {
        let p = NWParameters.udp; p.includePeerToPeer = true
        p.serviceClass = .interactiveVoice   // Wi-Fi's lowest-latency queue
        return p
    }
    func host(name: String) throws {
        disconnect(); host = true; advertisedHost = name; token = UUID().uuidString
        let listener = try NWListener(using: parameters())
        advertisedMetadata = "tennis-1"
        listener.service = NWListener.Service(name: Self.advertisedName(name, token: token), type: service, txtRecord:NWTXTRecord(["sport":"tennis","players":"1","version":String(MultiplayerPacket.version)]).data)
        listener.serviceRegistrationUpdateHandler = { [weak self] change in
            Task { @MainActor in
                guard let self else { return }
                if case .add = change { self.registered = true; if let (sport,players) = self.pendingMetadata { self.pendingMetadata = nil; self.advertise(sport:sport,players:players) } }
                #if DEBUG
                OnlineLobbyProofDriver.event("advertisement",String(describing:change))
                #endif
            }
        }
        let epoch = generation
        listener.newConnectionHandler = { [weak self] c in Task { @MainActor in guard self?.generation == epoch else { c.cancel(); return }; self?.connect(c) } }
        listener.stateUpdateHandler = { [weak self] state in
            #if DEBUG
            Task { @MainActor in OnlineLobbyProofDriver.event("listener",String(describing:state)) }
            #endif
            if case .failed(let error) = state { Task { @MainActor in self?.onError?(error) } }
            if case .waiting(let error) = state, Self.isLocalNetworkDenied(error) { Task { @MainActor in self?.onError?(MultiplayerError.localNetworkDenied) } }
        }
        self.listener = listener; listener.start(queue: queue)
        listenForDatagrams(epoch: epoch)
    }
    private func listenForDatagrams(epoch: Int) {
        guard let udp = try? NWListener(using: datagramParameters()) else { return }   // (TCP carries everything then)
        udp.newConnectionHandler = { [weak self] c in Task { @MainActor in
            guard let self, self.generation == epoch, self.unclaimed.count < 8 else { c.cancel(); return }
            self.unclaimed[ObjectIdentifier(c)] = c
            c.start(queue: self.queue); self.receiveDatagram(c, epoch: epoch)
            // a flow that never says a valid hello is dropped
            Task { @MainActor [weak self] in
                try? await Task.sleep(for: .seconds(10))
                if self?.unclaimed.removeValue(forKey: ObjectIdentifier(c)) != nil { c.cancel() }
            }
        } }
        udp.stateUpdateHandler = { [weak self] state in
            guard case .ready = state else { return }
            Task { @MainActor in guard let self, self.generation == epoch else { return }; self.udpPort = udp.port?.rawValue }
        }
        udpListener = udp; udp.start(queue: queue)
    }
    func advertise(sport: String, players: Int) {
        guard host, let listener else { return }; let key = "\(sport)-\(players)"
        guard key != advertisedMetadata else { return }
        guard registered else { pendingMetadata = (sport,players); return }; advertisedMetadata = key
        listener.service = NWListener.Service(name: Self.advertisedName(advertisedHost, token: token), type: service, txtRecord: NWTXTRecord(["sport":sport,"players":String(players),"version":String(MultiplayerPacket.version)]).data)
    }
    func browse() {
        browser?.cancel()
        let b = NWBrowser(for: .bonjourWithTXTRecord(type: service, domain: nil), using: parameters())
        b.browseResultsChangedHandler = { [weak self] results, _ in
            let lobbies = results.compactMap { result -> DiscoveredLobby? in
                guard case .service(let name, _, _, _) = result.endpoint else { return nil }
                let txt: NWTXTRecord? = { if case .bonjour(let txt) = result.metadata { return txt }; return nil }()
                return DiscoveredLobby(id: name, name: name.components(separatedBy: "~").first ?? name, endpoint: result.endpoint, sport: txt?["sport"] ?? "tennis", players: max(1,min(4,Int(txt?["players"] ?? "1") ?? 1)))
            }.sorted { $0.name < $1.name }
            Task { @MainActor in self?.onDiscovery?(lobbies) }
        }
        b.stateUpdateHandler = { [weak self] state in
            #if DEBUG
            Task { @MainActor in OnlineLobbyProofDriver.event("browser",String(describing:state)) }
            #endif
            if case .failed(let e) = state { Task { @MainActor in self?.onError?(e) } }
            if case .waiting(let e) = state, Self.isLocalNetworkDenied(e) { Task { @MainActor in self?.onError?(MultiplayerError.localNetworkDenied) } } }
        browser = b; b.start(queue: queue)
    }
    func join(_ lobby: DiscoveredLobby) throws {
        guard connections.isEmpty, pending.isEmpty, listener == nil else { throw MultiplayerError.invalidOperation("Leave the current lobby first.") }
        guard let secret = lobby.id.components(separatedBy: "~").last, UUID(uuidString: secret) != nil else { throw MultiplayerError.incompatible }
        browser?.cancel(); browser = nil; host = false; token = secret; joined = lobby; reconnectUntil = nil
        connect(NWConnection(to: lobby.endpoint, using: parameters()))
    }
    private func connect(_ c: NWConnection) {
        guard pending.count + connections.count < (host ? 3 : 1) else {
            guard host else { c.cancel(); return }
            c.stateUpdateHandler = { [weak self] state in
                if case .ready = state { Task { @MainActor in
                    guard let self, let data = try? JSONEncoder().encode(Hello(id:self.localID,version:MultiplayerPacket.version,token:self.token,reason:MultiplayerError.full.localizedDescription)) else { c.cancel(); return }
                    self.write(data,connection:c) { c.cancel() }
                } }
            }; c.start(queue:queue); return
        }
        let key = UUID(), epoch = generation; pending[key] = c
        c.stateUpdateHandler = { [weak self] state in
            Task { @MainActor in
                guard let self, epoch == self.generation else { return }
                switch state {
                case .ready:
                    guard let data = try? JSONEncoder().encode(Hello(id: self.localID, version: MultiplayerPacket.version, token: self.token, udp: self.host ? self.udpPort : nil)) else { return }
                    self.write(data, connection: c) { }
                    self.readHello(c, key: key, epoch: epoch)
                case .failed(let error): self.remove(c, key: key); if !self.host { self.lost(error) }
                case .cancelled: self.remove(c, key: key); if !self.host { self.lost(MultiplayerError.unavailable("The local lobby closed the connection.")) }
                default: break
                }
            }
        }
        c.start(queue: queue)
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(10))
            guard let self, self.generation == epoch, self.pending[key] != nil else { return }
            c.cancel(); self.remove(c, key: key); self.lost(MultiplayerError.unavailable("Local lobby connection timed out. Keep both phones close together, with Wi-Fi turned on (no shared network needed)."))
        }
    }
    /// A guest lost (or could not reach) the host. Mid-match it dials again, once a second, until reconnectSeconds have passed;
    /// otherwise, or after that, the error goes up (and its match ends).
    private func lost(_ error: Error) {
        let now = ProcessInfo.processInfo.systemUptime
        guard !host, holdForReconnect, let lobby = joined, connections.isEmpty else { reconnectUntil = nil; onError?(error); return }
        let until = reconnectUntil ?? now + MultiplayerTuning.reconnectSeconds; reconnectUntil = until
        guard now < until else { reconnectUntil = nil; onError?(error); return }
        guard pending.isEmpty else { return }   // (a dial is already under way; its own failure comes back here)
        let epoch = generation
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(1))
            guard let self, self.generation == epoch, !self.host, self.connections.isEmpty, self.pending.isEmpty else { return }
            self.connect(NWConnection(to: lobby.endpoint, using: self.parameters()))
        }
    }
    private func readHello(_ c: NWConnection, key: UUID, epoch: Int) {
        read(c) { [weak self] data in
            guard let self, self.generation == epoch, let data, let hello = try? JSONDecoder().decode(Hello.self, from: data) else { c.cancel(); return }
            if let reason = hello.reason { self.onError?(MultiplayerError.unavailable(reason)); c.cancel(); return }
            guard hello.version == MultiplayerPacket.version else { self.onError?(MultiplayerError.incompatible); c.cancel(); return }
            guard hello.token == self.token, UUID(uuidString: hello.id) != nil, hello.id != self.localID else { c.cancel(); return }
            if let stale = self.connections[hello.id] {
                // The same player dialled in again (it knows the lobby's secret): its old connection is dead and this one replaces it.
                guard self.host else { c.cancel(); return }
                self.connections.removeValue(forKey: hello.id); self.outbound.removeValue(forKey: hello.id); self.latest.removeValue(forKey: hello.id); self.sending.remove(hello.id)
                self.dropDatagrams(hello.id)
                stale.cancel()
            }
            self.reconnectUntil = nil
            self.pending.removeValue(forKey: key); self.connections[hello.id] = c; self.onPeersChanged?(); self.readPacket(c, id: hello.id, epoch: epoch)
            // a guest opens its datagram flow to the host it has just reached (after every reconnect too: a fresh flow)
            if !self.host, let port = hello.udp.flatMap(NWEndpoint.Port.init(rawValue:)), case .hostPort(let address, _)? = c.currentPath?.remoteEndpoint {
                self.openDatagrams(to: address, port: port, peer: hello.id, epoch: epoch)
            }
        }
    }
    private func readPacket(_ c: NWConnection, id: String, epoch: Int) {
        read(c) { [weak self] data in
            guard let self, self.generation == epoch, self.connections[id] === c else { return }
            guard let data else { c.cancel(); return }
            self.onData?(data, id); self.readPacket(c, id: id, epoch: epoch)
        }
    }
    /// TCP has no message boundaries. Read the exact header, then a bounded body.
    private func read(_ c: NWConnection, completion: @escaping @MainActor (Data?) -> Void) {
        c.receive(minimumIncompleteLength: 4, maximumLength: 4) { data, _, complete, error in
            guard error == nil, !complete, let data, data.count == 4 else { Task { @MainActor in completion(nil) }; return }
            let n = data.reduce(0) { ($0 << 8) | Int($1) }
            guard n > 0, n <= MultiplayerPacket.maximumBytes else { c.cancel(); Task { @MainActor in completion(nil) }; return }
            c.receive(minimumIncompleteLength: n, maximumLength: n) { body, _, done, error in
                Task { @MainActor in completion(error == nil && !done && body?.count == n ? body : nil) }
            }
        }
    }
    private func write(_ data: Data, connection: NWConnection, completion: @escaping @MainActor () -> Void) {
        let n = UInt32(data.count)
        var framed = Data([UInt8((n >> 24) & 255), UInt8((n >> 16) & 255), UInt8((n >> 8) & 255), UInt8(n & 255)]); framed.append(data)
        connection.send(content: framed, completion: .contentProcessed { [weak self] error in
            Task { @MainActor in if let error { if self?.host == true { connection.cancel() } else if self?.holdForReconnect == true { connection.cancel() /* its .cancelled state re-dials */ } else { self?.onError?(error) } }; completion() }
        })
    }
    func send(_ data: Data, to ids: [String]?, reliable: Bool) throws {
        guard data.count <= MultiplayerPacket.maximumBytes else { throw MultiplayerError.invalidOperation("Network packet is too large.") }
        for id in ids ?? peers {
            guard connections[id] != nil else { continue }
            if reliable {
                guard (outbound[id]?.count ?? 0) < 64 else { throw MultiplayerError.unavailable("A local peer is not keeping up.") }
                outbound[id, default: []].append(data)
            } else if let flow = datagrams[id], datagramsUp(id), data.count <= Self.datagramLimit {
                var datagram = Data([Datagram.packet.rawValue]); datagram.append(data)
                flow.send(content: datagram, completion: .idempotent); datagramsSent += 1
                continue
            } else { latest[id] = data } // Coalesce snapshots under backpressure, never grow indefinitely.
            flush(id)
        }
    }
    private func flush(_ id: String) {
        guard !sending.contains(id), let c = connections[id] else { return }
        let data: Data?
        if !(outbound[id]?.isEmpty ?? true) { data = outbound[id]?.removeFirst() }
        else { data = latest.removeValue(forKey: id) }
        guard let data else { return }; sending.insert(id)
        let epoch = generation
        write(data, connection: c) { [weak self] in guard let self, self.generation == epoch else { return }; self.sending.remove(id); self.flush(id) }
    }
    private func remove(_ c: NWConnection, key: UUID) {
        pending.removeValue(forKey: key)
        for id in Array(connections.keys) where connections[id] === c { connections.removeValue(forKey: id); outbound.removeValue(forKey: id); latest.removeValue(forKey: id); sending.remove(id); dropDatagrams(id) }
        onPeersChanged?()
    }

    // MARK: datagrams

    private func datagramsUp(_ id: String) -> Bool {
        guard let heard = datagramHeard[id] else { return false }
        return ProcessInfo.processInfo.systemUptime - heard < Self.datagramQuiet
    }
    private func dropDatagrams(_ id: String) {
        datagrams.removeValue(forKey: id)?.cancel(); datagramHeard.removeValue(forKey: id)
    }
    private func helloDatagram() -> Data {
        var d = Data([Datagram.hello.rawValue]); d.append(Data("\(localID)|\(token)".utf8)); return d
    }
    /// Guest: the flow to the host's datagram port, and the hello every half second that keeps it open and tells both ends it works.
    private func openDatagrams(to address: NWEndpoint.Host, port: NWEndpoint.Port, peer: String, epoch: Int) {
        dropDatagrams(peer)
        let flow = NWConnection(host: address, port: port, using: datagramParameters())
        datagrams[peer] = flow
        flow.start(queue: queue); receiveDatagram(flow, epoch: epoch)
        Task { @MainActor [weak self] in
            while let self, self.generation == epoch, self.datagrams[peer] === flow {
                flow.send(content: self.helloDatagram(), completion: .idempotent)
                try? await Task.sleep(for: .milliseconds(500))
            }
        }
    }
    private func receiveDatagram(_ c: NWConnection, epoch: Int) {
        c.receiveMessage { [weak self] data, _, _, error in
            Task { @MainActor in
                guard let self, self.generation == epoch else { return }
                guard error == nil else {
                    self.unclaimed.removeValue(forKey: ObjectIdentifier(c))
                    for (id, flow) in self.datagrams where flow === c {
                        self.datagrams.removeValue(forKey: id)
                        // a guest's flow that failed (the port was briefly unreachable) is opened again while the host is still there
                        if !self.host, case .hostPort(let address, let port) = c.endpoint {
                            Task { @MainActor [weak self] in
                                try? await Task.sleep(for: .seconds(1))
                                guard let self, self.generation == epoch, self.datagrams[id] == nil, self.connections[id] != nil else { return }
                                self.openDatagrams(to: address, port: port, peer: id, epoch: epoch)
                            }
                        }
                    }
                    c.cancel(); return
                }
                if let data, data.count > 1, data.count <= MultiplayerPacket.maximumBytes + 1 { self.datagram(data, on: c) }
                self.receiveDatagram(c, epoch: epoch)
            }
        }
    }
    private func datagram(_ data: Data, on c: NWConnection) {
        let body = data.dropFirst()
        switch Datagram(rawValue: data[data.startIndex]) {
        case .hello:
            let parts = String(decoding: body, as: UTF8.self).split(separator: "|").map(String.init)
            guard parts.count == 2, parts[1] == token, connections[parts[0]] != nil, parts[0] != localID else { return }
            let id = parts[0]
            if host {
                // this flow is that guest's now (a re-dialled guest opens a new one, which replaces the old)
                unclaimed.removeValue(forKey: ObjectIdentifier(c))
                if datagrams[id] !== c { datagrams.removeValue(forKey: id)?.cancel(); datagrams[id] = c }
                c.send(content: helloDatagram(), completion: .idempotent)
            } else if datagrams[id] !== c { return }
            datagramHeard[id] = ProcessInfo.processInfo.systemUptime
        case .packet:
            guard let id = datagrams.first(where: { $0.value === c })?.key, connections[id] != nil else { return }
            datagramHeard[id] = ProcessInfo.processInfo.systemUptime; datagramsReceived += 1
            onData?(Data(body), id)
        case nil: break
        }
    }
    func disconnect() {
        generation += 1; registered = false; pendingMetadata = nil; advertisedMetadata = ""; browser?.cancel(); browser = nil; listener?.cancel(); listener = nil
        udpListener?.cancel(); udpListener = nil; udpPort = nil
        datagrams.values.forEach { $0.cancel() }; unclaimed.values.forEach { $0.cancel() }; datagrams.removeAll(); unclaimed.removeAll(); datagramHeard.removeAll()
        joined = nil; reconnectUntil = nil; holdForReconnect = false
        let all = Array(connections.values) + Array(pending.values); connections.removeAll(); pending.removeAll()
        outbound.removeAll(); latest.removeAll(); sending.removeAll(); all.forEach { $0.cancel() }; onPeersChanged?()
    }
    #if DEBUG
    /// Tests: the listener's TCP port, the lobby secret and whether a peer is reachable by datagram (a loopback lobby).
    var debugPort: UInt16? { listener?.port?.rawValue }
    var debugToken: String { token }
    var debugUDPReady: Bool { udpPort != nil }
    func debugDatagramsUp(_ id: String) -> Bool { datagramsUp(id) }
    /// Tests: the host's TCP connections break (as a Wi-Fi blip would) while its listeners stay up.
    func debugDropConnections() { connections.values.forEach { $0.cancel() } }
    #endif
}
