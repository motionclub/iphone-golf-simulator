import Foundation

/// First launch, on the TV (PLAN_Onboarding_GolfLesson.md): a welcome, the phone as the controller, room to swing, your
/// player and their club card, then the first lesson (golf or tennis) and its reward. A lesson is the only step that runs a game.
enum OnboardingStep: Equatable {
    case hello, account, controller, room, player, card, choose, lesson(Sport), reward(Sport), done
    var key: String {
        switch self {
        case .hello: "hello"; case .account: "account"; case .controller: "controller"; case .room: "room"; case .player: "player"
        case .card: "card"; case .choose: "choose"; case .done: "done"
        case .lesson(let sport): "lesson:\(sport.rawValue)"
        case .reward(let sport): "reward:\(sport.rawValue)"
        }
    }
    init?(key: String) {
        switch key {
        case "hello": self = .hello; case "account": self = .account; case "controller": self = .controller; case "room": self = .room
        case "player": self = .player; case "card": self = .card; case "choose": self = .choose; case "done": self = .done
        default:
            let pair = key.split(separator: ":").map(String.init)
            guard pair.count == 2, let sport = Sport(rawValue: pair[1]), sport.playable else { return nil }
            if pair[0] == "lesson" { self = .lesson(sport) }
            else if pair[0] == "reward" { self = .reward(sport) }
            else { return nil }
        }
    }
    /// The three parts the TV's top bar names.
    var act: Int {
        switch self {
        case .hello, .account, .controller, .room: 0
        case .player, .card: 1
        default: 2
        }
    }
}

@MainActor
final class OnboardingStore {
    let defaults: UserDefaults
    init(defaults: UserDefaults = .standard) { self.defaults = defaults }
    /// The step to come back to. Earlier builds' keys (account, connect, tutorial:…) read as the start.
    var step: OnboardingStep {
        get { defaults.string(forKey: "ftue.step.v2").flatMap(OnboardingStep.init(key:)) ?? .hello }
        set { defaults.set(newValue.key, forKey: "ftue.step.v2") }
    }
    /// This onboarding has saved a step on this phone (it was started here).
    var hasSavedStep: Bool { defaults.string(forKey: "ftue.step.v2") != nil }
    /// The lesson station to resume a sport's lesson at (Unity's lesson reports each one it starts).
    func lessonStation(_ sport: Sport) -> Int { max(0, defaults.integer(forKey: "ftue.lessonStation.\(sport.rawValue).v1")) }
    func setLessonStation(_ sport: Sport, _ index: Int) { defaults.set(max(0, index), forKey: "ftue.lessonStation.\(sport.rawValue).v1") }
    /// Onboarding replayed from Settings (it runs even though a lesson has been finished).
    var explicitRun: Bool {
        get { defaults.bool(forKey: "ftue.explicitRun.v1") }
        set { defaults.set(newValue, forKey: "ftue.explicitRun.v1") }
    }
    var characterInitialized: Bool {
        get { defaults.bool(forKey: "ftue.characterInitialized.v1") }
        set { defaults.set(newValue, forKey: "ftue.characterInitialized.v1") }
    }
    var installedAt: TimeInterval {
        if let time = defaults.object(forKey: "ftue.installedAt.v1") as? Double { return time }
        let time = Date().timeIntervalSince1970
        defaults.set(time, forKey: "ftue.installedAt.v1")
        return time
    }
    func rewardClaimed(_ sport: Sport) -> Bool { defaults.bool(forKey: "ftue.reward.\(sport.rawValue).v1") }
    var anyRewardClaimed: Bool { [.tennis, .golf].contains { rewardClaimed($0) } }
    func markReward(_ sport: Sport, xp: Int, item: String?) {
        defaults.set(true, forKey: "ftue.reward.\(sport.rawValue).v1")
        defaults.set(xp, forKey: "ftue.rewardXP.\(sport.rawValue).v1")
        defaults.set(item, forKey: "ftue.rewardItem.\(sport.rawValue).v1")
        if let item { requestEquip(item) }
    }
    func rewardXP(_ sport: Sport) -> Int { defaults.integer(forKey: "ftue.rewardXP.\(sport.rawValue).v1") }
    func rewardItem(_ sport: Sport) -> String? { defaults.string(forKey: "ftue.rewardItem.\(sport.rawValue).v1") }
    var requestedHeadband: Bool { defaults.string(forKey: "ftue.equipRequested.v1") == "white-headband" }
    func requestEquip(_ item: String) { defaults.set(item, forKey: "ftue.equipRequested.v1") }
    func reset() {
        for key in defaults.dictionaryRepresentation().keys where key.hasPrefix("ftue.") { defaults.removeObject(forKey: key) }
    }
    static func name(_ value: String) -> String {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? "Player 1" : String(trimmed.prefix(14))
    }
}
