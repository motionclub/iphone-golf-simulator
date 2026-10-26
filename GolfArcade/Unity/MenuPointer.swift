import CoreMotion
import Foundation
import simd

/// The pointer menu's maths (PLAN_PointerMenu.md), pure so tests can drive it: the phone's attitude relative to where it pointed at
/// Recenter becomes a cursor position on the TV, x and y in -1...1 (+y up).
///
/// The pointing axis is picked at Recenter: the phone's top edge (+Y) when it is held like a remote, or its back (-Z) when it is held
/// upright like a camera. Turning `yawRange` degrees reaches the side of the screen, tilting `pitchRange` the top (16:9). Past an
/// edge the reference slides along, so the cursor never sticks off screen and a few swings re-centre it naturally. A One Euro filter
/// takes out the hand's tremor without adding much lag to a quick move.
struct MenuPointerMath {
    var yawRange = 20.0, pitchRange = 11.25
    private(set) var yaw0 = 0.0, pitch0 = 0.0, useBack = false, centred = false
    private var fx = OneEuro(), fy = OneEuro()

    /// The pointing axis in the reference frame (z up) for attitude `q`.
    private func axis(_ q: simd_quatd, back: Bool) -> SIMD3<Double> { q.act(back ? SIMD3(0, 0, -1) : SIMD3(0, 1, 0)) }
    private static func angles(_ v: SIMD3<Double>) -> (yaw: Double, pitch: Double) {
        let h = (v.x * v.x + v.y * v.y).squareRoot()
        return (atan2(v.y, v.x) * 180 / .pi, atan2(v.z, h) * 180 / .pi)
    }
    private static func wrap(_ a: Double) -> Double { var a = a.truncatingRemainder(dividingBy: 360); if a > 180 { a -= 360 }; if a < -180 { a += 360 }; return a }

    /// Here is the middle of the TV.
    mutating func recenter(_ q: simd_quatd) {
        // held upright (the top edge points at the sky or the floor): point with the back of the phone instead
        useBack = abs(axis(q, back: false).z) > 0.8
        let a = Self.angles(axis(q, back: useBack)); yaw0 = a.yaw; pitch0 = a.pitch; centred = true
        fx = OneEuro(); fy = OneEuro()
    }

    /// The cursor for attitude `q` at time `t` (seconds).
    mutating func point(_ q: simd_quatd, at t: Double) -> (x: Double, y: Double) {
        if !centred { recenter(q) }
        let a = Self.angles(axis(q, back: useBack))
        // turning right (clockwise seen from above) lowers the yaw: the cursor goes right
        var x = -Self.wrap(a.yaw - yaw0) / yawRange, y = (a.pitch - pitch0) / pitchRange
        // edge drag: past an edge the reference follows the phone
        if x > 1 { yaw0 = Self.wrap(yaw0 - (x - 1) * yawRange); x = 1 }
        if x < -1 { yaw0 = Self.wrap(yaw0 + (-1 - x) * yawRange); x = -1 }
        if y > 1 { pitch0 += (y - 1) * pitchRange; y = 1 }
        if y < -1 { pitch0 -= (-1 - y) * pitchRange; y = -1 }
        return (fx.filter(x, t), fy.filter(y, t))
    }

    /// One Euro filter (Casiez 2012): low cutoff when still (no jitter), higher with speed (little lag).
    struct OneEuro {
        var minCutoff = 1.0, beta = 0.02, dCutoff = 1.0
        private var last: (t: Double, x: Double, dx: Double)?
        static func alpha(_ cutoff: Double, _ dt: Double) -> Double { let tau = 1 / (2 * .pi * cutoff); return 1 / (1 + tau / dt) }
        mutating func filter(_ x: Double, _ t: Double) -> Double {
            guard let l = last, t > l.t else { last = (t, x, 0); return x }
            let dt = t - l.t
            let dx = (x - l.x) / dt
            let edx = l.dx + Self.alpha(dCutoff, dt) * (dx - l.dx)
            let cutoff = minCutoff + beta * abs(edx) * 100   // (beta per unit / s in screen halves)
            let out = l.x + Self.alpha(cutoff, dt) * (x - l.x)
            last = (t, out, edx); return out
        }
    }
}

