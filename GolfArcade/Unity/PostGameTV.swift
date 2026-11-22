import SwiftUI

// MARK: - The post-game on the TV, every sport (ArtDir/ui/tv-results-calibration, 2026-11-20)
//
// Winner on the map's sign (Venue Plaque) → the standings (tennis and bowling: Box Score; golf: Scorebook, with the hole-by-hole
// Scorecard one tap away) → XP → Play again. Drawn by the app in its window over the game (SportsDisplays.showTennisSetupOnTV),
// stepped from the phone (MatchFinishControls). Unity hides its own end cards while this window is up (command postGameTV);
// handheld play with no TV keeps them.

/// A finished golf round's or bowling game's sheet, every player's, as Unity sends it at the end ("golfCard": GolfGame
/// NativeRoundCard; "bowlingCard": BowlingGame.Card).
struct PostGameBoard: Equatable {
    enum Sport: Equatable { case golf, bowling }
    struct Player: Equatable {
        var name: String
        /// This phone's player.
        var me = false
        /// Where they sat (their colour).
        var seat = 0
        /// Golf: strokes per hole (nil: not played).
        var strokes: [Int?] = []
        /// Bowling: each frame's marks ("X", "9 /", "X X 8") and running totals, the final score and the strikes.
        var marks: [String] = [], totals: [Int?] = []
        var pins = 0, strikes = 0
        /// 1 for the winner; a tie shares the place.
        var place = 1
    }
    let sport: Sport
    /// Golf: the holes' numbers as played ("1"…, or "10"… on a back nine) and their pars.
    var holes: [String] = [], pars: [Int] = []
    /// Best first.
    var players: [Player] = []

    init(sport: Sport, holes: [String] = [], pars: [Int] = [], players: [Player]) {
        self.sport = sport; self.holes = holes; self.pars = pars; self.players = players
        rank()
    }

    /// "holes=1,2,3;pars=4,4,5;p=1|Adnan|3,4,5;p=0|Milo|4,4,"
    init(golf line: String) {
        sport = .golf
        for (key, value) in Self.pairs(line) {
            switch key {
            case "holes": holes = value.split(separator: ",", omittingEmptySubsequences: false).map(String.init)
            case "pars": pars = value.split(separator: ",", omittingEmptySubsequences: false).map { Int($0) ?? 0 }
            case "p":
                let f = value.split(separator: "|", omittingEmptySubsequences: false).map(String.init)
                guard f.count >= 3 else { continue }
                players.append(Player(name: f[1], me: f[0] == "1", seat: players.count,
                                      strokes: f[2].split(separator: ",", omittingEmptySubsequences: false).map { Int($0) }))
            default: break
            }
        }
        rank()
    }

    /// "p=1|Adnan|X,9 /,8 1,…|20,38,47,…|123|4;p=0|…"
    init(bowling line: String) {
        sport = .bowling
        for (key, value) in Self.pairs(line) where key == "p" {
            let f = value.split(separator: "|", omittingEmptySubsequences: false).map(String.init)
            guard f.count >= 6 else { continue }
            players.append(Player(name: f[1], me: f[0] == "1", seat: players.count,
                                  marks: f[2].split(separator: ",", omittingEmptySubsequences: false).map(String.init),
                                  totals: f[3].split(separator: ",", omittingEmptySubsequences: false).map { Int($0) },
                                  pins: Int(f[4]) ?? 0, strikes: Int(f[5]) ?? 0))
        }
        rank()
    }

    private static func pairs(_ line: String) -> [(String, String)] {
        line.split(separator: ";").compactMap { pair in
            let kv = pair.split(separator: "=", maxSplits: 1, omittingEmptySubsequences: false).map(String.init)
            return kv.count == 2 ? (kv[0], kv[1]) : nil
        }
    }

