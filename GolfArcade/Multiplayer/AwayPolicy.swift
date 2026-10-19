import Foundation

/// What leaving the app (swiping home, the app switcher) does, as party games do it (Switch Sports, Mario Kart, Fortnite):
/// - on your own (menus, the Plaza, a local match): everything pauses where you left it and is there when you come back
///   (a match waits for Ready);
/// - in a friends' party: only your phone pauses; the party carries on and you are back in it when you return;
/// - in an online match: the match carries on without you (tennis: the CPU plays your side; golf: your turns pass) and you
///   take your place again when you return;
/// - away longer than `onlineLimit`: you are out of the match or party (the others see you leave), and your phone goes back to
///   the Plaza on its own when it opens again.
/// Control Center or a notification banner only makes the app inactive: that is not leaving.
@MainActor final class AwayPolicy {
    static let shared = AwayPolicy()
    static var onlineLimit: TimeInterval { MultiplayerTuning.awayLimitSeconds }
    /// Away at least this long, a Club Hub connection is assumed dead (iOS closes sockets of a suspended app) and is opened again.
    static let staleLinkSeconds: TimeInterval = 5

    var now: () -> Date = { Date() }
    private(set) var leftAt: Date?

    /// The app went to the background.
    func left() { if leftAt == nil { leftAt = now() } }
    /// The app is active again: how long it was away (0 when it never left).
    func returned() -> TimeInterval {
        defer { leftAt = nil }
        guard let leftAt else { return 0 }
        return max(0, now().timeIntervalSince(leftAt))
    }

    enum Outcome: Equatable { case stay, leaveMatch, leaveParty }
    /// What coming back after `seconds` away means for this phone.
    static func outcome(away seconds: TimeInterval, inOnlineMatch: Bool, inParty: Bool, droppedFromMatch: Bool) -> Outcome {
        if inOnlineMatch && (droppedFromMatch || seconds > onlineLimit) { return .leaveMatch }
        if inParty && seconds > onlineLimit { return .leaveParty }
        return .stay
    }
    static func notice(for outcome: Outcome) -> String {
        let minutes = Int(onlineLimit / 60)
        switch outcome {
        case .stay: return ""
        case .leaveMatch: return "You were away for more than \(minutes) minutes, so you left the match."
        case .leaveParty: return "You were away for more than \(minutes) minutes, so you left the party."
        }
    }
}
