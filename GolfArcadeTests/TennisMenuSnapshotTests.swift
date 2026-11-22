import SwiftUI
import SceneKit
import AVFoundation
import XCTest
@testable import GolfArcade

/// Renders every tennis front-end screen to PNG (TV at 1280×720, phone at 402×874) so the
/// layouts can be reviewed without a TV attached. Output: $TMPDIR/tennis-menu/.
@MainActor
final class TennisMenuSnapshotTests: XCTestCase {
    /// Native production setup screens with explicit fixture sensor/network state. Physical sensors are checked on devices.
    func testOnlineCalibrationScreensAndFlow() async throws {
        let session = SportsSession.shared, service = MultiplayerService.shared
        let active = session.active, ready = session.ready, paused = session.paused
        let sport = session.sport, stage = session.setupStage, gate = session.axisGate
        defer {
            session.debugSetOnlineMatch(nil); service.leave()
            session.active = active; session.ready = ready; session.paused = paused; session.motion.fixtureSensors = false
            session.sport = sport; session.setupStage = stage; session.axisGate = gate; session.setupProblem = ""
            session.loading.cancel()
        }
        try service.enableMock(count: 2, player: Player(name: "You", colorIndex: 0))
        service.mockState(phase: .loading)
        session.active = true; session.ready = false; session.paused = true
        session.sport = "tennis"; session.debugSetOnlineMatch("ui-proof", seat: 0)
        session.loading.begin(now: LoadingModel.clockNow, multiplayer: true)
        session.setupStage = .scan; session.axisGate = SportsAxisGate()
        let phone = CGSize(width: 402, height: 874)
        let proof = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("proof/online-calibration")
        try FileManager.default.createDirectory(at: proof, withIntermediateDirectories: true)
        func capture<V: View>(_ view: V, _ name: String, _ size: CGSize) async throws {
            try await saveHosted(view, name, size, destination: proof)
        }
        try await capture(SportsHome(), "online-setup-direction-phone", phone)
        session.axisGate.progress = 0.6; session.axisGate.message = "Hold it there…"
        try await capture(TennisRacketController(session: session), "online-setup-hold-phone", phone)
        try await capture(TennisSetupTVView(session: session).frame(maxWidth: .infinity, maxHeight: .infinity).background(IslandUI.dark), "online-setup-direction-tv", CGSize(width: 1280, height: 720))
        session.axisGate.stalledFor = 5; session.axisGate.progress = 0
        session.setupProblem = "No camera frame yet. Keep the lens uncovered."
        try await capture(TennisRacketController(session: session), "online-setup-recovery-phone", phone)
        try await capture(TennisRacketController(session: session).environment(\.dynamicTypeSize, .xxxLarge), "online-setup-recovery-large-text", CGSize(width: 375, height: 812))
        session.setupStage = .ready; session.setupProblem = ""
        try await capture(TennisRacketController(session: session), "online-setup-ready-phone", phone)
        session.motion.fixtureSensors = true; session.readyToPlay()
        XCTAssertEqual(session.setupStage, .waiting)
        session.motion.fixtureSensors = false
        try await capture(TennisRacketController(session: session), "online-setup-waiting-phone", phone)
        service.mockStartCountdown()
        try await capture(TennisRacketController(session: session), "online-setup-countdown-phone", phone)
        try await Task.sleep(for: .seconds(3))
        session.ready = true; session.loading.cancel(); session.setupStage = .playing; session.paused = false; session.tennisPhase = "receive"
        try await capture(TennisRacketController(session: session), "online-setup-receive-phone", phone)
    }

    /// Tennis setup (11-20): every step on the phone and the TV, solo and two phones on one TV. Output: work/local-setup-1120/proof/.
    func testPointAndHoldSetupScreens() async throws {
        let session = SportsSession.shared, service = MultiplayerService.shared
        let active = session.active, ready = session.ready, paused = session.paused, players = session.players, index = session.playerIndex
        let sport = session.sport, stage = session.setupStage, gate = session.axisGate, connected = session.displayConnected
        defer {
            session.displayConnected = connected
            session.debugSetHolding(false); session.debugSetCalibration(); session.debugSetOnlineMatch(nil); service.leave()
            session.active = active; session.ready = ready; session.paused = paused; session.motion.fixtureSensors = false
            session.sport = sport; session.setupStage = stage; session.axisGate = gate; session.setupProblem = ""
            session.players = players; session.playerIndex = index
            session.loading.cancel()
        }
        let proof = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("work/local-setup-1120/proof")
        // (only this test's own images: the post-game tests keep theirs in subfolders)
        for file in (try? FileManager.default.contentsOfDirectory(at: proof, includingPropertiesForKeys: nil)) ?? [] where file.pathExtension == "png" {
            try? FileManager.default.removeItem(at: file)
        }
        try FileManager.default.createDirectory(at: proof, withIntermediateDirectories: true)
        let phone = CGSize(width: 402, height: 874)
        let court = Image(uiImage: UIImage(contentsOfFile: URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("ArtDir/ui/tv-results-calibration/scenes/tennis.jpg").path) ?? UIImage()).resizable().scaledToFill()
        func tv(_ name: String) throws {
            let view = TennisSetupTVView(session: session).frame(width: 1280, height: 720).background(court.frame(width: 1280, height: 720).clipped())
            let renderer = ImageRenderer(content: view); renderer.scale = 1
            try XCTUnwrap(renderer.uiImage?.pngData()).write(to: proof.appendingPathComponent("\(name)-tv.png"))
        }
        func phoneShot(_ name: String) async throws {
            try await saveHosted(TennisRacketController(session: session), "\(name)-phone", phone, destination: proof)
            try await Task.sleep(for: .seconds(1))   // (each capture's hold button lets go when its window closes)
        }

        session.players = [Player(name: "Adnan", colorIndex: 0)]; session.playerIndex = 0
        session.active = true; session.ready = true; session.paused = true; session.sport = "tennis"; session.loading.cancel()
        // solo, step by step
        session.setupStage = .scan; session.axisGate = SportsAxisGate(); session.axisGate.message = SportsMotion.pointPrompt
        try tv("s1-point"); try await phoneShot("s1-point")
        session.debugSetHolding(true); session.axisGate.progress = 0.6; session.axisGate.message = "Keep holding…"
        try await phoneShot("s2-holding"); session.debugSetHolding(false)
        session.axisGate.locked = true
        session.debugSetCalibration(flashes: true)
        try tv("s3-flashes"); try await phoneShot("s3-flashes")
        session.debugSetCalibration(prompt: true, latency: 0.128)
        try tv("s4-latency"); try await phoneShot("s4-timing-prompt")
        session.debugSetCalibration(drill: true, latency: 0.128, swings: [], drillStart: SportsRuntime.shared().clock() + 3.2)
        try tv("s5-countdown")
        session.debugSetCalibration(drill: true, latency: 0.128, swings: [2, 3, 4], drillStart: SportsRuntime.shared().clock() - 5.4)
        try tv("s6-drill"); try await phoneShot("s6-drill")
        session.debugSetCalibration(); session.setupStage = .ready
        try tv("s7-ready"); try await phoneShot("s7-ready")

        // two phones, one TV (this phone has the TV): Sam is behind by a step at each point
        try service.enableMock(count: 2, player: Player(name: "Adnan", colorIndex: 0))
        service.mockState(phase: .calibrating)
        session.debugSetOnlineMatch("setup-proof", seat: 0); session.displayConnected = true
        service.mockOneTV(otherStep: "hold", mineHasTV: true)
        session.setupStage = .scan; session.axisGate = SportsAxisGate(); session.axisGate.message = SportsMotion.pointPrompt
        session.debugSetHolding(true); session.axisGate.progress = 0.5
        try tv("m1-both-pointing"); try await phoneShot("m1-pointing")
        session.debugSetHolding(false); session.axisGate.locked = true
        session.debugSetCalibration()
        try tv("m2-waiting-for-sam"); try await phoneShot("m2-waiting-for-sam")
        service.mockOneTV(otherStep: "pointed", mineHasTV: true)
        session.debugSetCalibration(flashes: true)
        try tv("m3-flashes")
        service.mockOneTV(otherStep: "timing", mineHasTV: true)
        session.debugSetCalibration(goAt: service.networkTime + 30, latency: 0.142)
        try tv("m4-latency-one-started"); try await phoneShot("m4-waiting-for-start")
        service.mockOneTV(otherStep: "check:2", mineHasTV: true)
        session.debugSetCalibration(drill: true, latency: 0.142, swings: [2, 3, 4], drillStart: SportsRuntime.shared().clock() - 5.4)
        try tv("m5-drill-both")
        service.mockOneTV(otherStep: "ready", mineHasTV: true)
        session.debugSetCalibration(); session.setupStage = .waiting
        try tv("m6-ready"); try await phoneShot("m6-waiting")
    }

