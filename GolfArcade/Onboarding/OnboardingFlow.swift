import SwiftUI
import GameKit

/// First launch on the TV (option B of PLAN_Onboarding_GolfLesson.md): SwiftUI screens in the TV window, driven by the phone's
/// click remote exactly like the menu (arrows move the focus, A selects, B goes back). Only a lesson runs the game; while one runs
/// the TV and phone belong to it, and Unity's lesson reports (LessonCenter) bring the flow back for the reward.
@MainActor @Observable
final class OnboardingFlow {
    static let shared = OnboardingFlow()
    let store: OnboardingStore
    let progress: SportProgress
    private(set) var step: OnboardingStep
    /// TV focus, as TennisMenu keeps it.
    private(set) var row = 0
    private(set) var column = 0
    /// The controller step's practice button has been pressed.
    private(set) var triedSelect = false
    private(set) var lessonBegan: Double?
    var active: Bool { step != .done }
    /// A lesson's game is on: the TV and phone are the game's, not onboarding's.
    var lessonRunning: Bool { if case .lesson = step { return SportsSession.shared.active }; return false }
    /// Onboarding owns the TV and the phone (every step but a running lesson), except while the player is joining or in a friend's
    /// party: a Join puts onboarding off until the party is over, TV or not (2026-10-26; before, an invite could never be joined
    /// during onboarding, and with no TV the connect screen had no way out).
    var holdsMenu: Bool { active && !lessonRunning && !partyWaits() }
    @ObservationIgnored var askNotifications: @MainActor () -> Void = {
        if ProcessInfo.processInfo.environment["XCTestConfigurationFilePath"] == nil { ClubPush.requestPermission() }
    }
    /// Joining, or in, a friends' party now.
    @ObservationIgnored var partyWaits: @MainActor () -> Bool = {
        ClubHub.shared.joining != nil || ClubHub.shared.cloud.knocking != nil || (MultiplayerService.shared.lobby != nil && MultiplayerService.shared.isParty)
    }

    /// Shirt colours offered on first launch (the Locker has the full range).
    static let shirts = ["1F5BD8", "D8262B", "F1B120", "2E9A3A", "18245A", "ECEAE3", "E2533F", "7A4DD8"]
    static let nameIdeas = ["Ace", "Birdie", "Eagle", "Chip", "Lefty"]

    init(store: OnboardingStore = OnboardingStore(), progress: SportProgress = .shared,
         arguments: [String] = ProcessInfo.processInfo.arguments) {
        self.store = store; self.progress = progress
        // A fresh install has no install time yet. A phone that used the app before this onboarding existed (no step saved by
        // it) is not shown it; one that started it carries on where it was.
        let first = store.defaults.object(forKey: "ftue.installedAt.v1") == nil
        _ = store.installedAt
        var selected = store.step
        if !first && !store.explicitRun && !store.hasSavedStep { selected = .done }
        if progress.anyTutorialDone && !store.explicitRun { selected = .done }
        #if DEBUG
        if arguments.contains("-resetOnboarding") { store.reset(); _ = store.installedAt; selected = .hello }
        let force = arguments.contains("-forceOnboarding")
        let legacy = arguments.contains { arg in
            ["-skipPlayerCalibration", "-startInCameraMode", "-startCourse", "--lobby-mock", "--lobby", "--character-editor", "-benchTennis", "-benchGolf", "-range.swingInput"].contains(arg) || arg.hasPrefix("--resume-tennis-round-")
        }
        let unitHost = ProcessInfo.processInfo.environment["XCTestConfigurationFilePath"] != nil && arguments == ProcessInfo.processInfo.arguments
        if force { store.explicitRun = true; selected = .hello }
        else if arguments.contains("-skipOnboarding") || legacy || unitHost { selected = .done }
        if let i = arguments.firstIndex(of: "-onboardingStep"), arguments.indices.contains(i + 1),
           let override = OnboardingStep(key: arguments[i + 1]) { selected = override; store.explicitRun = true }
        #endif
        // A lesson cannot pick up mid-game after the app was closed: offer it again from the lesson's own screen.
        store.step = selected; step = selected
        if first { Analytics.track("app_first_open") }
        let n = store.defaults.integer(forKey: "ftue.sessions.v1") + 1
        store.defaults.set(n, forKey: "ftue.sessions.v1")
        Analytics.track("session_start", ["n": String(n)])
        viewed()
    }

    // MARK: Steps

