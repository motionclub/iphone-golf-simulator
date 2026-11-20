import XCTest
import SwiftUI
@testable import GolfArcade

/// The party in the menu, phone half, over an in-memory network: a friend's presence becomes a friend in the line-up in their
/// lobby look; the leader picks the party's game and taps Start, every other player taps Ready, and the match starts when the
/// last one has (2026-10-25); the host leaving an idle lobby hands it to the next phone; Leave game and Leave party.
/// (The walk-around Plaza's benches, Call party and follow-the-leader were removed 2026-11-15, and their tests with them.)
@MainActor
final class HubPartyTests: XCTestCase {
    @MainActor final class Bus {
        var links: [String: Link] = [:]
        /// Lose a packet (sender, kind) on its way.
        var drop: (String, String) -> Bool = { _, _ in false }
        func link(_ id: String) -> Link { let l = Link(id: id, bus: self); links[id] = l; return l }
    }
    final class Link: PartyTransport {
        let localID: String; unowned let bus: Bus
        var onData: ((Data, String) -> Void)?; var onPeersChanged: (() -> Void)?; var onError: ((Error) -> Void)?
        var peers: [String] { bus.links.keys.filter { $0 != localID }.sorted() }
        init(id: String, bus: Bus) { localID = id; self.bus = bus }
        func send(_ data: Data, to ids: [String]?, reliable: Bool) throws {
            let kind = (try? JSONDecoder().decode(MultiplayerPacket.self, from: data))?.kind ?? ""
            guard !bus.drop(localID, kind) else { return }
            for id in ids ?? peers { bus.links[id]?.onData?(data, localID) }
        }
        func disconnect() { bus.links.removeValue(forKey: localID); for link in bus.links.values.sorted(by: { $0.localID < $1.localID }) { link.onPeersChanged?() } }
    }
    private func service(_ name: String, shirt: String) -> MultiplayerService {
        let s = MultiplayerService(sendToRuntime: { _ in true }, pollRuntime: { nil }, clock: { 100 })
        s.onMatchRequested = { _ in }; s.onReturnToLobby = {}
        // every phone in the Plaza has a TV (the plaza only runs with one); the link-steadiness gate has its own MultiplayerTests
        s.setScreen(true); s.requiresStableLink = false
        s.setIdentity(name: name, female: name == "Bea", loadout: MultiplayerLoadout(skinHex: "C47A4C", colours: ["shirt": shirt], emotes: EmoteCatalog.defaults, shirtHex: shirt, shortsHex: "24345E"))
        return s
    }
    private func hub(_ s: MultiplayerService, _ session: String) -> HubSession {
        let h = HubSession(); h.partyService = s; h.debugLive(session: session); return h
    }
    private var savedDisplay = false
    override func setUp() async throws { savedDisplay = SportsSession.shared.displayConnected; SportsSession.shared.displayConnected = true; TennisMenu.shared.debugShow(.main); OnboardingFlow.shared.exitToMenu() }
    override func tearDown() async throws { HubTestState.restore(display: savedDisplay) }

    func testAFriendsPresenceBecomesAPlazaFriendInTheirLook() throws {
        let bus = Bus(), a = service("Ann", shirt: "E8505B"), b = service("Bea", shirt: "3F62CC")
        try a.host(using: bus.link("a")); try b.connect(using: bus.link("b"))
        defer { b.leave(); a.leave() }
        XCTAssertEqual(b.lobby?.participants.count, 2, "Bea joined Ann's lobby")
        let ha = hub(a, "ha"), hb = hub(b, "hb")
        var toUnity: [[String: Any]] = []; hb.debugSent = { toUnity.append($0) }
        ha.receive(["type": "hubPose", "session": "ha", "message": "plaza|1.000|0.000|2.000|90.0|1.20||"])
        let remote = toUnity.first { $0["action"] as? String == "hubRemote" }
        XCTAssertNotNil(remote, "Ann's pose reached Bea's plaza")
        let state = try JSONSerialization.jsonObject(with: Data((remote?["remote"] as? String ?? "").utf8)) as? [String: Any]
        XCTAssertEqual(state?["id"] as? String, "a"); XCTAssertEqual(state?["name"] as? String, "Ann")
        XCTAssertEqual(state?["shirt"] as? String, "E8505B", "in Ann's own shirt (LOOK)")
        XCTAssertEqual(state?["x"] as? Double, 1); XCTAssertEqual(state?["place"] as? String, "plaza")
        // the member list goes to Unity too; Ann leaving removes her
        hb.debugPartyTick()
        XCTAssertTrue(toUnity.contains { $0["action"] as? String == "hubRoster" && $0["mode"] as? String == "a" })
    }

