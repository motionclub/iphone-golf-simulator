import ARKit
import CoreMotion
import Vision

// Bounded, local-only diagnostics: no camera images or player identity.
enum SportsDiagnostics {
    private static let queue=DispatchQueue(label:"sports.diagnostics")
    static func write(_ message:String) {
        NSLog("[SportsDiagnostic] %@",message)
        let line="\(Date().timeIntervalSince1970) \(message)\n"
        queue.async {
            let url=FileManager.default.urls(for:.documentDirectory,in:.userDomainMask)[0].appendingPathComponent("SportsDiagnostics.log")
            if !FileManager.default.fileExists(atPath:url.path) { FileManager.default.createFile(atPath:url.path,contents:nil) }
            guard let handle=try? FileHandle(forWritingTo:url) else { return }
            defer { try? handle.close() }
            if let end=try? handle.seekToEnd(), end>1_048_576 {   // 1 MB: at 256 KB the file held only the last few minutes of play
                // Keep the most recent half rather than wiping the file: a full reset throws
                // away the Ready and axis-lock lines that explain everything after them.
                try? handle.seek(toOffset:end/2)
                let kept=(try? handle.readToEnd()) ?? nil
                try? handle.truncate(atOffset:0); try? handle.seek(toOffset:0)
                if let kept { try? handle.write(contentsOf:kept) }
            }
            if let data=line.data(using:.utf8) { try? handle.write(contentsOf:data) }
        }
    }
}

/// Tracking is graded, not a boolean. A hard swing blurs the camera and ARKit drops to
/// `.limited` for a fraction of a second; that must warn, not end the rally.
enum SportsTrackingQuality: String, Sendable { case good, degraded, lost }

/// Live state of the aim-at-the-TV gate that locks the court axis before play.
struct SportsAxisGate: Sendable {
    var locked = false
    var progress = 0.0          // 0...1 once every condition holds
    var message = "Hold still to begin."
    /// Live sensor readout, so a gate that refuses to settle can be diagnosed on the spot.
    var detail = ""
    /// Seconds the gate has been failing, used to offer a manual override.
    var stalledFor = 0.0
}

/// What the screens need from the sensors: posted to the main thread when it changes, and at
/// most ten times a second otherwise. Unity never waits on this; it gets samples directly.
struct SportsMotionStatus: Equatable, Sendable {
    var target = 0.0
    var phase = "calibrating"
    var quality = SportsTrackingQuality.lost
    var valid = false
}

/// Phone motion for the sports: the motion sensors (swings, grip, racket-face aim) and ARKit
/// world tracking (court position, and the court axis captured once by aiming at the TV).
///
/// Threading. Everything time-critical runs on `queue`, a serial high-priority queue of its
/// own: latest-sensor polling, ARKit frames, swing detection and the sample handed to Unity.
/// It used to run on the main thread, which Unity renders on, so a swing could sit behind a
/// frame being drawn before Unity heard of it. Samples now go to the bridge (a mutex-guarded
/// ring) the moment they are read, and Unity takes the newest at the start of its next frame.
/// The screens get their updates on the main thread. State below is only touched on `queue`;
/// the public methods hop onto it.
final class SportsMotion: NSObject, ARSessionDelegate, @unchecked Sendable {
    /// The court axis only survives while ARKit keeps the same world origin. Everything here
    /// is built so `resetTracking` happens exactly once, at axis capture.
    private static let signKey="sports.tennis.steerSign"
    private static let holdRequired=1.0
    private static let maxLensPitch=60.0*Double.pi/180
    private static let maxGateRotation=0.5
    private static let degradedGrace=2.0
    /// The TV must have been seen this recently for the direction hold to keep counting (Vision misses the odd frame).
    private static let screenGrace=0.5
    /// How often the camera image is searched for the TV while the direction is captured.
    private static let screenLookInterval=0.12

    private let queue = DispatchQueue(label: "sports.motion", qos: .userInteractive)
    /// CoreMotion delivers here, so every sample is handled on `queue` the moment it is measured.
    private lazy var motionDelivery: OperationQueue = {
        let delivery = OperationQueue()
        delivery.underlyingQueue = queue; delivery.maxConcurrentOperationCount = 1
        return delivery
    }()
    /// A sample this old when its turn comes is skipped: after a stall the queue catches up on the present, not the past.
    private static let staleSample = 0.06
    private var lastSensorTimestamp = -Double.infinity
    private let ar = ARSession()
    private let motion = CMMotionManager()
    private var filter = SteeringFilter()
    private var position = SIMD3<Float>.zero, right = SIMD3<Float>(1,0,0)
    private var interrupted=false
    private var frameAt = -Double.infinity, reliableAt = -Double.infinity
    private var tennis = false, calibrated = false
    private var neutralX=0.0, neutralY:Float=0
    /// Horizontal direction toward the TV, fixed when the axis locks.
    private var courtForward = SIMD3<Float>(0,0,-1)
    /// Direction out of the screen, updated every frame; compared against `courtForward`.
    private var screenNormal = SIMD3<Float>(0,0,1)
    private var strokeFacing = -1.0
    private var activeStrokeFacing = -1.0
    /// Latest motion-sensor attitude, and the heading of the TV in that frame (captured when
    /// the axis locks). Grip and racket-face aim are read from these, never the camera.
    private var attitude: simd_quatd?
    private var tvHeading: Double?
    /// Each player's habitual face angle per wing (forehand, backhand), learnt as they play.
    private var faceNeutral = [0.0, 0.0]
    private var aimProfile: TennisAimProfile?
    private var aimHistory = [(time:Double,angle:Double,wing:Int)]()
    private var faceAim = 0.0
    /// Distance to the TV from the depth sensor while the axis is being captured.
    private var tvDistance: Double?
    private var nextDiagnostic=0.0, nextPreview=0.0, trackingReason="not started"
    private var worldRunning=false
    private var capturingAxis=false, gateHeldSince = -Double.infinity, lastRotation=0.0, captureStartedAt=0.0
    private var gate = SportsAxisGate()
    /// The TV in the camera image (SportsScreenFinder), searched off `queue` while the direction is captured.
    private let screenQueue = DispatchQueue(label: "sports.screen", qos: .userInitiated)
    private var screenLookInFlight=false, nextScreenLook=0.0, screenSeenAt = -Double.infinity
    private var screenProblem=SportsScreenFinder.lookingMessage
    private var sign: Double = UserDefaults.standard.object(forKey:SportsMotion.signKey) as? Double ?? 1
    /// Recent rate/force history, written out around each stroke candidate so the detection
    /// thresholds can be tuned from real swings instead of reasoning. Fixed size, no growth.
    private var trace = [(Double,Double,Double)](repeating:(0,0,0),count:80)
    private var traceHead = 0, traceOnsets = 0, traceDue = Double.infinity
    private var traceOutcome = ""
    // Output to Unity.
    private var token: Int32 = 0, live = false, swings = 0, lastPower = 0.0
    private var swingContacts = 0
    private var status = SportsMotionStatus(), nextStatusAt = 0.0
    // Delay probe: centre-of-frame brightness while the camera is aimed at the TV.
    private var probing = false
    private var probe = SportsDelayProbe.Samples()

