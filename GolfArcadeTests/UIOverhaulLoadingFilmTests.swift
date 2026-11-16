import SwiftUI
import XCTest
@testable import GolfArcade

/// UI OVERHAUL 11-15: puts the loading screen on the simulator's screen as people load into a game (the art's slow push-in,
/// the sculpted title popping in and bobbing, the ready list arriving row by row, the bar filling) and holds it, while
/// `xcrun simctl io recordVideo` films the real screen (work/ui-overhaul-1115/film_phone.sh). The TV layout is shown scaled
/// to the phone's width on a dark card. Skipped unless UO_FILM_LIVE is set (a proof recorder, not a gate).
@MainActor
final class UIOverhaulLoadingFilmTests: XCTestCase {
    func testFilmLoadingScreens() async throws {
        guard ProcessInfo.processInfo.environment["UO_FILM_LIVE"] == "1" else { throw XCTSkip("UO_FILM_LIVE not set") }
        let s = SportsSession.shared, menu = TennisMenu.shared
        let saved = (s.sport, s.tennisVenue, s.golfCourse, s.bowlingVenue)
        let savedName = s.players.indices.contains(s.playerIndex) ? s.players[s.playerIndex].name : nil
        if savedName != nil { s.players[s.playerIndex].name = "Adnan" }
        defer {
            s.sport = saved.0; s.tennisVenue = saved.1; s.golfCourse = saved.2; s.bowlingVenue = saved.3; s.loading.cancel()
            if let savedName { s.players[s.playerIndex].name = savedName }
        }
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let screen = scene.screen.bounds
        // a black lead-in so the cut can find the start
        let lead = UIWindow(windowScene: scene); lead.frame = screen; lead.backgroundColor = .black; lead.windowLevel = .alert + 1
        lead.rootViewController = UIViewController(); lead.rootViewController?.view.backgroundColor = .black; lead.isHidden = false
        try await Task.sleep(for: .seconds(3)); lead.isHidden = true
        for id in ["tennis-resort", "golf-cliffside", "bowling-neon"] {
            let skin = try XCTUnwrap(MapSkin.all.first { $0.id == id })
            let venue = String(id.split(separator: "-", maxSplits: 1)[1])
            s.sport = skin.sport.rawValue
            switch skin.sport { case .tennis: s.tennisVenue = venue; case .golf: s.golfCourse = venue; case .bowling: s.bowlingVenue = venue }
            menu.debugShow(.loading, launch: MenuLaunch(sport: skin.sport == .golf ? .golf : .tennis, mode: skin.sport == .golf ? .round : .exhibition))
            for compact in [false, true] {
                s.loading.begin(now: LoadingModel.clockNow)
                let tvScale = screen.width / 1280
                let root = ZStack {
                    Color.black
                    if compact { LoadingScreen(menu: menu, compact: true) }
                    else { LoadingScreen(menu: menu, compact: false).frame(width: 1280, height: 720).scaleEffect(tvScale).frame(width: screen.width, height: 720 * tvScale) }
                }.ignoresSafeArea()
                let window = UIWindow(windowScene: scene)
                window.frame = screen; window.windowLevel = .alert; window.rootViewController = UIHostingController(rootView: root); window.isHidden = false
                let t0 = Date()
                while Date().timeIntervalSince(t0) < 4.5 {
                    let t = Date().timeIntervalSince(t0)
                    s.loading.reach(min(0.95, t / 4)); s.loading.tick(now: LoadingModel.clockNow)
                    try await Task.sleep(for: .milliseconds(50))
                }
                window.isHidden = true
            }
            s.loading.cancel()
        }
    }
}
