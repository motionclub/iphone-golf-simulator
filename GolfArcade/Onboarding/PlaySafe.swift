import SwiftUI

/// Play safe (PLAN_Onboarding_v3, Adnan 2026-11-15: "make sure they understand to not stand too close to the TV, and make sure there
/// are warnings people accept when loading into a game"). Before every lesson, and before the first game of each sport each time
/// the app runs, the phone shows how to stand for that sport and the safety checklist; one
/// tap accepts it (Wii / Ring Fit style, research in work/onboarding-v3/RESEARCH.md). A game held for it waits on its loading screen.
/// The how-to-play animation is not here: it plays in game, on the lesson's first step (HowToGIF).
@MainActor @Observable
final class PlaySafeGate {
    static let shared = PlaySafeGate()

    struct Request: Identifiable {
        let id = UUID()
        let sport: Sport
        /// A Tutorial lesson (its how-to-play is the point) rather than the safety reminder before a game.
        let tutorial: Bool
        /// A game is loaded behind it and waits for the accept.
        let holding: Bool
        let onAccept: @MainActor () -> Void
        /// Tennis with no TV in the Tutorial: put the lesson off.
        let onDefer: (@MainActor () -> Void)?
    }
    private(set) var request: Request?
    /// Sports whose card was accepted since the app started (a second game of the same sport goes straight in).
    private(set) var accepted: Set<Sport> = []

    /// A Tutorial lesson's card (always shown).
    func present(sport: Sport, tutorial: Bool, onAccept: @escaping @MainActor () -> Void, onDefer: (@MainActor () -> Void)? = nil) {
        request = Request(sport: sport, tutorial: tutorial, holding: false, onAccept: onAccept, onDefer: onDefer)
        Analytics.track("playsafe_show", ["sport": sport.rawValue, "tutorial": String(tutorial)])
        HubSession.shared.evaluate()
    }
    /// SportsSession.loadingFinished: the first game of a sport this run waits for the card. True = held (call `then` on accept).
    func hold(sport name: String, then: @escaping @MainActor () -> Void) -> Bool {
        guard let sport = Sport(rawValue: name), sport.playable, !accepted.contains(sport) else { return false }
        if let r = request, r.holding { return true }
        request = Request(sport: sport, tutorial: false, holding: true, onAccept: then, onDefer: nil)
        Analytics.track("playsafe_show", ["sport": sport.rawValue, "tutorial": "false"])
        return true
    }
    func needsCard(_ sport: Sport) -> Bool { !accepted.contains(sport) }
    func accept() {
        guard let r = request else { return }
        accepted.insert(r.sport); request = nil
        Analytics.track("playsafe_accept", ["sport": r.sport.rawValue])
        r.onAccept()
        HubSession.shared.evaluate()
    }
    /// Not now: a held game is left (back to the menu).
    func cancel() {
        guard let r = request else { return }
        request = nil
        if r.holding, SportsSession.shared.active { OnboardingFlow.shared.lessonSport != nil ? OnboardingFlow.shared.gameLeft() : TennisMenu.shared.goHome() }
        HubSession.shared.evaluate()
    }
    func deferLesson() {
        guard let r = request, let d = r.onDefer else { return }
        request = nil; d()
        HubSession.shared.evaluate()
    }
    /// The game it held went away (left, lost the TV).
    func sessionEnded() { if request?.holding == true { request = nil } }
    /// Tests.
    func reset() { request = nil; accepted = [] }

    // MARK: words

    static func steps(_ sport: Sport, tvConnected: Bool) -> [String] {
        switch sport {
        case .golf: [
            "Stand side-on to the TV.",
            "Hold the phone like a club, screen to the target.",
            "Tap SWING, then swing back and through.",
        ] + (tvConnected ? [] : ["No TV? Golf plays on this phone."])
        case .tennis: [
            "Face the TV and hold the phone like a racket.",
            "Swing as the rings close on the ball.",
        ]
        case .bowling: [
            "Hold the phone like the ball, screen up.",
            "Hold the button, swing back, then let go at the bottom.",
        ] + (tvConnected ? [] : ["No TV? Bowling plays on this phone."])
        default: []
        }
    }
    static let safety: [(icon: String, text: String)] = [
        ("hand.raised.fill", "Hold on tight. A wrist strap helps."),
        ("circle.dashed", "Clear 2 m (6 ft) around you."),
        ("tv", "Stand 2 m (6 ft) back from the TV."),
    ]
}

