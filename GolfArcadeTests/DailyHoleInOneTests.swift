import XCTest
@testable import GolfArcade

/// The Daily Hole in One's phone half (DailyHoleInOne.swift): the score curve (the same as Unity's DailyHoleInOne.Score), the
/// UTC day everyone shares, one counted go a day, the world standing's words, and the board the TV draws.
@MainActor
final class DailyHoleInOneTests: XCTestCase {
    private final class FakeBoard: HoleInOneLeaderboard, @unchecked Sendable {
        var submitted: [(Int, Int)] = []
        var page = HoleInOnePage(entries: [], local: nil, players: 0)
        var fail: Error?
        func submit(_ score: Int, day: Int) async throws { submitted.append((score, day)) }
        func load(size: Int) async throws -> HoleInOnePage { if let fail { throw fail }; return page }
    }

    private func make(_ date: String = "2026-11-15T12:00:00Z") -> (DailyHoleInOne, FakeBoard) {
        let defaults = UserDefaults(suiteName: "DailyHoleInOneTests-\(UUID().uuidString)")!
        let daily = DailyHoleInOne(defaults: defaults)
        let fake = FakeBoard()
        daily.leaderboard = fake
        daily.changed = {}
        let now = ISO8601DateFormatter().date(from: date)!
        daily.now = { now }
        return (daily, fake)
    }

    func testScoreCurve() {
        XCTAssertEqual(DailyHoleInOne.score(feet: 0, holed: true), 1000)
        XCTAssertEqual(DailyHoleInOne.score(feet: 0, holed: false), 800, "the best miss is 800")
        XCTAssertEqual(DailyHoleInOne.score(feet: 5, holed: false), 758, "= Unity's DailyHoleInOneTests")
        XCTAssertEqual(DailyHoleInOne.score(feet: 7, holed: false), 741)
        XCTAssertEqual(DailyHoleInOne.score(feet: 10, holed: false), 717)
        XCTAssertEqual(DailyHoleInOne.score(feet: 75, holed: false), 280)
        XCTAssertEqual(DailyHoleInOne.score(feet: 149, holed: false), 2)
        XCTAssertEqual(DailyHoleInOne.score(feet: 150, holed: false), 0)
        XCTAssertEqual(DailyHoleInOne.score(feet: 400, holed: false), 0)
        XCTAssertEqual(DailyHoleInOne.score(feet: -1, holed: false), 0, "in a hazard")
        // every foot counts: each foot closer is worth at least 2 more points, all the way out to 150 ft
        for feet in 0..<150 {
            let near = DailyHoleInOne.score(feet: Double(feet), holed: false), far = DailyHoleInOne.score(feet: Double(feet + 1), holed: false)
            XCTAssertGreaterThanOrEqual(near - far, 2, "\(feet) ft vs \(feet + 1) ft")
            XCTAssertLessThanOrEqual(near, DailyHoleInOne.maxMissShot)
        }
        for tenth in 0..<1500 { XCTAssertGreaterThanOrEqual(DailyHoleInOne.score(feet: Double(tenth) / 10, holed: false), DailyHoleInOne.score(feet: Double(tenth + 1) / 10, holed: false)) }
    }

    func testDayIsEastern() {
        let f = ISO8601DateFormatter()
        XCTAssertEqual(DailyHoleInOne.day(of: f.date(from: "2026-11-16T04:59:59Z")!), 20261115, "11:59 pm Eastern is still the 15th")
        XCTAssertEqual(DailyHoleInOne.day(of: f.date(from: "2026-11-16T05:00:00Z")!), 20261116, "12 midnight Eastern starts the 16th")
        XCTAssertEqual(DailyHoleInOne.day(of: f.date(from: "2026-11-15T20:00:00-08:00")!), 20261115, "the same day for the whole world")
        XCTAssertEqual(DailyHoleInOne.day(of: f.date(from: "2026-07-01T03:59:59Z")!), 20260630, "summer time: midnight Eastern is 04:00 UTC")
        XCTAssertEqual(DailyHoleInOne.day(of: f.date(from: "2026-07-01T04:00:00Z")!), 20260701)
    }

    func testPercentileAndTop() {
        XCTAssertEqual(DailyHoleInOne.percentile(rank: 1, players: 100), 100)
        XCTAssertEqual(DailyHoleInOne.percentile(rank: 100, players: 100), 0)
        XCTAssertEqual(DailyHoleInOne.percentile(rank: 13, players: 100), 88)
        XCTAssertEqual(DailyHoleInOne.top(rank: 13, players: 100), 13)
        XCTAssertEqual(DailyHoleInOne.top(rank: 1, players: 4210), 1)
        XCTAssertEqual(DailyHoleInOne.percentile(rank: 1, players: 1), 100, "alone on the board")
    }

