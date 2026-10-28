import Foundation

// The party link (2026-10-27): what keeps a friends' party connected, in one place.
//
// A party is its leader. Every party meets in ONE private Game Center group worked out from the leader's gamePlayerID
// (`PartyGroup.of`), the same number on every phone, every time. So every way in (an invite card, Game Center's notification, a
// CloudKit knock or code, a relaunch, a phone coming back from the background) is the same thing: search the leader's group until
// the leader is there. The leader searches its own group while it expects someone (a friend it invited or who knocked, or a member
// whose phone dropped). Nothing has to pass between the phones first, so an invitation that got stuck, crossed, expired on one side
// or was answered twice still leads to the right place.
//
// Apple ends a GKMatch underneath the game whenever a phone leaves it (the background, Wi-Fi, the other phone hanging up): on iOS 26
// that is GameCenterFoundation.FastSyncTransportError error 4, `groupSessionInvalidated` (decoded from the iOS 26.3.1 and 26.6
// GameCenterFoundation binaries: cases internalError, illegalState, failedToElectLeader, failedToSendData,
// groupSessionInvalidated). Before this, the game kept the dead match, showed that text, and every send failed. Now a dead match is
// dropped and both phones meet again in the leader's group; the lobby, the Plaza and a match in progress carry on.
//
// (The file keeps its name so both Xcode projects still compile it; the one-handshake coordinator it held is gone.)

/// The private Game Center group a leader's party meets in.
enum PartyGroup {
    /// The same for the same leader on every phone and every launch (FNV-1a, never Swift's per-process Hasher), inside the private
    /// range GameCenterPartyInvitation accepts.
    static func of(_ leader: String) -> UInt32 {
        var h: UInt32 = 0x811C9DC5
        for b in leader.utf8 { h ^= UInt32(b); h = h &* 0x01000193 }
        return 0x60000000 | (h & 0x0FFFFFFF)
    }
    static func valid(_ group: UInt32) -> Bool { group >= 0x60000000 && group < 0x70000000 }
}

/// The party this phone is in, kept across a relaunch: who leads it and who is in it, and when they were last together.
struct PartyMemory: Codable, Equatable {
    var leader: String
    var leaderName: String
    var members: [String]
    /// Seconds since 1970 this phone last had someone from the party connected.
    var at: Double

    nonisolated(unsafe) static var defaults = UserDefaults.standard
    private static func key(_ local: String) -> String { "party.link.v1." + local }
    /// The party this phone was in, if it was together with it within `patience` seconds.
    static func load(_ local: String, now: Double, patience: Double) -> PartyMemory? {
        guard !local.isEmpty, let data = defaults.data(forKey: key(local)),
              let m = try? JSONDecoder().decode(PartyMemory.self, from: data), now - m.at <= patience, m.members.contains(local) else { return nil }
        return m
    }
    static func save(_ m: PartyMemory?, _ local: String) {
        guard !local.isEmpty else { return }
        if let m, let data = try? JSONEncoder().encode(m) { defaults.set(data, forKey: key(local)) } else { defaults.removeObject(forKey: key(local)) }
    }
}

/// What the party link does next on one phone, from what that phone knows now. Pure: every case is tested without Game Center.
enum PartyLinkPlan: Equatable {
    /// Nobody to connect: everyone this phone wants is here, or there is no party.
    case idle
    /// Not now (signed out, the background, a quick match, a match on, not in the Plaza). The next change or tick asks again.
    case wait(String)
    /// Meet in `group`: a new match of `min...max` players (this phone counted) with at least one of `need` in it.
    case find(group: UInt32, min: Int, max: Int, need: Set<String>)
    /// Bring one of `need` into the live match (the leader, with friends still connected to it).
    case add(group: UInt32, min: Int, max: Int, need: Set<String>)
    /// The leader has been gone longer than a party waits: the party is over on this phone.
    case lost

    struct Input {
        var local: String
        /// A Join this phone is making: the leader, and the party size it expects with this phone in it.
        var join: (leader: String, players: Int)?
        var party: PartyMemory?
        /// Leader: friends who may come in (invited, tapped Join, knocked), not in yet.
        var expected: Set<String> = []
        /// Connected to this phone's live match now.
        var connected: Set<String> = []
        /// Party members not connected, since when (seconds).
        var missingSince: [String: Double] = [:]
        var matchAlive = false
        /// This party's lobby is up on this phone (MultiplayerService is bound to it). A party remembered from before a relaunch is
        /// not, and waits for the Plaza like a new Join.
        var inLobby = false
        var signedIn = true, active = true, quickMatch = false
        /// In the Plaza: a party may be joined now.
        var canJoin = true
        /// New friends may be brought in now (false: later, a match is on; nil: never, this phone is a guest elsewhere).
        var canHost: Bool? = true
        var capacity = 4
        var now: Double
        var patience: Double
    }

    static func next(_ s: Input) -> PartyLinkPlan {
        if s.join == nil && s.party == nil && s.expected.isEmpty { return .idle }
        guard s.signedIn else { return .wait("not signed in to Game Center") }
        guard s.active else { return .wait("in the background") }
        guard !s.quickMatch else { return .wait("a quick match is searching") }
        func size(_ n: Int) -> Int { Swift.max(2, Swift.min(s.capacity, n)) }
        if let j = s.join {
            if s.connected.contains(j.leader) { return .idle }
            guard s.canJoin else { return .wait("joining once this phone is back in the Plaza") }
            return .find(group: PartyGroup.of(j.leader), min: 2, max: size(j.players), need: [j.leader])
        }
        if let p = s.party, p.leader != s.local {
            if s.connected.contains(p.leader) { return .idle }
            // (the leader left on purpose: the lobby hands the party to someone else, and the link follows)
            guard p.members.contains(p.leader) else { return .wait("the leader left; the party picks a new one") }
            if s.now - (s.missingSince[p.leader] ?? s.now) > s.patience { return .lost }
            guard s.inLobby || s.canJoin else { return .wait("back into the party once this phone is in the Plaza") }
            return .find(group: PartyGroup.of(p.leader), min: 2, max: size(p.members.count), need: [p.leader])
        }
        // leading: a party of its own, or friends invited to one
        let members = Set(s.party?.members ?? []).subtracting([s.local])
        var need = members.subtracting(s.connected).filter { s.now - (s.missingSince[$0] ?? s.now) <= s.patience }
        if !s.inLobby && s.canHost != true { need = [] }   // (a party remembered from a relaunch comes back in the Plaza)
        if s.canHost == true { need.formUnion(s.expected.subtracting(s.connected)) }
        if need.isEmpty { return s.expected.subtracting(s.connected).isEmpty ? .idle : .wait("friends come in after this match") }
        let group = PartyGroup.of(s.local)
        if s.matchAlive && !s.connected.isEmpty {
            let here = 1 + s.connected.count
            guard here < s.capacity else { return .wait("the party is full") }
            return .add(group: group, min: here + 1, max: Swift.min(s.capacity, here + need.count), need: need)
        }
        return .find(group: group, min: 2, max: size(1 + need.count), need: need)
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
