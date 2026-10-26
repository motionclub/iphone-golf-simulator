import Foundation
import Observation
import UIKit

/// What the hub needs from the lobby and the game, behind a protocol so tests drive it without Game Center or Unity.
@MainActor protocol ClubHubRoom: AnyObject {
    /// This phone is in a friends' party (the lobby that lives on the hub's relay room).
    var inLobby: Bool { get }
    var isHost: Bool { get }
    var partySize: Int { get }
    var capacity: Int { get }
    var sport: String { get }
    /// Host: a party over this relay room (made on the first invite). Any other lobby is left first.
    func hostParty(over transport: MultiplayerTransport) throws
    /// Guest: leave any lobby and join the host's party over this relay room. Returns once the host's lobby is here.
    func joinParty(over transport: MultiplayerTransport, host: String) async throws
    func leaveLobby()
}

extension ClubHubRoom { var isHost: Bool { true } }

/// What the player is doing right now, from the game's own state.
struct ClubHubContext: Equatable {
    var background = false
    var inMatch = false
    /// A match or the plaza is loading, or the arrival fly-in plays: banners wait until it is over.
    var busyLoading = false
    /// First-run onboarding holds the phone: an invite waits until the player reaches the Plaza.
    var onboarding = false
}

/// The online hub (PLAN_OnlineHub_FriendsInvites.md): Game Center friends with online / offline from the Club Hub service,
/// invites that arrive inside the game, a pasted or linked invite code, and the join that follows. One instance for the app.
///
/// Online is Game Center only (2026-10-19): Invite goes through `nativeInvite` (a stored Game Center invitation plus a private
/// Game Center match), the banner's Join through `nativeAccept`, and the party, the Plaza, room changes and chat ride that match.
/// The Club Hub service paths below (presence, relay rooms, share codes) are dormant: a shipped build has no service address
/// (ClubHubConfig.serverURL), so `link` stays `.notConfigured` and nothing here waits for it.
@MainActor @Observable
final class ClubHub {
    static let shared = ClubHub()

    enum Link: Equatable {
        /// No service address in this build: friends show without presence.
        case notConfigured
        case signedOut
        case connecting
        case online
        case offline(String)
    }
    struct Friend: Identifiable, Equatable {
        var id: String
        var name: String
        var online = false
        var state: HubPresenceState?
        var lobby: HubLobbyInfo?
    }
    enum Sent: Equatable {
        case sending, delivered, pushed, queued, accepted, declined, busy, unavailable, expired, cancelled, full
        var text: String {
            switch self {
            case .sending: "Sending…"; case .delivered: "Invite sent! Waiting for them…"; case .pushed: "Notified"; case .queued: "Invited · sees it when they open the game"
            case .accepted: "Joining…"; case .declined: "Said not now"; case .busy: "Busy"; case .unavailable: "Didn't send. Tap Invite again."
            case .expired: "No answer. Tap Invite again."; case .cancelled: "Cancelled"; case .full: "Your party is full"
            }
        }
        /// Still on its way or waiting for an answer (the row offers Cancel).
        var pending: Bool { [.sending, .delivered, .pushed, .queued].contains(self) }
    }

    // MARK: state the screens read
    private(set) var link: Link = .offline("")
    private(set) var access: FriendsAccess = .signedOut
    private(set) var friends: [Friend] = []
    private(set) var recent: [FriendProfile] = []
    /// Invites waiting for an answer, newest first.
    private(set) var invites: [HubInvite] = []
    /// The invite shown as a banner now (nil while none, while held, or once snoozed).
    private(set) var banner: HubInvite?
    private(set) var sent: [String: Sent] = [:]
    private(set) var notice = ""
    /// Joining a friend's game: who, until it connects or fails (or, said while busy, until the player is back in the Plaza).
    private(set) var joining: String?
    enum JoinStage: Equatable {
        /// Join was tapped during a match, a load or onboarding (or from Game Center's notification): it happens in the Plaza.
        case later
        /// Waiting for the host's phone to say go (it may be finishing a match).
        case waiting
        case connecting
    }
    private(set) var joinStage: JoinStage?
    /// A match, a load or onboarding holds banners and the joining pill (nothing pops over a swing or a lesson).
    private(set) var heldForGame = false
    /// A code looked up (pasted or from a link): who invited you.
    private(set) var resolvedInvite: HubInvite?
    var hubOpen = false
    var invisible: Bool { didSet { UserDefaults.standard.set(invisible, forKey: "clubhub.invisible"); publishPresence(force: true) } }
    var doNotDisturb: Bool { didSet { UserDefaults.standard.set(doNotDisturb, forKey: "clubhub.dnd"); publishPresence(force: true); updateBanner() } }
    private(set) var blocked: Set<String>
    /// The party this phone is in (made by the first invite, or joined): its code is the relay room's and what friends and share
    /// links use. (`group` stays in the protocol for older builds; it is 0.)
    private(set) var party: (code: String, group: UInt32)?
    /// The party's relay room (nil with no party).
    @ObservationIgnored private(set) var relayRoom: HubRoomTransport?
    /// My id on the service (the Game Center teamPlayerID).
    var selfID: String { you.isEmpty ? source.localID : you }
    @ObservationIgnored private var you = ""

