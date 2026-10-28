import Foundation
import Observation
import UIKit
import GameKit

/// Public integration surface for future UI. Creating the singleton never starts networking.
@MainActor @Observable
final class MultiplayerService {
    static let shared = MultiplayerService()
    private(set) var lobby: MultiplayerLobby?
    private(set) var lastError: String?
    private(set) var searching = false
    private(set) var loadingNeedsDecision = false
    /// The player turned Local Network access off for this app: phones in the same room cannot find each other until they turn it on.
    private(set) var localNetworkDenied = false
    private(set) var discoveredLobbies: [LocalMultiplayerTransport.DiscoveredLobby] = []
    private(set) var roundTrip: Double = 0
    private(set) var emotes: [String: MultiplayerEmote] = [:]
    #if DEBUG
    @ObservationIgnored var proofRecording = false
    @ObservationIgnored private(set) var proofSnapshot: String?
    @ObservationIgnored private var proofPeers: Set<String> = []
    @ObservationIgnored private var proofKinds: Set<String> = []
    #endif
    var onMatchRequested: ((MultiplayerMatchConfiguration) -> Void)?
    /// The Plaza's party traffic (PLAN_MenuHub_WalkableWorld §4): where each friend is and what they do, any phone to all,
    /// only while the lobby is idle. (kind, payload, sender)
    @ObservationIgnored var onHub: ((String, String, String) -> Void)?
    func sendHub(_ kind: String, payload: String, reliable: Bool) {
        guard lobby?.phase == .lobby, ["hubPresence", "hubEvent"].contains(kind), payload.utf8.count <= 2048 else { return }
        try? broadcast(kind, payload: payload, reliable: reliable)
    }
    /// The party channel: typed chat, voice frames and "I am recording" notices between the phones of ONE lobby, in every phase (the lobby,
    /// loading, a match). Only real players of this lobby can send (the receiver checks), nothing is stored here, and nothing is sent to
    /// Unity or any server. (kind, payload, sender)
    @ObservationIgnored var onParty: ((String, String, String) -> Void)?
    static let partyKinds: Set<String> = ["partyChat", "partyVoice"]
    func sendParty(_ kind: String, payload: String, reliable: Bool) {
        guard lobby != nil, !sharedPhoneHost, Self.partyKinds.contains(kind), payload.utf8.count <= 4096 else { return }
        try? broadcast(kind, payload: payload, reliable: reliable)
    }
    /// The other phones in this party (real players, connected), for who can hear and read what you send.
    var partyMembers: [MultiplayerParticipant] { lobby?.participants.filter { !$0.isGuest && $0.id != localID && $0.connected } ?? [] }
    var onReturnToLobby: (() -> Void)?
    /// A party match connected (the host's id): the Plaza takes this phone to them. Nil: the app's HubSession (tests give each phone its own).
    @ObservationIgnored var onJoinedParty: (@MainActor (String) -> Void)?
    var onResult: ((String) -> Void)?
    @ObservationIgnored private var transport: (any MultiplayerTransport)?
    @ObservationIgnored private var gameCenter: GameCenterTransport?
    @ObservationIgnored private var local: LocalMultiplayerTransport?
    @ObservationIgnored private var timer: Timer?
    @ObservationIgnored private var encoder = JSONEncoder()
    @ObservationIgnored private var decoder = JSONDecoder()
    @ObservationIgnored private var sequence: Int64 = 0
    @ObservationIgnored private var seen: [String: Int64] = [:]
    /// The transport's peers at the last change (who is back is told from it).
    @ObservationIgnored private var connectedPeers: Set<String> = []
    @ObservationIgnored private var hello: [String: MultiplayerParticipant] = [:]
    @ObservationIgnored private var disconnected: [String: Double] = [:]
    @ObservationIgnored private var epoch = 0
    @ObservationIgnored private var prepared = false
    @ObservationIgnored private var loadingStarted: Double = 0
    @ObservationIgnored private var presentationReadyAt: [String: Double] = [:]
    private(set) var scheduledRunAt: Double = 0
    @ObservationIgnored private var localLoadReport: String?
    @ObservationIgnored private var localCalibrationReported = false
    @ObservationIgnored private var nextSetupReport: Double = 0
    @ObservationIgnored private var loadReports: [String: String] = [:]
    @ObservationIgnored private var winnerSeat: Int = -1
    @ObservationIgnored private var searchGeneration = 0
    @ObservationIgnored private var matchConfiguration: MultiplayerMatchConfiguration?
    @ObservationIgnored private var quickSport: MultiplayerSport?
    @ObservationIgnored private var clockOffset: Double = 0
    @ObservationIgnored private var clockFilter = ClockFilter()
    @ObservationIgnored private var nextPing: Double = 0
    @ObservationIgnored private var nextHello: Double = 0
    // Noticing a player who goes quiet without Apple (or Wi-Fi) reporting a disconnect.
    @ObservationIgnored private var lastHeard: [String: Double] = [:]
    @ObservationIgnored private var silent: [String: Int] = [:]
    @ObservationIgnored private var nextHeartbeat: Double = 0
    @ObservationIgnored private var silenceArmedAt: Double = .infinity
    /// Guests: when the host's phone went missing mid-match (it may only be out of the app).
    @ObservationIgnored private var ownerMissingSince: Double?
    @ObservationIgnored private var stats = NetStats()
    // Connection check before a tennis match: the guest grades its own pings and reports to the owner, who starts only when every
    // guest's connection has been steady (see LinkWindow). `requiresStableLink` is off only in tests about something else.
    var requiresStableLink = true
    private(set) var linkNeedsDecision = false
    @ObservationIgnored private var linkWindow = LinkWindow()
    @ObservationIgnored private var nextLinkReport: Double = 0
    @ObservationIgnored private var linkSteadySince: [String: Double] = [:]
    @ObservationIgnored private var linkHeardAt: [String: Double] = [:]
    @ObservationIgnored private var linkWaitingSince: Double?
    @ObservationIgnored private var linkOverride = false
    // Tennis setup between loading and play: when it began, whether the "still waiting" note went out, and which competitors
    // reloaded mid-match (play stays paused for them until they point their phone at the TV again).
    @ObservationIgnored private var calibrationStarted: Double = 0
    @ObservationIgnored private var calibrationNoticed = false
    @ObservationIgnored private var awaitingCalibration: Set<String> = []
    /// Kinds Apple refused to send unreliably (too big): sent reliably from then on.
    @ObservationIgnored private var unreliableRefused: Set<String> = []
    @ObservationIgnored private var rate: [String: (Double, Int)] = [:]
    @ObservationIgnored private var name = "Player"
    @ObservationIgnored private var hasScreen = false
    @ObservationIgnored private var female = false
    @ObservationIgnored private var left = false
    @ObservationIgnored private var loadout: MultiplayerLoadout?
    @ObservationIgnored private var lastLook: [String: Double] = [:]
    @ObservationIgnored private var lastEmote: [String: Double] = [:]
    @ObservationIgnored private var localEmoteAt = -Double.infinity
    @ObservationIgnored private let runtimeSend: @MainActor (String) -> Bool
    @ObservationIgnored private let runtimePoll: @MainActor () -> String?
    @ObservationIgnored private let runtimeClear: @MainActor () -> Void
    @ObservationIgnored private let clock: @MainActor () -> Double
    var localID: String { transport?.localID ?? "" }
    var isOwner: Bool { lobby?.ownerID == localID && !localID.isEmpty }
    var localSeat: Int { lobby?.participants.first { $0.id == localID }?.seat ?? -1 }
    private var now: Double { clock() }
    var networkTime: Double { now + (isOwner ? 0 : clockOffset) }
    var emoteCooldown: Double { max(0, MultiplayerEmote.cooldown - (now - localEmoteAt)) }
    @ObservationIgnored private var sharedPhoneHost = false
    /// Joining a friend's party: this phone must not elect itself owner while the invited host's lobby is on its way.
    @ObservationIgnored private var expectingHost: String?
    /// A friends' party over the Club Hub relay (invited from the Friends list), not a quick match or a nearby lobby.
    private var nativeParty = false
    /// Leader handed the party to this player: their lobby is the party's from now on.
    @ObservationIgnored private var promotedTo: (lobbyID: String, to: String)?
    /// Leader: party members whose phone dropped (they did not leave), since when. The party link brings them back by itself.
    @ObservationIgnored private var dropped: [String: Double] = [:]
    var isParty: Bool { transport is any PartyTransport || (nativeParty && transport === gameCenter) }
    var hasFriendsInLobby: Bool { lobby?.participants.contains { !$0.isGuest && $0.id != localID } ?? false }
    /// Phones connected to this party that its lobby does not list yet (they are still joining: their hello or the lobby is on its way).
    var joiningPeers: Int {
        guard let transport else { return 0 }
        let listed = Set(lobby?.participants.map(\.id) ?? [])
        return transport.peers.filter { !listed.contains($0) }.count
    }
    var isNearby: Bool { (local != nil || sharedPhoneHost) && transport != nil }
    var localJoinCode: String? { isNearby && isOwner ? local?.joinCode : nil }
    func joinLocal(code: String) throws {
        let clean = code.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        let matches = discoveredLobbies.filter { LocalMultiplayerTransport.joinCode(for: $0.id.components(separatedBy: "~").last ?? "") == clean }
        guard clean.count == 6, matches.count == 1, let item = matches.first else {
            throw MultiplayerError.invalidOperation("Lobby not found. Check the six-character code and keep both phones close together.")
        }
        try joinLocal(item)
    }
    func addLocalGuest() throws {
        try requireOwnerIdle()
        guard isNearby, lobby?.sport == .golf else { throw MultiplayerError.invalidOperation("Shared-phone guests are available in local golf.") }
        let number = (1...4).first { n in !lobby!.participants.contains { $0.name == "Guest \(n)" } } ?? 4
        let palette = ["F4A65A", "78C5E8", "C997DF", "8AD0AD", "F19DAB", "F5DD7C"]
        let used = Set(lobby!.participants.compactMap { $0.loadout?.colours["shirt"] })
        let shirt = palette.filter { !used.contains($0) }.randomElement() ?? palette[0]
        let shorts = ["23344D", "F0E2CC", "425D4D"].randomElement()!
        let skin = ["F2D0AF", "D5A17C", "A8704E", "754B37"].randomElement()!
        let look = MultiplayerLoadout(skinHex: skin, colours: ["shirt":shirt,"shorts":shorts], emotes: EmoteCatalog.defaults, shirtHex:shirt, shortsHex:shorts)
        try lobby?.add(MultiplayerParticipant(id: UUID().uuidString, name: "Guest \(number)", ready: true, female: Bool.random(), loadout:look, controllerID:localID))
        publishLobby()
    }
    func removeLocalGuest() throws {
        try requireOwnerIdle()
        guard let index = lobby?.participants.lastIndex(where: { $0.controllerID == localID }) else { return }
        lobby?.participants.remove(at:index); lobby?.revision += 1; publishLobby()
    }
    var authenticated: Bool { GKLocalPlayer.local.isAuthenticated }
    func clearError() { lastError = nil }