    /// The leader's tools (2026-10-25): hand the crown to a member (their lobby is the party's from then on, and the party follows
    /// them), and take someone out (their phone leaves and says why, and is not invited back by itself).
    func testTheLeaderCanHandOverTheCrownAndTakeSomeoneOut() throws {
        let bus = Bus(), a = service("Ann", shirt: "E8505B"), b = service("Bea", shirt: "3F62CC"), c = service("Cy", shirt: "2FA36B")
        try a.host(using: bus.link("a")); try b.connect(using: bus.link("b")); try c.connect(using: bus.link("c"))
        defer { c.leave(); b.leave(); a.leave() }
        XCTAssertEqual(a.lobby?.participants.count, 3)
        XCTAssertThrowsError(try b.makeLeader("c"), "only the leader hands over the crown")
        XCTAssertThrowsError(try b.removeFromParty("c"), "only the leader takes someone out")
        try a.makeLeader("b")
        XCTAssertTrue(b.isOwner); XCTAssertFalse(a.isOwner)
        XCTAssertEqual(a.lobby?.ownerID, "b"); XCTAssertEqual(c.lobby?.ownerID, "b", "everyone follows the new leader")
        XCTAssertEqual(b.lastError, "You're the party leader now.")
        XCTAssertThrowsError(try a.removeFromParty("c"), "the old leader has no leader tools any more")
        try b.removeFromParty("c")
        XCTAssertNil(c.lobby, "Cy's phone left the party"); XCTAssertEqual(c.lastError, "Bea took you out of the party.")
        XCTAssertEqual(b.lobby?.participants.map(\.id).sorted(), ["a", "b"]); XCTAssertEqual(a.lobby?.participants.map(\.id).sorted(), ["a", "b"])
    }

    /// The party's game from the menu: the leader's station sets the sport, everyone connected is in (no benches to sit on), the
    /// settings reach every phone, only the leader starts, Start asks everyone to get ready, and the last Ready starts the match.
    func testThePartyGameStartsWhenTheLastPlayerTapsReady() throws {
        let bus = Bus(), a = service("Ann", shirt: "E8505B"), b = service("Bea", shirt: "3F62CC")
        try a.host(using: bus.link("a")); try b.connect(using: bus.link("b"))
        defer { b.leave(); a.leave() }
        let ha = hub(a, "ha"), hb = hub(b, "hb")
        ha.receive(["type": "menuOpen", "session": "ha", "message": "bay-tennis-online"])   // Online, picked on the TV's menu
        XCTAssertEqual(ha.station, "bay-tennis-online"); XCTAssertEqual(a.lobby?.sport, .tennis)
        ha.debugPartyTick()   // seats: everyone connected; settings and Start belong to the leader
        ha.debugPartyTick()
        XCTAssertEqual(Set(a.lobby?.participants.filter { $0.seat >= 0 }.map(\.id) ?? []), ["a", "b"], "everyone connected is in")
        XCTAssertEqual(a.lobby?.phase, .lobby, "opening the party's game never starts it")
        ha.configureParty(venue: "volcano", sets: 3, games: 6)
        XCTAssertEqual(b.lobby?.venue, "volcano"); XCTAssertEqual(b.lobby?.sets, 1, "an online game is always one set"); XCTAssertEqual(b.lobby?.games, 6)
        hb.forcePartyStart(); XCTAssertEqual(a.lobby?.phase, .lobby, "a guest cannot start"); XCTAssertFalse(b.partyReadyCheck)
        ha.forcePartyStart()
        XCTAssertEqual(a.lobby?.phase, .lobby, "Start asks everyone to get ready; it never starts by itself")
        XCTAssertTrue(b.partyReadyCheck, "Bea's phone shows Ready"); XCTAssertEqual(b.lobby?.participants.first { $0.id == "a" }?.ready, true)
        hb.setPartyReady(true)
        XCTAssertEqual(a.lobby?.phase, .loading, "the last Ready starts the match")
        XCTAssertEqual(b.lobby?.phase, .loading)
        XCTAssertEqual(Set(a.lobby?.competitors.map(\.id) ?? []), ["a", "b"])
    }