    /// Tennis post-game (ArtDir/ui/tv-results-calibration): winner plaque → box score → XP → play again, TV and phone, stepped by Continue.
    func testTennisPostGameScreens() async throws {
        let session = SportsSession.shared, menu = TennisMenu.shared
        let active = session.active, ready = session.ready, players = session.players, index = session.playerIndex, sport = session.sport
        let opponent = session.opponentName, post = menu.postMatch
        defer {
            session.debugFinishMatch(nil); session.lastMatchStats = nil
            session.active = active; session.ready = ready; session.players = players; session.playerIndex = index; session.sport = sport
            session.opponentName = opponent; menu.debugSetPostMatch(post); session.loading.cancel()
        }
        let proof = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("work/local-setup-1120/proof/postgame")
        try? FileManager.default.removeItem(at: proof)
        try FileManager.default.createDirectory(at: proof, withIntermediateDirectories: true)
        let court = Image(uiImage: UIImage(contentsOfFile: URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("ArtDir/ui/tv-results-calibration/scenes/tennis.jpg").path) ?? UIImage()).resizable().scaledToFill()
        func tv(_ name: String) throws {
            let view = TennisSetupTVView(session: session).frame(width: 1280, height: 720).background(court.frame(width: 1280, height: 720).clipped())
            let renderer = ImageRenderer(content: view); renderer.scale = 1
            try XCTUnwrap(renderer.uiImage?.pngData()).write(to: proof.appendingPathComponent("\(name)-tv.png"))
        }
        session.players = [Player(name: "Adnan", colorIndex: 0)]; session.playerIndex = 0
        session.active = true; session.ready = true; session.sport = "tennis"; session.loading.cancel(); session.opponentName = "Milo"
        var stats = MatchStats(won: true); stats.gamesWon = 6; stats.gamesLost = 3; stats.pointsWon = 25; stats.pointsLost = 16; stats.aces = 3
        session.lastMatchStats = stats
        menu.debugSetPostMatch(PostMatchSummary(won: true, score: "6-3", opponent: "Milo", stats: stats,
            lines: [XPLine(id: 0, title: "Match played", detail: "", xp: 60), XPLine(id: 1, title: "Victory", detail: "", xp: 120),
                    XPLine(id: 2, title: "Aces", detail: "", xp: 36), XPLine(id: 3, title: "Winners", detail: "", xp: 54), XPLine(id: 4, title: "Points won", detail: "", xp: 25)],
            total: 295, startLevel: 1, startXP: 0, endLevel: 2, endXP: 95))
        session.debugFinishMatch((true, "6-3"))
        XCTAssertEqual(session.postGameStage, .victory)
        try tv("1-victory"); try await saveHosted(MatchFinishControls(session: session), "1-victory-phone", CGSize(width: 402, height: 874), destination: proof)
        session.advancePostGame(); XCTAssertEqual(session.postGameStage, .results)
        try tv("2-results")
        session.advancePostGame(); XCTAssertEqual(session.postGameStage, .xp)
        try tv("3-xp"); try await saveHosted(MatchFinishControls(session: session), "3-xp-phone", CGSize(width: 402, height: 874), destination: proof)
        session.advancePostGame(); XCTAssertEqual(session.postGameStage, .again)
        try tv("4-again"); try await saveHosted(MatchFinishControls(session: session), "4-again-phone", CGSize(width: 402, height: 874), destination: proof)
    }