    init(sendToRuntime: @escaping @MainActor (String) -> Bool = { SportsRuntime.shared().pushNetwork($0) },
         pollRuntime: @escaping @MainActor () -> String? = { SportsRuntime.shared().pollNetwork() },
         clearRuntime: @escaping @MainActor () -> Void = { SportsRuntime.shared().clearNetwork() },
         clock: @escaping @MainActor () -> Double = { ProcessInfo.processInfo.systemUptime }) {
        self.runtimeSend = sendToRuntime; self.runtimePoll = pollRuntime; self.runtimeClear = clearRuntime; self.clock = clock
    }
    /// Shared host path also permits an injected transport for protocol verification. `quick`: as hostLocal's.
    func host(using connection: any MultiplayerTransport, sharedPhone: Bool = false, quick: MultiplayerSport? = nil) throws {
        guard transport == nil, !searching else { throw MultiplayerError.invalidOperation("Leave the current lobby first.") }
        sharedPhoneHost = sharedPhone; quickSport = quick; bind(connection); createLobby(owner: localID)
    }
    func connect(using connection: any MultiplayerTransport, quick: MultiplayerSport? = nil) throws {
        guard transport == nil, !searching else { throw MultiplayerError.invalidOperation("Leave the current lobby first.") }
        quickSport = quick; bind(connection)
    }
    /// Register invitation/lifecycle listeners without presenting authentication or matchmaking UI.
    func prepare() {
        guard !prepared, !ProcessInfo.processInfo.arguments.contains("--lobby-mock") else { return }; prepared = true
        _ = ensureGameCenter()
        NotificationCenter.default.addObserver(forName: UIApplication.didEnterBackgroundNotification, object: nil, queue: .main) { [weak self] _ in Task { @MainActor in self?.setForeground(false) } }
        NotificationCenter.default.addObserver(forName: UIApplication.didBecomeActiveNotification, object: nil, queue: .main) { [weak self] _ in
            // (back in the app: a party match that died in the background meets again now, and a friend who tapped Join while this
            // phone was away is brought in now, not at the next poll)
            Task { @MainActor in self?.setForeground(true); self?.gameCenter?.appBecameActive(); await self?.gameCenter?.refreshInvitations() }
        }
    }
    func createOnlineLobby() throws {
        guard transport == nil, !searching else { throw MultiplayerError.invalidOperation("Already in a lobby.") }
        local?.disconnect(); local = nil; discoveredLobbies = []
        let gc=ensureGameCenter()
        guard GKLocalPlayer.local.isAuthenticated else { throw MultiplayerError.unavailable("Sign in to Game Center first.") }
        bind(gc); createLobby(owner: localID)
    }
    func setIdentity(name: String, female: Bool = false, left: Bool = false, loadout: MultiplayerLoadout? = nil) {
        guard loadout?.valid() ?? true else { return }
        self.name = String(name.prefix(40)); self.female = female; self.left = left; self.loadout = loadout
        if lobby?.phase == .lobby { try? updateLook(loadout, name: self.name, female: female, left: left) }
        else if lobby == nil, transport != nil { try? broadcast("hello", payload: json(identity())) }
    }
    /// This phone gained or lost a TV or Mac. Tennis needs one on at least one of its two players' phones, and the lobby shows who has it.
    func setScreen(_ connected: Bool) {
        guard connected != hasScreen else { return }
        hasScreen = connected
        if lobby != nil { try? sendControl("display", payload: connected ? "true" : "false") }
        else if transport != nil { try? broadcast("hello", payload: json(identity())) }
    }
    /// The host explicitly confirms that both people can see the same TV.
    func setSharedScreen(_ shared: Bool) throws {
        try requireOwnerIdle()
        lobby?.sharedScreen = shared; lobby?.revision += 1; publishLobby()
    }
    var startCountdown: Int? {
        guard lobby?.sport == .tennis, lobby?.phase == .playing, scheduledRunAt > networkTime,
              scheduledRunAt - networkTime <= 3 else { return nil }
        return max(1, Int(ceil(scheduledRunAt - networkTime)))
    }
    /// The phone with the TV tells the lobby how late its picture is, so the other player's swings are judged against the same picture.
    func setScreenDelay(_ seconds: Double) {
        guard lobby != nil, seconds.isFinite else { return }
        try? sendControl("screenDelay", payload: String(seconds))
    }
    func updateLook(_ look: MultiplayerLoadout?, name: String? = nil, female: Bool? = nil, left: Bool? = nil) throws {
        guard lobby?.phase == .lobby, look?.valid() ?? true else { throw MultiplayerError.invalidOperation("Change clothes between matches.") }
        let update = MultiplayerLookUpdate(participantID: localID, name: name, female: female, left: left, loadout: look)
        try sendControl("look", payload: json(update))
        self.loadout = look
        if let name { self.name = String(name.prefix(40)) }; if let female { self.female = female }; if let left { self.left = left }
    }
    /// Local response is immediate; the owner confirms the timestamp and rebroadcasts the same event id.
    func playEmote(_ id: String) throws {
        guard lobby?.phase == .lobby, MultiplayerEmote.ids.contains(id) else { throw MultiplayerError.invalidOperation("Emotes are available in the lobby.") }
        guard emoteCooldown == 0 else { throw MultiplayerError.invalidOperation("Wait a moment before the next emote.") }
        let event = MultiplayerEmote(participantID: localID, emoteID: id, startedAt: networkTime, eventID: UUID().uuidString)
        try sendControl("emote", payload: json(event))
        if !isOwner { emotes[localID] = event }
        localEmoteAt = now
    }
    func authenticate(present: @escaping (UIViewController) -> Void) async throws {
        let gc = ensureGameCenter(); try await gc.authenticate(present: present)
    }
    private func ensureGameCenter() -> GameCenterTransport {
        if let gameCenter { return gameCenter }
        let gc = GameCenterTransport(); gameCenter = gc
        return wire(gc)
    }
    #if DEBUG
    /// Tests: this service's Game Center transport (two phones in one process), wired as the app wires its own.
    func debugUseGameCenter(_ gc: GameCenterTransport) { gameCenter = gc; _ = wire(gc) }
    /// Tests: every leave() that had something to leave, with its reason.
    @ObservationIgnored private(set) var debugLeaves: [String] = []
    #endif
    private func wire(_ gc: GameCenterTransport) -> GameCenterTransport {
        gc.onInvitations = { ClubHub.shared.gameCenterInvitations($0) }
        gc.onInvitationSent = { ClubHub.shared.gameCenterInvitationSent(to: $0, match: $1, players: $2) }
        gc.onInvitationOpened = { ClubHub.shared.accept($0) }
        gc.onOutgoing = { ClubHub.shared.gameCenterOutgoing(to: $0, $1) }
        gc.onSharePlayInvited = { ClubHub.shared.say("\($0) from your call is invited. They tap Join to come in.") }
        gc.onJoinStage = { ClubHub.shared.gameCenterJoinStage($0) }
        gc.joinAvailable = { ClubHub.shared.canJoinNow }
        // A friend tapped Join: bring them in when this phone is in the Plaza. Never while this phone is a guest in another party
        // (its own invitations are void then); later while it is joining someone, searching, in another kind of lobby or a match.
        gc.hostAvailable = { [weak self, weak gc] in
            guard let self, let gc else { return nil }
            if self.transport === gc && self.isParty && !self.isOwner { return nil }
            if gc.joining || self.searching || ClubHub.shared.cloud.knocking != nil { return false }
            if self.transport != nil && !(self.transport === gc && self.isParty) { return false }
            return ClubHub.shared.canJoinNow
        }
        gc.inConnectedParty = { [weak self] in self?.inConnectedParty ?? false }
        gc.partyInLobby = { [weak self, weak gc] in
            guard let self, let gc else { return false }
            return self.transport === gc && self.nativeParty && self.lobby != nil
        }
        // the leader never came back (gone longer than a party waits): back to the Plaza on this phone's own
        gc.onPartyLost = { [weak self] name in
            guard let self else { return }
            self.leave("\(name)'s party never came back")
            self.lastError = "Lost the connection to \(name)'s party."; ClubHub.shared.say("Lost the connection to \(name)'s party.")
        }
        gc.onLinkNotice = { ClubHub.shared.say($0) }
        gc.invitationAllowed = { gameID, teamID in
            !ClubHub.shared.blocked.contains(gameID) && !ClubHub.shared.blocked.contains(teamID)
            && !PartySafety.shared.isBlocked(gameID) && !PartySafety.shared.isBlocked(teamID)
        }
        gc.onConnected = { [weak self, weak gc] in if let gc { self?.nativeParty = false; self?.bind(gc) } }
        // Going into a friend's party: the one you go into wins over the one you are in. Not for a join nobody tapped (a rejoin, a
        // resumed or crossed join): that one never leaves a party with friends connected (it used to, every time: cause 1, 10-26).
        gc.canAcceptParty = { [weak self] automatic in
            guard let self, !SportsSession.shared.active else { return false }
            if automatic && self.inConnectedParty { return false }
            if self.transport != nil || self.searching { self.cancelSearch(); self.leave("going into a friend's party\(automatic ? " (automatic)" : "")") }
            return true
        }
        gc.onAuthenticationController = { ClubSignIn.offer($0) }
        gc.onError = { [weak self] error in self?.lastError = error.localizedDescription; ClubHub.shared.say(error.localizedDescription) }
        gc.onAuthenticationChanged = { ClubSignIn.authenticationFinished(); Task { @MainActor in await ClubHub.shared.refresh() } }
        gc.onPartyConnected = { [weak self, weak gc] host in
            guard let self, let gc else { return }
            // The same party back after its match was lost (the background, Wi-Fi, Apple's error 4): the lobby, the Plaza and a match in
            // progress carry on; hellos and the lobby go round again.
            if self.transport === gc, self.nativeParty, let lobby = self.lobby, lobby.ownerID == host {
                SportsDiagnostics.write("multiplayer: party back together (\(lobby.participants.count) in the lobby, \(lobby.phase.rawValue))")
                self.bind(gc); return
            }
            if self.transport !== gc { self.leave("party match connected over Game Center, another lobby goes") }
            self.nativeParty = true; self.quickSport = nil; self.expectingHost = host
            self.bind(gc)
            // The host keeps the party it leads: binding has just sent that lobby to the friend, and a second, new lobby made here was
            // refused by the friend's phone (another lobby id), so it never got the party, Plaza or Ready (10-27 harness: every party
            // that dropped and formed again).
            if host == self.localID, !(self.lobby.map { $0.ownerID == host && $0.phase == .lobby } ?? false) { self.createLobby(owner: host) }
            if let joined = self.onJoinedParty { joined(host) } else { HubSession.shared.joinedParty(host: host) }
            ClubHub.shared.hubOpen = false
        }
        return gc
    }
    func acceptGameCenterInvitation(_ invite: HubInvite) async throws {
        guard !SportsSession.shared.active else { throw MultiplayerError.invalidOperation("Return to the Plaza to join your friend.") }
        let gc = ensureGameCenter()
        // (opened from the invite's notification: Game Center may still be signing in)
        try await gc.untilSignedIn()
        TennisMenu.shared.online.identity(TennisMenu.shared)
        setScreen(SportsSession.shared.displayConnected)
        try await gc.acceptStoredInvitation(invite)
    }
    /// In a lobby with other phones connected now: an automatic join never takes this phone out of it.
    var inConnectedParty: Bool { lobby != nil && !(transport?.peers.isEmpty ?? true) }
    func declineGameCenterInvitation(_ invite: String) { ensureGameCenter().declineStoredInvitation(invite) }
    func cancelGameCenterJoin() { gameCenter?.cancelJoin() }
    /// Everyone on this phone's FaceTime call can join the party (SharePlay); stops when the party is left.
    func startSharePlay() throws {
        guard !SportsSession.shared.active else { throw MultiplayerError.invalidOperation("Return to the Plaza first.") }
        let gc = ensureGameCenter()
        if transport != nil && !(transport === gc && isParty && isOwner) { throw MultiplayerError.invalidOperation("Only the party leader can invite people.") }
        gc.startSharePlay()
    }
    var sharePlayOn: Bool { gameCenter?.sharing ?? false }

    // MARK: CloudKit drop-in and codes (ClubCloud): the same private Game Center match, met through a knock instead of an invite
    /// This phone's party for someone knocking: its group, its size with them in, and capacity. Nil while it is a guest elsewhere or
    /// in a quick match or nearby lobby.
    func cloudHostParty() -> (group: UInt32, size: Int, capacity: Int)? {
        guard GKLocalPlayer.local.isAuthenticated else { return nil }
        let gc = ensureGameCenter()
        if transport != nil && !(transport === gc && isParty && isOwner) { return nil }
        if gc.joining { return nil }   // (going into someone else's party: none of its own to offer)
        return (gc.hostGroup(), gc.peers.count + 2, gc.capacity)
    }
    /// Host: someone who knocked can be let in now (not joining anyone, in the Plaza).
    var canLetIn: Bool {
        guard let gc = gameCenter, !gc.joining else { return false }
        return gc.hostAvailable?() == true
    }
    /// Joiner: a knock on `host`'s party starts (it stops a Join from an invitation). Nil: not now.
    func beginKnock(host: String, onCancel: @escaping () -> Void) -> Int? { ensureGameCenter().beginKnockJoin(host: host, onCancel: onCancel) }
    func endKnock(_ token: Int) { gameCenter?.endKnock(token) }
    func letIn(_ gameID: String, group: UInt32, players: Int) async throws {
        let gc = ensureGameCenter()
        if transport === gc { try? broadcast("partyAdmission", payload: gameID) }
        try await gc.letIn(gameID, group: group, players: players)
    }
    func joinGroup(host: String, group: UInt32, players: Int) async throws {
        guard !SportsSession.shared.active else { throw MultiplayerError.invalidOperation("Return to the Plaza to join your friend.") }
        TennisMenu.shared.online.identity(TennisMenu.shared)
        setScreen(SportsSession.shared.displayConnected)
        forgetParty()
        let gc = ensureGameCenter()
        if transport != nil || searching { cancelSearch(); leave() }   // (one party at a time: the one you are going into wins)
        try await gc.joinGroup(host: host, group: group, players: players)
    }
    func cancelGameCenterInvite(_ player: GKPlayer) { gameCenter?.cancelInvite(player.gamePlayerID) }
    func refreshGameCenterInvitations() async { await ensureGameCenter().refreshInvitations() }
    func inviteGameCenterFriend(_ player: GKPlayer) async throws {
        guard !SportsSession.shared.active else { throw MultiplayerError.invalidOperation("Return to the Plaza before inviting a friend.") }
        let gc = ensureGameCenter()
        if transport != nil && transport !== gc { throw MultiplayerError.invalidOperation("Leave your current party before starting a Game Center party.") }
        if transport === gc && !isParty { throw MultiplayerError.invalidOperation("Leave quick match before inviting a friend.") }
        if transport === gc && !isOwner { throw MultiplayerError.invalidOperation("The party host can invite more friends.") }
        if transport === gc { try broadcast("partyAdmission", payload: player.gamePlayerID) }
        try await gc.invite(player)
    }
    // MARK: friends' parties (the Club Hub relay: invites from the Friends list, no Game Center screen at any step)

