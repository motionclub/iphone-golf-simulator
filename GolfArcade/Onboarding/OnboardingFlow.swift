import SwiftUI

/// First launch, v3 (PLAN_Onboarding_v3_IntroTutorial.md, Adnan 2026-11-15). No TV is needed at any point: the menu loads first
/// (on the TV if one is connected, on the phone if not) and the intro runs on the phone over it (IntroCoach):
///   welcome → make your player (the real Locker) → how it works (motion control · TV or phone only · play safe) → go to Play.
/// Pressing PLAY ends the intro, and from then Play is locked to the Tutorial (golf → tennis → bowling) until all three are done
/// (tennis may be put off on a phone with no TV, since it cannot be played without one). Each lesson opens with its how-to-play
/// sheet and the safety card (PlaySafeGate); the lessons themselves are Unity's (GolfLesson, TennisTutorial, BowlingLesson),
/// reported through LessonCenter.
@MainActor @Observable
final class OnboardingFlow {
    static let shared = OnboardingFlow()
    let store: OnboardingStore
    let progress: SportProgress
    private(set) var step: OnboardingStep
    /// The How it works card shown (0 motion, 1 TV or phone, 2 play safe).
    private(set) var howPage = 0
    static let howPages = 3
    /// A lesson just finished: its card (next lesson, or everything unlocked) shows over the menu until dismissed.
    private(set) var celebrating: Sport?
    private(set) var lessonBegan: Double?
    /// The sport whose lesson is loading or running (nil between lessons).
    private(set) var lessonSport: Sport?

    var active: Bool { step != .done }
    /// The menu is never held any more: it boots behind the intro (kept for the callers that asked).
    var holdsMenu: Bool { false }
    /// Joining, or in, a friends' party now: the intro steps aside until it is over.
    @ObservationIgnored var partyWaits: @MainActor () -> Bool = {
        ClubHub.shared.joining != nil || ClubHub.shared.cloud.knocking != nil || (MultiplayerService.shared.lobby != nil && MultiplayerService.shared.isParty)
    }
    /// Is a TV (AirPlay or a cable) connected right now.
    @ObservationIgnored var tvConnected: @MainActor () -> Bool = { SportsSession.shared.displayConnected }
    @ObservationIgnored var askNotifications: @MainActor () -> Void = {
        if ProcessInfo.processInfo.environment["XCTestConfigurationFilePath"] == nil { ClubPush.requestPermission() }
    }
    /// Seams for tests (the real ones touch the menu runtime / start a match).
    @ObservationIgnored var beginLesson: @MainActor (Sport, Int) -> Void = { sport, station in TennisMenu.shared.beginLesson(sport, station: station) }
    @ObservationIgnored var stateChanged: @MainActor () -> Void = { HubSession.shared.evaluate() }

    /// The tutorial's order (Adnan: golf first, then tennis, then bowling).
    static let lessons: [Sport] = [.golf, .tennis, .bowling]

