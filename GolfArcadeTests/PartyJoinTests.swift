import XCTest
@testable import GolfArcade

/// Joining a friend's party reliably: the party link's pieces (2026-10-27: the leader's group, the party kept across a relaunch,
/// what the link does next, Apple's error 4), crossed invites and knocks settled the same way on both phones (PartyTieBreak), a
/// relaunch that resumes only a fresh Join (JoinMemory), CloudKit knocks that leave with their wait, and onboarding that steps aside
/// for a party. The link end to end: PartyLinkHarnessTests. Game Center itself is a two-phone gate.
@MainActor
final class PartyJoinTests: XCTestCase {
    // MARK: the party link

    func testEveryPartyHasOneGroupWorkedOutFromItsLeader() {
        let ids = (0..<500).map { "G:\($0 * 7919)" } + ["A:_d651b", "T:_9f65u6", ""]
        for id in ids {
            XCTAssertEqual(PartyGroup.of(id), PartyGroup.of(id))
            XCTAssertTrue(PartyGroup.valid(PartyGroup.of(id)), "in the private range invitations accept")
            var invitation = GameCenterPartyInvitation(host: id + "h", recipient: "me", name: "n", group: PartyGroup.of(id), players: ["me", id + "h"], expiresAt: 2_000)
            invitation.step = .invited
            XCTAssertTrue(invitation.valid(for: "me", now: 1_000))
        }
        XCTAssertEqual(Set(ids.map(PartyGroup.of)).count, ids.count, "different leaders, different groups")
        // pinned: the number must never change between builds (two phones on two builds still meet)
        XCTAssertEqual(PartyGroup.of("G:1"), 0x69375dbf)
        XCTAssertEqual(PartyGroup.of("A:_d651b"), 0x6e3b9eeb)
    }

    func testThePartyIsKeptAcrossARelaunchForAsLongAsAPartyWaits() {
        let saved = PartyMemory.defaults
        defer { PartyMemory.defaults = saved }
        PartyMemory.defaults = UserDefaults(suiteName: "party-memory-\(UUID())")!
        let m = PartyMemory(leader: "H", leaderName: "Ann", members: ["H", "J"], at: 1_000)
        PartyMemory.save(m, "J")
        XCTAssertEqual(PartyMemory.load("J", now: 1_000 + 599, patience: 600), m)
        XCTAssertNil(PartyMemory.load("J", now: 1_000 + 601, patience: 600), "too long ago")
        XCTAssertNil(PartyMemory.load("K", now: 1_000, patience: 600), "another player's")
        PartyMemory.save(m, "K")
        XCTAssertNil(PartyMemory.load("K", now: 1_000, patience: 600), "a party this player is not in")
        PartyMemory.save(nil, "J")
        XCTAssertNil(PartyMemory.load("J", now: 1_000, patience: 600), "left on purpose: forgotten")
    }

