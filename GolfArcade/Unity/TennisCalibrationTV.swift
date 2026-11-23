import SwiftUI
import UIKit

// MARK: - Tennis calibration on the TV (ArtDir/ui/tv-results-calibration, 2026-11-20)
//
// What the TV shows while the players set up, drawn by the app in its own window over the game (SportsDisplays.showTennisSetupOnTV):
// point at the TV (scan banner and reticle) → "Get ready for flashes" → the flashes (nothing over them) → "TV latency" → the timing
// drill (the ball dropping onto the line, recorded-swing pips) → "Ready to play". Same steps solo and with friends; with two phones on
// one TV a row of name chips says where each player is. Colours are the map's skin (MapSkin), type is Kanit, sizes are the design's,
// in hundredths of the TV's width (`cq`).

/// The design's colours, from the map's skin (review.css `.tv` tokens).
struct TVCalibrationPalette {
    let skin: MapSkin
    /// Club Lanes' sheets are navy with cream type (review.css `.tv[data-venue="bowling-club"]`); every other map's are light.
    var dark: Bool { skin.id == "bowling-club" }
    var panel: Color { dark ? skin.top : skin.cream.mixed(with: skin.line, 0.55) }
    var panelLight: Color { dark ? skin.surface.mixed(with: skin.top, 0.35) : panel.mixed(with: .white, 0.2) }
    var panelShadow: Color { dark ? skin.bottom : panel.mixed(with: skin.frame, 0.14) }
    var ink: Color { skin.ink }
    /// Type on the panel.
    var panelInk: Color { dark ? skin.cream : skin.ink }
    var inset: Color { dark ? skin.bottom : panel.mixed(with: skin.surface, 0.13) }
    var rule: Color { panel.mixed(with: panelInk, 0.26) }
    var muted: Color { panelInk.mixed(with: panel, 0.18) }
    var trim: Color { skin.frame.mixed(with: skin.accent, 0.45) }
    var meterFill: Color { dark ? skin.accent : skin.accentDeep.mixed(with: skin.ink, 0.38) }
    var meterTrack: Color { panel.mixed(with: panelInk, 0.16) }
    /// A table row, and the winner's.
    var row: Color { dark ? skin.surface.mixed(with: skin.top, 0.15) : panel.mixed(with: .white, 0.28) }
    var rowWinner: Color { dark ? accent.mixed(with: skin.cream, 0.23) : row.mixed(with: accent, 0.32) }
    var winnerInk: Color { accentInk }
    /// The actions' and the winner's colour: Club Lanes' brass on the TV (review.js), where its controller uses cream.
    var accent: Color { dark ? skin.glow : skin.accent }
    var accentDeep: Color { skin.accentDeep }
    var accentInk: Color { skin.accentInk }
}

extension Color {
    /// Light type or paint (relative luminance over 0.5).
    var isLight: Bool {
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        UIColor(self).getRed(&r, green: &g, blue: &b, alpha: &a)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.5
    }
    /// `self` with `t` of `other` mixed in (sRGB).
    func mixed(with other: Color, _ t: Double) -> Color {
        var a = (r: CGFloat(0), g: CGFloat(0), b: CGFloat(0), o: CGFloat(0)), b = a
        UIColor(self).getRed(&a.r, green: &a.g, blue: &a.b, alpha: &a.o)
        UIColor(other).getRed(&b.r, green: &b.g, blue: &b.b, alpha: &b.o)
        let t = CGFloat(t)
        return Color(red: a.r + (b.r - a.r) * t, green: a.g + (b.g - a.g) * t, blue: a.b + (b.b - a.b) * t, opacity: a.o + (b.o - a.o) * t)
    }
}

/// One player's line on the TV while several share it.
struct TVSetupChip: Identifiable, Equatable { let id: String; let name: String; let text: String; let done: Bool; var pips: Int? = nil }

struct TennisSetupTVView: View {
    let session: SportsSession
    var service: MultiplayerService = .shared

