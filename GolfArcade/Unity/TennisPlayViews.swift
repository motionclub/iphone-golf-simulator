import SwiftUI

/// What the TV shows whenever a match is not on: the menu, loading and results, laid out on a
/// 1280×720 canvas and scaled to the screen so every TV frames it the same.
struct TennisTVRoot: View {
    var body: some View {
        GeometryReader { g in
            // Fit the 1280×720 canvas (16:10 Mac screens get backdrop above and below), less
            // the edge margin for TVs that crop.
            let scale = min(g.size.width / 1280, g.size.height / 720) * (1 - SportsSession.shared.overscan)
            ZStack {
                Club.lagoonDeep   // around the canvas on 16:10 screens; each screen paints its own scene
                Group {
                    // the Plaza is the TV's only menu: its loading screen (or why it did not open), then the plaza itself (this window hides)
                    if HubSession.shared.drivesPhone || !SportsSession.shared.active { HubLoadingScreen(hub: .shared) }
                    // a match from the Plaza or the pointer menu: this window is hidden under the match and only its pause screen is ever
                    // shown. The classic home it used to fall through to built a SceneKit hero (~130 MB rig) and the club cinemagraph just
                    // as the match loaded (10-26 20:39 party golf: killed for memory).
                    else if SportsSession.shared.active && !SportsSession.shared.menuPauseVisible { Color.clear }
                    else { TennisMenuScreen(compact: false)
                        .overlay(alignment: .bottomTrailing) {
                            Text("Feedback on your phone").font(IslandUI.font(13, bold: true))
                                .foregroundStyle(IslandUI.ink).padding(8).background(IslandUI.paper, in: Capsule()).padding(12)
                                .allowsHitTesting(false)
                        }
                    }
                }
                    .frame(width: 1280, height: 720)
                    .scaleEffect(scale)
                    .frame(width: g.size.width, height: g.size.height)
            }
        }
        .ignoresSafeArea()
        .preferredColorScheme(.dark)
    }
}

/// The phone with no TV: the whole menu, upright and touch-driven.
struct TennisPhoneMenu: View {
    var body: some View {
        ZStack {
            IslandBrandBackground()
            TennisMenuScreen(compact: true)
        }
        .preferredColorScheme(.dark)
    }
}

// MARK: - In game

/// A big lime action button for the controller (Ready, Toss, Start timing check).
private struct ControllerButton: View {
    let title: String
    var icon: String? = nil
    var height: CGFloat = 64
    var size: CGFloat = 24
    /// Acts when the finger lands instead of when it lifts. For the controls where the lift is latency the player
    /// feels directly (TOSS, SWING); menu-like buttons keep the usual tap.
    var onPress = false
    let action: () -> Void
    var body: some View {
        if onPress {
            PressButton(action: action) { pressed in face.scaleEffect(pressed ? 0.97 : 1) }
        } else {
            Button(action: action) { face }.buttonStyle(.plain)
        }
    }
    // UI OVERHAUL 11-15: the map's one big action (accent face, deep lip, no icon), as on the boards' TOSS / Ready to play.
    private var face: some View {
        MapActionFace(skin: .current, title: title, height: height)
            .accessibilityElement(children: .ignore).accessibilityLabel(title)
    }
}

/// Acts the instant a finger lands, once per touch. SwiftUI's `Button` fires when the finger lifts, 60-120 ms later: on a
/// toss or a swing that is delay the player feels directly.
private struct PressButton<Label: View>: View {
    var enabled = true
    let action: () -> Void
    @ViewBuilder let label: (Bool) -> Label
    @State private var pressed = false
    var body: some View {
        label(pressed)
            .contentShape(Rectangle())
            .gesture(DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    guard enabled, !pressed else { return }
                    pressed = true; action()
                }
                .onEnded { _ in pressed = false })
            .accessibilityAddTraits(.isButton)
            .accessibilityAction { if enabled { action() } }
    }
}

/// The phone during a match: your racket. Its string bed is the same hit radar as the TV's, showing where each shot
/// met the strings and how well it was timed. Eyes are on the TV, so this screen stays calm: the score, the radar, stamina,
/// no buttons to hunt for during a rally (the Dive button went with the dive, 2026-11-13). Pausing needs a hold so a swing can never trigger it.
struct TennisRacketController: View {
    @Bindable var session: SportsSession
    @State private var showOptions = false
    @State private var shotAim = 0.0
    @State private var holdHint = false
    /// The map being played: the controller wears its material (UI OVERHAUL 11-15).
    private var skin: MapSkin { .current }
    var body: some View {
        VStack(spacing: 14) {
            if !session.showsOnlineTennisSetup { topBar }
            if session.finishedMatch != nil {
                MatchFinishControls(session: session)
            } else if session.showsOnlineTennisSetup {
                OnlineTennisSetupPanel(session: session)
                    .padding(.top, CaptureDock.reservedWidth(session: session) > 0 ? 52 : 0)
            } else if !session.ready || !session.loading.finished {
                // The same loading screen as the TV: tips, how-to cards, the flowing bar.
                LoadingScreen(menu: .shared, compact: true).padding(-24)
            } else if session.setupStage == .scan {
                ScrollView { AxisGatePanel(session: session) }
            } else if session.measuringDelay {
                DelayProbePanel(session: session)
            } else if session.timingPrompt {
                TimingCheckPrompt(session: session)
            } else if session.checkingTiming {
                TimingCheckPanel(countdownEnds: session.timingCountdownEnds)
            } else if session.setupStage == .ready {
                ControllerReadyPanel(session: session)
            } else if session.setupStage == .waiting {
                WaitingForPlayersPanel()
            } else if session.calibrationMode && session.sport == "tennis" && session.setupStage == .playing {
                CalibrationPanel(session: session)
            } else if !session.paused && (session.tennisPhase == "serve" || session.tennisPhase == "toss") {
                ServePanel(session: session)
            } else if !session.paused && session.tennisPhase == "receive" {
                ReceivePanel(session: session)
            } else {
                rallyCard
            }
            if session.ready && session.loading.finished && session.finishedMatch == nil {
                if session.canPlayEmote { TennisEmoteControls(session: session) }
            }
            if session.finishedMatch == nil && session.ready && session.paused && session.setupStage == .playing {
                Text(session.status).font(IslandUI.font(14, bold: true)).multilineTextAlignment(.center)
                ControllerButton(title: "Resume", icon: "play.fill") { session.readyToPlay() }
            }
            if session.ready && session.loading.finished && session.finishedMatch == nil && session.setupStage == .playing && session.tennisPhase == "point" {
                PointClipControls(session: session).tint(.white)
            }
        }
        .foregroundStyle(.white)
        .padding(20)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(MapControllerBackground(skin: skin))
        .preferredColorScheme(.dark)
        .sheet(isPresented: $showOptions) {
            IslandPauseScreen(compact: true) { showOptions = false }.presentationDetents([.large])
        }
    }