    /// A full party of four. Online tennis is 1 v 1, so four friends play golf: the leader's station makes it golf, everyone connected
    /// is in, and one match starts on all four phones.
    func testFourFriendsStartOneGolfMatchFromTheMenu() throws {
        let bus = Bus(), bay = "bay-golf-online"
        let ids = ["a", "b", "c", "d"], names = ["Ann", "Bea", "Cal", "Dee"], shirts = ["E8505B", "3F62CC", "2FA36B", "F2B233"]
        let services = ids.indices.map { service(names[$0], shirt: shirts[$0]) }
        var configs: [String: MultiplayerMatchConfiguration] = [:]
        for (i, s) in services.enumerated() { let id = ids[i]; s.onMatchRequested = { configs[id] = $0 } }
        try services[0].host(using: bus.link("a"))
        for i in 1..<4 { try services[i].connect(using: bus.link(ids[i])) }
        defer { for s in services.reversed() { s.leave() } }
        XCTAssertEqual(services[0].lobby?.participants.count, 4)
        let hubs = ids.indices.map { hub(services[$0], "h" + ids[$0]) }
        hubs[0].receive(["type": "menuOpen", "session": "ha", "message": bay])
        XCTAssertEqual(services[0].lobby?.sport, .golf, "the leader's station sets the party's sport")
        hubs[0].debugPartyTick(); hubs[0].debugPartyTick()
        XCTAssertEqual(services[0].lobby?.participants.filter { $0.seat >= 0 }.count, 4, "everyone connected is in: the menu has no benches")
        XCTAssertEqual(services[0].lobby?.phase, .lobby, "nothing starts before the leader's Start")
        hubs[0].forcePartyStart()
        XCTAssertEqual(services[0].lobby?.phase, .lobby, "waiting for three Readys")
        for i in 1..<4 { hubs[i].setPartyReady(true) }
        XCTAssertEqual(services[0].lobby?.phase, .loading, "the last Ready starts the match")
        XCTAssertEqual(configs["a"]?.sport, "golf", "the golf station plays golf")
        XCTAssertEqual(configs.count, 4, "all four phones were asked to load")
        XCTAssertEqual(Set(configs.values.map(\.matchID)).count, 1, "the same match for everyone")
        // every phone's launch is made from its menu (the leader's from the station it opened), and remembered for the way back
        for (i, h) in hubs.enumerated() {
            XCTAssertEqual(h.bayForLaunch(), i == 0 ? bay : "menu")
            h.runtimeTaken(bay: h.bayForLaunch()); h.sessionEnded(finished: true)
            XCTAssertEqual(h.returnBay, i == 0 ? bay : "menu", "back from the match the menu opens on Home")
        }
    }

    /// Joining a friend's party closes whatever station was open on this phone; the party's chat goes to the TV.
    func testJoiningAPartyClosesTheOpenStationAndChatReachesTheTV() throws {
        let bus = Bus(), a = service("Ann", shirt: "E8505B"), b = service("Bea", shirt: "3F62CC")
        try a.host(using: bus.link("a")); try b.connect(using: bus.link("b"))
        defer { b.leave(); a.leave() }
        let hb = hub(b, "hb")
        var commands: [[String: Any]] = []; hb.debugSent = { commands.append($0) }
        hb.useStation("desk-settings"); XCTAssertNotNil(hb.station)
        hb.joinedParty(host: "a")
        XCTAssertNil(hb.station); XCTAssertFalse(hb.panelOpen)
        XCTAssertEqual(hb.phase, .live)
        hb.showChat(PartyChatMessage(senderID: "a", senderName: "Ann", text: "meet here!", date: Date()))
        XCTAssertTrue(commands.contains { $0["action"] as? String == "hubChat" && $0["remote"] as? String == "a" && $0["mode"] as? String == "meet here!" })
    }

