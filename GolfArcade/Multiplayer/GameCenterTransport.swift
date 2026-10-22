@preconcurrency import GameKit
import UIKit

private struct GameKitDelivery<T>: @unchecked Sendable { let value: T }

/// Game Center stores the invitation; the real-time match still carries the party.
/// A tagged turn-based record provides a readable inbox without a separate server.
struct GameCenterPartyInvitation: Codable, Equatable {
    var kind = "motionclub.partyInvite.v1"
    var host: String
    var recipient: String
    var name: String
    var group: UInt32
    var players: [String]
    var expiresAt: Double
    func valid(for local: String, now: Double) -> Bool {
        kind == "motionclub.partyInvite.v1" && recipient == local && host != local && !host.isEmpty
        && group >= 0x60000000 && group < 0x70000000 && (2...4).contains(players.count)
        && Set(players).count == players.count && players.contains(host) && players.contains(local)
        && expiresAt.isFinite && expiresAt > now && expiresAt <= now + 125_000
    }
    func card(_ matchID: String) -> HubInvite {
        HubInvite(inviteID: "gc:" + matchID, from: HubPlayerRef(id: host, name: name), sport: "party",
                  lobbyCode: matchID, group: group, capacity: players.count, expiresAt: expiresAt)
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
    override init() { super.init(); register() }
    var capacity: Int { min(4, GKMatchRequest.maxPlayersAllowedForMatch(of: .peerToPeer)) }

    private var authenticationWaiters: [CheckedContinuation<Void, Error>] = []
    private var authenticationPresenter: ((UIViewController) -> Void)?
    private var authenticationController: UIViewController?
    var onAuthenticationController: ((UIViewController) -> Void)?
    var onAuthenticationChanged: (() -> Void)?
    var onPartyConnected: ((String) -> Void)?
    var canAcceptParty: (() -> Bool)?
    var onInvitations: (([HubInvite]) -> Void)?
    var onInvitationSent: ((String) -> Void)?
    var invitationAllowed: ((String, String) -> Bool)?
    /// The player tapped Game Center's notification for this invitation: that tap is the Join (no second tap on our banner).
    var onInvitationOpened: ((HubInvite) -> Void)?
    private var openedFromNotification: String?
    private var inbox: [String: GKTurnBasedMatch] = [:]
    private var inboxTimer: Timer?
    private var refreshingInbox = false
    private var outgoingInvitation: GKTurnBasedMatch?
    private var partyGroup: UInt32?
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

    /// Apple's stored invitation inbox is polled while active and refreshed on turn
    /// events. Accepting joins a private real-time playerGroup, with the inviter host.
    func invite(_ player: GKPlayer) async throws {
        guard peers.count + 2 <= capacity else { throw MultiplayerError.full }
        let group = partyGroup ?? UInt32.random(in: 0x60000000..<0x70000000)
        let members = Array(Set([localID, player.gamePlayerID] + peers)).sorted()
        let invitation = GameCenterPartyInvitation(host: localID, recipient: player.gamePlayerID,
            name: GKLocalPlayer.local.displayName, group: group, players: members,
            expiresAt: Date().timeIntervalSince1970 * 1000 + 120_000)
        let storedRequest = try request(sport: nil, count: 2)
        storedRequest.playerGroup = Int(group); storedRequest.recipients = [player]
        storedRequest.inviteMessage = "Join my Motion Club lobby"
        generation += 1; let token = generation
        let stored = try await GKTurnBasedMatch.find(for: storedRequest)
        guard token == generation else { await retire(stored); throw CancellationError() }
        outgoingInvitation = stored
        let next = stored.participants.filter { $0.player?.gamePlayerID != localID }
        guard !next.isEmpty, stored.currentParticipant?.player?.gamePlayerID == localID else {
            outgoingInvitation = nil; await retire(stored)
            throw MultiplayerError.unavailable("Game Center could not create the invitation. Try again.")
        }
        let data = try JSONEncoder().encode(invitation)
        do { try await stored.endTurn(withNextParticipants: next, turnTimeout: 120, match: data) }
        catch { outgoingInvitation = nil; await retire(stored); throw error }
        guard token == generation else { await retire(stored); throw CancellationError() }
        onInvitationSent?(player.teamPlayerID)
        let request = try privateRequest(group: group, count: members.count)
        allowedPartyPlayers = Set(members); partyGroup = group
        let timeout = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(120))
            guard !Task.isCancelled, let self, self.generation == token else { return }
            self.cancelSearch()
        }
        defer { timeout.cancel(); if outgoingInvitation === stored { outgoingInvitation = nil }; Task { await retire(stored) } }
        if let match {
            try await GKMatchmaker.shared().addPlayers(to: match, matchRequest: request)
            guard token == generation else { throw CancellationError() }
            GKMatchmaker.shared().finishMatchmaking(for: match)
        } else {
            let found = try await GKMatchmaker.shared().findMatch(for: request)
            guard token == generation else { found.disconnect(); throw CancellationError() }
            try attachParty(found, host: localID)
        }
    }
    private func privateRequest(group: UInt32, count: Int) throws -> GKMatchRequest {
        let r = try request(sport: nil, count: count)
        r.playerGroup = Int(group); r.minPlayers = count; r.maxPlayers = count
        return r
    }

    func refreshInvitations() async {
        guard GKLocalPlayer.local.isAuthenticated, UIApplication.shared.applicationState == .active, !refreshingInbox else { return }
        refreshingInbox = true; defer { refreshingInbox = false }
        do {
            let matches = try await GKTurnBasedMatch.loadMatches()
            var cards: [HubInvite] = []; var pending: [String: GKTurnBasedMatch] = [:]
            for stored in matches where stored.status != .ended {
                guard let data = try? await stored.loadMatchData(),
                      let invite = try? JSONDecoder().decode(GameCenterPartyInvitation.self, from: data),
                      invite.kind == "motionclub.partyInvite.v1" else { continue }
                let now = Date().timeIntervalSince1970 * 1000
                if invite.expiresAt.isFinite, invite.expiresAt <= now,
                   invite.host == localID || invite.recipient == localID { await retire(stored); continue }
                guard invite.valid(for: localID, now: now),
                      let host = stored.participants.first(where: { $0.player?.gamePlayerID == invite.host && $0.status != .done && $0.status != .declined })?.player,
                      invitationAllowed?(host.gamePlayerID, host.teamPlayerID) != false,
                      let me = stored.participants.first(where: { $0.player?.gamePlayerID == localID }),
                      me.status == .invited || me.status == .active else { continue }
                let card = invite.card(stored.matchID)
                pending[card.id] = stored; cards.append(card)
            }
            inbox = pending; onInvitations?(cards.sorted { $0.expiresAt > $1.expiresAt })
            if let opened = openedFromNotification {
                openedFromNotification = nil
                if let card = cards.first(where: { $0.id == opened }) { onInvitationOpened?(card) }
            }
        } catch { SportsDiagnostics.write("Game Center invite inbox: \(error.localizedDescription)") }
    }

    func acceptStoredInvitation(_ card: HubInvite) async throws {
        guard let stored = inbox[card.id] else { throw MultiplayerError.unavailable("That invitation has ended. Refresh Friends and try again.") }
        guard let data = try? await stored.loadMatchData(),
              let invite = try? JSONDecoder().decode(GameCenterPartyInvitation.self, from: data),
              invite.valid(for: localID, now: Date().timeIntervalSince1970 * 1000),
              let host = stored.participants.first(where: { $0.player?.gamePlayerID == invite.host && $0.status != .done && $0.status != .declined })?.player,
              invitationAllowed?(host.gamePlayerID, host.teamPlayerID) != false else {
            throw MultiplayerError.unavailable("That invitation has ended. Ask your friend to invite you again.")
        }
        guard canAcceptParty?() != false else { throw MultiplayerError.invalidOperation("Return to the Plaza to join your friend.") }
        generation += 1; let token = generation
        if stored.participants.first(where: { $0.player?.gamePlayerID == localID })?.status == .invited { _ = try await stored.acceptInvite() }
        inbox[card.id] = nil
        allowedPartyPlayers = Set(invite.players); partyGroup = invite.group
        let request = try privateRequest(group: invite.group, count: invite.players.count)
        let timeout = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(30))
            guard !Task.isCancelled, let self, self.generation == token else { return }
            self.cancelSearch()
        }
        defer { timeout.cancel(); Task { await retire(stored) } }
        let found = try await GKMatchmaker.shared().findMatch(for: request)
        guard token == generation else { found.disconnect(); throw CancellationError() }
        try attachParty(found, host: invite.host)
    }

    func declineStoredInvitation(_ id: String) {
        guard let stored = inbox.removeValue(forKey: id) else { return }
        Task { await retire(stored) }
    }

    /// Retire only this feature's own temporary record, after a user's invitation action.
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
    private func register() {
        if GKLocalPlayer.local.isAuthenticated && !registered { GKLocalPlayer.local.register(self); registered = true }
        guard inboxTimer == nil else { return }
        let timer = Timer(timeInterval: 4, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in await self?.refreshInvitations() }
        }
        RunLoop.main.add(timer, forMode: .common); inboxTimer = timer
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
        if let stored = outgoingInvitation { outgoingInvitation = nil; Task { await retire(stored) } }
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
            guard self.canAcceptParty?() != false else { self.onError?(MultiplayerError.invalidOperation("Return to the Plaza, then accept your friend's invitation again.")); return }
            self.generation += 1; let token = self.generation
            self.allowedPartyPlayers = nil; self.partyGroup = nil
            do {
                let found = try await GKMatchmaker.shared().match(for: delivery.value)
                guard token == self.generation else { found.disconnect(); return }
                try self.attachParty(found, host: delivery.value.sender.gamePlayerID)
            } catch { if token == self.generation { self.onError?(error) } }
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
