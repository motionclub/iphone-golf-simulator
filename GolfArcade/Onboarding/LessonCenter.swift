import SwiftUI

/// A lesson in progress (PLAN_Onboarding_GolfLesson.md). Unity runs the lesson and decides every pass and miss; it reports
/// each station and attempt as a "lesson" event (JSON), and this draws them over the game on the TV (LessonOverlay) and keeps
/// onboarding in step (resume station, reward).
@MainActor @Observable
final class LessonCenter {
    static let shared = LessonCenter()

    struct Read: Equatable, Identifiable { let key: String, value: String, state: Int; var id: String { key } }   // state 1 good, 0 fault, 2 note
    struct Station: Equatable {
        var index = 0, count = 8
        var key = "", name = "", title = "", ask = "", hint = ""
        var tips: [String] = []
        /// A few words of why, shown first as a card (golf's "Putting is sensitive", 11-21).
        var explainTitle = "", explainBody = ""
        var explains: Bool { !explainTitle.isEmpty }
    }
    enum Shown: Equatable { case ask, miss, pass }

    private(set) var sport: Sport?
    private(set) var station = Station()
    private(set) var shown: Shown = .ask
    private(set) var text = ""
    private(set) var grade = ""
    private(set) var misses = 0
    private(set) var read: [Read] = []
    /// The lesson's opening animation (its first reported station), or a station's explain card, is up (for a few seconds:
    /// introSeconds / explainSeconds, or until the first swing).
    private(set) var explaining = false
    /// How long the opening animation stays (Adnan 11-16: "3-5 seconds max", not until the first swing).
    static let introSeconds = 4.0
    /// How long an explain card stays (it has a sentence or two to read).
    static let explainSeconds = 6.0
    /// No station reported yet this lesson (tennis reports from station 1: its court setup is station 0's place).
    private var firstStation = true
    /// Changes with every attempt, so the grade pops again.
    private(set) var attempt = 0
    private(set) var finished = false
    var active: Bool { sport != nil && !finished }
    var hintShown: Bool { shown == .miss && misses >= 2 }
    var skipOffered: Bool { shown == .miss && misses >= 3 }

    func begin(_ sport: Sport) {
        self.sport = sport; finished = false; station = Station(); shown = .ask; text = ""; grade = ""; misses = 0; read = []; explaining = false; firstStation = true
        LessonOverlay.shared.install()
    }
    func end() {
        sport = nil; finished = true; explaining = false
        LessonOverlay.shared.remove()
    }
    /// The opening animation has been up for introSeconds.
    func introDone() { explaining = false }
    /// The one line under the title: what to do, how the last try went, or (after two misses) the fix.
    var line: String { hintShown && !station.hint.isEmpty ? station.hint : shown == .ask ? station.ask : text }
    /// The phone's Skip this step (offered after three misses).
    func skipStep() { SportsSession.shared.command("lessonSkip") }

    /// One "lesson" event from Unity: {"kind":"station"|"attempt"|"done", ...}.
    func receive(_ json: String) {
        guard let data = json.data(using: .utf8), let e = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let kind = e["kind"] as? String else { return }
        if sport == nil, let s = (e["sport"] as? String).flatMap(Sport.init(rawValue:)) { begin(s) }
        guard let sport else { return }
        switch kind {
        case "station":
            station = Station(index: e["index"] as? Int ?? 0, count: e["count"] as? Int ?? 8, key: e["key"] as? String ?? "",
                              name: e["name"] as? String ?? "", title: e["title"] as? String ?? "", ask: e["ask"] as? String ?? "",
                              hint: e["hint"] as? String ?? "", tips: e["tips"] as? [String] ?? [],
                              explainTitle: (e["explain"] as? [String: Any])?["title"] as? String ?? "",
                              explainBody: (e["explain"] as? [String: Any])?["body"] as? String ?? "")
            shown = .ask; text = station.ask; grade = ""; misses = 0; read = []
            explaining = station.explains || (firstStation && HowToGIF.available(sport))
            firstStation = false
            OnboardingFlow.shared.lessonStation(station.index, sport: sport)
            Analytics.track("tutorial_step_start", ["sport": sport.rawValue, "i": String(station.index)])
        case "attempt":
            let pass = (e["result"] as? String) == "pass"
            shown = pass ? .pass : .miss
            text = e["text"] as? String ?? ""
            grade = e["grade"] as? String ?? ""
            misses = e["misses"] as? Int ?? (pass ? misses : misses + 1)
            read = (e["read"] as? [[Any]] ?? []).compactMap { row in
                guard row.count >= 2, let k = row[0] as? String, let v = row[1] as? String else { return nil }
                return Read(key: k, value: v, state: row.count > 2 ? (row[2] as? Int ?? 2) : 2)
            }
            explaining = false; attempt += 1
            if pass { Analytics.track("tutorial_step_pass", ["sport": sport.rawValue, "i": String(station.index), "misses": String(misses)]) }
        case "explained":
            explaining = false
        case "done":
            end()
            OnboardingFlow.shared.completed(sport)
        default: break
        }
    }
}

