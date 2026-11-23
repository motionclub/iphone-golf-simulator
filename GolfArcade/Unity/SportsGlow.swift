import Foundation
import simd

// MARK: - Point and fill (2026-11-22)
//
// The tennis setup's one step: point the phone at the TV and hold it there while a circle fills. It replaces the black-and-white
// flashes (which found the TV and timed it) and the swing timing drill (Adnan, 11-22: "too much friction"; mock in the chat of that
// day, https://claude.ai/artifact/6JUqPwq2YVuf81GC5AJ9Q8).
//
// While the circle is up, the app's window on the TV (TennisSetupTVView) slowly dims and brightens the picture behind its card to
// `SportsGlow.wave`, a known pattern on a clock every phone shares. Each phone's rear camera watches its own picture:
// - the part of it that brightens and dims in step with the wave is the TV (nothing else in a room follows that pattern), so the
//   phone knows it is pointed at the TV and in which direction the TV lies;
// - how far the camera's copy of the wave trails the game's is the TV's delay (AirPlay, the Apple TV and the TV's own processing).
// Every camera frame adds to the reading, so it settles in a couple of seconds; a wobbling hand only slows the fill.
//
// With several phones on one TV the circle is shared: it fills only while every one of them sees the TV at the same moment, and drains
// when one drops off, so nobody can be set up pointing somewhere else (Adnan, 11-22). The swing timing drill is gone: TennisLagLearner
// (Unity) refines the timing from the first few serves and rally hits, starting from this reading, and keeps it for this TV.

enum SportsGlow {
    /// The glow's level (0 dim ... 1 bright) at `t` seconds on the glow clock. Three slow waves that never line up the same way within
    /// the delays a TV can have, so there is exactly one best match.
    static func wave(_ t: Double) -> Double {
        0.5 + 0.22 * sin(2 * .pi * 0.9 * t) + 0.16 * sin(2 * .pi * 1.7 * t + 1.3) + 0.1 * sin(2 * .pi * 2.9 * t + 0.4)
    }
    /// How dark the veil over the picture is (black, this opacity) at glow level `level`: never black, never a flash.
    static let dimmest = 0.46, lightest = 0.04
    static func veil(_ t: Double) -> Double { lightest + (dimmest - lightest) * (1 - max(0, min(1, wave(t)))) }

    /// The glow clock minus the host clock (CACurrentMediaTime, the camera's timestamps, CADisplayLink). 0 alone; the multiplayer
    /// network clock's offset when phones share one TV, so every phone reads the same wave the TV phone draws. Main thread.
    @MainActor static var clockOffset = 0.0

    /// The game's own picture reaches the TV about a frame after the app's window does: Unity stamps its frames before they are
    /// presented (SportsDelayProbe measured from that stamp), the window's glow is stamped at the frame's presentation. Added to the
    /// reading so the game's timing gets the same number the flashes gave. To be tuned on a device against the old flashes.
    static let gameFrameLead = 1.0 / 60
}

/// What the phone's camera made of its last two seconds, handed to the main thread ten times a second while the circle is up.
struct SportsGlowSighting: Equatable, Sendable {
    /// When (host clock).
    var time: Double
    /// The TV is in view, following the wave.
    var seeing: Bool
    /// The TV's delay (seconds, without gameFrameLead), and how closely it followed the wave there.
    var delay: Double?
    var match: Double
    /// The direction through the TV (radians, in the motion sensors' frame), when seeing it level enough.
    var heading: Double?
}

/// One look at the camera's last two seconds: is the TV in it, where, and how far behind the game its picture runs.
enum SportsGlowReader {
    struct Reading: Equatable {
        /// The TV's middle in the camera image (0...1, origin top-left, the sensor's landscape orientation).
        var at: SIMD2<Double>
        /// Seconds the camera's copy of the wave trails the game's (no gameFrameLead).
        var delay: Double
        /// How closely the TV's brightness follows the wave at that delay (correlation, -1...1).
        var match: Double
        /// The TV's share of the picture.
        var share: Double
        var seeing: Bool { match >= SportsGlowReader.minimumMatch }
    }
    /// The frames read (seconds), and the least of them a reading needs.
    static let window = 2.0, minimumSpan = 1.2
    /// Delays searched (seconds), coarsely to find the TV, then finely to time it.
    static let longest = 0.6, coarseStep = 0.05, fineStep = 0.002
    /// A patch of the picture counts as glowing when its brightness follows the wave this closely at some delay, and moves this much
    /// (standard deviation, 0-255 luma).
    static let cellMatch = 0.6, minimumSwing = 1.2
    /// The glowing patch must be this much of the picture, and fill this much of the box around it (the card in the middle of the TV
    /// does not glow, so the TV reads as a frame around it).
    static let minimumShare = 0.004, minimumFill = 0.25
    /// The whole patch must follow the wave this closely for the phone to count as on the TV.
    static let minimumMatch = 0.8