    /// Host a friends' party over this relay room (made by the first invite). Any other lobby is left first.
    func hostParty(over connection: any MultiplayerTransport) throws {
        if transport != nil || searching { cancelSearch(); leave() }
        local?.disconnect(); local = nil; discoveredLobbies = []
        bind(connection); createLobby(owner: localID)
    }
    /// Join a friend's party over this relay room (an invite accepted with one tap). Waits up to 10 s for the host's lobby, and
    /// leaves again if it is not the invited host's.
    func joinParty(over connection: any MultiplayerTransport, host: String) async throws {
        if transport != nil || searching { cancelSearch(); leave() }
        local?.disconnect(); local = nil; discoveredLobbies = []
        expectingHost = host
        defer { if transport === connection { expectingHost = nil } }
        bind(connection)
        let deadline = now + 10
        while now < deadline, lobby == nil, transport === connection {
            if let relay = connection as? HubRoomTransport, relay.entered == false { break }
            try await Task.sleep(for: .milliseconds(50))
        }
        guard transport === connection else { throw CancellationError() }
        guard lobby?.ownerID == host else {
            let why = (connection as? HubRoomTransport)?.refusal
            leave(); throw MultiplayerError.unavailable(why ?? "Could not reach your friend's party. Ask them to invite you again.")
        }
    }
    func quickMatch(_ sport: MultiplayerSport, golfPlayers: Int = 4) async throws {
        guard transport == nil, !searching else { throw MultiplayerError.invalidOperation("Leave the current lobby first.") }
        guard gameCenter?.joining != true else { throw MultiplayerError.invalidOperation("Finish joining your friend first.") }
        guard sport != .tennis || hasScreen else {
            throw MultiplayerError.unavailable("Connect your TV with AirPlay before finding an online tennis opponent. Sharing a TV? Choose Local Tennis.")
        }
        searching = true; quickSport = sport
        searchGeneration += 1; let operation = searchGeneration
        defer { if operation == searchGeneration { searching = false } }
        do { try await ensureGameCenter().quickMatch(sport: sport, count: golfPlayers) }
        catch { if operation == searchGeneration { quickSport = nil; lastError = error.localizedDescription }; throw error }
    }
    func cancelSearch() { searchGeneration += 1; gameCenter?.cancelSearch(); searching = false; if transport == nil { quickSport = nil } }
    /// `quick`: a lobby for that sport that readies itself and starts as soon as it can (two phones playing tennis in one room).
    func hostLocal(name: String = "Friends", quick: MultiplayerSport? = nil) throws {
        guard transport == nil, !searching else { throw MultiplayerError.invalidOperation("Leave the current lobby first.") }
        local?.disconnect()
        let lan = LocalMultiplayerTransport(); local = lan; bind(lan)
        quickSport = quick
        do { try lan.host(name: name); createLobby(owner: localID) }
        catch { leave(); throw error }
    }
    /// `quiet`: the Plaza looking for nearby games in the background (the join banner). Its errors are not the player's business:
    /// only a refused Local Network permission is noted (and the browse stops).
    func browseLocal(quiet: Bool = false) {
        guard transport == nil else { return }
        let lan = local ?? LocalMultiplayerTransport(); local = lan
        lan.onError = { [weak self] error in
            guard let self else { return }
            if !quiet { self.localTransportError(error); return }
            self.noteLocalNetwork(error); if self.localNetworkDenied, self.transport == nil { self.local?.disconnect(); self.local = nil }
        }
        lan.onDiscovery = { [weak self] in self?.discoveredLobbies = $0; if !$0.isEmpty { self?.localNetworkDenied = false } }; lan.browse()
    }
    func stopBrowsing() { if transport == nil { local?.disconnect(); local = nil; discoveredLobbies = []; localNetworkDenied = false } }
    private func localTransportError(_ error: Error) { noteLocalNetwork(error); lastError = error.localizedDescription }
    private func noteLocalNetwork(_ error: Error) { if let e = error as? MultiplayerError, case .localNetworkDenied = e { localNetworkDenied = true } }
    func swapSeat(_ incoming: String, with outgoing: String) throws {
        try requireOwnerIdle()
        guard var state = lobby, let seat = state.participants.first(where: { $0.id == outgoing })?.seat,
              seat >= 0, state.participants.contains(where: { $0.id == incoming && $0.seat == -1 }) else { throw MultiplayerError.invalidOperation("Choose a spectator and a playing seat.") }
        try state.assign(outgoing, seat: -1); try state.assign(incoming, seat: seat); lobby = state; publishLobby()
    }
    func requestReturnToLobby() throws {
        guard lobby?.phase == .results || lobby?.phase == .interrupted else { throw MultiplayerError.invalidOperation("The match must finish first.") }
        if isOwner { try returnToLobby() } else { try sendControl("return") }
    }
    /// Joining a tennis lobby readies you at once: there is nothing to choose, the host starts when both phones are in.
    func joinLocal(_ item: LocalMultiplayerTransport.DiscoveredLobby) throws {
        guard transport == nil, !searching else { throw MultiplayerError.invalidOperation("Leave the current lobby first.") }
        let lan = local ?? LocalMultiplayerTransport(); local = lan; bind(lan)
        quickSport = item.sport == MultiplayerSport.tennis.rawValue ? .tennis : item.sport == MultiplayerSport.bowling.rawValue ? .bowling : nil
        do { try lan.join(item) } catch { leave(); throw error }
    }
    func configure(_ sport: MultiplayerSport, venue: String? = nil, sets: Int = 1, games: Int = 3) throws {
        try requireOwnerIdle()
        // golf: the course, played as long as this host last chose (its own holes, 9 or 18, linked on or round again)
        let session = SportsSession.shared
        let venue = sport == .golf ? MultiplayerLobby.golfRound(MultiplayerLobby.golfRoundParts(venue ?? "cliffside").course, holes: session.golfHoles, link: session.golfLinkCourses)
            : sport == .bowling ? (venue.flatMap { BowlingVenueChoice(rawValue: $0)?.rawValue } ?? session.bowlingVenue) : (venue ?? "resort")
        guard MultiplayerLobby.validVenue(venue, sport: sport), (1...3).contains(sets), [1,3,6].contains(games) else { throw MultiplayerError.invalidOperation("Invalid match settings.") }
        if sport != .golf { lobby?.participants.removeAll { $0.isGuest } }
        lobby?.configure(sport: sport, venue: venue)
        lobby?.readyCheck = nil   // (another game: the leader presses Start again)
        for i in lobby!.participants.indices where lobby!.participants[i].isGuest { lobby!.participants[i].ready = true }
        lobby?.sets = sets; lobby?.games = games
        // golf has no round twists (10-27): said on the wire too, so a phone on an earlier build deals none either
        lobby?.twistsOff = sport == .golf ? true : nil
        publishLobby()
    }
    /// Golf's round length: the course's own holes (0), 9 or 18, and whether a longer round goes on into the next courses or
    /// round the same course again; remembered for the next round like the twists. The seats and who is ready stay as they are.
    func setGolfRound(holes: Int, link: Bool) throws {
        try requireOwnerIdle()
        let session = SportsSession.shared
        session.golfHoles = holes; session.golfLinkCourses = link
        guard let l = lobby, l.sport == .golf else { return }
        lobby?.venue = MultiplayerLobby.golfRound(MultiplayerLobby.golfRoundParts(l.venue).course, holes: holes, link: link)
        lobby?.revision += 1; publishLobby()
    }
    func assignSeat(_ player: String, seat: Int) throws { try requireOwnerIdle(); try lobby?.assign(player, seat: seat); publishLobby() }
    /// Host of a friends' party: the competitors are exactly these players (in order, up to the sport's seats); everyone else
    /// watches from the menu. Being ready is the ready check's (`startPartyGame`), never a seat's: a player who loses their seat is
    /// no longer ready. Publishes only when something changed.
    func seatParty(_ ids: [String]) {
        guard isOwner, isParty, var state = lobby, state.phase == .lobby else { return }
        let want = Array(ids.prefix(state.capacity))
        var changed = false
        for i in state.participants.indices where !state.participants[i].isGuest {
            let seat = want.firstIndex(of: state.participants[i].id) ?? -1
            if state.participants[i].seat != seat { state.participants[i].seat = seat; changed = true }
            if seat < 0, state.participants[i].ready { state.participants[i].ready = false; changed = true }
        }
        guard changed else { return }
        state.queue.removeAll(); state.revision += 1; lobby = state; publishLobby()
    }
    /// Leader of a friends' party: play the game that is set up now (its sport, map and settings). Everyone connected takes a seat
    /// (up to the sport's seats, the leader first, then in the order they joined); the leader is ready, and each other player's phone
    /// asks them to tap Ready. The match starts when the last one does.
    func startPartyGame() throws {
        guard isParty, isOwner, var state = lobby, state.phase == .lobby else { throw MultiplayerError.invalidOperation("Only the party leader can start a game.") }
        let players = state.participants.filter { !$0.isGuest && $0.connected }
        guard players.count >= 2 else { throw MultiplayerError.invalidOperation("Invite a friend to play together.") }
        let order = [localID] + players.map(\.id).filter { $0 != localID }
        let seats = Array(order.prefix(state.capacity))
        for i in state.participants.indices where !state.participants[i].isGuest {
            let seat = seats.firstIndex(of: state.participants[i].id) ?? -1
            state.participants[i].seat = seat
            state.participants[i].ready = state.participants[i].id == localID
        }
        // Tennis is played on a TV: a game that could never begin is refused now, in words, instead of a ready check that never ends
        // (10-27 harness: the guest tapped Ready and nothing ever happened).
        guard state.hasScreenForSport else { throw MultiplayerError.invalidOperation(state.startReason) }
        state.queue.removeAll(); state.readyCheck = true; state.revision += 1; lobby = state; publishLobby()
        SportsDiagnostics.write("party game: \(state.sport.rawValue) \(state.venue), ready check for \(seats.count) players")
        advancePhase()
    }
    /// Leader: not this game after all (back to choosing). Nobody is ready any more.
    func cancelPartyGame() {
        guard isParty, isOwner, lobby?.phase == .lobby, lobby?.readyCheck == true else { return }
        lobby?.readyCheck = nil
        for i in lobby!.participants.indices where !lobby!.participants[i].isGuest { lobby!.participants[i].ready = false }
        lobby?.revision += 1; publishLobby()
    }
    /// A party game is waiting for its players to tap Ready.
    var partyReadyCheck: Bool { isParty && lobby?.phase == .lobby && lobby?.readyCheck == true }
    func setReady(_ ready: Bool) throws {
        if ready, onMatchRequested == nil, SportsSession.shared.active { throw MultiplayerError.invalidOperation("Finish the current sport session before becoming ready.") }
        try sendControl("ready", payload: ready ? "true" : "false")
    }
    func queueForNextMatch(_ queue: Bool = true) throws { try sendControl("queue", payload: queue ? "true" : "false") }
    func startMatch() throws {
        try requireOwnerIdle()
        guard onMatchRequested != nil || !SportsSession.shared.active else { throw MultiplayerError.invalidOperation("Finish the current sport session first.") }
        guard let lobby, lobby.canStart else { throw MultiplayerError.invalidOperation(lobby?.startReason ?? "Invite another player to play.") }
        presentationReadyAt.removeAll(); scheduledRunAt = 0; silent.removeAll(); silenceArmedAt = .infinity; stats = NetStats()
        awaitingCalibration.removeAll(); calibrationNoticed = false
        loadReports.removeAll()
        linkSteadySince.removeAll(); linkHeardAt.removeAll(); linkWaitingSince = nil; linkOverride = false; linkNeedsDecision = false
        assignViews()
        let id = UUID().uuidString
        self.lobby?.matchID = id; self.lobby?.phase = .loading; self.lobby?.readyCheck = nil; emotes.removeAll()
        loadingStarted = now; loadingNeedsDecision = false; winnerSeat = -1; quickSport = nil
        for i in self.lobby!.participants.indices { self.lobby!.participants[i].loaded = false; self.lobby!.participants[i].calibrated = false; self.lobby!.participants[i].setupStep = nil; self.lobby!.participants[i].linkOK = false }
        self.lobby?.revision += 1; publishLobby()
        let config = MultiplayerMatchConfiguration(lobbyID: lobby.id, matchID: id, hostID: localID, localID: "", sport: lobby.sport.rawValue, venue: lobby.venue, sets: lobby.sets, games: lobby.games, seed: Int.random(in: 1...Int(Int32.max)), participants: self.lobby!.participants, twistsOff: lobby.twistsOff)
        let payload = try json(config)
        try broadcast("launch", payload: payload); launch(payload)
    }
    func rematch() throws {
        guard isOwner, lobby?.phase == .results,
              (lobby?.competitors.filter(\.connected).count ?? 0) >= 2 else {
            throw MultiplayerError.invalidOperation("The host can rematch after the result with at least two connected competitors.")
        }
        try returnToLobby(rotateSeats: false, rematching: true)
        for i in lobby!.participants.indices {
            lobby!.participants[i].ready = lobby!.participants[i].connected && lobby!.participants[i].seat >= 0
        }
        try startMatch()
    }
    /// Back to the Plaza from a party's match (any phone, any phase): the owner ends it for everyone, a guest asks the owner.
    func endPartyMatch() {
        guard isParty, let phase = lobby?.phase, phase != .lobby else { return }
        if isOwner { try? returnToLobby(rotateSeats: false) } else { try? sendControl("return") }
    }
    func returnToLobby(rotateSeats: Bool = true, rematching: Bool = false) throws {
        guard isOwner else { throw MultiplayerError.invalidOperation("Only the lobby owner can end the match.") }
        try broadcast("stop", payload: rematching ? "rematch" : ""); stopRuntime(retainDirection: rematching)
        lobby?.phase = .lobby; lobby?.matchID = ""; lobby?.readyCheck = nil
        lobby?.participants.removeAll { !$0.connected }
        let remaining = Set(lobby!.participants.map(\.id))
        lobby?.queue.removeAll { !remaining.contains($0) }
        if rotateSeats && lobby?.sport == .tennis { rotate() }
        for i in lobby!.participants.indices { lobby!.participants[i].ready = lobby!.participants[i].isGuest; lobby!.participants[i].loaded = false; lobby!.participants[i].calibrated = false; lobby!.participants[i].linkOK = false; lobby!.participants[i].view = nil; lobby!.participants[i].screenDelay = nil }
        awaitingCalibration.removeAll(); linkNeedsDecision = false
        lobby?.revision += 1; publishLobby()
    }
    func findMorePlayers() async throws {
        try requireOwnerIdle(); guard !searching, let gc = gameCenter, transport === gc else { throw MultiplayerError.invalidOperation("Public matching needs an idle online lobby.") }
        guard lobby!.participants.count < 4 else { throw MultiplayerError.full }
        lobby?.publicAdmission = true; publishLobby(); searching = true
        searchGeneration += 1; let operation = searchGeneration
        defer { if operation == searchGeneration { searching = false; lobby?.publicAdmission = false; lobby?.revision += 1; publishLobby() } }
        try await gc.findMore(sport: lobby!.sport)
    }
    // MARK: the party leader's tools (a friends' party), and getting back in after a drop