    init(store: OnboardingStore = OnboardingStore(), progress: SportProgress = .shared,
         arguments: [String] = ProcessInfo.processInfo.arguments) {
        self.store = store; self.progress = progress
        // A fresh install has no install time yet. A phone that used the app before this onboarding (no step saved by it) is not
        // forced through it, nor is one that finished the 10-25 onboarding or any lesson; one that started it carries on.
        let first = store.defaults.object(forKey: "ftue.installedAt.v1") == nil
        _ = store.installedAt
        var selected = store.step
        if !first && !store.explicitRun && !store.hasSavedStep { selected = .done }
        if !store.explicitRun && !store.hasSavedStep && (store.legacyStep == "done" || progress.anyTutorialDone) { selected = .done }
        // Release too (2026-11-16): launch arguments only Xcode / devicectl can pass, to put a test phone through onboarding again
        // (-freshOnboarding also clears the finished lessons, so the Tutorial runs again)
        if arguments.contains("-freshOnboarding") { progress.resetTutorials() }
        if arguments.contains("-resetOnboarding") { store.reset(); _ = store.installedAt; selected = .welcome }
        #if DEBUG
        let force = arguments.contains("-forceOnboarding")
        let legacy = arguments.contains { arg in
            ["-skipPlayerCalibration", "-startInCameraMode", "-startCourse", "--lobby-mock", "--lobby", "--character-editor", "-benchTennis", "-benchGolf", "-range.swingInput"].contains(arg) || arg.hasPrefix("--resume-tennis-round-")
        }
        let unitHost = ProcessInfo.processInfo.environment["XCTestConfigurationFilePath"] != nil && arguments == ProcessInfo.processInfo.arguments
        if force { store.explicitRun = true; selected = .welcome }
        else if arguments.contains("-skipOnboarding") || legacy || unitHost { selected = .done }
        if let i = arguments.firstIndex(of: "-onboardingStep"), arguments.indices.contains(i + 1),
           let override = OnboardingStep(key: arguments[i + 1]) { selected = override; store.explicitRun = true }
        #endif
        store.step = selected; step = selected
        if first { Analytics.track("app_first_open") }
        let n = store.defaults.integer(forKey: "ftue.sessions.v1") + 1
        store.defaults.set(n, forKey: "ftue.sessions.v1")
        Analytics.track("session_start", ["n": String(n)])
        viewed()
    }

    // MARK: The intro (over the menu, on the phone)

    /// The intro is running (its tips show over the menu), unless a party is joining or a match runs.
    var introShowing: Bool { step.isIntro && !partyWaits() && !SportsSession.shared.active }
    /// (The 10-25 intro dimmed the TV while it ran on the phone; the tips are on the menu itself now.)
    var introOnPhone: Bool { false }
    /// The Locker was opened from the "Make your player" tip (coming back from it moves the intro on).
    private(set) var visitedLocker = false

    private func viewed() { Analytics.track("onboarding_step_view", ["step": step.key, "page": String(howPage)]) }
    func move(to next: OnboardingStep) {
        store.step = next; step = next; howPage = 0; visitedLocker = false; viewed()
        if next == .customize, !store.characterInitialized { store.characterInitialized = true }
        stateChanged()
    }
    /// NEXT on a tip.
    func next() {
        switch step {
        case .welcome: move(to: .customize)
        case .customize: keepLook()
        case .how:
            if howPage + 1 < Self.howPages { howPage += 1; viewed() } else { move(to: .goPlay) }
        case .goPlay: enterTutorial()
        case .tutorial, .done: break
        }
    }
    func back() {
        switch step {
        case .customize: move(to: .welcome)
        case .how: if howPage > 0 { howPage -= 1; viewed() } else { move(to: .customize) }
        case .goPlay: move(to: .how); howPage = Self.howPages - 1
        default: break
        }
    }
    func keepLook() { save(); move(to: .how) }
    /// The menu's screen changed (Unity's menuScreen): the Locker visited and left moves "Make your player" on; PLAY starts the Tutorial.
    func menuScreenChanged(_ screen: String) {
        menuScreen = screen
        if step == .customize, screen == "locker" { visitedLocker = true; Analytics.track("onboarding_customize_open") }
        else if step == .customize, visitedLocker, screen == "home" { Analytics.track("onboarding_customize_done"); keepLook() }
        if step == .goPlay, screen == "sport" || screen == "tutorial" { enterTutorial() }
    }
    func enterTutorial() {
        guard step.isIntro else { return }
        Analytics.track("onboarding_intro_done", ["seconds_since_install": String(Analytics.secondsSinceInstall)])
        move(to: .tutorial)
    }

    // MARK: The tips over the menu (MenuHud.Coach on the TV, or on the phone with no TV)

