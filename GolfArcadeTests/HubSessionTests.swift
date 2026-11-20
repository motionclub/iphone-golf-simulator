import SwiftUI
import XCTest
@testable import GolfArcade

/// The menu's session, phone half: when the menu opens (HUB_BOOT), that with no TV it opens on the phone itself (PHONE_ONLY), that
/// only a station's own screens ever replace the controller (CONTROLLER_LOCK), the boot loading bar, and the loading screens' look
/// (written to $MENU_SNAP_DIR/hub-*.png). (The walk-around Plaza these began with was removed 2026-11-15.)
@MainActor
final class HubSessionTests: XCTestCase {
    func testUnityLifecycleDoesNotRepeatPauseOrRenderOnEnteringBackground() {
        let runtime = SportsRuntime.shared(), nc = NotificationCenter.default
        runtime.setForeground(true)
        for _ in 0..<3 {
            let before = runtime.debugLifecycleEvents().count
            nc.post(name: UIApplication.willResignActiveNotification, object: nil)
            nc.post(name: UIApplication.willResignActiveNotification, object: nil)
            nc.post(name: UIApplication.didEnterBackgroundNotification, object: nil)
            nc.post(name: UIApplication.didEnterBackgroundNotification, object: nil)
            // A repeated SwiftUI inactive update cannot overwrite Unity's paused state.
            runtime.setForeground(false)
            nc.post(name: UIApplication.willEnterForegroundNotification, object: nil)
            nc.post(name: UIApplication.didBecomeActiveNotification, object: nil)
            nc.post(name: UIApplication.didBecomeActiveNotification, object: nil)
            XCTAssertEqual(Array(runtime.debugLifecycleEvents().dropFirst(before)), ["resign", "background", "foreground", "active"])
        }
        let before = runtime.debugLifecycleEvents().count
        runtime.setForeground(false); runtime.setForeground(false); runtime.setForeground(true)
        XCTAssertEqual(Array(runtime.debugLifecycleEvents().dropFirst(before)), ["resign", "active"], "an invite/Control Center interruption is not backgrounding")
    }
    /// An online match plays on while the app is only covered (a banner, Control Center): Unity is not paused, so the other phone
    /// never hears a connected player whose game stopped (2026-11-11). Going to the background still pauses it, and it resumes.
    func testAnOnlineMatchKeepsUnityRunningWhileTheAppIsOnlyCovered() {
        let runtime = SportsRuntime.shared(), nc = NotificationCenter.default
        runtime.setForeground(true); runtime.keepPlayingWhenInactive = true
        defer { runtime.keepPlayingWhenInactive = false; runtime.setForeground(true) }
        var before = runtime.debugLifecycleEvents().count
        runtime.setForeground(false); runtime.setForeground(true)
        XCTAssertEqual(Array(runtime.debugLifecycleEvents().dropFirst(before)), ["resign-kept", "active-kept"])
        before = runtime.debugLifecycleEvents().count
        nc.post(name: UIApplication.willResignActiveNotification, object: nil)
        nc.post(name: UIApplication.didEnterBackgroundNotification, object: nil)
        nc.post(name: UIApplication.willEnterForegroundNotification, object: nil)
        nc.post(name: UIApplication.didBecomeActiveNotification, object: nil)
        XCTAssertEqual(Array(runtime.debugLifecycleEvents().dropFirst(before)), ["resign-kept", "pause", "background", "foreground", "active"])
        runtime.keepPlayingWhenInactive = false
        before = runtime.debugLifecycleEvents().count
        runtime.setForeground(false); runtime.setForeground(true)
        XCTAssertEqual(Array(runtime.debugLifecycleEvents().dropFirst(before)), ["resign", "active"], "off a match, covering pauses as before")
    }
    /// Coming back to the app (a call, the lock button, the home swipe): within the limits the player stays where they were, in the
    /// match and in the party, with nothing to tap; only past them is a match (3 min) or a party (10 min) left, with a line saying why.
    func testComingBackWithinTheLimitsKeepsTheGameAndTheParty() {
        let away = AwayPolicy()
        var t = Date(timeIntervalSince1970: 1_000)
        away.now = { t }
        XCTAssertEqual(away.returned(), 0, "covered only (a banner, Control Center): never away")
        away.left(); t += 5; away.left(); t += 55
        XCTAssertEqual(away.returned(), 60, accuracy: 0.001, "away since the first background, not the last")
        let match = MultiplayerTuning.awayLimitSeconds, party = MultiplayerTuning.partyPatienceSeconds
        for seconds in [1.0, 30, match - 1] {
            XCTAssertEqual(AwayPolicy.outcome(away: seconds, inOnlineMatch: true, inParty: true, droppedFromMatch: false), .stay, "\(seconds) s in a party's match")
            XCTAssertEqual(AwayPolicy.outcome(away: seconds, inOnlineMatch: true, inParty: false, droppedFromMatch: false), .stay, "\(seconds) s in a quick match")
        }
        XCTAssertEqual(AwayPolicy.outcome(away: party - 1, inOnlineMatch: false, inParty: true, droppedFromMatch: false), .stay)
        XCTAssertEqual(AwayPolicy.outcome(away: match + 1, inOnlineMatch: true, inParty: true, droppedFromMatch: false), .leaveMatch)
        XCTAssertEqual(AwayPolicy.outcome(away: 10, inOnlineMatch: true, inParty: true, droppedFromMatch: true), .leaveMatch, "the host already let them go")
        XCTAssertEqual(AwayPolicy.outcome(away: party + 1, inOnlineMatch: false, inParty: true, droppedFromMatch: false), .leaveParty)
        XCTAssertGreaterThan(party, match, "a party waits longer than a match")
    }
    private var savedDisplay = false
    override func setUp() async throws {
        savedDisplay = SportsSession.shared.displayConnected
        HubSession.shared.debugReset(); OnboardingFlow.shared.exitToMenu()
        SportsSession.shared.displayConnected = true   // (each test that is about no TV says so)
    }
    override func tearDown() async throws {
        HubTestState.restore(display: savedDisplay)
    }

