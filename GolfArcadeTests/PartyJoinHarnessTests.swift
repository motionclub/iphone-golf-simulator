import XCTest
@testable import GolfArcade

/// Two phones joining one party, in-process (10-27: on build 13 the joiner's own phone ended the match 1.2–1.5 s after its hello, every
/// time, whichever phone hosted). Each phone is a real MultiplayerService wired to its own real GameCenterTransport, exactly as the
/// app wires them; only the GKMatch underneath is an in-memory pair (PartyMatchLink) with seeded, shuffled timing:
/// - the other player can already be in the match when it is handed over, or arrive later, and `.connected` can come twice;
/// - packets arrive late but reliably and in order, as GKMatch's reliable mode delivers them;
/// - the joiner may still have an idle lobby of its own, and a party remembered from yesterday.
/// The joiner then runs the real attach → onPartyConnected → bind → hello → lobby path for 5 s of game time. Neither phone may hang up
/// or leave, and both lobbies must list both players, connected. Game Center's matchmaking and turn records are not in here: they need
/// two phones (work/party-join-2026-10-26/TWO_PHONE_TEST.md).
@MainActor
final class PartyJoinHarnessTests: XCTestCase {
    /// SplitMix64: a run repeats exactly from its seed.
    struct Seeded { var s: UInt64; mutating func next() -> UInt64 { s &+= 0x9E3779B97F4A7C15; var z = s; z = (z ^ (z >> 30)) &* 0xBF58476D1CE4E5B9; z = (z ^ (z >> 27)) &* 0x94D049BB133111EB; return z ^ (z >> 31) }
        mutating func unit() -> Double { Double(next() >> 11) / Double(1 << 53) }
        mutating func chance(_ p: Double) -> Bool { unit() < p } }

    /// The network: events wait for the test clock.
    @MainActor final class Net {
        var time = 0.0, order = 0
        var queue: [(at: Double, order: Int, run: () -> Void)] = []
        func at(_ t: Double, _ run: @escaping () -> Void) { order += 1; queue.append((t, order, run)) }
        func flush() {
            while let i = queue.indices.filter({ queue[$0].at <= time }).min(by: { (queue[$0].at, queue[$0].order) < (queue[$1].at, queue[$1].order) }) {
                let e = queue.remove(at: i); e.run()
            }
        }
    }
    /// One phone's end of the match.
    @MainActor final class Link: PartyMatchLink {
        let me: String; let net: Net
        weak var other: Link?
        weak var gc: GameCenterTransport?
        var present: [String] = [], expected = 1, hungUp = false, lastArrival = 0.0, delay: () -> Double = { 0.05 }
        init(_ me: String, net: Net) { self.me = me; self.net = net }
        var playerIDs: [String] { hungUp ? [] : present }
        var expectedPlayerCount: Int { hungUp ? 0 : expected }
        func send(_ data: Data, to ids: [String]?, reliable: Bool) throws {
            guard !hungUp, let other, present.contains(other.me), ids?.contains(other.me) ?? true else { return }
            lastArrival = max(lastArrival, net.time + delay())   // (reliable: in order)
            let from = me
            net.at(lastArrival) { [weak other] in guard let other, !other.hungUp, let gc = other.gc else { return }; gc.received(data, from: from, on: other) }
        }
        func finish() {}
        func hangUp() {
            guard !hungUp else { return }
            hungUp = true
            let gone = me
            net.at(net.time + 0.02) { [weak other] in
                guard let other, let gc = other.gc else { return }
                other.present.removeAll { $0 == gone }; gc.playerChanged(gone, connected: false, on: other)
            }
        }
        /// The other player shows up in this end's match (and, sometimes, Apple says so twice).
        func arrive(_ id: String, twice: Bool) {
            if !present.contains(id) { present.append(id) }
            expected = 0
            gc?.playerChanged(id, connected: true, on: self)
            if twice { gc?.playerChanged(id, connected: true, on: self) }
        }
    }
    /// An idle lobby of the joiner's own (a party of one) that it must leave for the friend's.
    final class Idle: PartyTransport {
        let localID: String; init(_ id: String) { localID = id }
        var peers: [String] { [] }
        var onData: ((Data, String) -> Void)?, onPeersChanged: (() -> Void)?, onError: ((Error) -> Void)?
        func send(_ data: Data, to peers: [String]?, reliable: Bool) throws {}
        func disconnect() {}
    }
    @MainActor final class Flags { var hostDone = false, joinerDone = false, host = false, joiner = false, notes: [String] = [] }
    struct Phone { let id: String; let gc: GameCenterTransport; let service: MultiplayerService; let clock: () -> Double }
    private var clock = 100.0
    private func phone(_ id: String, _ name: String) -> Phone {
        let gc = GameCenterTransport(); gc.localIDOverride = id
        let service = MultiplayerService(sendToRuntime: { _ in true }, pollRuntime: { nil }, clearRuntime: {}, clock: { [unowned self] in clock })
        service.debugUseGameCenter(gc); service.setIdentity(name: name)
        return Phone(id: id, gc: gc, service: service, clock: { [unowned self] in clock })
    }

