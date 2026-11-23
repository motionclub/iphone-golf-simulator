import SwiftUI
import UIKit

/// What Unity's BowlingGame reports 4 times a second (NativeSportsSession.Bowling.cs):
/// phase|player|frame|ball|board|grade|mph|hook°|rpm|standing pins|mine|walking|aim°|canEmote.
struct BowlingControllerState: Equatable {
    var phase = "Setup", player = "", frame = 1, ball = 1, board = 20.0
    var grade = "", mph = 0.0, hook = 0, rpm = 0, standing = ""
    /// This phone bowls now (false: a friend's phone or the computer bowler is up).
    var mine = true
    /// Someone is walking (or the bowler is fetching the ball from the return): a tap on the ball skips it.
    var walking = false
    /// This phone's player is not up and may play one of their emotes (11-22: whenever it's not their turn).
    var canEmote = false
    /// The last ball's aim, degrees (+ = right of straight up the lane): the way the swing went through.
    var aim = 0.0

    init() {}
    init(_ line: String) {
        let p = line.split(separator: "|", omittingEmptySubsequences: false).map(String.init)
        guard p.count >= 10 else { return }
        phase = p[0]; player = p[1]; frame = Int(p[2]) ?? 1; ball = Int(p[3]) ?? 1; board = Double(p[4]) ?? 20
        grade = p[5]; mph = Double(p[6]) ?? 0; hook = Int(p[7]) ?? 0; rpm = Int(p[8]) ?? 0; standing = p[9]
        if p.count > 10 { mine = p[10] != "0" }
        if p.count > 12 { walking = p[11] == "1"; aim = Double(p[12]) ?? 0 }
        if p.count > 13 { canEmote = p[13] == "1" }
    }

    /// The ball can be picked up (setup) or is in the hand (hold, approach).
    var canHold: Bool { mine && !walking && (phase == "Setup" || phase == "Hold" || phase == "Approach") }
    var canMove: Bool { mine && phase == "Setup" }
}

/// The phone while bowling (PLAN_PhonePlay_NoTV_GolfBowling.md §5, bowling V2): move along the approach, then press and HOLD
/// the ball. The bowler walks up at one steady pace (the computer's); swing with them: push away, swing back, swing through, and
/// let go just as your arm passes the bottom. The release is judged against your own arm; the bowler lets the ball go on their
/// own beat. Swing through toward the right and the ball goes right, as much as you turned (10-27 feel pass: the aim is the
/// swing, no AIM row). Turn your wrist into a handshake as you let go to hook it. The phone ticks at the top of your backswing and buzzes
/// as your arm passes the bottom (BowlingHaptics, from the game's bowlCue).
struct BowlingPhoneController: View {
    @Bindable var session: SportsSession
    @State private var holding = false
    /// The board under the finger while it is on the lane slider (shown at once; the game's state comes 4 times a second).
    @State private var slideBoard: Double?
    @State private var skipSent = false
    private var state: BowlingControllerState { BowlingControllerState(session.bowlingState) }
    /// The centre being bowled in: the controller wears its material (UI OVERHAUL 11-15, boards 07-10).
    private var skin: MapSkin { MapSkin.of(sport: "bowling", venue: session.bowlingVenue) }

    var body: some View {
        Group {
            if session.phonePlay { phoneLayout } else { tvLayout }
        }
        .statusBarHidden().persistentSystemOverlays(.hidden)
        .onChange(of: state.phase) { _, phase in
            // the game took the ball (released, fouled, cancelled): the hold is over
            if phase != "Setup" && phase != "Hold" && phase != "Approach" { holding = false }
        }
        .onDisappear { if holding { release() } }
        .sheet(isPresented: $session.menuPauseVisible) { GamePauseMenu(session: session) }
    }

    private var gameOver: Bool { state.phase == "GameOver" }
    /// Someone else is up: this player can react with their emotes (11-22).
    private var waiting: Bool { !state.mine && !gameOver }

    /// The player's three equipped emotes, whenever it's not their turn: their player does it beside the lane.
    private var emotes: some View {
        EquippedEmoteControls(title: "React", ids: session.matchEmotes, enabled: state.canEmote && !session.paused,
            notice: state.player.isEmpty ? "Your player does it beside the lane." : "Your player does it while \(state.player) bowls.",
            identifier: "bowling-emote") { slot in
            session.command("bowlEmote", value: Double(slot))
            UIImpactFeedbackGenerator(style: .light).impactOccurred()
        }
    }

