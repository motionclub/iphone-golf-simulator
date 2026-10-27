import CloudKit
import Foundation
import GameKit
import Observation

// What Game Center cannot do, on Apple's CloudKit public database instead of a server of our own (Adnan, 2026-10-25):
// - who is in the game now, and whether their party has room (drop in on a friend);
// - a party code (and link) for anyone, friend or not, app or no app yet (texted to a phone number);
// - our own notifications: an invite or a knock record makes iCloud alert the player it is for, with Join.
// Dormant until the build has the iCloud (CloudKit) and Push Notifications capabilities and `ClubCloudContainer` in SportsInfo.plist
// (work/invites-audit-2026-10-25/CLOUDKIT_SETUP.md). Unit tests run it over an in-memory store.

/// A party anyone with its code can come into: the `Party` record, keyed by the code.
struct CloudParty: Equatable, Sendable {
    var code: String
    /// The host's teamPlayerID (knocks are addressed to it), gamePlayerID (the match) and name.
    var hostID: String
    var hostGameID: String
    var hostName: String
    var group: UInt32
    var size: Int
    var capacity: Int
    var open: Bool
}

/// One message from one player to another. `invite`: the friend's notification for a Game Center invite (Join opens it). `knock`: a
/// friend dropping in, or someone with the code, asks the host to let them in. `answer`: the host's go (both connect now) or full.
struct CloudNote: Equatable, Sendable {
    enum Kind: String, Sendable { case invite, knock, answer }
    var id = UUID().uuidString
    var kind: Kind
    var to: String
    var from: String
    var fromGameID: String
    var fromName: String
    var code = ""
    /// invite: the Game Center record to join. answer: "go" or "full".
    var detail = ""
    var group: UInt32 = 0
    var players = 0
    var round = 0
    var expires: Date
    /// The words of the notification ("Ann wants to play with you!").
    var message: String {
        switch kind {
        case .invite: "\(fromName) wants to play with you!"
        case .knock: "\(fromName) wants to join your party"
        case .answer: ""
        }
    }
}

/// The CloudKit calls, behind a protocol so the logic runs in tests.
@MainActor protocol ClubCloudStore: AnyObject {
    func available() async -> Bool
    func save(presence: HubPresence, id: String, gameID: String, name: String) async throws
    /// teamPlayerID → (online state, party, last seen).
    func presences(_ ids: [String]) async throws -> [String: (state: HubPresenceState, lobby: HubLobbyInfo?, seen: Date)]
    func save(party: CloudParty) async throws
    func party(code: String) async throws -> CloudParty?
    func send(_ note: CloudNote) async throws
    func notes(_ kind: CloudNote.Kind, to id: String) async throws -> [CloudNote]
    func delete(note: CloudNote) async throws
    func subscribe(id: String) async throws
}

/// The online layer over CloudKit. One for the app; ClubHub owns it and reads `on`.
@MainActor @Observable
final class ClubCloud {
    /// A player whose phone said so within this many seconds is online (phones say so every 45 s while the game is open).
    static let onlineWindow: TimeInterval = 120
    static let codeAlphabet = Array("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")

    /// CloudKit is there (the capability is in this build and the player is signed in to iCloud).
    private(set) var on = false
    /// This phone's party code (made when the player first shares one, or hosts a party friends can drop into).
    private(set) var code: String?
    /// Apple's own invite link for the code (iOS 26 game activities), when this build has the activity.
    private(set) var link: URL?
    /// Dropping in, or joining with a code: whose party and where it is.
    private(set) var knocking: (name: String, stage: String)?
    /// The party being knocked on now: its host's teamPlayerID and gamePlayerID (crossed knocks are settled with it).
    @ObservationIgnored private(set) var knockingHost: (id: String, gameID: String)?