    /// The player's name on the map's plate (usernames only: no YOU, no score on the phone; the TV has it) and pause. Pause needs a
    /// hold while playing so a swing can never trigger it; paused, one tap opens the options.
    private var topBar: some View {
        MapControllerHeader(skin: skin, name: MapSkin.playerName(session), plateHeight: 104) {
            MapPauseFace(skin: skin, size: 48, symbol: session.paused ? "slider.horizontal.3" : "pause.fill")
                .onTapGesture { if session.paused { showOptions = true } else { withAnimation { holdHint = true } } }
                .onLongPressGesture(minimumDuration: 0.5) { if !session.paused { session.pause() }; showOptions = true }
                .accessibilityLabel(session.paused ? "Options" : "Pause. Hold to pause.")
                .accessibilityAddTraits(.isButton)
                .accessibilityAction(named: "Pause") { if !session.paused { session.pause() }; showOptions = true }
        }
        .overlay(alignment: .leading) {
            if !session.trackingWarning.isEmpty {
                Image(systemName: "exclamationmark.triangle.fill").font(.system(size: 22, weight: .bold)).foregroundStyle(.orange)
            }
        }
        // the record / mic / chat / gear dock floats over the top-right corner: keep the plate clear of it
        .padding(.trailing, CaptureDock.reservedWidth(session: session))
        .overlay(alignment: .bottomTrailing) {
            if holdHint {
                Text("Hold to pause").font(MapFont.bold(13)).foregroundStyle(skin.accentInk)
                    .padding(.horizontal, 10).padding(.vertical, 5).background(skin.accent, in: Capsule()).offset(y: 30)
                    .task { try? await Task.sleep(for: .seconds(1.6)); withAnimation { holdHint = false } }
            }
        }
    }

    /// During a rally: RALLY, the racket's hit radar and stamina, on one panel of the map's surface (board: RALLY · radar · STAMINA).
    private var rallyCard: some View {
        VStack(spacing: 12) {
            HStack {
                Text("RALLY").font(MapFont.bold(16)).tracking(1).foregroundStyle(skin.ink)
                    .padding(.horizontal, 14).padding(.vertical, 5).background(skin.cream, in: Capsule())
                Spacer()
            }
            RacketRadar(contacts: session.contacts).frame(maxWidth: .infinity, maxHeight: .infinity)
            stamina
        }
        .padding(16).mapPanel(skin, radius: 26)
        .accessibilityIdentifier("controller-rally")
    }

    private var stamina: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 0) {
                Text("STAMINA").font(MapFont.bold(12)).tracking(1).foregroundStyle(skin.ink.opacity(0.75))
                Text("\(Int(session.stamina * 100))%").font(MapFont.bold(26)).foregroundStyle(skin.ink).monospacedDigit()
            }
            Capsule().fill(skin.ink.opacity(0.15)).frame(height: 12)
                .overlay(alignment: .leading) {
                    GeometryReader { g in Capsule().fill(session.stamina > 0.35 ? skin.glow : Arcade.crimson).frame(width: g.size.width * min(1, max(0, session.stamina))) }
                }
        }
        .padding(.horizontal, 14).padding(.vertical, 8)
        .background(skin.cream, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
        .accessibilityElement(children: .combine).accessibilityIdentifier("controller-stamina")
    }
}

struct TennisEmoteControls: View {
    let session: SportsSession
    var body: some View {
        let intro = session.emoteWindow == "intro"
        EquippedEmoteControls(title: intro ? "Choose an emote" : "Celebrate your point", ids: session.matchEmotes,
            enabled: session.canPlayEmote,
            notice: session.emoteNotice.isEmpty ? (intro ? "Your player does it on the TV when they're introduced." : "Choose an emote to celebrate your point.") : session.emoteNotice,
            identifier: "controller-emote") { session.playEmote(slot: $0) }
    }
}

/// Shared presentation for the same equipped emotes in golf and tennis.
struct EquippedEmoteControls: View {
    let title: String
    let ids: [String]
    let enabled: Bool
    let notice: String
    let identifier: String
    let select: (Int) -> Void
    /// The map the emotes are picked on (UI OVERHAUL 11-15: cream tiles on the map's material, as board 12's "Choose an emote").
    private var skin: MapSkin { .current }
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title).font(MapFont.bold(15))
                .foregroundStyle(enabled ? skin.ink : skin.ink.opacity(0.5))
                .padding(.horizontal, 14).padding(.vertical, 5).background(skin.cream, in: Capsule())
            HStack(spacing: 8) {
                ForEach(Array(ids.enumerated()), id: \.offset) { slot, id in
                    Button { select(slot) } label: {
                        VStack(spacing: 2) {
                            Text("\(slot + 1)").font(MapFont.semi(11)).opacity(0.55)
                            Text(EmoteCatalog.name(id)).font(MapFont.bold(15)).lineLimit(1).minimumScaleFactor(0.75)
                        }.frame(maxWidth: .infinity, minHeight: 54)
                            .foregroundStyle(skin.ink.opacity(enabled ? 1 : 0.45))
                            .background {
                                RoundedRectangle(cornerRadius: 16, style: .continuous).fill(skin.frameDeep).offset(y: 3)
                                RoundedRectangle(cornerRadius: 16, style: .continuous).fill(skin.cream.opacity(enabled ? 1 : 0.55))
                                RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(skin.frame, lineWidth: 2)
                            }
                    }.buttonStyle(.plain).disabled(!enabled)
                        .accessibilityIdentifier("\(identifier)-\(slot)")
                        .accessibilityLabel("Play \(EmoteCatalog.name(id)), emote slot \(slot + 1)")
                }
            }
            Text(notice).font(MapFont.semi(12)).foregroundStyle(.white.opacity(0.75))
        }
    }
}