    /// Golf and bowling post-game (ArtDir/ui/tv-results-calibration: Venue Plaque → Scorebook / Box Score → XP → Play again), from
    /// the sheets Unity sends at the end, TV and phone, over the design's own scenes.
    func testGolfAndBowlingPostGameScreens() async throws {
        let session = SportsSession.shared, menu = TennisMenu.shared
        let active = session.active, ready = session.ready, players = session.players, index = session.playerIndex, sport = session.sport
        let post = menu.postMatch, course = session.golfCourse, venue = session.bowlingVenue
        defer {
            session.debugSetPostGameBoard(nil)
            session.active = active; session.ready = ready; session.players = players; session.playerIndex = index; session.sport = sport
            session.golfCourse = course; session.bowlingVenue = venue; menu.debugSetPostMatch(post); session.loading.cancel()
            menu.debugShow(.title)
        }
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
        let proof = root.appendingPathComponent("work/local-setup-1120/proof/postgame-golf-bowling")
        try? FileManager.default.removeItem(at: proof)
        try FileManager.default.createDirectory(at: proof, withIntermediateDirectories: true)
        func tv(_ name: String, scene: UIImage?) throws {
            let back = Image(uiImage: scene ?? UIImage()).resizable().scaledToFill().frame(width: 1280, height: 720).clipped()
            let view = TennisSetupTVView(session: session).frame(width: 1280, height: 720).background(back)
            let renderer = ImageRenderer(content: view); renderer.scale = 1
            try XCTUnwrap(renderer.uiImage?.pngData()).write(to: proof.appendingPathComponent("\(name)-tv.png"))
        }
        func phone(_ name: String) async throws {
            try await saveHosted(MatchFinishControls(session: session), "\(name)-phone", CGSize(width: 402, height: 874), destination: proof)
        }
        session.players = [Player(name: "Adnan", colorIndex: 0)]; session.playerIndex = 0
        session.active = true; session.ready = true; session.loading.cancel()

        // golf, four players on Cliffside (the design's sample round), this phone's Adnan second
        session.sport = "golf"; session.golfCourse = "cliffside"
        menu.debugShow(.loading, launch: MenuLaunch(sport: .golf, mode: .round))
        let golf = PostGameBoard(golf: "holes=1,2,3,4,5;pars=4,4,5,3,3;p=0|Nia|3,3,4,3,3;p=1|Adnan|3,4,5,3,3;p=0|Milo|3,4,6,3,3;p=0|Kai|4,5,5,4,3")
        XCTAssertEqual(golf.players.map(\.name), ["Nia", "Adnan", "Milo", "Kai"])
        XCTAssertEqual(golf.players.map { golf.scoreText($0) }, ["\u{2212}3", "\u{2212}1", "E", "+2"])
        XCTAssertEqual(golf.players.map { golf.strokes($0) }, [16, 18, 19, 21])
        XCTAssertEqual(golf.parTotal, 19)
        XCTAssertFalse(golf.mineWon)
        menu.debugSetPostMatch(PostMatchSummary(won: false, score: "-1", opponent: "", stats: MatchStats(won: false),
            lines: [XPLine(id: 0, title: "Round played", detail: "", xp: 80), XPLine(id: 1, title: "Under par", detail: "", xp: 60),
                    XPLine(id: 2, title: "Birdies", detail: "", xp: 30), XPLine(id: 3, title: "Pars", detail: "", xp: 15)],
            total: 185, startLevel: 1, startXP: 0, endLevel: 2, endXP: 25))
        session.debugSetPostGameBoard(golf)
        let cliffside = UIImage(contentsOfFile: root.appendingPathComponent("ArtDir/ui/tv-results-calibration/scenes/golf.jpg").path)
        try tv("g1-victory", scene: cliffside); try await phone("g1-victory")
        session.advancePostGame(); XCTAssertEqual(session.postGameStage, .results)
        try tv("g2-results", scene: cliffside); try await phone("g2-results")
        session.togglePostGameScorecard(); XCTAssertEqual(session.postGameStage, .scorecard)
        try tv("g3-scorecard", scene: cliffside); try await phone("g3-scorecard")
        session.advancePostGame(); XCTAssertEqual(session.postGameStage, .xp)
        try tv("g4-xp", scene: cliffside)
        session.advancePostGame(); XCTAssertEqual(session.postGameStage, .again)
        XCTAssertEqual(session.postGameChoices.map(\.title), ["Play Again", "Change Course", "Main Menu"])
        XCTAssertEqual(session.postGameChoices.first?.after, .replay)
        try tv("g5-again", scene: cliffside); try await phone("g5-again")

        // golf on your own leads with the score against par; eighteen holes still fit the card
        let back9 = (10...18).map(String.init).joined(separator: ",")
        let solo = PostGameBoard(golf: "holes=1,2,3,4,5,6,7,8,9,\(back9);pars=4,4,5,3,4,4,3,5,4,4,4,3,5,4,4,3,5,4;p=1|Adnan|4,3,5,3,4,5,2,5,4,4,4,3,4,4,5,3,5,4")
        XCTAssertTrue(solo.solo); XCTAssertTrue(solo.mineWon)
        session.debugSetPostGameBoard(solo)
        try tv("g6-solo-victory", scene: cliffside)
        session.advancePostGame(); session.togglePostGameScorecard()
        try tv("g7-solo-18-scorecard", scene: cliffside)

        // bowling, four bowlers at Club Lanes (the design's sample game), Adnan third; a tie shares the place
        session.sport = "bowling"; session.bowlingVenue = "club"
        menu.debugShow(.loading, launch: MenuLaunch(sport: .bowling, mode: .exhibition))
        let lanes = UIImage(contentsOfFile: root.appendingPathComponent("GolfArcade/Unity/MenuArt/map-bowling-club.jpg").path)
        let bowling = PostGameBoard(bowling: [
            "p=0|Nia|X,9 /,8 -,4 /,9 /,- 5,X,2 /,X,6 -|20,38,46,65,75,80,100,120,136,142|142|3",
            "p=0|Kai|4 /,- -,X,9 -,X,X,X,2 /,X,8 1|10,10,29,38,68,90,110,130,149,158|158|5",
            "p=1|Adnan|X,8 1,8 1,X,8 1,8 1,X,8 1,8 1,X 1 1|19,28,37,56,65,74,93,102,111,123|123|4",
            "p=0|Milo|7 1,7 1,7 1,7 1,7 1,7 1,7 1,7 1,7 1,7 1|8,16,24,32,40,48,56,64,72,80|80|0"].joined(separator: ";"))
        XCTAssertEqual(bowling.players.map(\.name), ["Kai", "Nia", "Adnan", "Milo"])
        XCTAssertEqual(bowling.players.map(\.place), [1, 2, 3, 4])
        XCTAssertEqual(bowling.players[0].marks[9], "8 1")
        let tied = PostGameBoard(bowling: "p=1|Adnan|||150|3;p=0|Sam|||150|2;p=0|Kai|||90|0")
        XCTAssertEqual(tied.players.map(\.place), [1, 1, 3]); XCTAssertEqual(PostGameBoard.ordinal(tied.players[2].place), "3rd")
        XCTAssertTrue(tied.mineWon)
        menu.debugSetPostMatch(PostMatchSummary(won: false, score: "123", opponent: "", stats: MatchStats(won: false),
            lines: [XPLine(id: 0, title: "Game bowled", detail: "", xp: 60), XPLine(id: 1, title: "Triple digits", detail: "", xp: 30),
                    XPLine(id: 2, title: "Strikes", detail: "", xp: 60)],
            total: 150, startLevel: 1, startXP: 0, endLevel: 2, endXP: 40))
        session.debugSetPostGameBoard(bowling)
        try tv("b1-victory", scene: lanes); try await phone("b1-victory")
        session.advancePostGame(); XCTAssertEqual(session.postGameStage, .results)
        session.togglePostGameScorecard(); XCTAssertEqual(session.postGameStage, .results, "bowling has no hole-by-hole card")
        try tv("b2-results", scene: lanes); try await phone("b2-results")
        session.advancePostGame(); XCTAssertEqual(session.postGameStage, .xp)
        try tv("b3-xp", scene: lanes)
        session.advancePostGame()
        XCTAssertEqual(session.postGameChoices.map(\.title), ["Play Again", "Change Lanes", "Main Menu"])
        try tv("b4-again", scene: lanes); try await phone("b4-again")
    }

    func testOnlineDisplayRequirementsAndSharingChoice() async throws {
        let bus = HubPartyTests.Bus()
        let host = MultiplayerService(sendToRuntime: { _ in true }, pollRuntime: { nil }, clock: { 100 })
        let guest = MultiplayerService(sendToRuntime: { _ in true }, pollRuntime: { nil }, clock: { 100 })
        host.onMatchRequested = { _ in }; host.onReturnToLobby = {}
        guest.onMatchRequested = { _ in }; guest.onReturnToLobby = {}
        host.setIdentity(name: "Alex"); host.setScreen(true)
        guest.setIdentity(name: "Sam"); guest.setScreen(false)
        try host.host(using: bus.link("a")); try guest.connect(using: bus.link("b"))
        defer { guest.leave(); host.leave() }
        let hub = HubSession(); hub.partyService = host
        hub.debugLive(session: "display-choice"); hub.debugOnlineBench(.tennis, searching: false)
        let proof = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("proof/online-calibration")
        try FileManager.default.createDirectory(at: proof, withIntermediateDirectories: true)
        XCTAssertFalse(host.lobby!.hasScreenForSport)
        try await saveHosted(HubPartyBayPanel(hub: hub), "online-display-required", CGSize(width: 402, height: 874), destination: proof)
        try host.setSharedScreen(true)
        XCTAssertTrue(guest.lobby!.sharedScreen == true)
        XCTAssertTrue(host.lobby!.hasScreenForSport)
        try await saveHosted(HubPartyBayPanel(hub: hub), "online-sharing-tv", CGSize(width: 402, height: 874), destination: proof)
    }