    /// PHONE_ONLY: with no TV the menu is drawn on the phone itself (Unity's start says external: false and phoneOnly).
    func testNoTVThePlazaOpensOnThePhone() {
        let hub = HubSession.shared, menu = TennisMenu.shared
        SportsSession.shared.displayConnected = false
        for screen in [MenuScreen.title, .main, .character, .settings] {
            menu.debugShow(screen)
            XCTAssertTrue(hub.wanted, "no TV: the plaza is still the menu, on the phone (\(screen))")
        }
        var start: [String: Any]?; hub.debugSent = { if $0["action"] as? String == "start" { start = $0 } }
        hub.debugBoot(session: "phone", onPhone: true)
        XCTAssertEqual(start?["external"] as? Bool, false, "Unity draws the menu on the phone")
        XCTAssertEqual(start?["phoneOnly"] as? Bool, true)
        XCTAssertEqual(start?["menu"] as? Bool, true, "the menu, always")
        XCTAssertTrue(hub.drivesPhone); XCTAssertTrue(hub.onPhone)
    }

    /// CONTROLLER_LOCK: the menu is the only menu, with a TV or without. A station's own screens open as its panel; any other screen
    /// (home, the old play / online / lobby screens) ends the station and the controller comes back.
    func testThePlazaIsTheOnlyMenuAndOldScreensNeverShow() {
        let hub = HubSession.shared, menu = TennisMenu.shared
        for tv in [true, false] {
            SportsSession.shared.displayConnected = tv
            hub.debugReset(); hub.debugLive(onPhone: !tv); menu.debugShow(.main)
            XCTAssertTrue(hub.wanted); XCTAssertFalse(hub.panelOpen); XCTAssertTrue(hub.drivesPhone)
            hub.receive(["type": "menuOpen", "session": "debug-hub", "message": "desk-settings"]); XCTAssertTrue(hub.panelOpen, "a station's screen is its panel")
            for screen in [MenuScreen.party, .localChoice, .onlineChoice, .online(.entry), .online(.lobby), .online(.results), .hub(.tennis), .gameSelect, .multiplayer] {
                hub.receive(["type": "menuOpen", "session": "debug-hub", "message": "desk-settings"])
                menu.debugShow(screen); hub.evaluate()
                XCTAssertEqual(menu.screen, .main, "\(screen) never shows on the phone (tv \(tv))"); XCTAssertNil(hub.station); XCTAssertFalse(hub.panelOpen)
            }
            // a lobby screen asked for with no station open (an old path) is turned away too
            menu.debugShow(.online(.lobby)); hub.evaluate(); XCTAssertEqual(menu.screen, .main)
            // the panel's Done goes home, still on the menu
            hub.receive(["type": "menuOpen", "session": "debug-hub", "message": "desk-settings"]); hub.leaveStation()
            XCTAssertEqual(menu.screen, .main); XCTAssertFalse(hub.panelOpen); XCTAssertTrue(hub.wanted)
        }
    }

