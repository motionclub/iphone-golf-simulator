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

/// Game Center connection behind the in-app friends list. Only authentication may require an Apple controller.
@MainActor
final class GameCenterTransport: NSObject, MultiplayerTransport, GKMatchDelegate, GKLocalPlayerListener, GKMatchmakerViewControllerDelegate {
    var localID: String { GKLocalPlayer.local.gamePlayerID }
    var peers: [String] { match?.players.map(\.gamePlayerID).filter { !disconnected.contains($0) } ?? [] }
    var onData: ((Data, String) -> Void)?
    var onPeersChanged: (() -> Void)?
    var onError: ((Error) -> Void)?
    var onConnected: (() -> Void)?
    private(set) var match: GKMatch?
    private var generation = 0
    private var registered = false
    private var disconnected: Set<String> = []
    private var activeController: GKMatchmakerViewController?
    /// Searches running on GKMatchmaker now. Its cancel() stops every one of them, and a cancel sent just before a new search also
    /// cancels that search (2026-10-25 phone log: "join attempt 1 failed: … canceled"). So it is only sent while one is running.
    private var matchmaking = 0
    private func matchmake<T>(_ work: () async throws -> T) async throws -> T {
        matchmaking += 1; defer { matchmaking -= 1 }
        return try await work()
    }
    private func cancelMatchmaking() { if matchmaking > 0 { GKMatchmaker.shared().cancel() } }
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
    var canAcceptParty: (() -> Bool)?
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
    enum Outgoing: Equatable { case joining, waiting, joined, declined, expired, full }
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
    private var joinConnecting = false
    private var joinGeneration = 0
    private var resumed: Set<String> = []
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

    /// Host: the friend tapped Join and this phone is free: say go (with the party as it is now) and match with them.
    private func bringIn(_ stored: GKTurnBasedMatch, _ invitation: GameCenterPartyInvitation, teamID: String) {
        hostMatching = stored.matchID
        Task { @MainActor [weak self] in
            guard let self else { return }
            defer { if self.hostMatching == stored.matchID { self.hostMatching = nil } }
            let members = Array(Set([self.localID, invitation.recipient] + self.peers)).sorted()
            guard members.count <= self.capacity, let friend = self.participant(stored, invitation.recipient) else {
                self.outgoing[stored.matchID] = nil; self.onOutgoing?(teamID, .full); await self.retire(stored); return
            }
            self.onOutgoing?(teamID, .joining)
            var go = invitation; go.step = .go; go.round += 1; go.players = members
            do { try await stored.endTurn(withNextParticipants: [friend], turnTimeout: Self.turnTimeout(go), match: JSONEncoder().encode(go)) }
            catch { self.onOutgoing?(teamID, .waiting); return }   // (the record still says accepted: the next refresh tries again)
            self.allowedPartyPlayers = (self.allowedPartyPlayers ?? Set([self.localID] + self.peers)).union([invitation.recipient])
            self.generation += 1; let token = self.generation
            let timeout = Task { @MainActor [weak self] in
                try? await Task.sleep(for: .seconds(60))
                guard !Task.isCancelled, let self, self.generation == token else { return }
                self.cancelMatchmaking()
            }
            defer { timeout.cancel() }
            do {
                let request = try self.privateRequest(group: invitation.group, count: members.count)
                if let match = self.match {
                    try await self.matchmake { try await GKMatchmaker.shared().addPlayers(to: match, matchRequest: request) }
                    try await self.waitForPlayers(match, [invitation.recipient])
                    GKMatchmaker.shared().finishMatchmaking(for: match)
                    self.onPeersChanged?()
                } else {
                    let found = try await self.matchmake { try await GKMatchmaker.shared().findMatch(for: request) }
                    guard token == self.generation else { found.disconnect(); self.onOutgoing?(teamID, .waiting); return }
                    try await self.attachParty(found, host: self.localID, expecting: [invitation.recipient])
                }
                self.outgoing[stored.matchID] = nil
                self.onOutgoing?(teamID, .joined)
                await self.retire(stored)
            } catch {
                // the friend's phone says Join once more and this goes round again, until the invitation runs out
                SportsDiagnostics.write("Game Center invite: host match failed: \(error.localizedDescription)")
                self.onOutgoing?(teamID, .waiting)
            }
        }
    }

    // MARK: CloudKit knocks (ClubCloud): the same private match, met when the host's phone answers a knock