    /// The screens' callbacks, always called on the main thread.
    @MainActor var onProblem: ((String) -> Void)?
    @MainActor var onGate: ((SportsAxisGate) -> Void)?
    @MainActor var onStatus: ((SportsMotionStatus) -> Void)?
    @MainActor var onAimSwing: ((TennisAimSwing) -> Void)?
    @MainActor weak var preview: SportsPreviewView?

    /// Flips left/right without recapturing the axis, for when the mapping comes out mirrored.
    var courtSign: Double {
        get { queue.sync { sign } }
        set { UserDefaults.standard.set(newValue,forKey:Self.signKey); queue.async { self.sign=newValue } }
    }
    #if DEBUG
    /// Tests stand in for the camera and motion sensors: the court direction reads as locked and Ready always takes a centre.
    var fixtureSensors = false
    #endif
    var axisLocked: Bool {
        #if DEBUG
        if fixtureSensors { return true }
        #endif
        return queue.sync { gate.locked }
    }
    /// Exposed so the aiming screen can show a viewfinder from this same session.
    var previewSession: ARSession { ar }

    // MARK: - Main-thread callbacks

    private func report(_ message: String) {
        DispatchQueue.main.async { MainActor.assumeIsolated { self.onProblem?(message) } }
    }
    private func publish(_ gate: SportsAxisGate) {
        DispatchQueue.main.async { MainActor.assumeIsolated { self.onGate?(gate) } }
    }
    private func publish(_ status: SportsMotionStatus) {
        DispatchQueue.main.async { MainActor.assumeIsolated { self.onStatus?(status) } }
    }

    // MARK: - Session lifecycle

    func start(tennis: Bool, travel: Double) {
        if tennis && AVCaptureDevice.authorizationStatus(for: .video) != .authorized {
            AVCaptureDevice.requestAccess(for: .video) { [weak self] allowed in
                if allowed { self?.start(tennis:true,travel:travel) }
                else { self?.report("Camera permission denied. Physical steering needs the rear camera.") }
            }
            return
        }
        queue.async { self.startOnQueue(tennis: tennis, travel: travel) }
    }

    private func startOnQueue(tennis: Bool, travel: Double) {
        calibrated = !tennis; self.tennis=tennis; filter=SteeringFilter(); filter.travel=travel
        filter.tennisStroke = tennis
        SportsDiagnostics.write("motion start tennis=\(tennis) axisLocked=\(gate.locked)")
        guard motion.isDeviceMotionAvailable else { report("Motion sensors unavailable on this phone."); return }
        if tennis {
            guard ARWorldTrackingConfiguration.isSupported else { report("Physical steering is unsupported on this phone."); return }
            runWorldTracking(reset: !worldRunning)
        }
        startDeviceMotion()
    }

