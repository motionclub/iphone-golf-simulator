import XCTest
import SwiftUI
import Network
@testable import GolfArcade

@MainActor
final class MultiplayerTests: XCTestCase {
    @MainActor final class Bus {
        var links: [String: Link] = [:]
        /// Messages on a link with delay, waiting for the test clock to reach their arrival time.
        var inFlight: [(at: Double, deliver: () -> Void)] = []
        var time = 0.0
        func link(_ id: String) -> Link { let result = Link(id: id, bus: self); links[id] = result; return result }
        /// Moves the bus clock to `now` and delivers, in order, every message that has arrived by then.
        func flush(to now: Double) {
            time = now
            let due = inFlight.filter { $0.at <= now + 1e-9 }.sorted { $0.at < $1.at }
            inFlight.removeAll { $0.at <= now + 1e-9 }
            for item in due { item.deliver() }
        }
    }
    final class Link: MultiplayerTransport {
        let localID: String
        unowned let bus: Bus
        var onData: ((Data, String) -> Void)?
        var onPeersChanged: (() -> Void)?
        var onError: ((Error) -> Void)?
        var connected = true
        /// A link that is still "connected" but delivers nothing: the player has gone quiet without the transport noticing.
        var drop = false
        var dropKinds: Set<String> = []
        /// Refuses unreliable messages bigger than this, as Apple's GameKit might.
        var refuseUnreliableOver: Int?
        var refused = 0
        /// Seconds a message takes to arrive (0 = at once). Delayed messages wait on the bus until `Bus.flush` reaches them.
        var oneWayDelay = 0.0
        /// Share of unreliable messages that never arrive (0...1), drawn from a fixed seed so a test repeats exactly.
        var lossRate = 0.0
        private var seed: UInt64 = 20261010
        private func chance() -> Double { seed = seed &* 6364136223846793005 &+ 1442695040888963407; return Double(seed >> 11) / Double(1 << 53) }
        var peers: [String] { connected ? bus.links.keys.filter { $0 != localID }.sorted() : [] }
        var sent: [MultiplayerPacket] = []
        /// How each accepted message was actually sent (the packet's own `reliable` field is only advice).
        var transportModes: [(kind: String, reliable: Bool)] = []
        init(id: String, bus: Bus) { localID = id; self.bus = bus }
        func send(_ data: Data, to ids: [String]?, reliable: Bool) throws {
            if !reliable, let limit = refuseUnreliableOver, data.count > limit { refused += 1; throw MultiplayerError.unavailable("too big to send unreliably") }
            if let packet = try? JSONDecoder().decode(MultiplayerPacket.self, from: data) { sent.append(packet); transportModes.append((kind: packet.kind, reliable: reliable)) }
            if drop || (try? JSONDecoder().decode(MultiplayerPacket.self, from: data)).map({ dropKinds.contains($0.kind) }) == true { return }
            if lossRate > 0, !reliable, chance() < lossRate { return }   // reliable messages are resent by the real transport
            for id in ids ?? peers {
                if oneWayDelay > 0 { let from = localID, network = bus; bus.inFlight.append((at: bus.time + oneWayDelay, deliver: { [weak network] in network?.links[id]?.onData?(data, from) })) }
                else { bus.links[id]?.onData?(data, localID) }
            }
        }
        func disconnect() { bus.links.removeValue(forKey: localID); for link in bus.links.values { link.onPeersChanged?() } }
    }
    @MainActor final class Runtime {
        var received: [MultiplayerPacket] = []
        var outgoing: [String] = []
        var configurations: [MultiplayerMatchConfiguration] = []
        var time: Double = 100
        func service() -> MultiplayerService {
            let s = MultiplayerService(sendToRuntime: { [self] text in
                if let p = try? JSONDecoder().decode(MultiplayerPacket.self, from: Data(text.utf8)) { received.append(p) }; return true
            }, pollRuntime: { [self] in outgoing.isEmpty ? nil : outgoing.removeFirst() }, clock: { [self] in time })
            s.onMatchRequested = { [self] in configurations.append($0) }; s.onReturnToLobby = {}
            return s
        }
    }
    @MainActor struct Party {
        let bus: Bus; let services: [MultiplayerService]; let runtimes: [Runtime]
        var host: MultiplayerService { services[0] }
        func close() { for s in services.reversed() { s.leave() } }
    }
    /// `screens[n]` says whether phone n has a TV connected; by default every phone does, as in a two-TV match.
    /// `linkCheck`: the owner waits for every guest's connection to be steady before a tennis match starts (off by default, so the many
    /// tests that are about something else do not have to run the clock).
    func party(_ count: Int = 4, screens: [Bool]? = nil, linkCheck: Bool = false, sharedScreen: Bool = true) throws -> Party {
        let bus = Bus(), runtime = Runtime(), host = runtime.service()
        host.requiresStableLink = linkCheck
        host.setScreen(screens?[0] ?? true)
        try host.host(using: bus.link("a"))
        try host.setSharedScreen(sharedScreen)
        var services = [host], runtimes = [runtime]
        for n in 1..<count { let r = Runtime(), s = r.service(); s.requiresStableLink = linkCheck; s.setScreen(screens?[n] ?? true); try s.connect(using: bus.link(String(UnicodeScalar(97+n)!))); services.append(s); runtimes.append(r) }
        return Party(bus: bus, services: services, runtimes: runtimes)
    }
    func start(_ p: Party, _ sport: MultiplayerSport = .tennis) throws {
        try p.host.configure(sport)
        for s in p.services where s.localSeat >= 0 { try s.setReady(true) }
        try p.host.startMatch()
        for s in p.services where s.localSeat >= 0 { s.runtimeLoaded() }
        // Tennis players then point their phone at the TV and tap Ready; play starts when all have.
        if sport == .tennis { for s in p.services where s.localSeat >= 0 { s.runtimeCalibrated() } }
    }
    /// Disconnects the guest "b" and brings it back, as the transport would when a phone drops and returns.
    func dropAndReturn(_ p: Party, _ id: String = "b") {
        let link = p.bus.links.removeValue(forKey: id)!; link.connected = false
        p.bus.links["a"]!.onPeersChanged?(); link.onPeersChanged?()
        link.connected = true; p.bus.links[id] = link
        p.bus.links["a"]!.onPeersChanged?(); link.onPeersChanged?()
    }
    func packet(_ service: MultiplayerService, kind: String, sender: String, sequence: Int64 = 10000, payload: String = "") throws -> Data {
        try JSONEncoder().encode(MultiplayerPacket(lobbyID: service.lobby!.id, matchID: service.lobby!.matchID, sender: sender, sequence: sequence, kind: kind, payload: payload))
    }
    func testSharedPhoneGuestsLoadWithHostAndKeepIndependentLooks() throws {
        let bus=Bus(); let phone=bus.link("host"); let host=MultiplayerService(sendToRuntime:{_ in true},pollRuntime:{nil})
        host.onMatchRequested={ _ in }; defer { host.leave() }
        try host.host(using:phone,sharedPhone:true);try host.configure(.golf,venue:"cliffside")
        try host.addLocalGuest();try host.addLocalGuest();try host.addLocalGuest()
        XCTAssertEqual(host.lobby?.participants.count,4);XCTAssertTrue(host.lobby!.valid())
        let guests=host.lobby!.participants.filter(\.isGuest)
        XCTAssertEqual(Set(guests.compactMap{$0.loadout?.colours["shirt"]}).count,3)
        XCTAssertTrue(guests.allSatisfy{$0.controllerID==host.localID && $0.loadout?.valid()==true})
        XCTAssertThrowsError(try host.addLocalGuest());try host.setReady(true);try host.startMatch();host.runtimeLoaded()
        XCTAssertEqual(host.lobby?.phase,.playing);XCTAssertTrue(host.lobby!.competitors.allSatisfy(\.loaded))
    }
    /// Pass the phone needs no network: a lobby only this phone is in (no listener, so no Local Network prompt, and nobody can
    /// join), its guests ready, straight into loading, and no "keep waiting or leave" choice however long this one phone takes.
    func testPassThePhoneIsALobbyOfOnePhoneWithNoNetwork() throws {
        var now=100.0
        let host=MultiplayerService(sendToRuntime:{_ in true},pollRuntime:{nil},clock:{now})
        host.onMatchRequested={ _ in }; defer { host.leave() }
        try host.host(using:SharedPhoneTransport(),sharedPhone:true);try host.configure(.golf)
        try host.addLocalGuest();try host.addLocalGuest()
        XCTAssertTrue(host.isNearby,"guests can be added on the shared phone")
        XCTAssertEqual(host.lobby?.participants.count,3);XCTAssertEqual(host.lobby?.venue,"cliffside")
        try host.setReady(true);try host.startMatch()
        XCTAssertEqual(host.lobby?.phase,.loading)
        now+=60;host.update()
        XCTAssertFalse(host.loadingNeedsDecision,"one phone has nobody to wait for")
    }
    func testSharedGuestsAndSeparatePhoneKeepTheirOwnSeatsAndLooks() throws {
        let bus=Bus(), runtime=Runtime(), remoteRuntime=Runtime()
        let host=runtime.service(), remote=remoteRuntime.service()
        defer { remote.leave();host.leave() }
        try host.host(using:bus.link("host"),sharedPhone:true);try host.configure(.golf,venue:"cliffside")
        try host.addLocalGuest();try host.addLocalGuest()
        let look=MultiplayerLoadout(skinHex:"A8704E",colours:["shirt":"78C5E8"],emotes:EmoteCatalog.defaults,shirtHex:"78C5E8")
        remote.setIdentity(name:"Sam",female:true,loadout:look)
        try remote.connect(using:bus.link("remote"))
        XCTAssertEqual(remote.localSeat,3);XCTAssertEqual(host.lobby,remote.lobby)
        XCTAssertEqual(host.lobby?.participants.first{$0.id=="remote"}?.loadout,look)
        XCTAssertTrue(host.lobby!.participants.allSatisfy(\.connected))
        try host.setReady(true);XCTAssertFalse(host.lobby!.canStart)
        try remote.setReady(true);try host.startMatch();host.runtimeLoaded()
        XCTAssertEqual(host.lobby?.phase,.loading)
        remote.runtimeLoaded();XCTAssertEqual(host.lobby?.phase,.playing)
        XCTAssertTrue(remoteRuntime.configurations.last!.usesHostGolfDisplay)
        XCTAssertFalse(runtime.configurations.last!.usesHostGolfDisplay)
        XCTAssertTrue(host.lobby!.competitors.allSatisfy(\.loaded))
    }
    func testGolfPartyPhoneScreens() async throws {
        let session=SportsSession.shared
        let before=session.golfController;let oldPhase=session.golfPhase;let oldReady=session.ready;let oldPaused=session.paused
        defer { session.golfController=before;session.golfPhase=oldPhase;session.ready=oldReady;session.paused=oldPaused }
        let players=(0..<4).map { GolfControllerReading.PartyPlayer(seat:$0,name:$0==0 ? "Adnan" : "Guest \($0)",controlled:true,canEmote:true,emotes:EmoteCatalog.defaults) }
        var reading=GolfControllerReading.reference
        reading.party = .init(turn:0,shotID:1,player:"Adnan",outcome:"FAIRWAY",phase:"result",myTurn:true,shared:true,putt:false,resultSeconds:2,carry:176,roll:22,apex:28,total:198,players:players)
        session.golfController=reading;session.golfPhase="Result";session.ready=true;session.paused=false
        session.loading.begin(now:.now);session.loading.markReady();session.loading.skip()
        let scene=try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap{$0 as? UIWindowScene}.first)
        let window=UIWindow(windowScene:scene);window.frame=CGRect(x:0,y:0,width:402,height:874)
        let host=UIHostingController(rootView:GolfPhoneController(session:session));host.safeAreaRegions=[]
        window.rootViewController=host;window.isHidden=false;host.view.frame=window.bounds
        defer { window.isHidden=true }
        try await Task.sleep(for:.milliseconds(500));host.view.layoutIfNeeded()
        let out=URL(fileURLWithPath:#filePath).deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("work/golf-party/native-proof")
        try FileManager.default.createDirectory(at:out,withIntermediateDirectories:true)
        let format=UIGraphicsImageRendererFormat();format.scale=2
        let image=UIGraphicsImageRenderer(size:window.bounds.size,format:format).image { _ in host.view.drawHierarchy(in:window.bounds,afterScreenUpdates:true) }
        try XCTUnwrap(image.pngData()).write(to:out.appendingPathComponent("phone-result.png"))
        XCTAssertEqual(session.golfController.party?.players.filter(\.controlled).count,4)
    }
    func testNearbyCodeAndForgedGuestOwnership() {
        XCTAssertEqual(LocalMultiplayerTransport.joinCode(for:"abc12345-6789-1234-5678-123456789012"),"ABC123")
        let host=MultiplayerParticipant(id:"host",name:"Host",seat:0)
        let guest=MultiplayerParticipant(id:"guest",name:"Guest",seat:1,controllerID:"intruder")
        XCTAssertFalse(MultiplayerLobby(ownerID:"host",sport:.golf,participants:[host,guest]).valid())
    }
    func testFourPersonPartyAgreesOnOwnerSeatsAndWatchers() throws {
        let p = try party(); defer { p.close() }
        XCTAssertEqual(p.host.localSeat, 0)
        for s in p.services { XCTAssertEqual(s.lobby, p.host.lobby); XCTAssertEqual(s.lobby?.participants.count, 4); XCTAssertEqual(s.lobby?.competitors.count, 2) }
        XCTAssertEqual(p.services[2].localSeat, -1); XCTAssertEqual(p.services[3].localSeat, -1)
    }
    func testGolfConfigurationSeatsAllFourAndClearsReady() throws {
        let p = try party(); defer { p.close() }; try p.host.setReady(true); try p.host.configure(.golf)
        XCTAssertFalse(p.host.lobby!.canStart); XCTAssertEqual(p.services.map(\.localSeat), [0,1,2,3]); XCTAssertTrue(p.host.lobby!.participants.allSatisfy { !$0.ready })
    }
    func testStartRequiresReadyCompetitorsAndOwner() throws {
        let p = try party(); defer { p.close() }; XCTAssertThrowsError(try p.host.startMatch()); XCTAssertThrowsError(try p.services[1].configure(.golf))
        try p.host.setReady(true); XCTAssertThrowsError(try p.host.startMatch())
    }
    func testObserversDoNotBlockLoadingAndEveryPhoneGetsOwnConfiguration() throws {
        let p = try party(); defer { p.close() }; try start(p)
        for (i,s) in p.services.enumerated() { XCTAssertEqual(s.lobby?.phase, .playing); XCTAssertEqual(p.runtimes[i].configurations.last?.localID,s.localID); XCTAssertEqual(p.runtimes[i].configurations.last?.matchID,p.host.lobby?.matchID) }
        XCTAssertTrue(p.runtimes[0].received.contains { $0.kind == "run" })
    }
    func testObserverInputAndForgedSenderCannotControlHost() throws {
        let p = try party(); defer { p.close() }; try start(p)
        let before = p.runtimes[0].received.count
        try p.bus.links["c"]!.send(packet(p.host,kind:"input",sender:"b"),to:["a"],reliable:true)
        XCTAssertEqual(before,p.runtimes[0].received.count)
        try p.bus.links["b"]!.send(packet(p.host,kind:"input",sender:"c"),to:["a"],reliable:true)
        XCTAssertEqual(p.runtimes[0].received.last?.sender,"b")
    }
    func testStaleMatchAndDuplicateSequenceAreRejected() throws {
        let p = try party(2); defer { p.close() }; try start(p)
        var stale = MultiplayerPacket(lobbyID:p.host.lobby!.id,matchID:"old",sender:"b",sequence:10000,kind:"input")
        let before=p.runtimes[0].received.count
        try p.bus.links["b"]!.send(JSONEncoder().encode(stale),to:["a"],reliable:true); XCTAssertEqual(before,p.runtimes[0].received.count)
        stale.matchID=p.host.lobby!.matchID; stale.sequence+=1
        let data=try JSONEncoder().encode(stale); try p.bus.links["b"]!.send(data,to:["a"],reliable:true); try p.bus.links["b"]!.send(data,to:["a"],reliable:true)
        XCTAssertEqual(before+1,p.runtimes[0].received.count)
    }
    func testReturnAndSportSwitchPreservePartyButCreateFreshContest() throws {
        let p=try party(); defer { p.close() }; try start(p)
        let partyID=p.host.lobby!.id, match=p.host.lobby!.matchID
        try p.host.returnToLobby(); XCTAssertEqual(p.host.lobby?.id,partyID); XCTAssertEqual(p.host.lobby?.phase,.lobby)
        try start(p,.golf); XCTAssertNotEqual(p.host.lobby?.matchID,match); XCTAssertEqual(p.host.lobby?.participants.count,4); XCTAssertEqual(p.host.lobby?.competitors.count,4)
    }
    func testFifthPersonIsNotAdmitted() throws {
        let p=try party(); defer { p.close() }; let r=Runtime(), fifth=r.service(); defer { fifth.leave() }
        try fifth.connect(using:p.bus.link("e")); XCTAssertEqual(p.host.lobby?.participants.count,4); XCTAssertNotNil(p.host.lastError); XCTAssertNil(fifth.lobby)
    }
    func testLateViewerGetsLaunchAndLoadedRequestsCheckpoint() throws {
        let p=try party(2); defer { p.close() }; try start(p)
        let r=Runtime(), viewer=r.service(); defer { viewer.leave() }; try viewer.connect(using:p.bus.link("c"))
        XCTAssertEqual(viewer.localSeat,-1); XCTAssertEqual(r.configurations.count,1)
        viewer.runtimeLoaded(); XCTAssertTrue(r.received.contains { $0.kind=="run" }); XCTAssertTrue(p.runtimes[0].received.contains { $0.kind=="snapshotRequest" })
    }
    func testSpectatorLeavingDoesNotSuspendPlay() throws {
        let p=try party(); defer { p.close() }; try start(p); p.services[2].leave()
        XCTAssertEqual(p.host.lobby?.phase,.playing); XCTAssertFalse(p.runtimes[0].received.contains { $0.kind=="suspend"||$0.kind=="drop" })
    }
    func testCompetitorRecoveryAndExpiry() throws {
        let p=try party(2); defer { p.close() }; try start(p)
        try p.bus.links["b"]!.send(packet(p.host,kind:"availability",sender:"b",payload:"false"),to:["a"],reliable:true)
        XCTAssertEqual(p.runtimes[0].received.last?.kind,"suspend")
        try p.bus.links["b"]!.send(packet(p.host,kind:"availability",sender:"b",sequence:10001,payload:"true"),to:["a"],reliable:true)
        XCTAssertEqual(p.runtimes[0].received.last?.kind,"resumePeer")
        try p.bus.links["b"]!.send(packet(p.host,kind:"availability",sender:"b",sequence:10002,payload:"false"),to:["a"],reliable:true)
        p.runtimes[0].time+=16;p.host.update();XCTAssertEqual(p.runtimes[0].received.last?.kind,"suspend","away, not out yet (AwayPolicy)")
        p.runtimes[0].time+=MultiplayerTuning.awayLimitSeconds;p.host.update();XCTAssertEqual(p.runtimes[0].received.last?.kind,"drop");XCTAssertEqual(p.host.lobby?.participants.first { $0.id=="b" }?.seat,-1)
    }
    func testSharedStartWaitsForTheLatestClientCoverDeadline() throws {
        let p=try party(2); defer { p.close() }
        for service in p.services { try service.setReady(true) }; try p.host.startMatch()
        p.host.runtimeLoaded(readyAfter: 0.2); p.services[1].runtimeLoaded(readyAfter: 1.5)
        p.host.runtimeCalibrated(); p.services[1].runtimeCalibrated()   // tennis: the shared start follows the setup
        let starts = p.runtimes.compactMap { runtime in runtime.received.last(where: { $0.kind == "run" }).flatMap { Double($0.payload) } }
        XCTAssertEqual(starts.count, 2); XCTAssertEqual(starts[0], starts[1])
        XCTAssertGreaterThanOrEqual(starts[0], p.runtimes[0].time + 2.0)
    }