// MARK: - Serve

/// The player's serve on the controller (board: court · T / WIDE · ◀ ▶ · TOSS): tap the court or a T / WIDE pill to aim, hold ◀ ▶ to
/// walk along the baseline, then TOSS. After the toss: swing as the TV's power bar peaks.
private struct ServePanel: View {
    @Bindable var session: SportsSession
    private var skin: MapSkin { .current }
    var body: some View {
        VStack(spacing: 14) {
            if session.tennisPhase == "toss" {
                Spacer()
                Image(systemName: "figure.tennis").font(.system(size: 64)).foregroundStyle(skin.glow)
                    .shadow(color: skin.glow.opacity(0.6), radius: 14)
                Text("SWING!").font(MapFont.bold(30)).foregroundStyle(skin.cream)
                Spacer()
            } else {
                ServeAimPad(session: session).frame(maxWidth: .infinity).frame(height: 210)
                HStack(spacing: 16) {
                    aimPill("T", across: -0.75)
                    aimPill("WIDE", across: 0.75)
                }
                MoveButtons(session: session, caption: "Hold to walk the baseline")
                Spacer(minLength: 0)
                ControllerButton(title: "TOSS", icon: "arrow.up.circle.fill", height: 104, size: 40, onPress: true) {
                    if session.haptics { UIImpactFeedbackGenerator(style: .rigid).impactOccurred() }
                    session.toss()
                }.accessibilityIdentifier("tennisToss")
            }
        }
    }
    /// Aim down the T or out wide, keeping the depth.
    private func aimPill(_ title: String, across: Double) -> some View {
        let lit = (across < 0) == (session.serveAim.across < 0) && abs(session.serveAim.across) > 0.4
        return Button {
            session.setServeAim(across: across, depth: session.serveAim.depth)
            if session.haptics { UISelectionFeedbackGenerator().selectionChanged() }
        } label: {
            MapPill(skin: skin, height: 50, lit: lit) { Text(title) }.frame(maxWidth: .infinity)
        }.buttonStyle(.plain).accessibilityIdentifier("serve-aim-\(title.lowercased())")
    }
}

/// The target box seen from behind the baseline, with the aim point on it. A tap sets the target. The T (centre line) is on
/// the right of the box from the deuce court and on the left from the ad court. Drawn in the map's court colours with a ring target.
struct ServeAimPad: View {
    @Bindable var session: SportsSession
    private var skin: MapSkin { .current }
    var body: some View {
        GeometryReader { g in
            let w = g.size.width, h = g.size.height
            let boxW = w * 0.5, boxLeft = session.serveFromDeuce ? 0 : w * 0.5
            let across = session.serveAim.across, depth = session.serveAim.depth
            let u = session.serveFromDeuce ? 1 - (across + 1) / 2 : (across + 1) / 2
            let point = CGPoint(x: boxLeft + u * boxW, y: (1 - depth) * h)
            ZStack {
                RoundedRectangle(cornerRadius: 18).fill(skin.surface)
                Rectangle().fill(.white.opacity(0.12)).frame(width: boxW, height: h).position(x: boxLeft + boxW / 2, y: h / 2)
                Path { p in
                    p.move(to: CGPoint(x: w / 2, y: 0)); p.addLine(to: CGPoint(x: w / 2, y: h))
                    p.addRect(CGRect(x: 1, y: 1, width: w - 2, height: h - 2))
                }.stroke(skin.line, lineWidth: 2.5)
                Rectangle().fill(skin.line).frame(height: 5).position(x: w / 2, y: h - 2)
                Text("NET").font(MapFont.bold(11)).foregroundStyle(skin.line.opacity(0.75)).position(x: w / 2, y: h - 13)
                Text("T").font(MapFont.bold(20)).foregroundStyle(skin.line)
                    .position(x: session.serveFromDeuce ? boxW - 16 : boxW + 16, y: 18)
                Text("WIDE").font(MapFont.bold(18)).foregroundStyle(skin.line)
                    .position(x: session.serveFromDeuce ? 34 : w - 34, y: 18)
                ZStack {
                    Circle().strokeBorder(skin.glow, lineWidth: 4).frame(width: 44, height: 44)
                    Circle().strokeBorder(skin.glow.opacity(0.85), lineWidth: 3).frame(width: 26, height: 26)
                    Circle().fill(skin.cream).frame(width: 12, height: 12)
                }
                .shadow(color: skin.glow, radius: 8)
                .position(point)
            }
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .overlay(RoundedRectangle(cornerRadius: 18).strokeBorder(skin.frame, lineWidth: 3))
            .contentShape(Rectangle())
            .gesture(SpatialTapGesture().onEnded { v in
                let x = min(max(v.location.x, boxLeft), boxLeft + boxW)
                let u = (x - boxLeft) / boxW
                let across = Double(session.serveFromDeuce ? 1 - 2 * u : 2 * u - 1)
                let depth = Double(1 - min(max(v.location.y / h, 0), 1))
                session.setServeAim(across: across, depth: depth)
                if session.haptics { UISelectionFeedbackGenerator().selectionChanged() }
            })
            .accessibilityElement().accessibilityLabel("Serve target. Tap to aim.")
        }
    }
}

