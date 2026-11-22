import SwiftUI
import XCTest
@testable import GolfArcade

/// UI OVERHAUL 11-15 ("UI overhaul.zip" → 01 Current UI): every map's skin is complete, and the phone's controllers and loading
/// screens render in it (written to $UO_SNAP_DIR for the proof boards next to the design boards).
@MainActor
final class UIOverhaulSnapshotTests: XCTestCase {
    func testEveryMapHasItsSculptedPiecesAndLoadingArt() {
        XCTAssertEqual(MapSkin.all.count, 9)   // 2026-11-21: three open-air bowling alleys replace the four indoor ones
        for skin in MapSkin.all {
            // the open-air bowling alleys (11-21) have no sculpted pieces yet: their HUD draws plain plates in the map's colours
            if skin.sport != .bowling {
                XCTAssertNotNil(skin.titleImage, "\(skin.id) title")
                XCTAssertNotNil(skin.plateImage, "\(skin.id) plate")
            }
            if skin.sport == .tennis { XCTAssertNotNil(skin.eventImage, "\(skin.id) point banner") }
            for art in skin.loadingArt { XCTAssertNotNil(MapSkin.image(art), art) }
            // map names stand alone: no sport words in a title
            for word in ["TENNIS", "GOLF", "BOWLING"] { XCTAssertFalse(skin.title.uppercased().contains(word)) }
        }
        XCTAssertEqual(MapSkin.of(sport: "golf", venue: "wildisles+9").id, "golf-wildisles")
        XCTAssertEqual(MapSkin.of(sport: "bowling", venue: "magma").id, "bowling-crater")
        XCTAssertEqual(MapSkin.of(sport: "tennis", venue: "nowhere").id, "tennis-resort")
    }

    func testControllerAndLoadingSnapshots() async throws {
        let s = SportsSession.shared, menu = TennisMenu.shared
        let saved = (s.sport, s.tennisVenue, s.golfCourse, s.bowlingVenue, s.ready, s.paused, s.setupStage, s.tennisPhase)
        let savedName = s.players.indices.contains(s.playerIndex) ? s.players[s.playerIndex].name : nil
        if let _ = savedName { s.players[s.playerIndex].name = "Adnan" }
        defer {
            s.sport = saved.0; s.tennisVenue = saved.1; s.golfCourse = saved.2; s.bowlingVenue = saved.3; s.ready = saved.4; s.paused = saved.5
            s.setupStage = saved.6; s.tennisPhase = saved.7; s.loading.cancel(); s.timingPrompt = false
            if let savedName { s.players[s.playerIndex].name = savedName }
        }
        let start = LoadingModel.clockNow
        for skin in MapSkin.all {
            let venue = String(skin.id.split(separator: "-", maxSplits: 1)[1])
            s.sport = skin.sport.rawValue
            switch skin.sport { case .tennis: s.tennisVenue = venue; case .golf: s.golfCourse = venue; case .bowling: s.bowlingVenue = venue }
            // loading at 68 % (board 11)
            menu.debugShow(.loading, launch: MenuLaunch(sport: skin.sport == .golf ? .golf : .tennis, mode: skin.sport == .golf ? .round : .exhibition))
            s.loading.begin(now: start); s.loading.reach(0.68)
            s.loading.tick(now: start.addingTimeInterval(LoadingModel.firstTipDelay + 0.1))
            try await save(LoadingScreen(menu: menu, compact: false), "loading-\(skin.id)-tv", size: CGSize(width: 1280, height: 720))
            try await save(LoadingScreen(menu: menu, compact: true), "loading-\(skin.id)-phone")
            s.loading.cancel()
            s.ready = true; s.paused = false; s.setupStage = .playing
            switch skin.sport {
            case .tennis:
                s.tennisPhase = "serve"
                try await save(TennisRacketController(session: s), "controller-\(skin.id)-serve")
                s.tennisPhase = "rally"; s.stamina = 0.82
                try await save(TennisRacketController(session: s), "controller-\(skin.id)-rally")
                s.setupStage = .ready
                try await save(TennisRacketController(session: s), "controller-\(skin.id)-ready")
                s.setupStage = .playing
            case .golf:
                var r = GolfControllerReading.waiting
                r.hole = 1; r.name = "Hole 1"; r.par = 4; r.yards = 416; r.wind = 0; r.clubIndex = 0; r.clubName = "Driver"; r.clubYards = 240
                s.golfController = r; s.golfPhase = "Aim"; s.golfShotReady = true
                try await save(GolfPhoneController(session: s), "controller-\(skin.id)")
            case .bowling:
                s.bowlingState = "Setup|Adnan|4|1|20|Good|17.2|5|300|0|1|0|0"
                try await save(BowlingPhoneController(session: s), "controller-\(skin.id)")
            }
        }
    }