    @ObservationIgnored let store: ClubCloudStore?
    /// Me: teamPlayerID, gamePlayerID, name (nil until Game Center has signed in).
    @ObservationIgnored var me: @MainActor () -> (id: String, gameID: String, name: String)? = { nil }
    /// What to publish about me (my state and my open party).
    @ObservationIgnored var presence: @MainActor () -> HubPresence = { HubPresence(state: .plaza) }
    /// My party right now: its group and size (members + 1 to bring someone in), capacity; nil when this phone cannot host.
    @ObservationIgnored var hostParty: @MainActor () -> (group: UInt32, size: Int, capacity: Int)? = { nil }
    /// Host: let them in (both phones start the private match now). Throws when it did not connect.
    @ObservationIgnored var bringIn: @MainActor (_ gameID: String, _ group: UInt32, _ players: Int) async throws -> Void = { _, _, _ in }
    /// Joiner: connect to the host's private match.
    @ObservationIgnored var connect: @MainActor (_ hostGameID: String, _ group: UInt32, _ players: Int) async throws -> Void = { _, _, _ in }
    /// This phone may go into another party now (the Plaza; ClubHub.canJoinNow).
    @ObservationIgnored var canJoinNow: @MainActor () -> Bool = { true }
    /// Host: someone can be let in now (no other party handshake on this phone: PartyJoinCoordinator).
    @ObservationIgnored var canHost: @MainActor () -> Bool = { true }
    /// Joiner: a knock on this host (gamePlayerID) begins: its handshake token, or nil when it may not start now. The closure given is
    /// called when a player's other join cancels it.
    @ObservationIgnored var beginKnock: @MainActor (_ hostGameID: String, _ onCancel: @escaping () -> Void) -> Int? = { _, _ in 0 }
    @ObservationIgnored var endKnock: @MainActor (Int) -> Void = { _ in }
    /// Friends (teamPlayerIDs): a friend's knock is let in by itself; anyone else's only with the current code.
    @ObservationIgnored var isFriend: @MainActor (String) -> Bool = { _ in false }
    @ObservationIgnored var say: @MainActor (String) -> Void = { _ in }
    @ObservationIgnored var joined: @MainActor (String) -> Void = { _ in }
    @ObservationIgnored var now: @MainActor () -> Date = { Date() }
    @ObservationIgnored var pollInterval: Duration = .seconds(2)

    @ObservationIgnored private var ticker: Task<Void, Never>?
    @ObservationIgnored private var lastPublished = Date.distantPast
    @ObservationIgnored private var lastPresence: HubPresence?
    @ObservationIgnored private var subscribed = false
    @ObservationIgnored private var handled: Set<String> = []
    @ObservationIgnored private var knockTask: Task<Void, Never>?
    @ObservationIgnored private var knockToken: Int?
    /// Host: the let-in running now (the tick goes on beside it: it used to wait up to 80 s, and presence and knocks with it).
    @ObservationIgnored private var letInTask: Task<Void, Never>?
    /// Seconds between checks for CloudKit while it is not there (no iCloud account yet, or no network at launch).
    @ObservationIgnored var availabilityRetry: Duration = .seconds(30)

    init(store: ClubCloudStore?) { self.store = store }

    /// The CloudKit store this build can use: nil without `ClubCloudContainer` in Info.plist (the capability is off), in unit tests,
    /// or with `-clubCloudOff`.
    static func liveStore() -> ClubCloudStore? {
        let info = ProcessInfo.processInfo
        guard let id = Bundle.main.object(forInfoDictionaryKey: "ClubCloudContainer") as? String, !id.isEmpty,
              info.environment["XCTestConfigurationFilePath"] == nil, !info.arguments.contains("-clubCloudOff") else { return nil }
        return CloudKitClubStore(container: id)
    }

    // MARK: life

    /// The app is active and Game Center has signed in: say I'm here, listen for knocks and notes.
    func start() {
        guard let store, ticker == nil else { return }
        ticker = Task { @MainActor [weak self] in
            // (not there at launch, e.g. no network yet or iCloud signed in later: asked again, instead of off for the whole run)
            while !Task.isCancelled {
                let ok = await store.available()
                guard let self else { return }
                self.on = ok
                if ok { break }
                try? await Task.sleep(for: self.availabilityRetry)
            }
            while !Task.isCancelled {
                await self?.tick()
                try? await Task.sleep(for: .seconds(5))
            }
        }
    }
    func stop() { ticker?.cancel(); ticker = nil }

    /// Every 5 s while the game is open (and on a push): my presence when it changed or every 45 s, knocks at my party.
    func tick() async {
        guard on, let store, let me = me() else { return }
        if !subscribed { subscribed = (try? await store.subscribe(id: me.id)) != nil }
        // a code from the start, so friends can drop in (texting it to someone new adds Apple's link)
        if code == nil { code = Self.newCode() }
        await publish()
        if let knocks = try? await store.notes(.knock, to: me.id) { for k in knocks where !handled.contains(k.id) { await answer(k) } }
        // Invite notes only carry their notification (the Game Center record is the invite): gone once the game is open. Answers
        // nobody waits for any more go too. (Neither was ever deleted, 2026-10-26.)
        for n in (try? await store.notes(.invite, to: me.id)) ?? [] { try? await store.delete(note: n) }
        for n in (try? await store.notes(.answer, to: me.id)) ?? [] where n.expires <= now() { try? await store.delete(note: n) }
    }