/// While the opponent serves: get in position.
private struct ReceivePanel: View {
    @Bindable var session: SportsSession
    var body: some View {
        VStack(spacing: 18) {
            Spacer()
            Image(systemName: "figure.tennis").font(.system(size: 64)).foregroundStyle(MapSkin.current.glow)
                .shadow(color: MapSkin.current.glow.opacity(0.6), radius: 14)
            MoveButtons(session: session, caption: "Hold to walk")
            Spacer()
        }
    }
}

/// Hold to walk left or right: two cream ◀ ▶ pills.
private struct MoveButtons: View {
    let session: SportsSession
    let caption: String
    @State private var held = 0.0
    private var skin: MapSkin { .current }
    var body: some View {
        VStack(spacing: 6) {
            HStack(spacing: 16) {
                hold("chevron.left", -1)
                hold("chevron.right", 1)
            }
            Text(caption).font(MapFont.semi(13)).foregroundStyle(.white.opacity(0.75))
        }
        .onDisappear { held = 0; session.nudge(0) }
    }
    private func hold(_ icon: String, _ direction: Double) -> some View {
        let on = held == direction
        return MapPill(skin: skin, height: 64, lit: on) { Image(systemName: icon).font(.system(size: 28, weight: .black)) }
            .frame(maxWidth: .infinity)
            .scaleEffect(on ? 0.96 : 1)
            .contentShape(Capsule())
            .gesture(DragGesture(minimumDistance: 0)
                .onChanged { _ in if held != direction { held = direction; session.nudge(direction) } }
                .onEnded { _ in held = 0; session.nudge(0) })
            .accessibilityLabel(direction < 0 ? "Move left" : "Move right")
    }
}

// MARK: - Setup

/// While the TV flashes: the camera is timing how far its picture lags the game (board 13 screen 1: Set your direction).
private struct DelayProbePanel: View {
    let session: SportsSession
    @State private var pulse = false
    private var skin: MapSkin { .current }
    var body: some View {
        ScrollView {
            MapSetupCard(skin: skin, name: MapSkin.playerName(session), title: "Measure screen delay") {
                SportsCameraPreview(motion: session.motion).frame(height: 170)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .overlay { Image(systemName: "plus").font(.title).foregroundStyle(.white) }
                    .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(skin.frame, lineWidth: 3))
                    .scaleEffect(pulse ? 1.02 : 0.98)
                Text("Point the back of your phone at the TV. It will flash a few times while we time its picture, so your swings land when you see the ball.")
                    .font(MapFont.semi(16)).multilineTextAlignment(.center)
                ProgressView().tint(skin.accentDeep)
            }
            .padding(.top, 8)
        }
        .scrollIndicators(.hidden)
        .onAppear { withAnimation(.easeInOut(duration: 0.5).repeatForever(autoreverses: true)) { pulse = true } }
    }
}

/// Offered the first time on a TV: what the timing check is for, and a button to start it (board 13 screen 2: Timing check).
private struct TimingCheckPrompt: View {
    let session: SportsSession
    private var skin: MapSkin { .current }
    var body: some View {
        ScrollView {
            MapSetupCard(skin: skin, name: MapSkin.playerName(session), title: "Timing check") {
                BounceMark(skin: skin).frame(height: 96)
                Text("Swing on every bounce.").font(MapFont.bold(20)).multilineTextAlignment(.center)
                Text("Every TV shows the picture a little late. This quick check measures that delay so your swings land exactly when you see the ball.")
                    .font(MapFont.semi(15)).multilineTextAlignment(.center).opacity(0.85)
                if !session.timingNote.isEmpty {
                    Text(session.timingNote).font(MapFont.semi(14)).multilineTextAlignment(.center)
                }
                if !session.delayTip.isEmpty {
                    Text(session.delayTip).font(MapFont.semi(13)).multilineTextAlignment(.center).opacity(0.8)
                        .accessibilityIdentifier("timing-tv-delay")
                }
                ControllerButton(title: "Start timing check", icon: "play.fill", height: 60, size: 21) { session.startTimingCheck() }.accessibilityIdentifier("timing-start")
                MapQuietButton(skin: skin, title: "Skip for now") { session.skipTimingCheck() }.accessibilityIdentifier("timing-skip")
                Button("Retry screen flashes") { session.measureTVDelay() }.font(MapFont.semi(14)).tint(skin.ink.opacity(0.7))
                    .accessibilityIdentifier("timing-flashes")
            }
            .padding(.top, 8)
        }
        .scrollIndicators(.hidden)
    }
}

/// Board 13's bounce picture: a ball hopping over a line with a gold mark where to swing.
private struct BounceMark: View {
    let skin: MapSkin
    @State private var up = false
    var body: some View {
        GeometryReader { g in
            let w = g.size.width, h = g.size.height
            ZStack {
                Path { p in
                    p.move(to: CGPoint(x: w * 0.18, y: h * 0.72)); p.addQuadCurve(to: CGPoint(x: w * 0.5, y: h * 0.72), control: CGPoint(x: w * 0.34, y: -h * 0.2))
                    p.addQuadCurve(to: CGPoint(x: w * 0.82, y: h * 0.72), control: CGPoint(x: w * 0.66, y: -h * 0.2))
                }.stroke(skin.glow.opacity(0.55), style: StrokeStyle(lineWidth: 3, lineCap: .round, dash: [2, 7]))
                Capsule().fill(skin.surface).frame(width: w * 0.8, height: 10).position(x: w / 2, y: h * 0.8)
                Capsule().fill(Color(hex: "F5C542")).frame(width: 46, height: 14).overlay(Capsule().strokeBorder(.white, lineWidth: 2)).position(x: w / 2, y: h * 0.8)
                Circle().fill(skin.glow).overlay(Circle().strokeBorder(.white, lineWidth: 3)).frame(width: 30, height: 30)
                    .position(x: w / 2, y: up ? h * 0.12 : h * 0.66)
            }
        }
        .onAppear { withAnimation(.easeInOut(duration: 0.55).repeatForever(autoreverses: true)) { up = true } }
        .accessibilityHidden(true)
    }
}