    /// The private group this phone's party meets in, made now if it has none.
    func hostGroup() -> UInt32 {
        if let g = partyGroup { return g }
        let g = UInt32.random(in: 0x60000000..<0x70000000); partyGroup = g; return g
    }
    /// Host: let in someone who knocked (a friend dropping in, or someone with the code).
    func letIn(_ gameID: String, group: UInt32, players: Int) async throws {
        allowedPartyPlayers = (allowedPartyPlayers ?? Set([localID] + peers)).union([gameID])
        generation += 1; let token = generation
        let timeout = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(60))
            guard !Task.isCancelled, let self, self.generation == token else { return }
            self.cancelMatchmaking()
        }
        defer { timeout.cancel() }
        let request = try privateRequest(group: group, count: players)
        do {
            if let match {
                try await matchmake { try await GKMatchmaker.shared().addPlayers(to: match, matchRequest: request) }
                try await waitForPlayers(match, [gameID])
                GKMatchmaker.shared().finishMatchmaking(for: match)
                onPeersChanged?()
            } else {
                let found = try await matchmake { try await GKMatchmaker.shared().findMatch(for: request) }
                guard token == generation else { found.disconnect(); throw CancellationError() }
                try await attachParty(found, host: localID, expecting: [gameID])
            }
        } catch { throw Self.friendly(error, "Couldn't connect. Try again.") }
    }
    /// Joiner: into the host's party group after its go.
    func joinGroup(host: String, group: UInt32, players: Int) async throws {
        joinGeneration += 1; let token = joinGeneration
        joinConnecting = true; defer { if joinGeneration == token { joinConnecting = false } }
        allowedPartyPlayers = nil; partyGroup = group   // (the host checks who comes in)
        let request = try privateRequest(group: group, count: players)
        let timeout = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(45))
            guard !Task.isCancelled, let self, self.joinGeneration == token, self.joinConnecting else { return }
            self.cancelMatchmaking()
        }
        defer { timeout.cancel() }
        let found: GKMatch
        do { found = try await matchmake { try await GKMatchmaker.shared().findMatch(for: request) } } catch { throw Self.friendly(error, "Couldn't connect. Try again.") }
        guard token == joinGeneration else { found.disconnect(); throw CancellationError() }
        try await attachParty(found, host: host, expecting: [host])
    }

    private func privateRequest(group: UInt32, count: Int) throws -> GKMatchRequest {
        let r = try request(sport: nil, count: count)
        r.playerGroup = Int(group); r.minPlayers = count; r.maxPlayers = count
        return r
    }

    // MARK: the inbox (both sides)

    /// Apple's stored records, polled every 4 s while the app is active and on every turn event: the friend's inbox cards, a join to
    /// carry on, and the host's friends who tapped Join.
    func refreshInvitations() async {
        guard GKLocalPlayer.local.isAuthenticated, UIApplication.shared.applicationState == .active, !refreshingInbox else { return }
        refreshingInbox = true; defer { refreshingInbox = false }
        acceptPendingRealTimeInvite()
        let known = outgoing
        do {
            let matches = try await GKTurnBasedMatch.loadMatches()
            var cards: [HubInvite] = [], pending: [String: GKTurnBasedMatch] = [:], resume: [HubInvite] = [], seen: Set<String> = []
            for stored in matches where stored.status != .ended {
                guard let data = try? await stored.loadMatchData(),
                      let invite = try? JSONDecoder().decode(GameCenterPartyInvitation.self, from: data) else { continue }
                let now = Self.now
                guard invite.kind == GameCenterPartyInvitation.kindV2 else {
                    // an older build's record: cleaned up once it has run out
                    if invite.kind.hasPrefix("motionclub.partyInvite"), invite.expiresAt <= now,
                       invite.host == localID || invite.recipient == localID { await retire(stored) }
                    continue
                }
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
                    let card = invite.card(stored.matchID)
                    pending[card.id] = stored; cards.append(card)
                    if step == .resume, !resumed.contains(card.id) { resumed.insert(card.id); resume.append(card) }
                default: break
                }
            }
            // the host's record ended on the friend's side (they said Not now) without passing through here. Missing twice in a row,
            // so a record sent while this refresh was loading (or not listed yet) is not taken for an answer.
            for (id, out) in known where outgoing[id] != nil && !seen.contains(id) && id != hostMatching {
                missingOutgoing[id, default: 0] += 1
                if missingOutgoing[id]! >= 2 { outgoing[id] = nil; missingOutgoing[id] = nil; onOutgoing?(out.teamID, .declined) }
            }
            for id in seen { missingOutgoing[id] = nil }
            inbox = pending; onInvitations?(cards.sorted { $0.expiresAt > $1.expiresAt })
            let opened = openedFromNotification
            if let opened, let card = cards.first(where: { $0.id == opened }) { openedFromNotification = nil; onInvitationOpened?(card) }
            // tapped Join before the app closed (or before a failed connection): the join carries on by itself, once
            for card in resume where card.id != opened { onInvitationOpened?(card) }
        } catch { SportsDiagnostics.write("Game Center invite inbox: \(error.localizedDescription)") }
    }

    // MARK: joining a friend's party

    /// The friend tapped Join (and is in the Plaza): say yes, then wait for the host's go and connect. Keeps trying, round after round,
    /// until it is in, the invitation runs out, the host leaves, or the player cancels. Throws only words a player can act on.
    func acceptStoredInvitation(_ card: HubInvite) async throws {
        let id = card.lobbyCode, who = card.from.name
        joinGeneration += 1; let token = joinGeneration
        joiningRecord = id; resumed.insert(card.id); inbox[card.id] = nil
        defer { if joinGeneration == token { joiningRecord = nil; joinConnecting = false } }
        var tried = -1, failures = 0, loadFailures = 0, acceptFailures = 0
        var goSeen: (round: Int, at: Double)?
        while true {
            guard token == joinGeneration else { throw CancellationError() }
            let stored: GKTurnBasedMatch, invite: GameCenterPartyInvitation
            do {
                stored = try await GKTurnBasedMatch.load(withID: id)
                invite = try JSONDecoder().decode(GameCenterPartyInvitation.self, from: try await stored.loadMatchData() ?? Data())
                loadFailures = 0
            } catch {
                // no connection for a moment: try again for a while; Game Center cannot find or read the record: it has ended
                let network = Self.isNetwork(error)
                loadFailures += 1
                if loadFailures >= (network ? 8 : 3) { throw network ? Self.noInternet(who) : Self.ended(who) }
                try await Task.sleep(for: .seconds(2)); continue
            }
            guard token == joinGeneration else { throw CancellationError() }
            let now = Self.now
            guard stored.status != .ended, invite.kind == GameCenterPartyInvitation.kindV2, invite.recipient == localID, invite.expiresAt > now else { throw Self.ended(who) }
            guard let host = participant(stored, invite.host), Self.here(host), let hostPlayer = host.player,
                  invitationAllowed?(hostPlayer.gamePlayerID, hostPlayer.teamPlayerID) != false else {
                throw MultiplayerError.unavailable("\(who) left the game. Ask them to invite you again.")
            }
            if participant(stored, localID)?.status == .invited {
                do { _ = try await stored.acceptInvite() }
                catch {
                    acceptFailures += 1
                    if acceptFailures >= 8 { throw Self.isNetwork(error) ? Self.noInternet(who) : Self.ended(who) }
                    try await Task.sleep(for: .seconds(2))
                }
                continue   // (read the record again: accepting it changes it)
            }
            let myTurn = stored.currentParticipant?.player?.gamePlayerID == localID
            if invite.step == .go, goSeen?.round != invite.round { goSeen = (invite.round, now) }
            // a go that waited while this phone was busy is stale: the host stopped matching after a minute, so ask for a fresh one
            let staleGo = invite.step == .go && now - (goSeen?.at ?? now) > 40_000
            if myTurn && (invite.step == .invited || (invite.step == .go && (invite.round <= tried || staleGo))) {
                if joinAvailable?() != false {
                    // Join (again): the turn goes to the host, whose phone says go as soon as it is free
                    var yes = invite; yes.step = .accepted
                    try? await stored.endTurn(withNextParticipants: [host], turnTimeout: Self.turnTimeout(yes), match: JSONEncoder().encode(yes))
                    tried = max(tried, invite.round)
                }
                onJoinStage?(.waitingForHost)
            } else if myTurn && invite.step == .go {
                if joinAvailable?() != false, canAcceptParty?() != false {
                    tried = invite.round; joinConnecting = true; onJoinStage?(.connecting)
                    do {
                        try await connect(invite, token)
                        joinConnecting = false
                        await retire(stored)
                        return
                    } catch {
                        joinConnecting = false
                        guard token == joinGeneration else { throw CancellationError() }
                        failures += 1
                        SportsDiagnostics.write("Game Center invite: join attempt \(failures) failed: \(error.localizedDescription)")
                        if failures >= 4 { throw MultiplayerError.unavailable("Couldn't connect to \(who). Check the internet on both phones, then tap Join again.") }
                        continue   // (round again: the record now says go with a round already tried, so Join goes back to the host)
                    }
                }
            } else {
                onJoinStage?(.waitingForHost)
            }
            try await Task.sleep(for: .seconds(2))
        }
    }

    private func connect(_ invite: GameCenterPartyInvitation, _ token: Int) async throws {
        allowedPartyPlayers = Set(invite.players); partyGroup = invite.group
        let request = try privateRequest(group: invite.group, count: invite.players.count)
        let timeout = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(45))
            guard !Task.isCancelled, let self, self.joinGeneration == token, self.joinConnecting else { return }
            self.cancelMatchmaking()
        }
        defer { timeout.cancel() }
        let found = try await matchmake { try await GKMatchmaker.shared().findMatch(for: request) }
        guard token == joinGeneration else { found.disconnect(); throw CancellationError() }
        try await attachParty(found, host: invite.host, expecting: [invite.host])
    }

    /// The player cancelled the join: stop, and tell the host (their row says Not now).
    func cancelJoin() {
        joinGeneration += 1
        if joinConnecting { joinConnecting = false; cancelMatchmaking() }
        guard let id = joiningRecord else { return }
        joiningRecord = nil
        Task { if let stored = try? await GKTurnBasedMatch.load(withID: id) { await retire(stored) } }
    }

    func declineStoredInvitation(_ id: String) {
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

    /// A private match was found: it is the party's once the `expecting` players are really connected to it. Game Center hands the
    /// match over while the phones are still connecting (players empty, expectedPlayerCount above 0), and the party used to be called
    /// joined right then: both phones said so, but no lobby ever got through (2026-10-25). Waits, then binds; a connection that never
    /// comes throws, and the handshake goes round again.
    private func attachParty(_ found: GKMatch, host: String, expecting: [String]) async throws {
        if let allowedPartyPlayers, found.players.contains(where: { !allowedPartyPlayers.contains($0.gamePlayerID) }) {
            found.disconnect(); throw MultiplayerError.unavailable("Game Center connected a player outside this invitation. Please try again.")
        }
        if let previous = match, previous !== found { previous.delegate = nil; previous.disconnect() }
        // the delegate first: a state change or the first packet must not arrive before anyone listens
        match = found; disconnected.removeAll(); found.delegate = self
        do { try await waitForPlayers(found, expecting) }
        catch { if match === found { match = nil; found.delegate = nil }; found.disconnect(); throw error }
        for p in found.players { knownPlayers[p.gamePlayerID] = p }
        GKMatchmaker.shared().finishMatchmaking(for: found)
        onPartyConnected?(host); onPeersChanged?()
    }
    /// Seconds a found match may take to connect its players before it is given up.
    static var connectSeconds = 20.0
    /// Until every one of `ids` is connected to `found` (in its players, nobody else still expected), or `connectSeconds`.
    private func waitForPlayers(_ found: GKMatch, _ ids: [String]) async throws {
        let others = ids.filter { $0 != localID }
        let started = Date()
        SportsDiagnostics.write("party match found: players=\(found.players.count) expected=\(found.expectedPlayerCount) waiting for \(others.count)")
        while true {
            let here = Set(found.players.map(\.gamePlayerID))
            if others.allSatisfy(here.contains), found.expectedPlayerCount == 0 {
                SportsDiagnostics.write("party match connected after \(String(format: "%.1f", Date().timeIntervalSince(started))) s: players=\(found.players.count)")
                return
            }
            if match !== found { throw CancellationError() }
            if Date().timeIntervalSince(started) > Self.connectSeconds {
                SportsDiagnostics.write("party match never connected: players=\(found.players.count) expected=\(found.expectedPlayerCount)")
                throw MultiplayerError.unavailable("Couldn't connect to your friend. Check the internet on both phones and try again.")
            }
            try await Task.sleep(for: .milliseconds(200))
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
        let request = try request(sport: sport, count: sport == .tennis ? 2 : count)
        // Programmatic matchmaking works on iOS 17 too. Use a fixed requested group size;
        // partial-fill UI is deliberately deferred rather than pretending a timeout can start it.
        request.minPlayers = request.maxPlayers
        generation += 1; let token = generation
        let found = try await matchmake { try await GKMatchmaker.shared().findMatch(for: request) }
        guard token == generation else { found.disconnect(); throw CancellationError() }
        attach(found)
    }
    func findMore(sport: MultiplayerSport) async throws {
        guard let match, peers.count + 1 < capacity else { throw MultiplayerError.full }
        let request = try request(sport: sport, count: 4)
        try await matchmake { try await GKMatchmaker.shared().addPlayers(to: match, matchRequest: request) }
        GKMatchmaker.shared().finishMatchmaking(for: match)
    }
    /// Stops a search. Invitations already sent stay out (they wait for the friend's Join, not for a search).
    func cancelSearch() {
        generation += 1; cancelMatchmaking(); activeController?.dismiss(animated: true); activeController = nil
        if match == nil { partyGroup = nil; allowedPartyPlayers = nil }
    }
    private func attach(_ found: GKMatch) {
        if let previous = match, previous !== found { previous.disconnect() }
        match = found; disconnected.removeAll(); found.delegate = self
        GKMatchmaker.shared().finishMatchmaking(for: found)
        onConnected?(); onPeersChanged?()
    }
    func send(_ data: Data, to ids: [String]?, reliable: Bool) throws {
        guard data.count <= MultiplayerPacket.maximumBytes, let match else { throw MultiplayerError.unavailable("No Game Center connection.") }
        let mode: GKMatch.SendDataMode = reliable ? .reliable : .unreliable
        if let ids { try match.send(data, to: match.players.filter { ids.contains($0.gamePlayerID) }, dataMode: mode) }
        else { try match.sendData(toAllPlayers: data, with: mode) }
    }
    func disconnect() { cancelSearch(); match?.delegate = nil; match?.disconnect(); match = nil; partyGroup = nil; allowedPartyPlayers = nil; onPeersChanged?() }
    nonisolated func player(_ player: GKPlayer, receivedTurnEventFor match: GKTurnBasedMatch, didBecomeActive: Bool) {
        let id = "gc:" + match.matchID
        Task { @MainActor [weak self] in
            if didBecomeActive { self?.openedFromNotification = id }
            await self?.refreshInvitations()
        }
    }
    nonisolated func match(_ match: GKMatch, didReceive data: Data, fromRemotePlayer player: GKPlayer) {
        let id = player.gamePlayerID, delivery = GameKitDelivery(value: match)
        Task { @MainActor [weak self] in guard self?.match === delivery.value else { return }; self?.onData?(data, id) }
    }
    nonisolated func match(_ match: GKMatch, player: GKPlayer, didChange state: GKPlayerConnectionState) {
        let delivery = GameKitDelivery(value: match), delivery2 = GameKitDelivery(value: player), id = player.gamePlayerID, connected = state == .connected
        Task { @MainActor [weak self] in
            guard let self, self.match === delivery.value else { return }
            if connected, let allowed = self.allowedPartyPlayers, !allowed.contains(id) {
                self.onError?(MultiplayerError.unavailable("An uninvited player tried to join the party.")); self.disconnect(); return
            }
            if connected { self.disconnected.remove(id); self.knownPlayers[id] = delivery2.value } else { self.disconnected.insert(id) }
            SportsDiagnostics.write("game center player \(id.prefix(8)) \(connected ? "connected" : "disconnected") (players=\(delivery.value.players.count) expected=\(delivery.value.expectedPlayerCount))")
            self.onPeersChanged?()
        }
    }
    nonisolated func match(_ match: GKMatch, didFailWithError error: Error?) {
        let delivery = GameKitDelivery(value: match)
        Task { @MainActor [weak self] in guard self?.match === delivery.value else { return }; if let error { self?.onError?(error) } }
    }
    nonisolated func match(_ match: GKMatch, shouldReinviteDisconnectedPlayer player: GKPlayer) -> Bool { true }
    /// Apple's own real-time invitation: never dropped. Accepted during a match it waits, and joins once this phone is in the Plaza.
    nonisolated func player(_ player: GKPlayer, didAccept invite: GKInvite) {
        let delivery = GameKitDelivery(value: invite)
        Task { @MainActor [weak self] in self?.pendingRealTimeInvite = delivery.value; self?.acceptPendingRealTimeInvite() }
    }
    private func acceptPendingRealTimeInvite() {
        guard let invite = pendingRealTimeInvite, joinAvailable?() != false else { return }
        pendingRealTimeInvite = nil
        guard canAcceptParty?() != false else { pendingRealTimeInvite = invite; return }
        generation += 1; let token = generation
        allowedPartyPlayers = nil; partyGroup = nil
        let delivery = GameKitDelivery(value: invite)
        Task { @MainActor [weak self] in
            do {
                guard let self else { return }
                let found = try await self.matchmake { try await GKMatchmaker.shared().match(for: delivery.value) }
                guard token == self.generation else { found.disconnect(); return }
                try await self.attachParty(found, host: delivery.value.sender.gamePlayerID, expecting: [delivery.value.sender.gamePlayerID])
            } catch {
                guard let self, token == self.generation else { return }
                self.onError?(MultiplayerError.unavailable("Couldn't join \(delivery.value.sender.displayName). Ask them to invite you again."))
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
            guard self?.activeController === viewController else { delivery.value.disconnect(); return }
            viewController.dismiss(animated: true); self?.activeController = nil; self?.attach(delivery.value)
        }
    }
}