    func testResultLineParses() throws {
        let r = try XCTUnwrap(HoleInOneResult(line: "day=20261115;total=2337;s1=1000;f1=0.0;h1=12;s2=640;f2=11.6;h2=7;s3=697;f3=10.0;h3=20"))
        XCTAssertEqual(r.day, 20261115); XCTAssertEqual(r.total, 2337)
        XCTAssertEqual(r.shots, [1000, 640, 697]); XCTAssertEqual(r.feet, [0, 11.6, 10])
        XCTAssertNil(HoleInOneResult(line: "total=12"), "no day, no result")
        XCTAssertEqual(HoleInOneResult(line: "day=1;total=99999")?.total, 3000, "clamped to the maximum")
    }

    func testFirstGoOfTheDayCountsAndIsSubmitted() async {
        let (daily, fake) = make()
        fake.page = HoleInOnePage(entries: [HoleInOneEntry(rank: 1, name: "Ann", score: 2900, me: false),
                                            HoleInOneEntry(rank: 2, name: "Me", score: 2337, me: true)],
                                  local: HoleInOneEntry(rank: 2, name: "Me", score: 2337, me: true), players: 50)
        let first = HoleInOneResult(day: 20261115, total: 2337, shots: [1000, 640, 697], feet: [0, 11.6, 10])
        XCTAssertTrue(daily.finished(first))
        await daily.submitAndLoad(first)
        XCTAssertTrue(daily.playedToday)
        XCTAssertEqual(fake.submitted.first?.0, 2337); XCTAssertEqual(fake.submitted.first?.1, 20261115)
        XCTAssertEqual(daily.standing, HoleInOneStanding(rank: 2, players: 50))
        XCTAssertEqual(daily.standing?.top, 4)
        XCTAssertEqual(daily.boardState, .live)
        // a second go the same day is practice: the first result stays
        XCTAssertFalse(daily.finished(HoleInOneResult(day: 20261115, total: 3000, shots: [1000, 1000, 1000], feet: [0, 0, 0])))
        XCTAssertEqual(daily.todayResult?.total, 2337)
        // yesterday's result never counts for today
        XCTAssertFalse(daily.finished(HoleInOneResult(day: 20261114, total: 100, shots: [100, 0, 0], feet: [100, -1, -1])))
    }

    func testBoardJSONForTheTV() async throws {
        let (daily, fake) = make()
        fake.page = HoleInOnePage(entries: [HoleInOneEntry(rank: 1, name: "Ann", score: 2900, me: false)],
                                  local: HoleInOneEntry(rank: 7, name: "Me", score: 1800, me: true), players: 7)
        daily.finished(HoleInOneResult(day: 20261115, total: 1800, shots: [800, 500, 500], feet: [0.1, 20, 20]))
        await daily.load()
        let json = try XCTUnwrap(try JSONSerialization.jsonObject(with: Data(daily.boardJSON().utf8)) as? [String: Any])
        XCTAssertEqual(json["day"] as? Int, 20261115)
        XCTAssertEqual(json["played"] as? Bool, true)
        XCTAssertEqual(json["total"] as? Int, 1800)
        XCTAssertEqual(json["state"] as? String, "live")
        XCTAssertEqual(json["rank"] as? Int, 7); XCTAssertEqual(json["players"] as? Int, 7)
        XCTAssertEqual(json["percentile"] as? Int, 0); XCTAssertEqual(json["top"] as? Int, 100)
        XCTAssertEqual(json["hours"] as? Int, 17, "noon UTC is 7 am Eastern: 17 hours to the next 12 midnight Eastern")
        XCTAssertEqual((json["entries"] as? [[String: Any]])?.first?["name"] as? String, "Ann")
    }

    func testXPIsPointsNotPar() {
        let stats = GolfRoundStats(line: "toPar=0;strokes=3;par=3;holes=3;aces=1;eagles=0;birdies=0;pars=0;course=holeinone;holeInOne=2154")
        XCTAssertEqual(stats.holeInOne, 2154)
        let lines = Progression.golfBreakdown(stats, dailyFirst: false, streak: 0)
        XCTAssertEqual(lines.map(\.title), ["Daily Hole in One", "Hole in one!"])
        XCTAssertFalse(lines.contains { $0.title == "Level par" })
    }

    func testSignedOutSaysSo() async {
        let (daily, fake) = make()
        fake.fail = HoleInOneLeaderboardError.signedOut
        await daily.load()
        XCTAssertEqual(daily.boardState, .signedOut)
        XCTAssertTrue(daily.boardNote.contains("Game Center"))
        XCTAssertNil(daily.standing)
    }
}