    /// The menu's screen now (home, sport, tutorial, locker, …).
    private(set) var menuScreen = "home"
    struct Coach: Codable, Equatable {
        var id: String, kicker: String, title: String, body: String
        var target = ""
        /// "next" (its own NEXT), "press" (only `target` can be pressed), "hint" (no hold on the menu)
        var action = "next"
        var button = "NEXT"
    }
    /// The tip for this moment, nil for none. `tv`: the menu is on a TV (the phone is the remote) rather than on the phone.
    func coach(tv: Bool) -> Coach? {
        guard !partyWaits(), !SportsSession.shared.active, PlaySafeGate.shared.request == nil else { return nil }
        let screen = menuScreen
        let choose = tv ? "Press SELECT on your phone" : "Tap it"
        switch step {
        case .welcome where screen == "home":
            return Coach(id: "welcome", kicker: "WELCOME TO MOTIONSPORTS", title: "Let's get you playing",
                         body: tv ? "Your phone is the controller. Its arrows move around this menu and SELECT chooses. Press SELECT now."
                                  : "Golf, tennis and bowling, played by swinging your phone. Tap NEXT.")
        case .customize where screen == "home":
            return Coach(id: "customize", kicker: "STEP 1 OF 3 · YOUR PLAYER", title: "Make your player",
                         body: "Open the Locker to pick your kit colours, body and skin. \(choose).", target: "tab-locker", action: "press")
        case .customize where screen == "locker":
            return Coach(id: "locker", kicker: "THE LOCKER", title: "Pick your look",
                         body: "Choose a slot on the left, then a colour. MIRROR changes body, skin and hand on your phone. \(tv ? "Press BACK" : "Tap BACK") when you're done.",
                         action: "hint")
        case .how where screen == "home":
            switch howPage {
            case 0:
                return Coach(id: "how-0", kicker: "STEP 2 OF 3 · HOW IT WORKS", title: "Swing your phone",
                             body: "Its motion sensors read every swing. Swing it like a golf club, a tennis racket or a bowling ball, and your player copies you.")
            case 1:
                return tv
                    ? Coach(id: "how-1", kicker: "STEP 2 OF 3 · HOW IT WORKS", title: "You're on the big screen",
                            body: "That's the best way to play: AirPlay puts the game on the TV and your phone is the controller. No TV another time? Golf and bowling also play on the phone alone. Tennis needs a TV.")
                    : Coach(id: "how-1", kicker: "STEP 2 OF 3 · HOW IT WORKS", title: "Big screen or just your phone",
                            body: "Golf and bowling play right here on your phone. For the best experience use AirPlay: Control Center › Screen Mirroring › your Apple TV or AirPlay TV. Tennis needs a TV.")
            default:
                return Coach(id: "how-2", kicker: "STEP 2 OF 3 · PLAY SAFE", title: "Play safe",
                             body: "Hold on tight (a wrist strap helps). Clear about 2 m (6 ft) around you. Stand at least 2 m (6 ft) back from the TV, and swing smoothly, never hard.",
                             button: "GOT IT")
            }
        case .goPlay where screen == "home":
            return Coach(id: "goPlay", kicker: "STEP 3 OF 3", title: "Start your tutorial",
                         body: "Three short lessons: golf, tennis, then bowling. They unlock every game. \(choose) on PLAY.", target: "play", action: "press")
        case .goPlay, .customize, .how, .welcome:
            // the intro waits on the Plaza: from the Locker or the Clubhouse, back there first
            return screen == "locker" || screen == "clubhouse"
                ? Coach(id: "home-\(step.key)", kicker: "TUTORIAL", title: "Back to the Plaza", body: "Your next tip is on the Plaza.", target: "tab-home", action: "press") : nil
        case .tutorial:
            guard lessonSport == nil, let next = nextLesson else { return nil }
            let n = (Self.lessons.firstIndex(of: next) ?? 0) + 1
            let done = celebrating.map { "\($0.title.capitalized) done! " } ?? ""
            switch screen {
            case "home":
                return Coach(id: "t-home", kicker: "TUTORIAL · LESSON \(n) OF 3", title: done.isEmpty ? "Your tutorial is waiting" : "Nice work!",
                             body: "\(done)The \(next.rawValue) lesson is next. \(choose) on PLAY.", target: "play", action: "press")
            case "sport":
                return Coach(id: "t-sport", kicker: "TUTORIAL · LESSON \(n) OF 3", title: "Start here",
                             body: "Every game unlocks once the three lessons are done.", target: "sport-tutorial", action: "press")
            case "tutorial":
                return Coach(id: "t-\(next.rawValue)", kicker: "LESSON \(n) OF 3", title: done.isEmpty ? "\(next.title.capitalized) lesson" : "\(done)\(next.title.capitalized) next",
                             body: Self.lessonLine(next, tv: tv), target: "bay-tutorial-\(next.rawValue)", action: "press")
            default: return nil
            }
        case .done:
            guard celebrating != nil else { return nil }
            return Coach(id: "unlocked", kicker: "TUTORIAL COMPLETE", title: "Everything's unlocked!",
                         body: "Golf, tennis, bowling, daily challenges and online play are all yours. Have fun.", button: "LET'S PLAY")
        default: return nil
        }
    }
    static func lessonLine(_ sport: Sport, tv: Bool) -> String {
        switch sport {
        case .golf: "Swing, distance, aim and putting, about 6 minutes. You'll hold the phone like a club."
        case .tennis: tv ? "First calibration: point your phone at the TV so your swings line up with the picture. Then rally with Coach Ray."
                         : "Tennis needs a TV. Connect one with AirPlay, or put this lesson off until you have one."
        case .bowling: "Roll, time the release, line up and spin, about 3 minutes. You'll hold the phone like the ball."
        default: ""
        }
    }
    /// The tip as menuCoach JSON ("" = none).
    func coachJSON(tv: Bool) -> String {
        guard let c = coach(tv: tv), let data = try? JSONEncoder().encode(c) else { return "" }
        return String(data: data, encoding: .utf8) ?? ""
    }
    /// NEXT was pressed on the tip `id` (Unity's menuCoach event).
    func coachNext(_ id: String) {
        switch id {
        case "welcome": if step == .welcome { next() }
        case "how-0", "how-1", "how-2": if step == .how, id == "how-\(howPage)" { next() }
        case "unlocked": dismissCelebration(playNext: false)
        default: break
        }
    }
    private func save() {
        let s = SportsSession.shared
        guard s.players.indices.contains(s.playerIndex) else { return }
        let p = s.players[s.playerIndex]
        s.savePlayers()
        MultiplayerService.shared.setIdentity(name: p.name, female: p.standardFemale, left: p.handedness == .left, loadout: p.multiplayerLoadout)
        Analytics.track("hero_created", ["female": String(p.standardFemale), "named": String(p.name != "Player 1")])
    }