    /// What the TV shows now.
    enum Screen: Equatable { case none, explain, scan, warning, latency, drill, ready, starting(Int) }
    var screen: Screen {
        guard session.active, session.sport == "tennis", session.loading.finished, session.finishedMatch == nil,
              !session.menuPauseVisible, !session.tvFlashing else { return .none }
        if session.multiplayerMatchID != nil, let count = service.startCountdown { return .starting(count) }
        if session.calibrationExplain { return .explain }
        switch session.setupStage {
        case .scan: return .scan
        case .timing:
            switch session.calibrationStep {
            case .flashes?: return .warning
            case .prompt?, .startWaiting?: return .latency
            case .drill?: return .drill
            default: return .scan   // pointed, waiting for the others to point
            }
        case .ready, .waiting: return .ready
        default: return .none
        }
    }

    var body: some View {
        // Only the timing drill draws from the clock. The window stays over the game for the whole match (it is where the post-game
        // screens go), so a running 60 Hz timeline re-evaluated this view every frame of play on the main thread (11-22 smoothness audit).
        TimelineView(.animation(minimumInterval: 1.0 / 60, paused: screen != .drill)) { context in
            GeometryReader { g in
                let cq = g.size.width / 100, palette = TVCalibrationPalette(skin: .current)
                ZStack {
                    if let stage = session.postGameStage, session.active, session.finishedMatch != nil || session.postGameBoard != nil {
                        PostGameTV(session: session, service: service, stage: stage, cq: cq, palette: palette)
                    } else {
                        content(screen, cq: cq, palette: palette, now: context.date)
                    }
                }
                .frame(width: g.size.width, height: g.size.height)
            }
        }
        .ignoresSafeArea()
        .allowsHitTesting(false)
    }