/// The pointer's motion source: device motion at 100 Hz on its own queue, each reading pushed straight to Unity on the binary sample
/// channel (no main-thread hop), flagged MenuPointer. Runs only while the menu is up, this phone drives it and the app is in front; a
/// match's own motion (SportsMotion) never runs at the same time.
final class MenuPointerSource: @unchecked Sendable {
    static let shared = MenuPointerSource()
    private let manager = CMMotionManager()
    private let queue: OperationQueue = { let q = OperationQueue(); q.name = "menu.pointer"; q.maxConcurrentOperationCount = 1; q.qualityOfService = .userInteractive; return q }()
    private let lock = NSLock()
    private var math = MenuPointerMath()
    private var token: Int32 = 0, presses: Int32 = 0, held = false, wantCentre = true, running = false
    private var last = (x: 0.0, y: 0.0)
    /// The newest cursor (for the phone's own label and tests).
    var position: (x: Double, y: Double) { lock.lock(); defer { lock.unlock() }; return last }
    var isRunning: Bool { lock.lock(); defer { lock.unlock() }; return running }

    func start(token: Int32) {
        lock.lock(); self.token = token; let was = running; running = true; wantCentre = true; lock.unlock()
        guard !was, manager.isDeviceMotionAvailable else { return }
        manager.deviceMotionUpdateInterval = 1.0 / 100
        manager.startDeviceMotionUpdates(using: .xArbitraryZVertical, to: queue) { [weak self] motion, _ in
            guard let self, let motion else { return }
            self.handle(motion)
        }
    }
    func stop() {
        lock.lock(); let was = running; running = false; lock.unlock()
        if was { manager.stopDeviceMotionUpdates(); push(x: 0, y: 0, shown: false) }
    }
    /// The phone points at the middle of the TV now.
    func recenter() { lock.lock(); wantCentre = true; lock.unlock() }
    /// The Select pad went down (true) or up (false).
    func select(_ down: Bool) {
        lock.lock(); if down && !held { presses &+= 1 }; held = down; let p = last; lock.unlock()
        push(x: p.x, y: p.y, shown: true)   // the press goes out at once, not with the next motion reading
    }

    private func handle(_ motion: CMDeviceMotion) {
        let a = motion.attitude.quaternion
        let q = simd_quatd(ix: a.x, iy: a.y, iz: a.z, r: a.w)
        // stale readings (the app was paused) are not pointed with
        guard ProcessInfo.processInfo.systemUptime - motion.timestamp < 0.06 else { return }
        lock.lock()
        if wantCentre { math.recenter(q); wantCentre = false }
        let p = math.point(q, at: motion.timestamp); last = p
        lock.unlock()
        push(x: p.x, y: p.y, shown: true)
    }

    private func push(x: Double, y: Double, shown: Bool) {
        lock.lock(); let token = token, presses = presses, held = held; lock.unlock()
        guard token != 0 else { return }
        let sample = SportsSample(version: Int32(SportsSampleVersion), session: token, time: SportsRuntime.shared().clock(),
            target: Float(x), power: shown ? 1 : 0, aim: Float(y),
            swing: held ? 1 : 0, swingStart: presses, swingAbort: 0, flags: Int32(SportsSampleValid | SportsSampleMenuPointer),
            handSide: 0, lift: 0, strokeFacing: 0, qx: 0, qy: 0, qz: 0, qw: 0, rx: 0, ry: 0, rz: 0, gx: 0, gy: 0, gz: 0,
            onsetTime: 0, confirmationTime: 0, abortTime: 0)
        SportsRuntime.shared().push(sample)
    }

    /// A finger on the phone's own screen (no TV): the same samples, flagged Touch, x / y in -1...1 of the menu's picture.
    func touch(token: Int32, x: Double, y: Double, down: Bool, shown: Bool) {
        lock.lock(); self.token = token; if down && !held { presses &+= 1 }; held = down; last = (x, y); let p = presses; lock.unlock()
        let sample = SportsSample(version: Int32(SportsSampleVersion), session: token, time: SportsRuntime.shared().clock(),
            target: Float(x), power: shown ? 1 : 0, aim: Float(y),
            swing: down ? 1 : 0, swingStart: p, swingAbort: 0, flags: Int32(SportsSampleValid | SportsSampleMenuPointer | SportsSampleTouch),
            handSide: 0, lift: 0, strokeFacing: 0, qx: 0, qy: 0, qz: 0, qw: 0, rx: 0, ry: 0, rz: 0, gx: 0, gy: 0, gz: 0,
            onsetTime: 0, confirmationTime: 0, abortTime: 0)
        SportsRuntime.shared().push(sample)
    }
}