    /// With a TV: the phone is the controller, full screen.
    /// Boards 07-10: the bowler's name on the centre's plate, Frame · Ball, ◀ Board ▶, the centre's ball, Hold to start, LAST THROW and pause.
    private var tvLayout: some View {
        VStack(spacing: 16) {
            header
            moveStrip
            Spacer(minLength: 0)
            if gameOver { finishButton } else { ball }
            Spacer(minLength: 0)
            if waiting { emotes } else { lastThrow }
        }
        .padding(.horizontal, 22).padding(.vertical, 26)
        .background(MapControllerBackground(skin: skin))
    }

    /// No TV: handheld play (HandheldFrame). The lane and Unity's score sheet fill the top three quarters; where to stand, the
    /// ball and the last throw sit on a deck in the bottom quarter, so the bowler, the ball and the pins are never under a thumb.
    private var phoneLayout: some View {
        HandheldFrame {
            VStack { Spacer(minLength: 0); if gameOver { finishButton.padding(.bottom, 24) } }.frame(maxWidth: .infinity)
        } deck: {
            handheldDeck
        } deckBackground: {
            ZStack(alignment: .top) {
                LinearGradient(colors: [skin.top, skin.bottom], startPoint: .top, endPoint: .bottom)
                Rectangle().fill(skin.frame).frame(height: 4)
            }
        }
    }

    /// The deck on a 464 × 220 design canvas: where to stand on the left, the ball in the middle, the last throw on the right.
    private var handheldDeck: some View {
        ZStack(alignment: .topLeading) {
            Color.clear
            if !gameOver {
                ballView(caption: false).scaleEffect(0.4).frame(width: 104, height: 104).position(x: 232, y: 86)
                Text(ballCaption).font(MSBrand.font(.button, 15)).foregroundStyle(ballCaptionLive ? MSBrand.gold : MSBrand.n300)
                    .lineLimit(1).minimumScaleFactor(0.6).frame(width: 190).position(x: 232, y: 190)
            }
            if waiting {
                emotes.frame(width: 300).scaleEffect(0.6).frame(width: 180, height: 120).position(x: 96, y: 92)
            } else {
                Text("WHERE TO STAND").font(MSBrand.font(.heading, 15)).foregroundStyle(MSBrand.n300).position(x: 96, y: 18)
                moveStrip.frame(width: 300, height: 68).scaleEffect(0.6).frame(width: 180, height: 41).position(x: 96, y: 92)
            }
            Text("LAST THROW").font(MSBrand.font(.heading, 15)).foregroundStyle(MSBrand.n300).position(x: 372, y: 18)
            VStack(spacing: 2) {
                Text(state.mph > 0 ? String(format: "%.1f", state.mph) : "–").font(MSBrand.font(.hudNumber, 38)).foregroundStyle(MSBrand.white).monospacedDigit()
                Text("MPH").font(MSBrand.font(.hudLabel, 13)).foregroundStyle(MSBrand.n300)
                if !state.grade.isEmpty && state.mph > 0 {
                    Text(gradeText).font(MSBrand.font(.heading, 16)).foregroundStyle(state.grade == "Perfect" ? MSBrand.gold : MSBrand.white)
                        .multilineTextAlignment(.center).lineLimit(2).minimumScaleFactor(0.7)
                }
            }.frame(width: 150).position(x: 380, y: 98)
            Button { session.pause() } label: {
                Image(systemName: "pause.fill").font(.system(size: 17, weight: .black)).foregroundStyle(MSBrand.white)
                    .frame(width: 40, height: 40).background(MSBrand.navyDeep, in: Circle()).overlay(Circle().stroke(MSBrand.white, lineWidth: 2.5))
            }.buttonStyle(.plain).position(x: 440, y: 18).accessibilityLabel("Pause bowling").accessibilityIdentifier("bowling-pause")
        }
    }

    /// The game is over: on to the XP and results.
    private var finishButton: some View {
        Button { TennisMenu.shared.beginPostMatch() } label: {
            MapActionFace(skin: skin, title: "Finish", height: 84).frame(maxWidth: 320)
        }
        .buttonStyle(.plain).accessibilityIdentifier("bowling-finish")
    }