    func testTennisCameraSettingsChoicesAndLayout() async throws {
        let menu = TennisMenu.shared, session = SportsSession.shared
        let original = session.tennisCamera
        defer { session.tennisCamera = original; menu.debugShow(.title) }
        session.tennisCamera = "chase"
        menu.debugShow(.settings, row: 1, column: 0, tab: .display)
        XCTAssertEqual(menu.focused, "tennisCamera")
        try await saveHosted(IslandSettingsScreen(menu: menu, compact: true), "camera-settings-chase-phone", CGSize(width: 402, height: 874))
        menu.move(.right)
        XCTAssertEqual(session.tennisCamera, "elevated")
        XCTAssertEqual(UserDefaults.standard.string(forKey: "sports.tennisCamera"), "elevated")
        try await saveHosted(IslandSettingsScreen(menu: menu, compact: true).preferredColorScheme(.dark), "camera-settings-elevated-dark", CGSize(width: 402, height: 874))
        menu.move(.left)
        XCTAssertEqual(session.tennisCamera, "chase")
        try await saveHosted(IslandSettingsScreen(menu: menu, compact: true).environment(\.dynamicTypeSize, .xxxLarge), "camera-settings-large-text", CGSize(width: 402, height: 874))
        try await saveHosted(IslandSettingsScreen(menu: menu, compact: false), "camera-settings-tv", CGSize(width: 1280, height: 720))
        menu.tap("back")
        XCTAssertEqual(menu.screen, .main)
    }

    func testEmoteLoadoutScreens() async throws {
        let menu = TennisMenu.shared, session = SportsSession.shared
        let oldPlayers = session.players, oldIndex = session.playerIndex
        let oldActive = session.active, oldReady = session.ready, oldPaused = session.paused
        let oldSport = session.sport, oldWindow = session.emoteWindow
        let oldStage = session.setupStage, oldPhase = session.tennisPhase
        defer {
            session.players = oldPlayers; session.playerIndex = oldIndex
            session.active = oldActive; session.ready = oldReady; session.paused = oldPaused
            session.sport = oldSport; session.emoteWindow = oldWindow
            session.setupStage = oldStage; session.tennisPhase = oldPhase
            session.loading.cancel(); menu.debugShow(.title)
        }
        var p = Player(name: "Adnan", colorIndex: 0)
        p.equipEmote("pushups", slot: 0); p.equipEmote("bringIt", slot: 1)
        session.players = [p]; session.playerIndex = 0
        menu.debugShow(.character); menu.tap("lk-tab-emotes")
        XCTAssertEqual(menu.lockerTab, .emotes)
        let out = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("ArtDir/screenshots/emote_loadout")
        try FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        func capture<V: View>(_ view: V, size: CGSize, name: String) async throws {
            let host = UIHostingController(rootView: view); host.safeAreaRegions = []
            let window = UIWindow(windowScene: scene); window.frame = CGRect(origin: .zero, size: size)
            window.rootViewController = host; window.isHidden = false
            host.view.frame = window.bounds; host.view.layoutIfNeeded()
            defer { window.isHidden = true }
            try await Task.sleep(for: .milliseconds(750))
            let format = UIGraphicsImageRendererFormat(); format.scale = 1
            let image = UIGraphicsImageRenderer(size: size, format: format).image { _ in host.view.drawHierarchy(in: host.view.bounds, afterScreenUpdates: true) }
            try XCTUnwrap(image.pngData()).write(to: out.appendingPathComponent(name + ".png"))
        }
        try await capture(IslandLockerScreen(menu: menu, compact: true), size: CGSize(width: 402, height: 874), name: "locker_phone")
        try await capture(IslandLockerScreen(menu: menu, compact: false), size: CGSize(width: 1280, height: 720), name: "locker_tv")
        session.active = true; session.ready = true; session.paused = false; session.sport = "tennis"
        session.loading.begin(now: Date()); session.loading.markReady(); session.loading.skip()
        session.setupStage = .playing; session.tennisPhase = "intro"
        session.emoteWindow = "intro"
        XCTAssertTrue(session.canPlayEmote, "the intro's emote window lets the player pick their intro emote")
        try await capture(TennisEmoteControls(session: session).padding(20).background(IslandUI.navy), size: CGSize(width: 402, height: 180), name: "controller_intro_layout")
        session.tennisPhase = "point"; session.emoteWindow = "point"
        XCTAssertTrue(session.canPlayEmote)
        session.emoteWindow = ""
        XCTAssertFalse(session.canPlayEmote)
        try await capture(TennisEmoteControls(session: session).padding(20).background(IslandUI.navy), size: CGSize(width: 402, height: 180), name: "controller_rally_layout")
    }

    func testSportLockerPreviewSwitchesOutfitEquipmentAndBack() async throws {
        let menu = TennisMenu.shared, session = SportsSession.shared
        let oldPlayers = session.players, oldIndex = session.playerIndex
        defer { session.players = oldPlayers; session.playerIndex = oldIndex; menu.debugShow(.title) }
        let out = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("ArtDir/screenshots/golf_locker_swap")
        try FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        for female in [false, true] {
            var p = Player(name: "Adnan", colorIndex: 0); p.standardFemale = female
            let c = CharacterModelPreview.Coordinator(cameraDistance: 2.7)
            c.update(p, sport: .tennis)
            let tennis = try XCTUnwrap(c.hero)
            XCTAssertGreaterThan(try XCTUnwrap(c.racket).childNodes.count, 0)
            c.update(p, sport: .golf)
            let golf = try XCTUnwrap(c.hero)
            XCTAssertFalse(golf === tennis, "sport switch must replace the preview even when Player is unchanged")
            XCTAssertNotNil(golf.childNode(withName: "Kit_Head", recursively: true))
            XCTAssertNotNil(golf.childNode(withName: "Kit_Glove_L", recursively: true))
            XCTAssertNil(golf.childNode(withName: "Kit_Sock_L", recursively: true))
            XCTAssertEqual(c.racket?.childNodes.count, 0)
            XCTAssertNotNil(golf.childNode(withName: "clubHead", recursively: true))
            let tool = try XCTUnwrap(golf.childNode(withName: "golfClub", recursively: false))
            let target = c.framingTarget(.racket), box = tool.boundingBox
            let centre = tool.convertPosition(SCNVector3((box.min.x + box.max.x)/2, (box.min.y + box.max.y)/2, (box.min.z + box.max.z)/2), to: nil)
            XCTAssertEqual(target.y, centre.y, accuracy: 0.001, "club close-up targets its full geometry")
            c.configureIdle(sport: nil, animate: false); c.applyFraming()
            XCTAssertTrue(try XCTUnwrap(c.racket).isHidden)
            XCTAssertFalse(try XCTUnwrap(golf.childNode(withName: "golfClub", recursively: false)).isHidden)
            c.update(p, sport: .tennis)
            XCTAssertGreaterThan(try XCTUnwrap(c.racket).childNodes.count, 0)
            XCTAssertNil(c.hero?.childNode(withName: "golfClub", recursively: true))
            session.players = [p]; session.playerIndex = 0; menu.debugShow(.character)
            for sport in ["tennis", "golf", "bowling"] {
                menu.tap("lk-sport-" + sport)
                let size = CGSize(width: 402, height: 874)
                let host = UIHostingController(rootView: IslandLockerScreen(menu: menu, compact: true)); host.safeAreaRegions = []
                let window = UIWindow(windowScene: scene); window.frame = CGRect(origin: .zero, size: size)
                window.rootViewController = host; window.isHidden = false; host.view.frame = window.bounds; host.view.layoutIfNeeded()
                try await Task.sleep(for: .milliseconds(900))
                let format = UIGraphicsImageRendererFormat(); format.scale = 1
                let image = UIGraphicsImageRenderer(size: size, format: format).image { _ in host.view.drawHierarchy(in: host.view.bounds, afterScreenUpdates: true) }
                try XCTUnwrap(image.pngData()).write(to: out.appendingPathComponent("\(female ? "female" : "male")_\(sport).png"))
                window.isHidden = true
            }
            p.handedness = .left; c.update(p, sport: .golf)
            XCTAssertLessThan(try XCTUnwrap(c.hero).scale.x, 0, "club and glove mirror with the left-handed hero")
        }
    }

