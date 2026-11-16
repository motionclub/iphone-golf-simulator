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
    }
    enum Shown: Equatable { case ask, miss, pass }

    private(set) var sport: Sport?
    private(set) var station = Station()
    private(set) var shown: Shown = .ask
    private(set) var text = ""
    private(set) var grade = ""
    private(set) var misses = 0
    private(set) var read: [Read] = []
    /// The station's "how it works" card is up (until the first attempt).
    private(set) var explaining = false
    /// Changes with every attempt, so the grade pops again.
    private(set) var attempt = 0
    private(set) var finished = false
    var active: Bool { sport != nil && !finished }
    var hintShown: Bool { shown == .miss && misses >= 2 }
    var skipOffered: Bool { shown == .miss && misses >= 3 }

    func begin(_ sport: Sport) {
        self.sport = sport; finished = false; station = Station(); shown = .ask; text = ""; grade = ""; misses = 0; read = []; explaining = false
        LessonOverlay.shared.install()
    }
    func end() {
        sport = nil; finished = true; explaining = false
        LessonOverlay.shared.remove()
    }
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
                              hint: e["hint"] as? String ?? "", tips: e["tips"] as? [String] ?? [])
            shown = .ask; text = station.ask; grade = ""; misses = 0; read = []; explaining = !station.tips.isEmpty
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

/// The lesson over the game on the TV (Adnan 2026-11-15: "less covering the screen, especially the coach … easily able to see the
/// character … start with the gif intro, with the explainers on top of that, then transparent so the person can get good gameplay").
/// The lesson's first step opens on the how-to GIF with the station's tips laid over it (until the first swing). After that the HUD
/// is a slim, see-through stack at the top: which step, its title, one line of coaching (and the hint after two misses). Nothing sits
/// over the middle or the bottom of the screen, where the player is.
struct LessonHUD: View {
    @Bindable var center: LessonCenter
    @Bindable var session: SportsSession
    var body: some View {
        // (tennis sets up the court first, on its own screens: that is the lesson's station 1)
        let live = center.active && session.active && session.ready && session.loading.finished && !session.menuPauseVisible
            && (session.sport != "tennis" || session.setupStage == .playing)
        ZStack {
            if live && !center.station.title.isEmpty {
                if center.explaining, center.station.index == 0, let sport = center.sport, HowToGIF.available(sport) {
                    LessonGIFIntro(station: center.station, sport: sport).transition(.opacity)
                } else {
                    VStack(spacing: 6) {
                        Text("\(center.sport?.title ?? "") LESSON · \(center.station.index + 1) OF \(center.station.count)")
                            .font(Onb.font(12, 900)).tracking(1.4).foregroundStyle(Onb.ink)
                            .padding(.horizontal, 12).frame(height: 24).background(Onb.gold.opacity(0.92), in: Capsule())
                        Text(center.station.title).font(Onb.font(26, 900)).italic().foregroundStyle(.white)
                            .shadow(color: Onb.ink.opacity(0.9), radius: 4, y: 2)
                        LessonSteps(index: center.station.index, count: center.station.count).scaleEffect(0.8)
                        LessonCoachStrip(center: center)
                        if center.explaining { LessonTipsLine(station: center.station) }
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top).padding(.top, 12)
                    if !center.grade.isEmpty, center.shown != .ask {
                        LessonGradePop(word: center.grade, pass: center.shown == .pass).id(center.attempt)
                            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top).padding(.top, 210)
                    }
                }
            }
        }
        .frame(width: 1280, height: 720)
        .animation(.spring(response: 0.38, dampingFraction: 0.84), value: center.attempt)
        .animation(.easeInOut(duration: 0.35), value: center.explaining)
        .animation(.easeInOut(duration: 0.3), value: center.station.index)
    }
}

