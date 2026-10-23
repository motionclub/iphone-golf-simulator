@preconcurrency import GameKit
import UIKit

private struct GameKitDelivery<T>: @unchecked Sendable { let value: T }

/// A friend's answer to a Game Center invitation that did not end in a party.
enum GameCenterInviteAnswer: Error, LocalizedError, Equatable {
    case declined, noAnswer, incompatible, failed
    init(_ response: GKInviteRecipientResponse) {
        switch response {
        case .declined: self = .declined
        case .noAnswer: self = .noAnswer
        case .incompatible: self = .incompatible
        default: self = .failed
        }
    }
    var errorDescription: String? {
        switch self {
        case .declined: "Your friend said not now."
        case .noAnswer: "No answer. Your friend may be away from their phone."
        case .incompatible: "Your friend needs the same Motion Club update as you. Update both phones from TestFlight."
        case .failed: "Game Center could not reach your friend. Try again."
        }
    }
}

/// The in-game half of an invitation: a small turn-based record Game Center keeps for the friend, so their game shows its own
/// banner (Join / Not now) beside Apple's. Join from that banner answers on the record, and both phones meet in the invitation's
/// private Game Center group.
struct GameCenterDoorbell: Codable, Equatable {
    static let kind = "motionclub.partyDoor.v2"
    static let groups: Range<UInt32> = 0x60000000..<0x70000000
    var kind = GameCenterDoorbell.kind
    var host: String
    var name: String
    var recipient: String
    var group: UInt32
    /// The party's size with this friend in it (both phones ask Game Center for exactly this many).
    var size: Int
    /// Milliseconds since 1970.
    var expiresAt: Double
    /// "join" once the friend tapped Join in the game.
    var answer: String?
    func valid(for local: String, now: Double) -> Bool {
        kind == Self.kind && recipient == local && host != local && !host.isEmpty && Self.groups.contains(group)
        && (2...4).contains(size) && expiresAt.isFinite && expiresAt > now && expiresAt <= now + 125_000
    }
    func card(_ matchID: String) -> HubInvite {
        HubInvite(inviteID: "gc:" + matchID, from: HubPlayerRef(id: host, name: name), sport: "party",
                  lobbyCode: matchID, group: group, capacity: size, expiresAt: expiresAt)
    }
}