/// The lesson's coaching over the game on the TV: which station, what to do, how the last swing went, and the station's
/// "how it works" card. A clear, touch-through window above Unity's own, on the TV canvas the menus use.
@MainActor
final class LessonOverlay {
    static let shared = LessonOverlay()
    private var window: UIWindow?
    func install() {
        guard window == nil else { return }
        // On the TV when there is one; with none (golf and bowling played on the phone) a compact coach card on the phone itself
        // (PLAN_Onboarding_v3: no TV is needed for the Tutorial's golf and bowling)
        let tv = SportsDisplays.shared.external?.windowScene
        guard let scene = tv ?? SportsDisplays.shared.phone?.windowScene
                ?? UIApplication.shared.connectedScenes.compactMap({ $0 as? UIWindowScene }).first(where: { $0.session.role == .windowApplication }) else { return }
        let w = UIWindow(windowScene: scene)
        w.windowLevel = .normal + 2
        w.backgroundColor = .clear; w.isUserInteractionEnabled = false
        let host = tv != nil ? UIHostingController(rootView: AnyView(LessonHUDRoot())) : UIHostingController(rootView: AnyView(LessonPhoneHUD(center: .shared, session: .shared)))
        host.view.backgroundColor = .clear; w.rootViewController = host
        w.isHidden = false; window = w
    }
    func remove() { window?.isHidden = true; window = nil }
}

private struct LessonHUDRoot: View {
    var body: some View {
        GeometryReader { g in
            let scale = min(g.size.width / 1280, g.size.height / 720) * (1 - SportsSession.shared.overscan)
            LessonHUD(center: .shared, session: .shared)
                .frame(width: 1280, height: 720).scaleEffect(scale)
                .frame(width: g.size.width, height: g.size.height)
        }
        .ignoresSafeArea().allowsHitTesting(false)
    }
}

/// The lesson over the game on the TV. Adnan 11-16: short and intentional, nothing redundant. The first station opens on the how-to
/// animation for a few seconds (introSeconds), with the station's title and what to do; then only the title, the progress dots and one
/// line at the top: what to do, how the last try went, or the fix after two misses. The game's own HUD shows the grade and the numbers.
struct LessonHUD: View {
    @Bindable var center: LessonCenter
    @Bindable var session: SportsSession
    var body: some View {
        // (tennis sets up the court first, on its own screens: that is the lesson's station 1)
        let live = center.active && session.active && session.ready && session.loading.finished && !session.menuPauseVisible
            && (session.sport != "tennis" || session.setupStage == .playing)
        ZStack {
            if live && !center.station.title.isEmpty {
                if center.explaining, center.station.explains {
                    LessonExplainCard(center: center).transition(.opacity)
                } else if center.explaining, let sport = center.sport, HowToGIF.available(sport) {
                    LessonGIFIntro(center: center, sport: sport).transition(.opacity)
                } else {
                    VStack(spacing: 6) {
                        Text(center.station.title).font(Onb.font(26, 900)).italic().foregroundStyle(.white)
                            .shadow(color: Onb.ink.opacity(0.9), radius: 4, y: 2)
                        LessonSteps(index: center.station.index, count: center.station.count).scaleEffect(0.8)
                        LessonCoachStrip(center: center)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top).padding(.top, 12)
                }
            }
        }
        .frame(width: 1280, height: 720)
        .animation(.spring(response: 0.38, dampingFraction: 0.84), value: center.attempt)
        .animation(.easeInOut(duration: 0.35), value: center.explaining)
        .animation(.easeInOut(duration: 0.3), value: center.station.index)
    }
}