    private func viewed() { Analytics.track("onboarding_step_view", ["step": step.key]) }
    func move(to next: OnboardingStep) {
        store.step = next; step = next; row = 0; column = 0; viewed()
        if next == .card { save() }
        if next == .player, !store.characterInitialized { TennisMenu.shared.randomizeLook(); store.characterInitialized = true }
        if next == .done { HubSession.shared.evaluate() }
    }
    func next() {
        switch step {
        case .hello: move(to: .account)
        case .account:
            // signed in: friends' invites can reach this phone with the game closed (the one place first-run asks)
            if signedIn { askNotifications() }
            move(to: .controller)
        case .controller: move(to: .room)
        case .room: move(to: .player)
        case .player: move(to: .card)
        case .card: move(to: .choose)
        case .reward(let sport): finish(sport)
        default: break
        }
    }
    func back() {
        switch step {
        case .hello, .done: return
        case .account: move(to: .hello)
        case .controller: move(to: .account)
        case .room: move(to: .controller)
        case .player: move(to: .room)
        case .card: move(to: .player)
        case .choose: move(to: .card)
        case .lesson: LessonCenter.shared.end(); if SportsSession.shared.active { SportsSession.shared.end() }; move(to: .choose)
        case .reward(let sport): finish(sport)
        }
    }

    // MARK: TV focus (the phone's remote)

    func rows() -> [[String]] {
        switch step {
        case .hello: [["go"]]
        case .account: signedIn ? [["next"]] : [["signin"], ["later"]]
        case .controller: [[triedSelect ? "next" : "try"]]
        case .room: [["ready"]]
        case .player: [["male", "female"], ["skin"], ["shirt"], ["name"], ["shuffle", "save"]]
        case .card: [["play"]]
        case .choose: [["golf", "tennis"], ["skip"]]
        case .lesson: [["resume"], ["choose"], ["skip"]]
        case .reward(let sport):
            [["play", progress.finishedTutorial(sport == .golf ? .tennis : .golf) ? "menu" : "other"]] + (progress.finishedTutorial(sport == .golf ? .tennis : .golf) ? [] : [["menu"]])
        case .done: []
        }
    }
    var focused: String {
        let grid = rows()
        guard row < grid.count, column < grid[row].count else { return "" }
        return grid[row][column]
    }
    func isFocused(_ id: String) -> Bool { focused == id }
    func move(_ direction: MenuMove) {
        let grid = rows()
        guard !grid.isEmpty else { return }
        row = min(row, grid.count - 1); column = min(column, grid[row].count - 1)
        // A swatch row changes its value sideways, like the Locker's.
        if direction == .left || direction == .right, grid[row].count == 1, adjust(focused, by: direction == .left ? -1 : 1) { tick(); return }
        var r = row, c = column
        switch direction {
        case .up: r = max(0, r - 1)
        case .down: r = min(grid.count - 1, r + 1)
        case .left: c = max(0, c - 1)
        case .right: c = min(grid[r].count - 1, c + 1)
        }
        c = min(c, grid[r].count - 1)
        if r != row || c != column { row = r; column = c; tick() }
    }
    @discardableResult func focus(_ id: String) -> Bool {
        for (r, items) in rows().enumerated() { if let c = items.firstIndex(of: id) { row = r; column = c; return true } }
        return false
    }
    /// Touch on the TV canvas (snapshots, the simulator) and the phone's A button.
    func tap(_ id: String) { if focus(id) { select() } }
    private func tick() {
        if SportsSession.shared.haptics { UISelectionFeedbackGenerator().selectionChanged() }
        ClubSound.play("tick", volume: 0.4)
    }
    func select() {
        let id = focused
        if SportsSession.shared.haptics { UIImpactFeedbackGenerator(style: .medium).impactOccurred() }
        ClubSound.play("pop", volume: 0.5)
        switch id {
        case "go", "ready", "next", "later": next()
        case "signin": signIn()
        case "play":
            if step == .card { next() }
            else if case .reward(let sport) = step { finish(sport, playNext: true) }
        case "try": triedSelect = true; column = 0
        case "male", "female": edit { $0.standardFemale = id == "female" }
        case "skin", "shirt": _ = adjust(id, by: 1)
        case "name": nameRequested = true
        case "shuffle": TennisMenu.shared.randomizeLook(); edit { $0.name = OnboardingStore.name(Self.nameIdeas.randomElement() ?? "Ace") }
        case "save": move(to: .card)
        case "golf": startLesson(.golf)
        case "tennis": startLesson(.tennis)
        case "skip": skipLessons()
        case "resume": if case .lesson(let sport) = step { startLesson(sport) }
        case "choose": move(to: .choose)
        case "other": if case .reward(let sport) = step { startLesson(sport == .golf ? .tennis : .golf) }
        case "menu": if case .reward(let sport) = step { finish(sport) }
        default: break
        }
    }
    // MARK: Your Apple Account (Game Center): friends, invites and online play need it, so it is asked for at the start

    /// Signed in to Game Center on this phone (Apple's sign-in for games: it carries the friends list and the invites).
    var signedIn: Bool { signedInOverride ?? GKLocalPlayer.local.isAuthenticated }
    /// Tests: the sign-in state without Game Center.
    var signedInOverride: Bool?
    var accountName: String { GKLocalPlayer.local.isAuthenticated ? GKLocalPlayer.local.displayName : "" }
    /// Apple's sign-in sheet on the phone (or the normal flow when Game Center has none to show). Once signed in the step's
    /// Next lights up by itself.
    func signIn() {
        Analytics.track("onboarding_sign_in")
        ClubSignIn.signIn()
        row = 0; column = 0
    }