/// While the TV runs the timing check: a get-ready countdown, then swing with the ball.
private struct TimingCheckPanel: View {
    let countdownEnds: Date?
    private var skin: MapSkin { .current }
    var body: some View {
        TimelineView(.periodic(from: .now, by: 0.2)) { context in
            let left = countdownEnds.map { max(0, $0.timeIntervalSince(context.date)) } ?? 0
            VStack {
                Spacer(minLength: 0)
                MapSetupCard(skin: skin, name: MapSkin.playerName(.shared), title: left > 0 ? "Get ready" : "Swing on every bounce!") {
                    if left > 0 {
                        Text("\(Int(left.rounded(.up)))").font(MapFont.bold(110)).foregroundStyle(skin.accentDeep).monospacedDigit()
                        Text("Swing every time the ball drops onto the line.").font(MapFont.semi(16)).multilineTextAlignment(.center)
                    } else {
                        BounceMark(skin: skin).frame(height: 96)
                        Text("Follow the ball on the display. Two bounces warm you up; the next seven record your timing. Reset your arm between swings.")
                            .font(MapFont.semi(15)).multilineTextAlignment(.center)
                    }
                }
                Spacer(minLength: 0)
            }
        }
    }
}

private struct Scoreline: View {
    let session: SportsSession
    var body: some View {
        HStack(spacing: 10) {
            Text("YOU").font(IslandUI.font(15, bold: true)).foregroundStyle(IslandUI.lime)
            Text("\(session.score.player)").font(IslandUI.font(26, bold: true)).monospacedDigit()
            Text("–").font(IslandUI.font(20, bold: true)).foregroundStyle(.white.opacity(0.5))
            Text("\(session.score.opponent)").font(IslandUI.font(26, bold: true)).monospacedDigit()
            Text(session.opponentName.uppercased()).font(IslandUI.font(15, bold: true)).foregroundStyle(Arcade.sky).lineLimit(1).minimumScaleFactor(0.7)
            Spacer(minLength: 4)
            if !session.score.detail.isEmpty {
                Text(session.score.detail.components(separatedBy: "·").dropFirst().first?.trimmingCharacters(in: .whitespaces) ?? "")
                    .font(IslandUI.font(13, bold: true)).foregroundStyle(.white.opacity(0.7)).lineLimit(1)
            }
        }
        .padding(.horizontal, 16).padding(.vertical, 8)
        .background(.white.opacity(0.1), in: Capsule())
    }
}

/// The racket seen face-on: frame, strings, the sweet spot, and a dot for each recent hit
/// (newest brightest). Contact x/y arrive in half-widths of the string bed.
struct RacketRadar: View {
    let contacts: [TennisContact]
    @State private var ripple = false

    static func color(_ c: TennisContact) -> Color {
        if c.supercharged { return Arcade.sea }
        switch c.grade {
        case 5: return Color(hex: "FFD145")
        case 4: return IslandUI.lime
        case 3: return Color(red: 0.45, green: 0.9, blue: 0.45)
        case 2: return Arcade.sky
        default: return Arcade.crimson
        }
    }

    var body: some View {
        GeometryReader { g in
            // String bed 0.35 m × 0.48 m: keep its real proportions.
            let headH = min(g.size.height * 0.70, g.size.width * 0.9 / 0.73)
            let headW = headH * 0.73
            let centre = CGPoint(x: g.size.width / 2, y: headH / 2 + 34)
            ZStack {
                // Handle and throat.
                Path { p in
                    let base = CGPoint(x: centre.x, y: centre.y + headH / 2)
                    p.move(to: CGPoint(x: base.x - headW * 0.28, y: base.y - headH * 0.05))
                    p.addLine(to: CGPoint(x: base.x - headW * 0.06, y: base.y + headH * 0.22))
                    p.move(to: CGPoint(x: base.x + headW * 0.28, y: base.y - headH * 0.05))
                    p.addLine(to: CGPoint(x: base.x + headW * 0.06, y: base.y + headH * 0.22))
                }.stroke(IslandUI.dark, style: StrokeStyle(lineWidth: 14, lineCap: .round))
                RoundedRectangle(cornerRadius: 10)
                    .fill(IslandUI.lime)
                    .frame(width: headW * 0.16, height: max(10, g.size.height - headH - 34 - headH * 0.2))
                    .position(x: centre.x, y: centre.y + headH / 2 + headH * 0.2 + max(10, g.size.height - headH - 34 - headH * 0.2) / 2)
                // Strings.
                Ellipse().fill(Color.white.opacity(0.06)).frame(width: headW, height: headH).position(centre)
                Path { p in
                    for i in 1..<14 {
                        let x = centre.x - headW / 2 + headW * CGFloat(i) / 14
                        p.move(to: CGPoint(x: x, y: centre.y - headH / 2)); p.addLine(to: CGPoint(x: x, y: centre.y + headH / 2))
                    }
                    for i in 1..<18 {
                        let y = centre.y - headH / 2 + headH * CGFloat(i) / 18
                        p.move(to: CGPoint(x: centre.x - headW / 2, y: y)); p.addLine(to: CGPoint(x: centre.x + headW / 2, y: y))
                    }
                }
                .stroke(.white.opacity(0.3), lineWidth: 1.5)
                .mask(Ellipse().frame(width: headW, height: headH).position(centre))
                // Sweet spot.
                ForEach(0..<3, id: \.self) { i in
                    Ellipse().strokeBorder(IslandUI.lime.opacity(0.6 - Double(i) * 0.17), lineWidth: 3)
                        .frame(width: headW * (0.3 + CGFloat(i) * 0.22), height: headH * (0.3 + CGFloat(i) * 0.22))
                        .position(centre)
                }
                Text("SWEET SPOT").font(IslandUI.font(11, bold: true)).tracking(2).foregroundStyle(IslandUI.lime.opacity(0.85))
                    .position(x: centre.x, y: centre.y + headH * 0.2)
                // Frame.
                Ellipse().strokeBorder(.white, lineWidth: headW * 0.055)
                    .frame(width: headW + headW * 0.055, height: headH + headW * 0.055).position(centre)
                    .shadow(color: .black.opacity(0.4), radius: 8, y: 5)
                // Hits.
                ForEach(Array(contacts.enumerated()), id: \.element.id) { i, c in
                    let newest = i == contacts.count - 1
                    let age = Double(contacts.count - 1 - i)
                    let p = CGPoint(x: centre.x + CGFloat(max(-1.1, min(1.1, c.x))) * headW / 2,
                                    y: centre.y - CGFloat(max(-1.1, min(1.1, c.y))) * headH / 2)
                    ZStack {
                        if newest {
                            Circle().stroke(Self.color(c), lineWidth: 4).frame(width: 34, height: 34)
                                .scaleEffect(ripple ? 2.6 : 1).opacity(ripple ? 0 : 1)
                        }
                        Circle().fill(Self.color(c)).frame(width: newest ? 30 : 18, height: newest ? 30 : 18)
                            .overlay(Circle().strokeBorder(.white, lineWidth: newest ? 3 : 1.5))
                            .shadow(color: Self.color(c), radius: newest ? 12 : 0)
                    }
                    .opacity(newest ? 1 : max(0.2, 0.8 - age * 0.07))
                    .position(p)
                }
            }
            .onChange(of: contacts.last?.id) { _, _ in
                ripple = false
                withAnimation(.easeOut(duration: 0.7)) { ripple = true }
            }
        }
    }
}

