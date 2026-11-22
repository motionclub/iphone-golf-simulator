import SwiftUI

/// First launch (PLAN_Onboarding_Tutorial_TennisQuickStart_1121.md, 11-21). No TV is needed at any point: the menu loads first
/// (on the TV if one is connected, on the phone if not) and four short tips guide it: welcome → make your player (the real
/// Locker) → pick your look → PLAY. The first PLAY starts the Tutorial: golf, then tennis, then bowling, one lesson after another
/// (each opens on its card, PlaySafeGate; "Later" stops the run, any one can be skipped). Until a sport's lesson is done or
/// skipped, picking that sport asks: play the lesson or skip it (gate). Tennis may be put off on a phone with no TV, since it
/// cannot be played without one. The lessons themselves are Unity's (GolfLesson, TennisTutorial, BowlingLesson), reported
/// through LessonCenter.
@MainActor @Observable
final class OnboardingFlow {
    static let shared = OnboardingFlow()
    let store: OnboardingStore
    let progress: SportProgress
    private(set) var step: OnboardingStep
    /// (The retired "how it works" pages: the intro has none now.)
    private(set) var howPage = 0
    static let howPages = 0
    /// A lesson just finished: its card (next lesson, or everything unlocked) shows over the menu until dismissed.
    private(set) var celebrating: Sport?
    /// The whole Tutorial just ended: "All sports unlocked" over the menu until dismissed.
    private(set) var celebratingAll = false
    /// The Tutorial is running its lessons one after another (from the first PLAY, or the Tutorial card).
    private(set) var chaining = false
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
        if first || arguments.contains("-resetOnboarding") { store.sportGate = true }
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
        if selected == .how { selected = .goPlay }   // the retired step
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
        case .how: move(to: .goPlay)
        case .goPlay: enterTutorial()
        case .tutorial, .done: break
        }
    }
    func back() {
        switch step {
        case .customize: move(to: .welcome)
        case .how, .goPlay: move(to: .customize)
        default: break
        }
    }
    func keepLook() { save(); move(to: .goPlay) }
    /// The menu's screen changed (Unity's menuScreen): the Locker visited and left moves "Make your player" on; PLAY starts the Tutorial.
    func menuScreenChanged(_ screen: String) {
        menuScreen = screen
        if step == .customize, screen == "locker" { visitedLocker = true; Analytics.track("onboarding_customize_open") }
        else if step == .customize, visitedLocker, screen == "home" { Analytics.track("onboarding_customize_done"); keepLook() }
        if step == .goPlay, screen == "sport" || screen == "tutorial" { enterTutorial() }
    }
    /// The first PLAY: the intro is over and the Tutorial's card opens (golf, tennis, bowling).
    func enterTutorial() {
        guard step.isIntro else { return }
        Analytics.track("onboarding_intro_done", ["seconds_since_install": String(Analytics.secondsSinceInstall)])
        move(to: .tutorial)
        startTutorial()
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
            return Coach(id: "welcome", kicker: "", title: "Welcome to MotionSports",
                         body: tv ? "Swing your phone to play golf, tennis and bowling. Your phone is the controller: press SELECT."
                                  : "Swing your phone to play golf, tennis and bowling.")
        case .customize where screen == "home":
            return Coach(id: "customize", kicker: "", title: "Make your player",
                         body: "Open the Locker. \(choose).", target: "tab-locker", action: "press")
        case .customize where screen == "locker":
            return Coach(id: "locker", kicker: "", title: "Pick your look",
                         body: "Choose a section, then a colour. \(tv ? "Press BACK" : "Tap BACK") when you're done.", action: "hint")
        case .goPlay where screen == "home", .how where screen == "home":
            return Coach(id: "goPlay", kicker: "", title: "Learn to play", body: "\(choose) on PLAY to start a short tutorial.", target: "play", action: "press")
        case .goPlay, .customize, .how, .welcome:
            // the intro waits on the Plaza: from the Locker or the Clubhouse, back there first
            return screen == "locker" || screen == "clubhouse"
                ? Coach(id: "home-\(step.key)", kicker: "", title: "Back to the Plaza", body: "", target: "tab-home", action: "press") : nil
        case .tutorial:
            // the Tutorial was put off ("Not now" / "Later"): each sport asks for its lesson, or a skip, when picked
            guard lessonSport == nil, !chaining else { return nil }
            switch screen {
            case "home": return Coach(id: "t-home", kicker: "", title: "Pick a sport", body: "\(choose) on PLAY.", target: "play", action: "press")
            case "sport": return Coach(id: "t-sport", kicker: "", title: "Pick a sport", body: "Each one starts with a short lesson, or skip it.", action: "hint")
            default: return nil
            }
        case .done:
            if celebratingAll {
                return Coach(id: "unlocked-all", kicker: "", title: "All sports unlocked", body: "Play anything you like, online too.", button: "OK")
            }
            guard let sport = celebrating else { return nil }
            return Coach(id: "unlocked", kicker: "", title: "\(sport.title.capitalized) unlocked",
                         body: "Play it any way you like, online too.", button: "OK")
        default: return nil
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
        case "unlocked", "unlocked-all": dismissCelebration(playNext: false)
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

    /// Play is no longer locked as a whole (11-16): each sport's own lesson comes before its games (needsLesson).
    var locked: Bool { false }
    /// A lesson counts as out of the way: finished, skipped, or tennis put off on a phone with no TV.
    func cleared(_ sport: Sport) -> Bool { progress.finishedTutorial(sport) || store.lessonSkipped(sport) || (sport == .tennis && store.tennisDeferred) }
    /// The first lesson not done yet (nil when all are done).
    var nextLesson: Sport? { Self.lessons.first { !progress.finishedTutorial($0) } }
    /// Any lesson can be started, in any order.
    func available(_ sport: Sport) -> Bool { sport.playable }
    var lessonsDone: Int { Self.lessons.filter(progress.finishedTutorial).count }
    /// This sport's games wait for its own lesson, or a skip (a phone that went through this onboarding).
    func needsLesson(_ sport: Sport) -> Bool {
        store.sportGate && Self.lessons.contains(sport) && !progress.finishedTutorial(sport) && !store.lessonSkipped(sport)
    }
    /// The sport a menu station plays (nil for the lessons themselves and everything that is not a game).
    static func sport(forStation id: String) -> Sport? {
        if id.hasPrefix("bay-tutorial-") || id.hasPrefix("bay-gate-") { return nil }
        // phone casting: the screen phone plays no one, so it needs no lesson first (the players' phones join from their menus)
        if id.hasSuffix("-cast") { return nil }
        if id.hasPrefix("bay-tennis") { return .tennis }
        if id.hasPrefix("bay-golf") || id == "sport-daily" || id == "daily-holeinone" { return .golf }
        if id.hasPrefix("bay-bowling") { return .bowling }
        return nil
    }

    /// A menu station may be used now (HubSession.useStation): a game of a sport whose lesson comes first does not (the hub asks,
    /// lesson or skip, instead: lessonFirst).
    func allows(_ id: String) -> Bool {
        guard let sport = Self.sport(forStation: id) else { return true }
        return !needsLesson(sport)
    }
    /// A refused station: ask, play its sport's lesson or skip it (`then` carries on to what was picked after a skip).
    func lessonFirst(_ id: String, then: @escaping @MainActor () -> Void = {}) { if let sport = Self.sport(forStation: id) { gate(sport, then: then) } }

    /// What the TV's menu needs (MenuHud.Tutorial): {"locked":false,"next":…,"done":[…],"deferred":[…],"gate":[…]}.
    var menuState: String {
        let done = Self.lessons.filter(progress.finishedTutorial).map { "\"\($0.rawValue)\"" }.joined(separator: ",")
        let deferred = store.tennisDeferred && !progress.finishedTutorial(.tennis) ? "\"tennis\"" : ""
        let gate = Self.lessons.filter(needsLesson).map { "\"\($0.rawValue)\"" }.joined(separator: ",")
        return "{\"locked\":false,\"next\":\"\(nextLesson?.rawValue ?? "")\",\"done\":[\(done)],\"deferred\":[\(deferred)],\"gate\":[\(gate)]}"
    }

    // MARK: Lessons

    /// A Tutorial row: its how-to-play sheet and the safety card, then the lesson (one lesson; the run of all three is startTutorial).
    func startLesson(_ sport: Sport) {
        guard sport.playable else { return }
        celebrating = nil; celebratingAll = false; chaining = false
        var onDefer: (@MainActor () -> Void)? = nil
        if sport == .tennis && !tvConnected() { onDefer = { [weak self] in self?.deferTennis() } }
        PlaySafeGate.shared.present(sport: sport, tutorial: true, onAccept: { [weak self] in self?.launchLesson(sport) }, onDefer: onDefer)
    }

    // MARK: The Tutorial (all three, one after another)

    /// The lessons the Tutorial still has to run, in order (done and skipped ones drop out; tennis put off on a phone with no TV too).
    var tutorialLeft: [Sport] { Self.lessons.filter { !cleared($0) } }
    /// The first PLAY (or the Tutorial card): one card for the whole Tutorial, then its first lesson.
    func startTutorial() {
        celebrating = nil; celebratingAll = false
        guard let first = tutorialLeft.first else { finishTutorial(); return }
        chaining = true
        Analytics.track("tutorial_run_start", ["first": first.rawValue])
        PlaySafeGate.shared.present(PlaySafeGate.Request(sport: first, kind: .tutorial, holding: false,
            onAccept: { [weak self] in self?.launchOrDefer(first) }, onDefer: nil,
            onCancel: { [weak self] in self?.stopTutorial() }))
    }
    /// The Tutorial's next lesson's card ("Golf done. Next up, tennis (2 of 3)"), or its end.
    func continueTutorial(after done: Sport?) {
        guard chaining else { return }
        guard let next = tutorialLeft.first else { finishTutorial(); return }
        let n = (Self.lessons.firstIndex(of: next) ?? 0) + 1
        let note = done.map { "\($0.rawValue.capitalized) done. Next up, \(next.rawValue) (\(n) of \(Self.lessons.count))" }
        var onDefer: (@MainActor () -> Void)? = nil
        if next == .tennis && !tvConnected() { onDefer = { [weak self] in self?.deferTennis() } }
        PlaySafeGate.shared.present(PlaySafeGate.Request(sport: next, kind: .lesson, holding: false,
            onAccept: { [weak self] in self?.launchLesson(next) }, onDefer: onDefer,
            onSkip: { [weak self] in self?.skipLesson(next); self?.continueTutorial(after: nil) },
            onCancel: { [weak self] in self?.stopTutorial() }, note: note))
    }
    /// The Tutorial card's Start: its first lesson, or (tennis first with no TV) the tennis card that offers to put it off.
    private func launchOrDefer(_ sport: Sport) {
        if sport == .tennis && !tvConnected() { continueTutorial(after: nil) } else { launchLesson(sport) }
    }
    /// "Not now" / "Later": the run stops; the sports still gated ask for their lesson, or a skip, when picked.
    func stopTutorial() {
        guard chaining else { return }
        chaining = false
        Analytics.track("tutorial_run_stop", ["left": String(tutorialLeft.count)])
        if lessonsDone > 0, step != .done { endGuided() } else { stateChanged() }
    }
    private func finishTutorial() {
        let ran = chaining
        chaining = false
        Analytics.track("tutorial_run_done")
        if step != .done { endGuided() } else { stateChanged() }
        celebratingAll = ran
    }
    private func endGuided() {
        store.explicitRun = false
        Analytics.track("onboarding_done", ["seconds_since_install": String(Analytics.secondsSinceInstall)])
        move(to: .done)
    }

    // MARK: The gate (a sport picked before its lesson)

    /// "<Sport> lesson": play it now, or skip it and carry on (`then`) to what was picked.
    func gate(_ sport: Sport, then: @escaping @MainActor () -> Void = {}) {
        guard sport.playable else { return }
        celebrating = nil; celebratingAll = false
        Analytics.track("tutorial_gate", ["sport": sport.rawValue])
        PlaySafeGate.shared.present(PlaySafeGate.Request(sport: sport, kind: .gate, holding: false,
            onAccept: { [weak self] in self?.chaining = false; self?.launchLesson(sport) }, onDefer: nil,
            onSkip: { [weak self] in self?.skipLesson(sport); then() }))
    }
    /// Skip lesson: the sport's games open now (no lesson reward; the Tutorial row can still play it).
    func skipLesson(_ sport: Sport) {
        store.setLessonSkipped(sport, true)
        store.setLessonStation(sport, 0)
        Analytics.track("tutorial_skip", ["sport": sport.rawValue])
        if step != .done, !chaining, Self.lessons.allSatisfy(cleared) { endGuided() } else { stateChanged() }
    }

    /// Accepted: start (or resume) the lesson.
    func launchLesson(_ sport: Sport) {
        lessonSport = sport; lessonBegan = ProcessInfo.processInfo.systemUptime
        Analytics.track("tutorial_start", ["sport": sport.rawValue, "station": String(store.lessonStation(sport))])
        beginLesson(sport, store.lessonStation(sport))
    }
    /// No TV for tennis: put it off (tennis waits for a TV and its lesson); the Tutorial carries on with bowling.
    func deferTennis() {
        store.tennisDeferred = true
        Analytics.track("tutorial_defer", ["sport": "tennis"])
        lessonSport = nil
        if chaining { continueTutorial(after: nil) } else { stateChanged() }
    }
    /// Unity's lesson started a station (resumes there next time).
    func lessonStation(_ index: Int, sport: Sport) { store.setLessonStation(sport, index) }
    /// The lesson's last station is done.
    func completed(_ sport: Sport) {
        progress.completeTutorial(sport)
        store.setLessonStation(sport, 0)
        store.setLessonSkipped(sport, false)
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
        // the Tutorial goes straight on to its next lesson's card; a lesson played from a gate or the Tutorial row ends on its card
        if chaining { continueTutorial(after: sport); return }
        if step != .done, Self.lessons.allSatisfy(cleared) || lessonsDone > 0 { endGuided() } else { stateChanged() }
        if finished { celebrating = sport }
    }
    /// The card after a lesson: its next lesson (or nothing, to stay on the menu).
    func dismissCelebration(playNext: Bool) {
        let next = nextLesson
        celebrating = nil; celebratingAll = false
        if playNext, let next { startLesson(next) }
    }
    /// The game was left from its pause menu: a running lesson stops (its row resumes at the same station).
    func gameLeft() {
        LessonCenter.shared.end()
        lessonSport = nil; lessonBegan = nil
        // leaving a lesson stops the Tutorial's run too (its row resumes at the same station)
        if chaining { chaining = false; if lessonsDone > 0, step != .done { endGuided() } }
        if SportsSession.shared.active { SportsSession.shared.end() }
        TennisMenu.shared.goHome()
        stateChanged()
    }
    /// Leaving onboarding from anywhere (tests, Settings → Developer): everything unlocks, no reward is claimed.
    func exitToMenu() {
        store.explicitRun = false; lessonBegan = nil; lessonSport = nil; celebrating = nil; celebratingAll = false; chaining = false
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