    /// The phone opens its keyboard for the name (it is the only thing typed in onboarding).
    var nameRequested = false

    // MARK: Your player

    var player: Player? {
        let s = SportsSession.shared
        return s.players.indices.contains(s.playerIndex) ? s.players[s.playerIndex] : nil
    }
    var skinIndex: Int {
        guard let t = player?.skinT else { return 2 }
        return LockerColor.skinPresets.indices.min { abs(LockerColor.skinPresets[$0] - t) < abs(LockerColor.skinPresets[$1] - t) } ?? 2
    }
    var shirtIndex: Int { player?.outfitHex("shirt").map { LockerColor.nearest(Self.shirts, $0) } ?? 0 }
    @discardableResult func adjust(_ id: String, by step: Int) -> Bool {
        switch id {
        case "skin":
            let n = LockerColor.skinPresets.count, i = (skinIndex + step + n) % n
            edit { $0.setSkin(LockerColor.skinPresets[i]) }; return true
        case "shirt":
            let n = Self.shirts.count, i = (shirtIndex + step + n) % n
            edit { $0.setOutfitHex("shirt", Self.shirts[i]) }; return true
        default: return false
        }
    }
    func setName(_ value: String) { edit { $0.name = OnboardingStore.name(value) } }
    private func edit(_ change: (inout Player) -> Void) {
        let s = SportsSession.shared
        guard s.players.indices.contains(s.playerIndex) else { return }
        change(&s.players[s.playerIndex]); s.savePlayers()
    }
    private func save() {
        guard let p = player else { return }
        SportsSession.shared.savePlayers()
        MultiplayerService.shared.setIdentity(name: p.name, female: p.standardFemale, left: p.handedness == .left, loadout: p.multiplayerLoadout)
        Analytics.track("hero_created", ["female": String(p.standardFemale), "named": String(p.name != "Player 1")])
    }

    // MARK: Lessons

    /// Start (or resume) a sport's lesson. From onboarding, or from the menu's Lessons any time.
    func startLesson(_ sport: Sport) {
        guard sport.playable else { return }
        step = .lesson(sport); store.step = step; row = 0; column = 0
        lessonBegan = ProcessInfo.processInfo.systemUptime
        Analytics.track("tutorial_start", ["sport": sport.rawValue, "station": String(store.lessonStation(sport))])
        TennisMenu.shared.beginLesson(sport, station: store.lessonStation(sport))
    }
    /// Unity's lesson started a station (resumes there next time).
    func lessonStation(_ index: Int, sport: Sport) { store.setLessonStation(sport, index) }
    /// The lesson's last station is done: its reward, then on.
    func completed(_ sport: Sport) {
        progress.completeTutorial(sport)
        store.setLessonStation(sport, 0)
        if let player { Progression.shared.awardTutorial(player: player.id, sport: sport, store: store) }
        Analytics.track("tutorial_complete", ["sport": sport.rawValue, "seconds": String(lessonBegan.map { ProcessInfo.processInfo.systemUptime - $0 } ?? 0)])
        lessonBegan = nil
        step = .reward(sport); store.step = step; row = 0; column = 0
        if SportsSession.shared.active { SportsSession.shared.end() }
    }
    /// The game was left from its pause menu: a lesson stops and its screen offers Resume; anything else leaves onboarding.
    func gameLeft() {
        guard case .lesson = step else { exitToMenu(); return }
        LessonCenter.shared.end()
        if SportsSession.shared.active { SportsSession.shared.end() }
        row = 0; column = 0
    }
    private func skipLessons() {
        Analytics.track("onboarding_skip_lessons")
        store.explicitRun = false; move(to: .done)
        TennisMenu.shared.goHome()
    }
    func finish(_ sport: Sport, playNext: Bool = false) {
        store.explicitRun = false
        Analytics.track("onboarding_done", ["seconds_since_install": String(Analytics.secondsSinceInstall)])
        move(to: .done)
        if playNext { TennisMenu.shared.begin(sport == .golf ? MenuLaunch(sport: .golf, mode: .round) : MenuLaunch(sport: .tennis, mode: .exhibition, round: 0)) }
        else { TennisMenu.shared.goHome() }
    }
    /// Leaving onboarding from anywhere (tests, Settings): no reward is claimed.
    func exitToMenu() {
        store.explicitRun = false; lessonBegan = nil
        move(to: .done)
        TennisMenu.shared.goHome()
    }
    /// Settings → Replay onboarding.
    func replay() {
        // a lesson finished before pays nothing when it is played again
        for sport in [Sport.tennis, .golf] where progress.finishedTutorial(sport) && !store.rewardClaimed(sport) {
            store.markReward(sport, xp: 0, item: nil)
        }
        store.explicitRun = true; store.characterInitialized = true
        Analytics.track("onboarding_replay"); move(to: .hello)
        HubSession.shared.evaluate()
    }
}