/// The lesson's opening: how it looks to play this sport in front of the TV (the GIF), the first station's title and what to do.
/// Up for introSeconds; the game stays visible round it.
private struct LessonGIFIntro: View {
    @Bindable var center: LessonCenter
    let sport: Sport
    var body: some View {
        ZStack(alignment: .bottomLeading) {
            HowToGIF(sport: sport).frame(width: 720, height: 450)
            LinearGradient(colors: [.clear, Onb.ink.opacity(0.88)], startPoint: UnitPoint(x: 0.5, y: 0.45), endPoint: .bottom)
            VStack(alignment: .leading, spacing: 6) {
                Text(center.station.title).font(Onb.font(30, 900)).italic().foregroundStyle(.white)
                if !center.station.ask.isEmpty { Text(center.station.ask).font(Onb.font(18, 700)).foregroundStyle(.white).fixedSize(horizontal: false, vertical: true) }
            }
            .padding(22)
        }
        .frame(width: 720, height: 450)
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(.white, lineWidth: 3))
        .shadow(color: Onb.deep.opacity(0.5), radius: 14, y: 10)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .task { try? await Task.sleep(for: .seconds(LessonCenter.introSeconds)); center.introDone() }
    }
}

/// A station's few words of why (golf's "Putting is sensitive"), over the game on the TV for explainSeconds or until the first swing.
private struct LessonExplainCard: View {
    @Bindable var center: LessonCenter
    var compact = false
    var body: some View {
        VStack(alignment: .leading, spacing: compact ? 4 : 8) {
            Text(center.station.explainTitle).font(Onb.font(compact ? 18 : 34, 900)).italic().foregroundStyle(Onb.goldHi)
            Text(center.station.explainBody).font(Onb.font(compact ? 13 : 21, 700)).foregroundStyle(.white).fixedSize(horizontal: false, vertical: true)
            if !center.station.ask.isEmpty {
                Text(center.station.ask).font(Onb.font(compact ? 12 : 17, 700)).foregroundStyle(Color(hex: "8CF5B8")).fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding(compact ? 12 : 26)
        .frame(maxWidth: compact ? .infinity : 720, alignment: .leading)
        .background(Onb.ink.opacity(0.86), in: RoundedRectangle(cornerRadius: compact ? 16 : 24, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: compact ? 16 : 24, style: .continuous).strokeBorder(.white, lineWidth: compact ? 2 : 3))
        .frame(maxWidth: .infinity, maxHeight: compact ? nil : .infinity)
        .accessibilityIdentifier("lesson-explain")
        .task(id: center.station.key) { try? await Task.sleep(for: .seconds(LessonCenter.explainSeconds)); center.introDone() }
    }
}

private struct LessonSteps: View {
    let index: Int, count: Int
    var body: some View {
        HStack(spacing: 7) {
            ForEach(0..<max(1, count), id: \.self) { k in
                Capsule().fill(k < index ? Onb.goldHi : k == index ? .white : .clear)
                    .overlay(Capsule().strokeBorder(k <= index ? .white : Color(hex: "8FA8E8"), lineWidth: 2))
                    .frame(width: k == index ? 36 : 14, height: 14)
            }
        }
        .padding(.horizontal, 12).frame(height: 30).background(Onb.navy.opacity(0.9), in: Capsule())
        .overlay(Capsule().strokeBorder(.white, lineWidth: 2.5))
    }
}

/// The one see-through line under the title (LessonCenter.line), green after a pass and amber after a miss.
private struct LessonCoachStrip: View {
    @Bindable var center: LessonCenter
    var compact = false
    var body: some View {
        let pass = center.shown == .pass, miss = center.shown == .miss
        let line = center.line
        if !line.isEmpty || (center.skipOffered && !compact) {
            VStack(alignment: compact ? .leading : .center, spacing: 4) {
                if !line.isEmpty {
                    Text(line)
                        .font(Onb.font(compact ? 14 : 18, 700)).foregroundStyle(pass ? Color(hex: "8CF5B8") : miss ? Color(hex: "FFD08A") : .white)
                        .lineLimit(2).fixedSize(horizontal: false, vertical: true)
                }
                // (on the phone the SKIP button itself is on screen; on the TV it says where it is)
                if center.skipOffered && !compact { Text("Skip on your phone").font(Onb.font(13, 800)).foregroundStyle(Onb.goldHi) }
            }
            .padding(.horizontal, compact ? 10 : 16).padding(.vertical, compact ? 6 : 8)
            .frame(maxWidth: compact ? .infinity : 760, alignment: compact ? .leading : .center)
            .background(Onb.ink.opacity(0.42), in: RoundedRectangle(cornerRadius: compact ? 12 : 16, style: .continuous))
        }
    }
}

/// The lesson's coach on the phone itself (no TV: golf and bowling play handheld): the opening animation for introSeconds, then the
/// title and the one line at the top, so the game (and the player) stays in view.
struct LessonPhoneHUD: View {
    @Bindable var center: LessonCenter
    @Bindable var session: SportsSession
    var body: some View {
        let live = center.active && session.active && session.ready && session.loading.finished && !session.menuPauseVisible && !center.station.title.isEmpty
        VStack {
            if live {
                if center.explaining, center.station.explains {
                    LessonExplainCard(center: center, compact: true).padding(.horizontal, 10).padding(.top, 54).transition(.opacity)
                } else if center.explaining, let sport = center.sport, HowToGIF.available(sport) {
                    // (a clear 16:10 box sets the size: the animated image view and the gradient would take all the room offered)
                    Color.clear.aspectRatio(16 / 10, contentMode: .fit)
                        .overlay { HowToGIF(sport: sport) }
                        .overlay { LinearGradient(colors: [.clear, Onb.ink.opacity(0.88)], startPoint: UnitPoint(x: 0.5, y: 0.4), endPoint: .bottom) }
                        .overlay(alignment: .bottomLeading) {
                            VStack(alignment: .leading, spacing: 3) {
                                Text(center.station.title).font(Onb.font(18, 900)).italic().foregroundStyle(.white)
                                if !center.station.ask.isEmpty { Text(center.station.ask).font(Onb.font(13, 700)).foregroundStyle(.white).fixedSize(horizontal: false, vertical: true) }
                            }
                            .padding(10)
                        }
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(.white, lineWidth: 2))
                    .padding(.horizontal, 10).padding(.top, 54)
                    .transition(.opacity)
                    .task { try? await Task.sleep(for: .seconds(LessonCenter.introSeconds)); center.introDone() }
                } else {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(center.station.title).font(Onb.font(16, 900)).italic().foregroundStyle(.white)
                            .shadow(color: Onb.ink.opacity(0.9), radius: 3, y: 1).lineLimit(1)
                        LessonCoachStrip(center: center, compact: true)
                    }
                    .padding(.horizontal, 10).padding(.top, 54)
                    .transition(.move(edge: .top).combined(with: .opacity))
                }
            }
            Spacer()
        }
        .allowsHitTesting(false)
        .animation(.spring(response: 0.38, dampingFraction: 0.84), value: center.attempt)
        .animation(.easeInOut(duration: 0.35), value: center.explaining)
        .animation(.easeInOut(duration: 0.3), value: center.station.index)
    }
}