    /// The bowler's username on the centre's plate, and Frame · Ball on a cream pill under it.
    private var header: some View {
        VStack(spacing: 10) {
            MapPlate(skin: skin, text: (state.player.isEmpty ? MapSkin.playerName(session) : state.player).uppercased(), height: 96).mapEntrance(delay: 0.1)
                .accessibilityIdentifier("controller-name-plate")
            Text("Frame \(state.frame) · Ball \(state.ball)").font(MapFont.bold(22)).foregroundStyle(skin.ink)
                .padding(.horizontal, 22).padding(.vertical, 6)
                .background(skin.cream, in: Capsule()).overlay(Capsule().strokeBorder(skin.frame, lineWidth: 2.5))
                .accessibilityIdentifier("bowling-frame")
        }
    }

    /// Where to stand (Adnan 10-27: "make it easier to move side to side, it takes a while"): the lane itself, edge to edge.
    /// Touch or drag anywhere on it and the bowler goes to that board; the chevrons step one board, and keep going (faster) while held.
    private var moveStrip: some View {
        HStack(spacing: 10) {
            StepButton(skin: skin, icon: "chevron.left", label: "Move left") { step(+1) }
            laneSlider
            StepButton(skin: skin, icon: "chevron.right", label: "Move right") { step(-1) }
        }
        .padding(8)
        .background {
            Capsule().fill(skin.frameDeep).offset(y: 4)
            Capsule().fill(LinearGradient(colors: [skin.frame, skin.frameDeep.mix(skin.frame, 0.5)], startPoint: .top, endPoint: .bottom))
        }
        .opacity(state.canMove ? 1 : 0.35).disabled(!state.canMove)
        .onChange(of: state.canMove) { _, can in if !can { slideBoard = nil } }
    }

    private var shownBoard: Double { slideBoard ?? state.board }

    /// The lane seen from behind: board 39 at the left gutter, board 1 at the right (boards count from the right), the seven
    /// target arrows, and a gold ball where the bowler stands.
    private var laneSlider: some View {
        GeometryReader { geo in
            let w = geo.size.width
            ZStack(alignment: .topLeading) {
                Capsule().fill(skin.cream)
                ForEach([5, 10, 15, 20, 25, 30, 35], id: \.self) { b in
                    Image(systemName: "arrowtriangle.up.fill").font(.system(size: 9, weight: .bold)).foregroundStyle(skin.ink.opacity(0.4))
                        .position(x: x(for: Double(b), width: w), y: 12)
                }
                Text(boardText).font(MapFont.bold(24)).foregroundStyle(skin.ink).monospacedDigit().lineLimit(1).minimumScaleFactor(0.6)
                    .frame(width: w).position(x: w / 2, y: 40)
                Circle().fill(skin.glow).overlay(Circle().stroke(.white, lineWidth: 2.5)).frame(width: 20, height: 20)
                    .shadow(color: .black.opacity(0.3), radius: 2, y: 1)
                    .position(x: x(for: shownBoard, width: w), y: 12)
            }
            .overlay(Capsule().strokeBorder(skin.frame, lineWidth: 2.5))
            .contentShape(Rectangle())
            .gesture(DragGesture(minimumDistance: 0).onChanged { g in
                let b = board(atX: g.location.x, width: w)
                if b != slideBoard { slideBoard = b; session.command("bowlBoard", value: b); UISelectionFeedbackGenerator().selectionChanged() }
            }.onEnded { _ in
                // keep showing it until the game's state has caught up
                let b = slideBoard
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { if slideBoard == b { slideBoard = nil } }
            })
        }
        .frame(height: 68)
        .accessibilityElement().accessibilityLabel("Board \(boardText)").accessibilityAdjustableAction { dir in step(dir == .increment ? -1 : +1) }
    }