    /// Reset only when there is no locked axis to protect. Relocalizing into the existing
    /// map is what keeps "right" pointing the same way for the whole session.
    private func runWorldTracking(reset: Bool, depth: Bool = false) {
        let configuration=ARWorldTrackingConfiguration()
        configuration.worldAlignment = .gravity
        // No plane detection: nothing uses planes, and finding them costs every frame.
        configuration.planeDetection = []
        if depth && ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth) {
            // LiDAR depth only while aiming at the TV, to measure how far away the player is.
            configuration.frameSemantics.insert(.sceneDepth)
        } else if let lean = Self.leanestFormat() {
            // During play only the phone's position is needed: the smallest image at the full
            // frame rate leaves the most room for the game and the AirPlay encoder.
            configuration.videoFormat = lean
        }
        ar.delegate=self; ar.delegateQueue = queue
        ar.run(configuration,options: reset ? [.resetTracking,.removeExistingAnchors] : [])
        worldRunning=true
        if reset { gate.locked=false }
        SportsDiagnostics.write("world tracking run reset=\(reset) depth=\(depth) format=\(configuration.videoFormat.imageResolution)@\(configuration.videoFormat.framesPerSecond)")
    }

    /// Lowest-resolution world-tracking format among those at the highest frame rate.
    private static func leanestFormat() -> ARConfiguration.VideoFormat? {
        let formats = ARWorldTrackingConfiguration.supportedVideoFormats
        guard let fastest = formats.map(\.framesPerSecond).max() else { return nil }
        return formats.filter { $0.framesPerSecond == fastest }
            .min { $0.imageResolution.width * $0.imageResolution.height < $1.imageResolution.width * $1.imageResolution.height }
    }

    private func startDeviceMotion() {
        guard !motion.isDeviceMotionActive else { return }
        motion.deviceMotionUpdateInterval=0.01
        // Z vertical with long-term yaw correction: the racket-face heading has to stay
        // anchored to the TV direction for a whole match.
        let frame: CMAttitudeReferenceFrame = CMMotionManager.availableAttitudeReferenceFrames().contains(.xArbitraryCorrectedZVertical)
            ? .xArbitraryCorrectedZVertical : .xArbitraryZVertical
        // Every sample as it is measured (100 Hz, the iPhone's ceiling). A 10 ms timer reading the latest value beat
        // against the sensor's own clock: a sample was sometimes read twice and sometimes never (two landed between
        // ticks), so a fast swing could lose its peak, and each sample waited 0-10 ms for its tick. A stalled queue still
        // never plays through a backlog of old arm motion: anything `staleSample` old by its turn is skipped.
        lastSensorTimestamp = -Double.infinity
        motion.startDeviceMotionUpdates(using:frame, to:motionDelivery) { [weak self] sample, _ in
            guard let self, let sample, sample.timestamp>self.lastSensorTimestamp else { return }
            self.lastSensorTimestamp=sample.timestamp
            guard ProcessInfo.processInfo.systemUptime-sample.timestamp <= Self.staleSample else { return }
            self.consume(sample)
        }
    }

    private func stopDeviceMotion() {
        motion.stopDeviceMotionUpdates()
        motionDelivery.cancelAllOperations()
    }

    // MARK: - Output to Unity

    /// Where samples go and whether they flow: `live` while a motion-controlled session is
    /// playing (not paused). `swingBase` continues the swing count.
    func setAimProfile(_ profile: TennisAimProfile?) {
        queue.sync { aimProfile=profile?.valid == true ? profile : nil; aimHistory.removeAll(); faceAim=0 }
    }
    func setOutput(token: Int32, live: Bool, swingBase: Int) {
        queue.async { self.token=token; self.live=live; self.swings=max(self.swings,swingBase) }
    }
    /// Swings counted so far.
    var swingCount: Int { queue.sync { swings } }

    // MARK: - Aim-at-the-TV gate

    /// Forget the court direction, so the next match captures it again (Settings → Controls).
    func clearAxis() {
        queue.async { self.gate=SportsAxisGate(); self.publish(self.gate) }
    }

    /// Begin capturing the court axis. Tennis cannot start until this locks, because a phone
    /// that flips between forehand and backhand can never reveal where the TV is mid-rally.
    func beginAxisCapture(travel: Double) {
        guard ARWorldTrackingConfiguration.isSupported else { report("Physical steering is unsupported on this phone."); return }
        guard AVCaptureDevice.authorizationStatus(for: .video) == .authorized else {
            AVCaptureDevice.requestAccess(for: .video) { [weak self] allowed in
                if allowed { self?.beginAxisCapture(travel:travel) }
                else { self?.report("Camera permission denied. Physical steering needs the rear camera.") }
            }
            return
        }
        queue.async {
            self.tennis=true; self.filter=SteeringFilter(); self.filter.travel=travel; self.filter.tennisStroke=true
            self.capturingAxis=true; self.gateHeldSince = -Double.infinity; self.captureStartedAt=SportsRuntime.shared().clock()
            self.screenSeenAt = -Double.infinity; self.screenProblem=SportsScreenFinder.lookingMessage; self.nextScreenLook=0
            self.gate=SportsAxisGate(); self.publish(self.gate)
            self.runWorldTracking(reset: true, depth: true)
            self.startDeviceMotion()
            SportsDiagnostics.write("axis capture begin")
        }
    }

    func cancelAxisCapture() { queue.async { self.capturingAxis=false; self.gateHeldSince = -Double.infinity } }
    /// Reuse only the still-running AR/IMU origin. Never restore a heading from preferences or across tracking resets.
    var hasUsableCourtDirection: Bool {
        queue.sync {
            guard gate.locked, worldRunning, motion.isDeviceMotionActive, !interrupted,
                  SportsRuntime.shared().clock() - frameAt < 1,
                  let frame = ar.currentFrame, case .normal = frame.camera.trackingState else { return false }
            return true
        }
    }

    /// Last resort when the gate will not settle (dark room, awkward pose). Takes the axis
    /// from the current pose regardless of how steady or level it is. Left/right may come
    /// out mirrored, which is what the flip control is for.
    @discardableResult func forceAxisFromCurrentPose() -> Bool {
        let problem: String? = queue.sync {
            guard let frame=ar.currentFrame else { return "No camera frame yet. Keep the lens uncovered." }
            let back=frame.camera.transform.columns.2
            guard let axis=SportsMotionGeometry.horizontalRight(cameraBack:SIMD3<Float>(back.x,back.y,back.z)) else {
                return "Aim the back of the phone roughly at the TV, not straight up or down."
            }
            right=axis
            if let forward=SportsMotionGeometry.horizontal(SIMD3<Float>(back.x,back.y,back.z)) { courtForward = -forward }
            strokeFacing = -1
            captureTVHeading()
            gate.locked=true; gate.progress=1; gate.message="Court direction set manually."
            capturingAxis=false
            SportsDiagnostics.write("axis forced right=\(right) sign=\(sign)")
            publish(gate)
            return nil
        }
        if let problem { report(problem); return false }
        return true
    }

    private func evaluateGate(frame: ARFrame, time: Double) {
        let back=frame.camera.transform.columns.2
        let cameraBack=SIMD3<Float>(back.x,back.y,back.z)
        let pitch=SportsMotionGeometry.lensPitch(cameraBack:cameraBack)
        var failure: String?
        if case .notAvailable = frame.camera.trackingState {
            failure="Camera is not delivering frames yet."
        }
        if failure == nil && pitch > Self.maxLensPitch { failure="Tilt the phone level — aim the back of it straight at the TV (currently \(Int(pitch*180/Double.pi))° off level)." }
        // Nothing counts until the camera sees the TV with the game on it: a level, steady phone aimed at a wall used to lock too.
        let screenSeen = time-screenSeenAt <= Self.screenGrace
        if failure == nil && !screenSeen { failure=screenProblem }
        if failure == nil && lastRotation > Self.maxGateRotation { failure="Hold still for a moment." }
        tvDistance = Self.centreDepth(frame)
        // LiDAR may see a laptop's desk or bezel. Distance is guidance, not a
        // requirement for the horizontal court direction to be measured.
        if failure == nil && SportsMotionGeometry.horizontalRight(cameraBack:cameraBack) == nil { failure="Aim the back of the phone at the TV, not at the floor or ceiling." }
        guard failure == nil, let axis=SportsMotionGeometry.horizontalRight(cameraBack:cameraBack) else {
            gateHeldSince = -Double.infinity
            gate.progress=0; gate.message=failure ?? gate.message
            gate.detail="Tracking \(trackingReason) · \(screenSeen ? "TV seen" : "no TV") · \(Int(pitch*180/Double.pi))° off level" + (tvDistance.map { String(format:" · %.1f m from TV",$0) } ?? "")
            gate.stalledFor = capturingAxis ? time-captureStartedAt : 0
            publish(gate); return
        }
        if gateHeldSince == -Double.infinity { gateHeldSince=time }
        let held=time-gateHeldSince
        gate.progress=min(1,held/Self.holdRequired)
        gate.message = gate.progress<1 ? "TV found. Hold it there…" : "Court direction locked."
        gate.detail="Tracking \(trackingReason) · \(Int(pitch*180/Double.pi))° off level" + (tvDistance.map { String(format:" · %.1f m from TV",$0) } ?? "")
        if held >= Self.holdRequired {
            right=axis
            // The lens points at the TV right now, and the screen points away from it.
            if let forward=SportsMotionGeometry.horizontal(cameraBack) { courtForward = -forward }
            strokeFacing = -1
            captureTVHeading()
            gate.locked=true; capturingAxis=false
            // Depth was only for the distance check; drop it for the rest of the session.
            runWorldTracking(reset: false)
            SportsDiagnostics.write("axis locked right=\(right) forward=\(courtForward) sign=\(sign) pitch=\(pitch) tvHeading=\(tvHeading ?? .nan) distance=\(tvDistance ?? -1)")
        }
        publish(gate)
    }

    /// Search this frame for the TV (at most one search at a time, a few a second), off the sensor queue: Vision takes a few ms.
    private func lookForScreen(_ frame: ARFrame, time: Double) {
        guard !screenLookInFlight, time >= nextScreenLook else { return }
        screenLookInFlight=true; nextScreenLook=time+Self.screenLookInterval
        let image=SportsPixelBuffer(buffer:frame.capturedImage)
        screenQueue.async {
            let sighting=SportsScreenFinder.find(image.buffer)
            self.queue.async {
                self.screenLookInFlight=false
                guard self.capturingAxis else { return }
                switch sighting {
                case .screen: self.screenSeenAt=SportsRuntime.shared().clock()
                case .missing(let why): self.screenProblem=why
                }
            }
        }
    }

    // MARK: - TV delay probe

    /// While on, record how bright the middle of the camera image is (the TV, right after the
    /// axis is aimed at it) for SportsDelayProbe.
    func setDelayProbe(_ on: Bool) { queue.async { self.probing=on; if on { self.probe=SportsDelayProbe.Samples() } } }

    /// The TV's delay behind a white frame the game set at `rendered` (shared clock), from
    /// when the camera saw the TV turn bright. nil if it was not seen clearly.
    func delayAfterFlash(rendered: Double) -> Double? { queue.sync { SportsDelayProbe.delay(probe.series, rendered: rendered) } }

    /// Mean luma over the middle of the image: plane 0 of ARKit's YCbCr buffer, sparsely.
    private static func centreLuma(_ buffer: CVPixelBuffer) -> Double? {
        guard CVPixelBufferGetPlaneCount(buffer) > 0 else { return nil }
        CVPixelBufferLockBaseAddress(buffer,.readOnly); defer { CVPixelBufferUnlockBaseAddress(buffer,.readOnly) }
        guard let base=CVPixelBufferGetBaseAddressOfPlane(buffer,0) else { return nil }
        let w=CVPixelBufferGetWidthOfPlane(buffer,0), h=CVPixelBufferGetHeightOfPlane(buffer,0), row=CVPixelBufferGetBytesPerRowOfPlane(buffer,0)
        let pixels=base.assumingMemoryBound(to:UInt8.self)
        var total=0, count=0
        for y in stride(from:h*45/100,to:h*55/100,by:6) {
            for x in stride(from:w*45/100,to:w*55/100,by:6) { total+=Int(pixels[y*row+x]); count+=1 }
        }
        return count>0 ? Double(total)/Double(count) : nil
    }

    // MARK: - Per-sample steering

    private func consume(_ sample: CMDeviceMotion) {
        // Core Motion timestamps acquisition, not callback delivery. Rendering or an AR
        // callback can delay this queue; do not turn that backlog into slow detector time
        // or report an old stroke to Unity as if it just happened.
        let now=SportsRuntime.shared().clock()
        guard let time=SportsMotionSampleClock.acquisitionTime(sensor:sample.timestamp,
            uptime:ProcessInfo.processInfo.systemUptime,now:now) else { return }
        let rate=sample.rotationRate
        let speed=sqrt(rate.x*rate.x+rate.y*rate.y+rate.z*rate.z)
        lastRotation=speed
        let aq=sample.attitude.quaternion
        attitude=simd_quatd(ix:aq.x,iy:aq.y,iz:aq.z,r:aq.w)
        guard !capturingAxis else { return }
        let current=currentQuality(at:time)
        // Only `good` advances the fixed real-world→court mapping. `degraded` holds the last
        // court position and keeps the rally alive; `lost` is what finally pauses play.
        let tracked = !tennis || current == .good
        let x=Double(simd_dot(position,right))*sign
        // Swings never depend on the camera: a sideways or flat swing blurs or blinds it, but
        // the gyro reads it perfectly. Camera loss only holds the lean/steering hint.
        let grace = tennis
        let previousPhase=self.filter.phase
        let a=sample.userAcceleration
        let force=sqrt(a.x*a.x+a.y*a.y+a.z*a.z)
        let swing=filter.step(position:x,rate:speed,time:time,valid:tracked,allowSwingWhileUntracked:grace,acceleration:force)
        if time>=nextDiagnostic {
            nextDiagnostic=time+4
            SportsDiagnostics.write("sensor quality=\(current.rawValue) ar=\(trackingReason) frameAge=\(time-frameAt) reliableAge=\(time-reliableAt) ready=\(calibrated) axisLocked=\(gate.locked) phase=\(filter.phase.rawValue) delta=\(x-neutralX) target=\(filter.target) reachL=\(filter.reachLeft) reachR=\(filter.reachRight) seenL=\(filter.seenLeft) seenR=\(filter.seenRight) rate=\(speed) force=\(force) sign=\(sign) facing=\(strokeFacing)")
        }
        let q=sample.attitude.quaternion, g=sample.gravity
        let screenHeading = attitude.flatMap { SportsMotionGeometry.heading(SportsMotionGeometry.rotate(SIMD3<Double>(0,0,1),by:$0)) }
        if tennis, gate.locked {
            if let tv=tvHeading { strokeFacing=SportsMotionGeometry.strokeFacing(screenHeading:screenHeading,tvHeading:tv,previous:strokeFacing) }
            else { strokeFacing=SportsMotionGeometry.strokeFacing(screenNormal:screenNormal,courtForward:courtForward,previous:strokeFacing) }
        }
        if previousPhase != .swinging && filter.phase == .swinging { activeStrokeFacing=strokeFacing }
        // Use the same short filtered racket-face window for practice and live shots.
        // Profiles stay fixed throughout a match; follow-through cannot re-learn "straight".
        let swinging = filter.phase == .swinging || swing != nil
        let facing = swinging ? activeStrokeFacing : strokeFacing
        let wing = facing >= 0 ? 0 : 1
        if tennis, let tv=tvHeading, let screen=screenHeading {
            let angle=SportsMotionGeometry.faceAngle(screenHeading:screen,tvHeading:tv,facing:facing)
            aimHistory.append((time,angle,wing))
        }
        aimHistory.removeAll { time-$0.time > 0.06 }
        if aimHistory.count > 8 { aimHistory.removeFirst(aimHistory.count-8) }
        let recent=aimHistory.filter { $0.wing == wing }
        var filteredAngle:Double?
        if let latest=recent.last {
            let offsets=recent.map { TennisAimWing.relative($0.angle,to:latest.angle) }.sorted()
            let angle=latest.angle+offsets[offsets.count/2]
            filteredAngle=angle
            faceAim=(aimProfile ?? TennisAimProfile(forehand:.standard,backhand:.standard)).aim(angle:angle,facing:facing)
        }
        // The racket in the hand is at the ball: a strike the game has already decided is felt now, from this queue.
        if filter.contacts>swingContacts { swingContacts=filter.contacts; if live && tennis { RacketFeel.swingReachedBall() } }
        if let swing { NSLog("[SportsMotion] tennis stroke power=%.2f",swing) }
        recordTrace(time:time,rate:speed,force:force,swing:swing)
        let valid = tennis ? calibrated : current != .lost
        // Straight to Unity, from this queue: no hop through the main thread.
        if live {
            if let swing {
                lastPower=swing; swings+=1
                if let angle=filteredAngle {
                    let aimSwing=TennisAimSwing(time:time,angle:angle,facing:activeStrokeFacing)
                    Task { @MainActor [weak self] in self?.onAimSwing?(aimSwing) }
                }
            }
            var flags:Int32 = valid ? Int32(SportsSampleValid) : 0
            if current != .good { flags |= Int32(SportsSampleDegraded) }
            if tennis && filter.peakConfirm { flags |= Int32(SportsSamplePrediction) }
            let handSide = tracked ? Float(x-neutralX-filter.target*filter.travel) : 0
            let lift = tracked ? Float(position.y-neutralY) : 0
            SportsRuntime.shared().push(SportsSample(version:Int32(SportsSampleVersion),session:token,time:time,
                target:Float(filter.target),power:Float(lastPower),aim:tennis ? Float(faceAim) : 0,
                swing:Int32(swings),swingStart:Int32(filter.onsets),swingAbort:Int32(filter.aborts),flags:flags,
                handSide:handSide,lift:lift,strokeFacing:tennis ? Float(activeStrokeFacing) : 0,
                qx:Float(q.x),qy:Float(q.y),qz:Float(q.z),qw:Float(q.w),rx:Float(rate.x),ry:Float(rate.y),rz:Float(rate.z),
                gx:Float(g.x),gy:Float(g.y),gz:Float(g.z),
                onsetTime:filter.onsetTime,confirmationTime:filter.confirmationTime,abortTime:filter.abortTime))
        }
        // The screens only need the gist, and not every hundredth of a second.
        let next = SportsMotionStatus(target:filter.target,phase:filter.phase.rawValue,quality:current,valid:valid)
        if next.phase != status.phase || next.quality != status.quality || next.valid != status.valid || time>=nextStatusAt {
            status=next; nextStatusAt=time+0.1
            publish(next)
        }
    }

    /// Log the 0.8s of rate and force around each stroke candidate, with how it ended.
    private func recordTrace(time:Double,rate:Double,force:Double,swing:Double?) {
        guard tennis else { return }
        trace[traceHead]=(time,rate,force); traceHead=(traceHead+1)%trace.count
        if filter.onsets>traceOnsets { traceOnsets=filter.onsets; traceDue=time+0.4; traceOutcome="aborted" }
        if let swing { traceOutcome=String(format:"confirmed power=%.2f at=%@ afterPeak=%.0fms",swing,filter.confirmedAtPeak ? "peak" : "proof",(filter.confirmationTime-filter.peakTime)*1000) }
        guard time>=traceDue else { return }
        traceDue = .infinity
        var line="swingtrace outcome=\(traceOutcome) onsets=\(filter.onsets) aborts=\(filter.aborts) t,rate,force:"
        for i in 0..<trace.count {
            let (t,r,f)=trace[(traceHead+i)%trace.count]
            if t>0 { line+=String(format:" %.3f,%.1f,%.2f",t,r,f) }
        }
        SportsDiagnostics.write(line)
    }

    /// Heading of the phone's back (the lens) right now: at axis lock it points at the TV.
    private func captureTVHeading() {
        guard let attitude else { tvHeading=nil; return }
        tvHeading=SportsMotionGeometry.heading(SportsMotionGeometry.rotate(SIMD3<Double>(0,0,-1),by:attitude))
        faceNeutral=[0,0]; faceAim=0; aimHistory.removeAll()
    }

    /// Median LiDAR depth over the middle of the frame: the distance to whatever the lens is
    /// aimed at, i.e. the TV during axis capture. nil without a depth sensor or a reading.
    private static func centreDepth(_ frame: ARFrame) -> Double? {
        guard let map=frame.sceneDepth?.depthMap else { return nil }
        CVPixelBufferLockBaseAddress(map,.readOnly); defer { CVPixelBufferUnlockBaseAddress(map,.readOnly) }
        guard let base=CVPixelBufferGetBaseAddress(map) else { return nil }
        let w=CVPixelBufferGetWidth(map), h=CVPixelBufferGetHeight(map), row=CVPixelBufferGetBytesPerRow(map)
        var values=[Float]()
        for y in (h/2-4)...(h/2+4) {
            let line=base.advanced(by:y*row).assumingMemoryBound(to:Float32.self)
            for x in (w/2-4)...(w/2+4) { let d=line[x]; if d.isFinite && d>0.2 { values.append(d) } }
        }
        guard values.count>10 else { return nil }
        values.sort()
        return Double(values[values.count/2])
    }

    private func currentQuality(at time: Double) -> SportsTrackingQuality {
        guard tennis else { return .good }
        if interrupted { return .lost }
        let frameAge=time-frameAt
        if frameAge>Self.degradedGrace || time-reliableAt>Self.degradedGrace { return .lost }
        if trackingReason.contains("notAvailable") { return .lost }
        if frameAge<0.25 && time-reliableAt<0.25 { return .good }
        return .degraded
    }

    /// `quiet` keeps a failure to ourselves: used to re-centre at the moment an online match starts, where a missed frame
    /// must not pause the match for both players (the centre taken at Ready stays).
    @discardableResult func calibrate(quiet: Bool = false) -> Bool {
        #if DEBUG
        if fixtureSensors { return true }
        #endif
        let problem: String? = queue.sync {
            guard motion.isDeviceMotionActive else { return "Motion is starting. Tap Ready again in a moment." }
            guard !tennis || gate.locked else { return "Aim the back of the phone at the TV to set the court direction first." }
            // A laptop screen can leave ARKit short of features. The locked heading and
            // IMU still support swings; positional steering resumes when tracking recovers.
            guard !tennis || SportsRuntime.shared().clock() - frameAt < 1 else {
                return "No recent camera frame. Keep the rear camera uncovered, then tap Ready."
            }
            let x=Double(simd_dot(position,right))*sign
            filter.calibrate(position:x,time:SportsRuntime.shared().clock())
            neutralX=x; neutralY=position.y
            calibrated=true
            SportsDiagnostics.write("Ready captured tennis=\(tennis) axis=\(right) sign=\(sign) target=\(filter.target)")
            return nil
        }
        if let problem { if !quiet { report(problem) }; return false }
        return true
    }

    /// Snapshot the grip at the Ready tap, before the next sensor/render frame can move it.
    func golfReadyGrip() -> SIMD4<Double>? {
        queue.sync { attitude?.vector }
    }

    /// Stop steering but keep the world map, so the locked axis survives menus and pauses.
    func suspend() { queue.async { self.stopDeviceMotion(); self.calibrated=false } }

    func stop() {
        queue.async {
            self.ar.pause(); self.stopDeviceMotion()
            self.interrupted=false; self.calibrated=false; self.live=false; self.probing=false
            self.worldRunning=false; self.capturingAxis=false; self.gate=SportsAxisGate()
            self.frameAt = -Double.infinity; self.reliableAt = -Double.infinity
        }
    }

    // MARK: - ARSessionDelegate (on `queue`)

    func session(_ session: ARSession, didUpdate frame: ARFrame) {
        position=SIMD3(frame.camera.transform.columns.3.x,frame.camera.transform.columns.3.y,frame.camera.transform.columns.3.z)
        let out=frame.camera.transform.columns.2
        screenNormal=SIMD3<Float>(out.x,out.y,out.z)
        trackingReason=String(describing:frame.camera.trackingState)
        interrupted=false
        frameAt=SportsRuntime.shared().clock()
        if case .normal = frame.camera.trackingState { reliableAt=frameAt }
        if probing, let luma=Self.centreLuma(frame.capturedImage) { probe.add(time:frame.timestamp,luma:luma) }
        if capturingAxis { lookForScreen(frame, time:frameAt); evaluateGate(frame:frame,time:frameAt) }
        if capturingAxis || probing {
            // The viewfinder only matters while aiming at the TV.
            if frameAt>=nextPreview {
                nextPreview=frameAt+0.08
                let image=SportsPixelBuffer(buffer:frame.capturedImage)
                DispatchQueue.main.async { MainActor.assumeIsolated { self.preview?.show(image.buffer) } }
            }
        }
    }
    func session(_ session: ARSession, didFailWithError error: Error) { interrupted=true; report(error.localizedDescription) }
    func sessionWasInterrupted(_ session: ARSession) {
        interrupted=true
        SportsDiagnostics.write("ar interrupted")
    }
    /// Resume into the *existing* map. A reset here would silently invalidate the locked
    /// court axis and send the player sideways for the rest of the session.
    func sessionInterruptionEnded(_ session: ARSession) {
        SportsDiagnostics.write("ar interruption ended; relocalizing into existing map")
        runWorldTracking(reset: false)
    }
}

