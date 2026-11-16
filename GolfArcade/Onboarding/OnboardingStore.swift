import Foundation

/// First launch (PLAN_Onboarding_v3_IntroTutorial.md, 2026-11-15): the menu loads first (on the TV or, with none, on the phone) and
/// an intro plays over it on the phone: welcome, make your player, how it works (motion control, TV or phone only, play safe), then
/// go to Play. From there Play is locked to the Tutorial (golf, tennis, bowling) until all three are done.
enum OnboardingStep: String, CaseIterable, Equatable {
    case welcome, customize, how, goPlay, tutorial, done
    var key: String { rawValue }
    init?(key: String) { self.init(rawValue: key) }
    /// The intro cards over the menu (before the Tutorial).
    var isIntro: Bool { self == .welcome || self == .customize || self == .how || self == .goPlay }
}

@MainActor
final class OnboardingStore {
    let defaults: UserDefaults
    init(defaults: UserDefaults = .standard) { self.defaults = defaults }
    static let stepKey = "ftue.step.v3"
    /// The step to come back to (a quit resumes there).
    var step: OnboardingStep {
        get { defaults.string(forKey: Self.stepKey).flatMap(OnboardingStep.init(key:)) ?? .welcome }
        set { defaults.set(newValue.key, forKey: Self.stepKey) }
    }
    /// This onboarding has saved a step on this phone (it was started here).
    var hasSavedStep: Bool { defaults.string(forKey: Self.stepKey) != nil }
    /// The 10-25 TV onboarding's step on this phone, if it ever ran ("done" = finished it).
    var legacyStep: String? { defaults.string(forKey: "ftue.step.v2") }
    /// The lesson station to resume a sport's lesson at (Unity's lesson reports each one it starts).
    func lessonStation(_ sport: Sport) -> Int { max(0, defaults.integer(forKey: "ftue.lessonStation.\(sport.rawValue).v1")) }
    func setLessonStation(_ sport: Sport, _ index: Int) { defaults.set(max(0, index), forKey: "ftue.lessonStation.\(sport.rawValue).v1") }
    /// Onboarding replayed from Settings (it runs even though lessons have been finished).
    var explicitRun: Bool {
        get { defaults.bool(forKey: "ftue.explicitRun.v1") }
        set { defaults.set(newValue, forKey: "ftue.explicitRun.v1") }
    }
    /// This phone went through the v4 onboarding (a fresh install, or a reset): each sport's own lesson comes before its games
    /// (Adnan 11-16: "only force them to do one tutorial at a time"). Older phones keep everything open.
    var sportGate: Bool {
        get { defaults.bool(forKey: "ftue.sportGate.v1") }
        set { defaults.set(newValue, forKey: "ftue.sportGate.v1") }
    }
    var characterInitialized: Bool {
        get { defaults.bool(forKey: "ftue.characterInitialized.v1") }
        set { defaults.set(newValue, forKey: "ftue.characterInitialized.v1") }
    }
    /// Tennis needs a TV: a phone with none may put the tennis lesson off (it stays in the Tutorial, Play unlocks without it).
    var tennisDeferred: Bool {
        get { defaults.bool(forKey: "ftue.tennisDeferred.v1") }
        set { defaults.set(newValue, forKey: "ftue.tennisDeferred.v1") }
    }
    var installedAt: TimeInterval {
        if let time = defaults.object(forKey: "ftue.installedAt.v1") as? Double { return time }
        let time = Date().timeIntervalSince1970
        defaults.set(time, forKey: "ftue.installedAt.v1")
        return time
    }
    func rewardClaimed(_ sport: Sport) -> Bool { defaults.bool(forKey: "ftue.reward.\(sport.rawValue).v1") }
    var anyRewardClaimed: Bool { [.tennis, .golf, .bowling].contains { rewardClaimed($0) } }
    func markReward(_ sport: Sport, xp: Int, item: String?) {
        defaults.set(true, forKey: "ftue.reward.\(sport.rawValue).v1")
        defaults.set(xp, forKey: "ftue.rewardXP.\(sport.rawValue).v1")
        defaults.set(item, forKey: "ftue.rewardItem.\(sport.rawValue).v1")
        if let item { requestEquip(item) }
    }
    func rewardXP(_ sport: Sport) -> Int { defaults.integer(forKey: "ftue.rewardXP.\(sport.rawValue).v1") }
    func rewardItem(_ sport: Sport) -> String? { defaults.string(forKey: "ftue.rewardItem.\(sport.rawValue).v1") }
    func requestEquip(_ item: String) { defaults.set(item, forKey: "ftue.equipRequested.v1") }
    func reset() {
        for key in defaults.dictionaryRepresentation().keys where key.hasPrefix("ftue.") { defaults.removeObject(forKey: key) }
    }
    static func name(_ value: String) -> String {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? "Player 1" : String(trimmed.prefix(14))
    }
}