    /// Live capture of the same widescreen root used by SportsDisplays on AirPlay.
    func testRecordTVMenuTour() async throws {
        try XCTSkipUnless(ProcessInfo.processInfo.environment["RECORD_TV_MENU"] == "1", "Opt-in review capture")
        let out = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("ArtDir/review/tv-menus")
        try FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        let url = out.appendingPathComponent("TV_Intro_and_Menus.mp4")
        try? FileManager.default.removeItem(at: url)
        let menu = TennisMenu.shared
        menu.debugShow(.title)
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let size = CGSize(width: 1280, height: 720)
        let host = UIHostingController(rootView: TennisTVRoot())
        host.safeAreaRegions = []
        let window = UIWindow(windowScene: scene)
        window.frame = CGRect(origin: .zero, size: size)
        window.rootViewController = host; window.isHidden = false
        host.view.frame = window.bounds; host.view.layoutIfNeeded()
        defer { window.isHidden = true; menu.debugShow(.title); SportsSession.shared.loading.cancel() }
        try await Task.sleep(for: .seconds(2))
        let writer = try AVAssetWriter(outputURL: url, fileType: .mp4)
        let input = AVAssetWriterInput(mediaType: .video, outputSettings: [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: 1280, AVVideoHeightKey: 720])
        let adapter = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB, kCVPixelBufferWidthKey as String: 1280, kCVPixelBufferHeightKey as String: 720, kCVPixelBufferCGImageCompatibilityKey as String: true, kCVPixelBufferCGBitmapContextCompatibilityKey as String: true])
        writer.add(input); XCTAssertTrue(writer.startWriting()); writer.startSession(atSourceTime: .zero)
        let format = UIGraphicsImageRendererFormat(); format.scale = 1; format.opaque = true
        let renderer = UIGraphicsImageRenderer(size: size, format: format)
        let started = CACurrentMediaTime()
        var action = 0
        let actions: [(Double, String)] = [(4,"start"),(9,"play"),(13,"sport-tennis"),(18,"back"),(19,"sport-golf"),(23,"back"),(24,"back"),(25,"character"),(31,"back"),(32,"settings"),(36,"back")]
        var frame = 0
        while CACurrentMediaTime() - started < 39 {
            let elapsed = CACurrentMediaTime() - started
            if action < actions.count, elapsed >= actions[action].0 { menu.tap(actions[action].1); action += 1 }
            while !input.isReadyForMoreMediaData { try await Task.sleep(for: .milliseconds(5)) }
            let image = renderer.image { _ in host.view.drawHierarchy(in: CGRect(origin: .zero, size: size), afterScreenUpdates: false) }
            if frame % 90 == 0 { try image.pngData()?.write(to: out.appendingPathComponent("review-\(frame).png")) }
            var buffer: CVPixelBuffer?
            CVPixelBufferPoolCreatePixelBuffer(nil, try XCTUnwrap(adapter.pixelBufferPool), &buffer)
            let pixel = try XCTUnwrap(buffer)
            CVPixelBufferLockBaseAddress(pixel, [])
            let context = try XCTUnwrap(CGContext(data: CVPixelBufferGetBaseAddress(pixel), width: 1280, height: 720, bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(pixel), space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue))
            context.draw(try XCTUnwrap(image.cgImage), in: CGRect(origin: .zero, size: size))
            CVPixelBufferUnlockBaseAddress(pixel, [])
            XCTAssertTrue(adapter.append(pixel, withPresentationTime: CMTime(seconds: elapsed, preferredTimescale: 60000)))
            frame += 1
            try await Task.sleep(for: .milliseconds(16))
        }
        input.markAsFinished(); await writer.finishWriting()
        XCTAssertEqual(writer.status, .completed, "\(String(describing: writer.error))")
    }

    func testApprovedIslandScreens() async throws {
        let menu = TennisMenu.shared, session = SportsSession.shared
        let oldPlayers = session.players, oldIndex = session.playerIndex
        var referencePlayer = Player(name: "Adnan", colorIndex: 0); referencePlayer.setSkin(0.35); referencePlayer.hairColor = 3
        session.players = [referencePlayer]; session.playerIndex = 0
        defer { session.players = oldPlayers; session.playerIndex = oldIndex; session.loading.cancel(); session.menuPauseVisible = false; menu.debugShow(.title) }
        let out = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("ArtDir/ui/toybox-simple-v6/runtime")
        try FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let screens: [(String, MenuScreen)] = [("intro", .title), ("home", .main), ("sports", .gameSelect), ("courts", .map), ("tennis", .hub(.tennis)), ("campaign", .campaign), ("quick-match", .exhibition), ("training", .training), ("locker", .character), ("settings", .settings), ("guide", .howTo), ("connect", .connect), ("results", .results), ("pause", .main), ("loading", .loading)]
        for (name, screen) in screens {
            menu.debugShow(screen, launch: MenuLaunch(round: 0), result: MatchResult(won: true, score: "6–4", round: 0))
            session.menuPauseVisible = name == "pause"
            if screen == .loading { session.loading.begin(now: Date()); session.loading.reach(0.72); session.loading.tick(now: Date()) }
            let size = CGSize(width: 1280, height: 720)
            let host = UIHostingController(rootView: TennisTVRoot()); host.safeAreaRegions = []
            let window = UIWindow(windowScene: scene); window.frame = CGRect(origin: .zero, size: size)
            window.rootViewController = host; window.isHidden = false; host.view.frame = window.bounds; host.view.layoutIfNeeded()
            try await Task.sleep(for: .seconds(1))
            let format = UIGraphicsImageRendererFormat(); format.scale = 1
            func capture(_ suffix: String = "") throws {
                let image = UIGraphicsImageRenderer(size: size, format: format).image { _ in host.view.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
                try XCTUnwrap(image.pngData()).write(to: out.appendingPathComponent(name + suffix + ".png"))
            }
            try capture()
            window.isHidden = true
        }
        session.menuPauseVisible = false
        menu.debugShow(.main)
        try await saveHosted(TennisPhoneMenu(), "island-home-phone", CGSize(width: 402, height: 874))
        menu.debugShow(.character)
        try await saveHosted(TennisPhoneMenu(), "island-locker-phone", CGSize(width: 402, height: 874))
        for (name, route) in [("quick",MenuScreen.exhibition),("settings",.settings),("campaign",.campaign),("loading",.loading)] {
            menu.debugShow(route)
            try await saveHosted(TennisPhoneMenu(), "island-\(name)-phone", CGSize(width:402,height:874))
        }
    }

    private var folder: URL {
        // MENU_SNAP_DIR (passed as TEST_RUNNER_MENU_SNAP_DIR by xcodebuild) lets a review write straight to a chosen folder.
        let url = ProcessInfo.processInfo.environment["MENU_SNAP_DIR"].map { URL(fileURLWithPath: $0) }
            ?? FileManager.default.temporaryDirectory.appendingPathComponent("tennis-menu")
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    private func save<V: View>(_ view: V, _ name: String, _ size: CGSize) throws {
        let renderer = ImageRenderer(content: view.frame(width: size.width, height: size.height))
        renderer.scale = 1.5
        let image = try XCTUnwrap(renderer.uiImage, "\(name) did not render")
        try XCTUnwrap(image.pngData()).write(to: folder.appendingPathComponent("\(name).png"))
    }

    func testLobbyLayouts() async throws {
        let menu = TennisMenu.shared
        menu.debugShow(.title); menu.tap("start")
        defer { menu.debugShow(.title); SportsSession.shared.loading.cancel() }
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let states: [(String, CGSize, Bool, MenuScreen, MenuLaunch?)] = [
            ("lobby-tv", CGSize(width: 1280, height: 720), false, .main, nil),
            ("lobby-mac", CGSize(width: 1440, height: 900), false, .main, nil),
            ("lobby-phone", CGSize(width: 402, height: 874), true, .main, nil),
            ("party-phone", CGSize(width: 402, height: 874), true, .party, nil),
            ("loading-tennis", CGSize(width: 1280, height: 720), false, .loading, MenuLaunch(mode: .exhibition, round: 0)),
            ("loading-golf-phone", CGSize(width: 402, height: 874), true, .loading, MenuLaunch(sport: .golf, mode: .round)),
            ("loading-stalled-phone", CGSize(width: 402, height: 874), true, .loading, MenuLaunch(mode: .training)),
            ("home-large-text", CGSize(width: 402, height: 874), true, .main, nil)
        ]
        for (name, size, compact, screen, launch) in states {
            menu.debugShow(screen, launch: launch, row: screen == .main ? 1 : 0)
            if screen == .loading {
                let loading = SportsSession.shared.loading
                let start = Date()
                loading.begin(now: start); loading.reach(0.4)
                loading.tick(now: start.addingTimeInterval(name.contains("stalled") ? 22 : 0.5))
            }
            let host = UIHostingController(rootView: Group {
                if compact { TennisPhoneMenu() } else { TennisTVRoot() }
            }.environment(\.dynamicTypeSize, name == "home-large-text" ? .accessibility1 : .large))
            let window = UIWindow(windowScene: scene)
            window.frame = CGRect(origin: .zero, size: size)
            window.rootViewController = host; window.isHidden = false
            host.view.frame = window.bounds; host.view.layoutIfNeeded()
            try await Task.sleep(for: .seconds(2))
            let image = UIGraphicsImageRenderer(size: size).image { _ in
                host.view.drawHierarchy(in: window.bounds, afterScreenUpdates: true)
            }
            try XCTUnwrap(image.pngData()).write(to: folder.appendingPathComponent("\(name).png"))
            window.isHidden = true
        }
    }

    func testLoadingIdlesRespectReducedMotionAndSport() throws {
        let preview = CharacterModelPreview.Coordinator()
        preview.update(Player(name: "Test", colorIndex: 0))
        preview.configureIdle(sport: .golf, animate: true)
        XCTAssertNotNil(preview.character.childNode(withName: "idleClub", recursively: false))
        XCTAssertEqual(preview.character.childNode(withName: "racket", recursively: true)?.isHidden, true)
        XCTAssertTrue(preview.character.hasActions)
        preview.configureIdle(sport: .tennis, animate: false)
        XCTAssertNil(preview.character.childNode(withName: "idleClub", recursively: false))
        XCTAssertFalse(preview.character.hasActions)
        XCTAssertEqual(preview.character.childNode(withName: "racket", recursively: true)?.isHidden, false)
        XCTAssertEqual(preview.scene.rootNode.childNode(withName: "idleBall", recursively: false)?.hasActions, false)
    }

    func testCharacterModelVariants() throws {
        for i in 0..<4 {
            var player = Player(name: "Preview", colorIndex: 0)
            player.hairStyle = i; player.faceShape = i; player.standardSkin = i + 1
            player.shirt = i + 1; player.heightChoice = i; player.buildChoice = i
            let coordinator = CharacterModelPreview.Coordinator()
            coordinator.update(player)
            XCTAssertNotNil(coordinator.hero, "the locker mirror shows the match hero")
            XCTAssertGreaterThan(coordinator.hero?.childNodes.count ?? 0, 2)
            let renderer = SCNRenderer(device: nil, options: nil)
            renderer.scene = coordinator.scene
            renderer.pointOfView = coordinator.scene.rootNode.childNodes.first { $0.camera != nil }
            let image = renderer.snapshot(atTime: 0, with: CGSize(width: 600,height: 800), antialiasingMode: .multisampling4X)
            try XCTUnwrap(image.pngData()).write(to: folder.appendingPathComponent("character-variant-\(i).png"))
        }
        let player = SportsSession.shared.players[0]
        let data = try JSONEncoder().encode(player)
        XCTAssertEqual(try JSONDecoder().decode(Player.self, from: data), player)
    }

    private func saveHosted<V: View>(_ view: V, _ name: String, _ size: CGSize, destination: URL? = nil) async throws {
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let host = UIHostingController(rootView: view)
        let window = UIWindow(windowScene: scene)
        let previous = scene.windows.first { $0.isKeyWindow }
        window.frame = CGRect(origin: .zero, size: size); window.rootViewController = host
        // Online proof must be visible to the simulator recorder as well as drawHierarchy.
        if destination != nil { window.windowLevel = .alert + 2 }
        window.makeKeyAndVisible()
        defer { window.isHidden = true; previous?.makeKeyAndVisible() }
        host.view.frame = window.bounds; host.view.layoutIfNeeded()
        try await Task.sleep(for: .seconds(1))
        let image = UIGraphicsImageRenderer(size: size).image { _ in host.view.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
        try XCTUnwrap(image.pngData()).write(to: (destination ?? folder).appendingPathComponent("\(name).png"))
    }

    /// The screens the phone shows over the pointer menu (HubStationPanel): Play choices, players, locker tabs, settings and so on.
    func testPhoneStationScreens() async throws {
        let menu = TennisMenu.shared, session = SportsSession.shared
        let oldPlayers = session.players, oldIndex = session.playerIndex
        var p = Player(name: "Adnan", colorIndex: 0); p.setSkin(0.35)
        session.players = [p]; session.playerIndex = 0
        defer { session.players = oldPlayers; session.playerIndex = oldIndex; menu.debugShow(.title) }
        let size = CGSize(width: 402, height: 874)
        let screens: [(String, MenuScreen)] = [("party", .party), ("local", .localChoice), ("players", .localPlayers), ("online", .onlineChoice),
            ("settings", .settings), ("campaign", .campaign), ("quick", .exhibition), ("courts", .map), ("hub", .hub(.tennis)),
            ("training", .training), ("results", .results), ("emotes", .homeEmotes)]
        for (name, screen) in screens {
            menu.debugShow(screen, launch: MenuLaunch(round: 0), result: MatchResult(won: true, score: "6–4", round: 0))
            try await saveHosted(HubStationPanel(hub: .shared), "station-\(name)", size)
        }
        for tab in ["gear", "customize", "emotes"] {
            menu.debugShow(.character); _ = menu.tap("lk-tab-\(tab)")
            try await saveHosted(HubStationPanel(hub: .shared), "station-locker-\(tab)", size)
        }
    }

    func testNewBaseLocker() async throws {
        let session=SportsSession.shared, menu=TennisMenu.shared
        let players=session.players, index=session.playerIndex
        defer { session.players=players; session.playerIndex=index; menu.debugShow(.title) }
        for female in [false,true] {
            var p=Player(name: female ? "Maya" : "Alex",colorIndex:0)
            p.standardFemale=female; p.bodySize=female ? 1 : 0; p.hairStyle=female ? 3 : 1
            session.players=[p];session.playerIndex=0;menu.debugShow(.character)
            try await saveHosted(IslandLockerScreen(menu:menu,compact:true),"new-locker-\(female)",CGSize(width:402,height:874))
            try await saveHosted(IslandLockerScreen(menu:menu,compact:false),"new-locker-tv-\(female)",CGSize(width:1280,height:720))
        }
    }

    func testFinishedPhoneControllers() async throws {
        let session = SportsSession.shared, menu = TennisMenu.shared
        TennisCampaign.shared.restart()
        TennisCampaign.shared.record(round: 0, won: true)
        menu.debugShow(.loading, launch: MenuLaunch(round: 0), result: MatchResult(won: true, score: "3–0", round: 0))
        session.sport = "tennis"
        session.active = true
        session.finishedMatch = (true, "3–0")
        defer { session.active = false; session.finishedMatch = nil }
        try await saveHosted(SportsHome(), "finish-phone", CGSize(width: 402, height: 874))
        try await saveHosted(SportsPreviewControls(), "finish-preview", CGSize(width: 800, height: 150))
    }

    /// (The ultimates, already empty calls, left 2026-11-15; the renders keep their file names.)
    func testRacketControllerScreens() async throws {
        let session = SportsSession.shared
        session.sport = "tennis"; session.ready = true; session.paused = true
        session.finishedMatch = nil
        defer { session.ready = false; session.paused = true }
        session.paused = false; session.tennisPhase = "rally"
        try await saveHosted(SportsPreviewControls(), "ultimate-preview", CGSize(width: 800,height: 300))
        session.loading.cancel()
        try await saveHosted(TennisRacketController(session: session), "ultimate-controller", CGSize(width: 390,height: 844))
        try await saveHosted(TennisRacketController(session: session), "ultimate-controller-small", CGSize(width: 375,height: 667))
    }

    func testRenderScreens() throws {
        let menu = TennisMenu.shared
        LoopingVideo.stillsOnly = true; defer { LoopingVideo.stillsOnly = false }
        let tv = CGSize(width: 1280, height: 720), phone = CGSize(width: 402, height: 874)
        let states: [(String, MenuScreen, MenuLaunch?, MatchResult?, Int, Int)] = [
            ("title", .title, nil, nil, 0, 0),
            ("main", .main, nil, nil, 0, 0),
            ("game-select", .gameSelect, nil, nil, 0, 1),
            ("hub-tennis", .hub(.tennis), nil, nil, 0, 0),
            ("hub-golf", .hub(.golf), nil, nil, 0, 1),
            ("exhibition", .exhibition, nil, nil, 0, 0),
            ("character", .character, nil, nil, 4, 0),
            ("howto", .howTo, nil, nil, 0, 1),
            ("connect", .connect, nil, nil, 1, 0),
            ("loading-tutorial", .loading, MenuLaunch(mode: .tutorial), nil, 0, 0),
            ("loading-golf", .loading, MenuLaunch(sport: .golf, mode: .round), nil, 0, 0),
            ("campaign", .campaign, nil, nil, 0, 0),
            ("campaign-locked", .campaign, nil, nil, 0, 2),
            ("training", .training, nil, nil, 1, 0),
            ("settings", .settings, nil, nil, 3, 0),
            ("loading", .loading, MenuLaunch(round: 3), nil, 0, 0),
            ("loading-final", .loading, MenuLaunch(round: 9), nil, 0, 0),
            ("loading-training", .loading, MenuLaunch(round: nil), nil, 0, 0),
            ("results-win", .results, MenuLaunch(round: 0), MatchResult(won: true, score: "3–1", round: 0), 0, 0),
            ("results-loss", .results, MenuLaunch(round: 3), MatchResult(won: false, score: "1–3", round: 3), 0, 0),
        ]
        for (name, screen, launch, result, row, column) in states {
            menu.debugShow(screen, launch: launch, result: result, row: row, column: column)
            try save(TennisTVRoot(), "tv-\(name)", tv)
            try save(TennisPhoneMenu(), "phone-\(name)", phone)
        }
        for tab in SettingsTab.allCases {
            menu.debugShow(.settings, row: 1, column: 0, tab: tab)
            try save(TennisTVRoot(), "tv-settings-\(tab.rawValue)", tv)
        }
        // A 16:10 MacBook receiving AirPlay: the canvas fits with backdrop above and below.
        menu.debugShow(.gameSelect, row: 0, column: 1)
        try save(TennisTVRoot(), "mac-game-select", CGSize(width: 1440, height: 900))
        for (name, lines, index) in [("story-ray", TennisStory.before(9), 0), ("story-rival", TennisStory.before(3), 1),
                                     ("story-offer", TennisStory.afterWin(0), 3)] {
            menu.debugStory(lines, index: index)
            try save(TennisTVRoot(), "tv-\(name)", tv)
            try save(TennisPhoneMenu(), "phone-\(name)", phone)
        }
        menu.debugShow(.campaign, row: 1, column: 4)
        try save(TennisTVRoot(), "tv-campaign-final", tv)

        let session = SportsSession.shared
        session.ready = true; session.paused = false; session.opponentName = "Suki"
        session.score = TennisScore(line: "2,1,GAMES 2–1 · 30–15 · YOUR SERVE")
        session.contacts = ["0.1,0.05,5,0", "-0.4,0.3,3,0", "0.6,-0.5,1,0", "0.0,-0.1,4,0", "0.2,0.2,5,1"].compactMap(TennisContact.init(line:))
        try save(TennisRacketController(session: session), "phone-racket", phone)
        session.axisGate.locked = true
        for phase in ["serve", "toss", "receive"] {
            session.tennisPhase = phase
            try save(TennisRacketController(session: session), "phone-\(phase)", phone)
        }
        session.tutorialStep = (0, 5, "SERVE: press TOSS near the meter's middle. Swing overhead as the ball reaches its highest point. Land one in the box.")
        session.tennisPhase = "serve"
        try save(TennisRacketController(session: session), "phone-tutorial-serve", phone)
        session.tutorialStep = (3, 5, "AIM RIGHT: now angle the face right and land a return toward the other gold ring.")
        session.tennisPhase = "rally"
        try save(TennisRacketController(session: session), "phone-tutorial-aim", phone)
        session.tutorialStep = nil
        session.tennisPhase = "" 
        menu.debugShow(.title)
    }
}


// Scripted component review, intentionally separate from integrated-device acceptance.
extension TennisMenuSnapshotTests {
    func testFilmPresentationNativeComponents() async throws {
        let session=SportsSession.shared, menu=TennisMenu.shared, displays=SportsDisplays.shared
        let scene=try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let window=UIWindow(windowScene:scene)
        let oldPhone=displays.phone, oldActive=session.active, oldSport=session.sport, oldIntros=session.presentationIntros
        let oldMatch=session.finishedMatch
        let oldFlyover=session.holeFlyover, oldMoments=session.presentationBigMoments
        let root=URL(fileURLWithPath:NSTemporaryDirectory()).appendingPathComponent("presentation-native-films",isDirectory:true)
        try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
        window.frame=CGRect(x:0,y:0,width:402,height:874); window.windowLevel = .normal + 2
        window.isHidden=false; displays.phone=window
        defer {
            displays.finishLoadingCover();session.loading.cancel();session.active=oldActive;session.sport=oldSport
            session.presentationIntros=oldIntros;session.finishedMatch=oldMatch
            session.holeFlyover=oldFlyover;session.presentationBigMoments=oldMoments
            displays.phone=oldPhone;window.isHidden=true;menu.debugShow(.title)
        }
        func show<V:View>(_ view:V, size:CGSize=CGSize(width:402,height:874)) {
            window.frame=CGRect(origin:.zero,size:size)
            let host=UIHostingController(rootView:view);host.safeAreaRegions=[];window.rootViewController=host
            host.view.frame=window.bounds;host.view.layoutIfNeeded()
        }
        func film(_ name:String, seconds:Double, update:(Double)->Void={_ in}) async throws {
            let dir=root.appendingPathComponent(name,isDirectory:true);try FileManager.default.createDirectory(at:dir,withIntermediateDirectories:true)
            let format=UIGraphicsImageRendererFormat();format.scale=1
            for frame in 0..<Int(seconds*10) {
                update(Double(frame)/10);window.rootViewController?.view.layoutIfNeeded()
                let image=UIGraphicsImageRenderer(size:window.bounds.size,format:format).image { _ in
                    for visible in scene.windows.filter({!$0.isHidden}).sorted(by:{$0.windowLevel < $1.windowLevel}) {
                        visible.drawHierarchy(in:window.bounds,afterScreenUpdates:true)
                    }
                }
                try XCTUnwrap(image.jpegData(compressionQuality:0.88)).write(to:dir.appendingPathComponent(String(format:"frame-%04d.jpg",frame)))
                try await Task.sleep(for:.milliseconds(100))
            }
        }
        for sport in ["tennis","golf"] {
            session.active=true;session.sport=sport
            menu.debugShow(.loading,launch:MenuLaunch(sport:sport=="golf" ? .golf:.tennis,mode:sport=="golf" ? .round:.exhibition,round:sport=="tennis" ? 0:nil))
            show(TennisPhoneMenu());session.loading.begin(now:LoadingModel.clockNow)
            session.loading.onFinish={displays.finishLoadingCover()};displays.beginLoadingCover(in:window,startRuntime:{})
            try await film("L1_\(sport)_native_cover_fixture_phone",seconds:5) { t in
                if t>=2 {session.loading.reach(t<3 ? 0.4:1)}
                if t>=3.5 {session.loading.markSceneReady();session.loading.markReady()}
                session.loading.tick(now:LoadingModel.clockNow)
            }
            displays.finishLoadingCover();session.loading.cancel()
        }
        session.active=false;session.sport="tennis"
        menu.debugShow(.loading,launch:MenuLaunch(mode:.training))
        session.loading.begin(now:LoadingModel.clockNow)
        show(LoadingScreen(menu:menu,compact:true))
        try await film("L1_long_load_tips_retry_fixture_phone",seconds:23) { t in
            if t>=10 {session.loading.reach(0.4)}
            session.loading.tick(now:LoadingModel.clockNow)
        }
        session.loading.cancel()
        let service=MultiplayerService.shared,bus=MultiplayerTests.Bus()
        let oldLaunch=service.onMatchRequested,oldReturn=service.onReturnToLobby
        service.onMatchRequested={_ in};service.onReturnToLobby={}
        service.setIdentity(name:"Adnan")
        try service.host(using:bus.link("film-host"))
        var peers:[MultiplayerService]=[]
        for (i,name) in ["Maya","Sam","Leo"].enumerated() {
            let peer=MultiplayerService(sendToRuntime:{_ in true},pollRuntime:{nil},clock:{ProcessInfo.processInfo.systemUptime})
            peer.setIdentity(name:name);peer.onMatchRequested={_ in};peer.onReturnToLobby={}
            try peer.connect(using:bus.link("film-\(i)"));peers.append(peer)
        }
        defer {for peer in peers.reversed(){peer.leave()};service.leave();service.onMatchRequested=oldLaunch;service.onReturnToLobby=oldReturn}
        try service.configure(.golf)
        for peer in peers {try peer.setReady(true)};try service.setReady(true);try service.startMatch()
        session.sport="golf"
        session.loading.begin(now:LoadingModel.clockNow,multiplayer:true)
        menu.debugShow(.online(.loading));show(LoadingScreen(menu:menu,compact:true))
        try await film("L1_multiplayer_delayed_keep_waiting_fixture_phone",seconds:24) { t in
            if t==2 {session.loading.markReady();service.runtimeLoaded();peers[0].runtimeLoaded();peers[1].runtimeLoaded()}
            service.update()
            session.loading.updatePlayers(waiting:service.lobby!.competitors.filter{!$0.loaded}.map(\.name),allReady:false)
            session.loading.tick(now:LoadingModel.clockNow)
            if t==22 {try? service.keepWaitingForLoad();session.loading.keepWaiting()}
        }
        for peer in peers.reversed(){peer.leave()};peers=[];service.leave()
        menu.debugShow(.settings);show(IslandSettingsScreen(menu:menu,compact:true))
        try await film("preferences_full_short_off_flyover_big_moments_fixture_phone",seconds:6) { t in
            session.presentationIntros=t<2 ? "full":t<4 ? "short":"off"
            session.holeFlyover=t<3;session.presentationBigMoments=t<4
        }
        session.active=true;session.sport="tennis";session.finishedMatch=(true,"3–1")
        show(MatchFinishControls(session:session))
        try await film("L7_results_rematch_leave_fixture_phone",seconds:4)
        session.finishedMatch=nil;session.active=false;menu.debugShow(.main);show(TennisPhoneMenu())
        session.presentationIntros="full";displays.beginExitCover()
        try await film("L8_native_exit_cover_fixture_phone",seconds:3)
        menu.debugShow(.loading,launch:MenuLaunch(mode:.exhibition,round:0));session.sport="tennis"
        session.loading.begin(now:LoadingModel.clockNow)
        show(LoadingScreen(menu:menu,compact:false),size:CGSize(width:1280,height:720))
        try await film("L1_tennis_loading_card_fixture_tv_canvas",seconds:4) {_ in session.loading.tick(now:LoadingModel.clockNow)}
        print("PRESENTATION_NATIVE_FILMS=\(root.path)")
    }
}