    /// Best first; equal scores share a place (no tiebreak).
    private mutating func rank() {
        let board = self
        func better(_ a: Player, _ b: Player) -> Bool { board.sport == .golf ? board.toPar(a) < board.toPar(b) : a.pins > b.pins }
        let all = players
        for i in players.indices { players[i].place = 1 + all.filter { better($0, all[i]) }.count }
        players = players.enumerated().sorted { ($0.element.place, $0.offset) < ($1.element.place, $1.offset) }.map(\.element)
    }

    func strokes(_ p: Player) -> Int { p.strokes.compactMap { $0 }.reduce(0, +) }
    /// Against the par of the holes played.
    func toPar(_ p: Player) -> Int {
        zip(p.strokes, pars).reduce(0) { sum, hole in hole.0.map { sum + $0 - hole.1 } ?? sum }
    }
    var parTotal: Int { pars.reduce(0, +) }
    var winners: [Player] { players.filter { $0.place == 1 } }
    var me: Player? { players.first(where: \.me) }
    var solo: Bool { players.count == 1 }
    /// A win: first of several, or a solo round at or under par / a solo game of 150 or more (BowlingGameStats.won).
    var mineWon: Bool {
        guard let me else { return false }
        if !solo { return me.place == 1 }
        return sport == .golf ? toPar(me) <= 0 : me.pins >= 150
    }
    /// The big number: to par for golf, pins for bowling.
    func scoreText(_ p: Player) -> String { sport == .golf ? GolfRoundStats.text(toPar: toPar(p)) : "\(p.pins)" }
    /// What goes with it: "16 strokes", "5 strikes".
    func detailText(_ p: Player) -> String {
        sport == .golf ? "\(strokes(p)) stroke\(strokes(p) == 1 ? "" : "s")" : "\(p.strikes) strike\(p.strikes == 1 ? "" : "s")"
    }

    static func ordinal(_ n: Int) -> String {
        let tens = n % 100
        let suffix = (11...13).contains(tens) ? "th" : n % 10 == 1 ? "st" : n % 10 == 2 ? "nd" : n % 10 == 3 ? "rd" : "th"
        return "\(n)\(suffix)"
    }
    /// The design's player marks (review.js: orange, teal, lavender, copper…), by seat.
    static let seatColors = ["E9A445", "2E9C8C", "8C8FD8", "B9733F", "D96B8F", "6FB34A"].map { Color(hex: $0) }
}

struct PostGameTV: View {
    let session: SportsSession
    var service: MultiplayerService = .shared
    let stage: SportsSession.PostGameStage
    let cq: CGFloat
    let palette: TVCalibrationPalette

    private var skin: MapSkin { palette.skin }
    private var board: PostGameBoard? { session.sport == "tennis" ? nil : session.postGameBoard }
    private var me: String { MapSkin.playerName(session) }

    // tennis: the phone's player against one rival
    private var won: Bool { session.finishedMatch?.won ?? false }
    private var rival: String {
        if session.multiplayerMatchID != nil, let other = service.lobby?.competitors.first(where: { $0.id != service.localID }) { return other.name }
        return session.opponentName.isEmpty ? "Rival" : session.opponentName
    }
    private var stats: MatchStats? { session.lastMatchStats }
    /// "6–3": games, or sets when the match had more than one.
    private var tennisScore: String {
        guard let s = stats else { return session.finishedMatch?.score ?? "" }
        let sets = s.setsWon + s.setsLost > 1
        let mine = sets ? s.setsWon : s.gamesWon, theirs = sets ? s.setsLost : s.gamesLost
        return won ? "\(mine)–\(theirs)" : "\(theirs)–\(mine)"
    }

    /// Who won, for the sheets' headers.
    private var winnerName: String {
        if let board { return board.winners.map(\.name).joined(separator: " & ") }
        return won ? me : rival
    }
    private var winnerNote: String {
        guard let board else { return "\(winnerName) wins" }
        if board.solo { return "" }
        return board.winners.count > 1 ? "Tied" : "\(winnerName) wins"
    }