/// Game Center connection behind the in-app friends list. Invitations are Apple's own (GKMatchRequest.recipients): Game Center
/// delivers them, the friend's tap joins through `player(_:didAccept:)`, and neither phone shows a matchmaking screen. Each one
/// also rings a GameCenterDoorbell, so a friend who is in the game sees our banner and joins from it.
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
    override init() { super.init(); register() }
    var capacity: Int { min(4, GKMatchRequest.maxPlayersAllowedForMatch(of: .peerToPeer)) }

    private var authenticationWaiters: [CheckedContinuation<Void, Error>] = []
    private var authenticationPresenter: ((UIViewController) -> Void)?
    private var authenticationController: UIViewController?
    var onAuthenticationController: ((UIViewController) -> Void)?
    var onAuthenticationChanged: (() -> Void)?
    var onPartyConnected: ((String) -> Void)?
    var canAcceptParty: (() -> Bool)?
    /// Game Center sent the invitation (the friend's teamPlayerID).
    var onInvitationSent: ((String) -> Void)?
    var invitationAllowed: ((String, String) -> Bool)?
    /// This phone accepted a friend's invitation and is joining them (their name).
    var onJoining: ((String) -> Void)?
    /// The player picked friends in Apple's Games app, which opened this game to play with them.
    var onRequestMatch: (([GKPlayer]) -> Void)?
    /// Friends' invitations to this phone, from their doorbells (for the banner and the Friends list).
    var onInvitations: (([HubInvite]) -> Void)?
    /// The player tapped Game Center's notification for a doorbell: that tap is the Join.
    var onInvitationOpened: ((HubInvite) -> Void)?
    /// The invitation waiting for answers: whom, its doorbells, and the call to finish (once). `leg` counts the matchmaking calls:
    /// Apple's invitation is the first, meeting a friend who joined from our banner the second.
    private struct Invitation {
        let token: Int; let players: [GKPlayer]; var waiting: Set<String>; var accepted = false
        let group: UInt32; var doors: [String: GKTurnBasedMatch] = [:]; var leg = 0; var meeting = false
        let done: CheckedContinuation<Void, Error>
    }
    private var invitation: Invitation?
    static let invitationSeconds = 100.0
    /// How long two phones look for each other in the invitation's group.
    static let meetingSeconds = 30.0
    private var doorbells: [String: (stored: GKTurnBasedMatch, bell: GameCenterDoorbell)] = [:]
    private var openedFromNotification: String?
    private var doorbellTimer: Timer?
    private var refreshingDoorbells = false
    private var retiring: Set<String> = []
    private var allowedPartyPlayers: Set<String>?
    func allowPartyPlayer(_ id: String) { allowedPartyPlayers?.insert(id) }

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

    /// Invite friends to this phone's party (made now if there is none). Game Center delivers Apple's invitation (a banner or a
    /// notification), and each friend also gets a doorbell: our own banner while they are in the game. Returns once an invited
    /// friend is in the party; throws their answer (GameCenterInviteAnswer) when nobody comes, or CancellationError after
    /// `cancelSearch`.
    func invite(_ players: [GKPlayer]) async throws {
        guard !players.isEmpty, peers.count + 1 + players.count <= capacity else { throw MultiplayerError.full }
        guard invitation == nil else { throw MultiplayerError.invalidOperation("An invitation is already waiting for an answer.") }
        let request = try request(sport: nil, count: 2)
        request.recipients = players
        request.inviteMessage = "Join my Motion Club party"
        // (GameKit calls these off the main thread: @Sendable keeps Swift from asserting the main actor inside them)
        request.recipientResponseHandler = { @Sendable [weak self] player, response in
            let id = player.gamePlayerID
            Task { @MainActor [weak self] in self?.answered(id, response) }
        }
        allowedPartyPlayers = (allowedPartyPlayers ?? Set(peers + [localID])).union(players.map(\.gamePlayerID))
        generation += 1; let token = generation
        let group = UInt32.random(in: GameCenterDoorbell.groups), size = peers.count + 2
        try await withCheckedThrowingContinuation { (done: CheckedContinuation<Void, Error>) in
            invitation = Invitation(token: token, players: players, waiting: Set(players.map(\.gamePlayerID)), group: group, done: done)
            if let match {
                GKMatchmaker.shared().addPlayers(to: match, matchRequest: request) { @Sendable error in
                    Task { @MainActor [weak self] in self?.invitationEnded(token, leg: 0, found: nil, error) }
                }
            } else {
                GKMatchmaker.shared().findMatch(for: request) { @Sendable found, error in
                    let delivery = GameKitDelivery(value: found)
                    Task { @MainActor [weak self] in self?.invitationEnded(token, leg: 0, found: delivery.value, error) }
                }
            }
            for player in players { onInvitationSent?(player.teamPlayerID); ring(player, token: token, group: group, size: size) }
            Task { @MainActor [weak self] in
                try? await Task.sleep(for: .seconds(Self.invitationSeconds))
                guard self?.invitation?.meeting == false else { return }
                self?.endInvitation(token, throwing: GameCenterInviteAnswer.noAnswer)
            }
            Task { @MainActor [weak self] in
                while true {
                    try? await Task.sleep(for: .seconds(2))
                    guard let self, self.invitation?.token == token else { return }
                    await self.checkDoorbells(token)
                }
            }
        }
    }
    /// A friend answered. Accepted: Game Center finishes the match. Anything else: that friend is out, and with nobody left to
    /// come the invitation ends with their answer.
    private func answered(_ id: String, _ response: GKInviteRecipientResponse) {
        guard var pending = invitation, pending.waiting.contains(id), !pending.meeting else { return }
        if response == .accepted { pending.accepted = true; invitation = pending; return }
        pending.waiting.remove(id); invitation = pending
        if pending.waiting.isEmpty, !pending.accepted { endInvitation(pending.token, throwing: GameCenterInviteAnswer(response)) }
    }
    /// Game Center's matchmaking call came back: the party is on (or bigger), or it failed. A call that was replaced (Apple's
    /// invitation, once the friend joined from our banner) is ignored.
    private func invitationEnded(_ token: Int, leg: Int, found: GKMatch?, _ error: Error?) {
        guard let pending = invitation, pending.token == token, pending.leg == leg else { found?.disconnect(); return }
        invitation = nil; retireDoorbells(pending)
        if let error { pending.done.resume(throwing: error); return }
        do {
            if let found { try attachParty(found, host: localID) }
            else if let match { GKMatchmaker.shared().finishMatchmaking(for: match) }
            pending.done.resume()
        } catch { pending.done.resume(throwing: error) }
    }
    /// Stop asking (no answer, every friend said no, or the host cancelled) and finish the invitation once.
    private func endInvitation(_ token: Int, throwing error: Error) {
        guard let pending = invitation, pending.token == token else { return }
        invitation = nil; retireDoorbells(pending)
        if match == nil || pending.meeting { GKMatchmaker.shared().cancel() }
        else { for player in pending.players { GKMatchmaker.shared().cancelPendingInvite(to: player) } }
        pending.done.resume(throwing: error)
    }

    // MARK: doorbells (the in-game banner)

    /// Leave the friend a doorbell. Best effort: Apple's invitation stands without it.
    private func ring(_ player: GKPlayer, token: Int, group: UInt32, size: Int) {
        Task { @MainActor [weak self] in
            guard let self else { return }
            do {
                let request = try self.request(sport: nil, count: 2)
                request.recipients = [player]
                request.inviteMessage = "\(GKLocalPlayer.local.displayName) invited you to their Motion Club party"
                let stored = try await GKTurnBasedMatch.find(for: request)
                let next = stored.participants.filter { $0.player?.gamePlayerID == player.gamePlayerID }
                guard self.invitation?.token == token, !next.isEmpty, stored.currentParticipant?.player?.gamePlayerID == self.localID else {
                    await self.retire(stored); return
                }
                let bell = GameCenterDoorbell(host: self.localID, name: GKLocalPlayer.local.displayName, recipient: player.gamePlayerID, group: group,
                                              size: size, expiresAt: Date().timeIntervalSince1970 * 1000 + Self.invitationSeconds * 1000)
                try await stored.endTurn(withNextParticipants: next, turnTimeout: Self.invitationSeconds, match: JSONEncoder().encode(bell))
                guard self.invitation?.token == token else { await self.retire(stored); return }
                self.invitation?.doors[player.gamePlayerID] = stored
            } catch { SportsDiagnostics.write("Game Center doorbell: \(error.localizedDescription)") }
        }
    }
    /// Host: has a friend answered on their doorbell? Join → meet them in the group; Not now → the invitation's answer.
    private func checkDoorbells(_ token: Int) async {
        guard let doors = invitation?.doors, invitation?.token == token, invitation?.meeting == false else { return }
        for (id, door) in doors {
            guard let fresh = try? await GKTurnBasedMatch.load(withID: door.matchID), invitation?.token == token, invitation?.meeting == false else { continue }
            if fresh.participants.first(where: { $0.player?.gamePlayerID == id })?.status == .declined { answered(id, .declined); continue }
            guard let data = try? await fresh.loadMatchData(), let bell = try? JSONDecoder().decode(GameCenterDoorbell.self, from: data),
                  bell.answer == "join", invitation?.token == token else { continue }
            meet(token, size: bell.size); return
        }
    }
    /// The friend tapped Join in the game: Apple's invitation is withdrawn and both phones ask Game Center for the invitation's
    /// private group.
    private func meet(_ token: Int, size: Int) {
        guard var pending = invitation, pending.token == token, !pending.meeting else { return }
        pending.meeting = true; pending.leg = 1; invitation = pending
        GKMatchmaker.shared().cancel()
        let request: GKMatchRequest
        do { request = try groupRequest(pending.group, size: size) } catch { endInvitation(token, throwing: error); return }
        Task { @MainActor [weak self] in
            // (give Game Center a moment to finish withdrawing the first call before the second starts)
            try? await Task.sleep(for: .milliseconds(500))
            guard let self, self.invitation?.token == token else { return }
            if let match = self.match {
                GKMatchmaker.shared().addPlayers(to: match, matchRequest: request) { @Sendable error in
                    Task { @MainActor [weak self] in self?.invitationEnded(token, leg: 1, found: nil, error) }
                }
            } else {
                GKMatchmaker.shared().findMatch(for: request) { @Sendable found, error in
                    let delivery = GameKitDelivery(value: found)
                    Task { @MainActor [weak self] in self?.invitationEnded(token, leg: 1, found: delivery.value, error) }
                }
            }
            try? await Task.sleep(for: .seconds(Self.meetingSeconds))
            self.endInvitation(token, throwing: GameCenterInviteAnswer.failed)
        }
    }
    private func groupRequest(_ group: UInt32, size: Int) throws -> GKMatchRequest {
        let r = try request(sport: nil, count: size)
        r.playerGroup = Int(group); r.minPlayers = size; r.maxPlayers = size
        return r
    }
    private func retireDoorbells(_ pending: Invitation) {
        for door in pending.doors.values { Task { await retire(door) } }
    }

    /// Friend: this game's doorbells, read while the game is open (every few seconds, and at once on a Game Center turn event).
    /// Old records (builds up to 0.1.5 (5)'s kind, expired ones, and a host's own leftovers) are ended on the way.
    func refreshInvitations() async {
        guard GKLocalPlayer.local.isAuthenticated, UIApplication.shared.applicationState == .active, !refreshingDoorbells else { return }
        refreshingDoorbells = true; defer { refreshingDoorbells = false }
        guard let matches = try? await GKTurnBasedMatch.loadMatches() else { return }
        let now = Date().timeIntervalSince1970 * 1000
        var found: [String: (stored: GKTurnBasedMatch, bell: GameCenterDoorbell)] = [:]
        for stored in matches where stored.status != .ended && !retiring.contains(stored.matchID) {
            guard let data = try? await stored.loadMatchData(), !data.isEmpty,
                  let kind = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["kind"] as? String else { continue }
            if kind == "motionclub.partyInvite.v1" { await retire(stored); continue }
            guard kind == GameCenterDoorbell.kind, let bell = try? JSONDecoder().decode(GameCenterDoorbell.self, from: data) else { continue }
            if bell.expiresAt <= now { await retire(stored); continue }
            guard bell.host != localID, bell.answer == nil, bell.valid(for: localID, now: now),
                  let host = stored.participants.first(where: { $0.player?.gamePlayerID == bell.host && $0.status != .done && $0.status != .declined })?.player,
                  invitationAllowed?(host.gamePlayerID, host.teamPlayerID) != false,
                  let me = stored.participants.first(where: { $0.player?.gamePlayerID == localID }), me.status == .invited || me.status == .active
            else { continue }
            found["gc:" + stored.matchID] = (stored, bell)
        }
        doorbells = found
        let cards = found.map { $0.value.bell.card($0.value.stored.matchID) }.sorted { $0.expiresAt > $1.expiresAt }
        onInvitations?(cards)
        if let opened = openedFromNotification {
            openedFromNotification = nil
            if let card = cards.first(where: { $0.id == opened }) { onInvitationOpened?(card) }
        }
    }
    /// Friend: Join on our banner. Answer on the doorbell, then meet the host in its group.
    func acceptInvitation(_ card: HubInvite) async throws {
        guard let entry = doorbells[card.id], case let (stored, bell) = entry, bell.valid(for: localID, now: Date().timeIntervalSince1970 * 1000),
              let host = stored.participants.first(where: { $0.player?.gamePlayerID == bell.host && $0.status != .done && $0.status != .declined }),
              let hostPlayer = host.player, invitationAllowed?(hostPlayer.gamePlayerID, hostPlayer.teamPlayerID) != false else {
            throw MultiplayerError.unavailable("That invitation has ended. Ask your friend to invite you again.")
        }
        guard canAcceptParty?() != false else { throw MultiplayerError.invalidOperation("Return to the Plaza to join your friend.") }
        generation += 1; let token = generation
        doorbells[card.id] = nil
        if stored.participants.first(where: { $0.player?.gamePlayerID == localID })?.status == .invited { _ = try await stored.acceptInvite() }
        var answer = bell; answer.answer = "join"
        try await stored.endTurn(withNextParticipants: [host], turnTimeout: Self.meetingSeconds, match: JSONEncoder().encode(answer))
        guard token == generation else { throw CancellationError() }
        allowedPartyPlayers = nil
        onJoining?(bell.name)
        let request = try groupRequest(bell.group, size: bell.size)
        let timeout = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(Self.meetingSeconds))
            guard !Task.isCancelled, let self, self.generation == token else { return }
            self.cancelSearch()
        }
        defer { timeout.cancel(); Task { await retire(stored) } }
        let found = try await GKMatchmaker.shared().findMatch(for: request)
        guard token == generation else { found.disconnect(); throw CancellationError() }
        try attachParty(found, host: bell.host)
    }
    /// Friend: Decline. The host's game reads it as "not now".
    func declineInvitation(_ id: String) {
        guard let entry = doorbells.removeValue(forKey: id) else { return }
        Task { await retire(entry.stored) }
    }
    /// Friend: in the host's party by Apple's invitation, so its doorbell is done with. Only hidden here (the host ends it): a
    /// "declined" on it now could reach the host before Apple's "accepted".
    private func forgetInvitations(from host: String) {
        let gone = doorbells.filter { $0.value.bell.host == host }
        guard !gone.isEmpty else { return }
        for (id, entry) in gone { doorbells[id] = nil; retiring.insert(entry.stored.matchID) }
        onInvitations?(doorbells.map { $0.value.bell.card($0.value.stored.matchID) }.sorted { $0.expiresAt > $1.expiresAt })
    }

    /// Retire only this feature's own temporary record (once).
    private func retire(_ stored: GKTurnBasedMatch) async {
        guard retiring.insert(stored.matchID).inserted else { return }
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
    private func attachParty(_ found: GKMatch, host: String) throws {
        if let allowedPartyPlayers, found.players.contains(where: { !allowedPartyPlayers.contains($0.gamePlayerID) }) {
            found.disconnect(); throw MultiplayerError.unavailable("Game Center connected a player outside this invitation. Please try again.")
        }
        if let previous = match, previous !== found { previous.delegate = nil; previous.disconnect() }
        match = found; disconnected.removeAll(); found.delegate = self
        GKMatchmaker.shared().finishMatchmaking(for: found)
        onPartyConnected?(host); onPeersChanged?()
    }
    /// Invitations reach this listener once Game Center has signed the player in (a cold launch from an invitation included).
    private func register() {
        guard GKLocalPlayer.local.isAuthenticated, !registered else { return }
        GKLocalPlayer.local.register(self); registered = true
        let timer = Timer(timeInterval: 5, repeats: true) { [weak self] _ in Task { @MainActor [weak self] in await self?.refreshInvitations() } }
        RunLoop.main.add(timer, forMode: .common); doorbellTimer = timer
        Task { await refreshInvitations() }
    }
    private func request(sport: MultiplayerSport?, count: Int) throws -> GKMatchRequest {
        guard GKLocalPlayer.local.isAuthenticated else { throw MultiplayerError.unavailable("Game Center is not signed in.") }
        guard capacity >= count, count >= 2 else { throw MultiplayerError.unavailable("Game Center cannot connect that many players on this OS.") }
        let request = GKMatchRequest(); request.minPlayers = 2; request.maxPlayers = count; request.defaultNumberOfPlayers = count
        // Stable, versioned queues; private parties are sport-neutral.
        request.playerGroup = sport == .tennis ? 0x4d500201 : sport == .golf ? 0x4d500202 : 0x4d500200
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
        let found = try await GKMatchmaker.shared().findMatch(for: request)
        guard token == generation else { found.disconnect(); throw CancellationError() }
        attach(found)
    }
    func findMore(sport: MultiplayerSport) async throws {
        guard let match, peers.count + 1 < capacity else { throw MultiplayerError.full }
        let request = try request(sport: sport, count: 4)
        try await GKMatchmaker.shared().addPlayers(to: match, matchRequest: request)
        GKMatchmaker.shared().finishMatchmaking(for: match)
    }
    func cancelSearch() {
        generation += 1; GKMatchmaker.shared().cancel(); activeController?.dismiss(animated: true); activeController = nil
        if let pending = invitation { endInvitation(pending.token, throwing: CancellationError()) }
        if match == nil { allowedPartyPlayers = nil }
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
    func disconnect() { cancelSearch(); match?.delegate = nil; match?.disconnect(); match = nil; allowedPartyPlayers = nil; onPeersChanged?() }
    nonisolated func match(_ match: GKMatch, didReceive data: Data, fromRemotePlayer player: GKPlayer) {
        let id = player.gamePlayerID, delivery = GameKitDelivery(value: match)
        Task { @MainActor [weak self] in guard self?.match === delivery.value else { return }; self?.onData?(data, id) }
    }
    nonisolated func match(_ match: GKMatch, player: GKPlayer, didChange state: GKPlayerConnectionState) {
        let delivery = GameKitDelivery(value: match), id = player.gamePlayerID, connected = state == .connected
        Task { @MainActor [weak self] in
            guard let self, self.match === delivery.value else { return }
            if connected, let allowed = self.allowedPartyPlayers, !allowed.contains(id) {
                self.onError?(MultiplayerError.unavailable("An uninvited player tried to join the party.")); self.disconnect(); return
            }
            if connected { self.disconnected.remove(id) } else { self.disconnected.insert(id) }
            self.onPeersChanged?()
        }
    }
    nonisolated func match(_ match: GKMatch, didFailWithError error: Error?) {
        let delivery = GameKitDelivery(value: match)
        Task { @MainActor [weak self] in guard self?.match === delivery.value else { return }; if let error { self?.onError?(error) } }
    }
    nonisolated func match(_ match: GKMatch, shouldReinviteDisconnectedPlayer player: GKPlayer) -> Bool { true }
    nonisolated func player(_ player: GKPlayer, didAccept invite: GKInvite) {
        let delivery = GameKitDelivery(value: invite)
        Task { @MainActor [weak self] in
            guard let self else { return }
            let sender = delivery.value.sender
            guard self.invitationAllowed?(sender.gamePlayerID, sender.teamPlayerID) != false else { return }
            guard self.canAcceptParty?() != false else { self.onError?(MultiplayerError.invalidOperation("Return to the Plaza, then accept your friend's invitation again.")); return }
            self.generation += 1; let token = self.generation
            self.allowedPartyPlayers = nil
            self.onJoining?(sender.displayName)
            do {
                let found = try await GKMatchmaker.shared().match(for: delivery.value)
                guard token == self.generation else { found.disconnect(); return }
                try self.attachParty(found, host: delivery.value.sender.gamePlayerID)
                self.forgetInvitations(from: delivery.value.sender.gamePlayerID)
            } catch { if token == self.generation { self.onError?(error) } }
        }
    }
    /// A doorbell rang (or was answered). Opened from Game Center's notification: that tap is the Join.
    nonisolated func player(_ player: GKPlayer, receivedTurnEventFor match: GKTurnBasedMatch, didBecomeActive: Bool) {
        let id = "gc:" + match.matchID
        Task { @MainActor [weak self] in
            if didBecomeActive { self?.openedFromNotification = id }
            if let token = self?.invitation?.token { await self?.checkDoorbells(token) }
            await self?.refreshInvitations()
        }
    }
    /// Friends picked in Apple's Games app (it opened this game to play with them): invite them as the Friends list would.
    nonisolated func player(_ player: GKPlayer, didRequestMatchWithRecipients recipientPlayers: [GKPlayer]) {
        let delivery = GameKitDelivery(value: recipientPlayers)
        Task { @MainActor [weak self] in self?.onRequestMatch?(delivery.value) }
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