    @ViewBuilder private func content(_ screen: Screen, cq: CGFloat, palette: TVCalibrationPalette, now: Date) -> some View {
        let chips = self.chips
        switch screen {
        case .none: Color.clear
        case .explain:
            // the lesson's setup opens on why it times the TV (the phone has the same card and its Continue)
            ZStack {
                Color(hex: "101C3F").opacity(0.6)
                TVSetupCard(cq: cq, palette: palette, width: 56) {
                    Text(CalibrationExplainPanel.title).font(MotionBrand.font(.extraBoldItalic, 4.7 * cq))
                    Text(CalibrationExplainPanel.message).font(MotionBrand.font(.medium, 2.1 * cq)).multilineTextAlignment(.center)
                        .fixedSize(horizontal: false, vertical: true)
                    Text("Point your phone at the TV and hold it there while the circle fills.")
                        .font(MotionBrand.font(.medium, 1.7 * cq)).foregroundStyle(palette.muted).multilineTextAlignment(.center)
                }
            }
        case .scan:
            // point and fill (11-22): the picture around the card glows to SportsGlow's wave, which the phones' cameras read
            ZStack {
                if session.glowActive { TVGlowVeil() }
                VStack(spacing: 1.8 * cq) {
                    TVSetupCard(cq: cq, palette: palette, width: 44, spacing: 0.8) {
                        Text(chips.isEmpty ? "Point at the TV" : "Point at the TV together").font(MotionBrand.font(.extraBoldItalic, 4.1 * cq))
                        Text(chips.isEmpty ? "Hold your phone on the screen until the circle fills." : "The circle fills while every phone is on the screen.")
                            .font(MotionBrand.font(.medium, 1.8 * cq))
                        TVFillRing(progress: session.glowProgress, done: !session.glowActive && session.glowProgress >= 1, cq: cq, palette: palette)
                            .frame(width: 12.5 * cq, height: 12.5 * cq).padding(.vertical, 0.5 * cq)
                        Text(glowFootLine).font(MotionBrand.font(.medium, 1.6 * cq)).foregroundStyle(palette.muted)
                    }
                    if !chips.isEmpty { TVChipRow(chips: chips, cq: cq, palette: palette) }
                }
            }
        case .warning:
            ZStack {
                Color(hex: "101C3F").opacity(0.73)
                TVSetupCard(cq: cq, palette: palette, width: 53) {
                    Text("Get ready for flashes").font(MotionBrand.font(.extraBoldItalic, 4.7 * cq))
                    Text("Keep your phone pointed at the TV.").font(MotionBrand.font(.medium, 2 * cq))
                }
            }
        case .latency:
            ZStack {
                RadialGradient(colors: [Color(hex: "101E4E").opacity(0.4), Color(hex: "142A55").opacity(0.23)], center: .center, startRadius: 0, endRadius: 60 * cq)
                VStack(spacing: 2 * cq) {
                    TVSetupCard(cq: cq, palette: palette, width: 38, spacing: 1) {
                        Text("TV latency").font(MotionBrand.font(.extraBoldItalic, 3.65 * cq))
                        if let lag = session.latencyReading {
                            HStack(alignment: .firstTextBaseline, spacing: 0.6 * cq) {
                                Text("\(Int((lag * 1000).rounded()))").font(MotionBrand.font(.extraBold, 8.2 * cq))
                                Text("ms").font(MotionBrand.font(.extraBold, 3.4 * cq))
                            }.foregroundStyle(palette.skin.accentInk)
                        } else {
                            Text("Your swings will set it").font(MotionBrand.font(.medium, 2 * cq)).foregroundStyle(palette.muted)
                        }
                        TVAction(title: "Start calibration", cq: cq, palette: palette).padding(.top, 0.45 * cq)
                        Text(chips.isEmpty ? "Tap Start on your phone." : "Everyone taps Start on their phone.")
                            .font(MotionBrand.font(.medium, 1.7 * cq)).foregroundStyle(palette.muted)
                    }
                    if !chips.isEmpty { TVChipRow(chips: chips, cq: cq, palette: palette) }
                }
            }
        case .drill:
            TVTimingCard(session: session, cq: cq, palette: palette, now: now, chips: chips)
        case .ready:
            VStack(spacing: 2 * cq) {
                TVSetupCard(cq: cq, palette: palette, width: 47) {
                    Text("Ready to play").font(MotionBrand.font(.extraBoldItalic, 4.05 * cq))
                    Text(readyLine).font(MotionBrand.font(.medium, 2 * cq))
                }
                if !chips.isEmpty { TVChipRow(chips: chips, cq: cq, palette: palette) }
            }
        case .starting(let count):
            TVSetupCard(cq: cq, palette: palette, width: 38) {
                Text("Get ready").font(MotionBrand.font(.extraBoldItalic, 4.05 * cq))
                Text("\(count)").font(MotionBrand.font(.extraBold, 8.2 * cq)).foregroundStyle(palette.skin.accentInk)
            }
        }
    }

    /// Under the circle on the TV.
    private var glowFootLine: String {
        if !session.glowActive, session.glowProgress >= 1 {
            return session.latencyReading.map { "TV delay \(Int(($0 * 1000).rounded())) ms" } ?? "Set"
        }
        if let first = session.playersOffTheTV.first { return "Waiting for \(first.name)…" }
        if !session.glowSeeing { return session.glowProgress > 0 ? "Point back at the screen…" : "Looking for your phone…" }
        return "Hold steady…"
    }

    private var readyLine: String {
        guard session.setupStage == .waiting else { return "Starting…" }
        let waiting = (service.lobby?.competitors ?? []).filter { $0.id != service.localID && !$0.calibrated }.map(\.name)
        return waiting.isEmpty ? "Starting…" : "Waiting for \(waiting.joined(separator: " and "))."
    }