    func testMatchTakesTheRuntimeAndThePlazaReloadsAfter() {
        let hub = HubSession.shared
        SportsSession.shared.displayConnected = true; TennisMenu.shared.debugShow(.main)
        hub.debugLive()
        hub.runtimeTaken()
        XCTAssertEqual(hub.phase, .suspended); XCTAssertFalse(hub.loaded, "the match scene replaced Hub.unity")
        hub.displayLost(); XCTAssertEqual(hub.phase, .off)
    }

    /// LOADING: the TV's loading bar follows Unity's real progress (runtime, scene, plaza build), never goes back, reads 100 % at
    /// ready, then the loading screen fades into the arrival (hubArrive). Back from a match the start says `screen: home` and there is
    /// no arrival.
    func testBootLoadingBarFollowsUnityAndFadesIntoTheArrival() async throws {
        let hub = HubSession.shared
        SportsSession.shared.displayConnected = true; TennisMenu.shared.debugShow(.title)
        var sent: [String] = [], starts: [[String: Any]] = []
        hub.debugSent = { sent.append($0["action"] as? String ?? ""); if $0["action"] as? String == "start" { starts.append($0) } }
        hub.debugBoot(session: "boot")
        XCTAssertEqual(starts.last?["menu"] as? Bool, true); XCTAssertNil(starts.last?["screen"], "a fresh boot has its arrival")
        XCTAssertTrue(hub.drivesPhone, "the TV shows the loading screen (TennisTVRoot), the phone its bar")
        XCTAssertEqual(hub.loadProgress, 0); XCTAssertEqual(hub.loadStage, "Starting up")
        hub.receive(["type": "loadProgress", "session": "boot", "message": "0.5"]); XCTAssertEqual(hub.loadProgress, 0.21, accuracy: 0.001)
        hub.receive(["type": "buildProgress", "session": "boot", "message": "0.5"]); XCTAssertEqual(hub.loadProgress, 0.625, accuracy: 0.001)
        hub.receive(["type": "loadProgress", "session": "boot", "message": "0.2"]); XCTAssertEqual(hub.loadProgress, 0.625, accuracy: 0.001, "the bar never goes back")
        XCTAssertEqual(hub.loadStage, "Building the Plaza")
        hub.receive(["type": "buildProgress", "session": "other", "message": "1"]); XCTAssertEqual(hub.loadProgress, 0.625, accuracy: 0.001, "another session's progress is ignored")
        hub.receive(["type": "buildProgress", "session": "boot", "message": "1"]); XCTAssertEqual(hub.loadStage, "Opening the gates")
        XCTAssertFalse(sent.contains("hubArrive"))
        hub.receive(["type": "ready", "session": "boot"])
        XCTAssertEqual(hub.loadProgress, 1); XCTAssertEqual(hub.phase, .live); XCTAssertTrue(hub.arriving, "100 %: the full bar holds, then fades")
        XCTAssertNotNil(hub.pace.readyAt, "ready: the bar eases to full")
        try await Task.sleep(for: .seconds(HubSession.readyHold + LoadingPace.finishLongest + 0.15))   // (the bar fills the rest first)
        XCTAssertTrue(sent.contains("hubArrive"), "the fly-in starts as the loading screen fades")
        XCTAssertFalse(hub.arriving)
        // back from a finished match: straight onto the menu's Home, no fly-in
        hub.runtimeTaken(bay: "bay-tennis-exhibition"); hub.sessionEnded(finished: true); sent.removeAll()
        XCTAssertEqual(hub.returnBay, "bay-tennis-exhibition")
        hub.debugBoot(session: "back")
        XCTAssertEqual(starts.last?["screen"] as? String, "home", "back from a match: the start opens the menu on Home")
        hub.receive(["type": "ready", "session": "back"])
        XCTAssertFalse(hub.arriving); XCTAssertNil(hub.returnBay, "the flag has done its work")
        try await Task.sleep(for: .seconds(HubSession.readyHold + 0.15))
        XCTAssertFalse(sent.contains("hubArrive"))
    }