/// Shared by the regular controller, classic controller and landscape Unity overlay.
/// Never exposes an advance action before Unity confirms a completed match.
struct MatchFinishControls: View {
    @Bindable var session: SportsSession
    var compact = false
    var body: some View {
        if let result = session.finishedMatch {
            VStack(alignment: .leading, spacing: 16) {
                ScrollView {
                    ClubVictorySummary(won: result.won, score: result.score, summary: TennisMenu.shared.postMatch, compact: true)
                }.scrollBounceBehavior(.basedOnSize)
                VStack(spacing: 8) {
                    IslandAction(title: "Rematch", primary: true, compact: true, identifier: "postGameReplay") { session.advanceAfterMatch(.replay) }
                    IslandAction(title: "Leave", compact: true, identifier: "postGameMenu") { session.advanceAfterMatch(.menu) }
                }
            }.padding(compact ? 14 : 24)
                .background(IslandUI.paper, in: RoundedRectangle(cornerRadius: 24))
        }
    }
}


/// The TV repeats the action on the phone; the court stays paused beneath this native banner.
struct OnlineTennisTVSetup: View {
    let session: SportsSession
    var service: MultiplayerService = .shared
    var body: some View {
        TimelineView(.periodic(from: .now, by: 0.1)) { _ in
            HStack(spacing: 20) {
                Image(systemName: session.setupStage == .scan ? "iphone.rear.camera" : "checkmark.circle.fill")
                    .font(.system(size: 32)).foregroundStyle(IslandUI.lime)
                VStack(alignment: .leading, spacing: 6) {
                    Text(title).font(IslandUI.font(26, bold: true))
                    Text(instruction).font(IslandUI.font(18, bold: true))
                }
            }.foregroundStyle(.white).padding(20)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(IslandUI.navy, in: RoundedRectangle(cornerRadius: 20))
        }
    }
    private var title: String {
        if let count = service.startCountdown { return "Starting in \(count)" }
        switch session.setupStage {
        case .scan: return "Set your racket direction"
        case .timing: return "Timing check"
        case .ready: return "Direction set"
        default: return "You're ready"
        }
    }
    private var instruction: String {
        switch session.setupStage {
        case .scan: return "Point the back of your phone at this TV. Hold still for one second."
        case .timing: return "Start the timing check on your phone, then swing with the bouncing ball."
        case .ready: return "Stand where you'll play. Tap Ready on your phone."
        default: return service.startCountdown == nil ? "Each player finishes setup on their own phone." : "Stay at your spot and get ready to play."
        }
    }
}