    // MARK: The Tutorial lock

    /// Play is locked to the Tutorial (every step before done).
    var locked: Bool { step != .done }
    /// A lesson counts as out of the way: finished, or tennis put off on a phone with no TV.
    func cleared(_ sport: Sport) -> Bool { progress.finishedTutorial(sport) || (sport == .tennis && store.tennisDeferred) }
    /// The lesson to play next (nil when all are cleared).
    var nextLesson: Sport? { Self.lessons.first { !cleared($0) } }
    /// A lesson can be started: it is finished (replay) or the next one. Later ones wait.
    func available(_ sport: Sport) -> Bool { progress.finishedTutorial(sport) || nextLesson == sport || (sport == .tennis && store.tennisDeferred) }
    var lessonsDone: Int { Self.lessons.filter(progress.finishedTutorial).count }

    /// A menu station may be used now (HubSession.useStation): with Play locked only the Tutorial's own rows and the stations that
    /// are not games (the Locker, settings, how to play, invites, feedback) pass.
    func allows(_ id: String) -> Bool {
        guard locked else { return true }
        if id.hasPrefix("bay-tutorial-") { return true }
        return !(id.hasPrefix("bay-") || id == "sport-daily" || id == "daily-holeinone")
    }
    static let lockMessage = "Finish the Tutorial first: it unlocks every game."

    /// What the TV's menu needs to style Play (MenuHud.Tutorial): {"locked":…,"next":…,"done":[…],"deferred":[…]}.
    var menuState: String {
        let done = Self.lessons.filter(progress.finishedTutorial).map { "\"\($0.rawValue)\"" }.joined(separator: ",")
        let deferred = store.tennisDeferred && !progress.finishedTutorial(.tennis) ? "\"tennis\"" : ""
        return "{\"locked\":\(locked),\"next\":\"\(nextLesson?.rawValue ?? "")\",\"done\":[\(done)],\"deferred\":[\(deferred)]}"
    }

