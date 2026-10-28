import Foundation
import CoreMotion
import QuartzCore

/// The loading bar's whole path, worked out when a load starts and once more when it is ready, so Core Animation can draw it
/// while Unity holds the main thread (a scene's activation and a venue's build block it for seconds: a bar redrawn by SwiftUI
/// froze there and then leapt to catch up; Adnan 10-28, "freezing, then loading sporadically"). Smooth over fast: the bar runs at
/// one steady speed to 90 % over the time this load usually takes (learned per venue), then creeps on, never quite still and
/// never full, until the load is ready; then it eases on to 100 % from the speed it had. A quick load still takes a moment to fill.
struct LoadingPace: Equatable {
    static let floor = 0.02, cruise = 0.9, tailRise = 0.08, tailSeconds = 5.0
    /// How far ahead an unfinished bar is laid out (past it the bar rests just short of full; a load that long shows its stall).
    static let horizon = 30.0
    /// The ease from "ready" to the full bar.
    static let finishShortest = 0.45, finishLongest = 2.5
    /// Longest a load is expected to take: with the finish, every bar fills inside 10 s.
    static let longestExpected = 8.0
    private(set) var start: TimeInterval
    private(set) var expected: TimeInterval
    private(set) var readyAt: TimeInterval?
    private var finishFrom = 0.0, finishLead = 0.0, finishSeconds = 0.0
    private var heldAt: TimeInterval?
    private var fixedValue: Double?

    init(start: TimeInterval, expected: TimeInterval) { self.start = start; self.expected = max(0.5, expected) }
    /// A bar that does not move.
    static func fixed(_ value: Double) -> LoadingPace { var p = LoadingPace(start: 0, expected: 1); p.fixedValue = value; return p }

    /// Still moving (not fixed, not stopped by a failure).
    var isMoving: Bool { fixedValue == nil && heldAt == nil }
    /// When the bar stops moving.
    var end: TimeInterval {
        if fixedValue != nil { return -.infinity }
        if let heldAt { return heldAt }
        if let readyAt { return readyAt + finishSeconds }
        return start + expected + Self.horizon
    }
    func isFull(at t: TimeInterval) -> Bool { fixedValue == 1 || readyAt != nil && heldAt == nil && t >= end }

    /// The bar at time `t` (the pace's clock: seconds of system uptime), 0...1.
    func value(at t: TimeInterval) -> Double {
        if let fixedValue { return fixedValue }
        let t = min(t, heldAt ?? .infinity)
        if let readyAt, t >= readyAt {
            // a Hermite ease: it leaves at the speed the bar had and arrives at rest on 100 %
            let u = min(1, (t - readyAt) / finishSeconds), u2 = u * u, u3 = u2 * u
            let h01 = 3 * u2 - 2 * u3
            return (1 - h01) * finishFrom + (u3 - 2 * u2 + u) * finishLead + h01
        }
        return climb(t - start)
    }
    private func climb(_ e: TimeInterval) -> Double {
        if e <= 0 { return Self.floor }
        if e < expected { return Self.floor + (Self.cruise - Self.floor) * e / expected }
        return Self.cruise + Self.tailRise * (1 - exp(-(e - expected) / Self.tailSeconds))
    }
    private func speed(_ e: TimeInterval) -> Double {
        if e < expected { return (Self.cruise - Self.floor) / expected }
        return Self.tailRise / Self.tailSeconds * exp(-(e - expected) / Self.tailSeconds)
    }

    /// The load is ready: from here the bar eases to full, its top speed under three times what it had (never a snap).
    mutating func markReady(at t: TimeInterval) {
        guard readyAt == nil, isMoving else { return }
        let e = max(0, t - start), v = climb(e), s = speed(e), gap = 1 - v
        // (a nearly full bar needs only a short ease: the last 2 % in 0.2 s)
        // (paced by the steady speed at least: a bar ready in its slow creep does not crawl the last few percent)
        let steady = (Self.cruise - Self.floor) / expected
        finishSeconds = min(Self.finishLongest, max(min(Self.finishShortest, max(0.2, gap * 4.5)), gap / (2 * max(s, steady))))
        finishLead = min(s * finishSeconds, 3 * gap)   // (≤ 3 × the gap keeps the ease from overshooting)
        finishFrom = v; readyAt = t
    }
    /// A failed load: the bar stops where it is.
    mutating func hold(at t: TimeInterval) { if isMoving { heldAt = max(t, start) } }