    func testWhatTheLinkDoesNext() {
        typealias Plan = PartyLinkPlan
        func input(_ local: String = "J", _ change: (inout Plan.Input) -> Void = { _ in }) -> Plan.Input {
            var s = Plan.Input(local: local, now: 1_000, patience: 600); change(&s); return s
        }
        let h = PartyGroup.of("H"), j = PartyGroup.of("J")
        let member = PartyMemory(leader: "H", leaderName: "Ann", members: ["H", "J"], at: 900)
        let leader = PartyMemory(leader: "J", leaderName: "Bea", members: ["H", "J"], at: 900)
        XCTAssertEqual(Plan.next(input()), .idle, "no party, nobody invited")
        // a Join: the leader's group until the leader is there, once in the Plaza
        XCTAssertEqual(Plan.next(input { $0.join = ("H", 2) }), .find(group: h, min: 2, max: 2, need: ["H"]))
        XCTAssertEqual(Plan.next(input { $0.join = ("H", 3) }), .find(group: h, min: 2, max: 3, need: ["H"]))
        XCTAssertEqual(Plan.next(input { $0.join = ("H", 2); $0.connected = ["H"] }), .idle)
        XCTAssertEqual(Plan.next(input { $0.join = ("H", 2); $0.canJoin = false }), .wait("joining once this phone is back in the Plaza"))
        XCTAssertEqual(Plan.next(input { $0.join = ("H", 2); $0.active = false }), .wait("in the background"))
        XCTAssertEqual(Plan.next(input { $0.join = ("H", 2); $0.signedIn = false }), .wait("not signed in to Game Center"))
        XCTAssertEqual(Plan.next(input { $0.join = ("H", 2); $0.quickMatch = true }), .wait("a quick match is searching"))
        // a member: back into the leader's group whenever the leader is gone (a match on or not), until a party has waited long enough
        XCTAssertEqual(Plan.next(input { $0.party = member; $0.inLobby = true; $0.connected = ["H"] }), .idle)
        XCTAssertEqual(Plan.next(input { $0.party = member; $0.inLobby = true; $0.missingSince = ["H": 990]; $0.canJoin = false }),
                       .find(group: h, min: 2, max: 2, need: ["H"]), "mid-match too: it is this phone's own party")
        XCTAssertEqual(Plan.next(input { $0.party = member; $0.missingSince = ["H": 990]; $0.canJoin = false }),
                       .wait("back into the party once this phone is in the Plaza"), "after a relaunch: the Plaza first")
        XCTAssertEqual(Plan.next(input { $0.party = member; $0.inLobby = true; $0.missingSince = ["H": 1_000 - 601] }), .lost)
        var left = member; left.members = ["J", "K"]
        XCTAssertEqual(Plan.next(input { $0.party = left; $0.inLobby = true; $0.connected = ["K"] }), .wait("the leader left; the party picks a new one"),
                       "a leader who left on purpose is not looked for")
        // a leader: its own group, for members who dropped (any time) and friends it invited (in the Plaza)
        XCTAssertEqual(Plan.next(input { $0.party = leader; $0.inLobby = true; $0.connected = ["H"]; $0.matchAlive = true }), .idle)
        XCTAssertEqual(Plan.next(input { $0.party = leader; $0.inLobby = true; $0.missingSince = ["H": 990] }), .find(group: j, min: 2, max: 2, need: ["H"]))
        XCTAssertEqual(Plan.next(input { $0.party = leader; $0.inLobby = true; $0.missingSince = ["H": 990]; $0.canHost = false }),
                       .find(group: j, min: 2, max: 2, need: ["H"]), "a dropped member comes back mid-match")
        XCTAssertEqual(Plan.next(input { $0.party = leader; $0.inLobby = true; $0.missingSince = ["H": 300] }), .idle, "gone too long")
        XCTAssertEqual(Plan.next(input { $0.expected = ["K"] }), .find(group: j, min: 2, max: 2, need: ["K"]), "invited: the leader looks in its group")
        XCTAssertEqual(Plan.next(input { $0.expected = ["K", "L"] }), .find(group: j, min: 2, max: 3, need: ["K", "L"]))
        XCTAssertEqual(Plan.next(input { $0.expected = ["K"]; $0.canHost = false }), .wait("friends come in after this match"))
        XCTAssertEqual(Plan.next(input { $0.party = leader; $0.inLobby = true; $0.expected = ["K"]; $0.connected = ["H"]; $0.matchAlive = true }),
                       .add(group: j, min: 3, max: 3, need: ["K"]), "into the live match the friends are in")
        XCTAssertEqual(Plan.next(input { $0.party = leader; $0.inLobby = true; $0.expected = ["K"]; $0.connected = ["H", "L", "M"]; $0.matchAlive = true }),
                       .wait("the party is full"))
    }

    /// GameCenterFoundation.FastSyncTransportError error 4 (`groupSessionInvalidated`) and 1 (`illegalState`): Apple ended the match.
    /// The player never reads that text.
    func testApplesError4MeansTheMatchIsGoneAndIsNeverShown() {
        let four = NSError(domain: "GameCenterFoundation.FastSyncTransportError", code: 4)
        XCTAssertTrue(GameCenterTransport.sessionGone(four))
        XCTAssertTrue(GameCenterTransport.sessionGone(NSError(domain: "GameCenterFoundation.FastSyncTransportError", code: 1)))
        XCTAssertFalse(GameCenterTransport.sessionGone(NSError(domain: "GameCenterFoundation.FastSyncTransportError", code: 3)), "a send that was too big")
        XCTAssertFalse(GameCenterTransport.sessionGone(NSError(domain: NSURLErrorDomain, code: 4)))
        let words = GameCenterTransport.friendly(four, "Reconnecting to your party…").localizedDescription
        XCTAssertEqual(words, "Reconnecting to your party…")
    }