    var body: some View {
        ZStack {
            LinearGradient(colors: [skin.bottom.opacity(0.1), skin.bottom.opacity(0.34)], startPoint: .leading, endPoint: .trailing)
            switch stage {
            case .victory: victory
            case .results: results
            case .scorecard: scorecard
            case .xp: xp
            case .again: again
            }
        }
    }

    // MARK: Winner (Venue Plaque)

    /// The winner set into the map's sign: name and WINS on one line, the score under it.
    private var victory: some View {
        let width = 50 * cq
        return ZStack {
            MapTitleArt(skin: skin, height: titleHeight(width: 17, height: 9)).frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading).padding(.top, 4.7 * cq).padding(.leading, 4 * cq)
            Group {
                if let plate = skin.plateImage {
                    let height = width * plate.size.height / max(1, plate.size.width), box = skin.plateBox
                    Image(uiImage: plate).resizable().interpolation(.high).frame(width: width, height: height)
                        .overlay(alignment: .topLeading) {
                            // (the board is short: the two lines may stand a little over its edges, as on the design's plaque)
                            plaqueText.fixedSize(horizontal: false, vertical: true).frame(width: box.width * width * 1.1, height: box.height * height)
                                .offset(x: (box.minX - box.width * 0.05) * width, y: box.minY * height)
                        }
                } else {
                    plaqueText.padding(1.5 * cq).background(skin.bottom, in: RoundedRectangle(cornerRadius: 1.2 * cq))
                }
            }
            .shadow(color: .black.opacity(0.35), radius: 1 * cq, y: 0.6 * cq)
            .position(x: 64 * cq, y: 31 * cq)
            continueAction("Results")
        }
    }
    /// (name, tag in the accent, big score, what goes with it)
    private var plaque: (name: String, tag: String, score: String, detail: String) {
        guard let board else { return (winnerName, "WINS", tennisScore, "vs. \(won ? rival : me)") }
        // a round on your own leads with the score (the design's README): "Adnan −3 / 16 strokes"
        if board.solo, let p = board.players.first {
            return board.sport == .golf ? (p.name, board.scoreText(p), "\(board.strokes(p))", "strokes") : (p.name, "\(p.pins)", "\(p.strikes)", p.strikes == 1 ? "strike" : "strikes")
        }
        guard let top = board.winners.first else { return ("", "", "", "") }
        return (winnerName, board.winners.count > 1 ? "TIE" : "WINS", board.scoreText(top), board.detailText(top))
    }
    private var plaqueText: some View {
        // line two: "6–3 vs. Milo", "−3 16 strokes", "158 5 strikes"
        let p = plaque
        return VStack(spacing: 0.1 * cq) {
            // the sign's own type colour (navy on Cliffside's stone, cream on the resort's wood), the accent that reads on it
            HStack(spacing: 0.7 * cq) {
                Text(p.name).foregroundStyle(skin.plateText)
                Text(p.tag).foregroundStyle(skin.plateText.isLight ? palette.accent : palette.accentDeep)
            }.font(MotionBrand.font(.extraBoldItalic, 3.6 * cq))
            HStack(alignment: .firstTextBaseline, spacing: 0.5 * cq) {
                Text(p.score).font(MotionBrand.font(.extraBold, 2.8 * cq))
                Text(p.detail).font(MotionBrand.font(.medium, 1.8 * cq))
            }.foregroundStyle(skin.plateText)
        }
        .lineLimit(1).minimumScaleFactor(0.4)
    }

    // MARK: Standings

    @ViewBuilder private var results: some View {
        if let board, board.sport == .golf { golfResults(board) }
        else if let board { bowlingResults(board) }
        else { tennisResults }
    }

    /// Tennis Box Score: both players, the winner on top.
    private var tennisResults: some View {
        let s = stats
        let mine = [me, s.map { "\($0.gamesWon)" } ?? "–", s.map { "\($0.pointsWon)" } ?? "–", s.map { "\($0.aces)" } ?? "–"]
        let theirs = [rival, s.map { "\($0.gamesLost)" } ?? "–", s.map { "\($0.pointsLost)" } ?? "–", "–"]
        let first = won ? mine : theirs, second = won ? theirs : mine
        let widths: [CGFloat] = [9, 26, 10, 14, 10, 11]
        return sheetScreen(title: "Match complete", width: 82) {
            VStack(spacing: 0) {
                tableRow(["Place", "Player", "Games", "Points won", "Aces", "Result"], widths: widths, header: true)
                tableRow(["1st"] + first + ["Win"], widths: widths, top: true, bigColumn: 2)
                rule
                tableRow(["2nd"] + second + ["Loss"], widths: widths, bigColumn: 2)
            }
        } actions: { TVAction(title: "Continue", cq: cq, palette: palette) }
    }

    /// Golf Scorebook: place, player, to par, strokes.
    private func golfResults(_ board: PostGameBoard) -> some View {
        let widths: [CGFloat] = [10, 31, 12, 12]
        return sheetScreen(title: "Round complete", width: 68) {
            VStack(spacing: 0) {
                tableRow(["Place", "Player", "To par", "Strokes"], widths: widths, header: true)
                ForEach(board.players.indices, id: \.self) { i in
                    let p = board.players[i]
                    tableRow([PostGameBoard.ordinal(p.place), p.name, board.scoreText(p), "\(board.strokes(p))"], widths: widths,
                             top: p.place == 1 && !board.solo, bigColumn: 3, seat: p.seat)
                    rule
                }
            }
        } actions: {
            HStack(spacing: 1.2 * cq) { TVAction(title: "Scorecard", cq: cq, palette: palette, quiet: true); TVAction(title: "Continue", cq: cq, palette: palette) }
        }
    }

    /// Golf's hole-by-hole card: par, then everyone, best first.
    private var scorecard: some View {
        let board = self.board ?? PostGameBoard(sport: .golf, players: [])
        let n = max(1, board.holes.count)
        let width: CGFloat = n > 9 ? 92 : 68
        let holeWidth = (width - 2.8 - 15 - 8) / CGFloat(n)
        let widths = [15] + Array(repeating: holeWidth, count: n) + [8]
        return sheetScreen(title: "Scorecard", width: width) {
            VStack(spacing: 0) {
                tableRow(["Hole"] + board.holes + ["Total"], widths: widths, header: true, leading: [0])
                tableRow(["Par"] + board.pars.map(String.init) + ["\(board.parTotal)"], widths: widths, bigColumn: n + 1, leading: [0])
                rule
                ForEach(board.players.indices, id: \.self) { i in
                    let p = board.players[i]
                    tableRow([p.name] + p.strokes.map { $0.map(String.init) ?? "–" } + ["\(board.strokes(p))"], widths: widths,
                             top: p.place == 1 && !board.solo, bigColumn: n + 1, leading: [0])
                    rule
                }
            }
        } actions: {
            HStack(spacing: 1.2 * cq) { TVAction(title: "Back", cq: cq, palette: palette, quiet: true); TVAction(title: "Continue", cq: cq, palette: palette) }
        }
    }

    /// Bowling Box Score: every frame's marks over its running total, then the score.
    private func bowlingResults(_ board: PostGameBoard) -> some View {
        let place: CGFloat = 6.5, name: CGFloat = 12, frame: CGFloat = 5.45, total: CGFloat = 7.5
        return sheetScreen(title: "Game complete", width: 84) {
            VStack(spacing: 0) {
                HStack(spacing: 0) {
                    headerCell("Place", place, .center); headerCell("Player", name, .leading)
                    ForEach(1...10, id: \.self) { f in headerCell("\(f)", frame, .center).overlay(alignment: .leading) { columnRule } }
                    headerCell("Total", total, .center).overlay(alignment: .leading) { columnRule }
                }
                .padding(.horizontal, 1.4 * cq).frame(height: 3.4 * cq)
                ForEach(board.players.indices, id: \.self) { i in
                    let p = board.players[i], top = p.place == 1 && !board.solo
                    HStack(spacing: 0) {
                        Text(PostGameBoard.ordinal(p.place)).font(MotionBrand.font(.extraBold, 1.9 * cq)).frame(width: place * cq)
                        Text(p.name).font(MotionBrand.font(.extraBold, 1.9 * cq)).frame(width: name * cq, alignment: .leading)
                        ForEach(0..<10, id: \.self) { f in
                            VStack(spacing: 0.15 * cq) {
                                Text(f < p.marks.count ? p.marks[f].replacingOccurrences(of: " ", with: "  ") : "").font(MotionBrand.font(.semiBold, 1.2 * cq))
                                Text(f < p.totals.count ? p.totals[f].map(String.init) ?? "" : "").font(MotionBrand.font(.extraBold, 1.75 * cq))
                            }
                            .frame(width: frame * cq).frame(maxHeight: .infinity)
                            .overlay(alignment: .leading) { columnRule }
                        }
                        Text("\(p.pins)").font(MotionBrand.font(.extraBold, 2.5 * cq)).frame(width: total * cq).frame(maxHeight: .infinity)
                            .overlay(alignment: .leading) { columnRule }
                    }
                    .lineLimit(1).minimumScaleFactor(0.6)
                    .foregroundStyle(top ? palette.winnerInk : palette.panelInk)
                    .padding(.horizontal, 0.6 * cq).frame(height: 5.6 * cq)
                    .background(top ? palette.rowWinner : .clear)
                    .padding(.horizontal, 0.8 * cq)
                    rule
                }
            }
        } actions: { TVAction(title: "Continue", cq: cq, palette: palette) }
    }

    // MARK: XP and Play again

    /// XP: the award, where it came from, and the level bar.
    private var xp: some View {
        let summary = TennisMenu.shared.postMatch
        let total = summary?.total ?? 0, level = summary?.endLevel ?? 1, into = summary?.endXP ?? 0, need = LevelCurve.needed(level)
        let lines = summary?.lines ?? []
        return sheetScreen(title: "XP earned", trailing: me, width: 82) {
            VStack(alignment: .leading, spacing: 1.4 * cq) {
                HStack(alignment: .top, spacing: 2 * cq) {
                    VStack(alignment: .leading, spacing: 0.3 * cq) {
                        Text(me).font(MotionBrand.font(.extraBold, 1.4 * cq)).padding(.horizontal, 0.8 * cq).padding(.vertical, 0.3 * cq)
                            .background(palette.accent, in: RoundedRectangle(cornerRadius: 0.4 * cq)).foregroundStyle(palette.accentInk)
                        HStack(alignment: .firstTextBaseline, spacing: 0.6 * cq) {
                            Text("+\(total)").font(MotionBrand.font(.extraBold, 5.4 * cq))
                            Text("XP").font(MotionBrand.font(.extraBold, 2.6 * cq))
                        }
                        if !(summary?.levelsGained.isEmpty ?? true) { Text("Level up").font(MotionBrand.font(.medium, 1.6 * cq)).foregroundStyle(palette.muted) }
                    }
                    .frame(width: 20 * cq, alignment: .leading)
                    Rectangle().fill(palette.rule).frame(width: 1)
                    let pairs = stride(from: 0, to: lines.count, by: 2).map { Array(lines[$0..<min($0 + 2, lines.count)]) }
                    VStack(spacing: 0.6 * cq) {
                        ForEach(pairs.indices, id: \.self) { r in
                            HStack(spacing: 1.2 * cq) {
                                ForEach(pairs[r]) { line in
                                    HStack {
                                        Text(line.title).font(MotionBrand.font(.medium, 1.6 * cq)).lineLimit(1).minimumScaleFactor(0.7)
                                        Spacer(minLength: 0.5 * cq)
                                        Text("+\(line.xp)").font(MotionBrand.font(.extraBold, 1.6 * cq))
                                    }
                                    .padding(.horizontal, 0.8 * cq).padding(.vertical, 0.5 * cq).frame(width: 25 * cq)
                                    .background(palette.row, in: RoundedRectangle(cornerRadius: 0.3 * cq))
                                }
                                Spacer(minLength: 0)
                            }
                        }
                    }
                }
                .fixedSize(horizontal: false, vertical: true)
                VStack(spacing: 0.6 * cq) {
                    HStack {
                        Text("Level \(level)").font(MotionBrand.font(.extraBold, 1.8 * cq))
                        Spacer()
                        Text("\(into) / \(need) XP").font(MotionBrand.font(.medium, 1.5 * cq)).foregroundStyle(palette.muted)
                    }
                    GeometryReader { g in
                        ZStack(alignment: .leading) {
                            Capsule().fill(palette.meterTrack)
                            Capsule().fill(palette.meterFill).frame(width: g.size.width * min(1, Double(into) / Double(max(1, need))))
                        }
                    }.frame(height: 0.7 * cq)
                }
                .padding(1.2 * cq).background(palette.inset, in: RoundedRectangle(cornerRadius: 0.5 * cq))
            }
            .foregroundStyle(palette.panelInk).padding(1.4 * cq)
        } actions: { TVAction(title: "Continue", cq: cq, palette: palette) }
    }

    /// Play again: the choices the phone picks from.
    private var again: some View {
        let choices = session.postGameChoices
        return ZStack {
            MapTitleArt(skin: skin, height: titleHeight(width: 16, height: 8)).frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top).padding(.top, 5 * cq)
            TVSheet(title: "Play again?", trailing: "", cq: cq, palette: palette, width: 55) {
                VStack(spacing: 1 * cq) {
                    ForEach(choices.indices, id: \.self) { i in
                        let on = i == session.postGameChoice
                        HStack {
                            Text(choices[i].title).font(MotionBrand.font(.extraBoldItalic, 1.9 * cq))
                            Spacer()
                            Image(systemName: "chevron.right").font(.system(size: 1.3 * cq, weight: .heavy))
                        }
                        .foregroundStyle(on ? palette.accentInk : palette.panelInk)
                        .padding(.horizontal, 1.3 * cq).frame(height: 4.4 * cq)
                        .background {
                            let shape = RoundedRectangle(cornerRadius: 0.86 * cq, style: .continuous)
                            if on {
                                shape.fill(palette.accentDeep).offset(y: 0.3 * cq)
                                shape.fill(palette.accent)
                            } else {
                                shape.fill(palette.row)
                            }
                            shape.strokeBorder(palette.trim, lineWidth: 0.18 * cq)
                        }
                    }
                    Text("Choose on your phone.").font(MotionBrand.font(.medium, 1.5 * cq)).foregroundStyle(palette.muted).padding(.top, 0.4 * cq)
                }
                .padding(1.4 * cq)
            }.offset(y: 4 * cq)
        }
    }

    // MARK: Pieces

    /// The map's sign at the top, a sheet in the middle, the actions under it at the right.
    private func sheetScreen<Content: View, Actions: View>(title: String, trailing: String? = nil, width: CGFloat,
                                                           @ViewBuilder content: @escaping () -> Content,
                                                           @ViewBuilder actions: () -> Actions) -> some View {
        ZStack {
            MapTitleArt(skin: skin, height: titleHeight(width: 16, height: 8)).frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top).padding(.top, 3 * cq)
            VStack(alignment: .trailing, spacing: 2.2 * cq) {
                TVSheet(title: title, trailing: trailing ?? winnerNote, cq: cq, palette: palette, width: width, content: content)
                actions()
            }
            .frame(width: width * cq).offset(y: 4 * cq)
        }
    }

    /// One row of a standings table: `bigColumn` is the score (ExtraBold, larger); `seat` puts the player's colour mark before
    /// their name (column 1); the `leading` columns sit left, the rest are centred.
    private func tableRow(_ cells: [String], widths: [CGFloat], header: Bool = false, top: Bool = false, bigColumn: Int? = nil,
                          seat: Int? = nil, leading: Set<Int> = [1]) -> some View {
        HStack(spacing: 0) {
            ForEach(cells.indices, id: \.self) { i in
                let left = leading.contains(i)
                HStack(spacing: 0.7 * cq) {
                    if i == 1, let seat, !header {
                        RoundedRectangle(cornerRadius: 0.1 * cq).fill(PostGameBoard.seatColors[seat % PostGameBoard.seatColors.count]).frame(width: 0.4 * cq, height: 1.8 * cq)
                    }
                    Text(cells[i])
                        .font(header ? MotionBrand.font(.semiBold, 1.45 * cq)
                              : i == bigColumn ? MotionBrand.font(.extraBold, 2.4 * cq)
                              : MotionBrand.font(i == 0 ? .extraBold : left ? .semiBold : .medium, 1.95 * cq))
                }
                .frame(width: (i < widths.count ? widths[i] : 8) * cq, alignment: left ? .leading : .center)
                .lineLimit(1).minimumScaleFactor(0.6)
            }
        }
        .foregroundStyle(header ? palette.muted : top ? palette.winnerInk : palette.panelInk)
        .padding(.horizontal, 0.6 * cq).frame(height: header ? 3.4 * cq : 5.1 * cq)
        .background(top ? palette.rowWinner : .clear)
        .overlay(alignment: .leading) { if top { Rectangle().fill(palette.accentDeep).frame(width: 0.4 * cq) } }
        .padding(.horizontal, 0.8 * cq)
    }
    private func headerCell(_ text: String, _ width: CGFloat, _ alignment: Alignment) -> some View {
        Text(text).font(MotionBrand.font(.semiBold, 1.45 * cq)).foregroundStyle(palette.muted).frame(width: width * cq, alignment: alignment)
    }
    private var rule: some View { Rectangle().fill(palette.rule).frame(height: 1).padding(.horizontal, 1.4 * cq) }
    private var columnRule: some View { Rectangle().fill(palette.rule).frame(width: 1) }

    /// The map's sign fitted in a box (hundredths of the TV's width): Cliffside's is long and low, Club Lanes' tall.
    private func titleHeight(width: CGFloat, height: CGFloat) -> CGFloat {
        guard let image = skin.titleImage, image.size.width > 0 else { return height * cq }
        return min(height, width * image.size.height / image.size.width) * cq
    }

    private func continueAction(_ title: String) -> some View {
        TVAction(title: title, cq: cq, palette: palette)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomTrailing)
            .padding(.trailing, 5.2 * cq).padding(.bottom, 4.4 * cq)
    }
}