    /// The bar never sits still and never leaps (Adnan 10-26: "stuck on 12, then instantly fills"; 10-28: "freezing, then
    /// loading sporadically"): one steady speed to 90 % over the expected time, a creep that never stops or fills, and from
    /// "ready" an ease to full that starts at the speed the bar had.
    func testLoadingPaceIsSteadyAndEasesToFull() {
        var pace = LoadingPace(start: 100, expected: 4)
        var last = pace.value(at: 100), steps: [Double] = []
        for k in 1...400 {   // 20 s at 20 Hz, never ready
            let v = pace.value(at: 100 + Double(k) * 0.05)
            XCTAssertGreaterThan(v, last, "always moving (t = \(Double(k) * 0.05))"); steps.append(v - last); last = v
        }
        XCTAssertEqual(steps[0], steps[70], accuracy: 1e-9, "one steady speed while loading")
        XCTAssertEqual(pace.value(at: 104), LoadingPace.cruise, accuracy: 1e-9)
        XCTAssertLessThan(last, 0.99, "never full before the load is ready")
        XCTAssertLessThanOrEqual(steps.max()!, (LoadingPace.cruise - LoadingPace.floor) / 4 * 0.05 + 1e-9, "never a leap")
        // ready early: its top speed stays under three times what it had, and it lands on 100 % at rest
        pace.markReady(at: 101)
        let before = pace.value(at: 101), speed = (LoadingPace.cruise - LoadingPace.floor) / 4
        var prev = before, biggest = 0.0
        for k in 1...Int(LoadingPace.finishLongest * 100) {
            let v = pace.value(at: 101 + Double(k) * 0.01); XCTAssertGreaterThanOrEqual(v, prev); biggest = max(biggest, v - prev); prev = v
        }
        XCTAssertLessThanOrEqual(biggest, speed * 0.01 * 3.5, "no snap to full")
        XCTAssertEqual(pace.value(at: pace.end), 1, accuracy: 1e-9); XCTAssertTrue(pace.isFull(at: pace.end))
        XCTAssertLessThanOrEqual(pace.end - 100, LoadingPace.longestExpected + LoadingPace.finishLongest)
        // a failure stops it
        var failed = LoadingPace(start: 0, expected: 4); failed.hold(at: 2)
        XCTAssertEqual(failed.value(at: 9), failed.value(at: 2)); XCTAssertFalse(failed.isFull(at: 99))
    }

    /// The approved loading screen (D) on the TV and the phone while the plaza boots, at 68 % (written to $MENU_SNAP_DIR).
    func testLoadingScreenSnapshots() async throws {
        let hub = HubSession.shared
        SportsSession.shared.displayConnected = true; TennisMenu.shared.debugShow(.title)
        hub.debugBoot(session: "snap"); hub.receive(["type": "buildProgress", "session": "snap", "message": "0.58"])
        XCTAssertEqual(Int((hub.loadProgress * 100).rounded()), 68)
        try await save(HubLoadingScreen(hub: hub), "hub-loading-tv", size: CGSize(width: 1280, height: 720))
        try await save(MenuControllerView(), "hub-loading-phone")
        hub.receive(["type": "ready", "session": "snap"])
        try await save(HubLoadingScreen(hub: hub), "hub-loading-tv-100", size: CGSize(width: 1280, height: 720))
    }

    /// LOADING ACTION (2026-11-13): every shot is in the app, a boot plays each one once before any comes back, never the same shot
    /// twice in a row (across a reshuffle too), and a boot never opens on the shot the last one ended on.
    func testLoadingShotsShuffleThroughTheWholePool() {
        XCTAssertEqual(LoadingShots.pool.count, 25, "the 25 painted loading pictures, nothing older")
        for shot in LoadingShots.pool { XCTAssertTrue(shot.asset.hasPrefix("load-"), shot.asset) }
        for shot in LoadingShots.pool { XCTAssertNotNil(UIImage(named: shot.asset), shot.asset) }
        // UI OVERHAUL 11-15: map names stand alone (no sport labels), and every map of all three sports is in the reel
        for shot in LoadingShots.pool { for word in ["TENNIS", "GOLF", "BOWLING"] { XCTAssertFalse(shot.label.contains(word), shot.label) } }
        XCTAssertEqual(Set(LoadingShots.pool.map(\.label).filter { !$0.isEmpty }).count, 10, "all ten maps")
        for last in 0..<LoadingShots.pool.count {
            var reel = LoadingShots.Reel(last: last)
            XCTAssertNotEqual(reel.index, last, "a boot does not open on the last boot's shot")
            var seen = [reel.index], prev = reel.index
            for _ in 1..<(LoadingShots.pool.count * 2) { reel.advance(); XCTAssertNotEqual(reel.index, prev); prev = reel.index; seen.append(reel.index) }
            XCTAssertEqual(Set(seen.prefix(LoadingShots.pool.count)).count, LoadingShots.pool.count, "every shot once before any repeats")
        }
    }