    // MARK: crossed invites

    private func invitation(_ host: String, _ to: String, step: GameCenterPartyInvitation.Step = .invited, party: [String] = []) -> GameCenterPartyInvitation {
        var i = GameCenterPartyInvitation(host: host, recipient: to, name: host, group: 0x60000020, players: Array(Set([host, to] + party)).sorted(), expiresAt: 1e15)
        i.step = step; return i
    }

    func testCrossedInvitationsKeepOneTheSameOnBothPhones() {
        let steps: [GameCenterPartyInvitation.Step] = [.invited, .accepted, .go]
        let parties: [[String]] = [[], ["c"], ["c", "d"]]
        for (a, b) in [("G:111", "G:222"), ("G:999", "G:123")] {
            for sa in steps { for sb in steps { for pa in parties { for pb in parties {
                let mine = invitation(a, b, step: sa, party: pa), theirs = invitation(b, a, step: sb, party: pb)
                XCTAssertNotEqual(PartyTieBreak.keeps(mine, over: theirs), PartyTieBreak.keeps(theirs, over: mine), "exactly one stays")
                let onA = PartyTieBreak.losers([("m", mine), ("t", theirs)], local: a)
                let onB = PartyTieBreak.losers([("t", theirs), ("m", mine)], local: b)
                XCTAssertEqual(onA, onB, "both phones retire the same record"); XCTAssertEqual(onA.count, 1)
            } } } }
        }
        // the rules, in order
        XCTAssertTrue(PartyTieBreak.keeps(invitation("z", "a", step: .accepted), over: invitation("a", "z")), "the one somebody said Join to")
        XCTAssertTrue(PartyTieBreak.keeps(invitation("z", "a", party: ["c"]), over: invitation("a", "z")), "the bigger party's")
        XCTAssertTrue(PartyTieBreak.keeps(invitation("a", "z"), over: invitation("z", "a")), "else the lower gamePlayerID hosts")
        // invitations that did not cross (other friends, or only one way) are left alone
        XCTAssertEqual(PartyTieBreak.losers([("1", invitation("a", "b")), ("2", invitation("c", "a")), ("3", invitation("a", "d"))], local: "a"), [])
        XCTAssertTrue(PartyTieBreak.localHosts(local: "G:1", other: "G:2")); XCTAssertFalse(PartyTieBreak.localHosts(local: "G:2", other: "G:1"))
    }

    // MARK: a relaunch resumes only a fresh Join

    func testOnlyAJoinTappedAMomentAgoCarriesOnAfterARelaunch() {
        let saved = (JoinMemory.defaults, JoinMemory.now)
        defer { JoinMemory.defaults = saved.0; JoinMemory.now = saved.1 }
        JoinMemory.defaults = UserDefaults(suiteName: "join-memory-\(UUID())")!
        var t = 1_000.0
        JoinMemory.now = { t }
        XCTAssertFalse(JoinMemory.recent("gc:m1"))
        JoinMemory.tapped("gc:m1")
        t += 60; XCTAssertTrue(JoinMemory.recent("gc:m1"), "the app closed under a Join: it carries on")
        t += JoinMemory.window; XCTAssertFalse(JoinMemory.recent("gc:m1"), "an old Join waits for a tap")
        JoinMemory.tapped("gc:m2"); JoinMemory.forget("gc:m2"); XCTAssertFalse(JoinMemory.recent("gc:m2"), "a failed or cancelled join is forgotten")
    }

    // MARK: CloudKit knocks