/// The lesson's opening: how it looks to play this sport in front of the TV (the GIF), with the station's tips over its lower part.
/// Up until the first swing; the game stays visible round it.
private struct LessonGIFIntro: View {
    let station: LessonCenter.Station
    let sport: Sport
    var body: some View {
        VStack(spacing: 10) {
            ZStack(alignment: .bottomLeading) {
                HowToGIF(sport: sport).frame(width: 720, height: 450)
                LinearGradient(colors: [.clear, Onb.ink.opacity(0.88)], startPoint: UnitPoint(x: 0.5, y: 0.35), endPoint: .bottom)
                VStack(alignment: .leading, spacing: 8) {
                    Text("\(sport.title) LESSON · HOW IT LOOKS").font(Onb.font(13, 900)).tracking(2).foregroundStyle(Onb.goldHi)
                    Text(station.title).font(Onb.font(30, 900)).italic().foregroundStyle(.white)
                    ForEach(Array(station.tips.enumerated()), id: \.offset) { i, tip in
                        HStack(alignment: .top, spacing: 10) {
                            Text("\(i + 1)").font(Onb.font(13, 900)).foregroundStyle(Onb.ink).frame(width: 24, height: 24).background(Onb.goldHi, in: Circle())
                            Text(tip).font(Onb.font(17, 700)).foregroundStyle(.white).fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .padding(22)
            }
            .frame(width: 720, height: 450)
            .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(.white, lineWidth: 3))
            .shadow(color: Onb.deep.opacity(0.5), radius: 14, y: 10)
            Text("Swing when you're ready").font(Onb.font(18, 800)).foregroundStyle(.white)
                .padding(.horizontal, 16).frame(height: 34).background(Onb.ink.opacity(0.6), in: Capsule())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
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

/// One see-through line of coaching under the title: what to do, or how the last try went; the hint after two misses.
private struct LessonCoachStrip: View {
    @Bindable var center: LessonCenter
    var compact = false
    var body: some View {
        let pass = center.shown == .pass, miss = center.shown == .miss
        VStack(alignment: compact ? .leading : .center, spacing: 4) {
            HStack(spacing: 8) {
                Image(systemName: pass ? "checkmark" : miss ? "arrow.counterclockwise" : center.sport?.icon ?? "figure.golf")
                    .font(.system(size: compact ? 10 : 12, weight: .black)).foregroundStyle(Onb.ink)
                    .frame(width: compact ? 18 : 22, height: compact ? 18 : 22).background(pass ? Onb.green : miss ? Color(hex: "FFB547") : Onb.goldHi, in: Circle())
                Text(center.shown == .ask ? center.station.ask : center.text)
                    .font(Onb.font(compact ? 13 : 17, 700)).foregroundStyle(pass ? Color(hex: "8CF5B8") : miss ? Color(hex: "FFD08A") : .white)
                    .lineLimit(2).fixedSize(horizontal: false, vertical: true)
            }
            if center.hintShown {
                Text("Try this: \(center.station.hint)").font(Onb.font(compact ? 12 : 15, 700)).foregroundStyle(Onb.goldHi).lineLimit(2)
            }
            if !compact, !center.read.isEmpty, center.shown != .ask {
                HStack(spacing: 6) {
                    ForEach(center.read) { r in
                        let color = r.state == 1 ? Onb.green : r.state == 0 ? Color(hex: "FF6B5B") : Color(hex: "FFB547")
                        HStack(spacing: 5) {
                            Text(r.key).font(Onb.font(10, 800)).tracking(0.8).foregroundStyle(Onb.mute)
                            Text(r.value).font(Onb.font(13, 800)).foregroundStyle(.white)
                            Circle().fill(color).frame(width: 7, height: 7)
                        }
                        .padding(.horizontal, 8).frame(height: 24)
                        .background(Onb.ink.opacity(0.5), in: Capsule())
                    }
                }
            }
            if center.skipOffered { Text(compact ? "Stuck? SKIP is below." : "Stuck? SKIP THIS STEP is on your phone.").font(Onb.font(compact ? 11 : 13, 800)).foregroundStyle(Onb.goldHi) }
        }
        .padding(.horizontal, compact ? 10 : 16).padding(.vertical, compact ? 6 : 8).frame(maxWidth: compact ? .infinity : 760, alignment: compact ? .leading : .center)
        .background(Onb.ink.opacity(0.42), in: RoundedRectangle(cornerRadius: compact ? 12 : 16, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: compact ? 12 : 16, style: .continuous).strokeBorder(pass ? Onb.green.opacity(0.8) : .white.opacity(0.25), lineWidth: 1.5))
    }
}

/// The grade, the moment an attempt is judged: big enough to read from the sofa, gone in a moment.
private struct LessonGradePop: View {
    let word: String, pass: Bool
    var size: CGFloat = 54
    @State private var shown = false
    var body: some View {
        let color: Color = ["PERFECT!", "ACE!", "POINT!", "PAR!", "IN!"].contains(word) ? Onb.goldHi
            : ["THIN", "LATE", "FAULT", "MISSED", "BUNKER", "TOO FIRM"].contains(word) ? Onb.coral
            : ["GREAT", "GREAT!", "EXCELLENT", "SAVED!"].contains(word) ? .white : Color(hex: "9CC2FF")
        Text(word).font(Onb.font(size, 900)).italic().foregroundStyle(color)
            .shadow(color: Onb.ink, radius: 0, x: 0, y: 4).shadow(color: Onb.ink.opacity(0.6), radius: 10, y: 6)
            .scaleEffect(shown ? 1 : 0.5).opacity(shown ? 1 : 0)
            .onAppear {
                withAnimation(.spring(response: 0.36, dampingFraction: 0.55)) { shown = true }
                withAnimation(.easeOut(duration: 0.5).delay(1.6)) { shown = false }
            }
    }
}

/// A station's tips (no GIF, or a later station), one small see-through line each, until the first try.
private struct LessonTipsLine: View {
    let station: LessonCenter.Station
    var compact = false
    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            ForEach(Array(station.tips.enumerated()), id: \.offset) { i, tip in
                Text("\(i + 1)  \(tip)").font(Onb.font(compact ? 12 : 14, 700)).foregroundStyle(.white.opacity(0.92)).lineLimit(compact ? 2 : 1)
            }
        }
        .padding(.horizontal, compact ? 10 : 14).padding(.vertical, compact ? 6 : 8).frame(maxWidth: compact ? .infinity : 760, alignment: .leading)
        .background(Onb.ink.opacity(0.32), in: RoundedRectangle(cornerRadius: compact ? 12 : 14, style: .continuous))
    }
}

/// The lesson's coach on the phone itself (no TV: golf and bowling play handheld). Its first step opens on the GIF with the tips over
/// it; after that a slim see-through strip at the top, so the game (and the player) stays in view.
struct LessonPhoneHUD: View {
    @Bindable var center: LessonCenter
    @Bindable var session: SportsSession
    var body: some View {
        let live = center.active && session.active && session.ready && session.loading.finished && !session.menuPauseVisible && !center.station.title.isEmpty
        VStack {
            if live {
                if center.explaining, center.station.index == 0, let sport = center.sport, HowToGIF.available(sport) {
                    // (a clear 16:10 box sets the size: the animated image view and the gradient would take all the room offered)
                    Color.clear.aspectRatio(16 / 10, contentMode: .fit)
                        .overlay { HowToGIF(sport: sport) }
                        .overlay { LinearGradient(colors: [.clear, Onb.ink.opacity(0.88)], startPoint: UnitPoint(x: 0.5, y: 0.3), endPoint: .bottom) }
                        .overlay(alignment: .bottomLeading) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("\(sport.title) LESSON · HOW IT LOOKS").font(Onb.font(10, 900)).tracking(1.4).foregroundStyle(Onb.goldHi)
                                ForEach(Array(center.station.tips.enumerated()), id: \.offset) { i, tip in
                                    Text("\(i + 1)  \(tip)").font(Onb.font(12, 700)).foregroundStyle(.white).fixedSize(horizontal: false, vertical: true)
                                }
                            }
                            .padding(10)
                        }
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(.white, lineWidth: 2))
                    .padding(.horizontal, 10).padding(.top, 54)
                    .transition(.opacity)
                } else {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 6) {
                            Text("\(center.sport?.title ?? "") · \(center.station.index + 1)/\(center.station.count)")
                                .font(Onb.font(10, 900)).tracking(1).foregroundStyle(Onb.ink)
                                .padding(.horizontal, 7).frame(height: 18).background(Onb.gold.opacity(0.92), in: Capsule())
                            Text(center.station.title).font(Onb.font(14, 900)).italic().foregroundStyle(.white)
                                .shadow(color: Onb.ink.opacity(0.9), radius: 3, y: 1).lineLimit(1)
                            Spacer(minLength: 0)
                            if !center.grade.isEmpty, center.shown != .ask {
                                Text(center.grade).font(Onb.font(14, 900)).italic().foregroundStyle(center.shown == .pass ? Onb.green : Onb.coral)
                            }
                        }
                        LessonCoachStrip(center: center, compact: true)
                        if center.explaining { LessonTipsLine(station: center.station, compact: true) }
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