    /// Four of the loading shots on the TV at 68 % (written to $MENU_SNAP_DIR as hub-loading-shot-<n>).
    func testLoadingShotSnapshots() async throws {
        let hub = HubSession.shared
        SportsSession.shared.displayConnected = true; TennisMenu.shared.debugShow(.title)
        hub.debugBoot(session: "snap-shots"); hub.receive(["type": "buildProgress", "session": "snap-shots", "message": "0.58"])
        defer { LoadingShots.pinned = nil }
        for n in [3, 12, 20, 24] {
            LoadingShots.pinned = n
            try await save(HubLoadingScreen(hub: hub), "hub-loading-shot-\(n)", size: CGSize(width: 1280, height: 720))
        }
    }

    /// A boot that is given up (the plaza moving screens, the TV going away) is ended in Unity too. 2026-10-25 device log: the
    /// TV connected mid-boot, Unity dropped the TV's start while the phone's load ran, and the boot sat until Try again.
    func testAnAbandonedBootIsEndedInUnity() {
        let hub = HubSession.shared
        SportsSession.shared.displayConnected = true; TennisMenu.shared.debugShow(.title)
        var sent: [String] = []; hub.debugSent = { sent.append($0["action"] as? String ?? "") }
        hub.debugBoot(session: "abandoned")
        XCTAssertEqual(sent, ["start"])
        hub.displayLost()
        XCTAssertEqual(sent, ["start", "end"], "Unity stops loading the old session, so the next start is not dropped")
    }

    /// The venue loading screens (2026-10-25): each venue's art, both of a load's tip cards and the bar at 50 % on the TV, and the
    /// phone's upright version (written to $MENU_SNAP_DIR).
    func testVenueLoadingSnapshots() async throws {
        let session = SportsSession.shared, menu = TennisMenu.shared
        let saved = (session.sport, session.tennisVenue, session.golfCourse)
        defer { session.sport = saved.0; session.tennisVenue = saved.1; session.golfCourse = saved.2; session.loading.cancel() }
        let start = LoadingModel.clockNow
        for (sport, venue) in [(Sport.tennis, "resort"), (.tennis, "skyscraper"), (.tennis, "volcano"),
                               (.golf, "cliffside"), (.golf, "wildisles"), (.golf, "magma")] {
            session.sport = sport.rawValue
            if sport == .tennis { session.tennisVenue = venue } else if sport == .golf { session.golfCourse = venue }
            menu.debugShow(.loading, launch: MenuLaunch(sport: sport, mode: sport == .golf ? .round : .exhibition))
            for tip in 1...LoadingModel.tipsPerLoad {
                session.loading.begin(now: start); session.loading.reach(0.5)
                session.loading.tick(now: start.addingTimeInterval(LoadingModel.firstTipDelay + LoadingModel.tipInterval * Double(tip - 1) + 0.1))
                XCTAssertEqual(session.loading.tipNumber, tip)
                XCTAssertGreaterThan(session.loading.displayProgress, LoadingPace.floor); XCTAssertLessThan(session.loading.displayProgress, LoadingPace.cruise)
                try await save(LoadingScreen(menu: menu, compact: false), "venue-\(sport.rawValue)-\(venue)-tv-\(tip)", size: CGSize(width: 1280, height: 720))
                if tip == 1 { try await save(LoadingScreen(menu: menu, compact: true), "venue-\(sport.rawValue)-\(venue)-phone") }
            }
        }
    }