    /// Leader: take a player out of the party. Their phone leaves and says why; they need a new invite to come back.
    func removeFromParty(_ id: String) throws {
        guard isParty, isOwner, lobby?.phase == .lobby, id != localID, lobby?.participants.contains(where: { $0.id == id }) == true else {
            throw MultiplayerError.invalidOperation("Only the party leader can do that, between games.")
        }
        // out of the list first: their phone's own "leave" can arrive while the kick is still being sent
        lobby?.participants.removeAll { $0.id == id }; lobby?.queue.removeAll { $0 == id }
        dropped[id] = nil
        gameCenter?.disallowPartyPlayer(id)
        lobby?.revision += 1; publishLobby()
        try? transmit("kick", to: [id])
    }
    /// Leader: hand the party to another member. Their phone publishes the lobby from now on (the party follows them).
    func makeLeader(_ id: String) throws {
        guard isParty, isOwner, let state = lobby, state.phase == .lobby, id != localID,
              state.participants.contains(where: { $0.id == id && $0.connected && !$0.isGuest }) else {
            throw MultiplayerError.invalidOperation("Only the party leader can do that, between games.")
        }
        try broadcast("promote", payload: id)
        promotedTo = (state.id, id)
        lobby?.ownerID = id   // (this phone is a member now; the new leader's lobby arrives in a moment)
        dropped = [:]
        rememberParty(leader: id, name: state.participants.first { $0.id == id }?.name ?? "")
    }
    /// The party this phone was last in as a member, for 15 minutes: an invite back from its leader is accepted by itself.
    var lastPartyLeader: String? {
        let d = UserDefaults.standard
        guard let id = d.string(forKey: "party.lastLeader"), Date().timeIntervalSince1970 - d.double(forKey: "party.lastLeaderAt") < 15 * 60 else { return nil }
        return id
    }
    private func rememberParty(leader: String, name: String) {
        UserDefaults.standard.set(leader, forKey: "party.lastLeader"); UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: "party.lastLeaderAt")
    }
    /// The player left on purpose, was taken out, or went to another party: no invite back is accepted by itself.
    func forgetParty() { UserDefaults.standard.removeObject(forKey: "party.lastLeader"); gameCenter?.stopSharePlay() }
    /// Leader: a member whose phone dropped (not one who left) keeps their place while the party link brings them back (both phones
    /// meet again in this party's group; until 2026-10-27 the leader sent a rejoin invitation, which raced Apple's own reconnect). A
    /// member gone for longer than a party waits leaves the party list.
    private func pruneDroppedMembers() {
        guard isOwner, isParty, lobby?.phase == .lobby, let gc = gameCenter, transport === gc else { return }
        for (id, at) in dropped where now - at > GameCenterTransport.patience {
            dropped[id] = nil
            lobby?.participants.removeAll { $0.id == id && !$0.connected }; lobby?.revision += 1; publishLobby()
        }
    }

    /// Leaves the lobby (and its connection). `why` and the caller go to SportsDiagnostics.log whenever there was something to leave
    /// (10-27: a joiner dropped 1 s after hello and no line said who hung up).
    func leave(_ why: String = "", file: String = #fileID, line: Int = #line) {
        if transport != nil || lobby != nil {
            #if DEBUG
            debugLeaves.append(why.isEmpty ? "\(file):\(line)" : why)
            #endif
            SportsDiagnostics.write("multiplayer leave (\(lobby.map { "\($0.participants.count) in lobby, \(isOwner ? "owner" : "guest")" } ?? "no lobby"), peers=\(transport?.peers.count ?? 0)) — \(why.isEmpty ? "from \(file):\(line)" : why)")
        }
        sharedPhoneHost = false; nativeParty = false; expectingHost = nil; promotedTo = nil; dropped = [:]
        if transport != nil { try? broadcast("leave") }
        epoch += 1; searchGeneration += 1; timer?.invalidate(); timer = nil; stopRuntime()
        // (a Nearby browse that never became the lobby's transport stops too, rather than running on unowned)
        if let local, (transport as AnyObject?) !== local { local.disconnect() }
        transport?.onPeersChanged = nil; transport?.disconnect(); transport = nil; local = nil; discoveredLobbies = []
        #if DEBUG
        proofPeers.removeAll();proofSnapshot=nil
        #endif
        ownerMissingSince = nil
        loadingNeedsDecision = false; lobby = nil; hello.removeAll(); dropNotes.removeAll(); seen.removeAll(); connectedPeers.removeAll(); disconnected.removeAll(); rate.removeAll(); matchConfiguration = nil; quickSport = nil; searching = false
        lastLook.removeAll(); lastEmote.removeAll(); emotes.removeAll(); localEmoteAt = -Double.infinity; clockOffset = 0; clockFilter = ClockFilter(); nextPing = 0; lastHeard.removeAll(); silent.removeAll(); nextHeartbeat = 0; silenceArmedAt = .infinity
        awaitingCalibration.removeAll(); calibrationNoticed = false; localNetworkDenied = false
        localLoadReport = nil; localCalibrationReported = false; loadReports.removeAll(); scheduledRunAt = 0
        linkWindow = LinkWindow(); nextLinkReport = 0; linkSteadySince.removeAll(); linkHeardAt.removeAll(); linkWaitingSince = nil; linkOverride = false; linkNeedsDecision = false
    }
    private func requireOwnerIdle() throws {
        guard isOwner, lobby?.phase == .lobby else { throw MultiplayerError.invalidOperation("The owner can change this only in the lobby.") }
    }
    private func bind(_ connection: any MultiplayerTransport) {
        if transport === connection { peersChanged(); return }
        // any other kind of lobby (Game Center, a friends' party) ends a background Nearby browse
        if let local, (connection as AnyObject) !== local { local.disconnect(); self.local = nil; discoveredLobbies = [] }
        transport = connection; epoch += 1; let token = epoch
        connection.onData = { [weak self] data, peer in self?.receive(data, from: peer) }
        connection.onPeersChanged = { [weak self] in self?.peersChanged() }
        connection.onError = { [weak self] error in
            guard let self else { return }; self.noteLocalNetwork(error); self.lastError = error.localizedDescription
            if self.matchConfiguration != nil {
                if self.isOwner { self.interrupt(error.localizedDescription) }
                else { try? self.sendControl("availability", payload: "false"); self.stopRuntime() }
            }
        }
        timer?.invalidate(); let t = Timer(timeInterval: 1.0 / 60, repeats: true) { [weak self] _ in MainActor.assumeIsolated { self?.update() } }
        timer = t; RunLoop.main.add(t, forMode: .common); peersChanged()
        // Existing owners respond to hello before the initial deterministic election.
        Task { @MainActor [weak self] in
            try? await Task.sleep(for: .milliseconds(750))
            guard let self, self.epoch == token, self.lobby == nil, self.local == nil, self.expectingHost == nil, let transport = self.transport else { return }
            let owner = ([transport.localID] + transport.peers).sorted().first!
            if owner == self.localID { self.createLobby(owner: owner) }
        }
    }
    private func createLobby(owner: String) {
        var me = identity(); me.seat = 0; lobby = MultiplayerLobby(ownerID: owner, participants: [me])
        lobby?.sharedScreen = isNearby
        for p in hello.values.sorted(by: { $0.id < $1.id }) { try? lobby?.add(p) }
        if let sport = quickSport { lobby?.configure(sport: sport, venue: sport == .golf ? "cliffside" : sport == .bowling ? SportsSession.shared.bowlingVenue : "resort") }
        publishLobby()
        if quickSport != nil { try? setReady(true) }
    }
    private func identity() -> MultiplayerParticipant { MultiplayerParticipant(id: localID, name: name, hasScreen: hasScreen, female: female, left: left, invited: quickSport == nil, loadout: loadout) }
    private func peersChanged() {
        guard let transport else { return }
        // A phone that is back (its match was lost, or its app closed and opened again) numbers its packets from 1 again: what was
        // heard from it before must not drop them as old (a relaunched leader's lobby, a guest's hello and input were all ignored).
        let current = Set(transport.peers)
        for back in current.subtracting(connectedPeers) { seen = seen.filter { !$0.key.hasPrefix(back + ":") } }
        connectedPeers = current
        try? broadcast("hello", payload: (try? json(identity())) ?? "")
        if isOwner {
            for i in lobby!.participants.indices where lobby!.participants[i].id != localID && !lobby!.participants[i].isGuest {
                let id = lobby!.participants[i].id, connected = transport.peers.contains(id)
                #if DEBUG
                if proofPeers.contains(id) { continue }
                #endif
                if !connected && lobby!.participants[i].connected { disconnected[id] = now; lobby!.participants[i].connected = false
                    if isParty { dropped[id] = now }
                    if lobby!.participants[i].seat >= 0 { try? broadcast("suspend", payload: id); pushRuntime("suspend", payload: id) }
                }
                if connected {
                    dropped[id] = nil
                    if disconnected[id] != nil, [.loading,.calibrating,.playing].contains(lobby!.phase) {
                        // A phone whose connection really dropped reloads the game when it comes back, so it is neither loaded nor set up any more.
                        // One that was only quiet or in the background never dropped (it is still marked connected) and keeps its state.
                        if !lobby!.participants[i].connected { lobby!.participants[i].loaded = false; lobby!.participants[i].calibrated = false; lobby!.participants[i].linkOK = false; linkSteadySince[id] = nil }
                    }
                    else { disconnected.removeValue(forKey: id) }
                    lobby!.participants[i].connected = true
                }
            }
            lobby?.revision += 1; publishLobby()
            if lobby?.readyCheck == true, lobby?.phase == .lobby { partyReadyAdvance() }
        } else if let owner = lobby?.ownerID, !transport.peers.contains(owner) {
            SportsDiagnostics.write("multiplayer: host \(owner.prefix(8)) not connected (phase \(lobby!.phase.rawValue), peers=\(transport.peers.count))")
            // The leader's phone dropped (it did not leave): the party link brings it back, and nobody takes the party over meanwhile
            // (that made two leaders the moment it came back). Mid-match the usual away limit still applies.
            if isParty, let gc = gameCenter, transport === gc, gc.waitingFor(owner) {
                if lobby?.phase == .playing, continuesWhileAway, ownerMissingSince == nil { ownerMissingSince = now }
                return
            }
            if lobby?.phase == .lobby, handOver(from: owner) { return }
            // Mid-match the host may only be out of the app: the match waits for it (update() ends it after awayLimitSeconds).
            if lobby?.phase == .playing, continuesWhileAway { if ownerMissingSince == nil { ownerMissingSince = now }; return }
            lobby?.phase = .interrupted; stopRuntime(); lastError = "The host disconnected. Leave and create a new lobby."
        } else if !isOwner { ownerMissingSince = nil }
    }
    /// The host left an idle lobby: the remaining phone with the lowest id takes it over and publishes it; the others accept that.
    private func handOver(from owner: String) -> Bool {
        guard var state = lobby, let transport else { return false }
        let remaining = state.participants.filter { !$0.isGuest && $0.id != owner && ($0.id == localID || transport.peers.contains($0.id)) }.map(\.id).sorted()
        guard let next = remaining.first, remaining.count >= 1 else { return false }
        if next != localID { return true }   // wait for the successor's lobby
        state.participants.removeAll { $0.id == owner || $0.controllerID == owner }
        state.ownerID = localID; state.queue.removeAll { $0 == owner }
        for i in state.participants.indices { state.participants[i].ready = false }
        state.revision += 1; lobby = state; publishLobby(); lastError = "The host left. You are the host now."
        return true
    }
    /// Diagnostics: why packets were dropped (each reason logged a few times, so the log says what went wrong between two phones).
    @ObservationIgnored private var dropNotes: [String: Int] = [:]
    private func noteDrop(_ reason: String, _ peer: String) {
        let n = dropNotes[reason, default: 0]; dropNotes[reason] = n + 1
        if n < 3 { SportsDiagnostics.write("multiplayer dropped a packet from \(peer.prefix(8)): \(reason)") }
    }
    private func receive(_ data: Data, from peer: String) {
        guard data.count <= MultiplayerPacket.maximumBytes, let transport else { return }
        guard transport.peers.contains(peer) else { noteDrop("not a connected player", peer); return }
        guard var packet = try? decoder.decode(MultiplayerPacket.self, from: data) else { noteDrop("unreadable", peer); return }
        guard packet.version == MultiplayerPacket.version else {
            noteDrop("version \(packet.version), this phone \(MultiplayerPacket.version)", peer)
            lastError = MultiplayerError.incompatible.localizedDescription; return
        }
        let bucket = rate[peer] ?? (now, 0)
        if now - bucket.0 < 1 && bucket.1 >= 180 { return }
        rate[peer] = now - bucket.0 >= 1 ? (now,1) : (bucket.0,bucket.1+1)
        packet.sender = peer
        let key = peer + ":" + packet.kind + ":" + String(packet.reliable)
        guard packet.sequence > (seen[key] ?? -1) else { return }; seen[key] = packet.sequence
        lastHeard[peer] = now
        if silent[peer] != nil { quietPeerHeard(peer) }
        if packet.kind == "hello" {
            guard var p = try? decoder.decode(MultiplayerParticipant.self, from: Data(packet.payload.utf8)) else { noteDrop("unreadable hello", peer); return }
            // a look this build cannot show is left out, never the player (it used to drop the whole hello: they never joined)
            if !(p.loadout?.valid() ?? true) { noteDrop("hello look not valid here", peer); p.loadout = nil }
            p.controllerID = nil; p.id = peer; p.name = String(p.name.prefix(40)); p.seat = -1; p.ready = false; p.loaded = false; p.calibrated = false; p.view = nil; p.screenDelay = nil; p.connected = true; p.invited = !(lobby?.publicAdmission ?? false)
            if hello[peer] == nil { SportsDiagnostics.write("multiplayer hello from \(peer.prefix(8)) (\(isOwner ? "added to the lobby" : "not the host"))") }
            hello[peer] = p
            if isOwner { do {
                try lobby?.add(p); publishLobby()
                if var config=matchConfiguration, [.loading,.calibrating,.playing,.results].contains(lobby!.phase), lobby!.competitors.count >= 2 {
                    config.localID=""; config.participants=lobby!.participants
                    try transmit("launch", payload: json(config), to: [peer])
                }
            } catch { lastError = error.localizedDescription; try? transmit("notice",payload:error.localizedDescription,to:[peer]) } }
            return
        }
        if packet.kind == "lobby" {
            guard var state = try? decoder.decode(MultiplayerLobby.self, from: Data(packet.payload.utf8)) else { noteDrop("unreadable lobby", peer); return }
            if state.sport == .golf { state.venue = MultiplayerLobby.currentGolfVenue(state.venue) }
            // (a handed-over lobby: the old owner is gone and its successor publishes the same lobby with a newer revision)
            let handover = lobby.map { $0.id == state.id && state.revision > $0.revision && !transport.peers.contains($0.ownerID) } ?? false
            // (the leader made this player leader: their lobby wins from now on)
            let promoted = promotedTo.map { $0.lobbyID == state.id && $0.to == peer } ?? false
            // looks this build cannot show are left out, as in a hello: the lobby still counts
            for i in state.participants.indices where !(state.participants[i].loadout?.valid() ?? true) { state.participants[i].loadout = nil }
            guard state.valid() else { noteDrop("lobby not valid here", peer); return }
            guard state.ownerID == peer, expectingHost == nil || expectingHost == peer else { noteDrop("lobby from someone who is not the host", peer); return }
            // (the host this phone just went into, or its party's leader with a new lobby: its app closed and opened again while this
            // phone waited, and the party met again)
            let awaited = expectingHost == peer
            let restarted = isParty && lobby.map { $0.ownerID == peer && $0.id != state.id } == true
            guard lobby == nil || awaited || restarted || handover || promoted || (lobby?.ownerID == peer && lobby?.id == state.id && state.revision > lobby!.revision) else { return }
            if restarted { SportsDiagnostics.write("multiplayer: the leader's new lobby replaces its old one (\(state.participants.count) players)") }
            if lobby == nil { SportsDiagnostics.write("multiplayer lobby from host \(peer.prefix(8)): \(state.participants.count) players") }
            if promoted { promotedTo = nil }
            lobby = state; expectingHost = nil; syncPartyLeader()
            if isParty, !isOwner { rememberParty(leader: state.ownerID, name: state.participants.first { $0.id == state.ownerID }?.name ?? "") }
            if state.phase != .loading { loadingNeedsDecision = false }
            if state.phase != .lobby { emotes.removeAll() }
            if quickSport != nil && state.phase == .lobby && !(state.participants.first { $0.id == localID }?.ready ?? true) { try? setReady(true) }
            return
        }
        guard let state = lobby, packet.lobbyID == state.id else { return }
        if packet.kind == "partyAdmission", peer == state.ownerID, state.phase == .lobby, packet.payload.utf8.count <= 128 {
            gameCenter?.allowPartyPlayer(packet.payload); return
        }
        if packet.kind == "promote", isParty, peer == state.ownerID, state.phase == .lobby, packet.payload.utf8.count <= 128 {
            promotedTo = (state.id, packet.payload)
            // every phone switches leaders the moment it hears this (the new leader's own lobby may arrive before or after it)
            var next = state; next.ownerID = packet.payload
            for i in next.participants.indices { next.participants[i].ready = next.participants[i].isGuest }
            if packet.payload == localID {
                next.revision += 1; lobby = next; publishLobby(); forgetParty()
                lastError = "You're the party leader now."
            } else {
                lobby = next; rememberParty(leader: packet.payload, name: next.participants.first { $0.id == packet.payload }?.name ?? ""); syncPartyLeader()
            }
            return
        }
        if packet.kind == "kick", isParty, peer == state.ownerID, state.phase == .lobby {
            let leader = state.participants.first { $0.id == peer }?.name ?? "The party leader"
            forgetParty(); leave("kicked by the leader")
            lastError = "\(leader) took you out of the party."
            return
        }
        if Self.partyKinds.contains(packet.kind) {
            guard packet.payload.utf8.count <= 4096, state.participants.contains(where: { $0.id == peer && !$0.isGuest }) else { return }
            onParty?(packet.kind, packet.payload, peer); return
        }
        if packet.kind == "hubPresence" || packet.kind == "hubEvent" {
            guard state.phase == .lobby, packet.payload.utf8.count <= 2048, state.participants.contains(where: { $0.id == peer }) else { return }
            onHub?(packet.kind, packet.payload, peer); return
        }
        if packet.kind == "emote", !isOwner {
            guard peer == state.ownerID, state.phase == .lobby,
                  let event = try? decoder.decode(MultiplayerEmote.self, from: Data(packet.payload.utf8)),
                  event.startedAt.isFinite, MultiplayerEmote.ids.contains(event.emoteID), state.participants.contains(where: { $0.id == event.participantID }) else { return }
            emotes[event.participantID] = event
            #if DEBUG
            if proofRecording { OnlineLobbyProofDriver.event("emote-received","\(event.participantID) \(event.emoteID) sent=\(event.startedAt)") }
            #endif
            return
        }
        if ["ready","queue","loaded","calibrated","setupStep","startRequest","display","screenDelay","leave","availability","look","emote","return","keepWaiting"].contains(packet.kind) {
            if isOwner { handleControl(packet) }; return
        }
        if packet.kind == "input" {
            guard isOwner, packet.matchID == state.matchID, state.phase == .playing,
                  state.participants.contains(where: { $0.id == peer && $0.seat >= 0 && $0.connected }) else { return }
            pushRuntimePacket(packet); return
        }
        // Versus tennis: the two players' phones talk to each other directly (each runs its own player; Unity TennisGame.Versus).
        if packet.kind == "peer" {
            guard packet.matchID == state.matchID, state.phase == .playing,
                  state.participants.contains(where: { $0.id == peer && $0.seat >= 0 && $0.connected }) else { return }
            pushRuntimePacket(packet); return
        }
        if packet.kind == "ping", isOwner { try? transmit("pong", payload: packet.payload, reliable: false, to: [peer]); return }
        if packet.kind == "link", isOwner { noteLink(from: peer, report: packet.payload); return }
        guard peer == state.ownerID else { return }
        switch packet.kind {
        case "loadTimeout": if packet.matchID == state.matchID && state.phase == .loading { loadingNeedsDecision = true }
        case "loadContinue": if packet.matchID == state.matchID && state.phase == .loading { loadingNeedsDecision = false }
        case "notice": lastError = String(packet.payload.prefix(200))
        case "launch": guard packet.matchID == state.matchID, [.loading,.calibrating,.playing,.results].contains(state.phase) else { return }; launch(packet.payload)
        case "run":
            guard packet.matchID == state.matchID, let at = Double(packet.payload), at.isFinite else { return }
            scheduledRunAt = at; clearSetupNotices(); pushRuntimePacket(packet)
            // the guest watches the owner from the shared start (its clock is the owner's minus the offset)
            if silenceArmedAt == .infinity { silenceArmedAt = at - clockOffset + MultiplayerTuning.silenceGrace; lastHeard[state.ownerID] = now }
        case "snapshot", "golfShot": guard packet.matchID == state.matchID else { return }; pushRuntimePacket(packet)
        case "suspend", "resumePeer", "drop": pushRuntimePacket(packet)
        case "result": guard packet.matchID == state.matchID else { return }; pushRuntimePacket(packet); rememberResult(packet.payload); onResult?(packet.payload)
        case "stop": stopRuntime(retainDirection: packet.payload == "rematch")
        case "pong":
            guard let sent = Double(packet.payload) else { return }
            // One slow packet must not move the shared clock: keep the least-delayed samples and slew (ClockFilter).
            stats.note(rtt: max(0, now - sent)); linkWindow.answered(sentAt: sent, rtt: max(0, now - sent))
            clockOffset = clockFilter.add(rtt: max(0, now - sent), offset: packet.sentAt - (sent + now) / 2)
            roundTrip = clockFilter.medianRTT
            pushRuntime("clock", payload: String(clockOffset))
        default: break
        }
    }
    /// A competitor that went quiet is heard again: after a few packets, resume play. (A guest's quiet owner: its own game only.)
    private func quietPeerHeard(_ id: String) {
        guard let heard = silent[id] else { return }
        silent[id] = heard + 1
        guard heard + 1 >= MultiplayerTuning.resumeBeats else { return }
        silent.removeValue(forKey: id); stats.resumes += 1
        guard isOwner else { pushRuntime("resumePeer", payload: id); return }
        disconnected.removeValue(forKey: id)
        try? broadcast("resumePeer", payload: id); pushRuntime("resumePeer", payload: id)
    }
    private func handleControl(_ p: MultiplayerPacket) {
        guard let i = lobby?.participants.firstIndex(where: { $0.id == p.sender }) else { return }
        switch p.kind {
        case "startRequest":
            guard p.matchID == lobby?.matchID, lobby?.phase == .playing, lobby!.participants[i].connected else { return }
            try? transmit("run", payload: String(scheduledRunAt), to: [p.sender]); return
        case "keepWaiting":
            guard lobby?.phase == .loading, p.matchID == lobby?.matchID, loadingNeedsDecision else { return }
            loadingStarted = now; loadingNeedsDecision = false; try? broadcast("loadContinue"); return
        case "return":
            // after the result anyone may bring the lobby back; in a friends' party any member may also end the match early
            let early = isParty && [.loading, .calibrating, .playing].contains(lobby?.phase ?? .lobby)
            if lobby?.phase == .results || lobby?.phase == .interrupted || early { try? returnToLobby(rotateSeats: !isParty) }; return
        case "look":
            guard lobby?.phase == .lobby, now - (lastLook[p.sender] ?? -Double.infinity) >= 0.1 - 1e-6,
                  let update = try? decoder.decode(MultiplayerLookUpdate.self, from: Data(p.payload.utf8)),
                  update.participantID == p.sender, update.loadout?.valid() ?? true else { return }
            lastLook[p.sender] = now; lobby!.participants[i].loadout = update.loadout
            #if DEBUG
            if proofRecording { OnlineLobbyProofDriver.event("look-accepted","\(p.sender) sent=\(p.sentAt)") }
            #endif
            if let name = update.name { lobby!.participants[i].name = String(name.prefix(40)) }
            if let female = update.female { lobby!.participants[i].female = female }
            if let left = update.left { lobby!.participants[i].left = left }
        case "emote":
            guard lobby?.phase == .lobby, now - (lastEmote[p.sender] ?? -Double.infinity) >= MultiplayerEmote.cooldown,
                  var event = try? decoder.decode(MultiplayerEmote.self, from: Data(p.payload.utf8)),
                  event.participantID == p.sender, event.startedAt.isFinite, MultiplayerEmote.ids.contains(event.emoteID),
                  (event.eventID?.utf8.count ?? 0) <= 64 else { return }
            lastEmote[p.sender] = now; event.startedAt = now; emotes[p.sender] = event
            try? broadcast("emote", payload: json(event)); return
        case "ready": if lobby?.phase == .lobby {
            lobby!.participants[i].ready = p.payload == "true"
            for g in lobby!.participants.indices where lobby!.participants[g].controllerID == p.sender { lobby!.participants[g].ready = p.payload == "true" }
        }
        case "queue": if lobby!.participants[i].seat == -1 {
            lobby!.queue.removeAll { $0 == p.sender }; if p.payload == "true" { lobby!.queue.append(p.sender) }
        }
        case "loaded": if p.matchID == lobby?.matchID {
            guard [.loading, .calibrating, .playing, .results].contains(lobby!.phase) else { return }
            // Retries keep the same report ID. A duplicate acknowledgement must never clear completed setup.
            // The same report after a reconnect is the same Unity load (a nearby guest's link came back without the game reloading): it
            // is loaded and still in the match, whatever the reconnect reset, so play resumes for it.
            if loadReports[p.sender] == p.payload {
                if !lobby!.participants[i].loaded { lobby!.participants[i].loaded = true; lobby!.revision += 1 }
                if lobby!.phase == .playing, !awaitingCalibration.contains(p.sender), disconnected.removeValue(forKey: p.sender) != nil {
                    silent.removeValue(forKey: p.sender); lastHeard[p.sender] = now
                    try? broadcast("resumePeer", payload: p.sender); pushRuntime("resumePeer", payload: p.sender)
                }
                publishLobby(); return
            }
            let reported = Double(p.payload.split(separator: "|").first.map(String.init) ?? "") ?? now
            guard reported.isFinite else { return }
            loadReports[p.sender] = p.payload
            presentationReadyAt[p.sender] = max(now, min(now + 2, reported))
            lobby!.participants[i].loaded = true
            for g in lobby!.participants.indices where lobby!.participants[g].controllerID == p.sender {
                lobby!.participants[g].loaded = true
                presentationReadyAt[lobby!.participants[g].id] = presentationReadyAt[p.sender]
            }
            silent.removeValue(forKey: p.sender); lastHeard[p.sender] = now
            // A tennis competitor that has just (re)loaded has no court direction yet, whatever it reported before.
            let setUpAgain = lobby!.sport == .tennis && lobby!.participants[i].seat >= 0 && [.calibrating, .playing].contains(lobby!.phase)
            if setUpAgain { lobby!.participants[i].calibrated = false }
            if setUpAgain, lobby!.phase == .playing {
                // Mid-match: play stays paused for this player until it reports `calibrated` (it gets longer than a plain
                // dropped connection to do so).
                awaitingCalibration.insert(p.sender)
                if disconnected[p.sender] == nil { try? broadcast("suspend", payload: p.sender); pushRuntime("suspend", payload: p.sender) }
                disconnected[p.sender] = now
            } else if disconnected.removeValue(forKey: p.sender) != nil {
                try? broadcast("resumePeer", payload: p.sender); pushRuntime("resumePeer", payload: p.sender)
            }
            if lobby?.phase == .playing || lobby?.phase == .results { try? transmit("run", payload: String(scheduledRunAt), to: [p.sender]); pushRuntime("snapshotRequest") }
        }
        case "calibrated":
            // Tennis only: the player has pointed the phone at the TV and tapped Ready.
            guard p.matchID == lobby?.matchID, lobby!.sport == .tennis, lobby!.participants[i].seat >= 0,
                  [.loading, .calibrating, .playing].contains(lobby!.phase), lobby!.participants[i].connected else { return }
            if !lobby!.participants[i].calibrated {
                SportsDiagnostics.write("multiplayer setup accepted seat=\(lobby!.participants[i].seat) phase=\(lobby!.phase.rawValue)")
            }
            lobby!.participants[i].calibrated = true
            silent.removeValue(forKey: p.sender); lastHeard[p.sender] = now
            awaitingCalibration.remove(p.sender)
            if lobby!.phase == .playing, disconnected.removeValue(forKey: p.sender) != nil {
                try? broadcast("resumePeer", payload: p.sender); pushRuntime("resumePeer", payload: p.sender)
            }
        case "setupStep":
            guard p.matchID == lobby?.matchID, lobby!.sport == .tennis, lobby!.participants[i].seat >= 0,
                  [.loading, .calibrating].contains(lobby!.phase), ["direction", "ready"].contains(p.payload) else { return }
            lobby!.participants[i].setupStep = p.payload
        case "display": lobby!.participants[i].hasScreen = p.payload == "true"
        case "screenDelay":
            // Only a phone with a TV has a delay to report; keep it within what the game would ever credit.
            if lobby!.participants[i].hasScreen, let seconds = Double(p.payload), seconds.isFinite { lobby!.participants[i].screenDelay = min(1, max(0, seconds)) }
        case "leave":
            if lobby!.participants[i].seat >= 0 && lobby!.phase == .playing { lastError = "\(lobby!.participants[i].name) left the match." }
            if lobby!.participants[i].seat >= 0 { try? broadcast("drop", payload: p.sender); pushRuntime("drop", payload: p.sender) }
            lobby!.participants.remove(at: i); lobby!.queue.removeAll { $0 == p.sender }; awaitingCalibration.remove(p.sender)
            dropped[p.sender] = nil
        case "availability":
            lobby!.participants[i].paused = p.payload == "false"
            if lobby!.participants[i].seat >= 0 && lobby!.phase == .playing {
                if p.payload == "false" { disconnected[p.sender] = now; try? broadcast("suspend", payload: p.sender); pushRuntime("suspend", payload: p.sender) }
                // Coming back to the foreground does not resume a player who still has to point at the TV.
                else if !awaitingCalibration.contains(p.sender) { disconnected.removeValue(forKey: p.sender); silent.removeValue(forKey: p.sender); lastHeard[p.sender] = now; try? broadcast("resumePeer", payload: p.sender); pushRuntime("resumePeer", payload: p.sender) }
            }
        default: break
        }
        lobby?.revision += 1; publishLobby()
        advancePhase()
    }
    /// Moves the lobby along when what it was waiting for has happened: everyone loaded; for tennis, everyone set up and on a steady connection.
    private func advancePhase() {
        if lobby?.phase == .loading, lobby!.competitors.count >= 2, lobby!.competitors.allSatisfy(\.loaded) {
            loadingNeedsDecision = false
            if lobby!.sport == .tennis { beginCalibration(); advancePhase() } else { beginPlay() }
        } else if lobby?.phase == .calibrating, lobby!.competitors.count >= 2, lobby!.competitors.allSatisfy({ $0.loaded && $0.calibrated }), linksAreSteady {
            beginPlay()
        } else if abortSetupIfShort() {
            return
        } else if quickSport != nil, lobby?.canStart == true { try? startMatch() }
        else if isOwner, isParty, lobby?.readyCheck == true, lobby?.phase == .lobby { partyReadyAdvance() }
    }
    /// The party's ready check: everyone seated tapped Ready, so the game starts; a player gone (or too few left) ends the check.
    private func partyReadyAdvance() {
        guard let state = lobby else { return }
        let seated = state.participants.filter { $0.seat >= 0 && !$0.isGuest }
        if seated.filter(\.connected).count < 2 {
            cancelPartyGame(); lastError = "Not enough players for that game. Pick it again when your friends are back."
            try? broadcast("notice", payload: lastError ?? ""); return
        }
        guard state.canStart else { return }
        do { try startMatch() } catch { lastError = error.localizedDescription }
    }
    /// The owner is never measured (it is the other end); every other tennis competitor must have been steady, unless the owner chose to play anyway.
    private var linksAreSteady: Bool {
        guard requiresStableLink, !linkOverride, let state = lobby else { return true }
        return state.competitors.allSatisfy { $0.id == state.ownerID || ($0.linkOK && now - (linkHeardAt[$0.id] ?? -Double.infinity) <= 1) }
    }
    /// The owner starts despite a weak connection (offered after a few seconds of waiting).
    func playAnyway() {
        guard isOwner, lobby?.phase == .calibrating else { return }
        linkOverride = true; linkNeedsDecision = false; advancePhase()
    }
    /// A guest's grade for its own connection: steady means Fair or better for 1.5 s in a row.
    private func noteLink(from peer: String, report: String) {
        guard let phase = lobby?.phase, [.loading, .calibrating].contains(phase), let i = lobby?.participants.firstIndex(where: { $0.id == peer && $0.seat >= 0 }),
              let result = LinkWindow.parse(report: report) else { return }
        linkHeardAt[peer] = now
        if result.grade >= .fair { linkSteadySince[peer] = linkSteadySince[peer] ?? now } else { linkSteadySince[peer] = nil }
        let steady = linkSteadySince[peer].map { now - $0 >= MultiplayerTuning.linkStableSeconds } ?? false
        if lobby!.participants[i].linkOK != steady { lobby!.participants[i].linkOK = steady; lobby!.revision += 1; publishLobby() }
        advancePhase()
    }
    /// Who shows a tennis match how. Both players have a TV: each sees their own court, as before. Exactly one TV: that phone shows both
    /// players and the other is only a controller. Spectators and golf get no view (golf guests always watch the host's TV).
    private func assignViews() {
        guard lobby != nil else { return }
        let screens = lobby!.competitors.filter(\.hasScreen).count
        for i in lobby!.participants.indices {
            let p = lobby!.participants[i]
            guard lobby!.sport == .tennis, p.seat >= 0 else { lobby!.participants[i].view = nil; continue }
            let view: MultiplayerView = screens >= 2 ? .near : (p.hasScreen ? .split : .controllerOnly)
            lobby!.participants[i].view = view
        }
    }
    /// Everyone has loaded. Tennis now lets each player set up their controller; the owner starts play when all are done.
    private func beginCalibration() {
        SportsDiagnostics.write("multiplayer all courts loaded; retaining completed controller setup")
        calibrationStarted = now; calibrationNoticed = false; awaitingCalibration.removeAll()
        // Direction/centre can already be complete while another phone was loading. Keep those acknowledgements.
        lobby!.phase = .calibrating; lobby!.revision += 1; publishLobby()
    }
    /// The two notices setup can post (a weak connection, slow setup) start with these.
    private static let weakLinkNoticePrefix = "The connection to ", slowSetupNoticePrefix = "Still waiting for "
    /// The "Play anyway" choice and those two notices are about setup; once play begins they would only sit on the screen all match.
    private func clearSetupNotices() {
        linkNeedsDecision = false
        if let text = lastError, text.hasPrefix(Self.weakLinkNoticePrefix) || text.hasPrefix(Self.slowSetupNoticePrefix) { lastError = nil }
    }
    /// Schedule the shared start (after the slowest phone's loading cover has gone) and tell everyone.
    private func beginPlay() {
        clearSetupNotices()
        scheduledRunAt = max(now, lobby!.competitors.map { presentationReadyAt[$0.id] ?? now }.max() ?? now) + max(lobby!.sport == .tennis ? 3 : 0.5, roundTrip * 2)
        SportsDiagnostics.write("multiplayer shared start scheduled in \(String(format: "%.2f", scheduledRunAt - now)) s")
        lobby!.phase = .playing; lobby!.revision += 1; publishLobby()
        try? broadcast("run", payload: String(scheduledRunAt)); pushRuntime("run", payload: String(scheduledRunAt))
        silenceArmedAt = scheduledRunAt + MultiplayerTuning.silenceGrace; silent.removeAll()
        for c in lobby!.competitors { lastHeard[c.id] = now }
    }
    /// Setup cannot finish with fewer than two seated players (one left, or was dropped): go back to the lobby, not wait forever.
    @discardableResult private func abortSetupIfShort() -> Bool {
        guard isOwner, lobby?.phase == .calibrating, lobby!.participants.filter({ $0.seat >= 0 }).count < 2 else { return false }
        let text = "The other player left during setup. Everyone is back in the lobby."
        try? returnToLobby(rotateSeats: false)
        lastError = text; try? broadcast("notice", payload: text)
        return true
    }
    func runtimeLoaded(readyAfter: Double = 0) {
        // A second renderer launch is a real reload, not an acknowledgement retry.
        if localLoadReport != nil { localCalibrationReported = false }
        localLoadReport = String(networkTime + min(2, max(0, readyAfter))) + "|" + UUID().uuidString
        SportsDiagnostics.write("multiplayer local renderer ready; reporting to owner")
        try? sendControl("loaded", payload: localLoadReport!)
    }
    /// Tennis: this phone's controller is set up (court direction found and centre taken).
    func runtimeCalibrated() { localCalibrationReported = true; try? sendControl("calibrated") }
    func runtimeSetupStep(_ step: String) { try? sendControl("setupStep", payload: step) }
    func keepWaitingForLoad() throws {
        guard lobby?.phase == .loading else { return }
        try sendControl("keepWaiting")
    }
    func runtimeUnavailable(_ reason: String) {
        if isOwner { interrupt(reason) }
        else { try? sendControl("availability", payload: "false"); stopRuntime(); lastError = reason }
    }
    func setForeground(_ foreground: Bool) {
        guard let state = lobby, state.phase == .playing else { return }
        guard isOwner else {
            // nothing was heard from the owner while this phone slept: its silence clock starts afresh
            if foreground { lastHeard[state.ownerID] = now; silenceArmedAt = now + MultiplayerTuning.silenceGrace }
            try? sendControl("availability", payload: foreground ? "true" : "false"); return
        }
        // The host leaving no longer ends the match: tennis goes on on the other phone against the CPU, golf waits for the host's
        // simulation. Everyone is told, so their games mark the host as away, and the host has awayLimitSeconds to come back.
        guard continuesWhileAway else { if !foreground { interrupt("The host entered the background.") }; return }
        if foreground {
            // nothing was heard while this phone slept: start the competitors' silence clocks afresh instead of suspending them all
            for p in state.participants where p.id != localID { lastHeard[p.id] = now }
            silenceArmedAt = now + MultiplayerTuning.silenceGrace
            try? broadcast("resumePeer", payload: localID); pushRuntime("resumePeer", payload: localID)
        } else {
            try? broadcast("suspend", payload: localID)
        }
    }
    /// An online match goes on while a player is away (AwayPolicy); only a match on one shared phone has nobody to go on with.
    var continuesWhileAway: Bool { !sharedPhoneHost && (lobby?.sport == .tennis || lobby?.sport == .golf || lobby?.sport == .bowling) }
    /// How long a competitor who went quiet or left the app keeps their place in the match.
    private func dropAfter(_ id: String) -> Double {
        if continuesWhileAway { return MultiplayerTuning.awayLimitSeconds }
        return awaitingCalibration.contains(id) ? MultiplayerTuning.recalibrationSeconds : 15
    }
    /// Has this phone been left out of its match while it was away (the host's timer ran out)? It then leaves when it opens again.
    var droppedFromMatch: Bool {
        guard let lobby, matchConfiguration != nil, [.playing, .results].contains(lobby.phase) else { return false }
        let mine = matchConfiguration?.participants.first { $0.id == localID }?.seat ?? -1
        return mine >= 0 && (lobby.participants.first { $0.id == localID }?.seat ?? -1) < 0
    }
    private func sendControl(_ kind: String, payload: String = "") throws {
        guard let lobby else { throw MultiplayerError.invalidOperation("There is no connected lobby.") }
        if isOwner { var p = packet(kind, payload: payload); p.sender = localID; handleControl(p) }
        else { try transmit(kind, payload: payload, to: [lobby.ownerID]) }
    }
    private func publishLobby() {
        guard let lobby else { return }
        if isOwner { local?.advertise(sport:lobby.sport.rawValue,players:lobby.participants.count) }
        syncPartyLeader()
        try? broadcast("lobby", payload: (try? json(lobby)) ?? "")
    }
    /// The party link meets in the leader's group: it follows the lobby's leader (handed over, or made leader).
    private func syncPartyLeader() {
        guard isParty, let gc = gameCenter, transport === gc, let lobby else { return }
        gc.setLeader(lobby.ownerID, name: lobby.participants.first { $0.id == lobby.ownerID }?.name ?? "your friend")
    }
    private func packet(_ kind: String, payload: String = "", reliable: Bool = true) -> MultiplayerPacket {
        sequence += 1
        return MultiplayerPacket(lobbyID: lobby?.id ?? "", matchID: lobby?.matchID ?? "", sender: localID, sequence: sequence, kind: kind, reliable: reliable, sentAt: now, payload: payload)
    }
    private func broadcast(_ kind: String, payload: String = "", reliable: Bool = true) throws { try transmit(kind, payload: payload, reliable: reliable, to: nil) }
    private func transmit(_ kind: String, payload: String = "", reliable: Bool = true, to: [String]? = nil) throws {
        guard transport != nil else { return }
        try sendPacket(packet(kind, payload: payload, reliable: reliable), to: to)
    }
    private func sendPacket(_ p: MultiplayerPacket, to ids: [String]?) throws {
        guard let transport else { return }
        let data = try encoder.encode(p)
        stats.largestPacket = max(stats.largestPacket, data.count)
        let reliable = p.reliable || unreliableRefused.contains(p.kind)
        do { try transport.send(data, to: ids, reliable: reliable) }
        catch {
            // Versus tennis' unreliable peer packets are its 30 Hz poses: one refused is dropped (the next is 33 ms away). Sending
            // the "peer" kind reliably from then on would put every pose behind every lost packet for the rest of the match.
            if !reliable, p.kind == "peer" {
                stats.unreliableRefused += 1
                if stats.unreliableRefused <= 3 { SportsDiagnostics.write("unreliable peer packet refused at \(data.count) bytes (\(error.localizedDescription)); dropped") }
                return
            }
            // Apple limits how big an unreliable message may be and does not say how much. If it refuses a big one, send that
            // kind reliably from now on; any other failure is not about size, so let it through.
            guard !reliable, data.count > MultiplayerTuning.unreliableSafeBytes else { throw error }
            unreliableRefused.insert(p.kind); stats.unreliableRefused += 1
            SportsDiagnostics.write("unreliable \(p.kind) refused at \(data.count) bytes (\(error.localizedDescription)); sending it reliably from now on")
            try transport.send(data, to: ids, reliable: true)
        }
    }
    /// Write this match's link statistics to the local diagnostics log (nothing is uploaded), then start afresh.
    private func reportStats() {
        guard !stats.isEmpty else { return }
        // (Nearby: how many unreliable packets went as UDP datagrams, sent/received; 0/0 means they all went over TCP)
        let datagrams = local.map { " datagrams=\($0.datagramsSent)/\($0.datagramsReceived)" } ?? ""
        SportsDiagnostics.write("multiplayer \(lobby?.sport.rawValue ?? "?") \(isOwner ? "owner" : "guest"): \(stats.summary)\(datagrams)")
        stats = NetStats()
    }
    private func json<T: Encodable>(_ value: T) throws -> String { String(decoding: try encoder.encode(value), as: UTF8.self) }
    private func launch(_ payload: String) {
        guard var config = try? decoder.decode(MultiplayerMatchConfiguration.self, from: Data(payload.utf8)), config.matchID != matchConfiguration?.matchID else { return }
        config.localID = localID
        if config.sport == "golf" { config.venue = MultiplayerLobby.currentGolfVenue(config.venue) }
        guard config.valid(), config.hostID == lobby?.ownerID, config.lobbyID == lobby?.id, config.matchID == lobby?.matchID else { lastError = "Invalid match configuration."; return }
        guard onMatchRequested != nil || !SportsSession.shared.active else { lastError = "Finish the current sport session before joining this match."; return }
        // In a friends' party only the people on the bench play: everyone else stays where they are in the Plaza.
        if isParty, (config.participants.first { $0.id == localID }?.seat ?? -1) < 0 { return }
        // the last match's packets (and any overflow report) must not use up this match's room in the bridge
        runtimeClear()
        silent.removeAll(); silenceArmedAt = .infinity; local?.holdForReconnect = true
        matchConfiguration = config; quickSport = nil; lastError = nil; stats = NetStats()
        localLoadReport = nil; localCalibrationReported = false; nextSetupReport = 0; scheduledRunAt = 0
        SportsDiagnostics.write("multiplayer launch \(config.sport) \(isOwner ? "owner" : "guest") seat=\(config.participants.first { $0.id == localID }?.seat ?? -1) peers=\(transport?.peers.count ?? 0) \(SportsDiagnostics.memory)")
        #if DEBUG
        if proofRecording { OnlineLobbyProofDriver.event("launch-config","bytes=\(payload.utf8.count) \(payload)") }
        #endif
        if let onMatchRequested { onMatchRequested(config) } else { SportsSession.shared.startMultiplayer(config) }
    }
    private func pushRuntimePacket(_ packet: MultiplayerPacket) {
        #if DEBUG
        if proofRecording && packet.kind == "run" { OnlineLobbyProofDriver.event("runtime-run",(try? json(packet)) ?? "") }
        if proofRecording && packet.kind == "snapshot" { proofSnapshot=packet.payload }
        #endif
        // Unity reads the bridge only while a match is configured, and the bridge holds 128 packets. The shared clock is worth sending
        // during a match and never otherwise: a guest waiting in a lobby (or on the results screen) used to put a reliable clock packet in
        // with every pong, twice a second, and after 64 s the bridge was full. The next match launch was then refused, and the guest
        // ejected itself half a second after the TV began to load.
        if packet.kind == "clock" && matchConfiguration == nil { return }
        if let text = try? json(packet), !runtimeSend(text), matchConfiguration != nil {
            SportsDiagnostics.write("multiplayer bridge refused a \(packet.kind) packet")
            lastError="The Unity multiplayer bridge is unavailable or full. Re-export Unity before playing."
        }
    }
    /// A clock update is stale a second later, so it goes as a packet the bridge may evict when it is under pressure; a bridge that holds
    /// nothing but reliable packets can only refuse (and then ends the match).
    private func pushRuntime(_ kind: String, payload: String = "") { pushRuntimePacket(packet(kind, payload: payload, reliable: kind != "clock")) }
    private func stopRuntime(retainDirection: Bool = false) {
        reportStats()
        if retainDirection, SportsSession.shared.multiplayerMatchID == lobby?.matchID {
            SportsSession.shared.retainCourtDirectionForRematch = true
        }
        localLoadReport = nil; localCalibrationReported = false; local?.holdForReconnect = false
        pushRuntime("stop"); matchConfiguration = nil
        if let onReturnToLobby { onReturnToLobby() }
        else if SportsSession.shared.multiplayerMatchID != nil { SportsSession.shared.end() }
    }
    private func rotate() {
        guard var state = lobby, let next = state.queue.first, let waiting = state.participants.firstIndex(where: { $0.id == next && $0.connected && $0.seat == -1 }) else { return }
        let vacant = (0..<2).first { n in !state.participants.contains { $0.seat == n } } ?? (winnerSeat == 1 ? 0 : 1)
        if let outgoing = state.participants.firstIndex(where: { $0.seat == vacant }) { state.participants[outgoing].seat = -1 }
        state.participants[waiting].seat = vacant; state.queue.removeFirst(); lobby = state
    }
    private func rememberResult(_ payload: String) {
        if let data = payload.data(using: .utf8), let result = try? JSONSerialization.jsonObject(with: data) as? [String: Any] { winnerSeat = result["winner"] as? Int ?? -1 }
    }
    private func interrupt(_ reason: String) {
        SportsDiagnostics.write("multiplayer interrupted: \(reason)")
        lobby?.phase = .interrupted; lobby?.revision += 1; publishLobby()
        try? broadcast("stop"); stopRuntime(); lastError = reason
    }
    func update() {
        guard let transport else { return }
        if let phase = lobby?.phase, [.loading, .calibrating, .playing].contains(phase), now >= nextSetupReport {
            nextSetupReport = now + 1
            let me = lobby?.participants.first { $0.id == localID }
            if me?.loaded == false, let report = localLoadReport { try? sendControl("loaded", payload: report) }
            if me?.calibrated == false, localCalibrationReported { try? sendControl("calibrated") }
            if !isOwner, matchConfiguration != nil, phase == .playing, scheduledRunAt == 0 { try? sendControl("startRequest") }
        }
        // Ping often enough to keep the clock filter fed (5/s in a match, 2/s otherwise). Unreliable, so a lost ping is
        // skipped instead of queueing behind other traffic and arriving late.
        // During tennis setup they go out 10 times a second, so the connection can be graded within two seconds.
        if now >= nextPing { nextPing = now + (lobby?.phase == .playing ? 0.2 : [.loading, .calibrating].contains(lobby?.phase ?? .lobby) ? MultiplayerTuning.linkPingInterval : 0.5)
            if !isOwner, let owner = lobby?.ownerID { stats.pingsSent += 1; linkWindow.sent(at: now); try? transmit("ping", payload: String(now), reliable: false, to: [owner]) }
        }
        if !isOwner { linkWindow.expire(now: now) }
        if !isOwner, [.loading, .calibrating].contains(lobby?.phase ?? .lobby), localSeat >= 0, now >= nextLinkReport, let owner = lobby?.ownerID {
            nextLinkReport = now + MultiplayerTuning.linkReportInterval
            try? transmit("link", payload: linkWindow.report, reliable: false, to: [owner])
        }
        // A competitor's phone tells the owner it is still there, 10 times a second during play.
        if !isOwner, lobby?.phase == .playing, localSeat >= 0, now >= nextHeartbeat, let owner = lobby?.ownerID {
            nextHeartbeat = now + MultiplayerTuning.heartbeatInterval
            try? transmit("hb", reliable: false, to: [owner])
        }
        if now >= nextHello { nextHello = now + 1
            // A phone not in the lobby keeps saying hello: its first one can go out before the connection to the host is up, and a
            // lobby that arrived before the host heard it does not list it (2026-10-25: neither phone ever saw the other).
            if lobby == nil || (!isOwner && lobby?.participants.contains(where: { $0.id == localID }) != true) {
                try? broadcast("hello", payload: (try? json(identity())) ?? "")
            }
            // ...and the host keeps sending its lobby to a connected phone it does not list yet, so that phone has a host to talk to
            if isOwner, joiningPeers > 0, lobby?.phase == .lobby { publishLobby() }
            pruneDroppedMembers()
        }
        if isOwner {
            // (one shared phone loads on its own: there is nobody to wait for, so no "keep waiting or leave" choice)
            if lobby?.phase == .loading, !loadingNeedsDecision, !sharedPhoneHost, now - loadingStarted >= 20 {
                loadingNeedsDecision = true
                try? broadcast("loadTimeout")
            }
            // A competitor we have heard nothing from pauses the match for everyone until it is heard again. Apple only
            // reports a disconnect after a while, and meanwhile the opponent would keep scoring.
            if lobby?.phase == .playing, now >= silenceArmedAt {
                for p in lobby!.participants where p.seat >= 0 && p.connected && !p.isGuest && p.id != localID {
                    guard disconnected[p.id] == nil, silent[p.id] == nil else { continue }
                    if now - (lastHeard[p.id] ?? now) >= MultiplayerTuning.silenceSeconds {
                        silent[p.id] = 0; disconnected[p.id] = now; stats.silences += 1
                        try? broadcast("suspend", payload: p.id); pushRuntime("suspend", payload: p.id)
                    }
                }
            }
            // A guest whose reports stopped arriving is no longer known to be steady.
            if [.loading, .calibrating].contains(lobby?.phase ?? .lobby) {
                for (id, heard) in linkHeardAt where now - heard > 1.0 {
                    linkHeardAt.removeValue(forKey: id); linkSteadySince[id] = nil
                    if let i = lobby?.participants.firstIndex(where: { $0.id == id }), lobby!.participants[i].linkOK { lobby!.participants[i].linkOK = false; lobby?.revision += 1; publishLobby() }
                }
            }
            // Everyone is set up but a connection is not steady: after a few seconds the owner is offered "Play anyway".
            if lobby?.phase == .calibrating, requiresStableLink, !linkOverride {
                let setUp = lobby!.competitors.count >= 2 && lobby!.competitors.allSatisfy { $0.loaded && $0.calibrated }
                if setUp && !linksAreSteady {
                    let since = linkWaitingSince ?? now; linkWaitingSince = since
                    if !linkNeedsDecision, now - since >= MultiplayerTuning.linkDecisionSeconds {
                        linkNeedsDecision = true
                        let weak = lobby!.competitors.filter { $0.id != lobby!.ownerID && !$0.linkOK }.map(\.name)
                        let text = "\(Self.weakLinkNoticePrefix)\(weak.joined(separator: " and ")) is weak. Play anyway, or leave."
                        lastError = text; try? broadcast("notice", payload: text)
                    }
                } else { linkWaitingSince = nil }
            }
            // Setup that drags on is mentioned to everyone (nobody is forced to wait: Leave is always on screen).
            if lobby?.phase == .calibrating, !calibrationNoticed, now - calibrationStarted >= MultiplayerTuning.calibrationNoticeSeconds {
                calibrationNoticed = true
                let waiting = lobby!.competitors.filter { !$0.calibrated }.map(\.name)
                if !waiting.isEmpty {
                    let text = "\(Self.slowSetupNoticePrefix)\(waiting.joined(separator: " and ")) to finish setting up."
                    lastError = text; try? broadcast("notice", payload: text)
                }
            }
            // A dropped connection gets 15 s; a player who came back mid-match and has to point at the TV again gets longer.
            for (id, since) in disconnected where now - since >= dropAfter(id) {
                SportsDiagnostics.write("multiplayer dropped \(id == localID ? "this phone" : String(id.prefix(8))) after \(Int(now - since)) s paused or silent")
                disconnected.removeValue(forKey: id); silent.removeValue(forKey: id); awaitingCalibration.remove(id); stats.drops += 1; try? broadcast("drop", payload: id); pushRuntime("drop", payload: id)
                if let i = lobby?.participants.firstIndex(where: { $0.id == id }) { lobby!.participants[i].seat = -1; lobby!.participants[i].connected = id == localID || transport.peers.contains(id) }
                lobby?.revision += 1; publishLobby()
                abortSetupIfShort()
            }
        }
        // Tennis: a guest watches the owner as the owner watches it (the owner's poses or snapshots never stop during play). A quiet
        // owner holds this phone's game; it resumes after resumeBeats packets (quietPeerHeard).
        if !isOwner, lobby?.phase == .playing, lobby?.sport == .tennis, localSeat >= 0, now >= silenceArmedAt, let owner = lobby?.ownerID,
           silent[owner] == nil, now - (lastHeard[owner] ?? now) >= MultiplayerTuning.silenceSeconds {
            silent[owner] = 0; stats.silences += 1; pushRuntime("suspend", payload: owner)
            SportsDiagnostics.write("multiplayer owner silent \(String(format: "%.1f", now - (lastHeard[owner] ?? now))) s; holding")
        }
        // A guest whose host has been gone from the match for the whole away limit: the match is over.
        if !isOwner, let since = ownerMissingSince, now - since >= MultiplayerTuning.awayLimitSeconds {
            ownerMissingSince = nil
            if lobby?.phase == .playing { lobby?.phase = .interrupted; stopRuntime(); lastError = "The host was away too long, so the match ended." }
        }
        for _ in 0..<64 {
            guard let text = runtimePoll() else { break }
            #if DEBUG
            if proofRecording, let raw = try? JSONSerialization.jsonObject(with:Data(text.utf8)) as? [String:Any],let kind=raw["kind"] as? String,proofKinds.insert(kind).inserted { OnlineLobbyProofDriver.event("runtime-output",text) }
            #endif
            guard let data = text.data(using: .utf8), let outgoing = try? decoder.decode(MultiplayerPacket.self, from: data) else { continue }
            // The bridge dropped packets it had no room for (it never refuses a match's traffic any more). Logged only: ending the
            // match here was what ejected guests. A lost versus call is caught by the next point's ready check (score and point number).
            if outgoing.kind == "bridgeError" {
                SportsDiagnostics.write("multiplayer bridge overflow during \(matchConfiguration == nil ? "no match" : "a match"): \(outgoing.payload)")
                continue
            }
            guard outgoing.matchID == lobby?.matchID else { continue }
            if outgoing.kind == "stats" { SportsDiagnostics.write("unity network stats: \(outgoing.payload)"); continue }
            do {
                if outgoing.kind == "availability" { try sendControl("availability", payload: outgoing.payload) }
                else if outgoing.kind == "peer" {
                    // to every other phone in the match (the other player; on one shared TV, the phone drawing it)
                    guard localSeat >= 0, lobby?.phase == .playing else { continue }
                    try sendPacket(packet("peer", payload: outgoing.payload, reliable: outgoing.reliable), to: nil)
                }
                else if outgoing.kind == "input" {
                    guard localSeat >= 0, lobby?.phase == .playing else { continue }
                    if isOwner { var p = packet("input", payload: outgoing.payload, reliable: outgoing.reliable); p.sender = localID; pushRuntimePacket(p) }
                    else { try transmit("input", payload: outgoing.payload, reliable: outgoing.reliable, to: [lobby!.ownerID]) }
                } else if isOwner, ["snapshot","golfShot","result"].contains(outgoing.kind) {
                    try sendPacket(packet(outgoing.kind, payload: outgoing.payload, reliable: outgoing.reliable), to: nil)
                    #if DEBUG
                    if proofRecording && outgoing.kind == "snapshot" { proofSnapshot=outgoing.payload }
                    #endif
                    if outgoing.kind == "result" { rememberResult(outgoing.payload); lobby?.phase = .results; lobby?.revision += 1; publishLobby(); onResult?(outgoing.payload) }
                }
            } catch { lastError = error.localizedDescription }
        }
    }
}