    /// CloudKit's public database in memory, which can be away at first (no iCloud yet, no network at launch).
    @MainActor final class Store: ClubCloudStore {
        var up = true, asked = 0
        var parties: [String: CloudParty] = [:]
        var notes: [CloudNote] = []
        var players: [String: (state: HubPresenceState, lobby: HubLobbyInfo?, seen: Date)] = [:]
        func available() async -> Bool { asked += 1; return up }
        func save(presence: HubPresence, id: String, gameID: String, name: String) async throws { players[id] = (presence.state, presence.lobby, Date()) }
        func presences(_ ids: [String]) async throws -> [String: (state: HubPresenceState, lobby: HubLobbyInfo?, seen: Date)] { players.filter { ids.contains($0.key) } }
        func save(party: CloudParty) async throws { parties[party.code] = party }
        func party(code: String) async throws -> CloudParty? { parties[code] }
        func send(_ note: CloudNote) async throws { notes.append(note) }
        func notes(_ kind: CloudNote.Kind, to id: String) async throws -> [CloudNote] { notes.filter { $0.kind == kind && $0.to == id } }
        func delete(note: CloudNote) async throws { notes.removeAll { $0.id == note.id } }
        func subscribe(id: String) async throws {}
    }
    final class Log { var lines: [String] = [], said: [String] = [] }
    private func phone(_ store: Store, _ id: String, friends: [String]) -> (cloud: ClubCloud, log: Log) {
        let c = ClubCloud(store: store), log = Log()
        c.me = { (id, "g-" + id, id.capitalized) }
        c.isFriend = { friends.contains($0) }
        c.hostParty = { (0x60000021, 2, 4) }
        c.bringIn = { gameID, _, _ in log.lines.append("in \(gameID)") }
        c.connect = { host, _, _ in log.lines.append("to \(host)") }
        c.say = { log.said.append($0) }
        c.pollInterval = .milliseconds(20)
        return (c, log)
    }
    private func until(_ what: String, _ condition: () -> Bool, file: StaticString = #filePath, line: UInt = #line) async {
        for _ in 0..<300 { if condition() { return }; try? await Task.sleep(for: .milliseconds(10)) }
        XCTFail("timed out waiting for \(what)", file: file, line: line)
    }

    /// Ann and Bea drop in on each other at the same moment: the lower gamePlayerID (Ann) hosts, Bea goes in, and Ann's own knock
    /// leaves with her wait (it is never let in afterwards).
    func testCrossedKnocksMeetInOneParty() async {
        let store = Store()
        let ann = phone(store, "ann", friends: ["bea"]), bea = phone(store, "bea", friends: ["ann"])
        defer { ann.cloud.stop(); bea.cloud.stop(); ann.cloud.cancelKnock(); bea.cloud.cancelKnock() }
        ann.cloud.start(); bea.cloud.start()
        await until("on") { ann.cloud.on && bea.cloud.on }
        await ann.cloud.tick(); await bea.cloud.tick()
        let annCode = try! XCTUnwrap(ann.cloud.code), beaCode = try! XCTUnwrap(bea.cloud.code)
        ann.cloud.join(code: beaCode); bea.cloud.join(code: annCode)
        await until("both knocked") { store.notes.filter { $0.kind == .knock }.count == 2 }
        await bea.cloud.tick()
        XCTAssertTrue(bea.log.lines.isEmpty, "Bea leaves Ann's knock be: Ann hosts")
        await ann.cloud.tick(); await ann.cloud.debugLetIn()
        await until("Bea in") { bea.log.lines == ["to g-ann"] }
        XCTAssertEqual(ann.log.lines, ["in g-bea"])
        await until("Ann's knock gone") { !store.notes.contains { $0.kind == .knock } }
        await bea.cloud.tick()
        XCTAssertEqual(bea.log.lines, ["to g-ann"], "nobody is let in twice")
        XCTAssertNil(ann.cloud.knocking)
    }