    func testLoadingTimeoutLeavesPartyRecoverable() throws {
        let p = try party(2); defer { p.close() }
        try p.host.setReady(true); try p.services[1].setReady(true); try p.host.startMatch()
        p.runtimes[0].time += 20; p.host.update()
        XCTAssertEqual(p.host.lobby?.phase, .loading); XCTAssertEqual(p.services[1].lobby?.phase, .loading)
        XCTAssertTrue(p.host.loadingNeedsDecision); XCTAssertTrue(p.services[1].loadingNeedsDecision)
        try p.services[1].keepWaitingForLoad()
        XCTAssertFalse(p.host.loadingNeedsDecision); XCTAssertFalse(p.services[1].loadingNeedsDecision)
        p.runtimes[0].time += 21; p.host.update(); XCTAssertTrue(p.host.loadingNeedsDecision)
        p.host.runtimeLoaded(); p.services[1].runtimeLoaded()
        XCTAssertEqual(p.host.lobby?.phase, .calibrating); XCTAssertFalse(p.host.loadingNeedsDecision)
        XCTAssertFalse(p.services[1].loadingNeedsDecision)
        p.host.runtimeCalibrated(); p.services[1].runtimeCalibrated()
        XCTAssertEqual(p.host.lobby?.phase, .playing)
    }
    func testRematchUsesAFreshReadinessBarrierAndRejectsRepeatedInput() throws {
        let p = try party(); defer { p.close() }; try start(p)
        try p.services[2].queueForNextMatch()
        let old = try XCTUnwrap(p.host.lobby?.matchID)
        let result = MultiplayerPacket(lobbyID:p.host.lobby!.id,matchID:old,sender:"a",kind:"result",payload:"{\"winner\":0,\"reason\":\"complete\"}")
        p.runtimes[0].outgoing.append(String(decoding:try JSONEncoder().encode(result),as:UTF8.self)); p.host.update()
        XCTAssertThrowsError(try p.services[1].rematch())
        try p.host.rematch()
        let next = try XCTUnwrap(p.host.lobby?.matchID)
        XCTAssertNotEqual(next, old)
        XCTAssertEqual(p.services.map(\.localSeat), [0,1,-1,-1], "Rematch keeps the same competitors")
        for s in p.services { XCTAssertEqual(s.lobby?.phase, .loading); XCTAssertFalse(s.lobby!.competitors.contains(where: \.loaded)) }
        XCTAssertThrowsError(try p.host.rematch())
        XCTAssertEqual(p.host.lobby?.matchID, next)
        p.host.runtimeLoaded(); XCTAssertEqual(p.host.lobby?.phase, .loading)
        p.services[1].runtimeLoaded(); XCTAssertEqual(p.host.lobby?.phase, .calibrating)
        XCTAssertFalse(p.host.lobby!.competitors.contains(where: \.calibrated), "A rematch sets the controllers up again")
        p.host.runtimeCalibrated(); p.services[1].runtimeCalibrated(); XCTAssertEqual(p.host.lobby?.phase, .playing)
        for r in p.runtimes { XCTAssertEqual(r.configurations.count, 2) }
    }
    func testTheHostLeavingTheAppKeepsTheMatchGoing() throws {
        // AwayPolicy: the match goes on without the host (the guest's game hands the host's side to the CPU) and the host rejoins.
        let p=try party(2);defer {p.close()};try start(p);p.host.setForeground(false)
        XCTAssertEqual(p.host.lobby?.phase,.playing);XCTAssertEqual(p.services[1].lobby?.phase,.playing)
        XCTAssertTrue(p.runtimes[1].received.contains { $0.kind == "suspend" && $0.payload == "a" }, "the guest's game is told the host is away")
        p.host.setForeground(true)
        XCTAssertTrue(p.runtimes[1].received.contains { $0.kind == "resumePeer" && $0.payload == "a" }, "...and that it is back")
        XCTAssertEqual(p.services[1].lobby?.phase,.playing)
    }
    func testAGuestWaitsForAMissingHostUntilTheAwayLimit() throws {
        let p=try party(2);defer {p.close()};try start(p); advancePastStart(p)
        let link=p.bus.links.removeValue(forKey:"a")!;link.connected=false;p.bus.links["b"]!.onPeersChanged?()
        advance(p, by: 60)
        XCTAssertEqual(p.services[1].lobby?.phase,.playing,"the host may only be out of the app: the match waits")
        advance(p, by: MultiplayerTuning.awayLimitSeconds)
        XCTAssertEqual(p.services[1].lobby?.phase,.interrupted)
        XCTAssertEqual(p.services[1].lastError,"The host was away too long, so the match ended.")
        link.connected=true;p.bus.links["a"]=link
    }
    func testWinnerStaysAndQueuedViewerTakesLoserSeat() throws {
        let p=try party();defer {p.close()};try start(p);try p.services[2].queueForNextMatch()
        let result=MultiplayerPacket(lobbyID:p.host.lobby!.id,matchID:p.host.lobby!.matchID,sender:"a",kind:"result",payload:"{\"winner\":1,\"reason\":\"complete\"}")
        p.runtimes[0].outgoing.append(String(decoding:try JSONEncoder().encode(result),as:UTF8.self));p.host.update();try p.host.returnToLobby()
        XCTAssertEqual(p.services[1].localSeat,1);XCTAssertEqual(p.services[2].localSeat,0);XCTAssertEqual(p.host.localSeat,-1)
    }
    /// The bridge reporting dropped packets is logged and play goes on: ending the match here (owner) or leaving it (guest) was what
    /// ejected guests mid-match. A lost versus call is caught by the next point's ready check in Unity.
    func testBridgeOverflowIsLoggedAndTheMatchPlaysOn() throws {
        let p=try party(2);defer {p.close()};try start(p)
        let error=MultiplayerPacket(kind:"bridgeError",payload:"Queue overflow")
        p.runtimes[0].outgoing.append(String(decoding:try JSONEncoder().encode(error),as:UTF8.self));p.host.update()
        p.runtimes[1].outgoing.append(String(decoding:try JSONEncoder().encode(error),as:UTF8.self));p.services[1].update()
        XCTAssertEqual(p.host.lobby?.phase,.playing);XCTAssertEqual(p.services[1].lobby?.phase,.playing)
        XCTAssertNil(p.host.lastError);XCTAssertNil(p.services[1].lastError)
        XCTAssertFalse(p.runtimes[1].received.contains { $0.kind=="stop" },"the guest keeps its match")
        XCTAssertFalse(p.runtimes[0].received.contains { $0.kind=="suspend" })
    }
    func testReconnectingCompetitorReloadsBeforeResume() throws {
        // Golf: reloading the game is enough. (Tennis also needs the controller set up again: see the calibration tests.)
        let p=try party(2);defer {p.close()};try start(p,.golf)
        let link=p.bus.links.removeValue(forKey:"b")!;link.connected=false;p.bus.links["a"]!.onPeersChanged?();link.onPeersChanged?()
        XCTAssertEqual(p.runtimes[0].received.last?.kind,"suspend");XCTAssertEqual(p.services[1].lobby?.phase,.playing,"it waits to get back in (AwayPolicy)")
        let prior=p.runtimes[0].received.filter {$0.kind=="resumePeer"}.count
        link.connected=true;p.bus.links["b"]=link;p.bus.links["a"]!.onPeersChanged?();link.onPeersChanged?()
        // (it kept its match while it waited, so the owner's repeated launch is the same match and nothing new is loaded)
        XCTAssertEqual(p.runtimes[1].configurations.count,1);XCTAssertEqual(p.runtimes[0].received.filter {$0.kind=="resumePeer"}.count,prior)
        p.services[1].runtimeLoaded();XCTAssertEqual(p.runtimes[0].received.filter {$0.kind=="resumePeer"}.count,prior+1);XCTAssertEqual(p.host.lobby?.phase,.playing)
    }
    // MARK: Tennis setup (calibration) before play

