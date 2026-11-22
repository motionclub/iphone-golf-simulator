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
            } else if session.pointsWhileLoading {
                // T4: point at the TV while the court loads (it is motion only), the loading bar under the card
                PointWhileLoadingPanel(session: session)
            } else if !session.ready || !session.loading.finished {
                // The same loading screen as the TV: tips, how-to cards, the flowing bar.
                LoadingScreen(menu: .shared, compact: true).padding(-24)
            } else if [.scan, .timing, .ready, .waiting].contains(session.setupStage) {
                TennisSetupFlow(session: session)
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
        .sheet(isPresented: Binding(get: { showOptions || (session.menuPauseVisible && session.active) }, set: { if !$0 { showOptions = false } })) {
            GamePauseMenu(session: session) { showOptions = false }
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
struct DelayProbePanel: View {
    let session: SportsSession
    @State private var pulse = false
    private var skin: MapSkin { .current }
    var body: some View {
        ScrollView {
            MapSetupCard(skin: skin, name: MapSkin.playerName(session), title: "Get ready for flashes", showsMap: false) {
                PointAtTVMark(skin: skin).frame(height: 78).scaleEffect(pulse ? 1.03 : 0.97)
                Text("Keep your phone pointed at the TV.").font(MapFont.bold(20)).multilineTextAlignment(.center)
                Text("The TV flashes a few times so the game knows how late its picture is.")
                    .font(MapFont.semi(15)).multilineTextAlignment(.center).opacity(0.85)
                ProgressView().tint(skin.accentDeep)
            }
            .padding(.top, 8)
        }
        .scrollIndicators(.hidden)
        .onAppear { withAnimation(.easeInOut(duration: 0.5).repeatForever(autoreverses: true)) { pulse = true } }
    }
}

/// Offered the first time on a TV: what the timing check is for, and a button to start it (board 13 screen 2: Timing check).
struct TimingCheckPrompt: View {
    let session: SportsSession
    private var skin: MapSkin { .current }
    var body: some View {
        ScrollView {
            MapSetupCard(skin: skin, name: MapSkin.playerName(session), title: "Timing check", showsMap: false) {
                BounceMark(skin: skin).frame(height: 96)
                Text("Swing on every bounce.").font(MapFont.bold(20)).multilineTextAlignment(.center)
                Text(session.sharesTV ? "Watch the ball on the TV and swing each time it lands on the line. Everyone does it together."
                     : "Watch the ball on the TV and swing each time it lands on the line.")
                    .font(MapFont.semi(15)).multilineTextAlignment(.center).opacity(0.85)
                ControllerButton(title: "Start timing check", icon: "play.fill", height: 60, size: 21) { session.startTimingCheck() }.accessibilityIdentifier("timing-start")
                MapQuietButton(skin: skin, title: "Skip for now") { session.skipTimingCheck() }.accessibilityIdentifier("timing-skip")
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
struct TimingCheckPanel: View {
    let countdownEnds: Date?
    private var skin: MapSkin { .current }
    var body: some View {
        TimelineView(.periodic(from: .now, by: 0.2)) { context in
            let left = countdownEnds.map { max(0, $0.timeIntervalSince(context.date)) } ?? 0
            VStack {
                Spacer(minLength: 0)
                MapSetupCard(skin: skin, name: MapSkin.playerName(.shared), title: left > 0 ? "Get ready" : "Swing on every bounce!", showsMap: false) {
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

/// Shared by the regular controller, classic controller and landscape Unity overlay: the post-game, stepped from here while the TV
/// shows it (PostGameTV). Tennis once Unity confirms the match is over; golf and bowling once their final sheet is in.
/// Never exposes an advance action before then.
struct MatchFinishControls: View {
    @Bindable var session: SportsSession
    var compact = false
    private var skin: MapSkin { .current }
    private var won: Bool? {
        if let result = session.finishedMatch { return result.won }
        if session.postGameStage != nil, let board = session.postGameBoard { return board.mineWon }
        return nil
    }
    var body: some View {
        if let won {
            VStack {
                Spacer(minLength: 0)
                MapSetupCard(skin: skin, name: MapSkin.playerName(session), title: title(won)) {
                    content(won)
                }
                Spacer(minLength: 0)
            }
            .padding(compact ? 12 : 20)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(MapControllerBackground(skin: skin).ignoresSafeArea())
            .accessibilityIdentifier("post-game")
        }
    }
    private var stage: SportsSession.PostGameStage { session.postGameStage ?? .again }
    private var golf: Bool { session.sport == "golf" && session.postGameBoard != nil }
    private var solo: Bool { session.postGameBoard?.solo ?? false }
    private func title(_ won: Bool) -> String {
        switch stage {
        case .victory: return solo ? (session.sport == "golf" ? "Round complete" : "Game complete") : won ? "You win!" : "Good game"
        case .results: return session.sport == "golf" ? "Round complete" : session.sport == "bowling" ? "Game complete" : "Match complete"
        case .scorecard: return "Scorecard"
        case .xp: return "XP earned"
        case .again: return "Play again?"
        }
    }
    @ViewBuilder private func content(_ won: Bool) -> some View {
        switch stage {
        case .victory, .results, .scorecard:
            Image(systemName: won ? "trophy.fill" : "flag.checkered").font(.system(size: 52, weight: .bold)).foregroundStyle(skin.accentDeep)
            Text("Watch the TV.").font(MapFont.bold(19))
            // a golf or bowling game with friends ends on the standings: the party's panel takes over from here
            if !(session.multiplayerMatchID != nil && session.sport != "tennis" && stage != .victory) {
                ControllerButton(title: stage == .victory ? "Results" : "Continue", icon: "chevron.right", height: 60, size: 21) { session.advancePostGame() }
                    .accessibilityIdentifier("postGameContinue")
            }
            if golf && stage != .victory {
                MapQuietButton(skin: skin, title: stage == .scorecard ? "Back" : "Scorecard") { session.togglePostGameScorecard() }
                    .accessibilityIdentifier("postGameScorecard")
            }
            if session.multiplayerMatchID != nil, stage != .victory {
                if session.sport == "tennis" { choices }
                else { MapQuietButton(skin: skin, title: "Leave game") { session.exitGame() }.accessibilityIdentifier("postGameLeave") }
            }
        case .xp:
            Text("+\(TennisMenu.shared.postMatch?.total ?? 0) XP").font(MapFont.bold(40)).foregroundStyle(skin.accentDeep)
            ControllerButton(title: "Continue", icon: "chevron.right", height: 60, size: 21) { session.advancePostGame() }
                .accessibilityIdentifier("postGameContinue")
        case .again:
            choices
        }
    }
    @ViewBuilder private var choices: some View {
        let list = session.postGameChoices
        ForEach(list.indices, id: \.self) { i in
            if i == 0 {
                ControllerButton(title: list[i].title, icon: "play.fill", height: 60, size: 21) { session.choosePostGame(i) }
                    .accessibilityIdentifier(list[i].after == .replay ? "postGameReplay" : "postGame-\(list[i].id)")
            } else {
                MapQuietButton(skin: skin, title: list[i].title) { session.choosePostGame(i) }
                    .accessibilityIdentifier(list[i].after == .menu ? "postGameMenu" : "postGame-\(list[i].id)")
            }
        }
    }
}

/// Each player sets up independently, including while either court is still loading.
struct OnlineTennisSetupPanel: View {
    @Bindable var session: SportsSession
    var service: MultiplayerService = .shared
    private var skin: MapSkin { .current }

    var body: some View {
        ScrollView {
            VStack(spacing: 14) {
                TennisSetupFlow(session: session)
                SetupPlayersStrip(session: session, service: service)
                recovery
            }
            .frame(maxWidth: .infinity)
        }
        .scrollIndicators(.hidden)
        .scrollDisabled(session.setupStage == .scan)   // a hold must not turn into a scroll
        .accessibilityIdentifier("online-tennis-setup")
    }

    @ViewBuilder private var recovery: some View {
        if let error = service.lastError { Text(error).font(MapFont.semi(14)).multilineTextAlignment(.center).foregroundStyle(skin.cream) }
        if service.loadingNeedsDecision || session.loading.isStalled {
            Text("The court is taking longer to load.").font(MapFont.semi(14)).multilineTextAlignment(.center).foregroundStyle(skin.cream)
            MapQuietButton(skin: skin, title: "Keep waiting") { try? service.keepWaitingForLoad(); session.loading.keepWaiting() }
        }
        Button("Leave game") { session.exitGame() }.font(MapFont.semi(15)).foregroundStyle(skin.cream.opacity(0.8))
            .frame(minHeight: 44).accessibilityIdentifier("setup-leave")
    }
}

/// The tennis setup on the phone, solo and online alike: point and hold → the TV's flashes → the timing check → Ready.
/// Every step is one card (board 13) with one thing to do.
struct TennisSetupFlow: View {
    @Bindable var session: SportsSession
    var service: MultiplayerService = .shared
    var body: some View {
        VStack {
            Spacer(minLength: 0)
            if session.multiplayerMatchID != nil, let count = service.startCountdown {
                StartCountdownPanel(session: session, count: count)
            } else if session.calibrationExplain {
                CalibrationExplainPanel(session: session)
            } else if session.setupStage == .scan {
                PointHoldPanel(session: session)
            } else if let step = session.calibrationStep {
                switch step {
                case .waitingToPoint, .waitingForTV: CalibrationWaitPanel(session: session)
                case .flashes: DelayProbePanel(session: session)
                case .prompt: TimingCheckPrompt(session: session)
                case .startWaiting: TimingStartWaitPanel(session: session)
                case .drill: TimingCheckPanel(countdownEnds: session.timingCountdownEnds)
                }
            } else if session.setupStage == .ready {
                ControllerReadyPanel(session: session)
            } else if session.setupStage == .waiting {
                WaitingForPlayersPanel()
            }
            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity)
    }
}

/// Pointed at the TV; the TV is not calibrating yet (another player is still pointing) or is calibrating on the other phone.
struct CalibrationWaitPanel: View {
    let session: SportsSession
    private var skin: MapSkin { .current }
    private var line: String {
        if let first = session.playersStillPointing.first, session.ownsTV { return "Waiting for \(first.name) to point at the TV." }
        return "The TV is calibrating. Keep your phone pointed at it."
    }
    var body: some View {
        MapSetupCard(skin: skin, name: MapSkin.playerName(session), title: session.ownsTV ? "Pointed at the TV" : "Calibrating the TV", showsMap: false) {
            Image(systemName: "checkmark.circle.fill").font(.system(size: 54, weight: .bold)).foregroundStyle(skin.accentDeep)
            Text(line).font(MapFont.bold(19)).multilineTextAlignment(.center)
            ProgressView().tint(skin.accentDeep)
        }
        .accessibilityIdentifier("calibration-wait")
    }
}

/// Shared TV: this player tapped Start; the ball starts when everyone has.
struct TimingStartWaitPanel: View {
    let session: SportsSession
    var service: MultiplayerService = .shared
    private var skin: MapSkin { .current }
    private var waitingFor: String {
        let names = (service.lobby?.competitors ?? []).filter { p in
            p.id != service.localID && p.connected && !p.calibrated && !(p.setupStep ?? "").hasPrefix("go:") && p.setupStep != "ready" && p.setupStep != "quick"
        }.map(\.name)
        return names.isEmpty ? "Starting…" : "Waiting for \(names.joined(separator: " and ")) to tap Start."
    }
    var body: some View {
        MapSetupCard(skin: skin, name: MapSkin.playerName(session), title: "Timing check", showsMap: false) {
            ProgressView().controlSize(.large).tint(skin.accentDeep)
            Text(waitingFor).font(MapFont.bold(19)).multilineTextAlignment(.center)
            Text("Then watch the ball on the TV and swing each time it lands on the line.")
                .font(MapFont.semi(15)).multilineTextAlignment(.center).opacity(0.85)
            MapQuietButton(skin: skin, title: "Skip for now") { session.skipTimingCheck() }.accessibilityIdentifier("timing-skip")
        }
        .accessibilityIdentifier("timing-start-wait")
    }
}

/// Everyone is set: the match starts on the TV.
struct StartCountdownPanel: View {
    let session: SportsSession
    let count: Int
    private var skin: MapSkin { .current }
    var body: some View {
        MapSetupCard(skin: skin, name: MapSkin.playerName(session), title: "Get ready", showsMap: false) {
            Text("\(count)").font(MapFont.bold(96)).foregroundStyle(skin.accentDeep).monospacedDigit()
                .accessibilityIdentifier("online-start-countdown")
            Text("Watch your TV.").font(MapFont.bold(19))
        }
    }
}

/// Online: where every player is in the setup, on the map's pills.
struct SetupPlayersStrip: View {
    let session: SportsSession
    var service: MultiplayerService = .shared
    private var skin: MapSkin { .current }
    var body: some View {
        let players = service.lobby?.competitors ?? []
        if players.count > 1 {
            HStack(spacing: 8) {
                ForEach(players, id: \.id) { p in
                    let chip = TennisSetupTVView(session: session, service: service).chipFor(p)
                    HStack(spacing: 10) {
                        Image(systemName: chip.done ? "checkmark.circle.fill" : "circle").foregroundStyle(chip.done ? skin.accentDeep : skin.ink.opacity(0.5))
                        VStack(alignment: .leading, spacing: 0) {
                            Text(p.id == service.localID ? "You" : p.name).font(MapFont.bold(15)).lineLimit(1)
                            Text(chip.text).font(MapFont.semi(12)).opacity(0.8).lineLimit(1)
                        }
                        Spacer(minLength: 0)
                    }
                    .foregroundStyle(skin.ink)
                    .padding(.horizontal, 14).padding(.vertical, 7).frame(maxWidth: .infinity)
                    .background(Capsule().fill(skin.cream)).overlay(Capsule().strokeBorder(skin.frame, lineWidth: 2))
                }
            }
            .accessibilityIdentifier("setup-players")
        }
    }
}

struct ControllerReadyPanel: View {
    let session: SportsSession
    private var skin: MapSkin { .current }
    var body: some View {
        ScrollView {
            // (a player coming back into a match being played skips the timing check: Ready is their second step)
            MapSetupCard(skin: skin, name: MapSkin.playerName(session), title: "Ready to play", showsMap: false) {
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
        return "the match to start"
    }
    var body: some View {
        VStack {
            Spacer(minLength: 0)
            MapSetupCard(skin: .current, name: MapSkin.playerName(.shared), title: "You're ready", showsMap: false) {
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

// MARK: - Point and hold (11-20)

/// The whole tennis setup, solo and online alike: point the back of the phone at the TV and hold the button until the ring is
/// full. No camera window, no blinks to wait for, no timing drill, no turns: anyone can do it, and every player does it at once.
struct PointHoldPanel: View {
    @Bindable var session: SportsSession
    private var skin: MapSkin { .current }
    var body: some View {
        MapSetupCard(skin: skin, name: MapSkin.playerName(session), title: "Point at the TV", showsMap: false) {
            PointAtTVMark(skin: skin).frame(height: 78)
            Text("Point the back of your phone at the TV, then hold the button.")
                .font(MapFont.bold(19)).multilineTextAlignment(.center).fixedSize(horizontal: false, vertical: true)
            PointHoldButton(session: session, skin: skin).padding(.vertical, 4)
            Text(session.pointMessage).font(MapFont.semi(15)).multilineTextAlignment(.center)
                .frame(minHeight: 40).fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("point-message")
            if !session.setupProblem.isEmpty {
                Text(session.setupProblem).font(MapFont.semi(14)).multilineTextAlignment(.center).opacity(0.8)
            }
        }
        .accessibilityIdentifier("point-hold-panel")
    }
}

/// The lesson's first setup card (quick start plan O5): why the setup times the TV, once. Continue, or it moves on by itself.
struct CalibrationExplainPanel: View {
    let session: SportsSession
    private var skin: MapSkin { .current }
    static let title = "Calibrate once"
    static let message = "Your TV shows the picture a moment late. We time it once and remember it for this TV, so your swings land on time."
    var body: some View {
        MapSetupCard(skin: skin, name: MapSkin.playerName(session), title: Self.title, showsMap: false) {
            PointAtTVMark(skin: skin).frame(height: 70)
            Text(Self.message).font(MapFont.bold(18)).multilineTextAlignment(.center).fixedSize(horizontal: false, vertical: true)
            Text("Point at the TV, watch a few flashes, then swing along with a bouncing ball.")
                .font(MapFont.semi(15)).multilineTextAlignment(.center).opacity(0.85).fixedSize(horizontal: false, vertical: true)
            ControllerButton(title: "Continue", icon: "arrow.right") { session.continueCalibrationExplain() }
                .accessibilityIdentifier("calibration-explain-continue")
        }
        .accessibilityIdentifier("calibration-explain")
    }
}

/// Under the loading screen (T4): point at the TV now, so the match is ready to start as soon as the court is.
struct PointWhileLoadingPanel: View {
    @Bindable var session: SportsSession
    private var skin: MapSkin { .current }
    var body: some View {
        VStack(spacing: 12) {
            PointHoldPanel(session: session)
            HStack(spacing: 10) {
                ProgressView().tint(skin.cream)
                Text(session.axisGate.locked ? "Pointed. Loading the court…" : "Loading the court…").font(MapFont.semi(15)).foregroundStyle(skin.cream)
            }
            .accessibilityIdentifier("point-while-loading-status")
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .accessibilityIdentifier("point-while-loading")
    }
}

/// A TV with the phone's back aimed at it.
struct PointAtTVMark: View {
    let skin: MapSkin
    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: "tv").font(.system(size: 54, weight: .semibold))
            Image(systemName: "ellipsis").font(.system(size: 22, weight: .heavy)).opacity(0.6)
            Image(systemName: "iphone.gen3").font(.system(size: 50, weight: .semibold)).rotationEffect(.degrees(-12))
        }
        .foregroundStyle(skin.ink)
        .accessibilityHidden(true)
    }
}

/// The big round button: down starts the hold, up ends it. The ring fills while the phone is held still at the TV.
struct PointHoldButton: View {
    @Bindable var session: SportsSession
    let skin: MapSkin
    var size: CGFloat = 150
    /// Down while a finger is on the button. A gesture state resets itself when the touch is taken away (a scroll, a system
    /// gesture), so a hold can never stay down without a finger.
    @GestureState private var pressed = false
    var body: some View {
        let done = session.axisGate.locked
        ZStack {
            Circle().fill(skin.ink.opacity(0.12))
            Circle().trim(from: 0, to: session.pointProgress)
                .stroke(skin.accent, style: StrokeStyle(lineWidth: 14, lineCap: .round)).rotationEffect(.degrees(-90))
                .animation(.linear(duration: 0.08), value: session.pointProgress)
            Circle().fill(done ? skin.accent : skin.accentDeep).padding(20)
                .overlay {
                    if done {
                        Image(systemName: "checkmark").font(.system(size: 48, weight: .heavy)).foregroundStyle(skin.accentInk)
                    } else {
                        Text(session.holdingPoint ? "HOLD…" : "HOLD").font(MapFont.bold(30)).foregroundStyle(skin.accentInk)
                    }
                }
                .scaleEffect(pressed ? 0.94 : 1).animation(.easeOut(duration: 0.12), value: pressed)
        }
        .frame(width: size, height: size)
        .contentShape(Circle())
        .gesture(DragGesture(minimumDistance: 0).updating($pressed) { _, down, _ in down = true })
        .onChange(of: pressed) { _, down in if down { session.pressPoint() } else { session.releasePoint() } }
        .onDisappear { session.releasePoint() }
        .accessibilityElement()
        .accessibilityLabel("Hold to point at the TV")
        .accessibilityValue("\(Int(session.pointProgress * 100)) percent")
        .accessibilityAddTraits(.isButton)
        .accessibilityAction { session.pointNow() }
        .accessibilityIdentifier("point-hold")
    }
}

/// Phone casting (PLAN_PhoneCasting_GolfBowling.md): over the screen phone's game. The game fills the screen sideways under it, like a
/// TV, so this is see-through and offers only Leave (the players play from their own phones; touch gameplay stays removed).
struct CastScreenOverlay: View {
    let session: SportsSession
    @State private var leaving = false
    var body: some View {
        Color.clear.ignoresSafeArea()
            .overlay(alignment: .topTrailing) {
                Button { leaving = true } label: {
                    Image(systemName: "xmark").font(.system(size: 15, weight: .bold)).foregroundStyle(.white)
                        .frame(width: 40, height: 40).background(.black.opacity(0.35), in: Circle())
                }
                .buttonStyle(.plain).padding(12).accessibilityLabel("Leave game").accessibilityIdentifier("cast-screen-leave")
            }
            .confirmationDialog("End the game for everyone?", isPresented: $leaving, titleVisibility: .visible) {
                Button("End game", role: .destructive) { session.exitGame() }
                Button("Keep playing", role: .cancel) {}
            } message: { Text("This phone is the screen: the game stops on every player's phone too.") }
            .accessibilityIdentifier("cast-screen")
    }
}

/// Phone casting, on a player's phone: the screen phone is away. The game waits for it (up to the away limit) and goes on when it is back.
struct CastScreenAwayBanner: View {
    var body: some View {
        HStack(spacing: 10) {
            ProgressView().tint(IslandUI.lime)
            VStack(alignment: .leading, spacing: 2) {
                Text("Waiting for the screen phone").font(IslandUI.font(16, bold: true))
                Text("The game goes on as soon as it's back. Keep the screen phone in the app.").font(IslandUI.font(13)).foregroundStyle(.white.opacity(0.75))
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer(minLength: 0)
        }
        .foregroundStyle(.white).padding(14)
        .background(IslandUI.dark.opacity(0.96), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(IslandUI.lime.opacity(0.7), lineWidth: 2))
        .accessibilityElement(children: .combine).accessibilityIdentifier("cast-screen-away")
    }
}