    struct Outcome: CustomStringConvertible {
        var seed: UInt64, hostHungUp = false, joinerHungUp = false, hostLeaves: [String] = [], joinerLeaves: [String] = []
        var hostLists: [String] = [], joinerLists: [String] = [], attached = (host: false, joiner: false), notes: [String] = []
        var ok: Bool { !hostHungUp && !joinerHungUp && hostLeaves.isEmpty && joinerLeaves.isEmpty && attached.host && attached.joiner
            && hostLists == ["H", "J"] && joinerLists == ["H", "J"] }
        var description: String { "seed \(seed): hung up host=\(hostHungUp) joiner=\(joinerHungUp), leaves host=\(hostLeaves) joiner=\(joinerLeaves), attached=\(attached), host lists \(hostLists), joiner lists \(joinerLists) \(notes)" }
    }

    /// One join, in one ordering. `crossed`: the phone that had invited first is the joiner (both invited each other; the tie-break
    /// made the other one host), which in the app means the joiner's own lobby or search is left right before connecting.
    private func join(seed: UInt64) async -> Outcome {
        var rng = Seeded(s: seed)
        var out = Outcome(seed: seed)
        clock = 100
        let saved = GameCenterTransport.connectPollMilliseconds
        GameCenterTransport.connectPollMilliseconds = 1
        defer { GameCenterTransport.connectPollMilliseconds = saved; UserDefaults.standard.removeObject(forKey: "party.lastLeader") }
        let host = phone("H", "Ann"), joiner = phone("J", "Bea")
        defer { host.service.leave("test over"); joiner.service.leave("test over") }
        let net = Net()
        let hl = Link("H", net: net), jl = Link("J", net: net)
        hl.other = jl; jl.other = hl; hl.gc = host.gc; jl.gc = joiner.gc
        let slow = rng.chance(0.3)
        hl.delay = { [weak net] in 0.01 + 0.2 * Double((net?.order ?? 0) % 7) / 7 * (slow ? 3 : 1) }
        jl.delay = hl.delay
        // yesterday's party, and an idle lobby of the joiner's own
        if rng.chance(0.5) { UserDefaults.standard.set("Z", forKey: "party.lastLeader"); UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: "party.lastLeaderAt") }
        if rng.chance(0.5) { try? joiner.service.host(using: Idle("J")) }
        // when each side sees the other in its match (before the hand-over, or up to 1.5 s after), and whether .connected comes twice
        let hostSees = rng.chance(0.3) ? -1 : rng.unit() * 1.5, joinerSees = rng.chance(0.3) ? -1 : rng.unit() * 1.5
        let hostTwice = rng.chance(0.4), joinerTwice = rng.chance(0.4)
        let joinerStartsAt = rng.unit() * 1.0
        if hostSees < 0 { hl.present = ["J"]; hl.expected = 0 } else { net.at(hostSees) { hl.arrive("J", twice: hostTwice) } }
        if joinerSees < 0 { jl.present = ["H"]; jl.expected = 0 } else { net.at(joinerStartsAt + joinerSees) { jl.arrive("H", twice: joinerTwice) } }
        out.notes = ["hostSees \(String(format: "%.2f", hostSees))", "joinerSees \(String(format: "%.2f", joinerSees))", "joinerStarts \(String(format: "%.2f", joinerStartsAt))", "twice \(hostTwice)/\(joinerTwice)"]