/// The card itself, over everything on the phone.
struct PlaySafeSheet: View {
    let request: PlaySafeGate.Request
    @State private var session = SportsSession.shared
    var body: some View {
        let sport = request.sport
        let needsTV = request.tutorial && sport == .tennis && !session.displayConnected
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(request.tutorial ? "How to play \(sport.rawValue)" : "Play safe")
                    .font(MotionBrand.font(.extraBoldItalic, 38)).lineLimit(1).minimumScaleFactor(0.6)
                // a still diagram (the animation is shown in game, in the lesson): you, 2 m / 6 ft, the TV
                DistanceDiagram()
                if request.tutorial {
                    VStack(alignment: .leading, spacing: 10) {
                        ForEach(Array(PlaySafeGate.steps(sport, tvConnected: session.displayConnected).enumerated()), id: \.offset) { i, line in
                            HStack(alignment: .top, spacing: 12) {
                                Text("\(i + 1)").font(MotionBrand.font(.extraBold, 15)).foregroundStyle(MotionBrand.navyInk)
                                    .frame(width: 28, height: 28).background(MotionBrand.gold, in: Circle())
                                Text(line).font(MotionBrand.font(.medium, 17)).fixedSize(horizontal: false, vertical: true)
                            }
                        }
                    }
                }
                VStack(alignment: .leading, spacing: 10) {
                    ForEach(PlaySafeGate.safety, id: \.icon) { row in
                        HStack(alignment: .top, spacing: 12) {
                            Image(systemName: row.icon).font(.system(size: 18, weight: .bold)).foregroundStyle(MotionBrand.gold).frame(width: 28)
                            Text(row.text).font(MotionBrand.font(.medium, 16)).fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .padding(16).frame(maxWidth: .infinity, alignment: .leading)
                .background(MotionBrand.navyInk.opacity(0.55), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).strokeBorder(.white.opacity(0.25), lineWidth: 1.5))
                if needsTV {
                    Text("Tennis needs a TV: Control Center › Screen Mirroring.")
                        .font(MotionBrand.font(.medium, 16)).foregroundStyle(MotionBrand.gold).fixedSize(horizontal: false, vertical: true)
                }
                Button { PlaySafeGate.shared.accept() } label: {
                    Text(needsTV ? "Waiting for a TV…" : request.tutorial ? "I'm ready" : request.holding ? "Got it, let's play" : "I'm ready")
                }
                .buttonStyle(MotionButtonStyle(kind: .primary)).disabled(needsTV).opacity(needsTV ? 0.5 : 1)
                .accessibilityIdentifier("playsafe-accept")
                if request.onDefer != nil {
                    Button { PlaySafeGate.shared.deferLesson() } label: { Text("No TV? Skip tennis for now") }
                        .buttonStyle(MotionButtonStyle(kind: .secondary)).accessibilityIdentifier("playsafe-defer")
                }
                Button { PlaySafeGate.shared.cancel() } label: { Text(request.holding ? "Leave game" : "Not now") }
                    .buttonStyle(MotionButtonStyle(kind: .ghost)).frame(maxWidth: .infinity)
                    .accessibilityIdentifier("playsafe-cancel")
            }
            .foregroundStyle(.white)
            .padding(.horizontal, 22).padding(.top, 24).padding(.bottom, 30)
        }
        .scrollIndicators(.hidden)
        .background(MotionBrand.background.ignoresSafeArea())
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("playsafe-\(request.tutorial ? "lesson" : "game")-\(sport.rawValue)")
    }
}

extension UIColor {
    /// "1F5BD8" or "#1F5BD8".
    convenience init?(hexString: String) {
        let s = hexString.trimmingCharacters(in: .whitespacesAndNewlines).replacingOccurrences(of: "#", with: "")
        guard s.count == 6, let v = Int(s, radix: 16) else { return nil }
        self.init(red: CGFloat((v >> 16) & 0xFF) / 255, green: CGFloat((v >> 8) & 0xFF) / 255, blue: CGFloat(v & 0xFF) / 255, alpha: 1)
    }
}

/// Stand back: you, a dashed 2 m · 6 ft line, the TV (a still picture; no animation outside the game).
struct DistanceDiagram: View {
    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: "figure.stand").font(.system(size: 44, weight: .bold)).foregroundStyle(MotionBrand.gold)
                .frame(width: 70, height: 70).overlay(Circle().strokeBorder(MotionBrand.gold, style: StrokeStyle(lineWidth: 2.5, dash: [5, 4])))
            VStack(spacing: 4) {
                Text("2 m · 6 ft").font(MotionBrand.font(.extraBoldItalic, 20)).foregroundStyle(.white)
                Rectangle().fill(.clear).frame(height: 3)
                    .overlay(Line().stroke(.white, style: StrokeStyle(lineWidth: 3, dash: [7, 6])))
                Text("at least").font(MotionBrand.font(.medium, 13)).foregroundStyle(MotionBrand.n300)
            }
            Image(systemName: "tv").font(.system(size: 40, weight: .bold)).foregroundStyle(.white).frame(width: 70, height: 70)
        }
        .padding(16).frame(maxWidth: .infinity)
        .background(MotionBrand.navyInk.opacity(0.55), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(.white, lineWidth: 3))
        .accessibilityElement(children: .ignore).accessibilityLabel("Stand at least 2 metres, 6 feet, back from the TV")
    }
    private struct Line: Shape {
        func path(in r: CGRect) -> Path { var p = Path(); p.move(to: CGPoint(x: 0, y: r.midY)); p.addLine(to: CGPoint(x: r.maxX, y: r.midY)); return p }
    }
}