    /// My state for my friends (also with `force` when I leave the game: "away").
    func publish(force: Bool = false) async {
        guard on, let store, let me = me() else { return }
        var p = presence()
        if let code, p.lobby == nil, let host = hostParty(), p.state == .plaza || p.state == .lobby {
            // (in the Plaza on my own I am still a party of one friends can drop into)
            p.lobby = HubLobbyInfo(code: code, sport: "party", size: host.size - 1, capacity: host.capacity, open: host.size <= host.capacity, group: host.group)
        }
        guard force || p != lastPresence || now().timeIntervalSince(lastPublished) > 45 else { return }
        lastPresence = p; lastPublished = now()
        try? await store.save(presence: p, id: me.id, gameID: me.gameID, name: me.name)
        if let lobby = p.lobby {
            try? await store.save(party: CloudParty(code: lobby.code, hostID: me.id, hostGameID: me.gameID, hostName: me.name,
                                                    group: lobby.group, size: lobby.size, capacity: lobby.capacity, open: lobby.open))
        }
    }

    /// Friends' online state, party and room, for the Friends list.
    func friends(_ ids: [String]) async -> [String: (online: Bool, state: HubPresenceState, lobby: HubLobbyInfo?)] {
        guard on, let store, !ids.isEmpty, let list = try? await store.presences(ids) else { return [:] }
        let t = now()
        return list.mapValues { p in
            let online = p.state != .away && t.timeIntervalSince(p.seen) < Self.onlineWindow
            return (online, p.state, online ? p.lobby : nil)
        }
    }

    // MARK: a code to share

