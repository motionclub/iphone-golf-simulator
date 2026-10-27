import simd
import XCTest
@testable import GolfArcade

/// The pointer menu's phone half (PLAN_PointerMenu.md): the pointer maths, and the menu's wiring in HubSession (what the phone
/// sends Unity, what it does with the TV's events).
@MainActor
final class MenuPointerMathTests: XCTestCase {
    /// A phone held like a remote (screen up, top edge at the TV), turned `yaw` degrees left and tilted `pitch` degrees up.
    private func remote(yaw: Double, pitch: Double) -> simd_quatd {
        simd_quatd(angle: yaw * .pi / 180, axis: SIMD3(0, 0, 1)) * simd_quatd(angle: pitch * .pi / 180, axis: SIMD3(1, 0, 0))
    }

    func testRecenterIsTheMiddleAndTheRangesReachTheEdges() {
        var m = MenuPointerMath()
        m.recenter(remote(yaw: 30, pitch: 5))
        var p = m.point(remote(yaw: 30, pitch: 5), at: 0)
        XCTAssertEqual(p.x, 0, accuracy: 1e-6); XCTAssertEqual(p.y, 0, accuracy: 1e-6)
        m = MenuPointerMath(); m.recenter(remote(yaw: 0, pitch: 0))
        p = m.point(remote(yaw: -10, pitch: 0), at: 1)   // turned 10° right: half way to the right edge
        XCTAssertEqual(p.x, 0.5, accuracy: 0.01)
        m = MenuPointerMath(); m.recenter(remote(yaw: 0, pitch: 0))
        p = m.point(remote(yaw: 0, pitch: 11.25), at: 1)  // tilted up 11.25°: the top
        XCTAssertEqual(p.y, 1, accuracy: 0.01)
    }

    func testPastTheEdgeTheReferenceFollowsSoComingBackMovesAtOnce() {
        var m = MenuPointerMath(); m.recenter(remote(yaw: 0, pitch: 0))
        var t = 0.0
        func at(_ yaw: Double) -> Double { t += 0.5; return m.point(remote(yaw: yaw, pitch: 0), at: t).x }
        XCTAssertEqual(at(-40), 1, accuracy: 0.01, "clamped at the right edge")
        XCTAssertLessThan(at(-30), 0.6, "10° back is half the screen back (the edge dragged the reference)")
    }

    func testAnUprightGripPointsWithTheBackOfThePhone() {
        // upright like a camera: the top edge points at the sky, the back at the TV
        let upright = simd_quatd(angle: .pi / 2, axis: SIMD3(1, 0, 0))
        var m = MenuPointerMath(); m.recenter(upright)
        XCTAssertTrue(m.useBack)
        let turned = simd_quatd(angle: -10 * .pi / 180, axis: SIMD3(0, 0, 1)) * upright
        XCTAssertEqual(m.point(turned, at: 1).x, 0.5, accuracy: 0.02)
    }

    func testTheFilterTakesOutTremorButFollowsAMove() {
        var f = MenuPointerMath.OneEuro()
        var out: [Double] = []
        for i in 0..<200 { out.append(f.filter(0.3 + 0.01 * sin(Double(i) * 1.9), Double(i) / 100)) }   // ±1 % at ~30 Hz
        let tail = out.suffix(100)
        XCTAssertLessThan((tail.max() ?? 0) - (tail.min() ?? 0), 0.01, "a still hand's tremor is mostly gone")
        var g = MenuPointerMath.OneEuro(), y = 0.0
        for i in 0..<20 { y = g.filter(i < 2 ? 0 : 0.8, Double(i) / 100) }
        XCTAssertGreaterThan(y, 0.7, "a quick move lands within 0.2 s")
    }

    // MARK: HubSession

    override func setUp() async throws { HubSession.shared.debugReset(); OnboardingFlow.shared.exitToMenu(); TennisMenu.shared.classic = false }
    override func tearDown() async throws { HubSession.shared.debugReset() }

    func testTheMenuBootTellsUnityToBuildTheMenu() {
        let hub = HubSession.shared
        var start: [String: Any]?; hub.debugSent = { if $0["action"] as? String == "start" { start = $0 } }
        hub.debugBoot(session: "menu", menu: true)
        XCTAssertEqual(start?["menu"] as? Bool, true)
        XCTAssertEqual(start?["leader"] as? Bool, true, "no party: you drive")
        XCTAssertEqual(start?["soloLocked"] as? Bool, false)
        XCTAssertNotNil(start?["playerName"])
    }

