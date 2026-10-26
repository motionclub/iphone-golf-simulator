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
        guard window == nil, let scene = SportsDisplays.shared.external?.windowScene else { return }
        let w = UIWindow(windowScene: scene)
        w.windowLevel = .normal + 2
        w.backgroundColor = .clear; w.isUserInteractionEnabled = false
        let host = UIHostingController(rootView: LessonHUDRoot())
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

struct LessonHUD: View {
    @Bindable var center: LessonCenter
    @Bindable var session: SportsSession
    var body: some View {
        // (tennis sets up the court first, on its own screens: that is the lesson's station 1)
        let live = center.active && session.active && session.ready && session.loading.finished && !session.menuPauseVisible
            && (session.sport != "tennis" || session.setupStage == .playing)
        ZStack {
            if live && !center.station.title.isEmpty {
                VStack(spacing: 6) {
                    Text("\(center.sport == .tennis ? "TENNIS" : "GOLF") LESSON · \(center.station.index + 1) OF \(center.station.count)")
                        .font(Onb.font(14, 900)).tracking(1.6).foregroundStyle(Onb.ink)
                        .padding(.horizontal, 14).frame(height: 30).background(Onb.gold, in: Capsule())
                    Text(center.station.title).font(Onb.font(34, 900)).italic().foregroundStyle(.white)
                        .shadow(color: Onb.ink.opacity(0.8), radius: 6, y: 2)
                    LessonSteps(index: center.station.index, count: center.station.count)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top).padding(.top, 18)
                if center.explaining { LessonExplainer(station: center.station).transition(.scale(scale: 0.94).combined(with: .opacity)) }
                LessonCoachCard(center: center)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottom).padding(.bottom, 26)
                if !center.grade.isEmpty, center.shown != .ask {
                    LessonGradePop(word: center.grade, pass: center.shown == .pass).id(center.attempt)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top).padding(.top, 150)
                }
            }
        }
        .frame(width: 1280, height: 720)
        .animation(.spring(response: 0.38, dampingFraction: 0.84), value: center.attempt)
        .animation(.easeInOut(duration: 0.3), value: center.explaining)
        .animation(.easeInOut(duration: 0.3), value: center.station.index)
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

/// What to do now, how the last attempt went (the Shot Read), the hint after two misses, and the skip after three.
private struct LessonCoachCard: View {
    @Bindable var center: LessonCenter
    var body: some View {
        let pass = center.shown == .pass, miss = center.shown == .miss
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                Image(systemName: pass ? "checkmark" : miss ? "arrow.counterclockwise" : "figure.\(center.sport == .tennis ? "tennis" : "golf")")
                    .font(.system(size: 17, weight: .black)).foregroundStyle(Onb.ink)
                    .frame(width: 34, height: 34).background(pass ? Onb.green : miss ? Color(hex: "FFB547") : Onb.goldHi, in: Circle())
                Text(pass ? "NICE!" : miss ? "NOT QUITE" : center.sport == .tennis ? "COACH RAY" : "COACH")
                    .font(Onb.font(16, 900)).tracking(2).foregroundStyle(pass ? Color(hex: "6BEBA2") : miss ? Color(hex: "FFC46B") : Onb.goldHi)
                Spacer()
                if center.misses > 0, !pass { Text("\(center.misses) \(center.misses == 1 ? "try" : "tries")").font(Onb.font(14, 700)).foregroundStyle(Onb.mute) }
            }
            Text(center.text).font(Onb.font(24, 800)).foregroundStyle(.white).fixedSize(horizontal: false, vertical: true)
            if center.hintShown {
                VStack(alignment: .leading, spacing: 4) {
                    Text("TRY THIS").font(Onb.font(13, 900)).tracking(2).foregroundStyle(Onb.goldHi)
                    Text(center.station.hint).font(Onb.font(19, 600)).foregroundStyle(.white).fixedSize(horizontal: false, vertical: true)
                }
                .padding(14).frame(maxWidth: .infinity, alignment: .leading)
                .background(Onb.ink, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(Onb.goldHi, lineWidth: 2.5))
            }
            if !center.read.isEmpty, center.shown != .ask {
                HStack(spacing: 8) {
                    ForEach(center.read) { r in
                        let color = r.state == 1 ? Onb.green : r.state == 0 ? Color(hex: "FF6B5B") : Color(hex: "FFB547")
                        HStack(spacing: 7) {
                            Text(r.key).font(Onb.font(12, 800)).tracking(1).foregroundStyle(Onb.mute)
                            Text(r.value).font(Onb.font(16, 800)).foregroundStyle(.white)
                            Circle().fill(color).frame(width: 9, height: 9)
                        }
                        .padding(.horizontal, 11).frame(height: 34)
                        .background(Onb.ink, in: RoundedRectangle(cornerRadius: 11, style: .continuous))
                        .overlay(RoundedRectangle(cornerRadius: 11, style: .continuous).strokeBorder(color, lineWidth: 2))
                    }
                }
            }
            if pass { Text("Next station in a moment…").font(Onb.font(14, 700)).foregroundStyle(Onb.mute) }
            if center.skipOffered { Text("Stuck? SKIP THIS STEP is on your phone.").font(Onb.font(14, 800)).foregroundStyle(Onb.goldHi) }
        }
        .padding(.horizontal, 24).padding(.vertical, 18).frame(width: 660, alignment: .leading)
        .background(Onb.navy, in: RoundedRectangle(cornerRadius: 26, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 26, style: .continuous).strokeBorder(pass ? Onb.green : .white, lineWidth: 3.5))
        .shadow(color: Onb.deep.opacity(0.45), radius: 10, y: 10)
    }
}

/// The grade, big, the moment an attempt is judged.
private struct LessonGradePop: View {
    let word: String, pass: Bool
    @State private var shown = false
    var body: some View {
        let color: Color = ["PERFECT!", "ACE!", "POINT!", "PAR!", "IN!"].contains(word) ? Onb.goldHi
            : ["THIN", "LATE", "FAULT", "MISSED", "BUNKER", "TOO FIRM"].contains(word) ? Onb.coral
            : ["GREAT", "GREAT!", "EXCELLENT", "SAVED!"].contains(word) ? .white : Color(hex: "9CC2FF")
        Text(word).font(Onb.font(84, 900)).italic().foregroundStyle(color)
            .shadow(color: Onb.ink, radius: 0, x: 0, y: 5).shadow(color: Onb.ink.opacity(0.6), radius: 14, y: 10)
            .scaleEffect(shown ? 1 : 0.5).opacity(shown ? 1 : 0)
            .onAppear { withAnimation(.spring(response: 0.36, dampingFraction: 0.55)) { shown = true } }
    }
}

/// The station's "how it works" card, up from the station's start until the first attempt.
private struct LessonExplainer: View {
    let station: LessonCenter.Station
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("HOW IT WORKS").font(Onb.font(14, 900)).tracking(2.4).foregroundStyle(Onb.mute)
            ForEach(Array(station.tips.enumerated()), id: \.offset) { i, tip in
                HStack(alignment: .top, spacing: 12) {
                    Text("\(i + 1)").font(Onb.font(15, 900)).foregroundStyle(Onb.ink).frame(width: 28, height: 28).background(Onb.goldHi, in: Circle())
                    Text(tip).font(Onb.font(19, 700)).foregroundStyle(.white).fixedSize(horizontal: false, vertical: true)
                }
            }
        }
        .padding(24).frame(width: 440, alignment: .leading).onbPanel(radius: 26)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .trailing).padding(.trailing, 150).padding(.bottom, 120)
    }
}
