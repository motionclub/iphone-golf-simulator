import Foundation

// DAILY SHARE (Adnan 2026-11-21): "people can one click share their hole in one challenge … it has an auto message that says
// can you beat my score … similar to how wordle worked". Mockups: ArtDir/ui/daily-challenge-ui-mockups.
//
// Adnan picked THE FRIEND CHALLENGE design (ArtDir/ui/daily-challenge-ui-mockups/concepts/03-friend-challenge.html): an invite
// card and this message, which names the score but never the holes or where the pin was:
//
//     I got 2,355 in Daily Hole in One. Same three shots. Your turn.
//     https://apps.apple.com/app/id6820719910

enum DailyShareText {
    /// The App Store page (MotionSports, App Store Connect app id 6820719910): it opens for anyone, with or without the game.
    nonisolated static let appLink = "https://apps.apple.com/app/id6820719910"
    /// The first Daily Hole in One, 2026-11-15, is #1.
    nonisolated static let firstDay = 20261115

    /// The challenge's number: #1 on 2026-11-15, one more each day.
    nonisolated static func number(day: Int) -> Int {
        guard let first = date(firstDay), let this = date(day) else { return 1 }
        return max(1, (DailyHoleInOne.eastern.dateComponents([.day], from: first, to: this).day ?? 0) + 1)
    }
    nonisolated static func date(_ day: Int) -> Date? {
        DailyHoleInOne.eastern.date(from: DateComponents(year: day / 10000, month: day / 100 % 100, day: day % 100, hour: 12))
    }
    /// "NOV 21" for the clip's title card.
    nonisolated static func shortDate(day: Int) -> String {
        guard let d = date(day) else { return "" }
        let f = DateFormatter(); f.locale = Locale(identifier: "en_US_POSIX"); f.timeZone = DailyHoleInOne.eastern.timeZone; f.dateFormat = "MMM d"
        return f.string(from: d).uppercased()
    }

    /// One shot's square: ⛳ holed, 🟩 inside 10 ft, 🟨 10–30 ft, 🟧 farther, 🟥 water, lava or out of bounds.
    nonisolated static func square(points: Int, feet: Double) -> String {
        if points >= DailyHoleInOne.maxShot { return "⛳" }
        guard feet >= 0, feet.isFinite else { return "🟥" }
        return feet < 10 ? "🟩" : feet < 30 ? "🟨" : "🟧"
    }
    nonisolated static func squares(_ result: HoleInOneResult) -> String {
        zip(result.shots, result.feet).map { square(points: $0, feet: $1) }.joined()
    }
    /// 2402 → "2,402" (the game's own way of writing points, whatever the phone's region).
    nonisolated static func points(_ value: Int) -> String {
        let f = NumberFormatter(); f.numberStyle = .decimal; f.locale = Locale(identifier: "en_US"); f.maximumFractionDigits = 0
        return f.string(from: NSNumber(value: value)) ?? "\(value)"
    }
    /// What one shot did, for the clip: "HOLE IN ONE!", "7.9 FT", "IN THE WATER".
    nonisolated static func shotWords(points: Int, feet: Double) -> String {
        if points >= DailyHoleInOne.maxShot { return "HOLE IN ONE!" }
        guard feet >= 0, feet.isFinite else { return "NO SCORE" }
        return String(format: "%.1f FT", feet)
    }

    /// The Friend Challenge's message (ArtDir/ui/daily-challenge-ui-mockups/concepts/03-friend-challenge.html), with the link on
    /// its own line so it still works where a destination shows no picture or preview.
    nonisolated static func message(_ result: HoleInOneResult, link: String = appLink) -> String {
        "I got \(points(result.total)) in Daily Hole in One. Same three shots. Your turn.\n\(link)"
    }
    /// The message without the link (the sheet's preview).
    nonisolated static func messageBody(_ result: HoleInOneResult) -> String {
        "I got \(points(result.total)) in Daily Hole in One. Same three shots. Your turn."
    }
    /// When the day's challenge closes: it changes at 12 midnight Eastern (DailyHoleInOne.day).
    nonisolated static let closes = "Closes at midnight ET"

    /// A day (yyyymmdd) in `format`, US English ("MMM d, yyyy" → "Nov 15, 2026").
    nonisolated static func formatted(day: Int, _ format: String) -> String {
        guard let d = date(day) else { return "" }
        let f = DateFormatter(); f.locale = Locale(identifier: "en_US_POSIX"); f.timeZone = DailyHoleInOne.eastern.timeZone; f.dateFormat = format
        return f.string(from: d)
    }

    /// The Wordle-style line (one square per shot), for the clip's end card.
    nonisolated static func wordle(_ result: HoleInOneResult) -> String {
        "Daily Hole in One #\(number(day: result.day)) ⛳ \(points(result.total)) / \(points(DailyHoleInOne.maxTotal)) \(squares(result))"
    }
}