/// A post-game sheet: a header bar in the map's colour (title left, a note right) over the panel.
struct TVSheet<Content: View>: View {
    let title: String
    let trailing: String
    let cq: CGFloat
    let palette: TVCalibrationPalette
    var width: CGFloat = 80
    @ViewBuilder let content: () -> Content
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text(title).font(MotionBrand.font(.extraBoldItalic, 3 * cq))
                Spacer()
                Text(trailing).font(MotionBrand.font(.extraBold, 1.6 * cq))
            }
            .foregroundStyle(palette.skin.cream).lineLimit(1)
            .padding(.horizontal, 1.8 * cq).frame(height: 5.6 * cq).background(palette.skin.top)
            .overlay(alignment: .bottom) { Rectangle().fill(palette.dark ? palette.accent : palette.accentDeep).frame(height: 0.22 * cq) }
            content().padding(.bottom, 0.8 * cq)
        }
        .frame(width: width * cq)
        .background(LinearGradient(colors: [palette.panelLight, palette.panel], startPoint: .top, endPoint: .bottom))
        .clipShape(RoundedRectangle(cornerRadius: 0.8 * cq, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 0.8 * cq, style: .continuous).strokeBorder(palette.skin.frame, lineWidth: 0.3 * cq))
        .background(RoundedRectangle(cornerRadius: 0.8 * cq, style: .continuous).fill(palette.skin.frameDeep).offset(y: 0.5 * cq)
            .shadow(color: .black.opacity(0.4), radius: 1.1 * cq, y: 1.1 * cq))
    }
}