/// Pass the phone: every player is on this phone, so the lobby needs no network at all (no listener, no Local Network
/// permission, nobody else can join). Messages go nowhere; the host plays the round on this phone.
@MainActor final class SharedPhoneTransport: MultiplayerTransport {
    let localID = UUID().uuidString
    var peers: [String] { [] }
    var onData: ((Data,String)->Void)?
    var onPeersChanged: (()->Void)?
    var onError: ((Error)->Void)?
    func send(_ data:Data,to peers:[String]?,reliable:Bool) throws { }
    func disconnect() { }
}

/// No sockets or Game Center: a deterministic party for screenshots and animation checks.
@MainActor private final class LobbyMockTransport: MultiplayerTransport {
    let localID = "00000000-0000-0000-0000-000000000001"
    var peers: [String] { [] }
    var onData: ((Data,String)->Void)?
    var onPeersChanged: (()->Void)?
    var onError: ((Error)->Void)?
    func send(_ data:Data,to peers:[String]?,reliable:Bool) throws { }
    func disconnect() { }
}

extension MultiplayerService {
    func enableMock(count: Int, player: Player) throws {
        leave(); setIdentity(name:player.name,female:player.standardFemale,left:player.handedness == .left,loadout:player.multiplayerLoadout)
        try host(using:LobbyMockTransport())
        let names = ["Sam","Maya","Leo"]
        for i in 1..<max(1,min(4,count)) {
            var p = Player(name:names[i-1],colorIndex:i,handedness:i == 2 ? .left : .right)
            p.standardFemale = i % 2 == 1; p.setSkin(Double(i) * 0.23)
            p.setOutfitHex("shirt",["D3F34B","FF6B4A","34435A"][i-1]); p.setOutfitHex("shorts",i == 2 ? "101D35" : "FAF8F3")
            try lobby?.add(MultiplayerParticipant(id:String(format:"00000000-0000-0000-0000-%012d",i+1),name:p.name,ready:i != 1,hasScreen:true,female:p.standardFemale,left:p.handedness == .left,loadout:p.multiplayerLoadout))
        }
        lobby?.participants[0].hasScreen = true
        lobby?.revision += 1; publishLobby()
    }
    #if DEBUG
    func mockState(phase:MultiplayerPhase, ready:Bool = false, disconnected:Bool = false, paused:Bool = false, spectator:Bool = false, guest:Bool = false, error:String? = nil) {
        guard transport is LobbyMockTransport else { return }
        lobby?.phase = phase
        if phase == .loading { loadingStarted = now; loadingNeedsDecision = false }
        lastError = error
        if guest, let peer = lobby?.participants.first(where:{ $0.id != localID }) { lobby?.ownerID = peer.id }
        for i in lobby!.participants.indices { lobby!.participants[i].ready = ready; lobby!.participants[i].loaded = i % 2 == 0; lobby!.participants[i].calibrated = phase == .playing || phase == .results }
        if lobby!.participants.count > 1 { lobby!.participants[1].connected = !disconnected; lobby!.participants[1].paused = paused }
        if spectator { lobby!.participants[0].seat = -1 }
        lobby?.revision += 1
    }
    /// Tests: what a background Nearby browse found.
    func debugSetDiscovered(_ lobbies: [LocalMultiplayerTransport.DiscoveredLobby]) { discoveredLobbies = lobbies }
    func mockNearby() {
        discoveredLobbies = [LocalMultiplayerTransport.DiscoveredLobby(id:"proof-nearby",name:"Sam",endpoint:.service(name:"Sam",type:"_partysports._tcp",domain:"local.",interface:nil),sport:"golf",players:3)]
    }
    func mockStartCountdown() {
        guard transport is LobbyMockTransport else { return }
        lobby?.phase = .playing; scheduledRunAt = networkTime + 3
        for i in lobby!.participants.indices { lobby!.participants[i].loaded = true; lobby!.participants[i].calibrated = true }
    }
    #endif
}

