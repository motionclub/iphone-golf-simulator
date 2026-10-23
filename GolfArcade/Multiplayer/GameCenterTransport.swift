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

/// Game Center connection behind the in-app friends list. Invitations are Apple's own (GKMatchRequest.recipients): Game Center
/// delivers them, the friend's tap joins through `player(_:didAccept:)`, and neither phone shows a matchmaking screen.
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
    /// The invitation waiting for answers: whom, and the call to finish (once).
    private struct Invitation { let token: Int; let players: [GKPlayer]; var waiting: Set<String>; var accepted = false; let done: CheckedContinuation<Void, Error> }
    private var invitation: Invitation?
    static let invitationSeconds = 100.0
    private var clearedStored = false
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

    /// Invite friends to this phone's party (made now if there is none). Game Center delivers Apple's invitation: a banner while
    /// the friend is in the game, a notification otherwise. Returns once an invited friend is in the party; throws their answer
    /// (GameCenterInviteAnswer) when nobody comes, or CancellationError after `cancelSearch`.
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
        try await withCheckedThrowingContinuation { (done: CheckedContinuation<Void, Error>) in
            invitation = Invitation(token: token, players: players, waiting: Set(players.map(\.gamePlayerID)), done: done)
            if let match {
                GKMatchmaker.shared().addPlayers(to: match, matchRequest: request) { @Sendable error in
                    Task { @MainActor [weak self] in self?.invitationEnded(token, found: nil, error) }
                }
            } else {
                GKMatchmaker.shared().findMatch(for: request) { @Sendable found, error in
                    let delivery = GameKitDelivery(value: found)
                    Task { @MainActor [weak self] in self?.invitationEnded(token, found: delivery.value, error) }
                }
            }
            for player in players { onInvitationSent?(player.teamPlayerID) }
            Task { @MainActor [weak self] in
                try? await Task.sleep(for: .seconds(Self.invitationSeconds))
                self?.endInvitation(token, throwing: GameCenterInviteAnswer.noAnswer)
            }
        }
    }
    /// A friend answered. Accepted: Game Center finishes the match. Anything else: that friend is out, and with nobody left to
    /// come the invitation ends with their answer.
    private func answered(_ id: String, _ response: GKInviteRecipientResponse) {
        guard var pending = invitation, pending.waiting.contains(id) else { return }
        if response == .accepted { pending.accepted = true; invitation = pending; return }
        pending.waiting.remove(id); invitation = pending
        if pending.waiting.isEmpty, !pending.accepted { endInvitation(pending.token, throwing: GameCenterInviteAnswer(response)) }
    }
    /// Game Center's matchmaking call came back: the party is on (or bigger), or it failed.
    private func invitationEnded(_ token: Int, found: GKMatch?, _ error: Error?) {
        guard let pending = invitation, pending.token == token else { found?.disconnect(); return }
        invitation = nil
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
        invitation = nil
        if match == nil { GKMatchmaker.shared().cancel() }
        else { for player in pending.players { GKMatchmaker.shared().cancelPendingInvite(to: player) } }
        pending.done.resume(throwing: error)
    }

    /// Builds up to 0.1.5 (4) kept each invitation as a turn-based record. End this game's own leftovers once a launch, so they do
    /// not sit in the Games app as open turns.
    private func clearStoredInvitations() {
        guard !clearedStored else { return }
        clearedStored = true
        Task { @MainActor [weak self] in
            guard let matches = try? await GKTurnBasedMatch.loadMatches() else { return }
            for stored in matches {
                guard let data = try? await stored.loadMatchData(),
                      (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["kind"] as? String == "motionclub.partyInvite.v1" else { continue }
                await self?.retire(stored)
            }
        }
    }

    /// Retire only this feature's own temporary record.
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
        clearStoredInvitations()
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
            } catch { if token == self.generation { self.onError?(error) } }
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