    /// A knock lasts as long as its wait and leaves with it (it used to outlive the joiner by minutes); the tick goes on while a
    /// let-in connects (it used to wait for it, up to 80 s); and a second knock waits for the first let-in.
    func testKnocksLeaveWithTheirWaitAndLetInsDoNotStallTheTick() async {
        let store = Store()
        let ann = phone(store, "ann", friends: ["bea", "cy"]), bea = phone(store, "bea", friends: ["ann"]), cy = phone(store, "cy", friends: ["ann"])
        defer { for p in [ann, bea, cy] { p.cloud.stop(); p.cloud.cancelKnock() } }
        var t = Date(timeIntervalSince1970: 1_000_000)
        bea.cloud.now = { t }
        for p in [ann, bea, cy] { p.cloud.start() }
        await until("on") { ann.cloud.on && bea.cloud.on && cy.cloud.on }
        await ann.cloud.tick()
        let code = try! XCTUnwrap(ann.cloud.code)
        // nobody answers Bea: her knock expires with her wait, and goes when she stops waiting
        bea.cloud.join(code: code)
        await until("knocked") { store.notes.contains { $0.kind == .knock && $0.from == "bea" } }
        XCTAssertEqual(store.notes.first { $0.from == "bea" }?.expires, t.addingTimeInterval(180))
        t = t.addingTimeInterval(181)
        await until("gave up") { bea.log.said.last?.hasPrefix("Ann didn't answer") == true }
        await until("knock gone") { !store.notes.contains { $0.kind == .knock && $0.from == "bea" } }
        // Cy knocks; Ann's let-in hangs (a slow connection): the tick still returns, and a second knock waits
        var release: CheckedContinuation<Void, Never>?
        ann.cloud.bringIn = { gameID, _, _ in ann.log.lines.append("in \(gameID)"); await withCheckedContinuation { release = $0 } }
        cy.cloud.join(code: code)
        await until("Cy knocked") { store.notes.contains { $0.kind == .knock && $0.from == "cy" } }
        await ann.cloud.tick()
        await until("letting Cy in") { ann.log.lines == ["in g-cy"] }
        bea.cloud.now = { Date() }
        bea.cloud.join(code: code)
        await until("Bea knocked again") { store.notes.contains { $0.kind == .knock && $0.from == "bea" } }
        await ann.cloud.tick()
        XCTAssertEqual(ann.log.lines, ["in g-cy"], "one let-in at a time")
        release?.resume(); await ann.cloud.debugLetIn()
        ann.cloud.bringIn = { gameID, _, _ in ann.log.lines.append("in \(gameID)") }
        await ann.cloud.tick(); await ann.cloud.debugLetIn()
        XCTAssertEqual(ann.log.lines, ["in g-cy", "in g-bea"])
    }

    /// CloudKit away at launch is asked again (it used to be off for the whole run); invite notes go once the game is open, and so do
    /// answers that ran out.
    func testCloudKitIsAskedAgainAndOldNotesAreCleanedUp() async {
        let store = Store(); store.up = false
        let ann = phone(store, "ann", friends: [])
        ann.cloud.availabilityRetry = .milliseconds(20)
        defer { ann.cloud.stop() }
        ann.cloud.start()
        await until("asked again") { store.asked >= 2 }
        XCTAssertFalse(ann.cloud.on)
        store.up = true
        await until("on") { ann.cloud.on }
        let past = Date().addingTimeInterval(-10), later = Date().addingTimeInterval(600)
        store.notes = [CloudNote(kind: .invite, to: "ann", from: "bea", fromGameID: "g-bea", fromName: "Bea", detail: "m1", expires: later),
                       CloudNote(kind: .answer, to: "ann", from: "bea", fromGameID: "g-bea", fromName: "Bea", expires: past),
                       CloudNote(kind: .answer, to: "ann", from: "cy", fromGameID: "g-cy", fromName: "Cy", expires: later),
                       CloudNote(kind: .invite, to: "dee", from: "bea", fromGameID: "g-bea", fromName: "Bea", expires: later)]
        await ann.cloud.tick()
        XCTAssertEqual(store.notes.map(\.to), ["ann", "dee"], "only someone else's notes and a live answer stay")
        XCTAssertEqual(store.notes.first?.kind, .answer)
    }

    // MARK: onboarding steps aside for a party

    func testOnboardingStepsAsideWhileJoiningOrInAPartyAndComesBack() {
        let d = UserDefaults(suiteName: "onboarding-party-\(UUID())")!
        let flow = OnboardingFlow(store: OnboardingStore(defaults: d), progress: SportProgress(defaults: d), arguments: [])
        var party = false
        flow.partyWaits = { party }
        XCTAssertTrue(flow.active); XCTAssertTrue(flow.holdsMenu)
        party = true
        XCTAssertFalse(flow.holdsMenu, "the Plaza (or the phone's own Plaza with no TV) while joining or in a party")
        XCTAssertTrue(flow.active, "onboarding is put off, not finished")
        party = false
        XCTAssertTrue(flow.holdsMenu, "and comes back where it was once the party is over")
        XCTAssertEqual(flow.step, .hello)
    }
}