    /// INVITE: every Invite (the TV menu's Friends entry, the Friends button) opens the Friends list (a sheet over the controller)
    /// and nothing else: no Game Center sheet, no old menu screen on the phone; the TV's menu is not left dimmed.
    func testInviteInThePlazaOpensTheHubAndNoMenuScreen() {
        let hub = HubSession.shared, menu = TennisMenu.shared
        hub.debugReset(); menu.debugShow(.main); hub.debugLive(session: "inv")
        var invites = 0; hub.presentInvite = { invites += 1 }
        var toUnity: [[String: Any]] = []; hub.debugSent = { toUnity.append($0) }
        hub.receive(["type": "menuOpen", "session": "inv", "message": "board-invite"])
        XCTAssertEqual(invites, 1, "the TV menu's Friends entry opens the Friends hub")
        XCTAssertEqual(menu.screen, .main, "no menu screen opens on the phone"); XCTAssertFalse(hub.panelOpen); XCTAssertNil(hub.station)
        XCTAssertTrue(toUnity.contains { $0["action"] as? String == "menuPhone" && $0["mode"] as? String == "off" }, "no station stays open: the TV's menu is live")
        hub.inviteFriends()
        XCTAssertEqual(invites, 2, "Friends button: the hub at once")
        menu.tap("homeInvite")
        XCTAssertEqual(invites, 3, "the menu's Play with Friends opens the same hub")
        XCTAssertEqual(menu.screen, .main)
    }

    /// JOIN: a friend connecting (or any lobby change) leaves both phones in the Plaza, also mid-station, with a TV or without.
    func testAFriendJoiningKeepsBothPhonesInThePlaza() throws {
        let bus = Bus(), a = service("Ann", shirt: "E8505B"), b = service("Bea", shirt: "3F62CC")
        let hub = HubSession.shared, menu = TennisMenu.shared
        hub.debugReset(); menu.debugShow(.main); hub.debugLive(session: "join")
        XCTAssertTrue(hub.drivesPhone)
        try a.host(using: bus.link("a")); try b.connect(using: bus.link("b"))
        defer { b.leave(); a.leave() }
        XCTAssertEqual(b.lobby?.participants.count, 2)
        for s in [a, b] { OnlineLobbyMenu(service: s).sync(menu) }
        XCTAssertEqual(menu.screen, .main, "in the plaza with your friend: no lobby screen")
        menu.debugShow(.character); OnlineLobbyMenu(service: b).sync(menu)
        XCTAssertEqual(menu.screen, .character, "a friend joining does not pull you out of the locker")
        SportsSession.shared.displayConnected = false; menu.debugShow(.main); OnlineLobbyMenu(service: b).sync(menu)
        XCTAssertEqual(menu.screen, .main, "no TV: the plaza is on the phone, still no lobby screen")
        menu.debugShow(.online(.lobby)); OnlineLobbyMenu(service: b).sync(menu)
        XCTAssertEqual(menu.screen, .main, "a lobby screen left over from an old path is closed")
    }

    /// Leaving a two-player party game (Leave game, or Back to the Plaza after it) brings the whole party back to the Plaza: nobody is
    /// left to play on. Never a lobby screen.
    func testBackToThePlazaFromAPartyMatchBringsEveryoneBack() throws {
        let bus = Bus(), a = service("Ann", shirt: "E8505B"), b = service("Bea", shirt: "3F62CC")
        var back = 0; a.onReturnToLobby = { back += 1 }; b.onReturnToLobby = { back += 1 }
        try a.host(using: bus.link("a")); try b.connect(using: bus.link("b"))
        defer { b.leave(); a.leave() }
        try a.configure(.tennis); try a.startPartyGame(); try b.setReady(true)
        XCTAssertEqual(b.lobby?.phase, .loading)
        b.leaveGame()   // a guest's Leave game mid-load
        XCTAssertEqual(a.lobby?.phase, .lobby, "the host brought everyone back"); XCTAssertEqual(b.lobby?.phase, .lobby)
        XCTAssertGreaterThanOrEqual(back, 2, "every phone's match stopped")
        XCTAssertEqual(a.lobby?.participants.count, 2, "the party is still together")
    }

