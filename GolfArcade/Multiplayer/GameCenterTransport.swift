@preconcurrency import GameKit
import UIKit

private struct GameKitDelivery<T>: @unchecked Sendable { let value: T }

/// Game Center stores the invitation; the real-time match still carries the party.
/// A tagged turn-based record is the readable inbox and the handshake, without a server of our own. It passes between the two phones
/// a turn at a time, so neither phone sits in matchmaking until both are ready:
/// `invited` (host → friend: the card with Join) · `accepted` (friend → host: they tapped Join) · `go` (host → friend: both start the
/// private playerGroup match now). A connection that fails goes round again (accepted → go) until the invitation runs out.
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
    /// Everyone in the party once the friend is in (rewritten at each go: the party may have changed since the invitation).
    var players: [String]
    var expiresAt: Double
    var step = Step.invited
    /// Counts the go's: the friend connects once per go.
    var round = 0
    /// The leader inviting back a member whose phone dropped: that phone accepts it by itself.
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

/// What one phone does next with one stored invitation, from what it can see of it. Pure, so the handshake is tested without
/// Game Center.
enum GameCenterInviteStep: Equatable {
    /// Nothing for this phone now (the other phone has the turn).
    case wait
    /// Friend: a card in the inbox, with Join.
    case card
    /// Friend: tapped Join before (the app was closed, or the connection failed): carry on joining.
    case resume
    /// Host: the friend tapped Join and this phone has the turn: say go and start the private match.
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

/// The real-time match a party rides on, as the transport needs it: a GKMatch in the app, an in-memory pair in tests
/// (PartyJoinHarnessTests), so two phones' join can be replayed in-process with every event ordering.
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

/// Game Center connection behind the in-app friends list. Only authentication may require an Apple controller.
@MainActor
final class GameCenterTransport: NSObject, MultiplayerTransport, GKMatchDelegate, GKLocalPlayerListener, GKMatchmakerViewControllerDelegate {
    #if DEBUG
    /// Tests: this phone's gamePlayerID (two phones in one process).
    var localIDOverride: String?
    var localID: String { localIDOverride ?? GKLocalPlayer.local.gamePlayerID }
    #else
    var localID: String { GKLocalPlayer.local.gamePlayerID }
    #endif
    var peers: [String] { match?.playerIDs.filter { !disconnected.contains($0) } ?? [] }
    var onData: ((Data, String) -> Void)?
    var onPeersChanged: (() -> Void)?
    var onError: ((Error) -> Void)?
    var onConnected: (() -> Void)?
    private(set) var match: PartyMatchLink?
    /// A party match found but still connecting (attachParty): `match` stays the party's until this one is in.
    private var pendingMatch: PartyMatchLink?
    private var handshakeName: String { handshakes.active.map { "handshake \($0.kind) #\($0.token)" } ?? "no handshake" }
    /// Every match this phone hangs up says why in SportsDiagnostics.log.
    private func drop(_ m: PartyMatchLink, _ why: String) {
        SportsDiagnostics.write("game center hangs up a match (players=\(m.playerIDs.count) expected=\(m.expectedPlayerCount)) — \(why) [\(handshakeName)]")
        m.hangUp()
    }
    private func drop(_ m: GKMatch, _ why: String) { drop(GameKitMatchLink(m), why) }
    /// One party handshake at a time on this phone (PartyJoinCoordinator). Its tokens also own the GKMatchmaker searches.
    let handshakes = PartyJoinCoordinator()
    /// The quick match (or find more) search's token; 0 when none.
    private var quickToken = 0
    private var registered = false
    private var disconnected: Set<String> = []
    private var activeController: GKMatchmakerViewController?
    /// The GKMatchmaker search running now, by its owner's token. GKMatchmaker.cancel() stops every search, and a cancel sent just
    /// before a new search also cancels that search (2026-10-25 phone log: "join attempt 1 failed: … canceled"). Since 2026-10-26 a
    /// handshake (or a timeout) only ever cancels its own search, and only while it runs: a let-in no longer kills a bring-in.
    private var searchOwner: Int?
    private func matchmake<T>(_ owner: Int, _ work: () async throws -> T) async throws -> T {
        searchOwner = owner; defer { if searchOwner == owner { searchOwner = nil } }
        return try await work()
    }
    private func cancelMatchmaking(_ owner: Int) { if owner != 0, searchOwner == owner { searchOwner = nil; GKMatchmaker.shared().cancel() } }
    /// Handshakes whose search was given up by its deadline (it then fails with words, never as a silent cancel).
    private var timedOut: Set<Int> = []
    /// Cancels the handshake's search after `seconds`, if it is still running then.
    private func deadline(_ token: Int, seconds: Double) -> Task<Void, Never> {
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(seconds))
            guard !Task.isCancelled, let self, self.handshakes.isCurrent(token) else { return }
            self.timedOut.insert(token); self.cancelMatchmaking(token)
        }
    }
    /// A search that failed: a deadline's says so in words (it used to come back as a cancel, which callers took for "stop quietly").
    private func searchFailed(_ token: Int, _ error: Error, _ words: String) -> Error {
        timedOut.remove(token) != nil ? MultiplayerError.unavailable(words) : Self.friendly(error, words)
    }
    override init() { super.init(); register() }
    var capacity: Int { min(4, GKMatchRequest.maxPlayersAllowedForMatch(of: .peerToPeer)) }

    private var authenticationWaiters: [CheckedContinuation<Void, Error>] = []
    private var authenticationPresenter: ((UIViewController) -> Void)?
    private var authenticationController: UIViewController?
    var onAuthenticationController: ((UIViewController) -> Void)?
    var onAuthenticationChanged: (() -> Void)?
    var onPartyConnected: ((String) -> Void)?
    /// This phone may go into a friend's party now (the Plaza: not a match, a load, onboarding or the background). No side effects.
    var joinAvailable: (() -> Bool)?
    /// Right before connecting to a friend's party: leave whatever party or search this phone is in. False: not now after all.
    /// `automatic` (a rejoin, a resumed or crossed join): never leave a party with friends connected for it.
    var canAcceptParty: ((_ automatic: Bool) -> Bool)?
    /// Host: true when a friend who tapped Join can be brought in now; false: later (a match is on); nil: never (this phone is a
    /// guest in someone else's party now).
    var hostAvailable: (() -> Bool?)?
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
    /// phones never connected, round after round.
    enum Outgoing: Equatable { case joining, waiting, joined, declined, expired, full, crossed, failed }
    enum JoinStage: Equatable { case waitingForHost, connecting }
    private var openedFromNotification: String?
    private var inbox: [String: GKTurnBasedMatch] = [:]
    private var inboxTimer: Timer?
    private var refreshingInbox = false
    /// Host: invitations out, by record id: the friend's ids. Rebuilt from Game Center on every refresh (it survives a relaunch).
    private var outgoing: [String: (teamID: String, gameID: String)] = [:]
    /// Host: the record whose friend this phone is matching with now (one private search at a time).
    private var hostMatching: String?
    private var missingOutgoing: [String: Int] = [:]
    /// Friend: the record being joined now, whether it is connecting, and the records already resumed in this run.
    private var joiningRecord: String?
    private var resumed: Set<String> = []
    /// Records a join gave up on while they could not be read: retired as soon as the inbox lists them.
    private var retireLater: Set<String> = []
    /// A turn event while a refresh was running: read the inbox again right after it (it used to wait for the next 4 s poll).
    private var refreshAgain = false
    /// A turn event since the joiner's last read: its wait ends now (the host's go arrives as one).
    private var kicked = false
    /// An Apple real-time invitation accepted while a match was on: joined once this phone is back in the Plaza.
    private var pendingRealTimeInvite: GKInvite?
    private var partyGroup: UInt32?
    private var allowedPartyPlayers: Set<String>?
    func allowPartyPlayer(_ id: String) { allowedPartyPlayers?.insert(id) }
    /// Taken out of the party: no way back in without a new invite.
    func disallowPartyPlayer(_ id: String) { allowedPartyPlayers?.remove(id); cancelInvite(id) }
    /// Everyone this phone has been in a party with this run, so a member who dropped can be invited back.
    private var knownPlayers: [String: GKPlayer] = [:]
    func reinvite(_ gameID: String) async throws {
        guard let player = knownPlayers[gameID] else { throw MultiplayerError.unavailable("That player is not known here.") }
        try await invite(player, rejoin: true)
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

    // MARK: invitations you send

    /// Sends the stored invitation and returns: nothing waits in matchmaking. The friend's Join comes back as the record's next turn,
    /// and `refreshInvitations` brings them in (several friends can be invited at once).
    func invite(_ player: GKPlayer, rejoin: Bool = false) async throws {
        guard !outgoing.values.contains(where: { $0.gameID == player.gamePlayerID }) else { return }
        guard peers.count + 2 <= capacity else { throw MultiplayerError.full }
        if !rejoin { freshGroupIfStale("a new invitation") }
        let group = partyGroup ?? UInt32.random(in: 0x60000000..<0x70000000)
        partyGroup = group
        let members = Array(Set([localID, player.gamePlayerID] + peers)).sorted()
        var invitation = GameCenterPartyInvitation(host: localID, recipient: player.gamePlayerID,
            name: GKLocalPlayer.local.displayName, group: group, players: members,
            expiresAt: Self.now + GameCenterPartyInvitation.lifetime)
        invitation.rejoin = rejoin ? true : nil
        let storedRequest = try request(sport: nil, count: 2)
        storedRequest.playerGroup = Int(group); storedRequest.recipients = [player]
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
        allowedPartyPlayers?.insert(player.gamePlayerID)
        onInvitationSent?(player.teamPlayerID, stored.matchID, members.count)
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
        for (id, out) in outgoing where out.gameID == gameID {
            outgoing[id] = nil
            Task { if let stored = try? await GKTurnBasedMatch.load(withID: id) { await retire(stored) } }
        }
    }

    /// Rounds of go before an invitation is given up on both phones (the friend's phone tries as many connections).
    static let maxRounds = 4

    /// Host: the friend tapped Join and this phone is free: say go (with the party as it is now) and match with them.
    private func bringIn(_ stored: GKTurnBasedMatch, _ invitation: GameCenterPartyInvitation, teamID: String) {
        // (another handshake is running: the record still says accepted, and the next refresh tries again)
        guard let token = handshakes.begin(.hostInvite(stored.matchID), cancel: { [weak self] in self?.cancelMatchmaking($0) }) else {
            onOutgoing?(teamID, .joining); return
        }
        hostMatching = stored.matchID
        Task { @MainActor [weak self] in
            guard let self else { return }
            defer {
                self.handshakes.end(token); self.timedOut.remove(token)
                if self.hostMatching == stored.matchID { self.hostMatching = nil }
            }
            let members = Array(Set([self.localID, invitation.recipient] + self.peers)).sorted()
            guard members.count <= self.capacity, let friend = self.participant(stored, invitation.recipient) else {
                self.outgoing[stored.matchID] = nil; self.onOutgoing?(teamID, .full); await self.retire(stored); return
            }
            self.onOutgoing?(teamID, .joining)
            var go = invitation; go.step = .go; go.round += 1; go.players = members
            do { try await stored.endTurn(withNextParticipants: [friend], turnTimeout: Self.turnTimeout(go), match: JSONEncoder().encode(go)) }
            catch { self.onOutgoing?(teamID, .waiting); return }   // (the record still says accepted: the next refresh tries again)
            // (a Join the player tapped meanwhile wins: no search starts for a handshake that is over)
            guard self.handshakes.isCurrent(token) else { self.onOutgoing?(teamID, .waiting); return }
            self.allowedPartyPlayers = (self.allowedPartyPlayers ?? Set([self.localID] + self.peers)).union([invitation.recipient])
            let timeout = self.deadline(token, seconds: 60)
            defer { timeout.cancel() }
            do {
                let request = try self.privateRequest(group: invitation.group, count: members.count)
                if let match = self.liveMatch(for: "bringing in a friend") {
                    guard let gk = (match as? GameKitMatchLink)?.gk else { throw MultiplayerError.unavailable("No Game Center match to add to.") }
                    try await self.matchmake(token) { try await GKMatchmaker.shared().addPlayers(to: gk, matchRequest: request) }
                    try await self.waitForPlayers(match, [invitation.recipient])
                    match.finish()
                    self.onPeersChanged?()
                } else {
                    let found = GameKitMatchLink(try await self.matchmake(token) { try await GKMatchmaker.shared().findMatch(for: request) })
                    guard self.handshakes.isCurrent(token) else { self.drop(found, "bring-in superseded after its search (token \(token))"); self.onOutgoing?(teamID, .waiting); return }
                    try await self.attachParty(found, host: self.localID, expecting: [invitation.recipient])
                }
                self.outgoing[stored.matchID] = nil
                self.onOutgoing?(teamID, .joined)
                await self.retire(stored)
            } catch {
                SportsDiagnostics.write("Game Center invite: host match failed (round \(go.round)): \(error.localizedDescription)")
                if go.round >= Self.maxRounds {
                    // never a record left at go for nobody: the friend's phone gave up after as many rounds
                    self.outgoing[stored.matchID] = nil; self.onOutgoing?(teamID, .failed); await self.retire(stored)
                } else {
                    // the friend's phone says Join once more and this goes round again
                    self.onOutgoing?(teamID, .waiting)
                }
            }
        }
    }

    // MARK: CloudKit knocks (ClubCloud): the same private match, met when the host's phone answers a knock

    /// The private group this phone's party meets in, made now if it has none.
    func hostGroup() -> UInt32 {
        // (presence asks every few seconds: a party emptied a moment ago keeps its group while Apple's reconnect and the rejoin run)
        if Date().timeIntervalSince(emptiedAt ?? .distantFuture) > Self.groupKeptSeconds { freshGroupIfStale("drop-in") }
        if let g = partyGroup { return g }
        let g = UInt32.random(in: 0x60000000..<0x70000000); partyGroup = g; return g
    }
    /// Host: let in someone who knocked (a friend dropping in, or someone with the code).
    func letIn(_ gameID: String, group: UInt32, players: Int) async throws {
        guard let token = handshakes.begin(.hostKnock(gameID), cancel: { [weak self] in self?.cancelMatchmaking($0) }) else {
            throw MultiplayerError.unavailable("Busy bringing someone else in. Try again.")
        }
        defer { handshakes.end(token); timedOut.remove(token) }
        allowedPartyPlayers = (allowedPartyPlayers ?? Set([localID] + peers)).union([gameID])
        let timeout = deadline(token, seconds: 60)
        defer { timeout.cancel() }
        let request = try privateRequest(group: group, count: players)
        do {
            if let match = liveMatch(for: "letting in a knock") {
                guard let gk = (match as? GameKitMatchLink)?.gk else { throw MultiplayerError.unavailable("No Game Center match to add to.") }
                try await matchmake(token) { try await GKMatchmaker.shared().addPlayers(to: gk, matchRequest: request) }
                try await waitForPlayers(match, [gameID])
                match.finish()
                onPeersChanged?()
            } else {
                let found = GameKitMatchLink(try await matchmake(token) { try await GKMatchmaker.shared().findMatch(for: request) })
                guard handshakes.isCurrent(token) else { drop(found, "let-in superseded after its search (token \(token))"); throw CancellationError() }
                try await attachParty(found, host: localID, expecting: [gameID])
            }
        } catch { throw searchFailed(token, error, "Couldn't connect. Try again.") }
    }
    /// Joiner, CloudKit: the knock to `host` begins here (ClubCloud.join holds it until it is in or gives up). Nil: not now.
    func beginKnockJoin(host: String, onCancel: @escaping () -> Void) -> Int? {
        handshakes.begin(.joinKnock(host), cancel: { [weak self] token in self?.cancelMatchmaking(token); onCancel() })
    }
    /// Joiner: into the host's party group after its go.
    func joinGroup(host: String, group: UInt32, players: Int) async throws {
        // the knock that led here holds the handshake; a connect on its own takes one
        let token: Int, own: Bool
        if let active = handshakes.active, active.kind == .joinKnock(host) { token = active.token; own = false }
        else {
            guard let t = handshakes.begin(.joinKnock(host), cancel: { [weak self] in self?.cancelMatchmaking($0) }) else { throw CancellationError() }
            token = t; own = true
        }
        defer { if own { handshakes.end(token) }; timedOut.remove(token) }
        let request = try privateRequest(group: group, count: players)
        let timeout = deadline(token, seconds: 45)
        defer { timeout.cancel() }
        let found: GameKitMatchLink
        do { found = GameKitMatchLink(try await matchmake(token) { try await GKMatchmaker.shared().findMatch(for: request) }) }
        catch { throw searchFailed(token, error, "Couldn't connect. Try again.") }
        guard handshakes.isCurrent(token) else { drop(found, "knock join superseded after its search (token \(token))"); throw CancellationError() }
        // (the host checks who comes in; the group is this phone's only once it is in)
        try await attachParty(found, host: host, expecting: [host], guest: Guest(allowed: nil, group: group))
    }

    /// Whether `group` is still the party's (someone is connected in it now). Pure, for tests.
    static func groupIsStale(hadPlayers: Bool, connectedNow: Int) -> Bool { hadPlayers && connectedNow == 0 }
    /// The party's group has had friends in it and all of them have gone: the next party gets a new group, and the empty match goes.
    /// (10-27: after a party dropped, both phones kept its group and its empty match. The next invites, both ways, used that same
    /// group, so both phones brought each other in as HOSTS into one match, each said "joined your party", nobody's lobby was
    /// taken, and the match fell apart a second later, every time.)
    private func freshGroupIfStale(_ why: String) {
        guard Self.groupIsStale(hadPlayers: groupHadPlayers, connectedNow: peers.count) else { return }
        SportsDiagnostics.write("party group \(String(partyGroup ?? 0, radix: 16)) is over (nobody left in it): a new one for \(why)")
        if let stale = match { drop(stale, "the party's match is empty: a new party starts"); match = nil }
        partyGroup = nil; groupHadPlayers = false; emptiedAt = nil
    }
    /// Somebody has been connected in this party's group (set once a party match connects), and when the last one went.
    private var groupHadPlayers = false
    private var emptiedAt: Date?
    /// Seconds an emptied party keeps its group for drop-ins (Apple's reconnect, then the 12 s rejoin, come first).
    static var groupKeptSeconds = 20.0
    /// The party's match, to add a friend to: only while somebody is connected in it. An empty one (everyone dropped) is hung up, and
    /// the friend is met in a new match.
    private func liveMatch(for why: String) -> PartyMatchLink? {
        guard let m = match else { return nil }
        if !peers.isEmpty { return m }
        drop(m, "nobody left in the party's match: \(why) meets in a new one"); match = nil
        return nil
    }
    private func privateRequest(group: UInt32, count: Int) throws -> GKMatchRequest {
        let r = try request(sport: nil, count: count)
        r.playerGroup = Int(group); r.minPlayers = count; r.maxPlayers = count
        return r
    }

    // MARK: the inbox (both sides)

    /// Apple's stored records, polled every 4 s while the app is active, on every turn event and as the app comes back: the friend's
    /// inbox cards, a join to carry on, the host's friends who tapped Join, and invitations that crossed.
    func refreshInvitations() async {
        guard GKLocalPlayer.local.isAuthenticated, UIApplication.shared.applicationState == .active else { return }
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
                    outgoing[id] = nil; missingOutgoing[id] = nil; onOutgoing?(teamID, .crossed)
                } else if id == joiningRecord {
                    handshakes.cancel { $0 == .joinInvite(id) }   // (this phone hosts instead: its own invitation stays)
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
                    guard stored.matchID != hostMatching else { continue }
                    let teamID = friend?.player?.teamPlayerID ?? outgoing[stored.matchID]?.teamID ?? invite.recipient
                    outgoing[stored.matchID] = (teamID, invite.recipient)
                    switch step {
                    case .retire(let ending):
                        outgoing[stored.matchID] = nil; onOutgoing?(teamID, ending == .expired ? .expired : .declined); await retire(stored)
                    case .go:
                        let ready: Bool? = hostAvailable == nil ? true : hostAvailable!()
                        switch ready {
                        case true?: if hostMatching == nil { bringIn(stored, invite, teamID: teamID) }
                        case false?: onOutgoing?(teamID, .joining)
                        case nil: outgoing[stored.matchID] = nil; onOutgoing?(teamID, .expired); await retire(stored)
                        }
                    default: break
                    }
                    continue
                }
                switch step {
                case .retire: await retire(stored)
                case .card, .resume:
                    guard stored.matchID != joiningRecord, let player = host?.player,
                          invitationAllowed?(player.gamePlayerID, player.teamPlayerID) != false else { continue }
                    // already together (a rejoin after the party came back by itself): nothing to join, the record goes
                    if peers.contains(invite.host) { await retire(stored); continue }
                    let card = invite.card(stored.matchID)
                    pending[card.id] = stored; cards.append(card)
                    var automatic = card; automatic.automatic = true
                    if step == .card, crossedFrom.contains(invite.host) { auto.append(automatic) }   // they invited this phone too: in
                    else if step == .resume, !resumed.contains(card.id) {
                        resumed.insert(card.id)
                        // Join tapped a moment ago, and the app closed under it: it carries on. An older one waits for a tap (it used to
                        // join by itself after any relaunch, even into a party this phone had long left).
                        if JoinMemory.recent(card.id) { auto.append(automatic) }
                    }
                default: break
                }
            }
            // the host's record ended on the friend's side (they said Not now) without passing through here. Missing twice in a row,
            // so a record sent while this refresh was loading (or not listed yet) is not taken for an answer. Missing while the friend's
            // own invitation to this phone is here: the friend's phone settled a crossing, and this phone goes into their party.
            for (id, out) in known where outgoing[id] != nil && !seen.contains(id) && id != hostMatching {
                missingOutgoing[id, default: 0] += 1
                guard missingOutgoing[id]! >= 2 else { continue }
                outgoing[id] = nil; missingOutgoing[id] = nil
                if let theirs = cards.first(where: { $0.from.id == out.gameID }) {
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
        } catch { SportsDiagnostics.write("Game Center invite inbox: \(error.localizedDescription)") }
    }

    // MARK: joining a friend's party

    /// A cold start from an invite's notification: Game Center may still be signing in. Waits for it (it used to fail at once).
    func untilSignedIn(seconds: Double = 30) async throws {
        let end = Date().addingTimeInterval(seconds)
        while !GKLocalPlayer.local.isAuthenticated {
            guard Date() < end else { throw MultiplayerError.unavailable("Sign in to Game Center to join your friend.") }
            try await Task.sleep(for: .milliseconds(250))
        }
        register()
    }

    /// The friend tapped Join (and is in the Plaza): say yes, then wait for the host's go and connect. Keeps trying, round after round,
    /// until it is in, the invitation runs out, the host leaves, or the player cancels. Throws only words a player can act on. Every
    /// way out but success and a cancel retires the record, so nothing is left to join by itself later.
    func acceptStoredInvitation(_ card: HubInvite) async throws {
        let id = card.lobbyCode, who = card.from.name, automatic = card.automatic == true
        // already together (the party came back by itself, or an old notification): nothing to join
        if peers.contains(card.from.id) {
            if let stored = try? await GKTurnBasedMatch.load(withID: id) { await retire(stored) }
            return
        }
        guard let token = handshakes.begin(.joinInvite(id), origin: automatic ? .automatic : .player,
                                           cancel: { [weak self] in self?.cancelMatchmaking($0) }) else { throw CancellationError() }
        joiningRecord = id; resumed.insert(card.id); inbox[card.id] = nil
        JoinMemory.tapped(card.id)
        defer { handshakes.end(token); timedOut.remove(token); if joiningRecord == id { joiningRecord = nil } }
        var last: GKTurnBasedMatch?
        func giveUp(_ error: Error) async -> Error {
            JoinMemory.forget(card.id)
            if let last { await retire(last) } else { retireLater.insert(id) }
            return error
        }
        var tried = -1, failures = 0, loadFailures = 0, acceptFailures = 0
        var goSeen: (round: Int, at: Double)?
        while true {
            guard handshakes.isCurrent(token) else { throw CancellationError() }
            // a rejoin is not needed once this phone is in a party with friends again (Apple reconnected it): it never leaves one
            if automatic, handshakes.inConnectedParty() { throw await giveUp(CancellationError()) }
            let stored: GKTurnBasedMatch, invite: GameCenterPartyInvitation
            do {
                stored = try await GKTurnBasedMatch.load(withID: id)
                invite = try JSONDecoder().decode(GameCenterPartyInvitation.self, from: try await stored.loadMatchData() ?? Data())
                loadFailures = 0; last = stored
            } catch {
                // no connection for a moment: try again for a while; Game Center cannot find or read the record: it has ended
                let network = Self.isNetwork(error)
                loadFailures += 1
                if loadFailures >= (network ? 8 : 3) { throw await giveUp(network ? Self.noInternet(who) : Self.ended(who)) }
                try await nap(2); continue
            }
            guard handshakes.isCurrent(token) else { throw CancellationError() }
            let now = Self.now
            guard stored.status != .ended, invite.kind == GameCenterPartyInvitation.kindV2, invite.recipient == localID, invite.expiresAt > now else { throw await giveUp(Self.ended(who)) }
            guard let host = participant(stored, invite.host), Self.here(host), let hostPlayer = host.player,
                  invitationAllowed?(hostPlayer.gamePlayerID, hostPlayer.teamPlayerID) != false else {
                throw await giveUp(MultiplayerError.unavailable("\(who) left the game. Ask them to invite you again."))
            }
            if participant(stored, localID)?.status == .invited {
                do { _ = try await stored.acceptInvite() }
                catch {
                    acceptFailures += 1
                    if acceptFailures >= 8 { throw await giveUp(Self.isNetwork(error) ? Self.noInternet(who) : Self.ended(who)) }
                    try await nap(2)
                }
                continue   // (read the record again: accepting it changes it)
            }
            let myTurn = stored.currentParticipant?.player?.gamePlayerID == localID
            if invite.step == .go, goSeen?.round != invite.round { goSeen = (invite.round, now) }
            // a go that waited while this phone was busy is stale: the host stopped matching after a minute, so ask for a fresh one
            let staleGo = invite.step == .go && now - (goSeen?.at ?? now) > 40_000
            if myTurn && (invite.step == .invited || (invite.step == .go && (invite.round <= tried || staleGo))) {
                if joinAvailable?() != false {
                    // Join (again): the turn goes to the host, whose phone says go as soon as it is free. Game Center's turn notification
                    // tells the host's phone, even with the game closed.
                    var yes = invite; yes.step = .accepted
                    stored.setLocalizableMessageWithKey("PARTY_READY", arguments: [GKLocalPlayer.local.displayName])
                    try? await stored.endTurn(withNextParticipants: [host], turnTimeout: Self.turnTimeout(yes), match: JSONEncoder().encode(yes))
                    tried = max(tried, invite.round)
                }
                onJoinStage?(.waitingForHost)
            } else if myTurn && invite.step == .go {
                if joinAvailable?() != false, canAcceptParty?(automatic) != false {
                    tried = invite.round; onJoinStage?(.connecting)
                    do {
                        try await connect(invite, token)
                        JoinMemory.forget(card.id)
                        await retire(stored)
                        return
                    } catch {
                        guard handshakes.isCurrent(token) else { throw CancellationError() }
                        failures += 1
                        SportsDiagnostics.write("Game Center invite: join attempt \(failures) failed: \(error.localizedDescription)")
                        if failures >= Self.maxRounds { throw await giveUp(MultiplayerError.unavailable("Couldn't connect to \(who). Check the internet on both phones, then tap Join again.")) }
                        continue   // (round again: the record now says go with a round already tried, so Join goes back to the host)
                    }
                }
            } else {
                onJoinStage?(.waitingForHost)
            }
            try await nap(2)
        }
    }
    /// The joiner's wait between reads: `seconds`, or less when a turn event says the record changed (the host's go).
    private func nap(_ seconds: Double) async throws {
        kicked = false
        let end = Date().addingTimeInterval(seconds)
        while !kicked, Date() < end { try await Task.sleep(for: .milliseconds(100)) }
    }

    private func connect(_ invite: GameCenterPartyInvitation, _ token: Int) async throws {
        let request = try privateRequest(group: invite.group, count: invite.players.count)
        let timeout = deadline(token, seconds: 45)
        defer { timeout.cancel() }
        let found: GameKitMatchLink
        do { found = GameKitMatchLink(try await matchmake(token) { try await GKMatchmaker.shared().findMatch(for: request) }) }
        catch { throw searchFailed(token, error, "Couldn't connect. Try again.") }
        guard handshakes.isCurrent(token) else { drop(found, "invite join superseded after its search (token \(token))"); throw CancellationError() }
        try await attachParty(found, host: invite.host, expecting: [invite.host], guest: Guest(allowed: Set(invite.players), group: invite.group))
    }

    /// The player cancelled the join: stop, and tell the host (their row says Not now).
    func cancelJoin() {
        handshakes.cancel { if case .joinInvite = $0 { return true }; return false }
        guard let id = joiningRecord else { return }
        joiningRecord = nil; JoinMemory.forget("gc:" + id)
        Task { if let stored = try? await GKTurnBasedMatch.load(withID: id) { await retire(stored) } }
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
    private static func ended(_ who: String) -> Error { MultiplayerError.unavailable("That invite has ended. Ask \(who) to invite you again.") }
    private static func noInternet(_ who: String) -> Error { MultiplayerError.unavailable("No internet right now, so you couldn't join \(who). Try again.") }
    private static func isNetwork(_ error: Error) -> Bool {
        if let code = (error as? GKError)?.code, code == .communicationsFailure || code == .connectionTimeout { return true }
        return (error as NSError).domain == NSURLErrorDomain
    }
    /// Game Center's errors in words a player can act on.
    static func friendly(_ error: Error, _ fallback: String) -> Error {
        if error is MultiplayerError || error is CancellationError { return error }
        switch (error as? GKError)?.code {
        case .notAuthenticated?: return MultiplayerError.unavailable("Sign in to Game Center first.")
        case .cancelled?: return CancellationError()
        default: return isNetwork(error) ? MultiplayerError.unavailable("No internet right now. Try again.") : MultiplayerError.unavailable(fallback)
        }
    }

    /// A guest's side of a private match: who may be in it (nil: the host checks), and its group, this phone's once it is in.
    struct Guest { var allowed: Set<String>?; var group: UInt32? }
    /// A private match was found: it is the party's once the `expecting` players are really connected to it. Game Center hands the
    /// match over while the phones are still connecting (players empty, expectedPlayerCount above 0), and the party used to be called
    /// joined right then: both phones said so, but no lobby ever got through (2026-10-25). Waits, then binds; a connection that never
    /// comes throws, and the handshake goes round again. A guest's failure leaves no group or guest list behind (the friend's phone
    /// used to publish the host's group as its own party after a failed join, 2026-10-26).
    private func attachParty(_ found: PartyMatchLink, host: String, expecting: [String], guest: Guest? = nil) async throws {
        let allowed = guest.map(\.allowed) ?? allowedPartyPlayers
        if let allowed, found.playerIDs.contains(where: { !allowed.contains($0) }) {
            drop(found, "found match holds a player outside the invitation: \(found.playerIDs.map { String($0.suffix(6)) })")
            throw MultiplayerError.unavailable("Game Center connected a player outside this invitation. Please try again.")
        }
        // A party this phone is in stays connected until the new match is: it used to be hung up first, so a second attach (whatever
        // started it) dropped a live party before knowing the new one worked (10-27: joiners dropped 1 s after hello).
        let previous = match
        if let previous, previous !== found {
            SportsDiagnostics.write("game center attach while in a match (players=\(previous.playerIDs.count)): kept until the new one connects [\(handshakeName)]")
        }
        // the delegate first: a state change or the first packet must not arrive before anyone listens
        pendingMatch = found; (found as? GameKitMatchLink)?.gk.delegate = self
        defer { if pendingMatch === found { pendingMatch = nil } }
        do { try await waitForPlayers(found, expecting) }
        catch {
            drop(found, "found match never connected: \(error.localizedDescription)")
            throw error
        }
        if let previous, previous !== found { drop(previous, "replaced by the new party match") }
        match = found; disconnected.removeAll(); groupHadPlayers = true
        if let guest { allowedPartyPlayers = guest.allowed; partyGroup = guest.group }
        for p in (found as? GameKitMatchLink)?.players ?? [] { knownPlayers[p.gamePlayerID] = p }
        found.finish()
        onPartyConnected?(host); onPeersChanged?()
    }
    /// Seconds a found match may take to connect its players before it is given up.
    static var connectSeconds = 20.0
    static var connectPollMilliseconds = 200
    /// Until every one of `ids` is connected to `found` (in its players, nobody else still expected), or `connectSeconds`.
    private func waitForPlayers(_ found: PartyMatchLink, _ ids: [String]) async throws {
        let others = ids.filter { $0 != localID }
        let started = Date()
        SportsDiagnostics.write("party match found: players=\(found.playerIDs.count) expected=\(found.expectedPlayerCount) waiting for \(others.count)")
        while true {
            let here = Set(found.playerIDs)
            if others.allSatisfy(here.contains), found.expectedPlayerCount == 0 {
                SportsDiagnostics.write("party match connected after \(String(format: "%.1f", Date().timeIntervalSince(started))) s: players=\(found.playerIDs.count)")
                return
            }
            if match !== found && pendingMatch !== found { throw CancellationError() }
            if Date().timeIntervalSince(started) > Self.connectSeconds {
                SportsDiagnostics.write("party match never connected: players=\(found.playerIDs.count) expected=\(found.expectedPlayerCount)")
                throw MultiplayerError.unavailable("Couldn't connect to your friend. Check the internet on both phones and try again.")
            }
            try await Task.sleep(for: .milliseconds(Self.connectPollMilliseconds))
        }
    }
    private func register() {
        if GKLocalPlayer.local.isAuthenticated && !registered { GKLocalPlayer.local.register(self); registered = true }
        guard inboxTimer == nil else { return }
        let timer = Timer(timeInterval: 4, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in await self?.refreshInvitations() }
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
        guard match == nil else { throw MultiplayerError.invalidOperation("Already connected to a lobby.") }
        guard handshakes.active == nil else { throw MultiplayerError.invalidOperation("Finish joining your friend first.") }
        let request = try request(sport: sport, count: sport == .tennis ? 2 : count)
        // Programmatic matchmaking works on iOS 17 too. Use a fixed requested group size;
        // partial-fill UI is deliberately deferred rather than pretending a timeout can start it.
        request.minPlayers = request.maxPlayers
        let token = handshakes.ticket(); quickToken = token
        let found = try await matchmake(token) { try await GKMatchmaker.shared().findMatch(for: request) }
        guard token == quickToken else { drop(found, "quick match cancelled"); throw CancellationError() }
        quickToken = 0
        attach(GameKitMatchLink(found))
    }
    func findMore(sport: MultiplayerSport) async throws {
        guard let match = (match as? GameKitMatchLink)?.gk, peers.count + 1 < capacity else { throw MultiplayerError.full }
        let request = try request(sport: sport, count: 4)
        let token = handshakes.ticket(); quickToken = token
        defer { if quickToken == token { quickToken = 0 } }
        try await matchmake(token) { try await GKMatchmaker.shared().addPlayers(to: match, matchRequest: request) }
        GKMatchmaker.shared().finishMatchmaking(for: match)
    }
    /// Stops a quick match (or find more) search. A party handshake has its own cancel; invitations already sent stay out (they wait
    /// for the friend's Join, not for a search).
    func cancelSearch() {
        let token = quickToken; quickToken = 0; cancelMatchmaking(token)
        activeController?.dismiss(animated: true); activeController = nil
        if match == nil { partyGroup = nil; allowedPartyPlayers = nil }
    }
    private func attach(_ found: GameKitMatchLink) {
        if let previous = match, previous !== found { drop(previous, "replaced by a quick match") }
        match = found; disconnected.removeAll(); found.gk.delegate = self
        found.finish()
        onConnected?(); onPeersChanged?()
    }
    func send(_ data: Data, to ids: [String]?, reliable: Bool) throws {
        guard data.count <= MultiplayerPacket.maximumBytes, let match else { throw MultiplayerError.unavailable("No Game Center connection.") }
        try match.send(data, to: ids, reliable: reliable)
    }
    func disconnect() { disconnect(because: "the lobby was left (MultiplayerService.leave logs why)") }
    func disconnect(because why: String) {
        if let match { SportsDiagnostics.write("game center leaves the party match (players=\(match.playerIDs.count)) — \(why) [\(handshakeName)]") }
        handshakes.cancel(where: \.hosting)   // (leaving the party: nobody is brought into it any more)
        cancelSearch(); match?.hangUp(); match = nil; groupHadPlayers = false; partyGroup = nil; allowedPartyPlayers = nil; onPeersChanged?()
    }
    nonisolated func player(_ player: GKPlayer, receivedTurnEventFor match: GKTurnBasedMatch, didBecomeActive: Bool) {
        let id = "gc:" + match.matchID
        Task { @MainActor [weak self] in
            if didBecomeActive { self?.openedFromNotification = id }
            self?.kicked = true
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
        let delivery = GameKitDelivery(value: match), delivery2 = GameKitDelivery(value: player), id = player.gamePlayerID, connected = state == .connected
        Task { @MainActor [weak self] in
            guard let self, let link = self.link(for: delivery.value) else { return }
            if connected { self.knownPlayers[id] = delivery2.value }
            self.playerChanged(id, connected: connected, on: link)
        }
    }
    /// A packet on a match: only the party's match feeds the lobby.
    func received(_ data: Data, from id: String, on link: PartyMatchLink) {
        guard match === link else { return }
        onData?(data, id)
    }
    /// A player connected to or dropped from a match. Only the party's match changes the lobby (one still connecting is watched by
    /// attachParty through its player list).
    func playerChanged(_ id: String, connected: Bool, on link: PartyMatchLink) {
        SportsDiagnostics.write("game center player \(id.prefix(8)) \(connected ? "connected" : "disconnected") (players=\(link.playerIDs.count) expected=\(link.expectedPlayerCount)\(match === link ? "" : ", match still connecting"))")
        guard match === link else { return }
        if connected, let allowed = allowedPartyPlayers, !allowed.contains(id) {
            onError?(MultiplayerError.unavailable("An uninvited player tried to join the party.")); disconnect(because: "uninvited player \(id.suffix(6)) connected (allowed: \(allowed.map { String($0.suffix(6)) }.sorted()))"); return
        }
        if connected { disconnected.remove(id) } else { disconnected.insert(id) }
        emptiedAt = peers.isEmpty ? (emptiedAt ?? Date()) : nil
        onPeersChanged?()
    }
    #if DEBUG
    /// Tests: a found match handed to the real attach (as findMatch's result would be).
    func debugAttachParty(_ link: PartyMatchLink, host: String, expecting: [String], guest: Guest? = nil) async throws {
        try await attachParty(link, host: host, expecting: expecting, guest: guest)
    }
    #endif
    nonisolated func match(_ match: GKMatch, didFailWithError error: Error?) {
        let delivery = GameKitDelivery(value: match)
        Task { @MainActor [weak self] in
            guard let self else { return }
            let ours = self.link(for: delivery.value)
            SportsDiagnostics.write("game center match failed: \(error?.localizedDescription ?? "no error") (ours: \(ours != nil))")
            guard ours === self.match, ours != nil else { return }; if let error { self.onError?(error) }
        }
    }
    nonisolated func match(_ match: GKMatch, shouldReinviteDisconnectedPlayer player: GKPlayer) -> Bool { true }
    /// Apple's own real-time invitation: never dropped. Accepted during a match it waits, and joins once this phone is in the Plaza.
    nonisolated func player(_ player: GKPlayer, didAccept invite: GKInvite) {
        let delivery = GameKitDelivery(value: invite)
        Task { @MainActor [weak self] in self?.pendingRealTimeInvite = delivery.value; self?.acceptPendingRealTimeInvite() }
    }
    private func acceptPendingRealTimeInvite() {
        guard let invite = pendingRealTimeInvite, joinAvailable?() != false else { return }
        let sender = invite.sender.gamePlayerID, name = invite.sender.displayName
        // (another join is running, or it is not the moment: it stays pending, and the next refresh tries again)
        guard let token = handshakes.begin(.joinRealTime(sender), cancel: { [weak self] in self?.cancelMatchmaking($0) }) else { return }
        guard canAcceptParty?(false) != false else { handshakes.end(token); return }
        pendingRealTimeInvite = nil
        let delivery = GameKitDelivery(value: invite)
        Task { @MainActor [weak self] in
            guard let self else { return }
            defer { self.handshakes.end(token) }
            guard self.handshakes.isCurrent(token) else { return }
            do {
                let found = GameKitMatchLink(try await self.matchmake(token) { try await GKMatchmaker.shared().match(for: delivery.value) })
                guard self.handshakes.isCurrent(token) else { self.drop(found, "real-time invite superseded after its search"); return }
                try await self.attachParty(found, host: sender, expecting: [sender], guest: Guest(allowed: nil, group: nil))
            } catch {
                guard self.handshakes.isCurrent(token) else { return }
                self.onError?(MultiplayerError.unavailable("Couldn't join \(name). Ask them to invite you again."))
            }
        }
    }
    nonisolated func matchmakerViewControllerWasCancelled(_ viewController: GKMatchmakerViewController) {
        Task { @MainActor [weak self] in guard self?.activeController === viewController else { return }; self?.cancelSearch() }
    }
    nonisolated func matchmakerViewController(_ viewController: GKMatchmakerViewController, didFailWithError error: Error) {
        Task { @MainActor [weak self] in guard self?.activeController === viewController else { return }; viewController.dismiss(animated: true); self?.activeController = nil; self?.onError?(error) }
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