    /// Both tennis phones have loaded and are now setting up their controllers.
    private func loadedTennisParty(_ count: Int = 2) throws -> Party {
        let p = try party(count)
        try p.host.setReady(true); try p.services[1].setReady(true); try p.host.startMatch()
        for s in p.services where s.localSeat >= 0 { s.runtimeLoaded() }
        return p
    }
    func testCalibrationCanCompleteBeforeEitherCourtLoadsAndSurvivesThePhaseChange() throws {
        let p = try party(2); defer { p.close() }
        for s in p.services { try s.setReady(true) }; try p.host.startMatch()
        p.services[1].runtimeSetupStep("ready")
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.setupStep, "ready")
        p.host.runtimeCalibrated(); p.services[1].runtimeCalibrated()
        XCTAssertEqual(p.host.lobby?.phase, .loading)
        XCTAssertTrue(p.host.lobby!.competitors.allSatisfy(\.calibrated))
        p.host.runtimeLoaded()
        XCTAssertEqual(p.host.lobby?.phase, .loading, "local calibration must not wait for the remote renderer")
        p.services[1].runtimeLoaded()
        XCTAssertEqual(p.host.lobby?.phase, .playing, "loading completion must preserve both players' Ready acknowledgements")
        XCTAssertTrue(p.host.lobby!.competitors.allSatisfy(\.calibrated))
        for r in p.runtimes { XCTAssertEqual(r.received.filter { $0.kind == "run" }.count, 1) }
    }

    func testConnectionCheckRunsWhileCourtsLoadAndDoesNotAddAnotherSetupWait() throws {
        let p = try party(2, linkCheck: true); defer { p.close() }
        for service in p.services { try service.setReady(true) }; try p.host.startMatch()
        p.host.runtimeCalibrated(); p.services[1].runtimeCalibrated()
        run(p, for: 4)
        XCTAssertEqual(p.host.lobby?.phase, .loading)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.linkOK, true)
        p.host.runtimeLoaded(); p.services[1].runtimeLoaded()
        XCTAssertEqual(p.host.lobby?.phase, .playing, "the connection check must not restart when the last court loads")
    }

    func testARealRuntimeReloadCannotResendItsPreviousCalibrationAsReady() throws {
        let p = try loadedTennisParty(); defer { p.close() }
        p.host.runtimeCalibrated(); p.services[1].runtimeCalibrated()
        p.services[1].runtimeLoaded()
        run(p, for: 2)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.calibrated, false)
        XCTAssertTrue(p.runtimes[0].received.contains { $0.kind == "suspend" })
        p.services[1].runtimeCalibrated()
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.calibrated, true)
        XCTAssertTrue(p.runtimes[0].received.contains { $0.kind == "resumePeer" })
    }

    func testDroppedCalibrationIsRetriedUntilTheHostAcknowledgesIt() throws {
        let p = try loadedTennisParty(); defer { p.close() }
        p.host.runtimeCalibrated()
        p.bus.links["b"]!.dropKinds = ["calibrated"]
        p.services[1].runtimeCalibrated()
        XCTAssertEqual(p.host.lobby?.phase, .calibrating)
        p.bus.links["b"]!.dropKinds = []
        run(p, for: 1.5)
        XCTAssertEqual(p.host.lobby?.phase, .playing)
        XCTAssertEqual(p.services[1].lobby?.participants.first { $0.id == "b" }?.calibrated, true)
    }

    func testLostLoadingAcknowledgementRetriesWithoutResettingReady() throws {
        let p = try party(2); defer { p.close() }
        for s in p.services { try s.setReady(true) }; try p.host.startMatch()
        p.bus.links["a"]!.dropKinds = ["lobby"]
        p.services[1].runtimeLoaded(); p.services[1].runtimeCalibrated()
        XCTAssertEqual(p.services[1].lobby?.participants.first { $0.id == "b" }?.loaded, false)
        p.host.runtimeLoaded(); p.host.runtimeCalibrated()
        XCTAssertEqual(p.host.lobby?.phase, .playing)
        p.bus.links["a"]!.dropKinds = []
        run(p, for: 1.5)
        XCTAssertEqual(p.services[1].lobby?.phase, .playing)
        XCTAssertTrue(p.host.lobby!.competitors.allSatisfy(\.calibrated), "repeated loaded reports must be idempotent")
        XCTAssertFalse(p.runtimes[0].received.contains { $0.kind == "suspend" })
    }

    func testMissingRunMessageIsRecoveredAndBothPhonesCountDownOnTheSameClock() throws {
        let p = try loadedTennisParty(); defer { p.close() }
        p.bus.links["a"]!.dropKinds = ["run"]
        p.host.runtimeCalibrated(); p.services[1].runtimeCalibrated()
        XCTAssertEqual(p.host.startCountdown, 3)
        XCTAssertEqual(p.services[1].scheduledRunAt, 0)
        p.bus.links["a"]!.dropKinds = []
        run(p, for: 0.5)
        XCTAssertEqual(p.services[1].scheduledRunAt, p.host.scheduledRunAt)
        XCTAssertEqual(p.services[1].startCountdown, p.host.startCountdown)
        run(p, for: 3)
        XCTAssertNil(p.host.startCountdown); XCTAssertNil(p.services[1].startCountdown)
    }

    func testOnlineTennisNeedsAScreenEachUnlessSharingATVIsExplicit() throws {
        let p = try party(2, screens: [true, false], sharedScreen: false); defer { p.close() }
        for s in p.services { try s.setReady(true) }
        XCTAssertFalse(p.host.lobby!.canStart)
        XCTAssertTrue(p.host.lobby!.startReason.contains("must connect a TV"))
        XCTAssertThrowsError(try p.host.startMatch())
        try p.host.setSharedScreen(true)
        XCTAssertTrue(p.host.lobby!.canStart)
        try p.host.startMatch()
        XCTAssertEqual(p.runtimes[1].configurations.last?.localView, .controllerOnly)
    }

    func testQuickMatchRequiresTheLocalDisplayBeforeSearchingOrAuthenticating() async {
        let s = MultiplayerService()
        do { try await s.quickMatch(.tennis); XCTFail("Must connect this phone's TV first") }
        catch { XCTAssertTrue(error.localizedDescription.contains("AirPlay")) }
        XCTAssertFalse(s.searching); XCTAssertNil(s.lobby)
    }

    func testTennisWaitsForBothPlayersToSetUpTheirControllersBeforeRunning() throws {
        let p = try loadedTennisParty(); defer { p.close() }
        for s in p.services { XCTAssertEqual(s.lobby?.phase, .calibrating) }
        XCTAssertFalse(p.runtimes.contains { $0.received.contains { $0.kind == "run" } }, "nothing starts while anyone is still setting up")
        p.host.runtimeCalibrated()
        XCTAssertEqual(p.host.lobby?.phase, .calibrating, "one player is not enough")
        XCTAssertFalse(p.runtimes.contains { $0.received.contains { $0.kind == "run" } })
        p.services[1].runtimeCalibrated()
        for s in p.services { XCTAssertEqual(s.lobby?.phase, .playing) }
        for r in p.runtimes { XCTAssertEqual(r.received.filter { $0.kind == "run" }.count, 1, "each runtime is told to start exactly once") }
        XCTAssertTrue(p.host.lobby!.competitors.allSatisfy(\.calibrated))
    }
    func testSpectatorsNeverHoldUpTheStart() throws {
        let p = try loadedTennisParty(3); defer { p.close() }
        p.host.runtimeCalibrated(); p.services[1].runtimeCalibrated()
        for s in p.services { XCTAssertEqual(s.lobby?.phase, .playing) }
        XCTAssertEqual(p.services[2].localSeat, -1)
    }
    func testGolfGoesStraightToPlayingAndIgnoresCalibration() throws {
        let p = try party(2); defer { p.close() }; try start(p, .golf)
        for s in p.services { XCTAssertEqual(s.lobby?.phase, .playing) }
        p.services[1].runtimeCalibrated()
        XCTAssertFalse(p.host.lobby!.participants.contains(where: \.calibrated), "golf has nothing to calibrate")
    }
    func testCalibratedFromAnObserverOrAnOldMatchIsIgnored() throws {
        let p = try loadedTennisParty(3); defer { p.close() }
        p.services[2].runtimeCalibrated()
        // Sequence 0, so that the real packet from "b" later in this test is still newer than this one.
        let old = MultiplayerPacket(lobbyID: p.host.lobby!.id, matchID: "old", sender: "b", sequence: 0, kind: "calibrated")
        try p.bus.links["b"]!.send(JSONEncoder().encode(old), to: ["a"], reliable: true)
        p.host.runtimeCalibrated()
        XCTAssertEqual(p.host.lobby?.phase, .calibrating)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.calibrated, false)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "c" }?.calibrated, false)
        p.services[1].runtimeCalibrated()
        XCTAssertEqual(p.host.lobby?.phase, .playing)
    }
    func testAReconnectingPlayerDuringSetupReloadsAndSetsUpAgainBeforeTheMatchStarts() throws {
        let p = try loadedTennisParty(); defer { p.close() }
        p.host.runtimeCalibrated()
        dropAndReturn(p)
        XCTAssertEqual(p.runtimes[1].configurations.count, 2, "the game is sent to the returning phone again")
        XCTAssertEqual(p.host.lobby?.phase, .calibrating)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.loaded, false)
        p.services[1].runtimeLoaded()
        XCTAssertEqual(p.host.lobby?.phase, .calibrating, "loaded again is not set up again")
        p.services[1].runtimeCalibrated()
        XCTAssertEqual(p.host.lobby?.phase, .playing)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "a" }?.calibrated, true, "the player who stayed does not repeat the setup")
    }
    func testAReloadedTennisPlayerStaysPausedUntilItHasPointedAtTheTVAgain() throws {
        let p = try party(2); defer { p.close() }; try start(p)
        advance(p, by: 3)
        dropAndReturn(p)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.calibrated, false)
        let resumed = p.runtimes[0].received.filter { $0.kind == "resumePeer" }.count
        p.services[1].runtimeLoaded()
        XCTAssertEqual(p.runtimes[0].received.filter { $0.kind == "resumePeer" }.count, resumed, "reloading alone does not resume play")
        // Coming back to the foreground does not resume it either.
        try p.bus.links["b"]!.send(packet(p.host, kind: "availability", sender: "b", sequence: 30000, payload: "true"), to: ["a"], reliable: true)
        XCTAssertEqual(p.runtimes[0].received.filter { $0.kind == "resumePeer" }.count, resumed)
        p.services[1].runtimeCalibrated()
        XCTAssertEqual(p.runtimes[0].received.filter { $0.kind == "resumePeer" }.count, resumed + 1)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.calibrated, true)
        XCTAssertEqual(p.host.lobby?.phase, .playing)
    }
    func testAReloadedTennisPlayerGetsLongerThanADroppedConnectionToSetUpAgain() throws {
        let p = try party(2); defer { p.close() }; try start(p)
        advance(p, by: 3)
        dropAndReturn(p); p.services[1].runtimeLoaded()
        advance(p, by: 50)   // (it used to be given up on after 15 s, then 45 s: an online match now keeps the place for the away limit)
        XCTAssertFalse(p.runtimes[0].received.contains { $0.kind == "drop" })
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.seat, 1)
        advance(p, by: MultiplayerTuning.awayLimitSeconds)   // ...but nobody waits forever
        XCTAssertTrue(p.runtimes[0].received.contains { $0.kind == "drop" && $0.payload == "b" })
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.seat, -1)
    }
    func testSetupIsAbandonedWhenAPlayerLeavesDuringIt() throws {
        let p = try loadedTennisParty(); defer { p.close() }
        p.services[1].leave()
        XCTAssertEqual(p.host.lobby?.phase, .lobby, "the owner is not left waiting for someone who is gone")
        XCTAssertEqual(p.host.lastError, "The other player left during setup. Everyone is back in the lobby.")
        XCTAssertTrue(p.runtimes[0].received.contains { $0.kind == "stop" })
    }
    func testSetupThatDragsOnIsMentionedToEveryoneButNothingIsForced() throws {
        let p = try loadedTennisParty(); defer { p.close() }
        p.host.runtimeCalibrated()
        advance(p, by: 30)
        XCTAssertNil(p.services[1].lastError)
        advance(p, by: 31)
        XCTAssertTrue(p.services[1].lastError?.hasPrefix("Still waiting for") == true, "everyone hears who is holding things up")
        XCTAssertTrue(p.services[1].lastError?.hasSuffix("to finish setting up.") == true)
        XCTAssertEqual(p.host.lobby?.phase, .calibrating, "...but the match is neither started nor cancelled for them")
        XCTAssertEqual(p.host.lobby?.competitors.count, 2)
    }

    // MARK: Roles: who has the TV

    private func startTennis(_ p: Party) throws {
        try p.host.configure(.tennis)
        for s in p.services where s.localSeat >= 0 { try s.setReady(true) }
        try p.host.startMatch()
    }
    func testOneTVOnTheOwnersPhoneMakesItSplitAndTheGuestAController() throws {
        let p = try party(2, screens: [true, false]); defer { p.close() }
        try startTennis(p)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "a" }?.view, .split)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.view, .controllerOnly)
        XCTAssertEqual(p.runtimes[0].configurations.last?.controllerOnly, false)
        XCTAssertEqual(p.runtimes[1].configurations.last?.controllerOnly, true, "the phone without a TV is only a controller")
        XCTAssertEqual(p.runtimes[1].configurations.last?.localView, .controllerOnly)
        XCTAssertEqual(p.services[1].lobby?.participants.first { $0.id == "a" }?.view, .split, "the guest sees the same roles")
    }
    func testOneTVOnTheGuestsPhoneMakesTheOwnerAHeadlessHost() throws {
        let p = try party(2, screens: [false, true]); defer { p.close() }
        try startTennis(p)
        XCTAssertEqual(p.runtimes[0].configurations.last?.controllerOnly, true, "the owner still runs the match, with nothing on screen")
        XCTAssertEqual(p.runtimes[1].configurations.last?.localView, .split)
        XCTAssertEqual(p.runtimes[1].configurations.last?.controllerOnly, false)
    }
    func testTwoTVsKeepEachPhoneOnItsOwnCourt() throws {
        let p = try party(2, screens: [true, true]); defer { p.close() }
        try startTennis(p)
        for i in 0..<2 {
            XCTAssertEqual(p.runtimes[i].configurations.last?.localView, .near)
            XCTAssertEqual(p.runtimes[i].configurations.last?.controllerOnly, false)
        }
    }
    func testNoTVAnywhereBlocksTennisWithAClearReason() throws {
        let p = try party(2, screens: [false, false]); defer { p.close() }
        try p.host.configure(.tennis)
        for s in p.services { try s.setReady(true) }
        XCTAssertFalse(p.host.lobby!.canStart)
        XCTAssertEqual(p.host.lobby?.startReason, "Connect one phone to a TV (AirPlay) to play")
        XCTAssertThrowsError(try p.host.startMatch())
        XCTAssertEqual(p.host.lobby?.phase, .lobby)
    }
    func testPluggingInOrLosingATVReevaluatesTheLobby() throws {
        let p = try party(2, screens: [false, false]); defer { p.close() }
        try p.host.configure(.tennis)
        for s in p.services { try s.setReady(true) }
        XCTAssertFalse(p.host.lobby!.canStart)
        p.services[1].setScreen(true)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.hasScreen, true, "the owner hears about the guest's TV")
        XCTAssertTrue(p.host.lobby!.canStart)
        XCTAssertEqual(p.services[1].lobby?.participants.first { $0.id == "b" }?.hasScreen, true, "...and so does everyone")
        p.services[1].setScreen(false)
        XCTAssertFalse(p.host.lobby!.canStart)
        p.host.setScreen(true)
        XCTAssertTrue(p.host.lobby!.canStart, "the owner's own TV counts too")
    }
    func testGolfNeedsNoScreenAndHasNoViews() throws {
        let p = try party(2, screens: [false, false]); defer { p.close() }
        try start(p, .golf)
        XCTAssertEqual(p.host.lobby?.phase, .playing)
        XCTAssertTrue(p.host.lobby!.participants.allSatisfy { $0.view == nil })
        XCTAssertEqual(p.runtimes[0].configurations.last?.controllerOnly, false, "the golf owner's TV shows the round")
        XCTAssertEqual(p.runtimes[1].configurations.last?.controllerOnly, true, "golf guests watch the owner's TV, as before")
    }
    func testViewsAreClearedBetweenMatchesAndChosenAgainFromTheTVsThen() throws {
        let p = try party(2, screens: [true, false]); defer { p.close() }
        try startTennis(p)
        try p.host.returnToLobby()
        XCTAssertTrue(p.host.lobby!.participants.allSatisfy { $0.view == nil })
        p.services[1].setScreen(true); p.host.setScreen(false)
        for s in p.services { try s.setReady(true) }
        try p.host.startMatch()
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "a" }?.view, .controllerOnly)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.view, .split)
    }
    func testAPeerCannotClaimAViewOrASetupStateInItsHello() throws {
        let p = try party(2); defer { p.close() }
        let forged = MultiplayerParticipant(id: "x", name: "X", calibrated: true, hasScreen: true, view: .split)
        let hello = MultiplayerPacket(lobbyID: "", matchID: "", sender: "c", sequence: 1, kind: "hello", payload: String(decoding: try JSONEncoder().encode(forged), as: UTF8.self))
        try p.bus.link("c").send(JSONEncoder().encode(hello), to: ["a"], reliable: true)
        let joined = try XCTUnwrap(p.host.lobby?.participants.first { $0.id == "c" })
        XCTAssertNil(joined.view); XCTAssertFalse(joined.calibrated)
        XCTAssertTrue(joined.hasScreen, "a phone does say whether it has a TV")
    }
    func testViewsMustBeConsistentInALobby() {
        func lobby(_ sport: MultiplayerSport, _ views: [MultiplayerView?], seats: [Int] = [0, 1]) -> MultiplayerLobby {
            let people = views.enumerated().map { MultiplayerParticipant(id: "p\($0.offset)", name: "P", seat: seats[$0.offset], view: $0.element) }
            return MultiplayerLobby(ownerID: "p0", sport: sport, participants: people)
        }
        XCTAssertTrue(lobby(.tennis, [.split, .controllerOnly]).valid())
        XCTAssertTrue(lobby(.tennis, [.near, .near]).valid())
        XCTAssertTrue(lobby(.tennis, [nil, nil]).valid())
        XCTAssertFalse(lobby(.tennis, [.split, .split]).valid())
        XCTAssertFalse(lobby(.tennis, [.split, .near]).valid(), "the partner of a shared-screen phone has no screen of its own")
        XCTAssertFalse(lobby(.golf, [.near, nil]).valid(), "views are tennis only")
    }
    func testTheSharedTVsDelayReachesTheLobbyAndStaysWithinWhatTheGameWouldCredit() throws {
        let p = try party(2, screens: [true, false]); defer { p.close() }
        try startTennis(p)
        func delay(_ service: MultiplayerService, _ id: String) -> Double? { service.lobby?.participants.first { $0.id == id }?.screenDelay }
        p.host.setScreenDelay(0.17)
        XCTAssertEqual(try XCTUnwrap(delay(p.host, "a")), 0.17, accuracy: 1e-9)
        XCTAssertEqual(try XCTUnwrap(delay(p.services[1], "a")), 0.17, accuracy: 1e-9, "the controller-only phone hears it")
        p.host.setScreenDelay(5);    XCTAssertEqual(try XCTUnwrap(delay(p.host, "a")), 1, accuracy: 1e-9)
        p.host.setScreenDelay(-3);   XCTAssertEqual(try XCTUnwrap(delay(p.host, "a")), 0, accuracy: 1e-9)
        p.host.setScreenDelay(0.2);  p.host.setScreenDelay(.nan)
        XCTAssertEqual(try XCTUnwrap(delay(p.host, "a")), 0.2, accuracy: 1e-9, "a bad value is ignored")
        p.services[1].setScreenDelay(0.3)
        XCTAssertNil(delay(p.host, "b"), "a phone without a TV has no delay to report")
        try p.host.returnToLobby()
        XCTAssertNil(delay(p.host, "a"), "it is measured again for the next match")
    }
    func testAbsurdScreenDelaysAreRejectedInALobby() {
        func lobby(_ delay: Double?) -> MultiplayerLobby {
            MultiplayerLobby(ownerID: "a", participants: [MultiplayerParticipant(id: "a", name: "A", seat: 0, screenDelay: delay), MultiplayerParticipant(id: "b", name: "B", seat: 1)])
        }
        XCTAssertTrue(lobby(nil).valid()); XCTAssertTrue(lobby(0.3).valid())
        XCTAssertFalse(lobby(3).valid()); XCTAssertFalse(lobby(-0.1).valid()); XCTAssertFalse(lobby(Double.nan).valid())
    }
    /// proof/multiplayer/fixtures/tennis_one_tv_config.json is also parsed by NetworkViewTests.cs in Unity's tests, so the field
    /// names the owner writes and the ones Unity reads cannot drift apart unnoticed.
    func testTheOneTVConfigurationFixtureParsesAsTheOwnerWritesIt() throws {
        let url = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("proof/multiplayer/fixtures/tennis_one_tv_config.json")
        let data = try Data(contentsOf: url)
        let config = try JSONDecoder().decode(MultiplayerMatchConfiguration.self, from: data)
        XCTAssertTrue(config.valid())
        XCTAssertEqual(config.localView, .controllerOnly)
        XCTAssertTrue(config.controllerOnly)
        XCTAssertEqual(config.participants.first { $0.id == "host-phone" }?.view, .split)
        // Writing the same configuration produces the same field names the fixture has.
        let look = MultiplayerLoadout(gear: [:], skinHex: "E6AE7E", colours: [:], emotes: ["wave", "scuba", "spike"], shirtHex: "FF6B4A", shortsHex: "101D35")
        let host = MultiplayerParticipant(id: "host-phone", name: "Adnan", seat: 0, ready: true, hasScreen: true, view: .split, screenDelay: 0.17, loadout: look)
        let guest = MultiplayerParticipant(id: "guest-phone", name: "Sam", seat: 1, ready: true, hasScreen: false, view: .controllerOnly, female: true, left: true)
        let written = MultiplayerMatchConfiguration(lobbyID: "L", matchID: "M", hostID: "host-phone", localID: "guest-phone", sport: "tennis", venue: "resort", sets: 1, games: 3, seed: 1, participants: [host, guest])
        func keys(_ object: Any?) -> Set<String> { Set((object as? [String: Any])?.keys.map { $0 } ?? []) }
        let fixtureJSON = try XCTUnwrap(JSONSerialization.jsonObject(with: data) as? [String: Any])
        let writtenJSON = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(written)) as? [String: Any])
        XCTAssertEqual(keys(fixtureJSON), keys(writtenJSON))
        let fixtureHost = (fixtureJSON["participants"] as? [[String: Any]])?[0], writtenHost = (writtenJSON["participants"] as? [[String: Any]])?[0]
        XCTAssertEqual(keys(fixtureHost), keys(writtenHost))
        XCTAssertEqual(keys(fixtureHost?["loadout"]), keys(writtenHost?["loadout"]))
        XCTAssertEqual(keys((fixtureJSON["participants"] as? [[String: Any]])?[1]), keys((writtenJSON["participants"] as? [[String: Any]])?[1]))
        XCTAssertEqual((writtenHost?["view"] as? String), "split", "the enum is written as the plain word Unity reads")
        XCTAssertEqual(((writtenJSON["participants"] as? [[String: Any]])?[1]["view"] as? String), "none")
    }

    // MARK: Connection check before a tennis match

    /// Moves the clock in 10 ms steps, letting delayed messages arrive and every service run its update (pings, reports, timers).
    private func run(_ p: Party, for seconds: Double) {
        for _ in 0..<Int((seconds * 100).rounded()) {
            for r in p.runtimes { r.time += 0.01 }
            p.bus.flush(to: p.runtimes[0].time)
            for s in p.services { s.update() }
        }
    }
    /// A two-phone tennis party that has loaded; `calibrated` says whether both players have also finished setting up.
    private func linkCheckParty(delay: Double = 0, loss: Double = 0, calibrated: Bool = true) throws -> Party {
        let p = try party(2, linkCheck: true)
        try p.host.setReady(true); try p.services[1].setReady(true); try p.host.startMatch()
        for l in p.bus.links.values { l.oneWayDelay = delay; l.lossRate = loss }
        p.host.runtimeLoaded(); p.services[1].runtimeLoaded()
        run(p, for: 0.5)
        if calibrated { p.host.runtimeCalibrated(); p.services[1].runtimeCalibrated(); run(p, for: 0.5) }
        return p
    }
    func testAGoodConnectionStartsOnceItHasBeenSteadyForAWhile() throws {
        let p = try linkCheckParty(delay: 0.02); defer { p.close() }   // 40 ms round trip
        XCTAssertEqual(p.host.lobby?.phase, .calibrating, "set up, but the connection has not been watched yet")
        run(p, for: 1.0)
        XCTAssertEqual(p.host.lobby?.phase, .calibrating, "a second of good pings is not yet a steady connection")
        run(p, for: 4.0)
        XCTAssertEqual(p.host.lobby?.phase, .playing)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.linkOK, true)
        XCTAssertEqual(p.services[1].lobby?.phase, .playing)
    }
    func testAWeakConnectionWaitsThenOffersPlayAnywayToTheOwnerOnly() throws {
        let p = try linkCheckParty(delay: 0.15); defer { p.close() }   // 300 ms round trip
        run(p, for: 6)
        XCTAssertEqual(p.host.lobby?.phase, .calibrating)
        XCTAssertFalse(p.host.linkNeedsDecision, "it waits a few seconds before asking")
        run(p, for: 5)
        XCTAssertEqual(p.host.lobby?.phase, .calibrating)
        XCTAssertTrue(p.host.linkNeedsDecision)
        XCTAssertTrue(p.services[1].lastError?.contains("weak") == true, "the guest hears why it is waiting")
        p.services[1].playAnyway()
        XCTAssertEqual(p.host.lobby?.phase, .calibrating, "only the owner can choose to play anyway")
        p.host.playAnyway()
        XCTAssertEqual(p.host.lobby?.phase, .playing)
        XCTAssertFalse(p.host.linkNeedsDecision)
    }
    func testALossyConnectionIsNotSteadyEvenWhenTheRoundTripsAreFast() throws {
        let p = try linkCheckParty(delay: 0.02, loss: 0.25); defer { p.close() }   // a quarter of pings and pongs vanish
        run(p, for: 9)
        XCTAssertEqual(p.host.lobby?.phase, .calibrating)
        XCTAssertTrue(p.host.linkNeedsDecision)
    }
    func testWithoutAGuestReportingTheOwnerDoesNotCallItSteady() throws {
        let p = try linkCheckParty(delay: 0.02, calibrated: false); defer { p.close() }
        run(p, for: 4)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.linkOK, true, "good pings for 4 s are steady")
        p.bus.links["b"]!.drop = true    // the guest goes quiet without the transport noticing
        run(p, for: 1.5)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.linkOK, false, "silence is not steadiness")
        p.bus.links["b"]!.drop = false
        run(p, for: 6)   // the pings lost during the silence must scroll out of the 20-ping window, then 1.5 s of good ones (modelled: ~4.3 s)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.linkOK, true, "...and it is steady again after a while of good pings")
    }
    func testTheWeakConnectionNoticeAndPlayAnywayGoAwayOnceTheLinkRecoversAndPlayBegins() throws {
        let p = try linkCheckParty(delay: 0.15); defer { p.close() }   // 300 ms round trip
        run(p, for: 11)
        XCTAssertTrue(p.host.linkNeedsDecision)
        XCTAssertTrue(p.host.lastError?.contains("weak") == true)
        XCTAssertTrue(p.services[1].lastError?.contains("weak") == true)
        for l in p.bus.links.values { l.oneWayDelay = 0.02 }   // the connection improves by itself, without anyone choosing Play anyway
        run(p, for: 8)
        XCTAssertEqual(p.host.lobby?.phase, .playing)
        XCTAssertFalse(p.host.linkNeedsDecision, "no dead Play anyway button for the rest of the match")
        XCTAssertNil(p.host.lastError, "the weak-connection notice is about setup")
        XCTAssertNil(p.services[1].lastError)
    }
    func testTheConnectionCheckNeverHoldsUpGolfOrAMatchThatIsAlreadyRunning() throws {
        let p = try party(2, linkCheck: true); defer { p.close() }
        try start(p, .golf)    // golf has no setup phase, so no check
        XCTAssertEqual(p.host.lobby?.phase, .playing)
    }
    func testLinkWindowGradesByRoundTripJitterAndLoss() {
        func window(_ rtts: [Double?]) -> LinkWindow {
            var w = LinkWindow(); var t = 0.0
            for rtt in rtts { w.sent(at: t); if let rtt { w.answered(sentAt: t, rtt: rtt) } else { w.expire(now: t + LinkWindow.lostAfter + 0.001) }; t += 0.1 }   // a hair over a second: 0.1 added twenty times is not exact
            return w
        }
        XCTAssertEqual(window(Array(repeating: 0.05, count: 20)).grade, .good)
        XCTAssertEqual(window(Array(repeating: 0.12, count: 20)).grade, .fair)
        XCTAssertEqual(window(Array(repeating: 0.20, count: 20)).grade, .poor)
        XCTAssertEqual(window(Array(repeating: 0.05, count: 9)).grade, .unknown, "fewer than ten answers cannot say")
        XCTAssertEqual(window(Array(repeating: nil, count: 12)).grade, .poor, "nothing came back")
        // Boundaries: exactly at a limit is still within it.
        XCTAssertEqual(window(Array(repeating: MultiplayerTuning.linkGoodRTT, count: 20)).grade, .good)
        XCTAssertEqual(window(Array(repeating: MultiplayerTuning.linkFairRTT, count: 20)).grade, .fair)
        XCTAssertEqual(window(Array(repeating: MultiplayerTuning.linkFairRTT + 0.001, count: 20)).grade, .poor)
        // A median that looks fine but jumps about is not.
        XCTAssertEqual(window((0..<20).map { $0 % 2 == 0 ? 0.02 : 0.12 }).grade, .poor, "jitter 100 ms")
        // Loss: one lost ping in twenty is 5% (fair); two is 10% (poor).
        XCTAssertEqual(window(Array(repeating: 0.05, count: 19) + [nil]).grade, .fair)
        XCTAssertEqual(window(Array(repeating: 0.05, count: 18) + [nil, nil]).grade, .poor)
    }
    func testLinkWindowCountsAPingNobodyAnsweredAsLostAndIgnoresStrangers() {
        var w = LinkWindow()
        w.sent(at: 10); w.sent(at: 10.1)
        w.answered(sentAt: 10.1, rtt: 0.05)
        w.answered(sentAt: 99, rtt: 0.05)       // a pong for a ping this window never sent
        w.answered(sentAt: 10.1, rtt: 0.05)     // the same pong twice
        XCTAssertEqual(w.samples.count, 1)
        w.expire(now: 10.5); XCTAssertEqual(w.samples.count, 1, "not yet a second")
        w.expire(now: 11.0); XCTAssertEqual(w.samples.count, 2)
        XCTAssertEqual(w.lossPercent, 50, accuracy: 1e-9)
        XCTAssertEqual(LinkWindow.parse(report: w.report)?.grade, .unknown)
        XCTAssertNil(LinkWindow.parse(report: "nonsense")); XCTAssertNil(LinkWindow.parse(report: "9|0.1|0|0"))
    }

    // MARK: Local play

    func testOnlyTheLocalNetworkDeniedErrorIsRecognisedAsSuch() {
        XCTAssertTrue(LocalMultiplayerTransport.isLocalNetworkDenied(.dns(-65570)), "iOS reports a denied Local Network permission this way")
        XCTAssertFalse(LocalMultiplayerTransport.isLocalNetworkDenied(.dns(-65537)))
        XCTAssertFalse(LocalMultiplayerTransport.isLocalNetworkDenied(.posix(.ECONNREFUSED)))
    }
    func testADeniedLocalNetworkIsRememberedSoTheMenuCanOfferSettingsAndForgottenOnLeaving() throws {
        let p = try party(2); defer { p.close() }
        XCTAssertFalse(p.host.localNetworkDenied)
        p.bus.links["a"]!.onError?(MultiplayerError.localNetworkDenied)
        XCTAssertTrue(p.host.localNetworkDenied)
        XCTAssertEqual(p.host.lastError, MultiplayerError.localNetworkDenied.localizedDescription)
        p.host.leave()
        XCTAssertFalse(p.host.localNetworkDenied)
    }

    func testLocalPartyNameFitsBonjourByteLimitWithEmoji() {
        let token=UUID().uuidString
        let name=LocalMultiplayerTransport.advertisedName(String(repeating:"🏌️~",count:30),token:token)
        XCTAssertLessThanOrEqual(name.utf8.count,63);XCTAssertEqual(name.components(separatedBy:"~").count,2);XCTAssertTrue(name.hasSuffix(token))
    }

    func testHostSeatSwapAndGuestSettingsStayProtected() throws {
        let p=try party();defer { p.close() }
        XCTAssertEqual(p.host.lobby?.startReason,"Waiting for Player to be ready")
        try p.host.swapSeat("c",with:"b")
        XCTAssertEqual(p.services.map(\.localSeat),[0,-1,1,-1])
        XCTAssertThrowsError(try p.services[1].swapSeat("d",with:"a"))
        XCTAssertThrowsError(try p.services[1].assignSeat("d",seat:0))
        try p.host.setReady(true);try p.services[2].setReady(true)
        XCTAssertTrue(p.host.lobby!.canStart)
    }

    func testGolfCourseIDsAreAcceptedOnlyForGolf() throws {
        let p = try party(); defer { p.close() }
        for venue in MultiplayerLobby.golfVenues {
            try p.host.configure(.golf, venue: venue)
            XCTAssertTrue(p.host.lobby!.valid()); XCTAssertEqual(p.services[1].lobby?.venue, venue)
        }
        XCTAssertEqual(MultiplayerLobby.golfVenues, ["cliffside", "wildisles", "magma"])
        XCTAssertEqual(GolfCourseChoice.allCases.map(\.rawValue), MultiplayerLobby.golfVenues)
        for venue in MultiplayerLobby.golfVenues { XCTAssertThrowsError(try p.host.configure(.tennis, venue: venue)) }
        XCTAssertThrowsError(try p.host.configure(.golf, venue: "../../invalid"))
    }
    func testRetiredPostcardsCourseBecomesCliffside() throws {
        let p = try party(2); defer { p.close() }
        XCTAssertEqual(MultiplayerLobby.currentGolfVenue("postcards"), "cliffside")
        XCTAssertEqual(MultiplayerLobby.currentGolfVenue("magma"), "magma")
        XCTAssertNil(GolfCourseChoice(rawValue: "postcards"))
        try p.host.configure(.golf); XCTAssertEqual(p.host.lobby?.venue, "cliffside")
        try p.host.configure(.golf, venue: "postcards"); XCTAssertEqual(p.host.lobby?.venue, "cliffside")
        XCTAssertThrowsError(try p.host.configure(.tennis, venue: "postcards"))
        // A lobby from an older host still names the retired course: the guest keeps it as Cliffside instead of dropping it.
        var old = try XCTUnwrap(p.host.lobby); old.venue = "postcards"; old.revision += 10
        let payload = String(decoding: try JSONEncoder().encode(old), as: UTF8.self)
        let raw = try JSONEncoder().encode(MultiplayerPacket(lobbyID: old.id, sender: "a", sequence: 1_000_000, kind: "lobby", payload: payload))
        try p.bus.links["a"]!.send(raw, to: ["b"], reliable: true)
        XCTAssertEqual(p.services[1].lobby?.revision, old.revision); XCTAssertEqual(p.services[1].lobby?.venue, "cliffside")
    }
    func testIdentityAndLookReachEveryPeerWithoutChangingSeatsOrReady() throws {
        let p = try party(); defer { p.close() }
        var player = Player(name: "Sam", colorIndex: 1); player.setSkin(0.8); player.setOutfitHex("shirt", "D3F34B")
        p.services[1].setIdentity(name: player.name, female: true, left: true, loadout: player.multiplayerLoadout)
        for s in p.services {
            let remote = s.lobby!.participants.first { $0.id == "b" }!
            XCTAssertEqual(remote.loadout, player.multiplayerLoadout); XCTAssertTrue(remote.female); XCTAssertTrue(remote.left)
            XCTAssertEqual(remote.seat, 1); XCTAssertEqual(remote.name, "Sam")
        }
        try p.services[1].setReady(true); p.runtimes[0].time += 0.1
        player.setOutfitHex("shorts", "FF6B4A"); try p.services[1].updateLook(player.multiplayerLoadout)
        XCTAssertEqual(p.host.lobby!.participants[1].loadout, player.multiplayerLoadout)
        XCTAssertTrue(p.host.lobby!.participants[1].ready)
    }
    func testForgedInvalidAndRapidLookPacketsAreRejected() throws {
        let p = try party(2); defer { p.close() }
        let look = MultiplayerLoadout(skinHex: "E6AE7E", colours: ["shirt":"D3F34B"])
        func send(_ id: String, _ look: MultiplayerLoadout, _ seq: Int64) throws {
            let payload = String(decoding: try JSONEncoder().encode(MultiplayerLookUpdate(participantID: id, loadout: look)), as: UTF8.self)
            try p.bus.links["b"]!.send(packet(p.host, kind: "look", sender: "a", sequence: seq, payload: payload), to: ["a"], reliable: true)
        }
        try send("a", look, 1000); XCTAssertNil(p.host.lobby!.participants[0].loadout)
        try send("b", MultiplayerLoadout(skinHex:"BAD"), 1001); XCTAssertNil(p.host.lobby!.participants[1].loadout)
        try send("b", look, 1002); XCTAssertEqual(p.host.lobby!.participants[1].loadout, look)
        try send("b", MultiplayerLoadout(skinHex:"FFFFFF"), 1003); XCTAssertEqual(p.host.lobby!.participants[1].loadout, look)
    }
    func testEmoteEchoHasSameEventAndCooldownAndPhaseGate() throws {
        let p = try party(); defer { p.close() }
        try p.services[1].playEmote("scuba")
        let event = p.services[1].emotes["b"]!
        XCTAssertTrue(p.services.allSatisfy { $0.emotes["b"]?.id == event.id })
        XCTAssertThrowsError(try p.services[1].playEmote("wave"))
        p.runtimes[0].time += 1.5; p.runtimes[1].time += 1.5
        try p.services[1].playEmote("wave"); XCTAssertEqual(p.host.emotes["b"]?.emoteID, "wave")
        try start(p); XCTAssertThrowsError(try p.services[1].playEmote("pushups"))
    }
    func testHostEnforcesEmoteLimitEvenWhenClientBypassesIt() throws {
        let p = try party(2); defer { p.close() }
        func send(_ id: String, _ seq: Int64, _ startedAt: Double = 100) throws {
            let payload = String(decoding: try JSONEncoder().encode(MultiplayerEmote(participantID:id, emoteID:"spike", startedAt:startedAt, eventID:String(seq))), as:UTF8.self)
            try p.bus.links["b"]!.send(packet(p.host,kind:"emote",sender:"a",sequence:seq,payload:payload),to:["a"],reliable:true)
        }
        try send("a", 1000); XCTAssertTrue(p.host.emotes.isEmpty)
        try send("b", 1001); XCTAssertEqual(p.host.emotes["b"]?.id, "1001")
        try send("b", 1002); XCTAssertEqual(p.host.emotes["b"]?.id, "1001")
        p.runtimes[0].time += 1.49; try send("b",1003); XCTAssertEqual(p.host.emotes["b"]?.id,"1001")
        p.runtimes[0].time += 0.02; try send("b",1004); XCTAssertEqual(p.host.emotes["b"]?.id,"1004")
    }
    func testAnyRemoteLobbyMemberLocksSoloMenuLaunchesUntilTheyLeave() throws {
        let p = try party(2); defer { p.close() }
        XCTAssertTrue(p.host.hasFriendsInLobby, "the lock also applies to Nearby and non-party transports")
        let menu = TennisMenu(); menu.online = OnlineLobbyMenu(service: p.host)
        menu.debugShow(.exhibition)
        menu.begin(MenuLaunch(mode: .exhibition))
        XCTAssertNil(menu.launch); XCTAssertEqual(menu.notice, HubSession.soloLockMessage)
        menu.chooseCourseForPassThePhone(2)
        XCTAssertNil(menu.launch)
        p.services[1].leave()
        XCTAssertFalse(p.host.hasFriendsInLobby)
    }

    func testOldPeerShowsIncompatibleAndOptionalLookDecodes() throws {
        let p = try party(2); defer { p.close() }
        var old = MultiplayerPacket(kind:"hello"); old.version = 1
        try p.bus.links["b"]!.send(JSONEncoder().encode(old),to:["a"],reliable:true)
        XCTAssertEqual(p.host.lastError,MultiplayerError.incompatible.localizedDescription)
        XCTAssertEqual(MultiplayerPacket.version,5)
        let data = try JSONEncoder().encode(MultiplayerParticipant(id:"old",name:"Old"))
        XCTAssertNil(try JSONDecoder().decode(MultiplayerParticipant.self,from:data).loadout)
    }
    func testFourFullLoadoutsStayWithinPacketBudget() throws {
        let look = MultiplayerLoadout(gear:["tennis":["skin":"standard","racket":"standard","shoes":"standard"],"golf":["skin":"standard","club":"standard","shoes":"standard"]],skinHex:"E6AE7E",colours:["shirt":"FFFFFF","shorts":"D3F34B","accent":"FF6B4A","racket":"101D35"])
        let participants = (0..<4).map { MultiplayerParticipant(id:UUID().uuidString,name:String(repeating:"A",count:40),seat:$0,loadout:look) }
        let lobby = MultiplayerLobby(ownerID:participants[0].id,sport:.golf,venue:"cliffside",participants:participants)
        let json = try JSONEncoder().encode(lobby)
        XCTAssertLessThan(json.count,MultiplayerPacket.maximumBytes)
        let packetBytes = try JSONEncoder().encode(MultiplayerPacket(kind:"lobby",payload:String(decoding:json,as:UTF8.self))).count
        XCTAssertLessThan(packetBytes,MultiplayerPacket.maximumBytes)
        print("LOBBY_JSON_BYTES lobby=\(json.count) packet=\(packetBytes) maximum=\(MultiplayerPacket.maximumBytes)")
    }

    // MARK: Shared clock

    /// Same vector as ClockFilterModelTests.FixedVectorForTheSwiftPort (Tools/netsim): the Swift filter must match the
    /// model that was validated against simulated jitter spikes.
    func testClockFilterMatchesTheSharedVector() {
        var filter = ClockFilter()
        var samples: [(Double, Double)] = [(0.050, 100.000), (0.030, 100.002), (0.200, 100.090), (0.040, 100.004), (0.300, 99.900), (0.032, 100.003)]
        samples += Array(repeating: (0.031, 100.040), count: 8) + Array(repeating: (0.025, 100.500), count: 4)
        let expected = [100.000, 100.001, 100.002, 100.002, 100.002, 100.003, 100.003, 100.008, 100.013, 100.018, 100.023, 100.028, 100.033, 100.038, 100.040,
                        100.500, 100.500, 100.500]
        XCTAssertEqual(samples.count, expected.count)
        for (i, sample) in samples.enumerated() {
            XCTAssertEqual(filter.add(rtt: sample.0, offset: sample.1), expected[i], accuracy: 1e-9, "sample \(i)")
        }
        XCTAssertEqual(filter.medianRTT, 0.028, accuracy: 1e-9)
    }
    func testClockFilterIgnoresBadSamples() {
        var filter = ClockFilter(); filter.add(rtt: 0.04, offset: 10)
        XCTAssertEqual(filter.add(rtt: .nan, offset: 99), 10, accuracy: 1e-12)
        XCTAssertEqual(filter.add(rtt: 0.04, offset: .infinity), 10, accuracy: 1e-12)
        XCTAssertEqual(filter.add(rtt: -1, offset: 99), 10, accuracy: 1e-12)
    }
    /// A pong that took 200 ms (one leg slow, so its offset is 75 ms off) must not move a clock that a 40 ms pong set.
    func testASlowPongDoesNotMoveTheSharedClock() throws {
        let p = try party(2); defer { p.close() }
        let guest = p.services[1], runtime = p.runtimes[1]
        func pong(sent: Double, hostSentAt: Double, sequence: Int64) throws {
            let data = try JSONEncoder().encode(MultiplayerPacket(lobbyID: guest.lobby!.id, matchID: guest.lobby!.matchID, sender: "a",
                                                                   sequence: sequence, kind: "pong", reliable: false, sentAt: hostSentAt, payload: String(sent)))
            try p.bus.links["a"]!.send(data, to: ["b"], reliable: false)
        }
        runtime.time = 200.00
        try pong(sent: 199.96, hostSentAt: 5.0 + (199.96 + 200.00) / 2, sequence: 5001)
        XCTAssertEqual(guest.networkTime - runtime.time, 5.0, accuracy: 1e-6, "a good pong sets the clock")
        runtime.time = 200.50
        try pong(sent: 200.30, hostSentAt: 5.0 + (200.30 + 200.50) / 2 + 0.075, sequence: 5002)
        XCTAssertEqual(guest.networkTime - runtime.time, 5.0, accuracy: 0.006, "a slow pong may nudge the clock by at most one slew step")
        XCTAssertEqual(guest.roundTrip, 0.12, accuracy: 1e-6, "round trip is the median of the recent pongs, not the last one")
    }

    // MARK: Quiet players

    /// Moves every phone's clock forward in 0.1 s steps and lets each service run its update (heartbeats, silence checks).
    private func advance(_ p: Party, by seconds: Double) {
        for _ in 0..<Int((seconds * 10).rounded()) {
            for r in p.runtimes { r.time += 0.1 }
            for s in p.services { s.update() }
        }
    }
    private func advancePastStart(_ p: Party) {
        advance(p, by: max(0, p.host.scheduledRunAt - p.runtimes[0].time) + MultiplayerTuning.silenceGrace + 0.2)
    }
    func testTheCountdownDoesNotCountAsAQuietOpponent() throws {
        let p = try party(2); defer { p.close() }; try start(p)
        p.bus.links["b"]!.drop = true
        advance(p, by: 3)
        XCTAssertFalse(p.runtimes[0].received.contains { $0.kind == "suspend" }, "the silence grace starts after the countdown")
    }
    func testAQuietCompetitorPausesPlayAfterTheSilenceLimitAndResumesWhenHeardAgain() throws {
        let p = try party(2); defer { p.close() }; try start(p)
        advancePastStart(p)   // past the start grace, with heartbeats flowing
        XCTAssertFalse(p.runtimes[0].received.contains { $0.kind == "suspend" }, "a healthy link never pauses")
        p.bus.links["b"]!.drop = true
        advance(p, by: MultiplayerTuning.silenceSeconds - 0.3)
        XCTAssertFalse(p.runtimes[0].received.contains { $0.kind == "suspend" }, "a gap shorter than the silence limit is played through")
        advance(p, by: 0.5)
        XCTAssertTrue(p.runtimes[0].received.contains { $0.kind == "suspend" && $0.payload == "b" }, "the owner must pause once the silence limit has passed")
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.connected, true, "...without waiting for the transport to report a disconnect")
        let resumedBefore = p.runtimes[0].received.filter { $0.kind == "resumePeer" }.count
        p.bus.links["b"]!.drop = false
        advance(p, by: 0.5)
        XCTAssertGreaterThan(p.runtimes[0].received.filter { $0.kind == "resumePeer" }.count, resumedBefore, "...and resume once it is heard again")
        XCTAssertEqual(p.host.lobby?.phase, .playing)
    }
    func testACompetitorQuietForTooLongIsDropped() throws {
        let p = try party(2); defer { p.close() }; try start(p)
        advancePastStart(p)
        p.bus.links["b"]!.drop = true
        advance(p, by: 16)
        XCTAssertFalse(p.runtimes[0].received.contains { $0.kind == "drop" }, "a player away keeps their place (AwayPolicy)")
        advance(p, by: MultiplayerTuning.awayLimitSeconds)
        XCTAssertTrue(p.runtimes[0].received.contains { $0.kind == "drop" && $0.payload == "b" })
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.seat, -1)
        p.bus.links["b"]!.drop = false; dropAndReturn(p); advance(p, by: 0.5)   // (its link comes back: the owner publishes the lobby)
        XCTAssertTrue(p.services[1].droppedFromMatch, "its phone knows it is out, and leaves when it opens again")
    }
    func testAGuestBackFromTheBackgroundInTimeKeepsItsPlace() throws {
        let p = try party(2); defer { p.close() }; try start(p)
        advancePastStart(p)
        p.services[1].setForeground(false); p.bus.links["b"]!.drop = true
        advance(p, by: 120)
        p.bus.links["b"]!.drop = false; p.services[1].setForeground(true); advance(p, by: 1)
        XCTAssertFalse(p.runtimes[0].received.contains { $0.kind == "drop" })
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.seat, 1)
        XCTAssertFalse(p.services[1].droppedFromMatch)
        XCTAssertTrue(p.runtimes[0].received.contains { $0.kind == "resumePeer" && $0.payload == "b" })
    }
    func testOccasionalLostPacketsDoNotPausePlay() throws {
        let p = try party(2); defer { p.close() }; try start(p)
        advancePastStart(p)
        // About 3% of the guest's packets are lost, from a fixed seed (the longest run of lost steps is 2).
        var seed: UInt64 = 20261009
        func chance() -> Double { seed = seed &* 6364136223846793005 &+ 1442695040888963407; return Double(seed >> 11) / Double(1 << 53) }
        for _ in 0..<600 {
            p.bus.links["b"]!.drop = chance() < 0.03
            advance(p, by: 0.1)
        }
        p.bus.links["b"]!.drop = false
        XCTAssertFalse(p.runtimes[0].received.contains { $0.kind == "suspend" }, "occasional packet loss must not pause play")
    }
    /// Both sides watch (P2): a guest that hears nothing from the owner holds its own game, and only its own (it does not speak for
    /// the lobby), then resumes after a few packets.
    func testAGuestHoldsItsGameWhileTheOwnerIsQuietAndResumes() throws {
        let p = try party(2); defer { p.close() }; try start(p)
        advancePastStart(p)
        XCTAssertFalse(p.runtimes[1].received.contains { $0.kind == "suspend" }, "a healthy link never holds the guest")
        p.bus.links["a"]!.drop = true
        advance(p, by: MultiplayerTuning.silenceSeconds - 0.3)
        XCTAssertFalse(p.runtimes[1].received.contains { $0.kind == "suspend" })
        advance(p, by: 0.5)
        XCTAssertTrue(p.runtimes[1].received.contains { $0.kind == "suspend" && $0.payload == "a" && $0.sender == "b" }, "the guest's own watch holds its game")
        XCTAssertFalse(p.runtimes[0].received.contains { $0.kind == "suspend" }, "the owner, which hears the guest, plays on")
        p.bus.links["a"]!.drop = false
        advance(p, by: 1)
        XCTAssertTrue(p.runtimes[1].received.contains { $0.kind == "resumePeer" && $0.payload == "a" }, "...and resumes once the owner is heard again")
        XCTAssertEqual(p.services[1].lobby?.phase, .playing)
    }
    /// A nearby guest whose connection broke and came back without its game reloading (LocalMultiplayerTransport dials again): its
    /// repeated load report is the same game, so play resumes for it without a reload.
    func testAGuestThatReconnectsWithoutReloadingResumes() throws {
        let p = try party(2); defer { p.close() }; try start(p, .golf)
        advancePastStart(p)
        dropAndReturn(p)
        XCTAssertTrue(p.runtimes[0].received.contains { $0.kind == "suspend" && $0.payload == "b" })
        let prior = p.runtimes[0].received.filter { $0.kind == "resumePeer" }.count
        advance(p, by: 1.5)
        XCTAssertGreaterThan(p.runtimes[0].received.filter { $0.kind == "resumePeer" && $0.payload == "b" }.count, prior)
        XCTAssertEqual(p.host.lobby?.participants.first { $0.id == "b" }?.loaded, true)
        XCTAssertEqual(p.runtimes[1].configurations.count, 1, "nothing was loaded again")
        XCTAssertEqual(p.host.lobby?.phase, .playing)
    }
    func testASpectatorGoingQuietNeverPausesPlay() throws {
        let p = try party(3); defer { p.close() }; try start(p)
        advancePastStart(p)
        p.bus.links["c"]!.drop = true
        advance(p, by: 5)
        XCTAssertFalse(p.runtimes[0].received.contains { $0.kind == "suspend" })
    }
    func testAQuietCompetitorKeepsItsSetUpStateWhenAnotherPhoneLeaves() throws {
        let p = try party(3); defer { p.close() }; try start(p)
        advancePastStart(p)
        p.bus.links["b"]!.drop = true
        advance(p, by: MultiplayerTuning.silenceSeconds + 0.2)
        XCTAssertTrue(p.runtimes[0].received.contains { $0.kind == "suspend" && $0.payload == "b" })
        p.services[2].leave()   // the spectator goes: the owner's list of connected phones changes while b is quiet
        p.bus.links["b"]!.drop = false
        advance(p, by: 0.5)
        let b = p.host.lobby?.participants.first { $0.id == "b" }
        XCTAssertEqual(b?.loaded, true, "b never dropped, so it is the same game session")
        XCTAssertEqual(b?.calibrated, true, "...and it must not be shown as 'getting ready' for the rest of the match")
        XCTAssertEqual(p.host.lobby?.phase, .playing)
    }

    // MARK: Staying awake, statistics, big unreliable messages

    func testThePhoneStaysAwakeWhileASportsSessionIsActive() {
        let session = SportsSession()
        UIApplication.shared.isIdleTimerDisabled = false
        session.active = true
        XCTAssertTrue(UIApplication.shared.isIdleTimerDisabled, "A motion-controlled match has no touches, so the phone would auto-lock")
        session.active = false
        XCTAssertFalse(UIApplication.shared.isIdleTimerDisabled)
    }
    func testNetStatsSummarizeRoundTripsAndLoss() {
        var stats = NetStats()
        XCTAssertTrue(stats.isEmpty)
        stats.pingsSent = 10
        for rtt in [0.04, 0.05, 0.04, 0.20, 0.05, 0.04, 0.05, 0.04] { stats.note(rtt: rtt) }
        XCTAssertEqual(stats.medianRTT, 0.045, accuracy: 1e-9)
        XCTAssertEqual(stats.p95RTT, 0.20, accuracy: 1e-9)
        XCTAssertEqual(stats.lossPercent, 20, accuracy: 1e-9)
        XCTAssertGreaterThan(stats.jitter, 0)
        stats.note(rtt: .nan); stats.note(rtt: -1)
        XCTAssertEqual(stats.pongsHeard, 8, "bad samples are not counted")
        XCTAssertTrue(stats.summary.contains("rtt median 45 ms"))
        XCTAssertFalse(stats.isEmpty)
    }
    func testARefusedBigUnreliableSendFallsBackToReliableOnceAndIsRemembered() throws {
        let p = try party(2); defer { p.close() }; try start(p)
        let link = p.bus.links["a"]!
        link.refuseUnreliableOver = 1000
        func relaySnapshot() throws {
            let packet = MultiplayerPacket(lobbyID: p.host.lobby!.id, matchID: p.host.lobby!.matchID, sender: "a", kind: "snapshot",
                                           reliable: false, payload: String(repeating: "x", count: 1500))
            p.runtimes[0].outgoing.append(String(decoding: try JSONEncoder().encode(packet), as: UTF8.self))
            p.host.update()
        }
        try relaySnapshot()
        XCTAssertEqual(link.refused, 1, "the transport refused the big unreliable message")
        XCTAssertEqual(link.transportModes.last { $0.kind == "snapshot" }?.reliable, true, "...so it was sent reliably instead")
        XCTAssertTrue(p.runtimes[1].received.contains { $0.kind == "snapshot" }, "...and the guest got it")
        try relaySnapshot()
        XCTAssertEqual(link.refused, 1, "the next one goes straight out reliably")
        XCTAssertEqual(link.transportModes.last { $0.kind == "snapshot" }?.reliable, true)
    }
    func testASmallUnreliableMessageIsNeverBlamedOnSize() throws {
        let p = try party(2); defer { p.close() }; try start(p)
        let link = p.bus.links["a"]!
        link.refuseUnreliableOver = 100   // refuses even a small snapshot
        let packet = MultiplayerPacket(lobbyID: p.host.lobby!.id, matchID: p.host.lobby!.matchID, sender: "a", kind: "snapshot", reliable: false, payload: "{}")
        p.runtimes[0].outgoing.append(String(decoding: try JSONEncoder().encode(packet), as: UTF8.self))
        p.host.update()
        XCTAssertEqual(link.refused, 1)
        XCTAssertFalse(link.transportModes.contains { $0.kind == "snapshot" }, "a small message that fails is some other problem: it is not silently resent")
        XCTAssertNotNil(p.host.lastError)
    }
    /// Versus tennis' unreliable "peer" packets are its 30 Hz poses: a refused one is dropped, and the kind is never switched to reliable
    /// (that would queue every later pose behind any lost packet for the rest of the match). Its reliable events still go reliably.
    func testARefusedVersusPoseIsDroppedAndThePeerKindStaysUnreliable() throws {
        let p = try party(2); defer { p.close() }; try start(p)
        let link = p.bus.links["a"]!
        link.refuseUnreliableOver = 100
        func relay(_ payload: String, reliable: Bool) throws {
            let packet = MultiplayerPacket(lobbyID: p.host.lobby!.id, matchID: p.host.lobby!.matchID, sender: "a", kind: "peer", reliable: reliable, payload: payload)
            p.runtimes[0].outgoing.append(String(decoding: try JSONEncoder().encode(packet), as: UTF8.self))
            p.host.update()
        }
        try relay(String(repeating: "x", count: 1200), reliable: false)
        XCTAssertEqual(link.refused, 1)
        XCTAssertFalse(link.transportModes.contains { $0.kind == "peer" }, "the refused pose is dropped, not resent reliably")
        XCTAssertNil(p.host.lastError)
        link.refuseUnreliableOver = nil
        try relay("P|0|3|105.1234|0.5|-11.4|0|0|0|0|-1|0", reliable: false)
        XCTAssertEqual(link.transportModes.last { $0.kind == "peer" }?.reliable, false, "the next pose still goes unreliably")
        try relay("{\"k\":\"hit\"}", reliable: true)
        XCTAssertEqual(link.transportModes.last { $0.kind == "peer" }?.reliable, true)
    }
    /// The compact pose (Unity's VersusWire) on the wire as this app sends it, with real-length ids, stays far below the size Apple may
    /// refuse unreliably.
    func testAVersusPosePacketIsSmall() throws {
        let gameCenterID = "T:_" + String(repeating: "a", count: 32)
        let pose = "P|1|123|12345.6789|-3.142|-11.875|-4.25|1.5|0.875|2.375|0.42|13"
        let packet = MultiplayerPacket(lobbyID: UUID().uuidString, matchID: UUID().uuidString, sender: gameCenterID, sequence: 123456, kind: "peer", reliable: false, sentAt: 12345.678901, payload: pose)
        let bytes = try JSONEncoder().encode(packet).count
        XCTAssertLessThan(pose.utf8.count, 100)
        XCTAssertLessThan(bytes, 400, "a pose packet is \(bytes) bytes")
        XCTAssertLessThan(bytes, MultiplayerTuning.unreliableSafeBytes / 2)
    }

    // MARK: The Swift → Unity bridge must not fill up while no match is running

    /// The native queue behind `SportsRuntime.pushNetwork` (Unity/Assets/Plugins/iOS/SportsBridge.mm, `networkPush`), drained by Unity
    /// only while a match is configured and cleared at each match launch. Past 128 entries an unreliable packet evicts the oldest
    /// unreliable one (or is dropped itself); reliable packets grow the queue to 1024, and only past that is the oldest lost (reported
    /// as `bridgeError`, which is logged). It never refuses a match's packet. (work/tennis-online-resilience/bridge_test.cpp runs the
    /// real C++ against the same rules.)
    // MARK: P3: Nearby tennis made convenient (PLAN_Tennis_Latency_Online_Local §3)

    /// The menu's "Tennis with a friend nearby" hosts a tennis game (one action, no walking); the friend's phone, browsing in the
    /// background on its menu, offers "Join Adnan's tennis game?" and one tap joins. The match then starts by itself on both phones.
    func testOneMenuActionHostsAndTheBannerJoinsInOneTap() throws {
        let saved = SportsSession.shared.displayConnected; SportsSession.shared.displayConnected = true
        let savedContext = ClubHub.shared.context; ClubHub.shared.context = { ClubHubContext() }
        TennisMenu.shared.debugShow(.main); OnboardingFlow.shared.exitToMenu()
        let bus = Bus(), hostRuntime = Runtime(), guestRuntime = Runtime()
        let hostService = hostRuntime.service(), guestService = guestRuntime.service()
        hostService.requiresStableLink = false; guestService.requiresStableLink = false
        let host = HubSession(), guest = HubSession()
        host.partyService = hostService; guest.partyService = guestService
        defer { hostService.leave(); guestService.leave(); ClubHub.shared.context = savedContext; HubTestState.restore(display: saved); withExtendedLifetime(bus) {} }
        host.debugLive(session: "h"); guest.debugLive(session: "g")   // (whatever menu is up: the nearby flow does not use the Plaza)
        var browsing: [Bool] = []
        host.nearbyBrowse = { _, _ in XCTFail("a hosting phone does not browse") }
        guest.nearbyBrowse = { _, on in browsing.append(on) }
        host.nearbyHost = { hub in try hub.partyService.host(using: bus.link("host"), quick: .tennis) }
        guest.nearbyJoin = { hub, _ in try hub.partyService.connect(using: bus.link("guest"), quick: .tennis) }

        host.useNearbyBench()   // the phone menu's Play › "Tennis with a friend nearby", or the pointer menu's Tennis › Nearby: 1 action
        XCTAssertEqual(host.station, HubSession.nearbyBay, "its panel shows (SportsHome)")
        XCTAssertTrue(host.nearbyHosting)
        XCTAssertEqual(hostService.lobby?.sport, .tennis)
        XCTAssertEqual(hostService.lobby?.participants.first?.ready, true, "the host is ready at once")
        host.evaluate(); host.nearbyTick()
        XCTAssertEqual(host.station, HubSession.nearbyBay, "not a menu screen evaluate would close")
        XCTAssertTrue(host.nearbyHosting)

        guest.nearbyTick()
        XCTAssertEqual(browsing, [true], "a free phone on the menu looks for nearby games in the background (no Plaza needed)")
        XCTAssertNil(guest.nearbyOffer)
        let found = LocalMultiplayerTransport.DiscoveredLobby(id: LocalMultiplayerTransport.advertisedName("Adnan", token: UUID().uuidString), name: "Adnan",
                                                             endpoint: .hostPort(host: "127.0.0.1", port: 9), sport: "tennis", players: 1)
        guestService.debugSetDiscovered([found])
        XCTAssertEqual(guest.nearbyOffer?.name, "Adnan", "the banner: Join Adnan's tennis game?")

        guest.joinNearby()   // the banner's Join: 1 tap
        XCTAssertNotNil(guestService.lobby, "joined the host's lobby")
        XCTAssertEqual(hostService.lobby?.participants.count, 2)
        XCTAssertEqual(hostRuntime.configurations.count, 1, "the host's quick lobby started the match as soon as the friend was in")
        XCTAssertEqual(guestRuntime.configurations.count, 1)
        guest.nearbyTick()
        XCTAssertNil(guest.nearbyJoining)
        XCTAssertTrue(guest.notice.contains("Adnan"), guest.notice)
        XCTAssertFalse(guest.wantsNearbyBrowse, "no background browse while in a lobby")
        XCTAssertNil(guest.nearbyOffer)
        XCTAssertEqual(browsing, [true], "joining ends the browse itself (no second call that could drop the new connection)")
        XCTAssertTrue(TennisMenu.shared.rows(.party).contains(["partyNearbyTennis"]), "the phone menu's Play list has the one-tap row")
        XCTAssertNotNil(HubSession.route(HubSession.nearbyBay), "the pointer menu opens the same station id")
    }

    /// ✕ hides that game only; a phone that could not join now (a match, loading, onboarding: ClubHub.canJoinNow, the invite rule)
    /// neither browses nor offers; cancelling the hosted game before a match ends it; a friends' party is never broken up by it.
    func testNearbyBannerDismissBusyPhonesAndCancelling() throws {
        let saved = SportsSession.shared.displayConnected; SportsSession.shared.displayConnected = true
        let savedContext = ClubHub.shared.context
        var context = ClubHubContext(); ClubHub.shared.context = { context }
        TennisMenu.shared.debugShow(.main); OnboardingFlow.shared.exitToMenu()
        let bus = Bus(), partyBus = Bus(), runtime = Runtime(), service = runtime.service(), friend = Runtime().service()
        let hub = HubSession(); hub.partyService = service
        // (the buses outlive every leave: their links hold them unowned)
        defer { friend.leave(); service.leave(); ClubHub.shared.context = savedContext; HubTestState.restore(display: saved); withExtendedLifetime((bus, partyBus)) {} }
        hub.debugLive(session: "n")
        var browsing: [Bool] = []
        hub.nearbyBrowse = { _, on in browsing.append(on) }
        hub.nearbyHost = { hub in try hub.partyService.host(using: bus.link("me"), quick: .tennis) }
        func lobby(_ name: String, players: Int = 1, sport: String = "tennis") -> LocalMultiplayerTransport.DiscoveredLobby {
            .init(id: LocalMultiplayerTransport.advertisedName(name, token: UUID().uuidString), name: name, endpoint: .hostPort(host: "127.0.0.1", port: 9), sport: sport, players: players)
        }
        let sam = lobby("Sam")
        service.debugSetDiscovered([lobby("Golfer", sport: "golf"), lobby("Full", players: 2), sam])
        XCTAssertEqual(hub.nearbyOffer?.name, "Sam", "only a tennis game with room is offered")
        hub.dismissNearby()
        XCTAssertNil(hub.nearbyOffer)
        service.debugSetDiscovered([sam, lobby("Sam")])
        XCTAssertEqual(hub.nearbyOffer?.name, "Sam", "a new game from the same phone is offered again")

        hub.nearbyTick(); XCTAssertEqual(browsing, [true])
        context.busyLoading = true
        hub.nearbyTick(); XCTAssertEqual(browsing, [true, false], "not joinable now (loading): the browse pauses")
        XCTAssertNil(hub.nearbyOffer, "and nothing is offered")
        context.busyLoading = false; context.onboarding = true
        hub.nearbyTick(); XCTAssertEqual(browsing, [true, false]); XCTAssertNil(hub.nearbyOffer)
        context.onboarding = false
        hub.nearbyTick(); XCTAssertEqual(browsing, [true, false, true])

        hub.useNearbyBench()
        XCTAssertEqual(browsing, [true, false, true, false], "hosting stops the browse first")
        XCTAssertTrue(hub.nearbyHosting); XCTAssertNotNil(service.lobby)
        XCTAssertNil(hub.nearbyOffer, "a hosting phone is not offered games")
        hub.leaveStation()   // the panel's Cancel
        XCTAssertFalse(hub.nearbyHosting); XCTAssertNil(service.lobby, "cancelling ends the game before a match")
        XCTAssertNil(hub.station)
        hub.nearbyTick(); XCTAssertEqual(browsing.last, true, "and the phone is free to find games again")

        // in a friends' party (another phone in the lobby) the nearby game is refused, and the party stays
        try service.host(using: partyBus.link("me2")); try friend.connect(using: partyBus.link("friend"))
        XCTAssertTrue(hub.soloLocked)
        hub.useNearbyBench()
        XCTAssertFalse(hub.nearbyHosting); XCTAssertNil(hub.station)
        XCTAssertEqual(hub.notice, HubSession.soloLockMessage)
        XCTAssertEqual(service.lobby?.participants.count, 2, "the party is not broken up")
    }

    /// Nearby over real sockets on this machine (loopback): the 30 Hz pose and other unreliable packets go as UDP datagrams, the
    /// rest over TCP; after the TCP connection breaks mid-match the guest dials again (§6's 30 s hold) and datagrams flow again.
    func testNearbyPosesTravelAsDatagramsAndSurviveAReconnect() async throws {
        let host = LocalMultiplayerTransport(), guest = LocalMultiplayerTransport()
        defer { host.disconnect(); guest.disconnect() }
        func until(_ seconds: Double, _ what: String, _ done: () -> Bool) async throws {
            let end = Date().addingTimeInterval(seconds)
            while !done() { guard Date() < end else { XCTFail("timed out: \(what)"); throw CancellationError() }; try await Task.sleep(for: .milliseconds(20)) }
        }
        try host.host(name: "Adnan")
        try await until(5, "listeners ready") { host.debugPort != nil && host.debugUDPReady }
        let lobby = LocalMultiplayerTransport.DiscoveredLobby(id: LocalMultiplayerTransport.advertisedName("Adnan", token: host.debugToken), name: "Adnan",
                                                             endpoint: .hostPort(host: "127.0.0.1", port: NWEndpoint.Port(rawValue: host.debugPort!)!))
        var atHost: [String] = [], atGuest: [String] = []
        host.onData = { data, _ in atHost.append(String(decoding: data, as: UTF8.self)) }
        guest.onData = { data, _ in atGuest.append(String(decoding: data, as: UTF8.self)) }
        try guest.join(lobby)
        try await until(5, "connected") { host.peers.count == 1 && guest.peers.count == 1 }
        try await until(5, "datagrams both ways") { guest.debugDatagramsUp(host.localID) && host.debugDatagramsUp(guest.localID) }

        try guest.send(Data("pose-1".utf8), to: nil, reliable: false)
        try guest.send(Data("hit-1".utf8), to: nil, reliable: true)
        try host.send(Data("pose-back".utf8), to: nil, reliable: false)
        try await until(5, "delivered") { atHost.contains("pose-1") && atHost.contains("hit-1") && atGuest.contains("pose-back") }
        XCTAssertEqual(guest.datagramsSent, 1, "the pose went as a datagram, the hit did not")
        XCTAssertEqual(host.datagramsReceived, 1)
        XCTAssertEqual(host.datagramsSent, 1); XCTAssertEqual(guest.datagramsReceived, 1)
        try guest.send(Data(repeating: 65, count: LocalMultiplayerTransport.datagramLimit + 1), to: nil, reliable: false)
        XCTAssertEqual(guest.datagramsSent, 1, "an unreliable packet too big for one datagram goes over TCP")

        // mid-match the host's side of the connection breaks; the guest dials again and opens a fresh datagram flow
        guest.holdForReconnect = true
        var errors = 0; guest.onError = { _ in errors += 1 }
        host.debugDropConnections()
        try await until(3, "the break is noticed") { guest.peers.isEmpty }
        try await until(8, "reconnected") { host.peers.count == 1 && guest.peers.count == 1 }
        try await until(5, "datagrams again") { guest.debugDatagramsUp(host.localID) && host.debugDatagramsUp(guest.localID) }
        XCTAssertEqual(errors, 0, "a reconnect within the hold is not an error")
        try guest.send(Data("pose-2".utf8), to: nil, reliable: false)
        try await until(5, "pose after reconnect") { atHost.contains("pose-2") }
        XCTAssertEqual(guest.datagramsSent, 2)
    }

    @MainActor final class BridgeModel {
        var queue: [String] = []
        var refused = 0, dropped = 0, clears = 0
        /// Every packet the queue accepted.
        var pushed: [MultiplayerPacket] = []
        func push(_ text: String) -> Bool {
            let unreliable = text.contains("\"reliable\":false")
            if queue.count >= 128 {
                if let oldest = queue.firstIndex(where: { $0.contains("\"reliable\":false") }) { queue.remove(at: oldest) }
                else if unreliable { dropped += 1; return true }
                else if queue.count >= 1024 { dropped += 1; queue.removeFirst() }
            }
            queue.append(text)
            if let packet = try? JSONDecoder().decode(MultiplayerPacket.self, from: Data(text.utf8)) { pushed.append(packet) }
            return true
        }
        func clear() { queue.removeAll(); clears += 1 }
    }
    /// A full bridge holding only reliable packets (Unity stalled mid-match) no longer refuses, and a match launch starts it empty.
    func testABridgeFullOfReliablePacketsKeepsTheMatchAndALaunchClearsIt() throws {
        let bus = Bus(), hostRuntime = Runtime(), guestRuntime = Runtime(), bridge = BridgeModel()
        let host = hostRuntime.service()
        let guest = MultiplayerService(sendToRuntime: { bridge.push($0) }, pollRuntime: { nil }, clearRuntime: { bridge.clear() }, clock: { guestRuntime.time })
        guest.onMatchRequested = { guestRuntime.configurations.append($0) }; guest.onReturnToLobby = {}
        host.requiresStableLink = false; guest.requiresStableLink = false
        host.setScreen(true); guest.setScreen(true)
        try host.host(using: bus.link("a")); try guest.connect(using: bus.link("b"))
        let party = Party(bus: bus, services: [host, guest], runtimes: [hostRuntime, guestRuntime])
        defer { party.close() }
        for n in 0..<200 { _ = bridge.push("{\"kind\":\"stale\",\"reliable\":true,\"n\":\(n)}") }
        try start(party)
        XCTAssertGreaterThanOrEqual(bridge.clears, 1, "the launch emptied the bridge of the last match's packets")
        XCTAssertFalse(bridge.queue.contains { $0.contains("stale") })
        for n in 0..<300 { XCTAssertTrue(bridge.push("{\"kind\":\"peer\",\"reliable\":true,\"n\":\(n)}")) }
        for _ in 0..<50 { guestRuntime.time += 0.1; hostRuntime.time += 0.1; host.update(); guest.update() }
        XCTAssertEqual(bridge.refused, 0); XCTAssertNil(guest.lastError); XCTAssertEqual(guest.lobby?.phase, .playing)
    }

    /// A guest that waits in the lobby: every pong used to put a reliable `clock` packet in a queue that nothing reads between matches,
    /// and after 128 of them (64 s at two pongs a second) the next match's first packet was refused and the guest ejected itself.
    func testAGuestWaitingInTheLobbyDoesNotFillTheUnityBridgeAndStillJoinsTheNextMatch() throws {
        let bus = Bus(), hostRuntime = Runtime(), guestRuntime = Runtime(), bridge = BridgeModel()
        let host = hostRuntime.service()
        let guest = MultiplayerService(sendToRuntime: { bridge.push($0) }, pollRuntime: { nil }, clock: { guestRuntime.time })
        guest.onMatchRequested = { guestRuntime.configurations.append($0) }; guest.onReturnToLobby = {}
        host.requiresStableLink = false; guest.requiresStableLink = false
        host.setScreen(true); guest.setScreen(true)
        try host.host(using: bus.link("a")); try guest.connect(using: bus.link("b"))
        let party = Party(bus: bus, services: [host, guest], runtimes: [hostRuntime, guestRuntime])
        defer { party.close() }

        // Three minutes in the lobby, in 0.1 s steps: the guest pings the owner twice a second and each ping is answered.
        for _ in 0..<1800 { hostRuntime.time += 0.1; guestRuntime.time += 0.1; host.update(); guest.update() }
        XCTAssertGreaterThan(bus.links["a"]!.sent.filter { $0.kind == "pong" }.count, 300, "the lobby really did exchange a pong every half second")
        XCTAssertEqual(bridge.refused, 0)
        XCTAssertLessThan(bridge.queue.count, 128, "nothing reads the bridge between matches, so nothing may be put in it")
        XCTAssertTrue(bridge.pushed.filter { $0.kind == "clock" }.isEmpty, "the shared clock is only worth sending to Unity once a match is configured")

        try start(party)
        XCTAssertEqual(guest.lobby?.phase, .playing, "the guest takes part in the match that the owner started")
        XCTAssertNil(guest.lastError)
        XCTAssertEqual(bridge.refused, 0)
        XCTAssertTrue(bridge.pushed.contains { $0.kind == "run" }, "...and Unity was handed the match")

        // During the match the clock does reach Unity, as a packet the bridge may evict rather than one that can jam it.
        for _ in 0..<50 { hostRuntime.time += 0.1; guestRuntime.time += 0.1; host.update(); guest.update() }
        let clocks = bridge.pushed.filter { $0.kind == "clock" }
        XCTAssertFalse(clocks.isEmpty)
        XCTAssertTrue(clocks.allSatisfy { !$0.reliable })
        XCTAssertEqual(bridge.refused, 0)
    }

    // MARK: Leaving the app (AwayPolicy)

    func testAwayPolicyOutcomes() {
        let limit = AwayPolicy.onlineLimit
        XCTAssertEqual(AwayPolicy.outcome(away: limit + 1, inOnlineMatch: false, inParty: false, droppedFromMatch: false), .stay, "on your own nothing is left")
        XCTAssertEqual(AwayPolicy.outcome(away: limit - 1, inOnlineMatch: true, inParty: true, droppedFromMatch: false), .stay)
        XCTAssertEqual(AwayPolicy.outcome(away: limit + 1, inOnlineMatch: true, inParty: true, droppedFromMatch: false), .leaveMatch)
        XCTAssertEqual(AwayPolicy.outcome(away: 30, inOnlineMatch: true, inParty: false, droppedFromMatch: true), .leaveMatch, "the host already gave the place up")
        // a party waits longer than a match: its phones meet again by themselves (the party link)
        XCTAssertEqual(AwayPolicy.outcome(away: limit + 1, inOnlineMatch: false, inParty: true, droppedFromMatch: false), .stay)
        XCTAssertEqual(AwayPolicy.outcome(away: AwayPolicy.partyLimit + 1, inOnlineMatch: false, inParty: true, droppedFromMatch: false), .leaveParty)
        XCTAssertTrue(AwayPolicy.notice(for: .leaveMatch).contains("3 minutes"))
        XCTAssertTrue(AwayPolicy.notice(for: .leaveParty).contains("10 minutes"))
    }
    func testAwayClockMeasuresOnlyRealAbsences() {
        let clock = AwayPolicy(); var t = Date(timeIntervalSince1970: 1000); clock.now = { t }
        XCTAssertEqual(clock.returned(), 0, "never left")
        clock.left(); t += 50; clock.left(); t += 10
        XCTAssertEqual(clock.returned(), 60, accuracy: 1e-9, "from the first time it left")
        XCTAssertEqual(clock.returned(), 0)
    }
}