/// Each player sets up independently, including while either court is still loading.
struct OnlineTennisSetupPanel: View {
    @Bindable var session: SportsSession
    var service: MultiplayerService = .shared
    @State private var scanStarted = Date()

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                Text("SET UP YOUR RACKET").font(IslandUI.font(13, bold: true)).tracking(2).foregroundStyle(IslandUI.lime)
                // Solo's own screens, in solo's order (2026-10-28): the court scan, the TV's delay, the timing check, Ready. Only a
                // player coming back into a match already being played gets the quick scan and Ready below, then the countdown.
                if session.setupStage == .scan && !session.onlineComeback {
                    AxisGatePanel(session: session)
                } else if session.setupStage == .scan {
                    direction
                } else if session.measuringDelay {
                    DelayProbePanel(session: session)
                } else if session.timingPrompt {
                    TimingCheckPrompt(session: session)
                } else if session.checkingTiming {
                    TimingCheckPanel(countdownEnds: session.timingCountdownEnds)
                } else if session.setupStage == .ready && !session.onlineComeback {
                    ControllerReadyPanel(session: session)
                } else if session.setupStage == .ready {
                    Image(systemName: "checkmark.circle.fill").font(.system(size: 64)).foregroundStyle(IslandUI.lime)
                    Text("Direction set").font(IslandUI.font(30, bold: true))
                    Text("Stand where you'll play. Tap Ready, then watch the TV.").multilineTextAlignment(.center)
                    ControllerButton(title: "Ready", icon: "play.fill") { session.readyToPlay() }
                        .accessibilityIdentifier("controller-ready")
                    if !session.setupProblem.isEmpty {
                        Text(session.setupProblem).font(.subheadline).multilineTextAlignment(.center)
                            .accessibilityIdentifier("controller-ready-status")
                    }
                    Button("Set direction again") { scanStarted = Date(); session.retryCourtDirection() }
                        .frame(minHeight: 44).tint(IslandUI.lime)
                } else {
                    TimelineView(.periodic(from: .now, by: 0.1)) { _ in
                        if let count = service.startCountdown {
                            Text("\(count)").font(IslandUI.font(80, bold: true)).monospacedDigit().foregroundStyle(IslandUI.lime)
                                .accessibilityIdentifier("online-start-countdown")
                            Text("Watch your TV").font(IslandUI.font(28, bold: true))
                        } else {
                            Image(systemName: "checkmark.circle.fill").font(.system(size: 64)).foregroundStyle(IslandUI.lime)
                            Text("You're ready").font(IslandUI.font(30, bold: true))
                            Text("Stay at your spot. We'll count you in when both players are ready.").multilineTextAlignment(.center)
                        }
                    }
                }
                players
                recovery
            }
            .frame(maxWidth: .infinity).padding(.vertical, 24)
        }
        .accessibilityIdentifier("online-tennis-setup")
    }

    private var direction: some View {
        VStack(spacing: 20) {
            HStack(spacing: 24) {
                Image(systemName: "iphone.rear.camera").font(.system(size: 52))
                Image(systemName: "arrow.right").font(.title2)
                Image(systemName: "tv").font(.system(size: 52))
            }.foregroundStyle(IslandUI.lime).accessibilityHidden(true)
            Text("Set your direction").font(IslandUI.font(30, bold: true))
            Text("Point the back of your phone at your TV. Hold still for one second.")
                .multilineTextAlignment(.center)
            ZStack {
                Circle().stroke(.white.opacity(0.15), lineWidth: 8)
                Circle().trim(from: 0, to: max(0, min(1, session.axisGate.progress)))
                    .stroke(IslandUI.lime, style: StrokeStyle(lineWidth: 8, lineCap: .round)).rotationEffect(.degrees(-90))
                Image(systemName: "scope").font(.system(size: 32)).foregroundStyle(IslandUI.lime)
            }.frame(width: 96, height: 96)
                .accessibilityLabel("Direction hold progress").accessibilityValue("\(Int(session.axisGate.progress * 100)) percent")
            Text(session.axisGate.message).font(.subheadline).multilineTextAlignment(.center)
            Text("Leave enough space to swing. Keep your rear camera uncovered.")
                .font(.footnote).foregroundStyle(.white.opacity(0.7)).multilineTextAlignment(.center)
            TimelineView(.periodic(from: .now, by: 0.25)) { context in
                if context.date.timeIntervalSince(scanStarted) >= 4 || session.axisGate.stalledFor >= 4 || !session.setupProblem.isEmpty {
                    VStack(spacing: 16) {
                        if !session.setupProblem.isEmpty { Text(session.setupProblem).font(.subheadline).multilineTextAlignment(.center) }
                        Button("Use this direction") { session.useCurrentDirection() }
                            .accessibilityIdentifier("forceAxis")
                        Button("Try again") { scanStarted = Date(); session.retryCourtDirection() }
                            .accessibilityIdentifier("retryAxis")
                    }.tint(IslandUI.lime).buttonStyle(.bordered).controlSize(.large)
                }
            }
        }
    }

    private var players: some View {
        VStack(spacing: 12) {
            ForEach(service.lobby?.participants.filter { $0.seat >= 0 } ?? [], id: \.id) { player in
                let local = player.id == service.localID
                let calibrated = local ? session.setupStage == .waiting : player.calibrated
                HStack(spacing: 12) {
                    Image(systemName: calibrated ? "checkmark.circle.fill" : "circle.dotted")
                        .foregroundStyle(calibrated ? IslandUI.lime : .white.opacity(0.6))
                    Text(local ? "You" : player.name).fontWeight(.semibold).lineLimit(2)
                    Spacer(minLength: 8)
                    Text(playerStatus(player, local: local, calibrated: calibrated))
                        .font(.subheadline).foregroundStyle(.white.opacity(0.8)).multilineTextAlignment(.trailing)
                }
            }
        }.padding(16).background(.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 20))
    }

    private func playerStatus(_ player: MultiplayerParticipant, local: Bool, calibrated: Bool) -> String {
        if !player.connected { return "Reconnecting" }
        if calibrated { return player.loaded ? "Ready" : "Ready · Court loading" }
        if local { return session.setupStage == .ready ? "Tap Ready" : session.setupStage == .timing ? "Checking timing" : "Setting direction" }
        if player.setupStep == "ready" { return "About to tap Ready" }
        if player.setupStep == "timing" { return "Checking timing" }
        if player.setupStep == "direction" { return "Setting direction" }
        return player.loaded ? "Setting up racket" : "Loading court"
    }

    @ViewBuilder private var recovery: some View {
        if service.lobby?.phase == .calibrating,
           service.lobby?.competitors.allSatisfy({ $0.calibrated }) == true {
            Text("Checking the connection…").font(.subheadline)
        }
        if let error = service.lastError { Text(error).font(.subheadline).multilineTextAlignment(.center) }
        if service.isOwner && service.linkNeedsDecision {
            ControllerButton(title: "Play anyway", icon: "play.fill") { service.playAnyway() }
        }
        if service.loadingNeedsDecision || session.loading.isStalled {
            Text("The court is taking longer to load. Your racket setup is saved.").font(.subheadline).multilineTextAlignment(.center)
            Button("Keep waiting") { try? service.keepWaitingForLoad(); session.loading.keepWaiting() }
                .buttonStyle(.bordered).controlSize(.large).tint(IslandUI.lime)
        }
        Button("Leave game") { session.exitGame() }.font(.subheadline).tint(.white.opacity(0.75))
            .frame(minHeight: 44).accessibilityIdentifier("setup-leave")
    }
}