/// A camera image handed to the main thread for the viewfinder (read-only there).
private struct SportsPixelBuffer: @unchecked Sendable { let buffer: CVPixelBuffer }

/// Finds the TV in the camera image while the court direction is captured: a screen-shaped rectangle holding the middle of the frame
/// (the phone is aimed at it) that is lit and shows the game, with detail and colour, not a dark TV, a blank wall, a door or a
/// window frame. The direction only locks while it is seen, so the scan starts when the court is on the TV in front of the camera.
enum SportsScreenFinder {
    enum Sighting: Equatable, Sendable { case screen, missing(String) }
    /// A patch of the camera image: mean luma (0-255), its spread, and how colourful it is (mean distance of Cb and Cr from grey).
    struct Patch: Equatable, Sendable { var mean = 0.0, spread = 0.0, colour = 0.0 }
    static let lookingMessage = "Looking for your TV. Point the back of your phone at the screen with the court on it."
    static let centreMessage = "Keep your TV in the middle of the camera."
    static let darkMessage = "Your TV looks dark. Is the court on it?"
    static let blankMessage = "That doesn't look like the game. Point at the TV showing the court."
    static let minimumMean = 35.0, minimumSpread = 10.0, minimumColour = 4.0   // lenient: a dark room can overexpose the screen
    /// The middle of the frame may sit this far (a share of the rectangle's size) outside it.
    static let aimSlack = 0.1