#if DEBUG
extension MultiplayerService {
    func breakProofConnection() { transport?.disconnect() }
    func addProofSpectators() throws {
        try requireOwnerIdle()
        for (i,name) in ["Maya","Leo"].enumerated() {
            let id="lobby-proof-\(i)";if lobby!.participants.contains(where:{$0.id==id}) {continue}
            var p=Player(name:name,colorIndex:i+2);p.standardFemale=i == 0;p.setSkin(Double(i)*0.6+0.1);p.setOutfitHex("shirt",i == 0 ? "D3F34B" : "34435A")
            try lobby?.add(MultiplayerParticipant(id:id,name:name,seat:-1,ready:true,female:p.standardFemale,loadout:p.multiplayerLoadout));proofPeers.insert(id)
        }
        for i in lobby!.participants.indices where proofPeers.contains(lobby!.participants[i].id) { lobby!.participants[i].seat = -1 }
        lobby?.revision+=1;publishLobby()
    }
    func removeProofSpectator() { guard isOwner else {return};lobby?.participants.removeAll { $0.id == "lobby-proof-1" };proofPeers.remove("lobby-proof-1");lobby?.revision+=1;publishLobby() }
    func sendProofInput(_ input:[String:Any]) throws {
        guard lobby?.phase == .playing,localSeat>=0 else { return }
        let payload=String(decoding:try JSONSerialization.data(withJSONObject:input),as:UTF8.self)
        if isOwner { pushRuntimePacket(packet("input",payload:payload)) } else { try transmit("input",payload:payload,to:[lobby!.ownerID]) }
    }
}
#endif