    // How long each load takes, learned per load (sport + venue, the plaza's boot), so the bar's steady speed fits it.
    private static let learnedKey = "loadingPaceSeconds"
    static func expected(for key: String, default seconds: TimeInterval = 4) -> TimeInterval {
        let learned = (UserDefaults.standard.dictionary(forKey: learnedKey) as? [String: Double])?[key]
        return min(longestExpected, max(1.5, (learned ?? seconds) * 1.1))
    }
    static func learn(_ key: String, took: TimeInterval) {
        guard took.isFinite, took > 0, !key.isEmpty else { return }
        var learned = UserDefaults.standard.dictionary(forKey: learnedKey) as? [String: Double] ?? [:]
        let took = min(30, took)
        learned[key] = learned[key].map { $0 * 0.5 + took * 0.5 } ?? took
        UserDefaults.standard.set(learned, forKey: learnedKey)
    }
}

/// Where a pace's clock stands against Core Animation's: pace time `pace` was media time `media`.
struct PaceAnchor: Equatable {
    var pace: TimeInterval, media: CFTimeInterval
    static var live: PaceAnchor { PaceAnchor(pace: ProcessInfo.processInfo.systemUptime, media: CACurrentMediaTime()) }
    /// The pace's clock now.
    var paceNow: TimeInterval { pace + (CACurrentMediaTime() - media) }
}

/// Loading reports actual work. The cover cannot finish before the target camera renders.
@MainActor @Observable
final class LoadingModel {
    enum Phase: String { case loading, frameReady, waitingForPlayers, transitioning, finished, cancelled, failed }
    static let minimum: TimeInterval = 1.2
    static let multiplayerMinimum: TimeInterval = 1.5
    static let finishDuration: TimeInterval = 0.25
    static var clockNow: Date { Date(timeIntervalSince1970: ProcessInfo.processInfo.systemUptime) }