    /// nil when the patch looks like a lit screen showing the game, else what the player should fix.
    static func problem(_ inside: Patch) -> String? {
        if inside.mean < minimumMean { return darkMessage }
        if inside.spread < minimumSpread || inside.colour < minimumColour { return blankMessage }
        return nil
    }
    /// The phone is aimed at `box` (0...1, origin top-left): the middle of the frame is in it, give or take `aimSlack`, and it is not
    /// the whole picture.
    static func aimed(at box: CGRect) -> Bool {
        guard box.width * box.height <= 0.95 else { return false }
        return box.insetBy(dx: -box.width * aimSlack, dy: -box.height * aimSlack).contains(CGPoint(x: 0.5, y: 0.5))
    }

    /// Searches one camera image (ARKit's YCbCr buffer, in the sensor's orientation). Runs Vision synchronously.
    static func find(_ buffer: CVPixelBuffer) -> Sighting {
        let request = VNDetectRectanglesRequest()
        // a 16:9 screen seen at an angle, either way up (the buffer is landscape whatever way the phone is held)
        request.minimumAspectRatio = 0.35; request.maximumAspectRatio = 0.9
        request.minimumSize = 0.12; request.quadratureTolerance = 30
        request.minimumConfidence = 0.5; request.maximumObservations = 6
        guard (try? VNImageRequestHandler(cvPixelBuffer: buffer, orientation: .up).perform([request])) != nil,
              let found = request.results, !found.isEmpty else { return .missing(lookingMessage) }
        var reason = centreMessage
        for rectangle in found.sorted(by: { $0.boundingBox.width * $0.boundingBox.height > $1.boundingBox.width * $1.boundingBox.height }) {
            let b = rectangle.boundingBox   // Vision: origin bottom-left
            let box = CGRect(x: b.minX, y: 1 - b.maxY, width: b.width, height: b.height)
            guard aimed(at: box) else { continue }
            // inset past the bezel: only the picture
            guard let inside = patch(buffer, in: box.insetBy(dx: box.width * 0.12, dy: box.height * 0.12)) else { continue }
            if let problem = problem(inside) { reason = problem; continue }
            return .screen
        }
        return .missing(reason)
    }