    /// The Daily Challenge's own loading screen (2026-11-15): its tab, name and facts in place of a course's, and its own tips
    /// (written to $MENU_SNAP_DIR as daily-loading-tv-1/2 and daily-loading-phone).
    func testDailyChallengeLoadingSnapshots() async throws {
        let session = SportsSession.shared, menu = TennisMenu.shared
        let saved = (session.sport, session.golfCourse)
        defer { session.sport = saved.0; session.golfCourse = saved.1; session.loading.cancel(); menu.debugShow(.title) }
        session.sport = "golf"; session.golfCourse = "cliffside"
        var launch = MenuLaunch(sport: .golf, mode: .round); launch.holeInOne = 20261115
        menu.debugShow(.loading, launch: launch)
        let start = LoadingModel.clockNow
        for tip in 1...LoadingModel.tipsPerLoad {
            session.loading.begin(now: start); session.loading.reach(0.5)
            session.loading.tick(now: start.addingTimeInterval(LoadingModel.firstTipDelay + LoadingModel.tipInterval * Double(tip - 1) + 0.1))
            XCTAssertEqual(session.loading.tipNumber, tip)
            let shown = try XCTUnwrap(session.loading.tip)
            XCTAssertTrue(GameTips.dailyHoleInOne.contains { $0.text == shown }, "a Daily Challenge tip, not a golf one: \(shown)")
            try await save(LoadingScreen(menu: menu, compact: false), "daily-loading-tv-\(tip)", size: CGSize(width: 1280, height: 720))
            if tip == 1 { try await save(LoadingScreen(menu: menu, compact: true), "daily-loading-phone") }
        }
        for tip in GameTips.dailyHoleInOne {
            XCTAssertLessThanOrEqual(tip.text.count, 130, tip.text); XCTAssertLessThanOrEqual(tip.title.count, 24, tip.title)
        }
        XCTAssertEqual(Set(GameTips.dailyHoleInOne.map(\.text)).count, GameTips.dailyHoleInOne.count)
    }

    private func save<V: View>(_ view: V, _ name: String, size: CGSize = CGSize(width: 402, height: 874)) async throws {
        let folder = URL(fileURLWithPath: ProcessInfo.processInfo.environment["MENU_SNAP_DIR"] ?? NSTemporaryDirectory() + "tennis-menu", isDirectory: true)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let host = UIHostingController(rootView: view)
        let window = UIWindow(windowScene: scene)
        window.frame = CGRect(origin: .zero, size: size); window.rootViewController = host; window.isHidden = false
        host.view.frame = window.bounds; host.view.layoutIfNeeded()
        try await Task.sleep(for: .seconds(1.0))
        let image = UIGraphicsImageRenderer(size: size).image { _ in host.view.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
        try XCTUnwrap(image.pngData()).write(to: folder.appendingPathComponent("\(name).png"))
        window.isHidden = true
    }
}

/// Stations: every old menu destination opens from the station the TV's menu sends for it (menuOpen; ROUTE_ALL), and a locker
/// colour pick goes to the menu hero at once (LOCKER_LIVE, phone half).
@MainActor
final class HubRouteTests: XCTestCase {
    private var savedDisplay = false
    override func setUp() async throws { savedDisplay = SportsSession.shared.displayConnected; HubSession.shared.debugReset(); OnboardingFlow.shared.exitToMenu(); SportsSession.shared.displayConnected = true; TennisMenu.shared.debugShow(.main) }
    override func tearDown() async throws { HubTestState.restore(display: savedDisplay) }