    private(set) var phase: Phase = .finished
    var finished: Bool { phase == .finished || phase == .cancelled }
    private(set) var started: Date?
    private(set) var sceneProgress: Double?
    // Retained for existing capture fixtures; this is measured scene work, never elapsed time.
    var progress: Double { phase == .finished ? 1 : sceneProgress ?? 0 }
    private(set) var elapsed: TimeInterval = 0
    private(set) var waitingPlayers: [String] = []
    private(set) var transitionFraction = 0.0
    private(set) var timing: [String: Double] = [:]
    private(set) var tipIndex = -1
    private(set) var tipStarted: Date?
    var tipRemaining: TimeInterval { guard let tipStarted else { return 0 }; return max(0, 1.5-LoadingModel.clockNow.timeIntervalSince(tipStarted)) }
    /// Where in the sport's tips this load starts, so a player who loads often does not always
    /// meet the same first tip.
    private var tipOffset = 0
    /// Each load shows two tips from different parts of the sport's list and alternates them ("TIP 1/2", "TIP 2/2").
    static let tipsPerLoad = 2
    private var currentTip: GameTip? {
        guard tipIndex >= 0 else { return nil }
        let sport = Sport(rawValue: SportsSession.shared.sport) ?? .tennis
        return GameTips.tip(sport, at: tipOffset + (tipIndex % Self.tipsPerLoad) * 7)
    }
    var tip: String? { currentTip?.text }
    /// The tip card's headline ("Add topspin").
    var tipTitle: String? { currentTip?.title }
    /// The tip's topic ("Technique", "Setup", …) for its label.
    var tipKind: String? { currentTip?.kind.title }
    /// Which of this load's tips is up, 1-based (nil before the first).
    var tipNumber: Int? { tipIndex >= 0 ? tipIndex % Self.tipsPerLoad + 1 : nil }
    /// The loading bar's path (LoadingPace: steady, learned per venue, drawn by Core Animation so Unity's main-thread work
    /// cannot freeze it). The cover lifts only once it is full.
    private(set) var pace = LoadingPace.fixed(1)
    /// The pace's clock against Core Animation's, from the latest begin/tick (tests drive the model with their own times).
    @ObservationIgnored private(set) var anchor = PaceAnchor.live
    @ObservationIgnored private var paceKey = ""
    /// The full bar holds this long before the cover lifts.
    static let fullHold: TimeInterval = 0.15
    /// The loading bar, 0...1, at the latest tick (the percentage and the bar both follow `pace`).
    var displayProgress: Double { finished || phase == .transitioning ? 1 : pace.value(at: anchor.pace) }
    /// Seconds from now until the cover lifts if every player were ready now (multiplayer tells the lobby).
    var secondsUntilLift: TimeInterval {
        var p = pace; p.markReady(at: anchor.pace)
        return max(readMinimum - elapsed, p.end + Self.fullHold - anchor.pace, 0) + Self.finishDuration
    }
    /// The first tip is up almost at once, and each stays long enough to read.
    static let firstTipDelay: TimeInterval = 0.4
    static let tipInterval: TimeInterval = 6
    private var localReady = false
    private var playersReady = true
    private var readMinimum = LoadingModel.minimum
    private var finishStart: Date?
    private var errorMessage = ""
    private var stalledAfter: TimeInterval = 20
    var onFinish: (() -> Void)?
    private(set) var practiceSequence = 0
    private var lastPractice = Date.distantPast
    private let practiceMotion = CMMotionManager()

    var isStalled: Bool { !finished && phase != .transitioning && elapsed >= stalledAfter }
    var showsActivity: Bool { elapsed >= 2 && !finished && phase != .transitioning }
    var statusText: String {
        if phase == .failed { return errorMessage }
        if phase == .transitioning || phase == .frameReady || phase == .finished { return "Ready!" }
        if !waitingPlayers.isEmpty && localReady { return "Waiting for \(waitingPlayers.joined(separator: ", "))…" }
        if isStalled { return "Loading is taking longer than expected. Retry or leave the match." }
        if localReady { return "Waiting for the other players…" }
        if timing["sceneReady"] != nil { return "Preparing the first frame…" }
        if sceneProgress != nil { return "Preparing \(sceneProgress == 1 ? "the match" : "the venue")…" }
        return "Preparing your match…"
    }

