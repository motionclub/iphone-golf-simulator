import XCTest
import SwiftUI
@testable import GolfArcade

/// The first-launch TV screens, the phone during them, and the lesson's coaching over the game, rendered for review
/// (proof/onboarding). Output: $ONB_SNAP_DIR, else $TMPDIR/onboarding.
@MainActor final class OnboardingSnapshotTests: XCTestCase {
    private var folder: URL {
        let url = ProcessInfo.processInfo.environment["ONB_SNAP_DIR"].map { URL(fileURLWithPath: $0) }
            ?? FileManager.default.temporaryDirectory.appendingPathComponent("onboarding")
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }
    private func save<V: View>(_ view: V, _ name: String, _ size: CGSize, wait: Double = 1.4) async throws {
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let host = UIHostingController(rootView: view)
        host.safeAreaRegions = []
        let window = UIWindow(windowScene: scene)
        window.frame = CGRect(origin: .zero, size: size); window.rootViewController = host; window.isHidden = false
        host.view.frame = window.bounds; host.view.layoutIfNeeded()
        try await Task.sleep(for: .seconds(wait))
        let image = UIGraphicsImageRenderer(size: size).image { _ in host.view.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
        try XCTUnwrap(image.pngData()).write(to: folder.appendingPathComponent("\(name).png"))
        window.isHidden = true
    }
    private let tv = CGSize(width: 1280, height: 720), phone = CGSize(width: 402, height: 874)

    private func player() -> () -> Void {
        let session = SportsSession.shared, saved = session.players, index = session.playerIndex
        var p = Player(name: "Adnan", colorIndex: 0)
        p.setSkin(0.45); p.setOutfitHex("shirt", "1F5BD8"); p.setOutfit("shorts", hue: 0.62, shade: -0.5)
        session.players = [p]; session.playerIndex = 0
        return { session.players = saved; session.playerIndex = index }
    }

    func testOnboardingScreens() async throws {
        let restore = player(); defer { restore() }
        let defaults = UserDefaults(suiteName: "onb-snap-\(UUID())")!
        let store = OnboardingStore(defaults: defaults)
        store.characterInitialized = true
        let progress = SportProgress(defaults: defaults)
        let flow = OnboardingFlow(store: store, progress: progress, arguments: [])
        let steps: [(OnboardingStep, String?, String)] = [
            (.hello, nil, "01-hello"), (.controller, nil, "02-controller"), (.room, nil, "03-room"),
            (.player, "shirt", "04-player"), (.card, nil, "05-card"), (.choose, "golf", "06-choose"),
            (.lesson(.golf), nil, "07-lesson-paused"), (.reward(.golf), nil, "08-reward-golf")
        ]
        for (step, focus, name) in steps {
            if step == .reward(.golf) { progress.completeTutorial(.golf) }   // completed(.golf) records it before the reward shows
            flow.move(to: step); if let focus { flow.focus(focus) }
            try await save(OnboardingTV(flow: flow), "tv-\(name)", tv, wait: step == .player || step == .card || step == .reward(.golf) ? 2.5 : 1.2)
        }
        flow.move(to: .controller); flow.select()
        try await save(OnboardingTV(flow: flow), "tv-02b-controller-pressed", tv)
        flow.move(to: .player)
        try await save(OnboardingRemote(flow: flow), "phone-remote-player", phone)
        try await save(OnboardingConnectScreen(), "phone-connect", phone)
    }

    func testLessonCoachingOverTheGame() async throws {
        let center = LessonCenter.shared
        defer { center.end() }
        let session = SportsSession.shared
        let saved = (session.active, session.ready, session.sport, session.setupStage)
        session.active = true; session.ready = true; session.sport = "golf"; session.loading.skip()
        defer { session.active = saved.0; session.ready = saved.1; session.sport = saved.2; session.setupStage = saved.3 }
        let backdrop = UIImage(named: "course-golf-cliffside.jpg")
        func shot<V: View>(_ name: String, _ hud: V) async throws {
            try await save(ZStack { if let backdrop { Image(uiImage: backdrop).resizable().scaledToFill() }; hud }.frame(width: 1280, height: 720).clipped(), name, tv)
        }
        center.receive(#"{"kind":"station","sport":"golf","index":1,"count":8,"key":"distance","name":"Distance","title":"Backswing = distance","ask":"Land the ball near the YELLOW flag. Take the phone back to shoulder height, then swing.","hint":"Stop when your hands reach your shoulder. On the TV, stop the meter in the gold band.","tips":["How far back you take the phone is how far the ball flies.","Hip high is about half; up behind you is full.","Swinging harder adds nothing: just commit through the ball."]}"#)
        try await shot("hud-01-station", LessonHUD(center: center, session: session))
        center.receive(#"{"kind":"attempt","result":"miss","grade":"GOOD","text":"Long! That was a full backswing, so it flew all 150 yards.","misses":2,"read":[["BACK","100%",0],["CARRY","150 yd",0],["COMMIT","full",1],["FACE","3° open",1]]}"#)
        try await shot("hud-02-miss-hint", LessonHUD(center: center, session: session))
        center.receive(#"{"kind":"attempt","result":"pass","grade":"GREAT!","text":"Right on the number. How far back you go is how far it flies.","misses":2,"read":[["BACK","76%",1],["CARRY","114 yd",1],["COMMIT","full",1],["FACE","2° open",1]]}"#)
        try await shot("hud-03-pass", LessonHUD(center: center, session: session))
        center.end()
        session.sport = "tennis"; session.setupStage = .playing
        center.receive(#"{"kind":"station","sport":"tennis","index":2,"count":8,"key":"pace","name":"Timing","title":"Timing sets the pace","ask":"Hit one GREAT or better. Swing exactly as the ball reaches you.","hint":"Wait a beat longer. Swing as the rings meet the ball.","tips":[]}"#)
        center.receive(#"{"kind":"attempt","result":"miss","grade":"OK","text":"EARLY. Your player held the swing back, so the ball floated short.","misses":3,"read":[["TIMING","EARLY 220 ms",0],["PACE","48 km/h",0],["LANDS","7.6 m",0]]}"#)
        try await shot("hud-04-tennis-skip", LessonHUD(center: center, session: session))
    }
}