    /// The code (and link) for this phone's party, made now if there is none. Nil when CloudKit is off.
    func shareCode() async -> String? {
        guard on else { return nil }
        if link == nil, #available(iOS 26.0, *), let apple = await Self.appleActivity(), let theirs = Self.normalized(apple.code) {
            code = theirs; link = apple.url
        }
        if code == nil { code = Self.newCode() }
        lastPresence = nil
        await publish(force: true)
        return code
    }
    static func newCode() -> String { String((0..<6).map { _ in codeAlphabet.randomElement()! }) }
    /// The party ended (left, or joined someone else's): the old code stops working.
    func dropCode() { code = nil; link = nil; lastPresence = nil }

    /// The words texted to a phone number: the link (Apple's, iOS 26) or the code, and where to get the game.
    func message(from name: String) -> String {
        let code = code.map(Self.pretty) ?? ""
        var lines = ["\(name) wants to play Motion Club with you!"]
        if let link { lines.append("Tap to join: \(link.absoluteString)") }
        if let store = Bundle.main.object(forInfoDictionaryKey: "ClubAppStoreURL") as? String, !store.isEmpty { lines.append("Get the game: \(store)") }
        lines.append("Then open Friends and enter code \(code)")
        return lines.joined(separator: "\n")
    }

    @available(iOS 26.0, *)
    private static func appleActivity() async -> (code: String, url: URL?)? {
        guard let definition = try? await GKGameActivityDefinition.all.first(where: { $0.identifier == "motionclub.party" }),
              let activity = try? GKGameActivity.start(definition: definition), let code = activity.partyCode else { return nil }
        return (code, activity.partyURL)
    }

    // MARK: notes

    /// The friend's notification for a Game Center invite (their Join opens that invite).
    func notifyInvite(to friendID: String, gcMatch: String, players: Int) {
        guard on, let store, let me = me() else { return }
        let note = CloudNote(kind: .invite, to: friendID, from: me.id, fromGameID: me.gameID, fromName: me.name, detail: gcMatch,
                             players: players, expires: now().addingTimeInterval(GameCenterPartyInvitation.lifetime / 1000))
        Task { try? await store.send(note) }
    }

    /// Host: someone knocked. A friend, or anyone with my current code, comes in when this phone is free and the party has room.
    private func answer(_ k: CloudNote) async {
        guard let store, let me = me() else { return }
        guard k.expires > now() else { handled.insert(k.id); try? await store.delete(note: k); return }
        guard isFriend(k.from) || (code != nil && k.code == code) else { handled.insert(k.id); try? await store.delete(note: k); return }
        // Knocking on each other: the lower gamePlayerID hosts (PartyTieBreak). That phone stops knocking and answers; the other one
        // leaves this knock be and keeps knocking (its owner takes it back).
        if let host = knockingHost, host.id == k.from {
            guard PartyTieBreak.localHosts(local: me.gameID, other: k.fromGameID) else { return }
            cancelKnock()
        }
        // (a match is on, or another handshake: answered after it, while the knock lasts)
        guard canJoinNow(), canHost(), letInTask == nil else { return }
        handled.insert(k.id)
        try? await store.delete(note: k)
        guard let host = hostParty() else { return }
        guard host.size <= host.capacity else {
            try? await store.send(CloudNote(kind: .answer, to: k.from, from: me.id, fromGameID: me.gameID, fromName: me.name, code: k.code,
                                            detail: "full", round: k.round, expires: now().addingTimeInterval(120)))
            return
        }
        try? await store.send(CloudNote(kind: .answer, to: k.from, from: me.id, fromGameID: me.gameID, fromName: me.name, code: k.code,
                                        detail: "go", group: host.group, players: host.size, round: k.round, expires: now().addingTimeInterval(120)))
        letInTask = Task { @MainActor [weak self] in
            guard let self else { return }
            defer { self.letInTask = nil }
            do { try await self.bringIn(k.fromGameID, host.group, host.size); self.joined(k.fromName) }
            catch { SportsDiagnostics.write("cloud: let-in failed: \(error.localizedDescription)") }
        }
    }
    /// Tests: until the let-in started by a knock is over.
    func debugLetIn() async { await letInTask?.value }

    // MARK: going into someone's party

    /// Drop in on a friend's party, or join with a code: knock, wait for the host's go, connect. Up to three tries; plain words.
    func join(code text: String) {
        guard let typed = Self.normalized(text) else { say("That code doesn't look right. It has 6 or 8 letters and numbers."); return }
        guard on, let store, let me = me() else { say("Sign in to iCloud in Settings to join with a code."); return }
        cancelKnock()
        knockTask = Task { @MainActor [weak self] in
            guard let self else { return }
            guard let party = try? await store.party(code: typed) else { self.say("That code isn't working. Check it, or ask for a new one."); return }
            guard party.hostID != me.id else { self.say("That's your own party code."); return }
            guard party.open, party.size < party.capacity else { self.say("\(party.hostName)'s party is full."); return }
            guard !Task.isCancelled else { return }
            // one handshake at a time: this knock is it until it is in or gives up (a player's other Join cancels it)
            guard let token = self.beginKnock(party.hostGameID, { [weak self] in self?.knockTask?.cancel() }) else {
                self.say("Finish joining your friend first."); return
            }
            self.knockToken = token; self.knockingHost = (party.hostID, party.hostGameID)
            var mine: CloudNote?
            defer {
                if self.knockToken == token { self.knockToken = nil; self.knockingHost = nil; self.knocking = nil }
                self.endKnock(token)
                // the knock leaves with the wait (it used to outlive it by minutes, and be let in after the joiner had gone)
                if let note = mine { Task { try? await store.delete(note: note) } }
            }
            self.knocking = (party.hostName, "Asking \(party.hostName) to let you in…")
            for round in 0..<3 {
                guard !Task.isCancelled else { return }
                // the host answers when its game is open and free (the knock also alerts their phone); it lasts as long as this wait
                let deadline = self.now().addingTimeInterval(round == 0 ? 180 : 90)
                if let old = mine { try? await store.delete(note: old) }
                let knock = CloudNote(kind: .knock, to: party.hostID, from: me.id, fromGameID: me.gameID, fromName: me.name,
                                      code: party.code, round: round, expires: deadline)
                mine = knock
                try? await store.send(knock)
                var answer: CloudNote?
                while answer == nil, self.now() < deadline, !Task.isCancelled {
                    try? await Task.sleep(for: self.pollInterval)
                    answer = (try? await store.notes(.answer, to: me.id))?.first { $0.code == party.code && $0.from == party.hostID && $0.round == round }
                }
                guard !Task.isCancelled else { return }
                guard let answer else { self.say("\(party.hostName) didn't answer. Their game may be closed: they got a notification."); return }
                try? await store.delete(note: answer); mine = nil   // (the host took the knock)
                if answer.detail == "full" { self.say("\(party.hostName)'s party is full."); return }
                while !self.canJoinNow() { try? await Task.sleep(for: .seconds(1)); if Task.isCancelled { return } }
                self.knocking = (party.hostName, "Joining \(party.hostName)…")
                do {
                    try await self.connect(party.hostGameID, answer.group, answer.players)
                    self.dropCode(); self.say("You joined \(party.hostName)'s party!")
                    return
                } catch {
                    // (a cancel is the player's, or another Join's: quiet. A connection that timed out says so, and knocks again.)
                    if Task.isCancelled || error is CancellationError { return }
                    SportsDiagnostics.write("cloud: join round \(round) failed: \(error.localizedDescription)")
                }
            }
            self.say("Couldn't connect to \(party.hostName). Check the internet on both phones, then try again.")
        }
    }
    func cancelKnock() {
        knockTask?.cancel(); knockTask = nil; knocking = nil; knockingHost = nil
        if let token = knockToken { knockToken = nil; endKnock(token) }
    }

    // MARK: codes

    /// "abc-234", "ABC234", a link ending in /j/ABC234 or ?c=ABC234 → "ABC234" (6 to 10 letters and numbers).
    static func normalized(_ text: String) -> String? {
        var t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if let url = URL(string: t), let c = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems?.first(where: { $0.name == "c" })?.value { t = c }
        if let r = t.range(of: "/j/", options: [.backwards, .caseInsensitive]) { t = String(t[r.upperBound...]) }
        let code = t.uppercased().filter { $0.isASCII && ($0.isLetter || $0.isNumber) }
        return (6...10).contains(code.count) ? code : nil
    }
    /// ABC234 → ABC-234, for reading out.
    static func pretty(_ code: String) -> String { code.count == 6 || code.count == 8 ? String(code.prefix(code.count / 2)) + "-" + String(code.suffix(code.count / 2)) : code }
}