    private var boardText: String { String(format: shownBoard.truncatingRemainder(dividingBy: 1) == 0 ? "Board %.0f" : "Board %.1f", shownBoard) }
    /// Boards 3...37 (the game's own limits), to the half board; x runs from board 39.5 (left gutter) to 0.5 (right gutter).
    private func board(atX x: CGFloat, width: CGFloat) -> Double { min(37, max(3, ((39.5 - 39 * Double(x / max(1, width))) * 2).rounded() / 2)) }
    private func x(for board: Double, width: CGFloat) -> CGFloat { CGFloat((39.5 - board) / 39) * width }
    /// One board along (+ = left), from where the bowler is shown to stand.
    private func step(_ boards: Double) {
        let b = min(37, max(3, (shownBoard + boards).rounded()))
        guard b != shownBoard else { return }
        slideBoard = b; session.command("bowlBoard", value: b)
        let shown = b
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) { if slideBoard == shown { slideBoard = nil } }
    }

    /// What the ball does now (under it on the TV layout, beside it on the handheld deck).
    private var ballCaption: String {
        holding ? "Swing · let go at the bottom" : state.walking ? "Tap to skip" : state.canHold ? "Hold to start" : !state.mine && !state.player.isEmpty ? "\(state.player) is bowling" : "Watch the pins"
    }
    private var ballCaptionLive: Bool { holding || state.canHold || state.walking }
    private var ball: some View {
        VStack(spacing: 18) {
            ballView(caption: false)
            // board: a cream pill, "Hold to start" over "Let go to release"
            VStack(spacing: 0) {
                Text(ballCaption).font(MapFont.bold(24)).lineLimit(1).minimumScaleFactor(0.6)
                if state.canHold && !holding { Text("Let go to release").font(MapFont.semi(17)) }
            }
            .foregroundStyle(ballCaptionLive ? skin.accentInk : skin.ink.opacity(0.7))
            .padding(.horizontal, 26).padding(.vertical, 10).frame(minWidth: 260)
            .background { Capsule().fill(skin.accentDeep).offset(y: 4); Capsule().fill(ballCaptionLive ? skin.accent : skin.cream) }
        }
    }
    /// The ball: press and hold to pick it up and start the approach; lift your thumb to let it go.
    private func ballView(caption: Bool) -> some View {
        ZStack {
            // the spotlight behind the hero object, in the centre's light
            Circle().fill(RadialGradient(colors: [skin.glow.opacity(0.4), .clear], center: .center, startRadius: 40, endRadius: 210)).frame(width: 420, height: 420)
            if let art = skin.ballImage {
                // the centre's own ball from the board (maroon in gold, neon purple, teal marble, cracked lava)
                Image(uiImage: art).resizable().interpolation(.high).scaledToFit().frame(width: 270, height: 270)
                    .shadow(color: .black.opacity(0.4), radius: 14, y: 10)
                    .overlay { if holding { Circle().strokeBorder(skin.glow, lineWidth: 8).frame(width: 250, height: 250).shadow(color: skin.glow, radius: 12) } }
            } else {
            // the club ball: deep teal-to-navy pearl, with the gold primary ring (the one gold action)
            Circle().fill(RadialGradient(colors: [Color(hex: "2E8C8A"), MSBrand.navyInk], center: .init(x: 0.35, y: 0.3), startRadius: 10, endRadius: 170))
                .shadow(color: MSBrand.shadowInk.opacity(0.43), radius: 14, y: 11)
            Circle().stroke(LinearGradient(colors: [MSBrand.gold, MSBrand.goldWordmark], startPoint: .top, endPoint: .bottom), lineWidth: holding ? 10 : 7)
            ForEach(Array([(CGPoint(x: 0, y: 46), CGFloat(34)), (CGPoint(x: -24, y: -34), 26), (CGPoint(x: 24, y: -34), 26)].enumerated()), id: \.offset) { _, hole in
                Circle().fill(MSBrand.navyInk.opacity(0.85)).frame(width: hole.1, height: hole.1).offset(x: hole.0.x, y: hole.0.y)
            }
            }
        }
        .frame(width: 260, height: 260)
        .scaleEffect(holding ? 0.94 : 1).animation(.easeOut(duration: 0.12), value: holding)   // BrandMotion press: 0.94, 0.12 s
        .contentShape(Circle())
        .gesture(DragGesture(minimumDistance: 0)
            .onChanged { _ in
                if !holding && state.walking && !skipSent { skipSent = true; session.command("bowlSkip", value: 1); UIImpactFeedbackGenerator(style: .light).impactOccurred() }
                else if !holding && !skipSent && state.canHold { press() }
            }
            .onEnded { _ in skipSent = false; if holding { release() } })
        .accessibilityLabel("Bowling ball. Hold to start the approach, let go to release. Tap to skip a walk.")
        .opacity(state.canHold || holding || state.walking ? 1 : 0.5)
    }

    /// LAST THROW on the centre's card, with the release grade and the pause button (boards 07-10).
    private var lastThrow: some View {
        VStack(spacing: 8) {
            HStack(spacing: 14) {
                VStack(spacing: -6) {
                    // (Club Lanes' card has LAST THROW on it; the others get it above, with how the release went)
                    if skin.id != "bowling-club" || (!state.grade.isEmpty && state.mph > 0) {
                        Text([skin.id != "bowling-club" ? "LAST THROW" : nil, !state.grade.isEmpty && state.mph > 0 ? gradeText.uppercased() : nil].compactMap { $0 }.joined(separator: " · "))
                            .font(MapFont.bold(13)).tracking(1.2).foregroundStyle(state.grade == "Perfect" ? skin.glow : .white.opacity(0.85)).lineLimit(1).minimumScaleFactor(0.7)
                            .padding(.bottom, 8)
                    }
                    MapPlate(skin: skin, kind: .card, text: state.mph > 0 ? String(format: "%.1f MPH", state.mph) : "– MPH", height: 92)
                }
                .accessibilityElement(children: .ignore).accessibilityLabel(state.mph > 0 ? String(format: "Last throw %.1f miles an hour", state.mph) : "No throw yet")
                .accessibilityIdentifier("bowling-last-throw")
                Button { session.pause() } label: { MapPauseFace(skin: skin, size: 58) }
                    .buttonStyle(.plain).accessibilityLabel("Pause bowling").accessibilityIdentifier("bowling-pause")
            }
        }
    }

    private var aimText: String {
        let a = state.aim
        if abs(a) < 0.05 { return "straight" }
        return String(format: "aimed %.1f° %@", abs(a), a > 0 ? "right" : "left")
    }

    private var gradeText: String {
        switch state.grade {
        case "Perfect": "PERFECT!"; case "Good": "Good release."; case "Early": "A touch early."
        case "Late": "Late. You lofted it."; case "Foul": "Foul. You held it too long."; case "Drop": "Oops! It slipped."
        default: state.grade
        }
    }

    private func press() {
        holding = true
        session.command("bowlHold", value: 1)
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        BowlingHaptics.prepare()
    }

    private func release() {
        holding = false
        session.command("bowlHold", value: 0)
    }
}


