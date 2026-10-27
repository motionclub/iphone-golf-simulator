import XCTest
@testable import GolfArcade

/// Joining a friend's party reliably (2026-10-26): one handshake at a time per phone (PartyJoinCoordinator), crossed invites and
/// knocks settled the same way on both phones (PartyTieBreak), a relaunch that resumes only a fresh Join (JoinMemory), CloudKit
/// knocks that leave with their wait, and onboarding that steps aside for a party. Game Center itself is a two-phone gate
/// (work/party-join-2026-10-26/TWO_PHONE_TEST.md).
@MainActor
final class PartyJoinTests: XCTestCase {
    typealias Coordinator = PartyJoinCoordinator

    // MARK: one handshake at a time

    func testCoordinatorRules() {
        func h(_ kind: Coordinator.Kind, _ origin: Coordinator.Origin = .player) -> Coordinator.Handshake { .init(token: 1, kind: kind, origin: origin) }
        let decide = Coordinator.decide
        // nothing running: anything starts, but an automatic join never takes the phone out of a party with friends in it
        XCTAssertEqual(decide(.joinInvite("r"), .player, nil, false), .start)
        XCTAssertEqual(decide(.joinInvite("r"), .automatic, nil, false), .start)
        XCTAssertEqual(decide(.joinInvite("r"), .automatic, nil, true), .refuse(.inParty))
        XCTAssertEqual(decide(.joinInvite("r"), .player, nil, true), .start, "a Join the player taps leaves the party for the new one")
        XCTAssertEqual(decide(.hostInvite("r"), .player, nil, true), .start, "hosting more friends from a party is fine")
        // no host role while joining; one host handshake at a time
        XCTAssertEqual(decide(.hostInvite("r"), .player, h(.joinInvite("x")), false), .refuse(.joining))
        XCTAssertEqual(decide(.hostKnock("g"), .player, h(.joinKnock("x")), false), .refuse(.joining))
        XCTAssertEqual(decide(.hostKnock("g"), .player, h(.hostInvite("x")), false), .refuse(.busy), "a let-in no longer aborts a bring-in")
        XCTAssertEqual(decide(.hostInvite("y"), .player, h(.hostKnock("g")), false), .refuse(.busy))
        // the same handshake twice: already happening
        XCTAssertEqual(decide(.joinInvite("x"), .player, h(.joinInvite("x")), false), .refuse(.busy))
        XCTAssertEqual(decide(.hostInvite("x"), .player, h(.hostInvite("x")), false), .refuse(.busy))
        // a player's join wins over anything; an automatic one over nothing
        XCTAssertEqual(decide(.joinInvite("y"), .player, h(.joinInvite("x")), false), .supersede)
        XCTAssertEqual(decide(.joinKnock("g"), .player, h(.hostInvite("x")), false), .supersede)
        XCTAssertEqual(decide(.joinRealTime("g"), .player, h(.joinKnock("h")), false), .supersede)
        XCTAssertEqual(decide(.joinInvite("y"), .automatic, h(.joinInvite("x")), false), .refuse(.busy))
        XCTAssertEqual(decide(.joinInvite("y"), .automatic, h(.hostInvite("x")), false), .refuse(.busy))
    }

    func testCoordinatorTokensCancelsAndEnds() {
        let c = Coordinator()
        var inParty = false
        c.inConnectedParty = { inParty }
        var cancelled: [Int] = []
        let host = try! XCTUnwrap(c.begin(.hostInvite("r1"), cancel: { cancelled.append($0) }))
        XCTAssertTrue(c.hosting); XCTAssertFalse(c.joining); XCTAssertTrue(c.isCurrent(host))
        XCTAssertNil(c.begin(.hostKnock("g")), "one host handshake at a time")
        XCTAssertNil(c.begin(.joinInvite("r2"), origin: .automatic), "a rejoin does not cancel a bring-in")
        XCTAssertEqual(cancelled, [])
        // the player taps Join: the bring-in is cancelled (its search stops), the join runs
        let join = try! XCTUnwrap(c.begin(.joinInvite("r2"), cancel: { cancelled.append($0) }))
        XCTAssertEqual(cancelled, [host]); XCTAssertFalse(c.isCurrent(host)); XCTAssertTrue(c.joining)
        c.end(host)
        XCTAssertTrue(c.isCurrent(join), "the cancelled handshake's own end changes nothing")
        XCTAssertNil(c.begin(.hostInvite("r3")), "no host role while joining")
        XCTAssertNil(c.begin(.joinInvite("r2")), "the same join is already happening")
        c.cancel { $0.hosting }
        XCTAssertTrue(c.isCurrent(join), "leaving a party stops bringing people in, not a join")
        c.cancel { if case .joinInvite = $0 { return true }; return false }
        XCTAssertEqual(cancelled, [host, join]); XCTAssertNil(c.active)
        // an automatic join waits for a party with friends in it to be over
        inParty = true
        XCTAssertNil(c.begin(.joinInvite("r4"), origin: .automatic))
        inParty = false
        let auto = try! XCTUnwrap(c.begin(.joinInvite("r4"), origin: .automatic))
        c.end(auto); XCTAssertNil(c.active)
        XCTAssertNotEqual(c.ticket(), c.ticket(), "quick-match searches get their own numbers")
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