    /// One chip per player when several share this TV (none solo, none with a TV each).
    var chips: [TVSetupChip] {
        guard session.multiplayerMatchID != nil, let lobby = service.lobby, lobby.competitors.contains(where: { $0.view == .split }) else { return [] }
        return lobby.competitors.sorted { ($0.id == service.localID ? 0 : 1, $0.seat) < ($1.id == service.localID ? 0 : 1, $1.seat) }.map { p in
            p.id == service.localID ? localChip(p) : remoteChip(p)
        }
    }
    /// One player's chip (also the phone's players strip).
    func chipFor(_ p: MultiplayerParticipant) -> TVSetupChip { p.id == service.localID ? localChip(p) : remoteChip(p) }
    private func localChip(_ p: MultiplayerParticipant) -> TVSetupChip {
        let swings = session.timingSwings.filter { $0 >= SportsSession.timingWarmUp }.count
        switch session.setupStage {
        case .scan: return .init(id: p.id, name: p.name, text: session.glowSeeing ? "On the TV" : "Point at the TV", done: session.glowSeeing)
        case .timing:
            switch session.calibrationStep {
            case .prompt?: return .init(id: p.id, name: p.name, text: "Tap Start", done: false)
            case .startWaiting?: return .init(id: p.id, name: p.name, text: "Ready to start", done: true)
            case .drill?: return .init(id: p.id, name: p.name, text: "Swinging", done: false, pips: swings)
            default: return .init(id: p.id, name: p.name, text: "Pointed", done: true)
            }
        case .ready: return .init(id: p.id, name: p.name, text: "Ready", done: true)
        default: return .init(id: p.id, name: p.name, text: "Ready", done: true)
        }
    }
    private func remoteChip(_ p: MultiplayerParticipant) -> TVSetupChip {
        let step = p.setupStep ?? ""
        if !p.connected { return .init(id: p.id, name: p.name, text: "Reconnecting", done: false) }
        if p.calibrated { return .init(id: p.id, name: p.name, text: "Ready", done: true) }
        if step == "hold" { return .init(id: p.id, name: p.name, text: "Holding…", done: false) }
        if let seeing = SportsGlowStep.seeing(step) { return .init(id: p.id, name: p.name, text: seeing ? "On the TV" : "Point at the TV", done: seeing) }
        if step == SportsGlowStep.done { return .init(id: p.id, name: p.name, text: "Set", done: true) }
        if step == "pointed" { return .init(id: p.id, name: p.name, text: "Pointed", done: true) }
        if step == "timing" { return .init(id: p.id, name: p.name, text: "Tap Start", done: false) }
        if step.hasPrefix("go:") { return .init(id: p.id, name: p.name, text: "Ready to start", done: true) }
        if step.hasPrefix("check:") { return .init(id: p.id, name: p.name, text: "Swinging", done: false, pips: Int(step.dropFirst(6)) ?? 0) }
        if step == "ready" { return .init(id: p.id, name: p.name, text: "Ready", done: true) }
        if step == "quick" { return .init(id: p.id, name: p.name, text: "Ready", done: true) }
        return .init(id: p.id, name: p.name, text: p.loaded ? "Point at the TV" : "Loading", done: false)
    }
}

/// The design's cream card (review.css `.card`, calibration.css `.setup-card`).
struct TVSetupCard<Content: View>: View {
    let cq: CGFloat
    let palette: TVCalibrationPalette
    var width: CGFloat = 47
    var spacing: CGFloat = 1.1
    @ViewBuilder let content: () -> Content
    var body: some View {
        VStack(spacing: spacing * cq) { content() }
            .multilineTextAlignment(.center).foregroundStyle(palette.ink).lineLimit(1).minimumScaleFactor(0.6)
            .padding(.horizontal, 2.4 * cq).padding(.top, 2.25 * cq).padding(.bottom, 2.55 * cq)
            .frame(width: width * cq)
            .background {
                let shape = RoundedRectangle(cornerRadius: 1.72 * cq, style: .continuous)
                shape.fill(palette.skin.frameDeep).offset(y: 0.54 * cq).shadow(color: .black.opacity(0.4), radius: 1.1 * cq, y: 1.1 * cq)
                shape.fill(LinearGradient(colors: [palette.panelLight, palette.panel, palette.panelShadow], startPoint: .topLeading, endPoint: .bottomTrailing))
                shape.strokeBorder(palette.trim, lineWidth: 0.12 * cq).padding(0.36 * cq)
                shape.strokeBorder(palette.skin.frame, lineWidth: 0.36 * cq)
            }
    }
}