    var unreadInvites: Int { invites.count }
    var onlineFriends: [Friend] { friends.filter { $0.online && !blocked.contains($0.id) }.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending } }
    var offlineFriends: [Friend] { friends.filter { !$0.online && !blocked.contains($0.id) }.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending } }
    var blockedFriends: [Friend] { friends.filter { blocked.contains($0.id) } }
    var recentNotFriends: [FriendProfile] { recent.filter { r in !friends.contains { $0.id == r.id } } }
    /// The words for sharing this party's code (a link when the service has a landing page).
    var shareText: String? { party.map { ClubHubConfig.shareMessage(code: $0.code, from: source.localName, sport: room.sport) } }

    // MARK: dependencies
    @ObservationIgnored let source: FriendsSource
    @ObservationIgnored let room: ClubHubRoom
    /// Apple's CloudKit: who is online, drop-in, codes and our own notifications (off until the build has the capability).
    let cloud: ClubCloud
    /// Friends' online state is known (the Club Hub service, or CloudKit).
    var presenceOn: Bool { link == .online || cloud.on }
    @ObservationIgnored var makeTransport: @MainActor () -> HubTransport
    @ObservationIgnored var serverURL: @MainActor () -> URL?
    @ObservationIgnored var devAuth: @MainActor () -> Bool
    @ObservationIgnored var context: @MainActor () -> ClubHubContext = { ClubHubContext() }
    @ObservationIgnored var playerName: @MainActor () -> String = { "Player" }
    /// Milliseconds since 1970 (a test moves it).
    @ObservationIgnored var now: @MainActor () -> Double = { Date().timeIntervalSince1970 * 1000 }
    @ObservationIgnored var tvToast: @MainActor (String) -> Void = { _ in }
    @ObservationIgnored var haptic: @MainActor () -> Void = {}
    @ObservationIgnored var pushToken: (token: String, env: String)?
    @ObservationIgnored var friendInParty: @MainActor (String) -> Bool = { id in MultiplayerService.shared.isParty && MultiplayerService.shared.lobby?.participants.contains { $0.id == id } == true }
    /// Stops the Game Center join in progress (and tells the host).
    @ObservationIgnored var nativeCancel: @MainActor () -> Void = {}
    /// Takes back the Game Center invitation to this friend.
    @ObservationIgnored var nativeCancelInvite: (@MainActor (String) -> Void)?
    /// An invite back into the party this phone dropped out of (accepted by itself), and forgetting that party once the player
    /// chooses another.
    @ObservationIgnored var isRejoin: @MainActor (HubInvite) -> Bool = { _ in false }
    @ObservationIgnored var forgetParty: @MainActor () -> Void = {}
    /// The invite being joined, or waiting to be joined in the Plaza.
    @ObservationIgnored private var joinTarget: String?
    @ObservationIgnored var autoOpenLobby = false
    @ObservationIgnored var nativeInvite: (@MainActor (String) async throws -> Void)?
    @ObservationIgnored var nativeAccept: (@MainActor (HubInvite) async throws -> Void)?
    @ObservationIgnored var nativeDecline: (@MainActor (String) -> Void)?
    @ObservationIgnored var nativeRefresh: (@MainActor () async -> Void)?
    @ObservationIgnored private var nativeJoining = false
    var canInvite: Bool { link == .online || (access != .signedOut && nativeInvite != nil) }
    @ObservationIgnored var requestPushPermission: @MainActor () -> Void = {}

    // MARK: private
    @ObservationIgnored private var transport: HubTransport?
    @ObservationIgnored private var connectionID = 0
    @ObservationIgnored private var helloSent = false
    @ObservationIgnored private var backoff = 1.0
    @ObservationIgnored private var reconnect: Task<Void, Never>?
    @ObservationIgnored private var clockOffset = 0.0
    @ObservationIgnored private var lastPresence: HubPresence?
    @ObservationIgnored private var lastPresenceSent = 0.0
    @ObservationIgnored private var snoozed: Set<String> = []
    @ObservationIgnored private var ticker: Task<Void, Never>?
    @ObservationIgnored private var outgoing: [String: String] = [:]   // inviteID -> friend id
    @ObservationIgnored private var joinTask: Task<Void, Never>?
    @ObservationIgnored private var pendingResponse: (inviteID: String, accept: Bool)?
    @ObservationIgnored private var pendingAccept: HubInvite?
    @ObservationIgnored private var askedPush = false
    @ObservationIgnored private var started = false
    @ObservationIgnored private var cloudTicks = 0
    /// The service closed this connection because another phone took the player's place (4409).
    @ObservationIgnored private var replaced = false

    init(source: FriendsSource? = nil, room: ClubHubRoom? = nil, makeTransport: (@MainActor () -> HubTransport)? = nil,
         serverURL: (@MainActor () -> URL?)? = nil, devAuth: (@MainActor () -> Bool)? = nil, cloud: ClubCloud? = nil) {
        self.cloud = cloud ?? ClubCloud(store: ClubCloud.liveStore())
        self.source = source ?? GameKitFriendsSource()
        self.room = room ?? MultiplayerRoom()
        self.makeTransport = makeTransport ?? { WebSocketHubTransport() }
        self.serverURL = serverURL ?? { ClubHubConfig.serverURL }
        self.devAuth = devAuth ?? { ClubHubConfig.devAuth }
        invisible = UserDefaults.standard.bool(forKey: "clubhub.invisible")
        doNotDisturb = UserDefaults.standard.bool(forKey: "clubhub.dnd")
        blocked = Set(UserDefaults.standard.stringArray(forKey: "clubhub.blocked") ?? [])
    }

    // MARK: lifecycle

    /// The app is active (or the hub opened): read the friends and go online. Safe to call again.
    func start() {
        started = true; replaced = false
        cloud.start()
        if ticker == nil {
            ticker = Task { @MainActor [weak self] in
                while !Task.isCancelled { try? await Task.sleep(for: .seconds(1)); self?.tick() }
            }
        }
        Task { await refresh() }
    }

    /// Back to the foreground, or the hub opened: friends and recents again (a friend accepted in Apple's screen shows up).
    func refresh() async {
        await nativeRefresh?()
        access = await source.access()
        if access == .authorized {
            if let list = try? await source.friends() { applyFriends(list) }
            recent = (try? await source.recent()) ?? recent
        }
        connectIfPossible()
        await refreshCloudFriends()
    }

    /// Who is online and whose party has room, from CloudKit (when the Club Hub service is not the one saying so).
    func refreshCloudFriends() async {
        guard cloud.on, link != .online else { return }
        let states = await cloud.friends(friends.map(\.id))
        for i in friends.indices {
            let s = states[friends[i].id]
            friends[i].online = s?.online ?? false; friends[i].state = s?.online == true ? s?.state : nil; friends[i].lobby = s?.lobby
        }
    }

    /// The hub asks the system for the friends list (Apple's prompt, the first time).
    func allowFriends() async {
        if let list = try? await source.friends() { applyFriends(list) }
        await refresh()
    }

    /// The Friends list opened: the one moment we ask to show notifications ("so you know when a friend invites you"), once.
    func friendsOpened() {
        guard !askedPush else { return }
        askedPush = true; requestPushPermission()
    }

    func addFriend() {
        do { try source.presentAddFriend() } catch { say(error.localizedDescription) }
    }

    private func applyFriends(_ list: [FriendProfile]) {
        let old = Dictionary(uniqueKeysWithValues: friends.map { ($0.id, $0) })
        friends = list.map { p in var f = old[p.id] ?? Friend(id: p.id, name: p.name); f.name = p.name; return f }
        if helloSent { send(HubClientMessage.friends(list.map(\.id))) }
    }

    func background() {
        if cloud.on { Task { await cloud.publish(force: true) } }
        guard link == .online else { return }
        publishPresence(force: true)
    }

    /// Back in the foreground after `seconds` in the background. iOS closes a suspended app's sockets without telling it, so after
    /// a few seconds the connection is opened afresh at once (not after the backoff): the welcome rejoins this phone's party room,
    /// so the party is still there when you come back (AwayPolicy).
    func returned(after seconds: TimeInterval) {
        guard started, seconds >= AwayPolicy.staleLinkSeconds, !replaced else { return }
        reconnect?.cancel(); backoff = 1
        if transport != nil { connectionID += 1; transport?.close(); transport = nil; helloSent = false }
        connectIfPossible()
    }

    // MARK: connection

    private func connectIfPossible() {
        guard started, transport == nil, !replaced else { return }
        guard source.localID.isEmpty == false, access != .signedOut else { link = .signedOut; return }
        guard serverURL() != nil else { link = .notConfigured; return }
        connect()
    }

    private func connect() {
        guard let url = serverURL() else { link = .notConfigured; return }
        link = .connecting; helloSent = false
        connectionID += 1; let id = connectionID
        let t = makeTransport(); transport = t
        t.onOpen = { [weak self] in
            guard let self, self.connectionID == id else { return }
            Task { await self.sendHello(id) }
        }
        t.onMessage = { [weak self] data in
            guard let self, self.connectionID == id else { return }
            self.receive(data)
        }
        t.onClose = { [weak self] code in
            guard let self, self.connectionID == id else { return }
            self.closed(code)
        }
        t.connect(url)
    }

    private func sendHello(_ id: Int) async {
        let auth: HubClientMessage.Auth
        if devAuth() { auth = .dev(source.localID) }
        else {
            do { auth = try await source.identity() }
            catch { if connectionID == id { link = .offline(error.localizedDescription); transport?.close(); transport = nil; scheduleReconnect() }; return }
        }
        guard connectionID == id, let transport else { return }
        let presence = currentPresence()
        lastPresence = presence; lastPresenceSent = now()
        transport.send(HubClientMessage.hello(auth: auth, name: playerName(), friends: friends.map(\.id), presence: presence, push: pushToken))
        helloSent = true
    }

    private func closed(_ code: Int?) {
        transport = nil; helloSent = false
        for i in friends.indices { friends[i].online = false; friends[i].state = nil; friends[i].lobby = nil }
        switch code {
        case 4401:
            link = .offline("The Club Hub could not verify you. Open Game Center and sign in again.")
        case 4409:
            // another phone signed in as this player: do not fight it for the connection (until the app is opened again)
            link = .offline("You are signed in on another device."); replaced = true; return
        default:
            link = .offline("")
        }
        // an invite stays valid on the service for its two minutes; the list is what this phone knew
        scheduleReconnect()
    }

    private func scheduleReconnect() {
        reconnect?.cancel()
        let delay = backoff; backoff = min(30, backoff * 2)
        reconnect = Task { @MainActor [weak self] in
            try? await Task.sleep(for: .seconds(delay))
            guard let self, !Task.isCancelled, self.transport == nil else { return }
            self.connectIfPossible()
        }
    }

    func disconnect() {
        reconnect?.cancel()
        if helloSent { transport?.send(HubClientMessage.bye) }
        connectionID += 1; transport?.close(); transport = nil; helloSent = false
        link = serverURL() == nil ? .notConfigured : .offline("")
    }

    private func send(_ data: Data) { if helloSent { transport?.send(data) } }

    // MARK: presence

    func currentPresence() -> HubPresence {
        let c = context()
        let state: HubPresenceState = c.background ? .away : doNotDisturb ? .dnd : c.inMatch ? .match : room.inLobby ? .lobby : .plaza
        var lobby: HubLobbyInfo?
        if let party, room.inLobby, room.isHost { lobby = HubLobbyInfo(code: party.code, sport: room.sport, size: room.partySize, capacity: 4, open: !c.inMatch && !c.background && !doNotDisturb && room.partySize < 4, group: party.group) }
        return HubPresence(state: state, lobby: lobby, invisible: invisible)
    }

    /// Sends my state if it changed, or as the heartbeat (at least every 20 s).
    func publishPresence(force: Bool = false) {
        if cloud.on { Task { await cloud.publish(force: force) } }
        guard helloSent else { return }
        let p = currentPresence()
        if !force, p == lastPresence, now() - lastPresenceSent < 20_000 { return }
        lastPresence = p; lastPresenceSent = now()
        send(HubClientMessage.presence(p))
    }

    // MARK: messages

    func receive(_ data: Data) {
        guard let message = HubServerMessage.decode(data) else { return }
        switch message {
        case .welcome(let id, let serverTime):
            link = .online; backoff = 1
            if !id.isEmpty { you = id }
            if serverTime > 0 { clockOffset = serverTime - now() }
            if let pending = pendingResponse { pendingResponse = nil; send(HubClientMessage.inviteResponse(pending.inviteID, accept: pending.accept)) }
            // back after a dropped connection: into the party's room again (the opener re-opens it if the service lost it)
            if let r = relayRoom, !r.closed { send(r.opener ? HubClientMessage.roomOpen(r.code) : HubClientMessage.roomJoin(r.code)) }
            if autoOpenLobby, party == nil, !room.inLobby, !context().inMatch, joining == nil { _ = ensureParty(); publishPresence(force: true) }
            if let p = pendingAccept { if expired(p) { pendingAccept = nil; joining = nil; say("That invite has ended.") } else { accept(p) } }
        case .presence(let id, let online, let state, let lobby, let name):
            guard let i = friends.firstIndex(where: { $0.id == id }) else {
                if online { friends.append(Friend(id: id, name: name ?? "Friend", online: true, state: state, lobby: lobby)) }
                return
            }
            if let name, !name.isEmpty { friends[i].name = name }
            friends[i].online = online; friends[i].state = online ? state : nil; friends[i].lobby = online ? lobby : nil
        case .invite(let invite): received(invite)
        case .inviteUpdate(let inviteID, let status, let to): updated(inviteID, status, to: to)
        case .inviteGone(let inviteID, _): remove(inviteID)
        case .resolved(let code, let found, let from, let sport, let group, let capacity):
            guard found, let from, let group else { say("That invite has ended."); resolvedInvite = nil; return }
            resolvedInvite = HubInvite(inviteID: "code-" + code, from: from, sport: sport ?? "tennis", lobbyCode: code, group: group,
                                       capacity: capacity ?? 2, expiresAt: now() + 120_000)
        case .roomPeers(let code, let peers):
            if let r = relayRoom, r.code == code { r.roomPeers(peers) }
        case .relay(let code, let from, let text):
            if let r = relayRoom, r.code == code { r.received(text, from: from) }
        case .error(let code, let text, let ref):
            if code.hasPrefix("room_") {
                // about the party's room: the host's is reopened at once if it went (the service restarted); a guest is refused.
                // (A late one about a room already left is nobody's business.)
                if let r = relayRoom, r.code == ref || ref == "rd" {
                    if r.opener, code == "room_gone" { send(HubClientMessage.roomOpen(r.code)); return }
                    r.refused(code, message: text)
                }
                return
            }
            switch code {
            case "rate_limited": say("Slow down a moment.")
            case "not_friends": say("You can invite friends who also have you as a friend in Game Center.")
            case "blocked": break
            default: if !text.isEmpty { say(text) }
            }
        case .pong, .unknown: break
        }
    }

    // MARK: invites you receive

    private func received(_ invite: HubInvite) {
        guard !blocked.contains(invite.from.id) else { return }
        invites.removeAll { $0.inviteID == invite.inviteID || $0.from.id == invite.from.id }   // the newest from one friend replaces the older
        invites.insert(invite, at: 0)
        if !context().inMatch {
            haptic()
            if !doNotDisturb { tvToast(invite.id.hasPrefix("gc:") ? "\(invite.from.name) wants to play! Tap Join on your phone" : "\(invite.from.name) invited you · \(invite.sportTitle) · accept on your phone") }
        }
        updateBanner()
    }
    /// Reconcile Game Center's inbox without replaying haptics or unsnoozing a
    /// card on every poll. The existing banner and Friends inbox use one model.
    func gameCenterInvitations(_ cards: [HubInvite]) {
        let ids = Set(cards.map(\.id))
        invites.removeAll { $0.id.hasPrefix("gc:") && !ids.contains($0.id) }
        for card in cards.reversed() where !invites.contains(where: { $0.id == card.id }) { received(card) }
        updateBanner()
        // dropped out of a party: its leader's invite back is accepted by itself (in the Plaza; it waits through a match)
        if joinTarget == nil, let back = cards.first(where: { isRejoin($0) && !expired($0) }) { accept(back) }
    }
    func gameCenterInvitationSent(to id: String, match: String = "", players: Int = 2) {
        if sent[id] == .sending { sent[id] = .delivered }
        // our own notification on the friend's phone, with Join (Game Center's own may be late or missing)
        if !match.isEmpty { cloud.notifyInvite(to: id, gcMatch: match, players: players) }
    }
    /// Host: what became of a Game Center invitation (the friend's id).
    func gameCenterOutgoing(to id: String, _ status: GameCenterTransport.Outgoing) {
        let name = friends.first { $0.id == id }?.name ?? "Your friend"
        switch status {
        case .joining: sent[id] = .accepted
        case .waiting: if sent[id] == nil { sent[id] = .accepted }   // (the friend's phone asks again by itself)
        case .joined:
            sent[id] = nil; haptic()
            say("\(name) joined your party!"); tvToast("\(name) joined your party!")
        case .declined: sent[id] = .declined
        case .expired: sent[id] = .expired
        case .full: sent[id] = .full; say("Your party is full, so \(name) couldn't join.")
        }
    }
    /// Friend: where the Game Center join is.
    func gameCenterJoinStage(_ stage: GameCenterTransport.JoinStage) {
        guard nativeJoining else { return }
        joinStage = stage == .connecting ? .connecting : .waiting
    }

    private func updated(_ inviteID: String, _ status: String, to: String?) {
        // the sender learns an invite's id from the first update, which names the friend it was for
        if let to { outgoing[inviteID] = to }
        guard let friend = outgoing[inviteID] else { return }
        let next: Sent?
        switch status {
        case "delivered": next = .delivered; case "pushed": next = .pushed; case "queued": next = .queued; case "accepted": next = .accepted
        case "declined": next = .declined; case "busy": next = .busy; case "unavailable": next = .unavailable
        case "expired": next = .expired; case "cancelled": next = .cancelled; default: next = nil
        }
        guard let next else { return }
        sent[friend] = next
        if [.declined, .busy, .unavailable, .expired, .cancelled].contains(next) { outgoing[inviteID] = nil }
    }

    private func remove(_ inviteID: String) {
        invites.removeAll { $0.inviteID == inviteID }
        snoozed.remove(inviteID)
        updateBanner()
    }

    /// Banner rules: held while a match or a load is on (a swing is never interrupted), when Do Not Disturb is on, or in the
    /// background; never shown once snoozed (it stays in the hub); shows the newest.
    func updateBanner() {
        let c = context()
        heldForGame = c.inMatch || c.busyLoading || c.onboarding
        if heldForGame || c.background || doNotDisturb { banner = nil }
        else { banner = invites.first { !snoozed.contains($0.inviteID) && !expired($0) && $0.inviteID != joinTarget } }
        joinWhenReady()
    }

    /// The phone is in the Plaza (or the phone-only Plaza): not a match, a load, onboarding or the background.
    var canJoinNow: Bool { let c = context(); return !c.inMatch && !c.busyLoading && !c.onboarding && !c.background }

    func expired(_ invite: HubInvite) -> Bool { invite.expiresAt <= now() + (invite.id.hasPrefix("gc:") ? 0 : clockOffset) }
    /// Fraction of the invite's time left (the banner's countdown: 15 minutes for Game Center, 2 for the Club Hub).
    func remaining(_ invite: HubInvite) -> Double {
        let gc = invite.id.hasPrefix("gc:")
        return max(0, min(1, (invite.expiresAt - now() - (gc ? 0 : clockOffset)) / (gc ? GameCenterPartyInvitation.lifetime : 120_000)))
    }

    /// Not now: off the banner, still in the hub until it expires.
    func snooze(_ invite: HubInvite) { snoozed.insert(invite.inviteID); updateBanner() }

    func decline(_ invite: HubInvite) {
        if invite.id.hasPrefix("gc:") {
            if joinTarget == invite.id { cancelJoin(); return }
            nativeDecline?(invite.id); remove(invite.id); return
        }
        send(HubClientMessage.inviteResponse(invite.inviteID, accept: false))
        remove(invite.inviteID)
    }

    /// Join (one tap on the banner): say yes to the service, then enter the host's party room. The phone stays where it is (the
    /// Plaza's controller); the friend appears in your Plaza and you in theirs. In a party of your own you leave it first.
    ///
    /// A Game Center invite is never refused for being on the wrong screen: Join said during a match, a load or onboarding (or by
    /// tapping Game Center's notification) is kept, and the join starts by itself the moment the player is back in the Plaza.
    func accept(_ invite: HubInvite) {
        guard !expired(invite), !blocked.contains(invite.from.id) else { say("That invite has ended. Ask \(invite.from.name) to invite you again."); return }
        if invite.id.hasPrefix("gc:"), nativeAccept != nil {
            guard joinTarget != invite.id else { return }
            if joinTarget != nil { cancelJoin() }   // (Join on another friend's invite: that one wins)
            if !isRejoin(invite) { forgetParty() }
            joinTarget = invite.id; joining = invite.from.name; hubOpen = false; snoozed.remove(invite.id)
            if canJoinNow { startNativeJoin(invite) } else { pendingAccept = invite; joinStage = .later; updateBanner() }
            return
        }
        guard !context().inMatch else { say("Return to the Plaza to join your friend."); return }
        guard joining == nil || pendingAccept?.inviteID == invite.inviteID else { return }
        guard link == .online else {
            // (opened from a notification, or the connection is coming back): join the moment it is up
            pendingAccept = invite; joining = invite.from.name; hubOpen = false; connectIfPossible(); return
        }
        pendingAccept = nil
        resolvedInvite = nil
        if !invite.inviteID.hasPrefix("code-") { send(HubClientMessage.inviteResponse(invite.inviteID, accept: true)) }
        remove(invite.inviteID)
        joining = invite.from.name; hubOpen = false
        tvToast("Joining \(invite.from.name)…")
        joinTask?.cancel()
        joinTask = Task { @MainActor [weak self] in
            guard let self else { return }
            if self.room.inLobby || self.relayRoom != nil { self.leaveParty() }
            let relay = HubRoomTransport(hub: self, code: invite.lobbyCode, opener: false)
            self.relayRoom = relay
            self.send(HubClientMessage.roomJoin(invite.lobbyCode))
            do {
                try await self.room.joinParty(over: relay, host: invite.from.id)
                guard self.relayRoom === relay else { return }
                self.party = (invite.lobbyCode, 0); self.joining = nil
                self.say("You joined \(invite.from.name)'s party"); self.tvToast("You joined \(invite.from.name)'s party")
                self.publishPresence(force: true)
                self.onJoined(invite.from.id)
            } catch {
                if self.relayRoom === relay { self.relayRoom = nil; relay.disconnect() }
                self.joining = nil
                if !(error is CancellationError) { self.say(relay.refusal ?? error.localizedDescription) }
            }
        }
    }

    /// A Join said while busy: it starts here, the moment the player is back in the Plaza (called on every banner update and tick).
    private func joinWhenReady() {
        guard let p = pendingAccept, p.id.hasPrefix("gc:"), !nativeJoining, canJoinNow else { return }
        pendingAccept = nil
        if expired(p) { joinTarget = nil; joining = nil; joinStage = nil; say("That invite has ended. Ask \(p.from.name) to invite you again."); return }
        startNativeJoin(p)
    }

    /// Game Center does the rest (its handshake waits for the host and tries again by itself until the invite runs out). A failure
    /// leaves the card in the inbox and back on the banner, so Join tries again.
    private func startNativeJoin(_ invite: HubInvite) {
        guard let nativeAccept else { return }
        joinTarget = invite.id; joining = invite.from.name; joinStage = .waiting; nativeJoining = true; hubOpen = false
        updateBanner()
        joinTask = Task { @MainActor [weak self] in
            guard let self else { return }
            defer {
                if self.joinTarget == invite.id { self.joinTarget = nil; self.joining = nil; self.joinStage = nil; self.nativeJoining = false }
                self.updateBanner()
            }
            do {
                try await nativeAccept(invite)
                guard !Task.isCancelled else { return }
                self.remove(invite.id)
                self.say("You joined \(invite.from.name)'s party!")
            } catch {
                guard !Task.isCancelled, !(error is CancellationError) else { return }
                self.snoozed.remove(invite.id)
                self.say(error.localizedDescription)
            }
        }
    }

    func cancelJoin() {
        joinTask?.cancel(); joinTask = nil
        if let p = pendingAccept, p.id.hasPrefix("gc:") { nativeDecline?(p.id); remove(p.id) }
        pendingAccept = nil
        if nativeJoining { nativeCancel(); nativeJoining = false; if let t = joinTarget { remove(t) } }
        if party == nil, let r = relayRoom { relayRoom = nil; r.disconnect() }
        joining = nil; joinTarget = nil; joinStage = nil
        updateBanner()
    }
    /// Joined a friend's party (their id): the Plaza takes you to them.
    @ObservationIgnored var onJoined: @MainActor (String) -> Void = { _ in }

    // MARK: invites you send

    /// Invite a friend (one tap, online or offline) to your party, made now if you have none. Online: their game shows the banner at
    /// once. Offline: the service keeps it and they get it the moment they open the game (or a notification, where push is set up).
    func invite(_ friend: Friend) {
        guard !blocked.contains(friend.id), friend.id != selfID, joining == nil else { return }
        if let nativeInvite, access != .signedOut {
            // several friends at once; the invite waits for each friend's Join (15 minutes), the phone does not
            guard sent[friend.id]?.pending != true, sent[friend.id] != .accepted else { return }
            sent[friend.id] = .sending
            Task { @MainActor in
                do { try await nativeInvite(friend.id); if self.sent[friend.id] == .sending { self.sent[friend.id] = .delivered } }
                catch is CancellationError { if self.sent[friend.id] == .sending { self.sent[friend.id] = nil } }
                catch { if self.sent[friend.id] == .sending { self.sent[friend.id] = .unavailable; self.say(error.localizedDescription) } }
            }
            return
        }
        guard link == .online else { say("Connect to Game Center to invite friends."); connectIfPossible(); return }
        guard let party = ensureParty() else { return }
        sent[friend.id] = .sending
        send(HubClientMessage.invite(to: friend.id, sport: room.sport, lobbyCode: party.code, group: party.group, capacity: room.capacity))
        publishPresence(force: true)
        haptic()
        if !askedPush { askedPush = true; requestPushPermission() }
    }

    func canJoin(_ friend: Friend) -> Bool {
        presenceOn && friend.online && !blocked.contains(friend.id) && friend.id != selfID
            && friend.lobby?.open == true && friend.state != .match && friend.state != .away && friend.state != .dnd
            && (friend.lobby?.size ?? 8) < (friend.lobby?.capacity ?? 8)
    }
    func join(_ friend: Friend) {
        guard canJoin(friend), let lobby = friend.lobby, !context().inMatch else { return }
        if link != .online { hubOpen = false; cloud.join(code: lobby.code); return }
        accept(HubInvite(inviteID: "code-" + lobby.code, from: HubPlayerRef(id: friend.id, name: friend.name),
                         sport: lobby.sport, lobbyCode: lobby.code, group: lobby.group, capacity: lobby.capacity, expiresAt: now() + 120_000))
    }

    /// Someone new (any phone number, app or not): this party's code and Apple's link, in the words texted to them. Nil when
    /// CloudKit is off (then the Club Hub service's share, if any).
    func prepareTextInvite() async -> String? {
        guard cloud.on else { return prepareShare() }
        guard await cloud.shareCode() != nil else { say("Couldn't make an invite. Check the internet and try again."); return nil }
        return cloud.message(from: source.localName.isEmpty ? playerName() : source.localName)
    }

    /// Someone without the app: make the party now and give back the words to send. Nil if it cannot be made.
    func prepareShare() -> String? {
        guard link == .online, let party = ensureParty() else { if link != .online { say("Connect to the Club Hub to share an invite.") }; return nil }
        publishPresence(force: true)
        return ClubHubConfig.shareMessage(code: party.code, from: source.localName, sport: room.sport)
    }

    /// The party to invite to: the one this phone is in, or a new one hosted here over a fresh relay room.
    private func ensureParty() -> (code: String, group: UInt32)? {
        if let party, room.inLobby, let r = relayRoom, !r.closed { return party }
        let code = ClubHubConfig.newCode()
        let relay = HubRoomTransport(hub: self, code: code, opener: true)
        do {
            if relayRoom != nil { leaveParty() }
            relayRoom = relay
            send(HubClientMessage.roomOpen(code))
            try room.hostParty(over: relay)
        } catch {
            if relayRoom === relay { relayRoom = nil; relay.disconnect() }
            say(error.localizedDescription); return nil
        }
        party = (code, 0)
        return party
    }

    func cancelInvite(to friend: Friend) {
        if nativeInvite != nil, access != .signedOut { nativeCancelInvite?(friend.id) }
        for (inviteID, id) in outgoing where id == friend.id { send(HubClientMessage.inviteCancel(inviteID)); outgoing[inviteID] = nil }
        sent[friend.id] = .cancelled
    }

    /// Leave the party (its lobby and its room).
    func leaveParty() {
        let r = relayRoom
        room.leaveLobby()               // (the lobby's transport is the relay: leaving it closes the room too)
        if let r, !r.closed { r.disconnect() }
        partyEnded()
    }

    /// The party ended or everyone left: a new party gets a fresh code.
    func partyEnded() {
        party = nil; sent = [:]; outgoing = [:]
        if let r = relayRoom, r.closed { relayRoom = nil }
        publishPresence(force: true)
    }

    // MARK: the relay (HubRoomTransport's side)

    func relayLive(_ r: HubRoomTransport) -> Bool { relayRoom === r && helloSent }
    func relay(_ code: String, to: [String]?, _ text: String) { send(HubClientMessage.relay(code, to: to, text)) }
    /// The party's transport closed (the lobby was left): leave the room on the service.
    func roomClosed(_ r: HubRoomTransport) {
        send(HubClientMessage.roomLeave(r.code))
        if relayRoom === r { relayRoom = nil; party = nil; sent = [:]; outgoing = [:]; publishPresence(force: true) }
    }

    // MARK: codes and links

    /// A code typed, pasted, or opened from a link: ask the service who it belongs to; the answer is `resolvedInvite`.
    func resolve(_ text: String) {
        if link != .online, cloud.on { hubOpen = false; cloud.join(code: text); return }
        guard let code = ClubHubConfig.normalizedCode(text) else { say("That is not an invite code. It has six letters and numbers."); return }
        guard link == .online else { say("Connect to the Club Hub to use an invite code."); return }
        resolvedInvite = nil
        send(HubClientMessage.resolve(code))
    }

    func open(url: URL) {
        if link != .online, cloud.on, let code = ClubCloud.normalized(url.absoluteString) { cloud.join(code: code); return }
        guard let code = ClubHubConfig.normalizedCode(url.absoluteString) else { return }
        hubOpen = true
        resolve(code)
    }

    // MARK: blocks

    func block(_ friend: Friend) {
        blocked.insert(friend.id); UserDefaults.standard.set(Array(blocked), forKey: "clubhub.blocked")
        send(HubClientMessage.block(friend.id, true))
        invites.removeAll { $0.from.id == friend.id }; updateBanner()
    }
    func unblock(_ friend: Friend) {
        blocked.remove(friend.id); UserDefaults.standard.set(Array(blocked), forKey: "clubhub.blocked")
        send(HubClientMessage.block(friend.id, false))
    }

    // MARK: push

    func setPushToken(_ token: String, env: String) {
        pushToken = (token, env)
        send(HubClientMessage.push(token: token, env: env))
    }

    /// The player tapped a notification (or its Join / Not now): the invite it carried, answered once connected.
    func notification(invite: HubInvite, accept: Bool?) {
        guard !expired(invite) else { say("That invite has ended."); return }
        if invite.id.hasPrefix("gc:") {
            // (a tap on our CloudKit notification is the Join, as a tap on Game Center's own is)
            if accept == false { decline(invite) } else { self.accept(invite) }
            return
        }
        if let accept {
            if accept { self.accept(invite) } else { pendingResponse = (invite.inviteID, false); if helloSent { send(HubClientMessage.inviteResponse(invite.inviteID, accept: false)); pendingResponse = nil } }
        } else {
            invites.removeAll { $0.inviteID == invite.inviteID }; invites.insert(invite, at: 0); snoozed.remove(invite.inviteID); updateBanner()
        }
    }

    // MARK: housekeeping

    func say(_ text: String) { notice = text }
    func clearNotice() { notice = "" }

    private func tick() {
        // expired invites leave; the banner moves on; the heartbeat goes out
        let before = invites.count
        invites.removeAll { expired($0) }
        if invites.count != before || banner != nil || !invites.isEmpty { updateBanner() }
        joinWhenReady()
        if link == .online { publishPresence() }
        cloudTicks += 1
        if cloud.on, cloudTicks % 20 == 0 { Task { await refreshCloudFriends() } }
    }

    /// Tests: one tick without waiting a second.
    func debugTick() { tick() }
    /// Tests: forget everything (the shared instance is reused between tests).
    func debugReset() {
        disconnect(); ticker?.cancel(); ticker = nil; started = false; joinTask?.cancel(); cloud.stop(); cloud.cancelKnock()
        friends = []; invites = []; banner = nil; sent = [:]; outgoing = [:]; notice = ""; joining = nil; resolvedInvite = nil
        joinTarget = nil; joinStage = nil; nativeJoining = false; heldForGame = false
        party = nil; relayRoom = nil; snoozed = []; pendingResponse = nil; pendingAccept = nil; askedPush = false; hubOpen = false; you = ""
    }
}