    /// `frames` on the glow clock (SportsScreenFinder.grid cells, `columns` across and `rows` down, oldest first).
    static func read(_ frames: [SportsScreenFinder.Frame], rows: Int, columns: Int = SportsScreenFinder.columns) -> Reading? {
        guard let newest = frames.last?.time, rows >= 2, columns >= 2 else { return nil }
        let recent = frames.filter { $0.time >= newest - window && $0.cells.count == rows * columns }
        guard recent.count >= 30, let first = recent.first, newest - first.time >= minimumSpan else { return nil }
        let n = recent.count, times = recent.map(\.time)

        // the picture pooled 2×2, as one brightness series per cell
        let pc = columns / 2, pr = rows / 2, cells = pc * pr
        var series = [Float](repeating: 0, count: cells * n)
        for (k, frame) in recent.enumerated() {
            frame.cells.withUnsafeBufferPointer { px in
                for y in 0..<pr {
                    let top = 2 * y * columns, bottom = top + columns
                    for x in 0..<pc {
                        let s = Int(px[top + 2 * x]) + Int(px[top + 2 * x + 1]) + Int(px[bottom + 2 * x]) + Int(px[bottom + 2 * x + 1])
                        series[(y * pc + x) * n + k] = Float(s) * 0.25
                    }
                }
            }
        }

        // the wave at each coarse delay, zero-mean and unit length
        let coarse = stride(from: 0.0, through: longest + 1e-9, by: coarseStep).map { lag in normalized(times.map { Float(SportsGlow.wave($0 - lag)) }) }
        var glowing = [Bool](repeating: false, count: cells)
        var x = [Float](repeating: 0, count: n)
        for c in 0..<cells {
            var mean: Float = 0
            for k in 0..<n { mean += series[c * n + k] }
            mean /= Float(n)
            var energy: Float = 0
            for k in 0..<n { let d = series[c * n + k] - mean; x[k] = d; energy += d * d }
            guard (Double(energy) / Double(n)).squareRoot() >= minimumSwing else { continue }
            let length = energy.squareRoot()
            var best: Float = -1
            for reference in coarse {
                var dot: Float = 0
                for k in 0..<n { dot += x[k] * reference[k] }
                best = max(best, dot / length)
            }
            glowing[c] = Double(best) >= cellMatch
        }

        // the largest patch of glowing cells
        var seen = [Bool](repeating: false, count: cells), patch = [Int]()
        for start in 0..<cells where glowing[start] && !seen[start] {
            var stack = [start], group = [Int]()
            seen[start] = true
            while let i = stack.popLast() {
                group.append(i)
                let cx = i % pc, cy = i / pc
                for (j, ok) in [(i - 1, cx > 0), (i + 1, cx < pc - 1), (i - pc, cy > 0), (i + pc, cy < pr - 1)] where ok && glowing[j] && !seen[j] {
                    seen[j] = true; stack.append(j)
                }
            }
            if group.count > patch.count { patch = group }
        }
        guard !patch.isEmpty else { return nil }
        let xs = patch.map { $0 % pc }, ys = patch.map { $0 / pc }
        let box = Double((xs.max()! - xs.min()! + 1) * (ys.max()! - ys.min()! + 1))
        let share = Double(patch.count) / Double(cells)
        guard share >= minimumShare, Double(patch.count) / box >= minimumFill else { return nil }

        // the patch's brightness as one series, timed against the wave finely
        var sum = [Double](repeating: 0, count: n)
        for c in patch { for k in 0..<n { sum[k] += Double(series[c * n + k]) } }
        let signal = normalized(sum.map { Float($0) })
        let lags = Array(stride(from: 0.0, through: longest + 1e-9, by: fineStep))
        let scores = lags.map { lag -> Double in
            let reference = normalized(times.map { Float(SportsGlow.wave($0 - lag)) })
            var dot: Float = 0
            for k in 0..<n { dot += signal[k] * reference[k] }
            return Double(dot)
        }
        guard let peak = scores.indices.max(by: { scores[$0] < scores[$1] }) else { return nil }
        var delay = lags[peak]
        if peak > 0, peak < scores.count - 1 {   // between the two neighbours, on the parabola through the three
            let a = scores[peak - 1], b = scores[peak], c = scores[peak + 1], bend = a - 2 * b + c
            if bend < 0 { delay += fineStep * max(-0.5, min(0.5, 0.5 * (a - c) / bend)) }
        }
        let at = SIMD2((Double(xs.reduce(0, +)) / Double(patch.count) + 0.5) / Double(pc), (Double(ys.reduce(0, +)) / Double(patch.count) + 0.5) / Double(pr))
        return Reading(at: at, delay: max(0, delay), match: scores[peak], share: share)
    }

