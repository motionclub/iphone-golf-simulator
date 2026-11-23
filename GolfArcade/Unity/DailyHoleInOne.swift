import Foundation
import GameKit
import Observation

// DAILY HOLE IN ONE (Adnan 2026-11-15): a daily challenge under PLAY → Daily Challenges. Three shots a day, each longer than the
// last (11-22): a chip from just off the green, a ~100-yard pitch, then a 150–175-yard iron, to a wider cup with the pin moved on the green. Every player in the world gets the same three
// shots that day (the Eastern date is the seed: Unity's DailyHoleInOne builds them from it). A holed shot scores 1000; any other shot at
// most 800, less the farther it stops from the cup (Unity scores it). The day's total, out of 3000, goes to a Game Center
// leaderboard that starts over every day; its rank and player count say how you did against the world.

/// One finished day: the three shots' scores and how far each one stopped from the cup (feet; 0 holed, -1 in the water or out).
struct HoleInOneResult: Codable, Equatable, Sendable {
    var day: Int
    var total: Int
    var shots: [Int]
    var feet: [Double]
    /// "total=2140;s1=800;s2=640;s3=700;f1=0.0;f2=9.4;f3=6.1;day=20261115" (Unity's "holeInOne" event).
    init?(line: String) {
        var v: [String: String] = [:]
        for part in line.split(separator: ";") {
            let kv = part.split(separator: "=", maxSplits: 1).map(String.init)
            if kv.count == 2 { v[kv[0]] = kv[1] }
        }
        guard let day = v["day"].flatMap(Int.init), let total = v["total"].flatMap(Int.init) else { return nil }
        self.day = day; self.total = max(0, min(DailyHoleInOne.maxTotal, total))
        shots = (1...DailyHoleInOne.shotCount).map { v["s\($0)"].flatMap(Int.init) ?? 0 }
        feet = (1...DailyHoleInOne.shotCount).map { v["f\($0)"].flatMap(Double.init) ?? -1 }
    }
    init(day: Int, total: Int, shots: [Int], feet: [Double]) { self.day = day; self.total = total; self.shots = shots; self.feet = feet }
}

/// One row of the world leaderboard.
struct HoleInOneEntry: Codable, Equatable, Sendable {
    var rank: Int
    var name: String
    var score: Int
    var me: Bool
}

/// Where you stand today: your rank among everyone who played (Game Center's own count).
struct HoleInOneStanding: Equatable, Sendable {
    var rank: Int
    var players: Int
    /// The share of players you beat or tied, 0–100 ("better than 87 % of the world").
    var percentile: Int { DailyHoleInOne.percentile(rank: rank, players: players) }
    /// Top X % (rank / players, rounded up, at least 1).
    var top: Int { DailyHoleInOne.top(rank: rank, players: players) }
}

@MainActor @Observable
final class DailyHoleInOne {
    static let shared = DailyHoleInOne()
    /// The App Store Connect leaderboard: recurring, every day from 12 midnight Eastern, integer score, high to low (work/daily-hole-in-one/README.md).
    nonisolated static let leaderboardID = "motionsports.daily.holeinone"
    nonisolated static let shotCount = 3, maxShot = 1000, maxMissShot = 800
    nonisolated static var maxTotal: Int { shotCount * maxShot }
    nonisolated static let boardSize = 50
    private static let key = "golf.holeinone.v1"

    enum BoardState: String, Sendable { case idle, loading, live, signedOut, unavailable }

    /// Every finished day (yyyymmdd → result). The first finished attempt of a day is the one that counts.
    private(set) var results: [Int: HoleInOneResult]
    private(set) var board: [HoleInOneEntry] = []
    private(set) var standing: HoleInOneStanding?
    private(set) var boardState: BoardState = .idle
    /// The day the board above is for.
    private(set) var boardDay = 0
    /// Called whenever the board or today's result changes: to the TV's daily screens and to the round's last card.
    @ObservationIgnored var changed: @MainActor () -> Void = { HubSession.shared.sendDaily(); SportsSession.shared.sendHoleInOneBoard() }
    /// A challenge was just finished: the TV opens the world board when the plaza comes back.
    var boardPending = false
    /// Seams for tests.
    @ObservationIgnored var now: @MainActor () -> Date = { Date() }
    @ObservationIgnored var store: UserDefaults = .standard
    @ObservationIgnored var leaderboard: HoleInOneLeaderboard = GameCenterHoleInOneLeaderboard()