/// CloudKit's public database. Record types: Player (p-<teamPlayerID>), Party (c-<code>), Invite / Knock / Answer (one per note, with
/// a queryable `to`). Subscriptions alert on Invite and Knock records addressed to this player.
@MainActor final class CloudKitClubStore: ClubCloudStore {
    private let container: CKContainer
    private var db: CKDatabase { container.publicCloudDatabase }
    init(container id: String) { container = CKContainer(identifier: id) }

    func available() async -> Bool { (try? await container.accountStatus()) == .available }

    func save(presence p: HubPresence, id: String, gameID: String, name: String) async throws {
        let r = CKRecord(recordType: "Player", recordID: CKRecord.ID(recordName: "p-" + id))
        r["gameID"] = gameID; r["name"] = name; r["seen"] = Date(); r["state"] = (p.invisible ? HubPresenceState.away : p.state).rawValue
        r["lobby"] = p.invisible ? nil : p.lobby.flatMap { try? JSONEncoder().encode($0) }
        _ = try await db.modifyRecords(saving: [r], deleting: [], savePolicy: .allKeys)
    }
    func presences(_ ids: [String]) async throws -> [String: (state: HubPresenceState, lobby: HubLobbyInfo?, seen: Date)] {
        let found = try await db.records(for: ids.map { CKRecord.ID(recordName: "p-" + $0) })
        var out: [String: (state: HubPresenceState, lobby: HubLobbyInfo?, seen: Date)] = [:]
        for (rid, result) in found {
            guard case .success(let r) = result, let seen = r["seen"] as? Date else { continue }
            let state = (r["state"] as? String).flatMap(HubPresenceState.init(rawValue:)) ?? .away
            let lobby = (r["lobby"] as? Data).flatMap { try? JSONDecoder().decode(HubLobbyInfo.self, from: $0) }
            out[String(rid.recordName.dropFirst(2))] = (state, lobby, seen)
        }
        return out
    }
    func save(party: CloudParty) async throws {
        let r = CKRecord(recordType: "Party", recordID: CKRecord.ID(recordName: "c-" + party.code))
        r["hostID"] = party.hostID; r["hostGameID"] = party.hostGameID; r["hostName"] = party.hostName
        r["group"] = Int64(party.group); r["size"] = party.size; r["capacity"] = party.capacity; r["open"] = party.open ? 1 : 0
        _ = try await db.modifyRecords(saving: [r], deleting: [], savePolicy: .allKeys)
    }
    func party(code: String) async throws -> CloudParty? {
        do {
            let r = try await db.record(for: CKRecord.ID(recordName: "c-" + code))
            guard let host = r["hostID"] as? String, let game = r["hostGameID"] as? String, let group = r["group"] as? Int64 else { return nil }
            return CloudParty(code: code, hostID: host, hostGameID: game, hostName: r["hostName"] as? String ?? "Your friend", group: UInt32(truncatingIfNeeded: group),
                              size: r["size"] as? Int ?? 1, capacity: r["capacity"] as? Int ?? 4, open: (r["open"] as? Int ?? 1) == 1)
        } catch let e as CKError where e.code == .unknownItem { return nil }
    }
    private static func type(_ kind: CloudNote.Kind) -> String { kind == .invite ? "Invite" : kind == .knock ? "Knock" : "Answer" }
    func send(_ n: CloudNote) async throws {
        let r = CKRecord(recordType: Self.type(n.kind), recordID: CKRecord.ID(recordName: n.id))
        r["to"] = n.to; r["from"] = n.from; r["fromGameID"] = n.fromGameID; r["fromName"] = n.fromName; r["code"] = n.code
        r["detail"] = n.detail; r["group"] = Int64(n.group); r["players"] = n.players; r["round"] = n.round; r["expires"] = n.expires
        r["message"] = n.message
        _ = try await db.save(r)
    }
    func notes(_ kind: CloudNote.Kind, to id: String) async throws -> [CloudNote] {
        let query = CKQuery(recordType: Self.type(kind), predicate: NSPredicate(format: "to == %@", id))
        let (results, _) = try await db.records(matching: query, resultsLimit: 20)
        return results.compactMap { rid, result in
            guard case .success(let r) = result else { return nil }
            return CloudNote(id: rid.recordName, kind: kind, to: id, from: r["from"] as? String ?? "", fromGameID: r["fromGameID"] as? String ?? "",
                             fromName: r["fromName"] as? String ?? "A friend", code: r["code"] as? String ?? "", detail: r["detail"] as? String ?? "",
                             group: UInt32(truncatingIfNeeded: r["group"] as? Int64 ?? 0), players: r["players"] as? Int ?? 0, round: r["round"] as? Int ?? 0,
                             expires: r["expires"] as? Date ?? .distantPast)
        }
    }
    func delete(note: CloudNote) async throws { _ = try await db.deleteRecord(withID: CKRecord.ID(recordName: note.id)) }