    /// Luma and colour over `box` (0...1, origin top-left), sparsely.
    static func patch(_ buffer: CVPixelBuffer, in box: CGRect) -> Patch? {
        guard CVPixelBufferGetPlaneCount(buffer) > 0 else { return nil }
        CVPixelBufferLockBaseAddress(buffer, .readOnly); defer { CVPixelBufferUnlockBaseAddress(buffer, .readOnly) }
        guard let lumaBase = CVPixelBufferGetBaseAddressOfPlane(buffer, 0) else { return nil }
        let w = CVPixelBufferGetWidthOfPlane(buffer, 0), h = CVPixelBufferGetHeightOfPlane(buffer, 0), row = CVPixelBufferGetBytesPerRowOfPlane(buffer, 0)
        let luma = lumaBase.assumingMemoryBound(to: UInt8.self)
        // plane 1: Cb and Cr interleaved at half resolution (absent: colour is not judged)
        let chroma = CVPixelBufferGetPlaneCount(buffer) > 1 ? CVPixelBufferGetBaseAddressOfPlane(buffer, 1)?.assumingMemoryBound(to: UInt8.self) : nil
        let chromaRow = chroma != nil ? CVPixelBufferGetBytesPerRowOfPlane(buffer, 1) : 0
        let x0 = max(0, Int(box.minX * Double(w))), x1 = min(w, Int(box.maxX * Double(w)))
        let y0 = max(0, Int(box.minY * Double(h))), y1 = min(h, Int(box.maxY * Double(h)))
        guard x1 > x0, y1 > y0 else { return nil }
        let stepX = max(1, (x1 - x0) / 24), stepY = max(1, (y1 - y0) / 24)
        var count = 0.0, sum = 0.0, squares = 0.0, colour = 0.0
        for y in stride(from: y0, to: y1, by: stepY) {
            for x in stride(from: x0, to: x1, by: stepX) {
                let l = Double(luma[y * row + x]); sum += l; squares += l * l; count += 1
                if let chroma {
                    let c = (y / 2) * chromaRow + (x / 2) * 2
                    colour += (abs(Double(chroma[c]) - 128) + abs(Double(chroma[c + 1]) - 128)) / 2
                }
            }
        }
        guard count > 0 else { return nil }
        let mean = sum / count
        return Patch(mean: mean, spread: sqrt(max(0, squares / count - mean * mean)), colour: chroma != nil ? colour / count : minimumColour)
    }
}