/// The design's primary action (`.action`): shown on the TV, pressed on the phone.
struct TVAction: View {
    let title: String
    let cq: CGFloat
    let palette: TVCalibrationPalette
    /// The design's `.action.quiet` (Scorecard, Back): the panel's colour.
    var quiet = false
    var body: some View {
        HStack(spacing: 0.85 * cq) {
            Text(title)
            Image(systemName: "chevron.right").font(.system(size: 1.3 * cq, weight: .heavy))
        }
        .font(MotionBrand.font(.extraBoldItalic, 1.89 * cq)).foregroundStyle(quiet ? palette.panelInk : palette.accentInk)
        .padding(.horizontal, 1.8 * cq).frame(minWidth: 14.2 * cq, minHeight: 4.4 * cq)
        .background {
            let shape = RoundedRectangle(cornerRadius: 0.86 * cq, style: .continuous)
            if quiet {
                shape.fill(palette.skin.frameDeep).offset(y: 0.32 * cq)
                shape.fill(palette.panel)
            } else {
                shape.fill(palette.accentDeep).offset(y: 0.4 * cq)
                shape.fill(LinearGradient(colors: [palette.accent.mixed(with: .white, 0.15), palette.accent], startPoint: .top, endPoint: .bottom))
            }
            shape.strokeBorder(palette.trim, lineWidth: 0.18 * cq)
        }
    }
}

/// The point-and-fill circle on the TV (SportsGlow): it fills while every phone sharing the TV sees it.
struct TVFillRing: View {
    let progress: Double
    let done: Bool
    let cq: CGFloat
    let palette: TVCalibrationPalette
    var body: some View {
        ZStack {
            Circle().stroke(palette.meterTrack, lineWidth: 1.5 * cq)
            Circle().trim(from: 0, to: max(0, min(1, progress)))
                .stroke(done ? palette.skin.accent : palette.skin.accentDeep, style: StrokeStyle(lineWidth: 1.5 * cq, lineCap: .round))
                .opacity(progress > 0.005 ? 1 : 0)
                .rotationEffect(.degrees(-90))
                .animation(.linear(duration: 0.12), value: progress)
            if done {
                Image(systemName: "checkmark").font(.system(size: 4.6 * cq, weight: .heavy)).foregroundStyle(palette.skin.accentDeep)
            } else {
                Text("\(Int((progress * 100).rounded()))%").font(MotionBrand.font(.extraBold, 3.1 * cq)).monospacedDigit()
            }
        }
    }
}

/// The glow behind the setup card (SportsGlow): a black veil whose opacity follows the wave, set for each frame the TV itself shows
/// (the TV screen's own display link), so the frame on the TV at `targetTimestamp` carries the wave's value for that moment.
struct TVGlowVeil: UIViewRepresentable {
    func makeUIView(context: Context) -> TVGlowVeilView { TVGlowVeilView(frame: .zero) }
    func updateUIView(_ view: TVGlowVeilView, context: Context) {}
}

final class TVGlowVeilView: UIView {
    private var link: CADisplayLink?
    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = .black; isUserInteractionEnabled = false; layer.opacity = Float(SportsGlow.lightest)
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) is unused") }
    override func didMoveToWindow() {
        super.didMoveToWindow()
        link?.invalidate(); link = nil
        guard let screen = window?.windowScene?.screen, let link = screen.displayLink(withTarget: self, selector: #selector(tick(_:))) else { return }
        link.preferredFrameRateRange = CAFrameRateRange(minimum: 30, maximum: 60, preferred: 60)
        link.add(to: .main, forMode: .common)
        self.link = link
    }
    @objc private func tick(_ link: CADisplayLink) {
        CATransaction.begin(); CATransaction.setDisableActions(true)
        layer.opacity = Float(SportsGlow.veil(link.targetTimestamp + SportsGlow.clockOffset))
        CATransaction.commit()
    }
}

