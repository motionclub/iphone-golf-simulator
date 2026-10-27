import SwiftUI
import UIKit

/// What Unity's BowlingGame reports 4 times a second (NativeSportsSession.Bowling.cs):
/// phase|player|frame|ball|board|grade|mph|hook°|rpm|standing pins.
struct BowlingControllerState: Equatable {
    var phase = "Setup", player = "", frame = 1, ball = 1, board = 20.0
    var grade = "", mph = 0.0, hook = 0, rpm = 0, standing = ""
    /// This phone bowls now (false: a friend's phone or the computer bowler is up).
    var mine = true

    init() {}
    init(_ line: String) {
        let p = line.split(separator: "|", omittingEmptySubsequences: false).map(String.init)
        guard p.count >= 10 else { return }
        phase = p[0]; player = p[1]; frame = Int(p[2]) ?? 1; ball = Int(p[3]) ?? 1; board = Double(p[4]) ?? 20
        grade = p[5]; mph = Double(p[6]) ?? 0; hook = Int(p[7]) ?? 0; rpm = Int(p[8]) ?? 0; standing = p[9]
        if p.count > 10 { mine = p[10] != "0" }
    }

    /// The ball can be picked up (setup) or is in the hand (hold, approach).
    var canHold: Bool { mine && (phase == "Setup" || phase == "Hold" || phase == "Approach") }
    var canMove: Bool { mine && phase == "Setup" }
}

