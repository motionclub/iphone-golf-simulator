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

    /// A view rendered with a see-through background (layers composited over Unity frames for the onboarding recording).
    private func saveClear<V: View>(_ view: V, _ name: String, _ size: CGSize, in dir: URL, wait: Double = 1.2) async throws {
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let host = UIHostingController(rootView: view)
        host.safeAreaRegions = []; host.view.backgroundColor = .clear; host.view.isOpaque = false
        let window = UIWindow(windowScene: scene)
        window.frame = CGRect(origin: .zero, size: size); window.backgroundColor = .clear; window.rootViewController = host; window.isHidden = false
        host.view.frame = window.bounds; host.view.layoutIfNeeded()
        try await Task.sleep(for: .seconds(wait))
        let format = UIGraphicsImageRendererFormat(); format.opaque = false; format.scale = 1
        let image = UIGraphicsImageRenderer(size: size, format: format).image { _ in host.view.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
        try XCTUnwrap(image.pngData()).write(to: dir.appendingPathComponent("\(name).png"))
        window.isHidden = true
    }

    /// The onboarding start to finish, as the real flow runs it (PLAN_Onboarding_v3), for a TV (1920x1080) and for a phone with no TV
    /// (9:16): each moment's menu tip (menuCoach JSON), the Tutorial lock (menuTutorialState), what the player does next and the phone at
    /// that moment. Writes film/script-tv.json and film/script-phone.json (Unity's OnboardingFilm replays them on the real menu),
    /// film/phone-NN.png (the TV's remote), the play-safe card and the lesson HUD layers; work/onboarding-v3/film.sh joins them.
    func testOnboardingWalkthrough() async throws {
        let restore = player(); defer { restore() }
        let dir = folder.appendingPathComponent("film"); try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let hub = HubSession.shared
        defer { hub.debugReset(); PlaySafeGate.shared.reset() }
        for tv in [true, false] {
            PlaySafeGate.shared.reset()
            let defaults = UserDefaults(suiteName: "onb-film-\(UUID())")!
            let store = OnboardingStore(defaults: defaults)
            let progress = SportProgress(defaults: defaults)
            let f = OnboardingFlow(store: store, progress: progress, arguments: [])
            var lessons: [Sport] = []
            f.partyWaits = { false }; f.tvConnected = { tv }; f.stateChanged = {}; f.beginLesson = { sport, _ in lessons.append(sport) }
            hub.debugReset(); hub.debugLive(); hub.debugSent = { _ in }
            var entries: [[String: Any]] = []
            let press = tv ? "SELECT" : "tap"
            func add(_ act: String, _ hold: Double, hover: String, caption: String, phone: String? = nil) async throws {
                let n = entries.count
                let name = phone ?? String(format: "phone-%02d", n)
                if phone == nil && tv {
                    hub.menuEvent("menuHover", "x|\(hover)")
                    try await save(MenuPointerPad(hub: hub), "film/\(name)", CGSize(width: 402, height: 874), wait: 0.6)
                }
                entries.append(["screen": f.menuScreen, "coach": f.coachJSON(tv: tv), "tutorial": f.menuState, "act": act, "hold": hold, "phone": name, "caption": caption])
            }
            f.menuScreenChanged("home")
            XCTAssertEqual(f.coach(tv: tv)?.id, "welcome")
            try await add("select", 4.5, hover: "Next", caption: tv ? "First launch: the menu loads, and tips pop up over it" : "No TV: the menu fills the phone, and tips pop up over it")
            f.coachNext("welcome")
            XCTAssertEqual(f.coach(tv: tv)?.target, "tab-locker")
            try await add("select", 3.5, hover: "Locker", caption: "Make your player: the tip frames the LOCKER")
            f.menuScreenChanged("locker")
            XCTAssertEqual(f.coach(tv: tv)?.action, "hint")
            try await add("locker", 4.5, hover: "Sky", caption: "The Locker: pick a colour, then BACK")
            f.menuScreenChanged("home")
            XCTAssertEqual(f.step, .how)
            for page in 0..<3 {
                try await add("select", 4.5, hover: page == 2 ? "Got it" : "Next", caption: ["How it works: swing your phone", tv ? "On the big screen (AirPlay)" : "Just your phone: golf and bowling play here", "Play safe: 2 m (6 ft) back from the TV"][page])
                f.coachNext("how-\(page)")
            }
            XCTAssertEqual(f.coach(tv: tv)?.target, "play")
            try await add("select", 3.5, hover: "Play", caption: "Go to Play (\(press) PLAY)")
            f.menuScreenChanged("sport")
            XCTAssertEqual(f.step, .tutorial); XCTAssertEqual(f.coach(tv: tv)?.target, "sport-tutorial")
            try await add("select", 4, hover: "Tutorial", caption: "Play is locked: only the Tutorial is open")
            f.menuScreenChanged("tutorial")
            XCTAssertEqual(f.coach(tv: tv)?.target, "bay-tutorial-golf")
            try await add("select", 4, hover: "Golf lesson", caption: "The Tutorial: golf first, then tennis, then bowling")
            f.startLesson(.golf)
            let request = try XCTUnwrap(PlaySafeGate.shared.request)
            if tv { try await save(PlaySafeSheet(request: request), "film/phone-safe", CGSize(width: 402, height: 874), wait: 1) }
            else { try await save(PlaySafeSheet(request: request), "film/phone-safe-916", CGSize(width: 402, height: 715), wait: 1) }
            try await add("safe", 6, hover: "", caption: "Before the lesson: the play-safe card, accepted with one tap", phone: tv ? "phone-safe" : "phone-safe-916")
            PlaySafeGate.shared.accept()
            XCTAssertEqual(lessons, [.golf])
            hub.debugReset(); hub.debugLive(); hub.debugSent = { _ in }   // (accepting re-evaluates the menu, which has no Unity in the simulator)
            try await add("lesson", 12, hover: "", caption: tv ? "In game: the lesson opens on the how-to GIF, then a slim coach line" : "In game on the phone: the how-to GIF, then a slim coach line (controls deck not shown)", phone: "none")
            f.completed(.golf); f.menuScreenChanged("tutorial")
            XCTAssertEqual(f.coach(tv: tv)?.target, "bay-tutorial-tennis")
            try await add("wait", 5, hover: "Tennis lesson", caption: "Back from the lesson: golf ticked, tennis next")
            f.completed(.tennis); f.completed(.bowling); f.menuScreenChanged("sport")
            XCTAssertEqual(f.step, .done); XCTAssertEqual(f.coach(tv: tv)?.id, "unlocked")
            try await add("select", 4.5, hover: "Let's play", caption: "All three lessons done (tennis and bowling skipped here)")
            f.coachNext("unlocked")
            XCTAssertNil(f.coach(tv: tv))
            try await add("wait", 3, hover: "Tennis", caption: "Everything is unlocked: free to play")
            let data = try JSONSerialization.data(withJSONObject: entries, options: [.prettyPrinted])
            try data.write(to: dir.appendingPathComponent(tv ? "script-tv.json" : "script-phone.json"))
        }
        // the lesson's coaching over the game, as GolfLesson's first station reports it: on the TV (its how-it-works card, then the ask)
        // and on the phone with no TV (LessonPhoneHUD, 9:16)
        let center = LessonCenter.shared
        let session = SportsSession.shared
        let saved = (session.active, session.ready, session.sport)
        session.active = true; session.ready = true; session.sport = "golf"; session.loading.skip()
        defer { session.active = saved.0; session.ready = saved.1; session.sport = saved.2; center.end() }
        center.receive(#"{"kind":"station","sport":"golf","index":0,"count":8,"key":"grip","name":"Grip","title":"Take your grip and swing","ask":"Hold the phone like a club handle, tap SWING, settle for a moment, then swing back and through.","hint":"Tap SWING with the phone already in your stance and keep still for a beat: the game reads your grip from that pause.","tips":["Hold the phone like the end of a club, screen facing your target.","Tap SWING on your phone, then stay still for a beat.","Swing back and through. That's it."]}"#)
        try await saveClear(LessonHUD(center: center, session: session), "hud-explain", CGSize(width: 1280, height: 720), in: dir)
        try await saveClear(LessonPhoneHUD(center: center, session: session), "hud-phone-explain", CGSize(width: 402, height: 715), in: dir)
        center.receive(#"{"kind":"explained"}"#)
        try await saveClear(LessonHUD(center: center, session: session), "hud-ask", CGSize(width: 1280, height: 720), in: dir)
        try await saveClear(LessonPhoneHUD(center: center, session: session), "hud-phone-ask", CGSize(width: 402, height: 715), in: dir)
    }

    /// The play-safe cards (before a lesson, before a game) and the no-TV lesson coach on the phone.
    func testOnboardingScreens() async throws {
        let restore = player(); defer { restore() }
        PlaySafeGate.shared.reset(); defer { PlaySafeGate.shared.reset() }
        for sport in OnboardingFlow.lessons {
            var onDefer: (@MainActor () -> Void)? = nil
            if sport == .tennis { onDefer = {} }
            let request = PlaySafeGate.Request(sport: sport, tutorial: true, holding: false, onAccept: {}, onDefer: onDefer)
            try await save(PlaySafeSheet(request: request), "v3-06-playsafe-lesson-\(sport.rawValue)", CGSize(width: 402, height: 1200))
        }
        try await save(PlaySafeSheet(request: .init(sport: .golf, tutorial: false, holding: true, onAccept: {}, onDefer: nil)), "v3-07-playsafe-game", phone)
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
        // the lesson opens on the how-to GIF with its tips over it (a stand-in GIF from work/onboarding-v3/standin until Codex's exist)
        if let dir = ProcessInfo.processInfo.environment["ONB_STANDIN_DIR"] { HowToGIF.stand[.golf] = URL(fileURLWithPath: dir).appendingPathComponent("howto-golf.gif") }
        defer { HowToGIF.stand = [:] }
        center.receive(#"{"kind":"station","sport":"golf","index":0,"count":8,"key":"grip","name":"Grip","title":"Take your grip and swing","ask":"Hold the phone like a club handle, tap SWING, settle for a moment, then swing back and through.","hint":"Tap SWING with the phone already in your stance and keep still for a beat.","tips":["Hold the phone like the end of a club, screen facing your target.","Tap SWING on your phone, then stay still for a beat.","Swing back and through. That's it."]}"#)
        try await shot("hud-00-gif-intro", LessonHUD(center: center, session: session))
        try await save(OverMenu(content: LessonPhoneHUD(center: center, session: session)), "hud-00b-gif-intro-phone", phone)
        center.receive(#"{"kind":"explained"}"#)
        try await shot("hud-00c-transparent", LessonHUD(center: center, session: session))
        try await save(OverMenu(content: LessonPhoneHUD(center: center, session: session)), "hud-00d-transparent-phone", phone)
        center.end()
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
        // no TV: the bowling lesson's coach card on the phone (v3)
        center.end(); session.sport = "bowling"
        center.receive(#"{"kind":"station","sport":"bowling","index":2,"count":5,"key":"line","name":"Line up","title":"Pick your spot","ask":"Slide to a new spot on the lane with the arrows, then roll from there.","hint":"Tap the arrows before you hold the ball, then roll.","tips":[]}"#)
        center.receive(#"{"kind":"attempt","result":"miss","grade":"","text":"Move at least 3 boards left or right before you hold the ball.","misses":2,"read":[["Board","20",0]]}"#)
        try await save(OverMenu(content: LessonPhoneHUD(center: center, session: session)), "v3-10-bowling-lesson-phone", phone)
    }
}

/// A menu stand-in behind an overlay (no Unity in the simulator): a course still where the menu would be.
private struct OverMenu<Content: View>: View {
    let content: Content
    var body: some View {
        ZStack {
            if let menu = UIImage(named: "map-golf-cliffside.jpg") {
                Image(uiImage: menu).resizable().scaledToFill().frame(width: 402, height: 874).clipped()
            }
            content
        }
        .frame(width: 402, height: 874)
    }
}