    /// `key` names the load (sport + venue) whose usual length paces the bar.
    func begin(now: Date, multiplayer: Bool = false, key: String = "match") {
        practiceMotion.stopGyroUpdates(); practiceSequence = 0; lastPractice = .distantPast
        started = now; phase = .loading; elapsed = 0; sceneProgress = nil; transitionFraction = 0
        localReady = false; playersReady = !multiplayer; readMinimum = multiplayer ? Self.multiplayerMinimum : Self.minimum
        tipIndex = -1; tipStarted = nil; tipOffset = Int.random(in: 0..<10_000)
        waitingPlayers = []; finishStart = nil; errorMessage = ""; stalledAfter = 20
        timing = ["commit": now.timeIntervalSince1970]
        paceKey = multiplayer ? key + "-online" : key
        anchor = PaceAnchor(pace: now.timeIntervalSince1970, media: CACurrentMediaTime())
        pace = LoadingPace(start: now.timeIntervalSince1970, expected: LoadingPace.expected(for: paceKey))
    }
    func cardAppeared(now: Date = LoadingModel.clockNow) { record("cardVisibleCallback", now) }
    func markBoot(now: Date = LoadingModel.clockNow) { guard phase == .loading else { return }; record("boot", now) }
    func reach(_ value: Double) {
        guard phase == .loading, value.isFinite else { return }
        sceneProgress = max(sceneProgress ?? 0, min(1, max(0, value)))
    }
    func markSceneReady(now: Date = LoadingModel.clockNow) { guard !finished, phase != .failed else { return }; record("sceneReady", now) }
    func markReady(now: Date = LoadingModel.clockNow) {
        guard !finished, phase != .failed, !localReady else { return }
        localReady = true; record("firstRenderedFrame", now)
        phase = playersReady ? .frameReady : .waitingForPlayers
        if let started { LoadingPace.learn(paceKey, took: now.timeIntervalSince(started)) }
        finishPace(now)
    }
    /// Everyone is ready: the bar eases to full (never earlier than the latest tick, so it cannot step back).
    private func finishPace(_ now: Date) {
        if localReady && playersReady { pace.markReady(at: max(now.timeIntervalSince1970, anchor.pace)) }
    }
    func updatePlayers(waiting: [String], allReady: Bool, now: Date = LoadingModel.clockNow) {
        guard !finished, phase != .failed, phase != .transitioning else { return }
        waitingPlayers = waiting; playersReady = allReady
        if allReady { record("allPlayersReady", now) }
        if localReady { phase = allReady ? .frameReady : .waitingForPlayers }
        finishPace(now)
    }
    func keepWaiting() { stalledAfter = elapsed + 20 }
    func fail(_ message: String) {
        guard !finished else { return }; phase = .failed; errorMessage = message; practiceMotion.stopGyroUpdates()
        pace.hold(at: anchor.pace)
    }
    /// Only explicit automated verification may bypass the identity-read interval.
    func skip() { guard localReady, playersReady, !finished, phase != .failed else { return }; pace = .fixed(1); transitionFraction = 1; complete() }
    func cancel() { practiceMotion.stopGyroUpdates(); phase = .cancelled; started = nil; onFinish = nil }

    func tick(now: Date) {
        guard let started, !finished, phase != .failed else { return }
        elapsed = max(0, now.timeIntervalSince(started))
        anchor = PaceAnchor(pace: now.timeIntervalSince1970, media: CACurrentMediaTime())
        finishPace(now)
        if (!localReady || tipIndex < 0) && elapsed >= Self.firstTipDelay {
            let next = Int((elapsed - Self.firstTipDelay) / Self.tipInterval)
            if next != tipIndex { tipIndex = next; tipStarted = now }
        }
        guard localReady, playersReady, elapsed >= readMinimum, pace.isFull(at: now.timeIntervalSince1970 - Self.fullHold) else { return }
        if finishStart == nil { finishStart = now; phase = .transitioning; record("wipeStart", now) }
        transitionFraction = min(1, max(0, now.timeIntervalSince(finishStart!) / Self.finishDuration))
        if transitionFraction >= 1 { record("wipeEnd", now); complete() }
    }
    private func record(_ name: String, _ now: Date) {
        if timing[name] == nil { timing[name] = now.timeIntervalSince1970 }
    }
    private func complete() {
        practiceMotion.stopGyroUpdates(); phase = .finished
        let done = onFinish; onFinish = nil; done?()
    }
    func practice(now: Date = Date()) {
        guard !finished, phase != .failed, started != nil, now.timeIntervalSince(lastPractice) >= 1.5 else { return }
        lastPractice = now; practiceSequence += 1
    }
    private func startPracticeInput() {
        guard practiceMotion.isGyroAvailable else { return }
        practiceMotion.gyroUpdateInterval = 1.0 / 30
        practiceMotion.startGyroUpdates(to: .main) { [weak self] data, _ in
            guard let data else { return }; let r = data.rotationRate
            // (spelt out with its types: as one expression it is slow for the type checker, too slow for CI's)
            let x: Double = r.x * r.x, y: Double = r.y * r.y, z: Double = r.z * r.z
            if x + y + z > 20 {
                MainActor.assumeIsolated { self?.practice() }
            }
        }
    }
}