/// The scan's four corners.
struct ScanReticle: View {
    let cq: CGFloat
    let color: Color
    var body: some View {
        GeometryReader { g in
            let w = g.size.width, h = g.size.height, l = 3.1 * cq, r = 0.55 * cq
            Path { p in
                for (x, y, dx, dy) in [(0.0, 0.0, 1.0, 1.0), (w, 0, -1, 1), (0, h, 1, -1), (w, h, -1, -1)] {
                    p.move(to: CGPoint(x: x, y: y + dy * l)); p.addLine(to: CGPoint(x: x, y: y + dy * r))
                    p.addQuadCurve(to: CGPoint(x: x + dx * r, y: y), control: CGPoint(x: x, y: y))
                    p.addLine(to: CGPoint(x: x + dx * l, y: y))
                }
            }
            .stroke(color, style: StrokeStyle(lineWidth: 0.35 * cq, lineCap: .round))
            .shadow(color: Color(hex: "142A55").opacity(0.86), radius: 0.23 * cq, y: 0.18 * cq)
        }
    }
}

/// Where each player sharing the TV is.
struct TVChipRow: View {
    let chips: [TVSetupChip]
    let cq: CGFloat
    let palette: TVCalibrationPalette
    var body: some View {
        HStack(spacing: 1.2 * cq) {
            ForEach(chips) { chip in
                HStack(spacing: 0.9 * cq) {
                    Image(systemName: chip.done ? "checkmark.circle.fill" : "circle")
                        .font(.system(size: 2 * cq, weight: .bold)).foregroundStyle(chip.done ? palette.skin.accentDeep : palette.muted)
                    Text(chip.name).font(MotionBrand.font(.extraBoldItalic, 2 * cq)).lineLimit(1)
                    Text(chip.text).font(MotionBrand.font(.medium, 1.7 * cq)).foregroundStyle(palette.muted).lineLimit(1)
                    if let pips = chip.pips { TVPips(count: pips, cq: cq, palette: palette) }
                }
                .foregroundStyle(palette.ink)
                .padding(.horizontal, 1.5 * cq).padding(.vertical, 0.8 * cq)
                .background(Capsule().fill(palette.panel)).overlay(Capsule().strokeBorder(palette.skin.frame, lineWidth: 0.25 * cq))
            }
        }
    }
}

/// The seven recorded-swing pips.
struct TVPips: View {
    let count: Int
    let cq: CGFloat
    let palette: TVCalibrationPalette
    var body: some View {
        HStack(spacing: 0.72 * cq) {
            ForEach(0..<(SportsSession.timingBeats - SportsSession.timingWarmUp), id: \.self) { i in
                Circle().fill(i < count ? palette.meterFill : .clear).overlay(Circle().strokeBorder(palette.meterFill, lineWidth: 1))
                    .frame(width: 1.18 * cq, height: 1.18 * cq)
            }
        }
    }
}