    /// destination -> (the stations the TV's menu opens it with, the phone screen that must come up)
    func testEveryOldMenuDestinationIsReachable() {
        let hub = HubSession.shared, menu = TennisMenu.shared
        // every bench is one sport and one mode (BENCH_ROUTES): the golf benches never lead to tennis
        let table: [(String, [String], (MenuScreen) -> Bool)] = [
            ("Locker", ["look-mirror", "emote-mirror", "rack-club"], { $0 == .character }),
            ("Settings", ["desk-settings"], { $0 == .settings }),
            ("How to play", ["screen-howto"], { $0 == .howTo }),
            ("Island Circuit", ["shelf-trophies"], { $0 == .campaign }),
            ("Quick match", ["bay-tennis-exhibition"], { $0 == .exhibition }),
            ("Training", ["bay-tennis-training"], { $0 == .training }),
            ("Calibration", ["bay-tennis-calibration"], { _ in TennisMenu.shared.launch?.mode == .calibration }),
            ("Golf round (course picker)", ["bay-golf-round"], { $0 == .map && TennisMenu.shared.mapSport == .golf }),
            ("Online tennis", ["bay-tennis-online"], { $0 == .main && HubSession.shared.onlineBench == .tennis && HubSession.shared.station == "bay-tennis-online" }),
            ("Online golf", ["bay-golf-online"], { $0 == .main && HubSession.shared.onlineBench == .golf && HubSession.shared.station == "bay-golf-online" }),
            ("Local golf", ["bay-golf-pass"], { $0 == .localPlayers }),   // how many players, then straight into the round
        ]
        var report: [String] = []
        for (name, spots, reached) in table {
            for spot in spots {
                hub.debugReset(); menu.debugShow(.main); hub.debugLive(session: "r")
                XCTAssertNotNil(HubSession.route(spot), spot)
                hub.receive(["type": "menuOpen", "session": "r", "message": spot])   // picked on the TV's menu (Unity reports the station)
                XCTAssertTrue(reached(menu.screen), "\(name) via \(spot): reached \(menu.screen)")
                report.append("\(name): \(spot) from the TV's menu")
            }
        }
        if let dir = ProcessInfo.processInfo.environment["MENU_SNAP_DIR"] {
            try? (report.joined(separator: "\n") + "\n").write(toFile: dir + "/route_all.txt", atomically: true, encoding: .utf8)
        }
    }

    func testStationKeepsThePlazaOnTheTVAndDoneReturns() {
        let hub = HubSession.shared, menu = TennisMenu.shared
        hub.debugLive(session: "r")
        hub.receive(["type": "menuOpen", "session": "r", "message": "desk-settings"])
        XCTAssertEqual(menu.screen, .settings); XCTAssertEqual(hub.station, "desk-settings")
        XCTAssertTrue(hub.wanted, "the TV keeps the menu while the phone shows the station")
        var sent: [[String: Any]] = []; hub.debugSent = { sent.append($0) }
        hub.leaveStation()
        XCTAssertNil(hub.station); XCTAssertEqual(menu.screen, .main)
        XCTAssertTrue(sent.contains { $0["action"] as? String == "menuPhone" && $0["mode"] as? String == "off" }, "the TV's menu is told the phone's screen closed")
        // the panel's own back to home also ends the station
        hub.receive(["type": "menuOpen", "session": "r", "message": "look-mirror"]); XCTAssertEqual(menu.screen, .character)
        menu.tap("lk-done"); hub.evaluate()
        XCTAssertNil(hub.station)
    }

    func testALockerPickIsSentToThePlazaHeroAtOnce() {
        let hub = HubSession.shared, session = SportsSession.shared
        let saved = session.players, index = session.playerIndex
        defer { session.players = saved; session.playerIndex = index }
        session.players = [Player(name: "Live", colorIndex: 0)]; session.playerIndex = 0
        hub.debugLive(session: "r")
        var looks: [[String: Any]] = []; hub.debugSent = { if $0["action"] as? String == "hubLook" { looks.append($0) } }
        session.players[0].setOutfit("shirt", hue: 0.33, shade: 0); session.savePlayers()
        XCTAssertEqual(looks.count, 1, "the save sends the look in the same call")
        XCTAssertEqual(looks.last?["shirt"] as? String, session.players[0].outfitHex("shirt"))
        session.savePlayers(); XCTAssertEqual(looks.count, 1, "an unchanged look is not re-sent")
    }
}

/// The hub tests drive the shared menu, session and lobby (an online bay route opens the online screens on the shared
/// MultiplayerService): put them all back so the suites that run after start clean.
@MainActor enum HubTestState {
    static func restore(display: Bool) {
        if SportsSession.shared.active { SportsSession.shared.end() }
        let service = MultiplayerService.shared
        service.cancelSearch(); if service.lobby != nil { service.leave() }; service.stopBrowsing()
        HubSession.shared.debugReset()
        // stations tap through the locker (rack-club picks the club slot): put it back on its opening shelf for the next suite
        TennisMenu.shared.debugShow(.character); for id in ["lk-tab-gear", "lk-sport-tennis", "lk-slot-skin"] { TennisMenu.shared.tap(id) }
        TennisMenu.shared.debugShow(.title)
        SportsSession.shared.displayConnected = display
    }
}