struct ControllerReadyPanel: View {
    let session: SportsSession
    private var skin: MapSkin { .current }
    var body: some View {
        ScrollView {
            // (a player coming back into a match being played skips the timing check: Ready is their second step)
            MapSetupCard(skin: skin, name: MapSkin.playerName(session), title: "Ready to play") {
                Image(systemName: "checkmark.seal.fill").font(.system(size: 60, weight: .bold)).foregroundStyle(skin.accentDeep)
                    .accessibilityLabel("Step \(session.onlineComeback ? 2 : 3)")
                if !session.timingNote.isEmpty { Text(session.timingNote).font(MapFont.semi(15)).multilineTextAlignment(.center) }
                if !session.delayTip.isEmpty { Text(session.delayTip).font(MapFont.semi(13)).multilineTextAlignment(.center).opacity(0.8) }
                Text("Watch the TV.\nYour phone stays your controller.").font(MapFont.bold(19)).multilineTextAlignment(.center)
                ControllerButton(title: "Ready to play", icon: "play.fill") { session.readyToPlay() }
                    .accessibilityIdentifier("controller-ready")
                // When Ready cannot be taken (no camera frame yet, tracking lost) the reason lands in `status`. Online, this panel is the only
                // thing standing between the player and the match, and the other player is waiting, so say why instead of doing nothing.
                if session.multiplayerMatchID != nil, !session.status.isEmpty {
                    Text(session.status).font(MapFont.semi(13)).multilineTextAlignment(.center).opacity(0.85)
                        .accessibilityIdentifier("controller-ready-status")
                }
            }
            .padding(.top, 8)
        }
        .scrollIndicators(.hidden)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

/// Play → Calibration: the lesson card on the phone. The TV shows the target ring and the ball; this says which shot to hit and how far
/// along the lesson is. Twelve takes learn the player's racket angles, twelve more check them.
struct CalibrationPanel: View {
    @Bindable var session: SportsSession
    private var lesson: TennisAimLesson? { session.aimLesson }
    private var complete: Bool { session.calibrationComplete }
    private func laneWord(_ lane: Int) -> String { lane < 0 ? "LEFT" : lane > 0 ? "RIGHT" : "STRAIGHT" }
    private func laneIcon(_ lane: Int) -> String { lane < 0 ? "arrow.left" : lane > 0 ? "arrow.right" : "arrow.up" }
    var body: some View {
        VStack(spacing: 16) {
            Spacer()
            if let lesson {
                Text(complete ? "AIMING READY" : lesson.progress.uppercased())
                    .font(IslandUI.font(13, bold: true)).tracking(2).foregroundStyle(IslandUI.lime)
                if complete {
                    Image(systemName: "checkmark.circle.fill").font(.system(size: 72)).foregroundStyle(IslandUI.lime)
                } else if let trial = lesson.current {
                    Image(systemName: laneIcon(trial.lane)).font(.system(size: 72, weight: .bold)).foregroundStyle(IslandUI.lime)
                    Text("\(trial.wing == 0 ? "Forehand" : "Backhand") · \(laneWord(trial.lane))").font(IslandUI.font(30, bold: true))
                    // the lesson only accepts the grip it asked for (TennisAimLesson.record), so say how to hold it
                    Text(trial.wing == 0 ? "Forehand: the screen faces the TV as you swing" : "Backhand: the back of the phone faces the TV as you swing")
                        .font(.footnote.weight(.semibold)).multilineTextAlignment(.center).foregroundStyle(.white.opacity(0.85)).padding(.horizontal, 24)
                        .accessibilityIdentifier("calibration-grip")
                }
                ProgressView(value: Double(min(lesson.index, lesson.trials.count)), total: Double(max(lesson.trials.count, 1)))
                    .tint(IslandUI.lime).padding(.horizontal, 40)
                Text(session.aimLessonMessage).font(IslandUI.font(16, bold: true)).multilineTextAlignment(.center).padding(.horizontal, 20)
                    .accessibilityIdentifier("calibration-message")
                if !complete {
                    Text("Watch the TV and swing toward the ring. The direction you swing aims, not where the phone points.")
                        .font(.footnote).multilineTextAlignment(.center).foregroundStyle(.white.opacity(0.75)).padding(.horizontal, 24)
                }
            } else {
                ProgressView().tint(.white)
                Text("Starting calibration…").font(IslandUI.font(20, bold: true))
            }
            ControllerButton(title: complete ? "Done" : "Stop", icon: complete ? "checkmark" : "xmark") { session.finishCalibration() }
                .accessibilityIdentifier("calibration-done")
            Button("Start over") { session.restartCalibration() }
                .frame(minHeight: 44).tint(IslandUI.lime).accessibilityIdentifier("calibration-restart")
            Spacer()
        }.frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

/// Online tennis: this player is set up. The match starts when the other player is too.
struct WaitingForPlayersPanel: View {
    private var waitingFor: String {
        let lobby = MultiplayerService.shared.lobby, competitors = lobby?.competitors ?? []
        let names = competitors.filter { !$0.calibrated }.map(\.name)
        if !names.isEmpty { return names.joined(separator: " and ") }
        // Everyone is set up: the owner is still checking that every guest's connection is steady.
        if competitors.contains(where: { !$0.linkOK && $0.id != lobby?.ownerID }) { return "a steady connection" }
        return "the match to start"
    }
    var body: some View {
        VStack {
            Spacer(minLength: 0)
            MapSetupCard(skin: .current, name: MapSkin.playerName(.shared), title: "You're ready") {
                ProgressView().controlSize(.large).tint(MapSkin.current.accentDeep)
                Text("Waiting for \(waitingFor)…").font(MapFont.bold(18)).multilineTextAlignment(.center)
                Text("Stay at your spot and watch the TV. The match starts as soon as everyone is set.")
                    .font(MapFont.semi(14)).multilineTextAlignment(.center).opacity(0.85)
            }
            Spacer(minLength: 0)
        }.frame(maxWidth: .infinity, maxHeight: .infinity)
            .accessibilityElement(children: .combine).accessibilityIdentifier("controller-waiting")
    }
}