    init(defaults: UserDefaults = .standard) {
        store = defaults
        if let data = defaults.data(forKey: Self.key), let saved = try? JSONDecoder().decode([Int: HoleInOneResult].self, from: data) { results = saved } else { results = [:] }
    }
    private func save() { if let data = try? JSONEncoder().encode(results) { store.set(data, forKey: Self.key) } }

    // MARK: the day

    /// Today's challenge, yyyymmdd in US Eastern time: one day for the whole world, changing at 12 midnight Eastern (11-19; it was 00:00 UTC).
    /// The Game Center recurring leaderboard must start over at the same moment (App Store Connect: 12:00 AM Eastern).
    var today: Int { Self.day(of: now()) }
    nonisolated static func day(of date: Date) -> Int {
        let c = eastern.dateComponents([.year, .month, .day], from: date)
        return (c.year ?? 2026) * 10000 + (c.month ?? 1) * 100 + (c.day ?? 1)
    }
    var todayResult: HoleInOneResult? { results[today] }
    var playedToday: Bool { todayResult != nil }
    /// Time left until the next challenge (the next 12 midnight Eastern).
    var untilNext: TimeInterval {
        let start = Self.eastern.startOfDay(for: now())
        return (Self.eastern.date(byAdding: .day, value: 1, to: start) ?? start).timeIntervalSince(now())
    }
    nonisolated static var eastern: Calendar {
        var c = Calendar(identifier: .gregorian); c.timeZone = TimeZone(identifier: "America/New_York")!; return c
    }

    // MARK: scoring (the same curve as Unity's DailyHoleInOne.Score, for the phone's words and the tests)

    /// A shot's points: holed 1000; otherwise 800 at the lip and less for every foot farther (k = 1 − ft/150: 800·(0.6k² + 0.4k),
    /// about 8 points a foot near the cup and never under 2 a foot out to 150 ft, so 5 ft always beats 7 ft and no two whole-foot
    /// distances tie); nothing from 150 ft or in a hazard.
    nonisolated static func score(feet: Double, holed: Bool) -> Int {
        if holed { return maxShot }
        guard feet >= 0, feet.isFinite else { return 0 }
        let k = max(0, 1 - feet / 150)
        return Int((Double(maxMissShot) * (0.6 * k * k + 0.4 * k)).rounded())
    }
    nonisolated static func percentile(rank: Int, players: Int) -> Int {
        guard players > 1, rank >= 1 else { return 100 }
        return Int((Double(players - min(rank, players)) / Double(players - 1) * 100).rounded())
    }
    nonisolated static func top(rank: Int, players: Int) -> Int {
        guard players > 0, rank >= 1 else { return 1 }
        return max(1, min(100, Int((Double(min(rank, players)) / Double(players) * 100).rounded(.up))))
    }

    // MARK: a finished challenge

    /// Unity's "holeInOne" event. The first result of a day is kept (a replay the same day is practice); it goes to Game Center
    /// and the board reloads. Returns whether this result counted.
    @discardableResult
    func finished(_ result: HoleInOneResult) -> Bool {
        let counts = results[result.day] == nil && result.day == today
        if counts { results[result.day] = result; save() }
        boardPending = true
        changed()
        Task { await submitAndLoad(counts ? result : nil) }
        return counts
    }

    func submitAndLoad(_ result: HoleInOneResult?) async {
        if let result {
            do { try await leaderboard.submit(result.total, day: result.day) }
            catch { NSLog("[DailyHoleInOne] submit failed: %@", String(describing: error)) }
        }
        await load()
    }

    /// The world board for today: the top rows and your rank among everyone who played.
    func load() async {
        let day = today
        boardState = .loading; boardDay = day; changed()
        do {
            let page = try await leaderboard.load(size: Self.boardSize)
            guard day == today else { return }
            board = page.entries; standing = page.local.map { HoleInOneStanding(rank: $0.rank, players: max(page.players, $0.rank)) }
            boardState = .live
        } catch HoleInOneLeaderboardError.signedOut {
            board = []; standing = nil; boardState = .signedOut
        } catch {
            NSLog("[DailyHoleInOne] board unavailable: %@", String(describing: error))
            board = []; standing = nil; boardState = .unavailable
        }
        changed()
    }