/// Measuring how far the TV's picture lags the game, with the phone's own camera.
///
/// During setup the phone is aimed at the TV. The game blanks the TV black, then white, and
/// reports (on the shared clock) when it set each white frame. ARKit timestamps every camera
/// frame on that same clock, so the delay is simply when the camera saw the TV turn bright,
/// minus when the game drew it: AirPlay, the Apple TV and the TV's own processing, all in.
enum SportsDelayProbe {
    struct Samples {
        private(set) var times = [Double]()
        private(set) var values = [Double]()
        mutating func add(time: Double, luma: Double) {
            times.append(time); values.append(luma)
            if times.count > 600 { times.removeFirst(100); values.removeFirst(100) }
        }
        var series: [(Double, Double)] { Array(zip(times, values)) }
    }

    /// Plausible delays: anything outside this is a misread, not a TV.
    static let shortest = 0.01, longest = 1.0
    /// The flash must move the camera's reading by at least this much (0-255 luma).
    static let minimumContrast = 22.0

    /// Delay for one flash: in the window around it, find the darkest reading (the black
    /// frame on screen), the brightest after it (the white), and when the brightness first
    /// crossed halfway between them, interpolated between camera frames.
    static func delay(_ series: [(Double, Double)], rendered: Double) -> Double? {
        let window = series.filter { $0.0 >= rendered - 0.25 && $0.0 <= rendered + longest + 0.05 }
        guard window.count >= 6 else { return nil }
        // Each pulse has a long black lead-in, so the first frames are the baseline.
        // Searching for the darkest frame anywhere can pick the *end* of a white pulse.
        let baseline = window.prefix(6).map(\.1).sorted()
        let dark = baseline[baseline.count / 2]
        guard let bright = window.map(\.1).max(), bright - dark >= minimumContrast else { return nil }
        let half = (dark + bright) / 2
        guard let cross = window.indices.dropFirst().first(where: {
            window[$0 - 1].1 < half && window[$0].1 >= half && window[$0].0 >= rendered + shortest
        }) else { return nil }
        let (t1, v1) = window[cross - 1], (t2, v2) = window[cross]
        let t = v2 > v1 ? t1 + (t2 - t1) * (half - v1) / (v2 - v1) : t2
        let delay = t - rendered
        return delay >= shortest && delay <= longest ? delay : nil
    }

    /// Median of the flashes that were read, once at least two agree.
    static func combine(_ delays: [Double]) -> Double? {
        guard delays.count >= 2 else { return nil }
        let sorted = delays.sorted()
        let median = sorted[sorted.count / 2]
        let agreeing = sorted.filter { abs($0 - median) <= 0.06 }
        guard agreeing.count >= 2 else { return nil }
        return agreeing[agreeing.count / 2]
    }
}