    /// 11-16: phone-only (handheld) decks in every golf and bowling skin, the Daily Challenge's loading in the map UI (DAILY
    /// CHALLENGE on the course plate, no old gold header), and the golf lesson wearing its real map (Cliffside), not the last pick.
    func testHandheldDailyAndLessonSnapshots() async throws {
        let s = SportsSession.shared, menu = TennisMenu.shared
        let saved = (s.sport, s.golfCourse, s.bowlingVenue, s.ready, s.paused, s.setupStage)
        let savedName = s.players.indices.contains(s.playerIndex) ? s.players[s.playerIndex].name : nil
        if savedName != nil { s.players[s.playerIndex].name = "Adnan" }
        defer {
            s.sport = saved.0; s.golfCourse = saved.1; s.bowlingVenue = saved.2; s.ready = saved.3; s.paused = saved.4; s.setupStage = saved.5
            s.loading.cancel(); s.debugPhonePlay(false); LessonCenter.shared.end()
            if let savedName { s.players[s.playerIndex].name = savedName }
        }
        let start = LoadingModel.clockNow
        // the Daily Challenge loading (TV + phone)
        s.sport = "golf"; s.golfCourse = "cliffside"
        var daily = MenuLaunch(sport: .golf, mode: .round); daily.holeInOne = 20261116
        menu.debugShow(.loading, launch: daily)
        s.loading.begin(now: start); s.loading.reach(0.68); s.loading.tick(now: start.addingTimeInterval(LoadingModel.firstTipDelay + 0.1))
        try await save(LoadingScreen(menu: menu, compact: false), "loading-golf-daily-tv", size: CGSize(width: 1280, height: 720))
        try await save(LoadingScreen(menu: menu, compact: true), "loading-golf-daily-phone")
        s.loading.cancel()
        // the golf lesson on Cliffside whatever course was picked last
        s.golfCourse = "magma"; LessonCenter.shared.begin(.golf)
        XCTAssertEqual(s.shownGolfCourse, "cliffside"); XCTAssertEqual(MapSkin.current.id, "golf-cliffside")
        menu.debugShow(.loading, launch: MenuLaunch(sport: .golf, mode: .tutorial))
        s.loading.begin(now: start); s.loading.reach(0.4)
        try await save(LoadingScreen(menu: menu, compact: true), "loading-golf-lesson-phone")
        s.loading.cancel(); LessonCenter.shared.end()
        XCTAssertEqual(s.shownGolfCourse, "magma")
        // handheld decks
        s.debugPhonePlay(true); s.ready = true; s.paused = false; s.setupStage = .playing
        for skin in MapSkin.all where skin.sport != .tennis {
            let venue = String(skin.id.split(separator: "-", maxSplits: 1)[1])
            s.sport = skin.sport.rawValue
            if skin.sport == .golf {
                s.golfCourse = venue
                var r = GolfControllerReading.waiting
                r.hole = 1; r.name = "Hole 1"; r.par = 4; r.yards = 416; r.wind = 0; r.clubIndex = 0; r.clubName = "Driver"; r.clubYards = 240
                s.golfController = r; s.golfPhase = "Aim"; s.golfShotReady = true
                try await save(GolfPhoneController(session: s), "handheld-controller-\(skin.id)")
            } else {
                s.bowlingVenue = venue
                s.bowlingState = "Setup|Adnan|4|1|20|Good|17.2|5|300|0|1|0|0"
                try await save(BowlingPhoneController(session: s), "handheld-controller-\(skin.id)")
            }
        }
    }

    private func save<V: View>(_ view: V, _ name: String, size: CGSize = CGSize(width: 402, height: 874)) async throws {
        let folder = URL(fileURLWithPath: ProcessInfo.processInfo.environment["UO_SNAP_DIR"] ?? NSTemporaryDirectory() + "ui-overhaul", isDirectory: true)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let host = UIHostingController(rootView: view)
        let window = UIWindow(windowScene: scene)
        window.frame = CGRect(origin: .zero, size: size); window.rootViewController = host; window.isHidden = false
        host.view.frame = window.bounds; host.view.layoutIfNeeded()
        try await Task.sleep(for: .seconds(0.8))
        let image = UIGraphicsImageRenderer(size: size).image { _ in host.view.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
        try XCTUnwrap(image.pngData()).write(to: folder.appendingPathComponent("\(name).png"))
        window.isHidden = true
    }
}