    func testSoloStationsAreLockedUntilTheFriendLeavesAndStartWaitsForReady() throws {
        let bus = Bus(), a = service("Ann", shirt: "E8505B"), b = service("Bea", shirt: "3F62CC")
        try a.host(using: bus.link("a")); try b.connect(using: bus.link("b"))
        defer { a.leave() }
        let ha = hub(a, "ha")
        XCTAssertTrue(ha.soloLocked)
        for station in HubSession.soloStations {
            ha.useStation(station)
            XCTAssertNil(ha.station)
            XCTAssertEqual(ha.notice, HubSession.soloLockMessage)
        }
        ha.useStation("bay-tennis-online"); ha.forcePartyStart()
        XCTAssertEqual(a.lobby?.phase, .lobby, "nobody is pulled into play: the friend taps Ready first")
        b.leave()
        XCTAssertFalse(ha.soloLocked, "leaving the party restores single player")
    }

    func testThePartyGamePanelsRender() async throws {
        let bus = Bus(), a = service("Ann", shirt: "E8505B"), b = service("Bea", shirt: "3F62CC")
        try a.host(using: bus.link("a")); try b.connect(using: bus.link("b"))
        defer { b.leave(); a.leave() }
        let ha = hub(a, "ha"), hb = hub(b, "hb")
        ha.useStation("bay-tennis-online"); hb.useStation("bay-tennis-online")
        ha.debugPartyTick(); ha.configureParty(venue: "volcano", sets: 3, games: 6)
        XCTAssertEqual(a.lobby?.phase, .lobby)
        guard let dir = ProcessInfo.processInfo.environment["MENU_SNAP_DIR"] else { return }
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        func shoot(_ name: String, _ h: HubSession, _ width: Double, _ height: Double) async throws {
            let controller = UIHostingController(rootView: HubPartyBayPanel(hub: h))
            let window = UIWindow(windowScene: scene)
            window.frame = CGRect(x: 0, y: 0, width: width, height: height)
            window.rootViewController = controller; window.isHidden = false
            controller.view.frame = window.bounds; controller.view.layoutIfNeeded()
            try await Task.sleep(for: .seconds(0.3))
            let image = UIGraphicsImageRenderer(size: window.bounds.size).image { _ in controller.view.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
            try XCTUnwrap(image.pngData()).write(to: URL(fileURLWithPath: dir).appendingPathComponent(name + ".png"))
            window.isHidden = true
        }
        try await shoot("party-leader-pick", ha, 402, 874); try await shoot("party-leader-small-phone", ha, 375, 667)
        ha.forcePartyStart()
        try await shoot("party-friend-ready", hb, 402, 874); try await shoot("party-leader-waiting", ha, 402, 874)
        hb.setPartyReady(true)
        XCTAssertEqual(a.lobby?.phase, .loading)
    }

    func testTheHostLeavingAnIdleLobbyHandsItOver() throws {
        let bus = Bus(), a = service("Ann", shirt: "E8505B"), b = service("Bea", shirt: "3F62CC"), c = service("Cy", shirt: "7BDA4A")
        try a.host(using: bus.link("a")); try b.connect(using: bus.link("b")); try c.connect(using: bus.link("c"))
        defer { c.leave(); b.leave() }
        XCTAssertEqual(c.lobby?.participants.count, 3)
        a.leave()
        XCTAssertTrue(b.isOwner, "the next phone (lowest id) is the host now")
        XCTAssertEqual(c.lobby?.ownerID, "b"); XCTAssertEqual(c.lobby?.phase, .lobby, "the party carries on")
        XCTAssertFalse(c.lobby?.participants.contains { $0.id == "a" } ?? true)
    }

    // MARK: 2026-10-25: friends who joined never showed up, and Play acted as if you were alone

    /// The friend's first hello went out before the connection to the host was up, and the host's lobby (with only the host in it)
    /// reached the friend first. The friend used to stop saying hello once it had any lobby, so the host never listed them and
    /// neither phone saw the other. Now it keeps saying hello until the lobby lists it, and the host keeps sending its lobby to a
    /// connected phone it does not list.
    func testAFriendWhoseFirstHelloWasLostStillEndsUpInTheLobby() throws {
        var t = 100.0
        let bus = Bus()
        func timed(_ name: String) -> MultiplayerService {
            let s = MultiplayerService(sendToRuntime: { _ in true }, pollRuntime: { nil }, clock: { t })
            s.onMatchRequested = { _ in }; s.onReturnToLobby = {}; s.setScreen(true); s.requiresStableLink = false
            s.setIdentity(name: name); return s
        }
        let a = timed("Ann"), b = timed("Bea")
        try a.host(using: bus.link("a"))
        let lb = bus.link("b")
        var lost = 1
        // Bea's first hello is lost on its way to Ann
        bus.drop = { from, kind in if from == "b", kind == "hello", lost > 0 { lost -= 1; return true }; return false }
        try b.connect(using: lb)
        defer { b.leave(); a.leave() }
        XCTAssertEqual(a.joiningPeers, 1, "Ann's phone is connected to Bea's but does not list her yet")
        // Ann's lobby (only Ann) reaches Bea
        a.update(); t += 1.1; a.update()
        XCTAssertEqual(b.lobby?.ownerID, "a", "Bea has Ann's lobby")
        t += 1.1; b.update()
        XCTAssertEqual(a.lobby?.participants.map(\.id).sorted(), ["a", "b"], "Bea's next hello got her in")
        XCTAssertEqual(b.lobby?.participants.map(\.id).sorted(), ["a", "b"], "and both phones see both")
        XCTAssertEqual(a.joiningPeers, 0)
    }

    /// The ready check from the friend's side: Not ready takes it back, and a friend who leaves during it ends it (back to choosing).
    func testTheReadyCheckWaitsForEveryoneAndEndsWhenTheFriendLeaves() throws {
        let bus = Bus(), a = service("Ann", shirt: "E8505B"), b = service("Bea", shirt: "3F62CC")
        try a.host(using: bus.link("a")); try b.connect(using: bus.link("b"))
        defer { a.leave() }
        let ha = hub(a, "ha"), hb = hub(b, "hb")
        XCTAssertThrowsError(try b.startPartyGame(), "only the leader starts")
        ha.forcePartyStart()
        XCTAssertTrue(a.partyReadyCheck); XCTAssertTrue(b.partyReadyCheck)
        hb.setPartyReady(true); XCTAssertEqual(a.lobby?.phase, .loading)
        try a.returnToLobby(rotateSeats: false)
        XCTAssertFalse(b.partyReadyCheck, "back from the match: the leader picks the next game")
        ha.forcePartyStart(); ha.cancelPartyGame()
        XCTAssertFalse(b.partyReadyCheck, "the leader cancelled"); XCTAssertEqual(b.lobby?.participants.first { $0.id == "b" }?.ready, false)
        ha.forcePartyStart(); XCTAssertTrue(b.partyReadyCheck)
        b.leave()
        XCTAssertFalse(a.partyReadyCheck, "the friend left: no game to wait for")
        XCTAssertEqual(a.lobby?.phase, .lobby)
    }

    /// Play online while a friend is still joining your party: never leaves the party for a quick match (it used to: the friend's
    /// phone was then alone too).
    func testPlayOnlineNeverLeavesAPartyAFriendIsJoining() throws {
        let bus = Bus(), a = service("Ann", shirt: "E8505B")
        try a.host(using: bus.link("a"))
        defer { a.leave() }
        bus.drop = { from, _ in from == "b" }   // Bea is connected, nothing of hers has arrived yet
        _ = bus.link("b")
        let ha = hub(a, "ha")
        XCTAssertEqual(a.joiningPeers, 1); XCTAssertNil(ha.party)
        ha.useStation("bay-tennis-online")
        XCTAssertEqual(ha.notice, HubSession.friendJoiningMessage)
        XCTAssertNil(ha.onlineBench, "no quick match"); XCTAssertNotNil(a.lobby, "still Ann's party")
    }

    // MARK: 2026-10-28: Leave game and Leave party

    /// A party where every phone counts its matches started and stopped, on a clock the test moves.
    private final class Counted { var launches = 0, stops = 0 }
    private func party(_ names: [String], bus: Bus, clock: @escaping @MainActor () -> Double) throws -> ([MultiplayerService], [Counted]) {
        var phones: [MultiplayerService] = [], counts: [Counted] = []
        for (i, name) in names.enumerated() {
            let s = MultiplayerService(sendToRuntime: { _ in true }, pollRuntime: { nil }, clock: clock), c = Counted()
            s.onMatchRequested = { (_: MultiplayerMatchConfiguration) in c.launches += 1 }; s.onReturnToLobby = { c.stops += 1 }
            s.setScreen(true); s.requiresStableLink = false; s.setIdentity(name: name)
            if i == 0 { try s.host(using: bus.link(String(name.prefix(1)).lowercased())) } else { try s.connect(using: bus.link(String(name.prefix(1)).lowercased())) }
            phones.append(s); counts.append(c)
        }
        return (phones, counts)
    }
    /// The leader starts `sport`, everyone taps Ready and loads: the game is on (golf plays at once; tennis sets up first).
    private func play(_ sport: MultiplayerSport, _ phones: [MultiplayerService]) throws {
        try phones[0].configure(sport); try phones[0].startPartyGame()
        for s in phones.dropFirst() { try s.setReady(true) }
        for s in phones { s.runtimeLoaded() }
    }

    /// Leave game from a two-player game: this phone is back in the Plaza at once and the game ends for both (nobody is left to play
    /// on); the party stays together, and the leader is told why.
    func testLeaveGameInATwoPlayerGameEndsItAndKeepsTheParty() throws {
        let bus = Bus(), (p, n) = try party(["Ann", "Bea"], bus: bus, clock: { 100 })
        let a = p[0], b = p[1]
        defer { b.leave(); a.leave() }
        try play(.tennis, p)
        XCTAssertEqual(a.lobby?.phase, .calibrating); XCTAssertEqual(n[1].launches, 1)
        b.leaveGame()
        XCTAssertGreaterThanOrEqual(n[1].stops, 1, "Bea's game stopped at once")
        XCTAssertEqual(a.lobby?.phase, .lobby, "nobody left to play: the game ended"); XCTAssertEqual(b.lobby?.phase, .lobby)
        XCTAssertGreaterThanOrEqual(n[0].stops, 1, "and on Ann's phone")
        XCTAssertEqual(a.lobby?.participants.map(\.id).sorted(), ["a", "b"], "still a party"); XCTAssertEqual(b.lobby?.ownerID, "a")
        XCTAssertEqual(a.lastError, "Bea left the game, so the game ended.")
        XCTAssertTrue(a.isParty && b.isParty)
    }

    /// A Leave game request lost on its way (a link healing) never keeps the phone in the game: it is already in the Plaza, it asks
    /// again each second until the leader lets it go, and the game it left never pulls it back in.
    func testALostLeaveGameRequestIsAskedAgainAndTheGameNeverTakesThePhoneBack() throws {
        var t = 100.0
        let bus = Bus(), (p, n) = try party(["Ann", "Bea"], bus: bus, clock: { t })
        let a = p[0], b = p[1]
        defer { b.leave(); a.leave() }
        try play(.tennis, p)
        var lost = 1
        bus.drop = { from, kind in if from == "b", kind == "return", lost > 0 { lost -= 1; return true }; return false }
        b.leaveGame()
        XCTAssertEqual(n[1].stops, 1, "Bea's game stopped at once"); XCTAssertEqual(a.lobby?.phase, .calibrating, "the request was lost")
        // Ann's phone sends the running game to a phone that says hello (as after a reconnect): Bea's never takes it
        bus.links["b"]?.onPeersChanged?()
        XCTAssertEqual(n[1].launches, 1, "the game Bea left did not start again on her phone")
        t += 1.1; b.update()
        XCTAssertEqual(a.lobby?.phase, .lobby, "asked again: the game ended"); XCTAssertEqual(b.lobby?.phase, .lobby)
        XCTAssertEqual(a.lobby?.participants.count, 2, "still a party")
        // the next game starts on Bea's phone as usual
        try play(.tennis, p)
        XCTAssertEqual(n[1].launches, 2)
    }

    /// Three playing golf: one leaving the game is out of it, and the other two play on (golf passes their turns). They stay in the
    /// party and are back with everyone when the game ends.
    func testInAThreePlayerGameTheOthersPlayOnWhenOneLeaves() throws {
        let bus = Bus(), (p, n) = try party(["Ann", "Bea", "Cy"], bus: bus, clock: { 100 })
        let a = p[0], b = p[1], c = p[2]
        defer { c.leave(); b.leave(); a.leave() }
        try play(.golf, p)
        XCTAssertEqual(a.lobby?.phase, .playing); XCTAssertEqual(a.lobby?.competitors.count, 3)
        c.leaveGame()
        XCTAssertEqual(n[2].stops, 1, "Cy is back in the Plaza")
        XCTAssertEqual(a.lobby?.phase, .playing, "Ann and Bea play on"); XCTAssertEqual(n[0].stops, 0); XCTAssertEqual(n[1].stops, 0)
        XCTAssertEqual(a.lobby?.competitors.map(\.id), ["a", "b"])
        XCTAssertEqual(a.lobby?.participants.first { $0.id == "c" }?.connected, true, "Cy is still in the party")
        XCTAssertEqual(b.lastError, "Cy left the game. The game goes on."); XCTAssertEqual(a.lastError, b.lastError)
        XCTAssertEqual(a.lobby?.participants.first { $0.id == "c" }?.status, .gone, "out of this game")
        try a.returnToLobby(rotateSeats: false)
        for s in p { XCTAssertEqual(s.lobby?.phase, .lobby); XCTAssertEqual(s.lobby?.participants.count, 3) }
    }

    /// Leave party in the middle of a game: the friend is out of the game and the party; with nobody left to play, the game ends and
    /// the leader is back in the Plaza with the rest of the party.
    func testAFriendLeavingThePartyMidGameEndsATwoPlayerGame() throws {
        let bus = Bus(), (p, n) = try party(["Ann", "Bea"], bus: bus, clock: { 100 })
        let a = p[0], b = p[1]
        defer { a.leave() }
        try play(.tennis, p)
        b.leave("left the party")
        XCTAssertNil(b.lobby)
        XCTAssertEqual(a.lobby?.phase, .lobby); XCTAssertGreaterThanOrEqual(n[0].stops, 1)
        XCTAssertEqual(a.lobby?.participants.map(\.id), ["a"])
        XCTAssertEqual(a.lastError, "Bea left the party, so the game ended.")
    }

    /// The leader leaving the party mid-game: the game it ran ends on every phone at once (nobody waits minutes for a leader who is
    /// not coming back), and the party goes on with the next leader.
    func testTheLeaderLeavingThePartyMidGameEndsItForTheOthersAtOnce() throws {
        let bus = Bus(), (p, n) = try party(["Ann", "Bea", "Cy"], bus: bus, clock: { 100 })
        let a = p[0], b = p[1], c = p[2]
        defer { c.leave(); b.leave() }
        try play(.golf, p)
        a.leave("left the party")
        for (s, count) in [(b, n[1]), (c, n[2])] {
            XCTAssertEqual(count.stops, 1, "the game ended"); XCTAssertEqual(s.lobby?.phase, .lobby); XCTAssertEqual(s.lobby?.ownerID, "b", "Bea leads now")
            XCTAssertEqual(s.lobby?.participants.map(\.id).sorted(), ["b", "c"])
        }
        XCTAssertEqual(c.lastError, "Ann left the party, so the game ended.")
        XCTAssertTrue(b.isOwner)
    }

    /// The leader ended the game but its "stop" never reached the guest (it was in the background, or the link was healing): the
    /// leader's next lobby says there is no game, and the guest's game ends too.
    func testAGuestThatMissedTheStopEndsItsGameWhenTheLobbySaysSo() throws {
        let bus = Bus(), (p, n) = try party(["Ann", "Bea"], bus: bus, clock: { 100 })
        let a = p[0], b = p[1]
        defer { b.leave(); a.leave() }
        try play(.tennis, p)
        bus.drop = { from, kind in from == "a" && kind == "stop" }
        try a.returnToLobby(rotateSeats: false)
        XCTAssertEqual(n[1].stops, 1, "the lobby ended Bea's game"); XCTAssertEqual(b.lobby?.phase, .lobby)
    }
}