    /// Alerts for Invite and Knock records addressed to me ("Ann wants to play with you!" / "… wants to join your party"), with the
    /// Join / Not now buttons on invites (ClubPush.category).
    func subscribe(id: String) async throws {
        func subscription(_ type: String, category: String?) -> CKQuerySubscription {
            let s = CKQuerySubscription(recordType: type, predicate: NSPredicate(format: "to == %@", id),
                                        subscriptionID: "\(type)-\(id)", options: [.firesOnRecordCreation])
            let info = CKSubscription.NotificationInfo()
            info.titleLocalizationKey = "Motion Club"
            info.alertLocalizationKey = "CLUB_NOTE"; info.alertLocalizationArgs = ["message"]
            info.desiredKeys = ["from", "fromGameID", "fromName", "detail", "players", "expires", "code"]
            info.soundName = "default"; info.category = category
            s.notificationInfo = info
            return s
        }
        _ = try await db.modifySubscriptions(saving: [subscription("Invite", category: ClubPush.category), subscription("Knock", category: nil)], deleting: [])
    }
}

extension ClubPush {
    /// A CloudKit alert (an Invite or Knock record addressed to this player): the Game Center invite it opens, or nil for a knock.
    static func cloudInvite(from userInfo: [AnyHashable: Any]) -> (invite: HubInvite?, knock: Bool)? {
        guard let note = CKNotification(fromRemoteNotificationDictionary: userInfo) as? CKQueryNotification,
              let sub = note.subscriptionID else { return nil }
        if sub.hasPrefix("Knock-") { return (nil, true) }
        guard sub.hasPrefix("Invite-"), let f = note.recordFields, let match = f["detail"] as? String, !match.isEmpty else { return nil }
        let expires = (f["expires"] as? Date)?.timeIntervalSince1970 ?? Date().timeIntervalSince1970 + 600
        return (HubInvite(inviteID: "gc:" + match, from: HubPlayerRef(id: f["fromGameID"] as? String ?? "", name: f["fromName"] as? String ?? "A friend"),
                          sport: "party", lobbyCode: match, group: 0, capacity: f["players"] as? Int ?? 2, expiresAt: expires * 1000), false)
    }
}