        let hostLeavesBefore = host.service.debugLeaves.count
        let f = Flags()
        var joinerStarted = false
        Task { do { try await host.gc.debugAttachParty(hl, host: "H", expecting: ["J"]); f.host = true } catch { f.notes.append("host attach: \(error.localizedDescription)") }; f.hostDone = true }
        // 5 s of game time after the joiner starts, in 10 ms steps; each step lets the attach loops run
        var t = 0.0
        while t < joinerStartsAt + 5 {
            t += 0.01; net.time = t; clock = 100 + t
            if !joinerStarted, t >= joinerStartsAt {
                joinerStarted = true
                let joinerLeavesBefore = joiner.service.debugLeaves.count
                _ = joiner.gc.canAcceptParty?(false)
                out.notes.append("idle lobby left: \(joiner.service.debugLeaves.count > joinerLeavesBefore)")
                Task { do { try await joiner.gc.debugAttachParty(jl, host: "H", expecting: ["H"], guest: .init(allowed: ["H", "J"], group: 0x60000001)); f.joiner = true } catch { f.notes.append("joiner attach: \(error.localizedDescription)") }; f.joinerDone = true }
            }
            net.flush()
            host.service.update(); joiner.service.update()
            for _ in 0..<3 { await Task.yield() }
            if !(f.hostDone && (f.joinerDone || !joinerStarted)) { try? await Task.sleep(for: .milliseconds(2)) }
        }
        out.attached = (f.host, f.joiner); out.notes += f.notes
        let idleLeave = out.notes.contains("idle lobby left: true") ? 1 : 0
        out.hostHungUp = hl.hungUp; out.joinerHungUp = jl.hungUp
        out.hostLeaves = Array(host.service.debugLeaves.dropFirst(hostLeavesBefore))
        out.joinerLeaves = Array(joiner.service.debugLeaves.dropFirst(idleLeave))
        out.hostLists = host.service.lobby?.participants.filter(\.connected).map(\.id).sorted() ?? []
        out.joinerLists = joiner.service.lobby?.participants.filter(\.connected).map(\.id).sorted() ?? []
        return out
    }

    /// A few hundred orderings of one join; every one must end with both phones in one party.
    func testTheJoinerNeverDropsAJustConnectedPartyInAnyOrdering() async {
        var failures: [Outcome] = []
        for seed in UInt64(1)...UInt64(240) {
            let o = await join(seed: seed)
            if !o.ok { failures.append(o) }
        }
        XCTAssertTrue(failures.isEmpty, "\(failures.count)/240 orderings dropped or never met:\n" + failures.prefix(8).map(\.description).joined(separator: "\n"))
    }

    // MARK: what goes wrong, and the fix (10-27)

    /// Two phones, connected, through the real attach (no lobby timing): the host's and the joiner's links.
    private func connected(_ net: Net) async -> (host: Phone, joiner: Phone, hl: Link, jl: Link) {
        let host = phone("H", "Ann"), joiner = phone("J", "Bea")
        let hl = Link("H", net: net), jl = Link("J", net: net)
        hl.other = jl; jl.other = hl; hl.gc = host.gc; jl.gc = joiner.gc
        hl.present = ["J"]; hl.expected = 0; jl.present = ["H"]; jl.expected = 0
        let saved = GameCenterTransport.connectPollMilliseconds; GameCenterTransport.connectPollMilliseconds = 1
        defer { GameCenterTransport.connectPollMilliseconds = saved }
        try? await host.gc.debugAttachParty(hl, host: "H", expecting: ["J"])
        try? await joiner.gc.debugAttachParty(jl, host: "H", expecting: ["H"], guest: .init(allowed: ["H", "J"], group: 0x60000001))
        return (host, joiner, hl, jl)
    }

    func testAGroupIsStaleOnlyOnceItsPartyHasEmptied() {
        XCTAssertFalse(GameCenterTransport.groupIsStale(hadPlayers: false, connectedNow: 0), "a new party of one keeps its group")
        XCTAssertFalse(GameCenterTransport.groupIsStale(hadPlayers: true, connectedNow: 1), "a party with friends in it keeps its group")
        XCTAssertTrue(GameCenterTransport.groupIsStale(hadPlayers: true, connectedNow: 0), "everyone went: the next party gets a new one")
    }

    /// The cause (10-27): after a party dropped, the phone kept its group and its empty match, so the next invitations (both ways)
    /// met in that same group and both phones hosted. Now, once the party has emptied, a new party has a new group and the empty
    /// match is hung up. (On the 10-26 code `hostGroup()` gave back the old group and the empty match stayed: this test fails there.)
    func testAnEmptiedPartyGetsANewGroupAndItsEmptyMatchGoes() async {
        let net = Net()
        let (host, joiner, hl, jl) = await connected(net)
        defer { host.service.leave("test over"); joiner.service.leave("test over") }
        let saved = GameCenterTransport.groupKeptSeconds; GameCenterTransport.groupKeptSeconds = 0
        defer { GameCenterTransport.groupKeptSeconds = saved }
        let first = host.gc.hostGroup()
        XCTAssertEqual(host.gc.hostGroup(), first, "a party with a friend in it keeps its group")
        XCTAssertFalse(hl.hungUp)
        // the joiner's phone drops out (signal lost): the host's match is empty
        jl.hangUp(); net.time += 1; net.flush()
        XCTAssertTrue(host.gc.peers.isEmpty)
        try? await Task.sleep(for: .milliseconds(5))
        let next = host.gc.hostGroup()
        XCTAssertNotEqual(next, first, "a new party, a new group: two phones can never both host one match again")
        XCTAssertTrue(hl.hungUp, "and the empty match is hung up, so a friend is never 'added' to it")
        XCTAssertEqual(host.gc.hostGroup(), next, "and the new group stays")
    }

    /// The symptom, replayed: two phones that both bring each other in (one shared group) are both hosts. Each lobby lists the other,
    /// but neither phone takes the other's lobby, so neither is in a party with the other ("joined your party", nobody appears).
    func testTwoHostsInOneMatchNeverMakeOneParty() async {
        let net = Net()
        let a = phone("H", "Ann"), b = phone("J", "Bea")
        defer { a.service.leave("test over"); b.service.leave("test over") }
        let al = Link("H", net: net), bl = Link("J", net: net)
        al.other = bl; bl.other = al; al.gc = a.gc; bl.gc = b.gc
        al.present = ["J"]; al.expected = 0; bl.present = ["H"]; bl.expected = 0
        GameCenterTransport.connectPollMilliseconds = 1
        defer { GameCenterTransport.connectPollMilliseconds = 200 }
        try? await a.gc.debugAttachParty(al, host: "H", expecting: ["J"])
        try? await b.gc.debugAttachParty(bl, host: "J", expecting: ["H"])
        for _ in 0..<300 { net.time += 0.01; clock += 0.01; net.flush(); a.service.update(); b.service.update(); await Task.yield() }
        XCTAssertTrue(a.service.isOwner && b.service.isOwner, "both host")
        XCTAssertNotEqual(a.service.lobby?.id, b.service.lobby?.id, "two lobbies: the friends are never in one party")
    }

    /// The harness does see a drop: a joiner whose invitation does not list the host hangs the match up (the uninvited-player check).
    func testTheHarnessSeesADropWhenThereIsOne() async {
        let net = Net()
        let host = phone("H", "Ann"), joiner = phone("J", "Bea")
        defer { host.service.leave("test over"); joiner.service.leave("test over") }
        let hl = Link("H", net: net), jl = Link("J", net: net)
        hl.other = jl; jl.other = hl; hl.gc = host.gc; jl.gc = joiner.gc
        jl.present = []; jl.expected = 1; hl.present = ["J"]; hl.expected = 0
        GameCenterTransport.connectPollMilliseconds = 1
        defer { GameCenterTransport.connectPollMilliseconds = 200 }
        try? await host.gc.debugAttachParty(hl, host: "H", expecting: ["J"])
        // the joiner is in its match with the host, but its allowed list has someone else
        jl.present = ["H"]; jl.expected = 0
        try? await joiner.gc.debugAttachParty(jl, host: "H", expecting: ["H"], guest: .init(allowed: ["J", "X"], group: 0x60000001))
        XCTAssertTrue(jl.hungUp, "caught: the joiner hung up")
        XCTAssertNil(joiner.service.lobby)
    }

    // MARK: together in the Plaza, then a game that starts on both phones

    /// A phone with its Plaza: HubSession (the menu, live, no Unity) feeding what it would send Unity into `sent`.
    @MainActor final class Plaza {
        let hub = HubSession(); var sent: [[String: Any]] = []
        let session: String
        init(_ p: Phone) {
            session = "hub-" + p.id
            hub.partyService = p.service
            hub.debugLive(session: session); hub.debugMenu(); hub.debugArrived()
            hub.debugSent = { [unowned self] in sent.append($0) }
            hub.uptime = p.clock
            p.service.onJoinedParty = { [unowned hub] in hub.joinedParty(host: $0) }
        }
        /// Unity's pose (the menu sends one a second): where my hero stands.
        func pose(x: Double) { hub.receive(["type": "hubPose", "session": session, "message": "plaza|\(x)|0|0|0|0||"]) }
        /// The TV connects mid-join: the plaza boots again on it.
        func reboot() { hub.debugBoot(session: session, menu: true); hub.receive(["type": "ready", "session": session, "message": ""]) ; hub.debugArrived() }
        /// The friend in this phone's Unity, from the last hubRemote for them since `from`.
        func remote(_ id: String, since from: Int = 0) -> [String: Any]? {
            for m in sent.dropFirst(from).reversed() where m["action"] as? String == "hubRemote" {
                if let text = m["remote"] as? String, let r = (try? JSONSerialization.jsonObject(with: Data(text.utf8))) as? [String: Any], r["id"] as? String == id { return r }
            }
            return nil
        }
    }

    struct RunResult: CustomStringConvertible {
        var seed: UInt64, sport: MultiplayerSport, problems: [String] = []
        var description: String { "seed \(seed) \(sport.rawValue): \(problems.joined(separator: "; "))" }
    }

    /// One whole evening: join (seeded ordering), both heroes in both Plazas (through a reboot of the joiner's Plaza), then the leader
    /// starts `sport`, the guest taps Ready, both load (and set up, for tennis) and play one match with 2 competitors. `reform`: the
    /// party first drops (the joiner's signal goes) and is formed again in a new match.
    private func evening(seed: UInt64, sport: MultiplayerSport, reform: Bool = false) async -> RunResult {
        var rng = Seeded(s: seed)
        var r = RunResult(seed: seed, sport: sport)
        clock = 100
        GameCenterTransport.connectPollMilliseconds = 1
        defer { GameCenterTransport.connectPollMilliseconds = 200 }
        let host = phone("H", "Ann"), joiner = phone("J", "Bea")
        // (online tennis is played on a TV on each phone; golf and bowling need none)
        host.service.setScreen(true); joiner.service.setScreen(sport == .tennis || rng.chance(0.5))
        var configs: [String: [MultiplayerMatchConfiguration]] = ["H": [], "J": []]
        host.service.onMatchRequested = { configs["H", default: []].append($0) }; joiner.service.onMatchRequested = { configs["J", default: []].append($0) }
        host.service.onReturnToLobby = {}; joiner.service.onReturnToLobby = {}
        let hp = Plaza(host), jp = Plaza(joiner)
        defer { host.service.leave("test over"); joiner.service.leave("test over"); hp.hub.debugReset(); jp.hub.debugReset() }
        let net = Net()
        var t = 0.0
        func step(_ seconds: Double, poses: Bool = true) async {
            let end = t + seconds
            while t < end {
                t += 0.01; net.time = t; clock = 100 + t
                net.flush(); host.service.update(); joiner.service.update()
                hp.hub.debugPartyTick(); jp.hub.debugPartyTick()
                if poses, Int((t * 100).rounded()) % 50 == 0 { hp.pose(x: 0); jp.pose(x: 3) }
                await Task.yield()
                if Int((t * 100).rounded()) % 10 == 0 { try? await Task.sleep(for: .milliseconds(1)) }
            }
        }
        func connect(_ hl: Link, _ jl: Link) async -> Bool {
            hl.other = jl; jl.other = hl; hl.gc = host.gc; jl.gc = joiner.gc
            let f = Flags()
            let hostSees = rng.unit() * 1.0, joinerSees = rng.unit() * 1.0, twice = rng.chance(0.4)
            net.at(t + hostSees) { hl.arrive("J", twice: twice) }; net.at(t + joinerSees) { jl.arrive("H", twice: !twice) }
            Task { do { try await host.gc.debugAttachParty(hl, host: "H", expecting: ["J"]); f.host = true } catch { f.notes.append("host attach: \(error.localizedDescription)") }; f.hostDone = true }
            _ = joiner.gc.canAcceptParty?(false)
            Task { do { try await joiner.gc.debugAttachParty(jl, host: "H", expecting: ["H"], guest: .init(allowed: ["H", "J"], group: 0x60000001)); f.joiner = true } catch { f.notes.append("joiner attach: \(error.localizedDescription)") }; f.joinerDone = true }
            var waited = 0.0
            while !(f.hostDone && f.joinerDone), waited < 3 { await step(0.05); waited += 0.05 }
            if !(f.host && f.joiner) { r.problems.append("never connected \(f.notes)") }
            return f.host && f.joiner
        }
        var hl = Link("H", net: net), jl = Link("J", net: net)
        guard await connect(hl, jl) else { return r }
        await step(3)
        if reform {
            // the joiner's signal goes: the party drops on both phones, then they meet again in a new match
            jl.hangUp(); await step(2)
            hl = Link("H", net: net); jl = Link("J", net: net)
            guard await connect(hl, jl) else { r.problems.append("never re-formed"); return r }
            await step(3)
            func info(_ svc: MultiplayerService, _ hub: HubSession) -> String {
                "lobby \(svc.lobby?.id.prefix(4) ?? "nil") owner \(svc.lobby?.ownerID ?? "-") rev \(svc.lobby?.revision ?? -1) phase \(svc.lobby?.phase.rawValue ?? "-") parts \(svc.lobby?.participants.map { "\($0.id):\($0.connected)" } ?? []) isParty \(svc.isParty) peers \(svc.partyMembers.map(\.id)) hubParty \(hub.party != nil) leaves \(svc.debugLeaves)"
            }
            r.problems.append("[re-formed: host \(info(host.service, hp.hub)) | joiner \(info(joiner.service, jp.hub))]")
        }
        // 1. together: each Plaza has the other's hero, in their look and name, beside them
        func checkPlaza(_ when: String, since h: Int = 0, _ j: Int = 0) {
            for (plaza, other, name) in [(hp, "J", "Bea"), (jp, "H", "Ann")] {
                guard let remote = plaza.remote(other, since: plaza === hp ? h : j) else { r.problems.append("\(when): \(plaza.session) has no hero for \(other)"); continue }
                if remote["name"] as? String != name { r.problems.append("\(when): \(other)'s hero has name \(remote["name"] ?? "nil")") }
                if remote["place"] as? String != "plaza" { r.problems.append("\(when): \(other)'s hero not in the plaza") }
            }
            for (svc, label) in [(host.service, "host"), (joiner.service, "joiner")] {
                let ids = svc.lobby?.participants.filter(\.connected).map(\.id).sorted() ?? []
                if ids != ["H", "J"] { r.problems.append("\(when): \(label)'s lobby lists \(ids)") }
            }
        }
        checkPlaza("after join")
        // the TV connects mid-party: the joiner's Plaza boots again and the friend must come back
        let hMark = hp.sent.count, jMark = jp.sent.count
        jp.reboot(); await step(3)
        checkPlaza("after the plaza rebooted", since: hMark, jMark)
        if !host.service.debugLeaves.isEmpty || !joiner.service.debugLeaves.filter({ $0 != "test over" }).isEmpty && !reform {
            r.problems.append("left: host \(host.service.debugLeaves) joiner \(joiner.service.debugLeaves)")
        }
        // 2. a game: the leader starts it, the guest taps Ready, both load and play
        do { try host.service.configure(sport); try host.service.startPartyGame() } catch { r.problems.append("start: \(error.localizedDescription)"); return r }
        await step(1)
        guard joiner.service.partyReadyCheck else { r.problems.append("the guest never got the ready check"); return r }
        do { try joiner.service.setReady(true) } catch { r.problems.append("ready: \(error.localizedDescription)"); return r }
        await step(1)
        guard configs["H"]?.count == 1, configs["J"]?.count == 1 else { r.problems.append("launch configs host \(configs["H"]?.count ?? 0) guest \(configs["J"]?.count ?? 0)"); return r }
        if configs["H"]?.first?.matchID != configs["J"]?.first?.matchID { r.problems.append("different matches") }
        host.service.runtimeLoaded(); await step(rng.unit()); joiner.service.runtimeLoaded()
        await step(1)
        if sport == .tennis { host.service.runtimeCalibrated(); joiner.service.runtimeCalibrated() }
        await step(8, poses: false)
        for (svc, label) in [(host.service, "host"), (joiner.service, "guest")] {
            guard let lobby = svc.lobby else { r.problems.append("\(label) has no lobby"); continue }
            if lobby.phase != .playing { r.problems.append("\(label) phase \(lobby.phase.rawValue)") }
            if lobby.competitors.count != 2 { r.problems.append("\(label) competitors \(lobby.competitors.map(\.id))") }
        }
        if hl.hungUp || jl.hungUp { r.problems.append("a phone hung up (host \(hl.hungUp) joiner \(jl.hungUp))") }
        return r
    }

    func testTogetherInThePlazaThenAGameStartsOnBothPhones() async {
        var failures: [RunResult] = []
        var seed: UInt64 = 1000
        for sport in [MultiplayerSport.golf, .tennis, .bowling] {
            for _ in 0..<20 { seed += 1; let r = await evening(seed: seed, sport: sport); if !r.problems.isEmpty { failures.append(r) } }
            seed += 1; let r = await evening(seed: seed, sport: sport, reform: true); if r.problems.contains(where: { !$0.hasPrefix("[re-formed") }) { failures.append(r) }
        }
        XCTAssertTrue(failures.isEmpty, "\(failures.count)/63 evenings went wrong:\n" + failures.prefix(10).map(\.description).joined(separator: "\n"))
    }

    /// Tennis needs a TV on each phone: a leader who starts it with a friend who has none is told why at once (it used to start a ready
    /// check that never ended). Fails on the 10-26 code: startPartyGame did not throw.
    func testTennisWithoutATVIsRefusedInWordsNotAnEndlessReadyCheck() async {
        let net = Net()
        let (host, joiner, _, _) = await connected(net)
        defer { host.service.leave("test over"); joiner.service.leave("test over") }
        host.service.setScreen(true); joiner.service.setScreen(false)
        for _ in 0..<300 { net.time += 0.01; clock += 0.01; net.flush(); host.service.update(); joiner.service.update(); await Task.yield() }
        XCTAssertEqual(host.service.lobby?.participants.count, 2)
        try? host.service.configure(.tennis)
        XCTAssertThrowsError(try host.service.startPartyGame()) { XCTAssertTrue($0.localizedDescription.contains("must connect a TV"), $0.localizedDescription) }
        XCTAssertFalse(host.service.partyReadyCheck)
        try? host.service.configure(.golf)
        XCTAssertNoThrow(try host.service.startPartyGame(), "golf needs no TV")
    }

    /// The party drops (the joiner's signal goes) and is formed again in a new match: Plaza and game as on a first join.
    func testADroppedPartyReformsWholly() async {
        let r = await evening(seed: 1021, sport: .golf, reform: true)
        XCTAssertTrue(r.problems.allSatisfy { $0.hasPrefix("[re-formed") }, r.description)
        print("REFORM-STATE", r.description)
    }
}
