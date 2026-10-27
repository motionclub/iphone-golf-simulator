import Foundation

/// One party handshake at a time on this phone (2026-10-26). On build 0.1.5 (11) up to five ran at once (the Game Center host's
/// bring-in, the Game Center guest's join, a CloudKit let-in, a CloudKit knock, the automatic rejoin), and each one tore down the
/// others: two friends who invited each other connected and dropped 1–2 s later, round after round.
///
/// Every path that connects this phone to another phone's party, or brings someone into its own, asks here first. The rules:
/// - one handshake at a time; another of the same kind is refused (it is already happening), a different host one waits (the next
///   inbox refresh or knock tick tries again);
/// - no host role while this phone is joining someone (it is about to leave whatever it would host);
/// - a join the player asked for (a tap on Join, a notification, a code) wins: whatever ran before is cancelled;
/// - an automatic join (a rejoin, a join resumed after a relaunch, a crossed invite) never starts while this phone is in a party
///   with other phones connected, and never cancels anything.
@MainActor
final class PartyJoinCoordinator {
    enum Kind: Equatable {
        /// Host, Game Center: bring in a friend who tapped Join on this phone's invitation (its record id).
        case hostInvite(String)
        /// Host, CloudKit: let in someone who knocked (their gamePlayerID).
        case hostKnock(String)
        /// Guest, Game Center: join a friend's party from their invitation (its record id).
        case joinInvite(String)
        /// Guest, CloudKit: drop in on a friend's party, or join with a code (the host's gamePlayerID).
        case joinKnock(String)
        /// Guest: Apple's own real-time invitation (the sender's gamePlayerID).
        case joinRealTime(String)
        var hosting: Bool { if case .hostInvite = self { return true }; if case .hostKnock = self { return true }; return false }
    }
    enum Origin: Equatable {
        /// The player said so (Join, a notification, a code): it wins over anything else.
        case player
        /// Nobody tapped anything: a rejoin, a join resumed after a relaunch, a crossed invite.
        case automatic
    }
    enum Refusal: Equatable, Error {
        /// The same handshake is already running, or another one this one must not cancel.
        case busy
        /// This phone is joining someone: it hosts nobody until that is over.
        case joining
        /// An automatic join would leave a party with friends in it.
        case inParty
    }
    enum Decision: Equatable { case start, supersede, refuse(Refusal) }
    struct Handshake: Equatable { let token: Int; let kind: Kind; let origin: Origin }

    /// What happens to `kind` asked for now, with `active` running. Pure: the rules above, tested without Game Center.
    static func decide(_ kind: Kind, _ origin: Origin, active: Handshake?, inConnectedParty: Bool) -> Decision {
        if !kind.hosting, origin == .automatic, inConnectedParty { return .refuse(.inParty) }
        guard let active else { return .start }
        if active.kind == kind { return .refuse(.busy) }
        if kind.hosting { return .refuse(active.kind.hosting ? .busy : .joining) }
        return origin == .player ? .supersede : .refuse(.busy)
    }

    private(set) var active: Handshake?
    /// This phone is in a party (any lobby) with other phones connected to it now.
    var inConnectedParty: @MainActor () -> Bool = { false }
    private var cancelActive: ((Int) -> Void)?
    private var counter = 0
    var joining: Bool { active.map { !$0.kind.hosting } ?? false }
    var hosting: Bool { active?.kind.hosting ?? false }

    /// The handshake's token, or nil when it may not start now. `cancel` stops it (its search) when a player's join supersedes it.
    func begin(_ kind: Kind, origin: Origin = .player, cancel: @escaping (Int) -> Void = { _ in }) -> Int? {
        switch Self.decide(kind, origin, active: active, inConnectedParty: inConnectedParty()) {
        case .refuse(let why):
            SportsDiagnostics.write("party handshake \(Self.name(kind)) refused: \(why) (running: \(active.map { Self.name($0.kind) } ?? "none"))")
            return nil
        case .supersede:
            if let old = active { SportsDiagnostics.write("party handshake \(Self.name(old.kind)) cancelled for \(Self.name(kind))") }
            stopActive()
        case .start: break
        }
        let token = ticket()
        active = Handshake(token: token, kind: kind, origin: origin); cancelActive = cancel
        return token
    }
    /// A number for a search that is not a party handshake (quick match), so its cancel never stops another one.
    func ticket() -> Int { counter += 1; return counter }
    func isCurrent(_ token: Int) -> Bool { active?.token == token }
    /// The handshake ended (in, failed or given up). Only the current one: a superseded handshake's end changes nothing.
    func end(_ token: Int) { if active?.token == token { active = nil; cancelActive = nil } }
    /// Stops the running handshake if `which` says so (its search is cancelled and it is no longer current).
    func cancel(where which: (Kind) -> Bool) { if let a = active, which(a.kind) { stopActive() } }
    private func stopActive() {
        guard let old = active else { return }
        let stop = cancelActive
        active = nil; cancelActive = nil
        stop?(old.token)
    }
    private static func name(_ kind: Kind) -> String {
        switch kind {
        case .hostInvite(let id): "host-invite \(id.prefix(8))"; case .hostKnock(let id): "host-knock \(id.prefix(8))"
        case .joinInvite(let id): "join-invite \(id.prefix(8))"; case .joinKnock(let id): "join-knock \(id.prefix(8))"
        case .joinRealTime(let id): "join-realtime \(id.prefix(8))"
        }
    }
}

/// Two friends who invite each other (or drop in on each other) at the same moment: one of them hosts, the same answer on both
/// phones, from what both can read. Before 2026-10-26 both phones joined each other and each join tore the other party down.
enum PartyTieBreak {
    /// Of two crossed invitations (each friend invited the other), whether `a` is the one that stays: one somebody already said Join
    /// to (past `invited`); else the bigger party's (nobody leaves friends behind); else the one whose host has the lower gamePlayerID.
    static func keeps(_ a: GameCenterPartyInvitation, over b: GameCenterPartyInvitation) -> Bool {
        let joinedA = a.step != .invited, joinedB = b.step != .invited
        if joinedA != joinedB { return joinedA }
        if a.players.count != b.players.count { return a.players.count > b.players.count }
        return a.host < b.host
    }
    /// The records (id, invitation) this phone can read → the ids to retire: for each friend with invitations both ways, every one
    /// but the one `keeps` keeps.
    static func losers(_ records: [(id: String, invite: GameCenterPartyInvitation)], local: String) -> Set<String> {
        let mine = records.filter { $0.invite.host == local }
        let theirs = records.filter { $0.invite.recipient == local && $0.invite.host != local }
        var out = Set<String>()
        for m in mine {
            for t in theirs where t.invite.host == m.invite.recipient { out.insert(keeps(m.invite, over: t.invite) ? t.id : m.id) }
        }
        return out
    }
    /// Two phones knocking on each other (CloudKit drop-in): the lower gamePlayerID hosts, the other one's knock goes in.
    static func localHosts(local: String, other: String) -> Bool { local < other }
}