/// The phone while bowling (PLAN_PhonePlay_NoTV_GolfBowling.md §5, bowling V2): move along the approach, then press and HOLD
/// the ball. The bowler walks up at one steady pace (the computer's); swing with them: push away, swing back, swing through, and
/// let go just as your arm passes the bottom. The release is judged against your own arm; the bowler lets the ball go on their
/// own beat. Turn your wrist into a handshake as you let go to hook it. The phone ticks at the top of your backswing and buzzes
/// as your arm passes the bottom (BowlingHaptics, from the game's bowlCue).
struct BowlingPhoneController: View {
    @Bindable var session: SportsSession
    @State private var holding = false
    @State private var dragBoards = 0.0
    private var state: BowlingControllerState { BowlingControllerState(session.bowlingState) }

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
    }

    private var gameOver: Bool { state.phase == "GameOver" }

    /// With a TV: the phone is the controller, full screen.
    private var tvLayout: some View {
        VStack(spacing: 18) {
            header
            moveStrip
            Spacer(minLength: 0)
            if gameOver { finishButton } else { ball }
            Spacer(minLength: 0)
            lastThrow
        }
        .padding(.horizontal, 20).padding(.vertical, 24)
        // brand background: Deep Navy at the top → Royal by 24 %, then flat
        .background(LinearGradient(stops: [.init(color: MSBrand.navyDeep, location: 0), .init(color: MSBrand.royal, location: 0.24), .init(color: MSBrand.royal, location: 1)],
                                   startPoint: .top, endPoint: .bottom).ignoresSafeArea())
    }

    /// No TV: the lane fills the screen (Unity, under this see-through window) and the controls sit over its foot, so the
    /// bowler, the ball and the pins stay in view between throws.
    private var phoneLayout: some View {
        VStack(spacing: 10) {
            Spacer(minLength: 0)
            if gameOver { finishButton.padding(.bottom, 30) }
            else {
                if !state.grade.isEmpty && state.mph > 0 && state.canMove {
                    Text(gradeText).font(MSBrand.font(.heading, 22)).foregroundStyle(state.grade == "Perfect" ? MSBrand.gold : MSBrand.white)
                        .shadow(color: MSBrand.textShadow.opacity(0.8), radius: 3, y: 1)
                }
                moveStrip.padding(.horizontal, 6)
                ball.scaleEffect(0.62).frame(height: 190)
            }
        }
        .padding(.horizontal, 16).padding(.bottom, 8)
        // a soft navy fade at the foot keeps the controls legible over the lane
        .background(alignment: .bottom) {
            LinearGradient(colors: [.clear, MSBrand.navyInk.opacity(0.85)], startPoint: .top, endPoint: .bottom).frame(height: 360).ignoresSafeArea()
        }
    }

    /// The game is over: on to the XP and results.
    private var finishButton: some View {
        Button { TennisMenu.shared.beginPostMatch() } label: {
            Text("FINISH").font(MSBrand.font(.button, 30)).foregroundStyle(MSBrand.navyInk)
                .frame(maxWidth: 320, minHeight: 72).background(LinearGradient(colors: [MSBrand.gold, MSBrand.goldWordmark], startPoint: .top, endPoint: .bottom), in: Capsule())
        }
        .buttonStyle(.plain).accessibilityIdentifier("bowling-finish")
    }

    // Two-line brand headline: white sets it up, gold pays it off.
    private var header: some View {
        VStack(spacing: 2) {
            Text(state.player.isEmpty ? "Roll it." : "\(state.player)'s up.").font(MSBrand.font(.title, 50)).foregroundStyle(MSBrand.white)
            Text("Frame \(state.frame) · Ball \(state.ball)").font(MSBrand.font(.title, 36)).foregroundStyle(MSBrand.gold)
        }
        .shadow(color: MSBrand.textShadow.opacity(0.55), radius: 2, y: 1)
    }

    private var moveStrip: some View {
        HStack(spacing: 12) {
            moveButton("chevron.left", boards: +1)
            VStack(spacing: 2) {
                Text("BOARD").font(MSBrand.font(.hudLabel, 14)).tracking(3).foregroundStyle(MSBrand.n300)
                Text(String(format: state.board.truncatingRemainder(dividingBy: 1) == 0 ? "%.0f" : "%.1f", state.board))
                    .font(MSBrand.font(.hudNumber, 40)).foregroundStyle(MSBrand.gold).monospacedDigit()
            }
            .frame(maxWidth: .infinity, minHeight: 72)
            .background(MSBrand.navyDeep.opacity(0.92), in: RoundedRectangle(cornerRadius: 17))
            .overlay(RoundedRectangle(cornerRadius: 17).stroke(MSBrand.white, lineWidth: 3))
            .gesture(DragGesture(minimumDistance: 4).onChanged { g in
                // dragging left moves the bowler left (boards count from the right): one board per 14 pt
                let boards = (-g.translation.width / 14).rounded()
                if boards != dragBoards { session.command("bowlMove", value: (boards - dragBoards) / 2); dragBoards = boards }
            }.onEnded { _ in dragBoards = 0 })
            moveButton("chevron.right", boards: -1)
        }
        .opacity(state.canMove ? 1 : 0.35).disabled(!state.canMove)
    }

    private func moveButton(_ icon: String, boards: Double) -> some View {
        // secondary buttons: Deep Navy with a white border (gold is saved for the ball)
        Button { session.command("bowlMove", value: boards / 2) } label: {
            Image(systemName: icon).font(.system(size: 26, weight: .heavy)).foregroundStyle(MSBrand.white)
                .frame(width: 68, height: 68).background(MSBrand.navyDeep, in: Circle())
                .overlay(Circle().stroke(MSBrand.white, lineWidth: 3))
        }
        .accessibilityLabel(boards > 0 ? "Move left" : "Move right")
    }

    /// The ball: press and hold to pick it up and start the approach; lift your thumb to let it go.
    private var ball: some View {
        ZStack {
            // the spotlight behind the hero object (Lift at 55 %)
            Circle().fill(RadialGradient(colors: [MSBrand.lift.opacity(0.55), .clear], center: .center, startRadius: 40, endRadius: 210)).frame(width: 420, height: 420)
            // the club ball: deep teal-to-navy pearl, with the gold primary ring (the one gold action)
            Circle().fill(RadialGradient(colors: [Color(hex: "2E8C8A"), MSBrand.navyInk], center: .init(x: 0.35, y: 0.3), startRadius: 10, endRadius: 170))
                .shadow(color: MSBrand.shadowInk.opacity(0.43), radius: 14, y: 11)
            Circle().stroke(LinearGradient(colors: [MSBrand.gold, MSBrand.goldWordmark], startPoint: .top, endPoint: .bottom), lineWidth: holding ? 10 : 7)
            ForEach(Array([(CGPoint(x: 0, y: 46), CGFloat(34)), (CGPoint(x: -24, y: -34), 26), (CGPoint(x: 24, y: -34), 26)].enumerated()), id: \.offset) { _, hole in
                Circle().fill(MSBrand.navyInk.opacity(0.85)).frame(width: hole.1, height: hole.1).offset(x: hole.0.x, y: hole.0.y)
            }
            Text(holding ? "SWING · LET GO AT THE BOTTOM" : state.canHold ? "HOLD TO BOWL" : !state.mine && !state.player.isEmpty ? "\(state.player.uppercased()) IS BOWLING" : "WATCH THE PINS")
                .font(MSBrand.font(.button, 24)).foregroundStyle(holding || state.canHold ? MSBrand.gold : MSBrand.n300).multilineTextAlignment(.center)
                .offset(y: 160)
        }
        .frame(width: 260, height: 260)
        .scaleEffect(holding ? 0.94 : 1).animation(.easeOut(duration: 0.12), value: holding)   // BrandMotion press: 0.94, 0.12 s
        .contentShape(Circle())
        .gesture(DragGesture(minimumDistance: 0)
            .onChanged { _ in if !holding && state.canHold { press() } }
            .onEnded { _ in if holding { release() } })
        .accessibilityLabel("Bowling ball. Hold to start the approach, let go to release.")
        .opacity(state.canHold || holding ? 1 : 0.5)
    }

    private var lastThrow: some View {
        VStack(spacing: 6) {
            if !state.grade.isEmpty && state.mph > 0 {
                Text(gradeText).font(MSBrand.font(.heading, 28)).foregroundStyle(state.grade == "Perfect" ? MSBrand.gold : MSBrand.white)
                Text(String(format: "%.1f mph · hook %d° · %d rpm", state.mph, abs(state.hook), state.rpm))
                    .font(MSBrand.font(.body, 17)).foregroundStyle(MSBrand.white).monospacedDigit()
            }
            Text("Swing with your bowler's steps. Let go as your arm swings through the bottom; turn your wrist like a handshake to hook it.")
                .font(MSBrand.font(.caption, 15)).foregroundStyle(MSBrand.n300).multilineTextAlignment(.center)
        }
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