/// The swing drill (calibration.css `.timing-card`): the ball drops onto the line in time with the game's own drill.
struct TVTimingCard: View {
    let session: SportsSession
    let cq: CGFloat
    let palette: TVCalibrationPalette
    let now: Date
    let chips: [TVSetupChip]
    /// Seconds from the end of the countdown (negative while counting down), on the clock Unity's drill runs on.
    private var t: Double {
        if let start = session.timingDrillStart { return SportsRuntime.shared().clock() - start }
        if let ends = session.timingCountdownEnds { return now.timeIntervalSince(ends) }
        return -SportsSession.timingCountdown
    }
    /// TennisBeatCalibration.Height: 0 on the line .. 1 at the top.
    private var height: Double {
        let since = t - SportsSession.timingLeadIn
        if since < 0 { let k = max(0, min(1, 1 + since / SportsSession.timingLeadIn)); return 1 - k * k }
        if since > Double(SportsSession.timingBeats - 1) * SportsSession.timingInterval { return 0 }
        let p = since.truncatingRemainder(dividingBy: SportsSession.timingInterval) / SportsSession.timingInterval
        return 4 * p * (1 - p)
    }
    var body: some View {
        let countdown = t < 0 ? Int(ceil(-t)) : 0
        let mine = session.timingSwings.filter { $0 >= SportsSession.timingWarmUp }.count
        TVSetupCard(cq: cq, palette: palette, width: 58, spacing: 0.85) {
            Text("Swing when the ball hits the line").font(MotionBrand.font(.extraBoldItalic, 3.35 * cq))
            ZStack(alignment: .bottom) {
                RoundedRectangle(cornerRadius: 0.55 * cq).fill(palette.inset)
                    .overlay(RoundedRectangle(cornerRadius: 0.55 * cq).strokeBorder(palette.rule, lineWidth: 1))
                Capsule().fill(palette.skin.surface).frame(height: 0.52 * cq).padding(.horizontal, 1.65 * cq).padding(.bottom, 1.35 * cq)
                Capsule().fill(palette.skin.accent).frame(width: 6.2 * cq, height: 1.05 * cq)
                    .shadow(color: palette.skin.accentDeep, radius: 0, y: 0.19 * cq).padding(.bottom, 1.08 * cq)
                TVBall(cq: cq).padding(.bottom, 1.87 * cq + height * 8.6 * cq)
                if countdown > 0 {
                    Text("\(countdown)").font(MotionBrand.font(.extraBold, 5.8 * cq)).foregroundStyle(palette.skin.surface)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading).padding(.top, 1.2 * cq).padding(.leading, 1.7 * cq)
                }
            }
            .frame(height: 15.8 * cq)
            if chips.isEmpty {
                Text(countdown > 0 ? "Get ready" : "Recorded swings").font(MotionBrand.font(.medium, 1.5 * cq)).foregroundStyle(palette.muted)
                TVPips(count: mine, cq: cq, palette: palette)
            } else {
                Text(countdown > 0 ? "Get ready" : "Recorded swings").font(MotionBrand.font(.medium, 1.5 * cq)).foregroundStyle(palette.muted)
                ForEach(chips) { chip in
                    HStack(spacing: 1 * cq) {
                        Text(chip.name).font(MotionBrand.font(.extraBoldItalic, 1.8 * cq)).frame(width: 14 * cq, alignment: .trailing).lineLimit(1)
                        TVPips(count: chip.pips ?? (chip.done ? SportsSession.timingBeats - SportsSession.timingWarmUp : 0), cq: cq, palette: palette)
                        Spacer(minLength: 0)
                    }.frame(width: 34 * cq)
                }
            }
        }
    }
}

/// The design's tennis ball (calibration.css `.ball`).
struct TVBall: View {
    let cq: CGFloat
    var body: some View {
        Circle()
            .fill(RadialGradient(stops: [.init(color: Color(hex: "F3F7A5"), location: 0), .init(color: Color(hex: "CDE861"), location: 0.35),
                                         .init(color: Color(hex: "9EB92C"), location: 0.68), .init(color: Color(hex: "667827"), location: 1)],
                                 center: UnitPoint(x: 0.29, y: 0.25), startRadius: 0, endRadius: 3 * cq))
            .overlay {
                Ellipse().stroke(Color(hex: "EFF3BE"), lineWidth: 0.16 * cq).frame(width: 2.55 * cq, height: 6.15 * cq)
                    .rotationEffect(.degrees(34)).offset(x: 0.6 * cq, y: -0.6 * cq)
            }
            .clipShape(Circle())
            .frame(width: 4.15 * cq, height: 4.15 * cq)
            .shadow(color: Color(hex: "6D7733").opacity(0.23), radius: 0.6 * cq, y: 0.34 * cq)
    }
}

