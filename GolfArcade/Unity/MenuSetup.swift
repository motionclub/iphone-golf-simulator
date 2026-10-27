import Foundation

/// The TV menu's match setup (Adnan 10-26: map selection and match options on the TV, not the phone). Unity's MenuHud draws the
/// screen from the description here (`state`), sends each change back (`set`) and START (`start`); the phone keeps the options where
/// they always lived (TennisMenu, SportsSession) and launches the match the way its own screens did, so nothing else changes.
@MainActor
enum MenuSetup {
    /// Bays that set up on the TV.
    static let modes: Set<String> = ["bay-tennis-exhibition", "bay-tennis-training", "bay-golf-round", "bay-golf-pass"]
    /// Local golf's player count, picked on the TV's players screen before its course setup.
    static var passPlayers = 2
    static let lengths = ["3 games", "1 set", "Best of 3"]
    /// The court badges' colours (TennisVenueChoice.tint: Club.sky / violet / coral).
    static let tagHex: [TennisVenueChoice: String] = [.resort: "3FA9F5", .skyscraper: "8A4FFF", .volcano: "FF6B4A"]

    struct Map: Encodable { let id, title, detail, tag, tagHex: String }
    struct Row: Encodable { let key, label: String; let choices: [String]; let value: Int }
    struct State: Encodable { let mode, sport, title, line2, start, map: String; let maps: [Map]; let rows: [Row] }

    static func state(_ mode: String) -> State? {
        let menu = TennisMenu.shared, session = SportsSession.shared
        let tennisMaps = TennisVenueChoice.allCases.map { Map(id: $0.rawValue, title: $0.title, detail: $0.tagline + ".", tag: $0.badge, tagHex: tagHex[$0] ?? "3FA9F5") }
        let golfMaps = GolfCourseChoice.allCases.map { Map(id: $0.rawValue, title: $0.title, detail: $0.detail + " · " + $0.card.lowercased(), tag: $0.theme, tagHex: "3FA9F5") }
        let levels = TennisMenu.trainingLevels.map(\.name)
        let ownHoles = GolfCourseChoice(rawValue: session.golfCourse)?.pars.count ?? 5   // "This course" said as its own count: it fits the row
        let holes = SportsSession.golfRoundLengths.map { "\($0 == 0 ? ownHoles : $0) holes" }
        let holeIndex = SportsSession.golfRoundLengths.firstIndex(of: session.golfHoles) ?? 0
        switch mode {
        case "bay-tennis-exhibition":
            return State(mode: mode, sport: "tennis", title: "Exhibition", line2: "Pick a court", start: "START MATCH", map: session.tennisVenue, maps: tennisMaps, rows: [
                Row(key: "opponent", label: "CPU opponent", choices: TennisCampaign.draw.map { "\($0.name) · \($0.nickname)" }, value: menu.quickOpponent),
                Row(key: "difficulty", label: "Difficulty", choices: levels, value: menu.quickDifficulty),
                Row(key: "length", label: "Match length", choices: lengths, value: menu.quickLength)])
        case "bay-tennis-training":
            return State(mode: mode, sport: "tennis", title: "Training", line2: "Pick a court", start: "START TRAINING", map: session.tennisVenue, maps: tennisMaps, rows: [
                Row(key: "level", label: "Coach level", choices: levels, value: menu.trainingLevel)])
        case "bay-golf-round", "bay-golf-pass":
            let pass = mode == "bay-golf-pass"
            return State(mode: mode, sport: "golf", title: pass ? "Local play · \(passPlayers) players" : "Golf", line2: "Pick a course", start: "TEE OFF",
                         map: session.golfCourse, maps: golfMaps, rows: [
                Row(key: "holes", label: "Holes", choices: holes, value: holeIndex),
                Row(key: "twists", label: "Twists", choices: ["Off", "On"], value: session.golfTwists ? 1 : 0)])
        default: return nil
        }
    }

    /// The JSON Unity reads (JsonUtility: plain fields, arrays of objects).
    static func json(_ mode: String) -> String? {
        guard let s = state(mode), let data = try? JSONEncoder().encode(s) else { return nil }
        return String(data: data, encoding: .utf8)
    }

    /// One change from the TV ("key|value": map|resort, difficulty|2, players|3 ...).
    static func set(_ mode: String, _ message: String) {
        let f = message.split(separator: "|", maxSplits: 1, omittingEmptySubsequences: false).map(String.init)
        guard f.count == 2 else { return }
        let menu = TennisMenu.shared, session = SportsSession.shared
        let index = Int(f[1]) ?? 0
        switch f[0] {
        case "map":
            if mode.contains("golf") { if GolfCourseChoice(rawValue: f[1]) != nil { session.golfCourse = f[1] } }
            else if TennisVenueChoice(rawValue: f[1]) != nil { session.tennisVenue = f[1] }
        case "opponent": menu.quickOpponent = min(max(0, index), TennisCampaign.draw.count - 1)
        case "difficulty": menu.quickDifficulty = min(max(0, index), TennisMenu.trainingLevels.count - 1)
        case "length": menu.quickLength = min(max(0, index), lengths.count - 1)
        case "level":
            menu.trainingLevel = min(max(0, index), TennisMenu.trainingLevels.count - 1)
            session.tennisDifficulty = TennisMenu.trainingLevels[menu.trainingLevel].difficulty
        case "holes": session.golfHoles = SportsSession.golfRoundLengths[min(max(0, index), SportsSession.golfRoundLengths.count - 1)]
        case "twists": session.golfTwists = index == 1
        case "players": passPlayers = min(max(2, index), 4)
        default: break
        }
    }

    /// START on the TV: the match the mode's own phone screen would have started, with the court / course already picked.
    static func start(_ mode: String) {
        let menu = TennisMenu.shared
        HubSession.shared.startFromMenu(mode) {
            switch mode {
            case "bay-tennis-exhibition":
                var match = MenuLaunch(mode: .exhibition, round: menu.quickOpponent)
                match.difficulty = TennisMenu.trainingLevels[menu.quickDifficulty].difficulty
                match.sets = menu.quickLength == 2 ? 2 : 1; match.games = menu.quickLength == 0 ? 3 : 6
                menu.openFromPlaza(.exhibition); menu.begin(match, skipMap: true)
            case "bay-tennis-training":
                menu.openFromPlaza(.training); menu.begin(MenuLaunch(mode: .training), skipMap: true)
            case "bay-golf-round":
                menu.openFromPlaza(.main); menu.begin(MenuLaunch(sport: .golf, mode: .round), skipMap: true)
            case "bay-golf-pass":
                menu.openFromPlaza(.localPlayers); menu.startPassThePhone(passPlayers)
            default: break
            }
        }
    }
}