    private static func normalized(_ v: [Float]) -> [Float] {
        guard !v.isEmpty else { return v }
        let mean = v.reduce(0, +) / Float(v.count)
        var out = v.map { $0 - mean }
        let length = out.reduce(0) { $0 + $1 * $1 }.squareRoot()
        if length > 0 { for i in out.indices { out[i] /= length } }
        return out
    }
}

/// The circle: fills while every phone sharing the TV sees it, drains when one does not. Kept by the phone whose game is on the TV;
/// every other phone shows that phone's progress.
struct SportsGlowFill: Equatable {
    /// Seconds to fill with every reading steady; readings that wander fill at `wandering` of that speed. A circle nobody is on drains
    /// at `drain` of a full circle a second.
    static let seconds = 2.6, wandering = 0.35, drain = 0.35
    /// Steady: the last few delays agree this closely (seconds).
    static let steadySpread = 0.02
    private(set) var progress = 0.0
    private(set) var done = false
    /// This phone's readings while the circle fills (delays without gameFrameLead), and the directions it pointed (radians).
    private(set) var delays = [Double]()
    private(set) var headings = [Double]()

    /// A reading from this phone's camera while it sees the TV.
    mutating func add(delay: Double?, heading: Double?) {
        guard !done else { return }
        if let delay, delay.isFinite { delays.append(delay); if delays.count > 30 { delays.removeFirst() } }
        if let heading, heading.isFinite { headings.append(heading); if headings.count > 150 { headings.removeFirst() } }
    }
    var steady: Bool {
        let last = delays.suffix(6)
        guard last.count >= 4, let low = last.min(), let high = last.max() else { return false }
        return high - low < Self.steadySpread
    }
    /// `dt` seconds passed; `everyoneOn`: every phone sharing the TV sees it now.
    mutating func step(_ dt: Double, everyoneOn: Bool) {
        guard !done, dt.isFinite, dt > 0 else { return }
        if everyoneOn {
            progress = min(1, progress + dt * (steady ? 1 : Self.wandering) / Self.seconds)
            if progress >= 1, !delays.isEmpty { done = true }
        } else {
            progress = max(0, progress - dt * Self.drain)
            if progress == 0 { delays.removeAll(); headings.removeAll() }
        }
    }
    /// The TV's delay: the median reading (seconds, without gameFrameLead).
    var delay: Double? {
        guard !delays.isEmpty else { return nil }
        let sorted = delays.sorted()
        return sorted[sorted.count / 2]
    }
    /// Where the TV is: the mean direction the phone pointed through it (on the circle, so ±180° average properly).
    var heading: Double? { SportsGlowFill.meanHeading(headings) }
    static func meanHeading(_ headings: [Double]) -> Double? {
        guard !headings.isEmpty else { return nil }
        return atan2(headings.map { sin($0) }.reduce(0, +), headings.map { cos($0) }.reduce(0, +))
    }
}

/// The setup steps a phone shares in the lobby while the circle is up (MultiplayerParticipant.setupStep).
enum SportsGlowStep {
    /// This phone sees the TV ("glow:on") or not ("glow:off"); the TV phone adds the circle's progress in percent ("glow:on:40").
    static func encode(seeing: Bool, progress: Int?) -> String { "glow:\(seeing ? "on" : "off")" + (progress.map { ":\($0)" } ?? "") }
    static func seeing(_ step: String?) -> Bool? {
        guard let step, step.hasPrefix("glow:") else { return nil }
        return step.hasPrefix("glow:on")
    }
    static func progress(_ step: String?) -> Double? {
        guard let step, step.hasPrefix("glow:"), let last = step.split(separator: ":").last, let percent = Double(last) else { return nil }
        return max(0, min(1, percent / 100))
    }
    /// The TV phone's circle is full (it said so, or it has moved on past it).
    static let done = "glowDone"
    static func pastCircle(_ step: String?) -> Bool {
        guard let step else { return false }
        return [done, "pointed", "timing", "ready", "quick"].contains(step) || step.hasPrefix("go:") || step.hasPrefix("check:")
    }
}