    func testTheTVsEventsReachThePhone() {
        let hub = HubSession.shared
        hub.debugLive(); hub.debugMenu()
        hub.receive(["type": "menuScreen", "session": "debug-hub", "message": "modes:tennis"])
        XCTAssertEqual(hub.menuScreen, "modes:tennis")
        hub.receive(["type": "menuHover", "session": "debug-hub", "message": "bay-tennis-exhibition|Exhibition"])
        XCTAssertEqual(hub.menuHoverLabel, "Exhibition")
        // a pick on the TV opens its detail screen on the phone, and the TV is told it is open
        var sent: [[String: Any]] = []; hub.debugSent = { sent.append($0) }
        hub.receive(["type": "menuOpen", "session": "debug-hub", "message": "bay-tennis-exhibition"])
        XCTAssertEqual(hub.station, "bay-tennis-exhibition")
        XCTAssertTrue(hub.panelOpen)
        XCTAssertTrue(sent.contains { $0["action"] as? String == "menuPhone" && $0["mode"] as? String == "on" })
        hub.leaveStation()
        XCTAssertTrue(sent.contains { $0["action"] as? String == "menuPhone" && $0["mode"] as? String == "off" }, "closing it brings the TV back")
    }

    func testALockerColourOnTheTVIsSaved() {
        let hub = HubSession.shared, session = SportsSession.shared
        guard session.players.indices.contains(session.playerIndex) else { return XCTFail("a player") }
        let saved = session.players[session.playerIndex]
        defer { session.players[session.playerIndex] = saved; session.savePlayers() }
        hub.debugLive(); hub.debugMenu()
        hub.receive(["type": "menuLook", "session": "debug-hub", "message": "shirt|3FA9F5"])
        XCTAssertEqual(session.players[session.playerIndex].outfitHex("shirt")?.uppercased(), "3FA9F5")
        hub.receive(["type": "menuLook", "session": "debug-hub", "message": "shirt|"])
        XCTAssertNotEqual(session.players[session.playerIndex].outfitHex("shirt")?.uppercased(), "3FA9F5", "Kit: the kit's own colour again")
    }

    func testAMatchFromTheMenuLoadsBehindIt() {
        let hub = HubSession.shared
        hub.debugLive(); hub.debugMenu()
        XCTAssertEqual(hub.bayForLaunch(), "menu", "the menu's launches load behind it on the TV")
        hub.receive(["type": "menuOpen", "session": "debug-hub", "message": "bay-tennis-training"])
        XCTAssertEqual(hub.bayForLaunch(), "bay-tennis-training")
        XCTAssertEqual(hub.menuLaunchLabel, "Training")
    }

    /// A mode picked from the menu goes straight in: no START on the TV (Unity starts the match once it is built), and the TV shows
    /// the loading screen (venue art and tips) while it builds behind the menu.
    func testAMatchFromTheMenuStartsWithoutStartAndShowsTheLoadingScreen() {
        let hub = HubSession.shared, session = SportsSession.shared, displays = SportsDisplays.shared
        let savedExternal = displays.external, savedDisplay = session.displayConnected
        displays.external = UIWindow(frame: CGRect(x: 0, y: 0, width: 1920, height: 1080)); session.displayConnected = true
        defer { if session.active { session.end() }; displays.external = savedExternal; HubTestState.restore(display: savedDisplay) }
        // (no menuOpen here: in the test host the app's own hub boot clears the station it sets, as testTheTVsEventsReachThePhone shows)
        hub.debugLive(); hub.debugMenu()
        XCTAssertEqual(hub.bayForLaunch(), "menu")
        let covers = displays.coversShown, launches = hub.bayLaunches
        session.startTennis(opponent: nil, round: nil, mode: "exhibition", difficulty: 0.45, preview: false)
        XCTAssertEqual(hub.bayLaunches, launches + 1, "still built behind the menu")
        XCTAssertEqual(displays.coversShown, covers + 1, "the loading screen covers the TV")
    }
}