/// A round step button that steps once on touch, then keeps stepping while held: 4 a second after 0.35 s, rising to 16 a second
/// (board 20 to the edge, 17 boards, in about 1.8 s held, against 34 taps of half a board before 10-27).
private struct StepButton: View {
    let skin: MapSkin
    let icon: String, label: String, action: () -> Void
    @State private var repeater: Task<Void, Never>?

    var body: some View {
        Image(systemName: icon).font(.system(size: 24, weight: .black)).foregroundStyle(skin.ink)
            .frame(width: 60, height: 60).background(skin.cream, in: Circle())
            .overlay(Circle().strokeBorder(skin.frameDeep, lineWidth: 2.5))
            .scaleEffect(repeater != nil ? 0.94 : 1).animation(.easeOut(duration: 0.12), value: repeater != nil)
            .contentShape(Circle())
            .gesture(DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    guard repeater == nil else { return }
                    action()
                    repeater = Task { @MainActor in
                        try? await Task.sleep(for: .milliseconds(350))
                        var gap = 0.25
                        while !Task.isCancelled {
                            action()
                            try? await Task.sleep(for: .seconds(gap))
                            gap = max(0.0625, gap * 0.8)
                        }
                    }
                }
                .onEnded { _ in repeater?.cancel(); repeater = nil })
            .onDisappear { repeater?.cancel(); repeater = nil }
            .accessibilityLabel(label).accessibilityAddTraits(.isButton)
    }
}

/// The self-timed swing's haptics (bowlCue from Unity): a light tick when the backswing turns forward, a firm short buzz as the
/// arm passes the bottom. They confirm the player's own swing; nothing waits on them.
@MainActor enum BowlingHaptics {
    private static let tick = UIImpactFeedbackGenerator(style: .light), buzz = UIImpactFeedbackGenerator(style: .heavy)
    static func prepare() { tick.prepare(); buzz.prepare() }
    static func cue(_ name: String) {
        switch name {
        case "top": tick.impactOccurred(intensity: 0.7)
        case "bottom": buzz.impactOccurred(intensity: 1)
        default:
            // "crash:<pins>": the pins go down on screen; a rumble as big as the hit (a strike gets a burst)
            guard name.hasPrefix("crash:"), let pins = Int(name.dropFirst(6)), pins > 0 else { return }
            let hits = min(6, 1 + pins / 2), strength = min(1, 0.35 + Double(pins) * 0.065)
            Task { @MainActor in
                for i in 0..<hits {
                    buzz.impactOccurred(intensity: strength * (1 - Double(i) * 0.12))
                    try? await Task.sleep(for: .milliseconds(pins >= 10 ? 55 : 80))
                }
                if pins >= 10 { UINotificationFeedbackGenerator().notificationOccurred(.success) }
            }
        }
    }
}
