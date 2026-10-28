@preconcurrency import GameKit
import UIKit

private struct GameKitDelivery<T>: @unchecked Sendable { let value: T }

/// Game Center stores the invitation; the real-time match carries the party.
/// A tagged turn-based record is the readable inbox: the friend's card with Join, and Game Center's notification on their phone. Since
/// 2026-10-27 it is only a mailbox: the friend's Join turns it to `accepted` (which notifies the host's phone, even with the game
/// closed), and both phones meet in the leader's private group (PartyGroup) at once. `go` is from builds before that and means the same
/// as `accepted`.
struct GameCenterPartyInvitation: Codable, Equatable {
    /// v1 (2026-10-15…10-25) made the host wait in matchmaking for 2 minutes; its records are ignored and cleaned up.
    static let kindV2 = "motionclub.partyInvite.v2"
    /// 15 minutes: long enough to finish a match, or to open the game from Game Center's notification, before saying Join.
    static let lifetime: Double = 15 * 60_000
    /// Two phones' clocks never agree exactly; a few minutes of difference never hides an invitation.
    static let clockSlack: Double = 5 * 60_000
    enum Step: String, Codable { case invited, accepted, go }
    var kind = Self.kindV2
    var host: String
    var recipient: String
    var name: String
    var group: UInt32
    /// Everyone in the party once the friend is in.
    var players: [String]
    var expiresAt: Double
    var step = Step.invited
    /// Counts the go's of builds before 2026-10-27.
    var round = 0
    /// The leader inviting back a member whose phone dropped (builds before 2026-10-27): that phone accepts it by itself.
    var rejoin: Bool?
    func valid(for local: String, now: Double) -> Bool {
        kind == Self.kindV2 && recipient == local && host != local && !host.isEmpty
        && group >= 0x60000000 && group < 0x70000000 && (2...4).contains(players.count)
        && Set(players).count == players.count && players.contains(host) && players.contains(local)
        && expiresAt.isFinite && expiresAt > now && expiresAt <= now + Self.lifetime + Self.clockSlack
    }
    func card(_ matchID: String) -> HubInvite {
        HubInvite(inviteID: "gc:" + matchID, from: HubPlayerRef(id: host, name: name), sport: "party",
                  lobbyCode: matchID, group: group, capacity: players.count, expiresAt: expiresAt, rejoin: rejoin)
    }
}

/// What one phone does next with one stored invitation, from what it can see of it. Pure, so the inbox is tested without Game Center.
enum GameCenterInviteStep: Equatable {
    /// Nothing for this phone now (the other phone has the turn).
    case wait
    /// Friend: a card in the inbox, with Join.
    case card
    /// Friend: tapped Join before (the app was closed, or the connection failed): carry on joining.
    case resume
    /// Host: the friend tapped Join (the record is back on this phone's turn).
    case go
    /// Remove the record (the host's Friends row says why).
    case retire(Ending)
    enum Ending: Equatable { case expired, declined, hostLeft }

    static func next(_ invitation: GameCenterPartyInvitation, local: String, myTurn: Bool, hostHere: Bool, friendHere: Bool, now: Double) -> Self {
        guard invitation.kind == GameCenterPartyInvitation.kindV2 else { return .wait }
        if invitation.host == local {
            if invitation.expiresAt <= now { return .retire(.expired) }
            if !friendHere { return .retire(.declined) }
            return invitation.step == .accepted && myTurn ? .go : .wait
        }
        guard invitation.recipient == local else { return .wait }
        if invitation.expiresAt <= now { return .retire(.expired) }
        if !hostHere { return .retire(.hostLeft) }
        guard invitation.valid(for: local, now: now) else { return .wait }
        if invitation.step == .invited { return myTurn ? .card : .wait }
        return .resume
    }
}

/// The real-time match a party rides on, as the transport needs it: a GKMatch in the app, an in-memory one in tests
/// (PartyJoinHarnessTests), so phones' joins and drops can be replayed in-process.
@MainActor protocol PartyMatchLink: AnyObject {
    /// The other players in the match now (gamePlayerIDs).
    var playerIDs: [String] { get }
    var expectedPlayerCount: Int { get }
    func send(_ data: Data, to ids: [String]?, reliable: Bool) throws
    /// Matchmaking for this match is over (GKMatchmaker.finishMatchmaking).
    func finish()
    func hangUp()
}
@MainActor final class GameKitMatchLink: PartyMatchLink {
    let gk: GKMatch
    init(_ gk: GKMatch) { self.gk = gk }
    var players: [GKPlayer] { gk.players }
    var playerIDs: [String] { gk.players.map(\.gamePlayerID) }
    var expectedPlayerCount: Int { gk.expectedPlayerCount }
    func send(_ data: Data, to ids: [String]?, reliable: Bool) throws {
        let mode: GKMatch.SendDataMode = reliable ? .reliable : .unreliable
        if let ids { try gk.send(data, to: gk.players.filter { ids.contains($0.gamePlayerID) }, dataMode: mode) }
        else { try gk.sendData(toAllPlayers: data, with: mode) }
    }
    func finish() { GKMatchmaker.shared().finishMatchmaking(for: gk) }
    func hangUp() { gk.delegate = nil; gk.disconnect() }
}

/// Game Center's matchmaking as the party link needs it: GKMatchmaker in the app, an in-memory server in tests.
@MainActor protocol PartyMatchmaker: AnyObject {
    /// A new match in `group` with `min...max` players (this phone counted).
    func find(group: UInt32, min: Int, max: Int) async throws -> PartyMatchLink
    /// More players from `group` into `match` (`min...max`: the match's size with them).
    func add(to match: PartyMatchLink, group: UInt32, min: Int, max: Int) async throws
    /// Stops the search running now.
    func cancel()
}
@MainActor final class GameKitPartyMatchmaker: PartyMatchmaker {
    private func request(_ group: UInt32, _ min: Int, _ max: Int) throws -> GKMatchRequest {
        guard GKLocalPlayer.local.isAuthenticated else { throw MultiplayerError.unavailable("Sign in to Game Center first.") }
        let r = GKMatchRequest(); r.minPlayers = min; r.maxPlayers = max; r.defaultNumberOfPlayers = max; r.playerGroup = Int(group)
        return r
    }
    func find(group: UInt32, min: Int, max: Int) async throws -> PartyMatchLink {
        GameKitMatchLink(try await GKMatchmaker.shared().findMatch(for: request(group, min, max)))
    }
    func add(to match: PartyMatchLink, group: UInt32, min: Int, max: Int) async throws {
        guard let gk = (match as? GameKitMatchLink)?.gk else { throw MultiplayerError.unavailable("No Game Center match to add to.") }
        try await GKMatchmaker.shared().addPlayers(to: gk, matchRequest: request(group, min, max))
    }
    func cancel() { GKMatchmaker.shared().cancel() }
}

/// Game Center connection behind the in-app friends list. Only authentication may require an Apple controller.
@MainActor
final class GameCenterTransport: NSObject, MultiplayerTransport, GKMatchDelegate, GKLocalPlayerListener, GKMatchmakerViewControllerDelegate {
    #if DEBUG
    /// Tests: this phone's gamePlayerID (several phones in one process).
    var localIDOverride: String?
    var localID: String { localIDOverride ?? GKLocalPlayer.local.gamePlayerID }
    #else
    var localID: String { GKLocalPlayer.local.gamePlayerID }
    #endif
    /// The other players in the party's match now. A leader never counts someone who is not in its party or invited.
    var peers: [String] { match?.playerIDs.filter { !disconnected.contains($0) && !strangers.contains($0) } ?? [] }
    var onData: ((Data, String) -> Void)?
    var onPeersChanged: (() -> Void)?
    var onError: ((Error) -> Void)?
    var onConnected: (() -> Void)?
    private(set) var match: PartyMatchLink?
    /// `match` is a party's (the link's), not a quick match's.
    private var matchIsParty = false
    /// A party match found but still connecting: `match` stays the party's until this one is in.
    private var pendingMatch: PartyMatchLink?
    /// Every match this phone hangs up says why in SportsDiagnostics.log.
    private func drop(_ m: PartyMatchLink, _ why: String) {
        SportsDiagnostics.write("game center hangs up a match (players=\(m.playerIDs.count) expected=\(m.expectedPlayerCount)) — \(why)")
        m.hangUp()
    }
    /// The quick match (or find more) search's token; 0 when none.
    private var quickToken = 0
    private var tickets = 0
    private var registered = false
    private var disconnected: Set<String> = []
    private var activeController: GKMatchmakerViewController?
    override init() { super.init(); register() }
    var capacity: Int { min(4, GKMatchRequest.maxPlayersAllowedForMatch(of: .peerToPeer)) }