    // MARK: Lessons

    /// A Tutorial row: its how-to-play sheet and the safety card, then the lesson. (From the menu's Tutorial, or the card after one.)
    func startLesson(_ sport: Sport) {
        guard sport.playable, available(sport) else { HubSession.shared.toast("Finish the \(nextLesson?.title.capitalized ?? "earlier") lesson first."); return }
        celebrating = nil
        var onDefer: (@MainActor () -> Void)? = nil
        if sport == .tennis && !tvConnected() { onDefer = { [weak self] in self?.deferTennis() } }
        PlaySafeGate.shared.present(sport: sport, tutorial: true, onAccept: { [weak self] in self?.launchLesson(sport) }, onDefer: onDefer)
    }
    /// Accepted: start (or resume) the lesson.
    func launchLesson(_ sport: Sport) {
        lessonSport = sport; lessonBegan = ProcessInfo.processInfo.systemUptime
        Analytics.track("tutorial_start", ["sport": sport.rawValue, "station": String(store.lessonStation(sport))])
        beginLesson(sport, store.lessonStation(sport))
    }
    /// No TV for tennis: put it off. The Tutorial carries on to bowling; tennis stays there to play once a TV is connected.
    func deferTennis() {
        store.tennisDeferred = true
        Analytics.track("tutorial_defer", ["sport": "tennis"])
        afterLesson(.tennis, finished: false)
    }
    /// Unity's lesson started a station (resumes there next time).
    func lessonStation(_ index: Int, sport: Sport) { store.setLessonStation(sport, index) }
    /// The lesson's last station is done.
    func completed(_ sport: Sport) {
        progress.completeTutorial(sport)
        store.setLessonStation(sport, 0)
        if sport == .tennis { store.tennisDeferred = false }
        let s = SportsSession.shared
        if s.players.indices.contains(s.playerIndex) { Progression.shared.awardTutorial(player: s.players[s.playerIndex].id, sport: sport, store: store) }
        Analytics.track("tutorial_complete", ["sport": sport.rawValue, "seconds": String(lessonBegan.map { ProcessInfo.processInfo.systemUptime - $0 } ?? 0)])
        lessonBegan = nil
        if s.active { s.end() }
        afterLesson(sport, finished: true)
    }
    private func afterLesson(_ sport: Sport, finished: Bool) {
        lessonSport = nil
        if locked, nextLesson == nil {
            store.explicitRun = false
            Analytics.track("onboarding_done", ["seconds_since_install": String(Analytics.secondsSinceInstall)])
            move(to: .done)
        } else { stateChanged() }
        if finished { celebrating = sport }
    }
    /// The card after a lesson: its next lesson (or nothing, to stay on the menu).
    func dismissCelebration(playNext: Bool) {
        let next = nextLesson
        celebrating = nil
        if playNext, let next { startLesson(next) }
    }
    /// The game was left from its pause menu: a running lesson stops (its row resumes at the same station).
    func gameLeft() {
        LessonCenter.shared.end()
        lessonSport = nil; lessonBegan = nil
        if SportsSession.shared.active { SportsSession.shared.end() }
        TennisMenu.shared.goHome()
        stateChanged()
    }
    /// Leaving onboarding from anywhere (tests, Settings → Developer): everything unlocks, no reward is claimed.
    func exitToMenu() {
        store.explicitRun = false; lessonBegan = nil; lessonSport = nil; celebrating = nil
        move(to: .done)
        TennisMenu.shared.goHome()
    }
    /// Settings → Replay onboarding: the intro again; Play stays open where every lesson is already done.
    func replay() {
        for sport in Self.lessons where progress.finishedTutorial(sport) && !store.rewardClaimed(sport) { store.markReward(sport, xp: 0, item: nil) }
        store.explicitRun = true; store.characterInitialized = true
        Analytics.track("onboarding_replay"); move(to: .welcome)
    }
}