    // MARK: what the TV draws

    /// The JSON the TV's Daily Challenges screen and the round's last card draw (MenuHud.Daily.cs, DailyHoleInOne.cs: `Board`).
    func boardJSON() -> String {
        struct Payload: Encodable {
            var day: Int; var played: Bool; var total: Int; var shots: [Int]; var feet: [Double]
            var state: String; var note: String; var rank: Int; var players: Int; var percentile: Int; var top: Int
            var hours: Int; var minutes: Int; var entries: [HoleInOneEntry]
        }
        let r = todayResult
        let left = Int(untilNext)
        let p = Payload(day: today, played: r != nil, total: r?.total ?? 0, shots: r?.shots ?? [], feet: r?.feet ?? [],
                        state: boardState.rawValue, note: boardNote, rank: standing?.rank ?? 0, players: standing?.players ?? 0,
                        percentile: standing?.percentile ?? 0, top: standing?.top ?? 0,
                        hours: left / 3600, minutes: (left % 3600) / 60, entries: board)
        guard let data = try? JSONEncoder().encode(p), let text = String(data: data, encoding: .utf8) else { return "{}" }
        return text
    }

    /// The line under the board when it has nothing to show.
    var boardNote: String {
        switch boardState {
        case .idle, .loading: "Loading the world leaderboard…"
        case .signedOut: "Sign in to Game Center to see how the world did."
        case .unavailable: "The world leaderboard isn't reachable right now."
        case .live: board.isEmpty ? "No scores yet today. Be the first!" : ""
        }
    }
}

/// The TV's daily screens (MenuHud.Daily.cs).
enum MenuDaily { static let screen = "daily", board = "dailyboard" }

// MARK: - Game Center

enum HoleInOneLeaderboardError: Error { case signedOut, missing }

struct HoleInOnePage: Sendable {
    var entries: [HoleInOneEntry]
    var local: HoleInOneEntry?
    var players: Int
}

/// The world board, behind a protocol so the logic runs in tests.
protocol HoleInOneLeaderboard: Sendable {
    func submit(_ score: Int, day: Int) async throws
    func load(size: Int) async throws -> HoleInOnePage
}

/// Game Center's recurring leaderboard (today's occurrence: Game Center starts it over at 12 midnight Eastern, set in App Store Connect).
struct GameCenterHoleInOneLeaderboard: HoleInOneLeaderboard {
    func submit(_ score: Int, day: Int) async throws {
        guard GKLocalPlayer.local.isAuthenticated else { throw HoleInOneLeaderboardError.signedOut }
        try await withCheckedThrowingContinuation { (c: CheckedContinuation<Void, Error>) in
            GKLeaderboard.submitScore(score, context: day, player: GKLocalPlayer.local, leaderboardIDs: [DailyHoleInOne.leaderboardID]) { error in
                if let error { c.resume(throwing: error) } else { c.resume() }
            }
        }
    }

    func load(size: Int) async throws -> HoleInOnePage {
        guard GKLocalPlayer.local.isAuthenticated else { throw HoleInOneLeaderboardError.signedOut }
        let me = GKLocalPlayer.local.gamePlayerID
        return try await withCheckedThrowingContinuation { (c: CheckedContinuation<HoleInOnePage, Error>) in
            GKLeaderboard.loadLeaderboards(IDs: [DailyHoleInOne.leaderboardID]) { boards, error in
                guard let board = boards?.first else { c.resume(throwing: error ?? HoleInOneLeaderboardError.missing); return }
                board.loadEntries(for: .global, timeScope: .allTime, range: NSRange(location: 1, length: max(1, size))) { local, entries, total, error in
                    if let error { c.resume(throwing: error); return }
                    func row(_ e: GKLeaderboard.Entry) -> HoleInOneEntry {
                        HoleInOneEntry(rank: e.rank, name: e.player.displayName, score: e.score, me: e.player.gamePlayerID == me)
                    }
                    c.resume(returning: HoleInOnePage(entries: (entries ?? []).map(row), local: local.map(row), players: total))
                }
            }
        }
    }
}