    private var authenticationWaiters: [CheckedContinuation<Void, Error>] = []
    private var authenticationPresenter: ((UIViewController) -> Void)?
    private var authenticationController: UIViewController?
    var onAuthenticationController: ((UIViewController) -> Void)?
    var onAuthenticationChanged: (() -> Void)?
    /// A party match connected (the leader's gamePlayerID): a new party, or the same one back after its match was lost.
    var onPartyConnected: ((String) -> Void)?
    /// The party's leader has been gone longer than a party waits (their name): the party is over on this phone.
    var onPartyLost: ((String) -> Void)?
    /// A line for the player about the party's connection ("Reconnecting…", "Back together").
    var onLinkNotice: ((String) -> Void)?
    /// This phone may go into a friend's party now (the Plaza: not a match, a load, onboarding or the background). No side effects.
    var joinAvailable: (() -> Bool)?
    /// Right before going into a friend's party: leave whatever party or search this phone is in. False: not now after all.
    /// `automatic` (a resumed or crossed join): never leave a party with friends connected for it.
    var canAcceptParty: ((_ automatic: Bool) -> Bool)?
    /// Host: true when friends can be brought in now; false: later (a match is on); nil: never (this phone is a guest in someone
    /// else's party now).
    var hostAvailable: (() -> Bool?)?
    /// This phone's party lobby is up (MultiplayerService is bound to this transport with a lobby).
    var partyInLobby: (() -> Bool)?
    /// In a lobby with other phones connected now.
    var inConnectedParty: (() -> Bool)?
    var onInvitations: (([HubInvite]) -> Void)?
    /// An invitation went out: the friend's teamPlayerID, the record's id, the party size with them.
    var onInvitationSent: ((String, String, Int) -> Void)?
    /// Host: what happened to an invitation, by the friend's teamPlayerID.
    var onOutgoing: ((String, Outgoing) -> Void)?
    /// Friend: where the join is.
    var onJoinStage: ((JoinStage) -> Void)?
    var invitationAllowed: ((String, String) -> Bool)?
    /// The player tapped Game Center's notification for this invitation: that tap is the Join (no second tap on our banner).
    var onInvitationOpened: ((HubInvite) -> Void)?
    /// `crossed`: the friend invited this phone too, and this phone goes into their party instead (PartyTieBreak). `failed`: the
    /// phones never connected.
    enum Outgoing: Equatable { case joining, waiting, joined, declined, expired, full, crossed, failed }
    enum JoinStage: Equatable { case waitingForHost, connecting }
    private var openedFromNotification: String?
    private var inbox: [String: GKTurnBasedMatch] = [:]
    private var inboxTimer: Timer?
    private var refreshingInbox = false
    /// Host: invitations out, by record id: the friend's ids. Rebuilt from Game Center on every refresh (it survives a relaunch).
    private var outgoing: [String: (teamID: String, gameID: String)] = [:]
    private var missingOutgoing: [String: Int] = [:]
    /// Friend: the records already resumed in this run.
    private var resumed: Set<String> = []
    /// Records a join gave up on while they could not be read: retired as soon as the inbox lists them.
    private var retireLater: Set<String> = []
    /// A turn event while a refresh was running: read the inbox again right after it.
    private var refreshAgain = false
    /// An Apple real-time invitation accepted while a match was on: joined once this phone is in the Plaza.
    private var pendingRealTimeInvite: GKInvite?
    /// Leader: let in friends invited from another phone of the party (it said so with partyAdmission). Kept for the protocol: a
    /// member's phone lets in whoever the leader's match brings.
    func allowPartyPlayer(_ id: String) { if leading { expected[id] = max(expected[id] ?? 0, Self.now + GameCenterPartyInvitation.lifetime) } }
    /// Taken out of the party: no way back in without a new invite.
    func disallowPartyPlayer(_ id: String) {
        expected[id] = nil; missingSince[id] = nil; barred.insert(id)
        party?.members.removeAll { $0 == id }; saveParty()
        cancelInvite(id)
    }
    private static var now: Double { Date().timeIntervalSince1970 * 1000 }

    func authenticate(present: @escaping (UIViewController) -> Void) async throws {
        if GKLocalPlayer.local.isAuthenticated { register(); return }
        try await withCheckedThrowingContinuation { continuation in
            authenticationWaiters.append(continuation)
            authenticationPresenter = present
            if let authenticationController { if authenticationController.presentingViewController == nil { present(authenticationController) }; return }
            guard authenticationWaiters.count == 1 else { return }
            GKLocalPlayer.local.authenticateHandler = { [weak self] controller, error in
                let delivery = GameKitDelivery(value: controller)
                Task { @MainActor [weak self] in
                    guard let self else { return }
                    self.authenticationController = delivery.value
                    if let controller = delivery.value { (self.authenticationPresenter ?? self.onAuthenticationController)?(controller); return }
                    let result: Result<Void, Error>
                    if GKLocalPlayer.local.isAuthenticated { self.register(); result = .success(()) }
                    else { result = .failure(error ?? MultiplayerError.unavailable("Sign in to Game Center to invite friends.")) }
                    let waiters = self.authenticationWaiters
                    self.authenticationWaiters.removeAll()
                    self.authenticationPresenter = nil
                    for waiter in waiters { waiter.resume(with: result) }
                    self.onAuthenticationChanged?()
                }
            }
        }
    }

    // MARK: the party link

    /// The party this phone is in (kept across a relaunch): it outlives any one GKMatch.
    private(set) var party: PartyMemory?
    /// A Join this phone is making: whose party, the size it expects, until when, and what started it (a record, a knock).
    private struct JoinGoal { var leader: String; var name: String; var players: Int; var until: Date; var record: String?; var knock: Int? }
    private var goal: JoinGoal?
    /// Leader: friends who may come in now (invited, tapped Join, knocked): gamePlayerID → until when (ms since 1970).
    private var expected: [String: Double] = [:]
    /// Party members not connected now, since when (seconds since 1970).
    private var missingSince: [String: Double] = [:]
    /// Left the party on purpose (said bye) or taken out of it: never waited for, never let back in by the link.
    private var departed: Set<String> = []
    private var barred: Set<String> = []
    /// Players a leader's match brought in who are not in its party or invited: told to go, never heard.
    private var strangers: Set<String> = []
    /// When each player of the party's match was last heard from (any packet, or the link's ping).
    private var lastHeard: [String: Date] = [:]
    private var linkTask: Task<Void, Never>?
    private var linkKicked = false
    /// The link's search running now (its number), 0 when none. Only the link's own search is ever cancelled by it.
    private var linkSearch = 0
    /// Apple's own real-time invitation is being joined (the link waits for it).
    private var realTimeJoining = false
    private var savedAt = Date.distantPast
    private var lostNoticeShown = false
    /// The matchmaking the link uses: GKMatchmaker (tests: an in-memory server).
    var matchmaker: PartyMatchmaker = GameKitPartyMatchmaker()
    var signedIn: () -> Bool = { GKLocalPlayer.local.isAuthenticated }
    var appActive: () -> Bool = { UIApplication.shared.applicationState == .active }

    /// How long a party waits for a phone that dropped (the background, Wi-Fi, a relaunch) before it is over.
    static var patience: Double { MultiplayerTuning.partyPatienceSeconds }
    /// Seconds one search runs before the link looks again at what it needs.
    static var searchSeconds = 30.0
    /// Seconds a found match may take to connect the player it was for.
    static var connectSeconds = 20.0
    static var connectPollMilliseconds = 200
    /// A party match where nobody has been heard for this long is as good as gone (the other phone's match may have died first).
    static var silentSeconds = 12.0
    /// Seconds between the link's looks while it waits out a failure (doubling up to 5).
    static var retryUnit = 1.0
    /// The link's own packets (a ping, a bye), sent beside the lobby's; never handed on to the lobby.
    static let linkMagic = Data("MCLINK1:".utf8)
    private static let ping = linkMagic + Data("ping".utf8), bye = linkMagic + Data("bye".utf8)

    private var leading: Bool { goal == nil && (party == nil || party?.leader == localID) }
    /// Going into someone else's party now.
    var joining: Bool { goal != nil || realTimeJoining }
    /// The group this phone's own party meets in (CloudKit knocks find it there).
    func hostGroup() -> UInt32 { PartyGroup.of(localID) }
    /// A party member this phone is waiting to see again (it dropped, it did not leave): the lobby keeps their place meanwhile.
    func waitingFor(_ id: String) -> Bool {
        guard let party, party.members.contains(id), !departed.contains(id), !peers.contains(id) else { return false }
        return Date().timeIntervalSince1970 - (missingSince[id] ?? Date().timeIntervalSince1970) <= Self.patience
    }
    /// The lobby's leader changed (handed over, or made leader): the party meets in the new leader's group from now on.
    func setLeader(_ id: String, name: String) {
        guard var p = party, p.leader != id, p.members.contains(id) || id == localID else { return }
        SportsDiagnostics.write("party link: leader is now \(id.suffix(6))")
        p.leader = id; p.leaderName = name; party = p; saveParty(force: true)
        stopLinkSearch(); runLink()   // (a search in the old leader's group is over)
    }

    private func planInput() -> PartyLinkPlan.Input {
        let nowS = Date().timeIntervalSince1970
        var s = PartyLinkPlan.Input(local: localID, now: nowS, patience: Self.patience)
        s.join = goal.map { (leader: $0.leader, players: $0.players) }
        s.party = party
        s.expected = Set(expected.keys)
        s.connected = Set(peers)
        s.missingSince = missingSince
        s.matchAlive = match != nil
        s.inLobby = partyInLobby?() ?? false
        // (a match with no party behind it is a quick match: the link leaves it alone)
        s.signedIn = signedIn(); s.active = appActive(); s.quickMatch = quickToken != 0 || realTimeJoining || (match != nil && !matchIsParty)
        s.canJoin = joinAvailable?() ?? true
        s.canHost = hostAvailable == nil ? true : hostAvailable!()
        s.capacity = capacity
        return s
    }
    /// Forgets what ran out: invitations past their time, members gone longer than a party waits, a Join past its wait.
    private func prune() {
        let ms = Self.now, s = Date().timeIntervalSince1970
        expected = expected.filter { $0.value > ms && !barred.contains($0.key) }
        guard var p = party, p.leader == localID else { return }
        let gone = p.members.filter { $0 != localID && s - (missingSince[$0] ?? s) > Self.patience }
        guard !gone.isEmpty else { return }
        SportsDiagnostics.write("party link: \(gone.map { String($0.suffix(6)) }) gone longer than \(Int(Self.patience)) s, out of the party")
        p.members.removeAll { gone.contains($0) }
        for id in gone { missingSince[id] = nil }
        party = p.members.count > 1 ? p : nil
        saveParty(force: true)
    }
    func planLink() -> PartyLinkPlan { prune(); return PartyLinkPlan.next(planInput()) }

    /// Look again at what the party needs, and connect it. One loop, one search at a time; every way in and every drop comes here.
    func runLink() {
        linkKicked = true
        guard linkTask == nil else { return }
        linkTask = Task { @MainActor [weak self] in
            var failures = 0
            while let self {
                self.linkKicked = false
                let plan = self.planLink()
                switch plan {
                case .idle, .wait:
                    self.linkTask = nil
                    return
                case .lost:
                    self.partyLost()
                case .find(let group, let min, let max, let need):
                    do { try await self.meet(group: group, min: min, max: max, need: need); failures = 0 }
                    catch { failures += 1; await self.afterFailure(error, failures, "find in \(String(group, radix: 16))") }
                case .add(let group, let min, let max, let need):
                    do { try await self.bringMore(group: group, min: min, max: max, need: need); failures = 0 }
                    catch { failures += 1; await self.afterFailure(error, failures, "add from \(String(group, radix: 16))") }
                }
                try? await Task.sleep(for: .milliseconds(50))   // (never a tight loop, whatever Game Center answers)
            }
        }
    }
    private func afterFailure(_ error: Error, _ failures: Int, _ what: String) async {
        if failures <= 3 || failures % 10 == 0 { SportsDiagnostics.write("party link: \(what) failed (\(failures)): \(error.localizedDescription)") }
        await linkNap(min(5, Self.retryUnit * Double(1 << min(failures - 1, 3))))
    }
    /// Waits `seconds`, or less when something changed (a drop, a Join, a cancel).
    private func linkNap(_ seconds: Double) async {
        linkKicked = false
        let end = Date().addingTimeInterval(seconds)
        while !linkKicked, Date() < end, !Task.isCancelled { try? await Task.sleep(for: .milliseconds(50)) }
    }
    /// One search, cut off after `searchSeconds` (the loop then looks again).
    private func search<T>(_ work: () async throws -> T) async throws -> T {
        tickets += 1; let mine = tickets; linkSearch = mine
        let timer = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(Self.searchSeconds))
            guard !Task.isCancelled, let self, self.linkSearch == mine else { return }
            self.linkSearch = 0; self.matchmaker.cancel()
        }
        defer { timer.cancel(); if linkSearch == mine { linkSearch = 0 } }
        return try await work()
    }
    /// Stops the link's search (a quick match, a leave, a cancelled Join), never anyone else's.
    private func stopLinkSearch() { if linkSearch != 0 { linkSearch = 0; matchmaker.cancel() } }

    private func meet(group: UInt32, min: Int, max: Int, need: Set<String>) async throws {
        let found = try await search { try await matchmaker.find(group: group, min: min, max: max) }
        // (the party changed while searching: a cancel, a leave, another Join)
        guard case .find(let still, _, _, _) = planLink(), still == group else { drop(found, "its search outlived what the party needed"); return }
        try await attachParty(found, need: need)
    }
    private func bringMore(group: UInt32, min: Int, max: Int, need: Set<String>) async throws {
        guard let live = match else { return }
        try await search { try await matchmaker.add(to: live, group: group, min: min, max: max) }
        let end = Date().addingTimeInterval(Self.connectSeconds)
        while match === live, !peers.contains(where: need.contains) {
            guard Date() < end else { throw MultiplayerError.unavailable("Couldn't connect to your friend. Try again.") }
            try await Task.sleep(for: .milliseconds(Self.connectPollMilliseconds))
        }
        if match === live { live.finish() }
    }

    /// Whose party a match this phone finds now belongs to.
    private var targetLeader: String { goal?.leader ?? party?.leader ?? localID }
    /// A leader lets in its members and whoever it invited; anyone else Game Center puts in its group is told to go.
    private func allowed(_ id: String) -> Bool {
        guard leading else { return true }
        return id == localID || !barred.contains(id) && (expected[id] != nil || (party?.members.contains(id) ?? false))
    }

    /// A match was found: it is the party's once one of `need` is really connected to it. Game Center hands the match over while the
    /// phones are still connecting (players empty, expectedPlayerCount above 0): it waits, then binds; one that never connects throws
    /// and the link searches again. The party's live match stays until the new one is in.
    private func attachParty(_ found: PartyMatchLink, need: Set<String>) async throws {
        if let outsider = found.playerIDs.first(where: { !allowed($0) }) {
            try? found.send(Self.bye, to: [outsider], reliable: true)
            drop(found, "found match holds \(outsider.suffix(6)), who is not in this party or invited")
            throw MultiplayerError.unavailable("Game Center connected a player outside this party.")
        }
        pendingMatch = found; (found as? GameKitMatchLink)?.gk.delegate = self
        defer { if pendingMatch === found { pendingMatch = nil } }
        do { try await waitForPlayers(found, need) }
        catch { drop(found, "found match never connected: \(error.localizedDescription)"); throw error }
        adopt(found)
    }
    /// Until one of `need` is connected to `found` (and Game Center is not still connecting others, for a moment), or `connectSeconds`.
    private func waitForPlayers(_ found: PartyMatchLink, _ need: Set<String>) async throws {
        let started = Date()
        SportsDiagnostics.write("party match found: players=\(found.playerIDs.count) expected=\(found.expectedPlayerCount) waiting for \(need.map { String($0.suffix(6)) }.sorted())")
        while true {
            if pendingMatch !== found { throw CancellationError() }
            let here = Set(found.playerIDs)
            let elapsed = Date().timeIntervalSince(started)
            if !here.isDisjoint(with: need) && (found.expectedPlayerCount == 0 || elapsed > 1.5) {
                SportsDiagnostics.write("party match connected after \(String(format: "%.1f", elapsed)) s: players=\(found.playerIDs.count)")
                return
            }
            // everyone it was going to get is in, and not who it is for (two members met while their leader was away)
            if !here.isEmpty && found.expectedPlayerCount == 0 && here.isDisjoint(with: need) {
                throw MultiplayerError.unavailable("Game Center connected the wrong players.")
            }
            if elapsed > Self.connectSeconds {
                SportsDiagnostics.write("party match never connected: players=\(found.playerIDs.count) expected=\(found.expectedPlayerCount)")
                throw MultiplayerError.unavailable("Couldn't connect to your friend. Check the internet on both phones and try again.")
            }
            try await Task.sleep(for: .milliseconds(Self.connectPollMilliseconds))
        }
    }
    /// The found match is the party's now: whose party it is, who is in it, and what that answers.
    private func adopt(_ found: PartyMatchLink) {
        let leader = targetLeader
        let name = goal.map(\.name) ?? (party?.leader == leader ? party?.leaderName : nil) ?? (leader == localID ? GKLocalPlayer.local.displayName : "your friend")
        let healed = party?.leader == leader
        if let old = match, old !== found { drop(old, "replaced by the party's new match") }
        match = found; matchIsParty = true; disconnected.removeAll(); strangers.removeAll()
        let s = Date().timeIntervalSince1970
        for id in found.playerIDs { lastHeard[id] = Date(); missingSince[id] = nil; departed.remove(id) }
        var members = Set(found.playerIDs + [localID, leader])
        if healed, let p = party { members.formUnion(p.members) }
        for id in members where id != localID && !found.playerIDs.contains(id) { missingSince[id] = missingSince[id] ?? s }
        party = PartyMemory(leader: leader, leaderName: name, members: members.sorted(), at: s)
        if goal?.leader == leader { goal = nil }
        for id in found.playerIDs { expected[id] = nil }
        saveParty(force: true)
        found.finish()
        answered(found.playerIDs)
        SportsDiagnostics.write("party link: \(healed ? "back together" : "in") \(leader == localID ? "my" : String(leader.suffix(6)) + "'s") party, players=\(found.playerIDs.map { String($0.suffix(6)) })")
        if lostNoticeShown { lostNoticeShown = false; onLinkNotice?("Back together!") }
        onPartyConnected?(leader); onPeersChanged?()
        runLink()
    }
    /// Leader: friends now in the party answered their invitations (the records go, the Friends rows say joined).
    private func answered(_ ids: [String]) {
        for (record, out) in outgoing where ids.contains(out.gameID) {
            outgoing[record] = nil; missingOutgoing[record] = nil
            onOutgoing?(out.teamID, .joined)
            Task { if let stored = try? await GKTurnBasedMatch.load(withID: record) { await self.retire(stored) } }
        }
    }
    /// The party's match is gone (Apple ended it: error 4, groupSessionInvalidated; everyone left it; nobody heard). The party stays:
    /// the link meets again in the leader's group. A quick match has nothing to go back to and says so in words.
    private func matchDied(_ why: String) {
        guard let dead = match else { return }
        drop(dead, "the match is gone: \(why)")
        match = nil; disconnected.removeAll(); strangers.removeAll()
        if var p = party {
            let s = Date().timeIntervalSince1970
            for id in p.members where id != localID { missingSince[id] = missingSince[id] ?? s }
            p.at = s; party = p; saveParty(force: true)
            if !lostNoticeShown { lostNoticeShown = true; onLinkNotice?(p.leader == localID ? "Lost the connection to your party. Reconnecting…" : "Lost the connection to \(p.leaderName)'s party. Reconnecting…") }
        } else if !matchIsParty {
            onError?(MultiplayerError.unavailable("The online match lost its connection."))
        }
        onPeersChanged?()
        runLink()
    }
    /// A member whose leader never came back: the party is over here.
    private func partyLost() {
        let name = party?.leaderName ?? "your friend"
        SportsDiagnostics.write("party link: the leader has been gone longer than \(Int(Self.patience)) s, the party is over here")
        party = nil; saveParty(force: true); missingSince.removeAll(); lostNoticeShown = false
        if let m = match { drop(m, "the party is over"); match = nil }
        onPartyLost?(name)
        onPeersChanged?()
    }
    /// Remembers the party for a relaunch (when it changed, or every 10 s while together).
    private func saveParty(force: Bool = false) {
        guard force || Date().timeIntervalSince(savedAt) > 10 else { return }
        savedAt = Date()
        PartyMemory.save(party, localID)
    }
    /// The party this phone was in before the app closed: back into it (the Plaza first, if it was a member).
    private func restoreParty() {
        guard party == nil, goal == nil, let m = PartyMemory.load(localID, now: Date().timeIntervalSince1970, patience: Self.patience) else { return }
        SportsDiagnostics.write("party link: back into \(m.leader == localID ? "my" : String(m.leader.suffix(6)) + "'s") party from before the app closed (\(m.members.count) players)")
        party = m
        for id in m.members where id != localID { missingSince[id] = m.at }
        runLink()
    }
    /// Every few seconds: tell the party this phone is here, notice a match nobody hears any more, remember the party, look again.
    private func linkTick() {
        if let m = match, party != nil, !peers.isEmpty {
            try? m.send(Self.ping, to: nil, reliable: false)
            let silent = peers.allSatisfy { Date().timeIntervalSince(lastHeard[$0] ?? Date()) > Self.silentSeconds }
            if silent { matchDied("nobody heard for \(Int(Self.silentSeconds)) s"); return }
            if var p = party { p.at = Date().timeIntervalSince1970; party = p; saveParty() }
        }
        runLink()
    }
    /// The app is open again: a match that died in the background is noticed now, not at the next send.
    func appBecameActive() {
        if party != nil, match != nil, peers.isEmpty { matchDied("nobody left in it after the background") }
        runLink()
    }

    // MARK: going into a friend's party (an invite, a knock or code, Apple's own invite)

    /// Starts a Join on `leader`'s party and waits until this phone is in it. Throws words a player can act on; a cancel (or another
    /// Join) throws CancellationError.
    private func joinParty(leader: String, name: String, players: Int, seconds: Double, record: String? = nil, knock: Int? = nil) async throws {
        if peers.contains(leader) { return }
        // a phone going into someone else's party hosts nobody: its own invitations are taken back
        for out in outgoing.values { cancelInvite(out.gameID) }
        expected.removeAll()
        let until = Date().addingTimeInterval(seconds)
        goal = JoinGoal(leader: leader, name: name, players: players, until: until, record: record, knock: knock)
        SportsDiagnostics.write("party link: joining \(leader.suffix(6)) (group \(String(PartyGroup.of(leader), radix: 16)), \(Int(seconds)) s)")
        stopLinkSearch(); runLink()
        while true {
            guard let g = goal, g.leader == leader, g.until == until else {
                if party?.leader == leader, peers.contains(leader) { return }
                throw CancellationError()
            }
            if Date() > until {
                goal = nil; stopLinkSearch()
                throw MultiplayerError.unavailable("Couldn't reach \(name). Make sure Motion Club is open on their phone, then tap Join again.")
            }
            try await Task.sleep(for: .milliseconds(100))
        }
    }
    /// Stops a Join this phone is making (`where` says which).
    private func cancelGoal(_ why: String, where which: (JoinGoal) -> Bool = { _ in true }) {
        guard let g = goal, which(g) else { return }
        SportsDiagnostics.write("party link: join on \(g.leader.suffix(6)) stopped — \(why)")
        goal = nil; stopLinkSearch(); runLink()
    }

    /// A cold start from an invite's notification: Game Center may still be signing in. Waits for it (it used to fail at once).
    func untilSignedIn(seconds: Double = 30) async throws {
        let end = Date().addingTimeInterval(seconds)
        while !signedIn() {
            guard Date() < end else { throw MultiplayerError.unavailable("Sign in to Game Center to join your friend.") }
            try await Task.sleep(for: .milliseconds(250))
        }
        register()
    }

    /// The friend tapped Join (on a card, a notification, or by itself for a crossed or resumed one): into the inviter's party. The
    /// record is told (that notifies the host's phone, even with the game closed), but nothing waits for it: both phones meet in the
    /// host's group, so a record that can't be read or answered any more still gets them together while the host is there.
    func acceptStoredInvitation(_ card: HubInvite) async throws {
        let id = card.lobbyCode, who = card.from.name, leader = card.from.id, automatic = card.automatic == true
        // already together (the party came back by itself, or an old notification): nothing to join
        if peers.contains(leader) {
            if let stored = try? await GKTurnBasedMatch.load(withID: id) { await retire(stored) }
            return
        }
        // an automatic join never takes this phone out of a party with friends in it; a Join the player tapped leaves it now
        if automatic, inConnectedParty?() == true { throw CancellationError() }
        guard canAcceptParty?(automatic) != false else { throw CancellationError() }
        resumed.insert(card.id); inbox[card.id] = nil
        JoinMemory.tapped(card.id)
        onJoinStage?(.waitingForHost)
        Task { @MainActor [weak self] in await self?.sayJoin(record: id) }
        // as long as the invitation lasts (the host may be finishing a match), at least 3 minutes
        let seconds = min(GameCenterPartyInvitation.lifetime, max(180_000, card.expiresAt - Self.now)) / 1000
        do {
            try await joinParty(leader: leader, name: who, players: max(2, card.capacity), seconds: seconds, record: id)
        } catch {
            JoinMemory.forget(card.id)
            if !(error is CancellationError) { retireLater.insert(id) }
            throw error
        }
        JoinMemory.forget(card.id)
        if let stored = try? await GKTurnBasedMatch.load(withID: id) { await retire(stored) }
    }
    /// The friend's Join on the record: accept it, and hand the turn to the host with PARTY_READY (Game Center notifies the host's
    /// phone). Best effort: the join itself never waits for it.
    private func sayJoin(record id: String) async {
        for attempt in 0..<4 {
            if attempt > 0 { try? await Task.sleep(for: .seconds(2)) }
            guard let stored = try? await GKTurnBasedMatch.load(withID: id), stored.status != .ended,
                  let data = try? await stored.loadMatchData(), var invite = try? JSONDecoder().decode(GameCenterPartyInvitation.self, from: data),
                  invite.recipient == localID, let host = participant(stored, invite.host) else { continue }
            if participant(stored, localID)?.status == .invited { _ = try? await stored.acceptInvite(); continue }
            guard stored.currentParticipant?.player?.gamePlayerID == localID, invite.step != .accepted else { return }
            invite.step = .accepted
            stored.setLocalizableMessageWithKey("PARTY_READY", arguments: [GKLocalPlayer.local.displayName])
            if (try? await stored.endTurn(withNextParticipants: [host], turnTimeout: Self.turnTimeout(invite), match: JSONEncoder().encode(invite))) != nil { return }
        }
    }

    /// The player cancelled the join: stop, and tell the host (their row says Not now).
    func cancelJoin() {
        guard let g = goal, let id = g.record else { cancelGoal("cancelled"); return }
        cancelGoal("cancelled")
        JoinMemory.forget("gc:" + id)
        Task { if let stored = try? await GKTurnBasedMatch.load(withID: id) { await retire(stored) } }
    }

    /// Joiner, CloudKit: a knock on `host` begins (a player's action: it stops a Join from an invitation). Its number.
    private var knock: (token: Int, host: String, onCancel: () -> Void)?
    func beginKnockJoin(host: String, onCancel: @escaping () -> Void) -> Int? {
        if let old = knock { knock = nil; old.onCancel() }
        cancelGoal("a knock on someone's party") { $0.knock == nil }
        tickets += 1
        knock = (tickets, host, onCancel)
        return tickets
    }
    func endKnock(_ token: Int) {
        guard knock?.token == token else { return }
        knock = nil
        cancelGoal("the knock ended") { $0.knock == token }
    }
    /// Joiner: into the host's party after its answer (a knock or a code).
    func joinGroup(host: String, group: UInt32, players: Int) async throws {
        try await joinParty(leader: host, name: "your friend", players: max(2, players), seconds: 45, knock: knock?.host == host ? knock?.token : nil)
    }
    /// Host: let in someone who knocked (a friend dropping in, or someone with the code). Throws when they never came in.
    func letIn(_ gameID: String, group: UInt32, players: Int) async throws {
        guard leading else { throw MultiplayerError.unavailable("Only the party leader can let people in.") }
        expected[gameID] = max(expected[gameID] ?? 0, Self.now + 90_000)
        runLink()
        let end = Date().addingTimeInterval(60)
        while !peers.contains(gameID) {
            guard Date() < end else { throw MultiplayerError.unavailable("Couldn't connect. Try again.") }
            try await Task.sleep(for: .milliseconds(200))
        }
    }

    // MARK: invitations you send

    /// Sends the stored invitation and returns. The link then looks for the friend in this phone's group, and the friend's Join meets it
    /// there (several friends can be invited at once).
    func invite(_ player: GKPlayer) async throws {
        guard !outgoing.values.contains(where: { $0.gameID == player.gamePlayerID }) else { return }
        guard peers.count + 2 <= capacity else { throw MultiplayerError.full }
        guard leading else { throw MultiplayerError.invalidOperation("The party leader can invite friends.") }
        let members = Array(Set([localID, player.gamePlayerID] + peers)).sorted()
        let invitation = GameCenterPartyInvitation(host: localID, recipient: player.gamePlayerID,
            name: GKLocalPlayer.local.displayName, group: hostGroup(), players: members,
            expiresAt: Self.now + GameCenterPartyInvitation.lifetime)
        let storedRequest = try request(sport: nil, count: 2)
        storedRequest.playerGroup = Int(invitation.group); storedRequest.recipients = [player]
        storedRequest.inviteMessage = "Come play with me in Motion Club!"
        let stored: GKTurnBasedMatch
        do { stored = try await GKTurnBasedMatch.find(for: storedRequest) }
        catch { throw Self.friendly(error, "Game Center could not send the invite. Try again.") }
        let next = stored.participants.filter { $0.player?.gamePlayerID != localID }
        guard !next.isEmpty, stored.currentParticipant?.player?.gamePlayerID == localID else {
            await retire(stored)
            throw MultiplayerError.unavailable("Game Center could not send the invite. Try again.")
        }
        do {
            try await stored.endTurn(withNextParticipants: next, turnTimeout: GameCenterPartyInvitation.lifetime / 1000,
                                     match: JSONEncoder().encode(invitation))
        } catch { await retire(stored); throw Self.friendly(error, "Game Center could not send the invite. Try again.") }
        outgoing[stored.matchID] = (player.teamPlayerID, player.gamePlayerID)
        barred.remove(player.gamePlayerID); departed.remove(player.gamePlayerID)
        expected[player.gamePlayerID] = invitation.expiresAt
        onInvitationSent?(player.teamPlayerID, stored.matchID, members.count)
        runLink()
    }

    /// SharePlay: the game shows up on this phone's FaceTime call (Apple's SharePlay bar), and each person on the call who wants to
    /// play gets our invite (the same banner and Join as any friend). It runs until the party ends.
    var onSharePlayInvited: ((String) -> Void)?
    private(set) var sharing = false
    func startSharePlay() {
        guard !sharing else { return }
        sharing = true
        GKMatchmaker.shared().startGroupActivity { [weak self] player in
            let delivery = GameKitDelivery(value: player)
            Task { @MainActor [weak self] in
                guard let self else { return }
                do { try await self.invite(delivery.value); self.onSharePlayInvited?(delivery.value.displayName) }
                catch { self.onError?(Self.friendly(error, "Couldn't invite \(delivery.value.displayName). Try again.")) }
            }
        }
    }
    func stopSharePlay() { guard sharing else { return }; sharing = false; GKMatchmaker.shared().stopGroupActivity() }

    /// Host: take back the invitation(s) to this friend.
    func cancelInvite(_ gameID: String) {
        expected[gameID] = nil
        for (id, out) in outgoing where out.gameID == gameID {
            outgoing[id] = nil
            Task { if let stored = try? await GKTurnBasedMatch.load(withID: id) { await retire(stored) } }
        }
    }

    // MARK: the inbox (both sides)

    /// Apple's stored records, polled every 4 s while the app is active, on every turn event and as the app comes back: the friend's
    /// inbox cards, a join to carry on, the host's friends on their way, and invitations that crossed.
    func refreshInvitations() async {
        guard signedIn(), appActive() else { return }
        guard !refreshingInbox else { refreshAgain = true; return }
        refreshingInbox = true; defer { refreshingInbox = false }
        repeat { refreshAgain = false; await readInbox() } while refreshAgain
    }

    private func readInbox() async {
        acceptPendingRealTimeInvite()
        let known = outgoing
        do {
            let matches = try await GKTurnBasedMatch.loadMatches()
            var records: [(stored: GKTurnBasedMatch, invite: GameCenterPartyInvitation)] = []
            for stored in matches where stored.status != .ended {
                guard let data = try? await stored.loadMatchData(),
                      let invite = try? JSONDecoder().decode(GameCenterPartyInvitation.self, from: data) else { continue }
                guard invite.kind == GameCenterPartyInvitation.kindV2 else {
                    // an older build's record: cleaned up once it has run out
                    if invite.kind.hasPrefix("motionclub.partyInvite"), invite.expiresAt <= Self.now,
                       invite.host == localID || invite.recipient == localID { await retire(stored) }
                    continue
                }
                if retireLater.remove(stored.matchID) != nil { await retire(stored); continue }
                records.append((stored, invite))
            }
            // Crossed invitations (each friend invited the other): the same one stays on both phones (PartyTieBreak), the other goes.
            // This phone goes into the friend's party when theirs stays, and hosts when its own stays.
            let losers = PartyTieBreak.losers(records.map { ($0.stored.matchID, $0.invite) }, local: localID)
            var crossedFrom = Set<String>()
            for r in records where losers.contains(r.stored.matchID) {
                let id = r.stored.matchID
                if r.invite.host == localID {
                    crossedFrom.insert(r.invite.recipient)
                    let teamID = outgoing[id]?.teamID ?? participant(r.stored, r.invite.recipient)?.player?.teamPlayerID ?? r.invite.recipient
                    outgoing[id] = nil; missingOutgoing[id] = nil; expected[r.invite.recipient] = nil; onOutgoing?(teamID, .crossed)
                } else {
                    cancelGoal("crossed invitations: this phone hosts") { $0.record == id }
                }
                SportsDiagnostics.write("Game Center invite: crossed with \((r.invite.host == localID ? r.invite.recipient : r.invite.host).prefix(8)), \(r.invite.host == localID ? "theirs stays" : "mine stays")")
                await retire(r.stored)
            }
            var cards: [HubInvite] = [], pending: [String: GKTurnBasedMatch] = [:], auto: [HubInvite] = [], seen: Set<String> = []
            for (stored, invite) in records where !losers.contains(stored.matchID) {
                let now = Self.now
                let host = participant(stored, invite.host), friend = participant(stored, invite.recipient)
                let step = GameCenterInviteStep.next(invite, local: localID, myTurn: stored.currentParticipant?.player?.gamePlayerID == localID,
                                                     hostHere: Self.here(host), friendHere: Self.here(friend), now: now)
                if invite.host == localID {
                    seen.insert(stored.matchID)
                    let teamID = friend?.player?.teamPlayerID ?? outgoing[stored.matchID]?.teamID ?? invite.recipient
                    outgoing[stored.matchID] = (teamID, invite.recipient)
                    // they are in (the match connected before this refresh): the invitation is answered
                    if peers.contains(invite.recipient) { answered([invite.recipient]); continue }
                    switch step {
                    case .retire(let ending):
                        outgoing[stored.matchID] = nil; expected[invite.recipient] = nil
                        onOutgoing?(teamID, ending == .expired ? .expired : .declined); await retire(stored)
                    case .go:
                        // they tapped Join: they are looking for this party now. A guest in someone else's party has none to offer.
                        let ready: Bool? = hostAvailable == nil ? true : hostAvailable!()
                        guard ready != nil else {
                            outgoing[stored.matchID] = nil; expected[invite.recipient] = nil; onOutgoing?(teamID, .expired); await retire(stored); continue
                        }
                        expected[invite.recipient] = max(expected[invite.recipient] ?? 0, invite.expiresAt)
                        onOutgoing?(teamID, .joining)
                    default:
                        // still an invitation: the party is open for them (the link waits for them in this phone's group)
                        if leading { expected[invite.recipient] = max(expected[invite.recipient] ?? 0, invite.expiresAt) }
                    }
                    continue
                }
                switch step {
                case .retire: await retire(stored)
                case .card, .resume:
                    guard goal?.record != stored.matchID, let player = host?.player,
                          invitationAllowed?(player.gamePlayerID, player.teamPlayerID) != false else { continue }
                    // already together (the party came back by itself): nothing to join, the record goes
                    if peers.contains(invite.host) { await retire(stored); continue }
                    let card = invite.card(stored.matchID)
                    pending[card.id] = stored; cards.append(card)
                    var automatic = card; automatic.automatic = true
                    if step == .card, crossedFrom.contains(invite.host) { auto.append(automatic) }   // they invited this phone too: in
                    else if step == .resume, !resumed.contains(card.id) {
                        resumed.insert(card.id)
                        // Join tapped a moment ago, and the app closed under it: it carries on. An older one waits for a tap.
                        if JoinMemory.recent(card.id) { auto.append(automatic) }
                    }
                default: break
                }
            }
            // the host's record ended on the friend's side (they said Not now, or joined and tidied up) without passing through here.
            // Missing twice in a row, so a record sent while this refresh was loading (or not listed yet) is not taken for an answer.
            // Missing while the friend's own invitation to this phone is here: the friend's phone settled a crossing, and this phone
            // goes into their party.
            for (id, out) in known where outgoing[id] != nil && !seen.contains(id) {
                missingOutgoing[id, default: 0] += 1
                guard missingOutgoing[id]! >= 2 else { continue }
                outgoing[id] = nil; missingOutgoing[id] = nil; expected[out.gameID] = nil
                if peers.contains(out.gameID) { onOutgoing?(out.teamID, .joined) }
                else if let theirs = cards.first(where: { $0.from.id == out.gameID }) {
                    onOutgoing?(out.teamID, .crossed)
                    if !auto.contains(where: { $0.id == theirs.id }), records.contains(where: { $0.stored.matchID == theirs.lobbyCode && $0.invite.step == .invited }) {
                        var automatic = theirs; automatic.automatic = true; auto.append(automatic)
                    }
                } else { onOutgoing?(out.teamID, .declined) }
            }
            for id in seen { missingOutgoing[id] = nil }
            inbox = pending; onInvitations?(cards.sorted { $0.expiresAt > $1.expiresAt })
            let opened = openedFromNotification
            if let opened, let card = cards.first(where: { $0.id == opened }) { openedFromNotification = nil; onInvitationOpened?(card) }
            for card in auto where card.id != opened { onInvitationOpened?(card) }
            runLink()
        } catch { SportsDiagnostics.write("Game Center invite inbox: \(error.localizedDescription)") }
    }

    func declineStoredInvitation(_ id: String) {
        JoinMemory.forget(id)
        let stored = inbox.removeValue(forKey: id)
        let matchID = String(id.dropFirst(3))
        Task {
            if let stored { await retire(stored) }
            else if let stored = try? await GKTurnBasedMatch.load(withID: matchID) { await retire(stored) }
        }
    }

    /// Retire only this feature's own temporary record, after a player's action or once it has ended.
    private func retire(_ stored: GKTurnBasedMatch) async {
        if stored.status != .ended {
            if stored.participants.first(where: { $0.player?.gamePlayerID == localID })?.status == .invited {
                try? await stored.declineInvite()
            } else if stored.currentParticipant?.player?.gamePlayerID == localID {
                for p in stored.participants { p.matchOutcome = .quit }
                try? await stored.endMatchInTurn(withMatch: stored.matchData ?? Data())
            } else { try? await stored.participantQuitOutOfTurn(with: .quit) }
        }
        try? await stored.remove()
    }
    private func participant(_ stored: GKTurnBasedMatch, _ id: String) -> GKTurnBasedParticipant? {
        stored.participants.first { $0.player?.gamePlayerID == id }
    }
    private static func here(_ p: GKTurnBasedParticipant?) -> Bool { p.map { $0.status != .done && $0.status != .declined } ?? false }
    private static func turnTimeout(_ invite: GameCenterPartyInvitation) -> TimeInterval { max(60, (invite.expiresAt - now) / 1000) }
    private static func isNetwork(_ error: Error) -> Bool {
        if let code = (error as? GKError)?.code, code == .communicationsFailure || code == .connectionTimeout { return true }
        return (error as NSError).domain == NSURLErrorDomain
    }
    /// Apple ended the match's session under the game (iOS 26's GKMatch transport): error 4 is `groupSessionInvalidated`, 1 is
    /// `illegalState` (no channel or no local participant any more). The match will never send again.
    static func sessionGone(_ error: Error) -> Bool {
        let e = error as NSError
        return e.domain.hasSuffix("FastSyncTransportError") && (e.code == 4 || e.code == 1)
    }
    /// Game Center's errors in words a player can act on (never "GameCenterFoundation.FastSyncTransportError error 4").
    static func friendly(_ error: Error, _ fallback: String) -> Error {
        if error is MultiplayerError || error is CancellationError { return error }
        switch (error as? GKError)?.code {
        case .notAuthenticated?: return MultiplayerError.unavailable("Sign in to Game Center first.")
        case .cancelled?: return CancellationError()
        default: return isNetwork(error) ? MultiplayerError.unavailable("No internet right now. Try again.") : MultiplayerError.unavailable(fallback)
        }
    }

    private func register() {
        if signedIn() && !registered {
            GKLocalPlayer.local.register(self); registered = true
            restoreParty()
        }
        guard inboxTimer == nil else { return }
        let timer = Timer(timeInterval: 4, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in self?.linkTick(); await self?.refreshInvitations() }
        }
        RunLoop.main.add(timer, forMode: .common); inboxTimer = timer
    }
    private func request(sport: MultiplayerSport?, count: Int) throws -> GKMatchRequest {
        guard GKLocalPlayer.local.isAuthenticated else { throw MultiplayerError.unavailable("Sign in to Game Center first.") }
        guard capacity >= count, count >= 2 else { throw MultiplayerError.unavailable("Game Center cannot connect that many players on this OS.") }
        let request = GKMatchRequest(); request.minPlayers = 2; request.maxPlayers = count; request.defaultNumberOfPlayers = count
        // Stable, versioned queues; private parties are sport-neutral.
        request.playerGroup = sport == .tennis ? 0x4d500201 : sport == .golf ? 0x4d500202 : sport == .bowling ? 0x4d500203 : 0x4d500200
        return request
    }
    // Quick match remains separate from friends' sport-neutral parties.
    func quickMatch(sport: MultiplayerSport, count: Int = 2) async throws {
        // (a party remembered from before a relaunch, not back yet, gives way to the quick match)
        if party != nil, partyInLobby?() != true, match == nil { disconnect(because: "a quick match instead of the party from before") }
        guard match == nil, party == nil else { throw MultiplayerError.invalidOperation("Already connected to a lobby.") }
        guard !joining else { throw MultiplayerError.invalidOperation("Finish joining your friend first.") }
        let request = try request(sport: sport, count: sport == .tennis ? 2 : count)
        // Programmatic matchmaking works on iOS 17 too. Use a fixed requested group size;
        // partial-fill UI is deliberately deferred rather than pretending a timeout can start it.
        request.minPlayers = request.maxPlayers
        tickets += 1; let token = tickets; quickToken = token
        // (the link waits while a quick match searches: its own search, looking for invited friends, stops first)
        if linkSearch != 0 { stopLinkSearch(); try await Task.sleep(for: .milliseconds(300)) }
        guard token == quickToken else { throw CancellationError() }
        let found: GKMatch
        do { found = try await GKMatchmaker.shared().findMatch(for: request) }
        catch { if token == quickToken { quickToken = 0; runLink() }; throw Self.friendly(error, "Couldn't find a match. Try again.") }
        guard token == quickToken else { drop(GameKitMatchLink(found), "quick match cancelled"); throw CancellationError() }
        quickToken = 0
        attach(GameKitMatchLink(found))
    }
    func findMore(sport: MultiplayerSport) async throws {
        guard let match = (match as? GameKitMatchLink)?.gk, party == nil, peers.count + 1 < capacity else { throw MultiplayerError.full }
        let request = try request(sport: sport, count: 4)
        tickets += 1; let token = tickets; quickToken = token
        defer { if quickToken == token { quickToken = 0 } }
        do { try await GKMatchmaker.shared().addPlayers(to: match, matchRequest: request) }
        catch { throw Self.friendly(error, "Couldn't find more players. Try again.") }
        GKMatchmaker.shared().finishMatchmaking(for: match)
    }
    /// Stops a quick match (or find more) search. Invitations already sent stay out (they wait for the friend's Join).
    func cancelSearch() {
        let searching = quickToken != 0
        quickToken = 0
        if searching { GKMatchmaker.shared().cancel() }
        activeController?.dismiss(animated: true); activeController = nil
        if searching { runLink() }
    }
    private func attach(_ found: GameKitMatchLink) {
        if let previous = match, previous !== found { drop(previous, "replaced by a quick match") }
        match = found; matchIsParty = false; disconnected.removeAll(); found.gk.delegate = self
        found.finish()
        onConnected?(); onPeersChanged?()
    }
    func send(_ data: Data, to ids: [String]?, reliable: Bool) throws {
        guard data.count <= MultiplayerPacket.maximumBytes, let match else {
            throw MultiplayerError.unavailable(party != nil ? "Reconnecting to your party…" : "No Game Center connection.")
        }
        do { try match.send(data, to: ids, reliable: reliable) }
        catch {
            // Apple ended the match under the game: the party meets again; the player never sees Apple's error text
            if Self.sessionGone(error) { matchDied("send failed: \(error.localizedDescription)") }
            throw Self.friendly(error, party != nil ? "Reconnecting to your party…" : "The connection to the other players was lost.")
        }
    }
    func disconnect() { disconnect(because: "the lobby was left (MultiplayerService.leave logs why)") }
    /// Leaving the party on purpose: the others are told (so they do not wait for this phone), and nothing comes back by itself.
    func disconnect(because why: String) {
        if let m = match {
            SportsDiagnostics.write("game center leaves the party match (players=\(m.playerIDs.count)) — \(why)")
            if party != nil, !peers.isEmpty { try? m.send(Self.bye, to: nil, reliable: true) }
            // (a moment for the bye to go out before the match is hung up)
            (m as? GameKitMatchLink)?.gk.delegate = nil
            Task { @MainActor in try? await Task.sleep(for: .milliseconds(400)); m.hangUp() }
        }
        let leavingParty = party != nil || goal != nil || matchIsParty
        match = nil; matchIsParty = false; pendingMatch = nil
        if leavingParty {
            SportsDiagnostics.write("party link: off — \(why)")
            // invitations still out are taken back: nobody comes into a party that is gone (a quick match left keeps them)
            for out in outgoing.values { cancelInvite(out.gameID) }
            party = nil; saveParty(force: true); goal = nil; expected.removeAll(); missingSince.removeAll(); departed.removeAll()
        }
        disconnected.removeAll(); strangers.removeAll(); lostNoticeShown = false
        stopLinkSearch(); cancelSearch()
        onPeersChanged?()
    }
    nonisolated func player(_ player: GKPlayer, receivedTurnEventFor match: GKTurnBasedMatch, didBecomeActive: Bool) {
        let id = "gc:" + match.matchID
        Task { @MainActor [weak self] in
            if didBecomeActive { self?.openedFromNotification = id }
            await self?.refreshInvitations()
        }
    }
    /// The link a GameKit callback is about: the party's match, or one still connecting.
    private func link(for gk: GKMatch) -> PartyMatchLink? {
        [match, pendingMatch].compactMap { $0 }.first { ($0 as? GameKitMatchLink)?.gk === gk }
    }
    nonisolated func match(_ match: GKMatch, didReceive data: Data, fromRemotePlayer player: GKPlayer) {
        let id = player.gamePlayerID, delivery = GameKitDelivery(value: match)
        Task { @MainActor [weak self] in
            guard let self, let link = self.link(for: delivery.value) else { return }
            self.received(data, from: id, on: link)
        }
    }
    nonisolated func match(_ match: GKMatch, player: GKPlayer, didChange state: GKPlayerConnectionState) {
        let delivery = GameKitDelivery(value: match), id = player.gamePlayerID, connected = state == .connected
        Task { @MainActor [weak self] in
            guard let self, let link = self.link(for: delivery.value) else { return }
            self.playerChanged(id, connected: connected, on: link)
        }
    }
    /// A packet on a match: only the party's match feeds the lobby; the link's own packets stop here.
    func received(_ data: Data, from id: String, on link: PartyMatchLink) {
        guard match === link else { return }
        lastHeard[id] = Date()
        if data.starts(with: Self.linkMagic) {
            if data == Self.bye { saidBye(id) }
            return
        }
        guard !strangers.contains(id) else { return }
        onData?(data, id)
    }
    /// Someone left the party on purpose: nobody waits for them. Their leader gone, the lobby hands the party over (MultiplayerService).
    private func saidBye(_ id: String) {
        guard !departed.contains(id) else { return }
        SportsDiagnostics.write("party link: \(id.suffix(6)) left the party")
        departed.insert(id); disconnected.insert(id); missingSince[id] = nil; expected[id] = nil
        if var p = party {
            p.members.removeAll { $0 == id }
            party = p.members.count > 1 ? p : nil
            saveParty(force: true)
        }
        // everyone has gone: the party's match goes too (the next friend meets this phone in a new one)
        if matchIsParty, let m = match, peers.isEmpty, party == nil { drop(m, "the party is over: everyone left it"); match = nil }
        onPeersChanged?()
        runLink()
    }
    /// A player connected to or dropped from a match. Only the party's match changes the lobby (one still connecting is watched by
    /// attachParty through its player list).
    func playerChanged(_ id: String, connected: Bool, on link: PartyMatchLink) {
        SportsDiagnostics.write("game center player \(id.prefix(8)) \(connected ? "connected" : "disconnected") (players=\(link.playerIDs.count) expected=\(link.expectedPlayerCount)\(match === link ? "" : ", match still connecting"))")
        guard match === link else { return }
        if connected {
            if party != nil, !allowed(id) {
                // Game Center brought someone into this party's group who is not in it: they are told to go and never heard
                strangers.insert(id); try? link.send(Self.bye, to: [id], reliable: true); return
            }
            disconnected.remove(id); departed.remove(id); missingSince[id] = nil; lastHeard[id] = Date()
            if var p = party, !p.members.contains(id) { p.members.append(id); p.members.sort(); party = p; saveParty(force: true) }
            expected[id] = nil; answered([id])
        } else {
            disconnected.insert(id)
            if let p = party, p.members.contains(id), !departed.contains(id) { missingSince[id] = missingSince[id] ?? Date().timeIntervalSince1970 }
            // nobody left in a party's match: it is gone (Apple ends it anyway); the party meets again in a new one
            if party != nil, peers.isEmpty { matchDied("everyone else left the match"); return }
        }
        onPeersChanged?()
        runLink()
    }
    #if DEBUG
    /// Tests: a found match handed to the real attach (as the link's search would), for `leader`'s party.
    func debugAttachParty(_ link: PartyMatchLink, leader: String, need: Set<String>) async throws {
        if leader != localID, party?.leader != leader { goal = JoinGoal(leader: leader, name: "Host", players: 2, until: .distantFuture, record: nil, knock: nil) }
        if leader == localID { for id in need { expected[id] = Self.now + GameCenterPartyInvitation.lifetime } }
        try await attachParty(link, need: need)
    }
    /// Tests: an invitation out to `id` (as `invite` leaves it), and a Join on `leader`'s party (as a card's Join starts it).
    func debugExpect(_ id: String) { expected[id] = Self.now + GameCenterPartyInvitation.lifetime; runLink() }
    func debugJoin(_ leader: String, name: String = "Host", players: Int = 2, seconds: Double = 60) async throws {
        try await joinParty(leader: leader, name: name, players: players, seconds: seconds)
    }
    /// Tests: Apple ended this phone's match (error 4), and the party remembered from before a relaunch.
    func debugMatchFailed() { matchDied("test: Apple ended the match (error 4)") }
    func debugRestore() { restoreParty() }
    func debugTick() { linkTick() }
    #endif
    /// Apple says the match failed. For the party's match that is Apple's FastSync error 4 (groupSessionInvalidated) and the like: the
    /// match is gone, the party meets again. A match still connecting is the link's to give up.
    nonisolated func match(_ match: GKMatch, didFailWithError error: Error?) {
        let delivery = GameKitDelivery(value: match), words = error?.localizedDescription ?? "no error"
        Task { @MainActor [weak self] in
            guard let self else { return }
            let ours = self.link(for: delivery.value)
            SportsDiagnostics.write("game center match failed: \(words) (ours: \(ours != nil))")
            guard let ours, ours === self.match else { return }
            self.matchDied("Apple ended it: \(words)")
        }
    }
    /// The link brings players back itself (both phones meet again in the leader's group); Apple's reinvite would make a second
    /// path into the same party.
    nonisolated func match(_ match: GKMatch, shouldReinviteDisconnectedPlayer player: GKPlayer) -> Bool { false }
    /// Apple's own real-time invitation: never dropped. Accepted during a match it waits, and joins once this phone is in the Plaza.
    nonisolated func player(_ player: GKPlayer, didAccept invite: GKInvite) {
        let delivery = GameKitDelivery(value: invite)
        Task { @MainActor [weak self] in self?.pendingRealTimeInvite = delivery.value; self?.acceptPendingRealTimeInvite() }
    }
    private func acceptPendingRealTimeInvite() {
        guard let invite = pendingRealTimeInvite, joinAvailable?() != false, !realTimeJoining else { return }
        let sender = invite.sender.gamePlayerID, name = invite.sender.displayName
        if peers.contains(sender) { pendingRealTimeInvite = nil; return }
        // (not the moment: it stays pending, and the next refresh tries again)
        guard canAcceptParty?(false) != false else { return }
        pendingRealTimeInvite = nil
        realTimeJoining = true; stopLinkSearch()
        let delivery = GameKitDelivery(value: invite)
        Task { @MainActor [weak self] in
            guard let self else { return }
            defer { self.realTimeJoining = false; self.runLink() }
            do {
                self.goal = JoinGoal(leader: sender, name: name, players: 2, until: Date().addingTimeInterval(60), record: nil, knock: nil)
                let found = GameKitMatchLink(try await GKMatchmaker.shared().match(for: delivery.value))
                guard self.goal?.leader == sender else { self.drop(found, "real-time invite superseded after its search"); return }
                try await self.attachParty(found, need: [sender])
            } catch {
                if self.goal?.leader == sender { self.goal = nil }
                self.onError?(MultiplayerError.unavailable("Couldn't join \(name). Ask them to invite you again."))
            }
        }
    }
    nonisolated func matchmakerViewControllerWasCancelled(_ viewController: GKMatchmakerViewController) {
        Task { @MainActor [weak self] in guard self?.activeController === viewController else { return }; self?.cancelSearch() }
    }
    nonisolated func matchmakerViewController(_ viewController: GKMatchmakerViewController, didFailWithError error: Error) {
        Task { @MainActor [weak self] in
            guard self?.activeController === viewController else { return }
            viewController.dismiss(animated: true); self?.activeController = nil
            self?.onError?(Self.friendly(error, "Couldn't find a match. Try again."))
        }
    }
    nonisolated func matchmakerViewController(_ viewController: GKMatchmakerViewController, didFind match: GKMatch) {
        let delivery = GameKitDelivery(value: match)
        Task { @MainActor [weak self] in
            guard let self, self.activeController === viewController else { delivery.value.disconnect(); return }
            viewController.dismiss(animated: true); self.activeController = nil; self.attach(GameKitMatchLink(delivery.value))
        }
    }
}

/// Joins the player said yes to, by card id, kept across a relaunch. One tapped a moment ago carries on by itself after the app closed
/// under it; an older one waits for a tap (before 2026-10-26 any join said yes to resumed by itself after a relaunch, with no tap,
/// even long after and into a party the phone had left).
@MainActor enum JoinMemory {
    static let key = "party.joinTapped.v1"
    /// Seconds a Join stays fresh enough to carry on with no tap.
    static let window: Double = 120
    static var defaults = UserDefaults.standard
    static var now: () -> Double = { Date().timeIntervalSince1970 }
    private static var all: [String: Double] {
        get { defaults.dictionary(forKey: key) as? [String: Double] ?? [:] }
        set { defaults.set(newValue.filter { now() - $0.value < window }, forKey: key) }
    }
    static func tapped(_ id: String) { var a = all; a[id] = now(); all = a }
    static func recent(_ id: String) -> Bool { all[id].map { now() - $0 < window } ?? false }
    static func forget(_ id: String) { var a = all; a[id] = nil; all = a }
}
