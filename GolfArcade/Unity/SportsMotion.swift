import AVFoundation
import CoreMotion
import Vision
import os
import simd

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
    /// The log files to share (Settings › Send diagnostics): every .log in Documents, SportsDiagnostics.log first.
    static var files: [URL] {
        let docs=FileManager.default.urls(for:.documentDirectory,in:.userDomainMask)[0]
        let logs=((try? FileManager.default.contentsOfDirectory(at:docs,includingPropertiesForKeys:nil)) ?? []).filter { $0.pathExtension=="log" }
        return logs.sorted { a,b in a.lastPathComponent=="SportsDiagnostics.log" || (b.lastPathComponent != "SportsDiagnostics.log" && a.lastPathComponent<b.lastPathComponent) }
    }
    /// What jetsam counts (phys_footprint) and what is left before this app's limit: "footprint=2310MB left=1650MB".
    static var memory: String {
        var info=task_vm_info_data_t()
        var count=mach_msg_type_number_t(MemoryLayout<task_vm_info_data_t>.size/MemoryLayout<integer_t>.size)
        let status=withUnsafeMutablePointer(to:&info) { $0.withMemoryRebound(to:integer_t.self,capacity:Int(count)) { task_info(mach_task_self_,task_flavor_t(TASK_VM_INFO),$0,&count) } }
        let footprint=status==KERN_SUCCESS ? "\(info.phys_footprint/1_048_576)MB" : "?"
        return "footprint=\(footprint) left=\(os_proc_available_memory()/1_048_576)MB"
    }
}

/// Tracking is graded, not a boolean: degraded must warn, not end the rally. Play reads only the motion sensors, which do not
/// drop out, so a live sample is always `good`; the grades stay for the screens and Unity's flags.
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

/// Phone motion for the sports: the motion sensors (swings, grip, racket-face aim, how far a stroke starts above or below the
/// Ready height) and, only while tennis is set up, the rear camera: it finds the TV while the court direction is captured, and
/// times the TV's delay. No ARKit (App Review 2026-11-07, Guideline 4.2.1: an app that uses ARKit is judged as an AR app); the
/// camera is plain AVFoundation, and nothing in play needs it.
///
/// Threading. Everything time-critical runs on `queue`, a serial high-priority queue of its
/// own: latest-sensor polling, camera frames, swing detection and the sample handed to Unity.
/// It used to run on the main thread, which Unity renders on, so a swing could sit behind a
/// frame being drawn before Unity heard of it. Samples now go to the bridge (a mutex-guarded
/// ring) the moment they are read, and Unity takes the newest at the start of its next frame.
/// The screens get their updates on the main thread. State below is only touched on `queue`;
/// the public methods hop onto it.
final class SportsMotion: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate, @unchecked Sendable {
    /// The court direction is a heading in the motion sensors' reference frame: it holds for as long as device motion keeps
    /// running, which it does from the capture until `stop()`.
    private static let signKey="sports.tennis.steerSign"
    /// The scan is forgiving (user 2026-11-08: it "looks for the most perfect angle possible"; the TV in the window should do):
    /// a short hold, a hand's ordinary shake allowed, and a miss only takes back what it lasted instead of starting over.
    private static let holdRequired=0.5
    private static let maxLensPitch=60.0*Double.pi/180
    private static let maxGateRotation=1.2
    /// The TV must have been seen this recently for the direction hold to keep counting (Vision misses the odd frame).
    private static let screenGrace=0.8
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
    /// The rear camera, running only while it is wanted (`runCamera`): aiming at the TV, and timing the TV's delay.
    private let capture = AVCaptureSession()
    /// Starting and stopping the camera blocks for a moment: never on `queue`.
    private let cameraQueue = DispatchQueue(label: "sports.camera")
    private var cameraConfigured = false, cameraWanted = false
    private let motion = CMMotionManager()
    private var filter = SteeringFilter()
    /// When the last camera frame (the capture) and the last motion sample arrived, on the shared clock.
    private var frameAt = -Double.infinity, sampleAt = -Double.infinity
    private var nextCameraNotice = 0.0
    private var tennis = false, calibrated = false
    /// How far the phone has risen or dropped lately: a stroke starting well above the Ready height is a lob, below it a slice.
    private var vertical = SportsVerticalTravel()
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
    private var nextDiagnostic=0.0, nextPreview=0.0
    private var capturingAxis=false, gateHeld=0.0, gateCheckedAt = -Double.infinity, lastRotation=0.0, captureStartedAt=0.0
    private var gate = SportsAxisGate()
    /// The TV in the camera image (SportsScreenFinder), searched off `queue` while the direction is captured.
    private let screenQueue = DispatchQueue(label: "sports.screen", qos: .userInitiated)
    private var screenLookInFlight=false, nextScreenLook=0.0, screenSeenAt = -Double.infinity
    private var screenProblem=SportsScreenFinder.lookingMessage
    /// Where the TV was last seen (0...1 in the camera image, origin top-left) and the image's shape: the court direction is taken
    /// through it, and the delay probe watches it there. The middle until it is found.
    private var screenAt=SIMD2<Double>(0.5,0.5), screenImage=SIMD2<Double>(4,3)
    /// tan of half the camera's field of view across the image's width (its format's own, read when the camera is configured).
    private var cameraTanHalfWidth=tan(35*Double.pi/180)
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
        queue.async { self.startOnQueue(tennis: tennis, travel: travel) }
    }

    private func startOnQueue(tennis: Bool, travel: Double) {
        calibrated = !tennis; self.tennis=tennis; filter=SteeringFilter(); filter.travel=travel
        filter.tennisStroke = tennis
        SportsDiagnostics.write("motion start tennis=\(tennis) axisLocked=\(gate.locked)")
        guard motion.isDeviceMotionAvailable else { report("Motion sensors unavailable on this phone."); return }
        startDeviceMotion()
    }

    /// The rear camera, a frame of which the TV search and the delay probe each read. On from the court direction's capture (or a
    /// delay probe) until Ready, `stop()` or a cancelled capture; off in play.
    /// On `queue`; the session itself starts and stops on `cameraQueue`.
    private func runCamera(_ on: Bool) {
        guard on != cameraWanted else { return }
        cameraWanted = on
        if on { frameAt = -Double.infinity }
        cameraQueue.async { [self] in
            if on {
                guard configureCamera() else { report("The rear camera is unavailable, so the TV can't be found. Set the court direction by hand."); return }
                if !capture.isRunning { capture.startRunning() }
            } else if capture.isRunning { capture.stopRunning() }
            SportsDiagnostics.write("camera \(on ? "on" : "off")")
        }
    }

    /// Once, on `cameraQueue`: the back wide camera at a small 60 fps format, frames in the YCbCr layout the TV search and the
    /// delay probe read, delivered on `queue`.
    private func configureCamera() -> Bool {
        if cameraConfigured { return true }
        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let input = try? AVCaptureDeviceInput(device: device) else { return false }
        capture.beginConfiguration(); defer { capture.commitConfiguration() }
        capture.sessionPreset = .inputPriority
        guard capture.canAddInput(input) else { return false }
        capture.addInput(input)
        let output = AVCaptureVideoDataOutput()
        output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarFullRange]
        output.alwaysDiscardsLateVideoFrames = true
        output.setSampleBufferDelegate(self, queue: queue)
        guard capture.canAddOutput(output) else { return false }
        capture.addOutput(output)
        if let format = Self.leanestFormat(device), (try? device.lockForConfiguration()) != nil {
            // 60 fps: the delay probe interpolates between frames, so a faster camera times the TV more finely
            device.activeFormat = format
            device.activeVideoMinFrameDuration = CMTime(value: 1, timescale: 60); device.activeVideoMaxFrameDuration = CMTime(value: 1, timescale: 60)
            device.unlockForConfiguration()
        }
        cameraConfigured = true
        let fov = Double(device.activeFormat.videoFieldOfView)   // degrees, across the image's width
        if fov > 10 && fov < 170 { queue.async { self.cameraTanHalfWidth = tan(fov / 2 * Double.pi / 180) } }
        SportsDiagnostics.write("camera configured format=\(device.activeFormat.formatDescription.dimensions.width)x\(device.activeFormat.formatDescription.dimensions.height) fov=\(fov)")
        return true
    }

    /// The smallest full-range format at least 640 wide that runs at 60 fps.
    private static func leanestFormat(_ device: AVCaptureDevice) -> AVCaptureDevice.Format? {
        device.formats.filter { format in
            let size = format.formatDescription.dimensions
            return CMFormatDescriptionGetMediaSubType(format.formatDescription) == kCVPixelFormatType_420YpCbCr8BiPlanarFullRange
                && size.width >= 640 && format.videoSupportedFrameRateRanges.contains { $0.maxFrameRate >= 60 && $0.minFrameRate <= 60 }
        }.min { a, b in
            let x = a.formatDescription.dimensions, y = b.formatDescription.dimensions
            return Int(x.width) * Int(x.height) < Int(y.width) * Int(y.height)
        }
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
        guard AVCaptureDevice.authorizationStatus(for: .video) == .authorized else {
            AVCaptureDevice.requestAccess(for: .video) { [weak self] allowed in
                if allowed { self?.beginAxisCapture(travel:travel) }
                else { self?.report("Camera permission denied. Finding your TV needs the rear camera.") }
            }
            return
        }
        queue.async {
            self.tennis=true; self.filter=SteeringFilter(); self.filter.travel=travel; self.filter.tennisStroke=true
            self.capturingAxis=true; self.gateHeld=0; self.gateCheckedAt = -Double.infinity; self.captureStartedAt=SportsRuntime.shared().clock()
            self.screenSeenAt = -Double.infinity; self.screenProblem=SportsScreenFinder.lookingMessage; self.nextScreenLook=0
            self.screenAt=SIMD2(0.5,0.5)
            self.gate=SportsAxisGate(); self.publish(self.gate)
            self.runCamera(true)
            self.startDeviceMotion()
            SportsDiagnostics.write("axis capture begin")
        }
    }

    func cancelAxisCapture() {
        queue.async { self.capturingAxis=false; self.gateHeld=0; if !self.probing { self.runCamera(false) } }
    }
    /// Reuse only the still-running motion reference frame. Never restore a heading from preferences or across a restart of the sensors.
    var hasUsableCourtDirection: Bool {
        queue.sync { gate.locked && tvHeading != nil && motion.isDeviceMotionActive && SportsRuntime.shared().clock() - sampleAt < 1 }
    }

    /// Last resort when the gate will not settle (dark room, awkward pose). Takes the court
    /// direction from where the back of the phone points now, however steady or level it is.
    @discardableResult func forceAxisFromCurrentPose() -> Bool {
        let problem: String? = queue.sync {
            guard let attitude else { return "Motion is starting. Try again in a moment." }
            guard SportsMotionGeometry.heading(SportsMotionGeometry.rotate(SIMD3<Double>(0,0,-1),by:attitude)) != nil else {
                return "Aim the back of the phone roughly at the TV, not straight up or down."
            }
            strokeFacing = -1
            captureTVHeading()
            gate.locked=true; gate.progress=1; gate.message="Court direction set manually."
            capturingAxis=false
            SportsDiagnostics.write("axis forced tvHeading=\(tvHeading ?? .nan) sign=\(sign)")
            publish(gate)
            return nil
        }
        if let problem { report(problem); return false }
        return true
    }

    /// On each camera frame while the direction is captured: the camera says whether the TV is in the picture, the motion sensors
    /// how level and how still the phone is, and where it points (the heading through the TV is kept as the TV's direction).
    private func evaluateGate(time: Double) {
        guard let attitude else {
            gate.progress=0; gate.message="Motion is starting…"; gate.stalledFor=time-captureStartedAt; publish(gate); return
        }
        let lens=SportsMotionGeometry.rotate(SIMD3<Double>(0,0,-1),by:attitude)
        let pitch=SportsMotionGeometry.lensPitch(lens:lens)
        var failure: String?
        if pitch > Self.maxLensPitch { failure="Tilt the phone level — aim the back of it at the TV (currently \(Int(pitch*180/Double.pi))° off level)." }
        // Nothing counts until the camera sees the TV with the game on it: a level, steady phone aimed at a wall used to lock too.
        let screenSeen = time-screenSeenAt <= Self.screenGrace
        if failure == nil && !screenSeen { failure=screenProblem }
        if failure == nil && lastRotation > Self.maxGateRotation { failure="Hold it there for a moment." }
        if failure == nil && SportsMotionGeometry.heading(lens) == nil { failure="Aim the back of the phone at the TV, not at the floor or ceiling." }
        // the hold builds while all is well and a miss takes back only what it lasted (a frame Vision missed does not start it over)
        let step=max(0,min(0.1,time-gateCheckedAt)); gateCheckedAt=time
        gateHeld = failure == nil ? gateHeld+step : max(0,gateHeld-step)
        gate.progress=min(1,gateHeld/Self.holdRequired)
        if let failure {
            gate.message=failure
            gate.detail="\(screenSeen ? "TV seen" : "no TV") · \(Int(pitch*180/Double.pi))° off level"
            gate.stalledFor = capturingAxis ? time-captureStartedAt : 0
            publish(gate); return
        }
        gate.message = gate.progress<1 ? "TV found. Hold it there…" : "Court direction locked."
        gate.detail="\(Int(pitch*180/Double.pi))° off level"
        if gateHeld >= Self.holdRequired {
            strokeFacing = -1
            captureTVHeading()
            gate.locked=true; capturingAxis=false
            // (the camera stays on for the TV's delay, next; Ready turns it off)
            SportsDiagnostics.write("axis locked sign=\(sign) pitch=\(pitch) tvHeading=\(tvHeading ?? .nan)")
        }
        publish(gate)
    }

    /// Search this frame for the TV (at most one search at a time, a few a second), off the sensor queue: Vision takes a few ms.
    private func lookForScreen(_ buffer: CVPixelBuffer, time: Double) {
        guard !screenLookInFlight, time >= nextScreenLook else { return }
        screenLookInFlight=true; nextScreenLook=time+Self.screenLookInterval
        let image=SportsPixelBuffer(buffer:buffer)
        let shape=SIMD2<Double>(Double(CVPixelBufferGetWidth(buffer)),Double(CVPixelBufferGetHeight(buffer)))
        screenQueue.async {
            let sighting=SportsScreenFinder.find(image.buffer)
            self.queue.async {
                self.screenLookInFlight=false
                guard self.capturingAxis else { return }
                switch sighting {
                case .screen(let at): self.screenSeenAt=SportsRuntime.shared().clock(); self.screenAt=at; self.screenImage=shape
                case .missing(let why): self.screenProblem=why
                }
            }
        }
    }

    // MARK: - TV delay probe

    /// While on, record how bright the TV is where the scan found it in the camera image (right after the
    /// axis is aimed at it) for SportsDelayProbe.
    func setDelayProbe(_ on: Bool) {
        queue.async {
            self.probing=on
            // (left on when the probe ends: a retry follows at once, and Ready turns the camera off)
            if on { self.probe=SportsDelayProbe.Samples(); self.runCamera(true) }
        }
    }

    /// The TV's delay behind a white frame the game set at `rendered` (shared clock), from
    /// when the camera saw the TV turn bright. nil if it was not seen clearly.
    func delayAfterFlash(rendered: Double) -> Double? { queue.sync { SportsDelayProbe.delay(probe.series, rendered: rendered) } }

    /// Mean luma over a small square of the image around `at` (0...1, origin top-left; where the scan found the TV): plane 0 of the
    /// camera's YCbCr buffer, sparsely.
    private static func screenLuma(_ buffer: CVPixelBuffer, at: SIMD2<Double>) -> Double? {
        guard CVPixelBufferGetPlaneCount(buffer) > 0 else { return nil }
        CVPixelBufferLockBaseAddress(buffer,.readOnly); defer { CVPixelBufferUnlockBaseAddress(buffer,.readOnly) }
        guard let base=CVPixelBufferGetBaseAddressOfPlane(buffer,0) else { return nil }
        let w=CVPixelBufferGetWidthOfPlane(buffer,0), h=CVPixelBufferGetHeightOfPlane(buffer,0), row=CVPixelBufferGetBytesPerRowOfPlane(buffer,0)
        let pixels=base.assumingMemoryBound(to:UInt8.self)
        let cx=Int(min(0.95,max(0.05,at.x))*Double(w)), cy=Int(min(0.95,max(0.05,at.y))*Double(h))
        var total=0, count=0
        for y in stride(from:max(0,cy-h/20),to:min(h,cy+h/20),by:6) {
            for x in stride(from:max(0,cx-w/20),to:min(w,cx+w/20),by:6) { total+=Int(pixels[y*row+x]); count+=1 }
        }
        return count>0 ? Double(total)/Double(count) : nil
    }

    // MARK: - Per-sample steering

    private func consume(_ sample: CMDeviceMotion) {
        // Core Motion timestamps acquisition, not callback delivery. Rendering or a camera
        // callback can delay this queue; do not turn that backlog into slow detector time
        // or report an old stroke to Unity as if it just happened.
        let now=SportsRuntime.shared().clock()
        guard let time=SportsMotionSampleClock.acquisitionTime(sensor:sample.timestamp,
            uptime:ProcessInfo.processInfo.systemUptime,now:now) else { return }
        sampleAt=time
        let rate=sample.rotationRate
        let speed=sqrt(rate.x*rate.x+rate.y*rate.y+rate.z*rate.z)
        lastRotation=speed
        let aq=sample.attitude.quaternion
        attitude=simd_quatd(ix:aq.x,iy:aq.y,iz:aq.z,r:aq.w)
        let a=sample.userAcceleration, g=sample.gravity
        // up along gravity, gravity itself removed: how the phone is rising or dropping (Core Motion reads in g)
        let gravity=sqrt(g.x*g.x+g.y*g.y+g.z*g.z)
        if gravity > 0.5 { vertical.step(up:-(a.x*g.x+a.y*g.y+a.z*g.z)/gravity*9.81,time:time,still:speed < 0.3) }
        if capturingAxis {
            // the gate moves on camera frames; with none coming, say so instead of sitting on the last message
            if time-max(frameAt,captureStartedAt) > 1, time >= nextCameraNotice {
                nextCameraNotice=time+0.25
                gate.progress=0; gate.message="Camera is not delivering frames yet."; gate.stalledFor=time-captureStartedAt
                publish(gate)
            }
            return
        }
        // Play reads the motion sensors alone, which never drop out: every live sample is good.
        let current=SportsTrackingQuality.good
        let previousPhase=self.filter.phase
        let force=sqrt(a.x*a.x+a.y*a.y+a.z*a.z)
        // (no court position without camera tracking: the player runs to the ball by himself, so steering stays centred)
        let swing=filter.step(position:0,rate:speed,time:time,valid:true,allowSwingWhileUntracked:tennis,acceleration:force)
        if time>=nextDiagnostic {
            nextDiagnostic=time+4
            SportsDiagnostics.write("sensor quality=\(current.rawValue) ready=\(calibrated) axisLocked=\(gate.locked) phase=\(filter.phase.rawValue) lift=\(vertical.lift) rate=\(speed) force=\(force) sign=\(sign) facing=\(strokeFacing)")
        }
        let q=sample.attitude.quaternion
        let screenHeading = attitude.flatMap { SportsMotionGeometry.heading(SportsMotionGeometry.rotate(SIMD3<Double>(0,0,1),by:$0)) }
        if tennis, gate.locked, let tv=tvHeading {
            strokeFacing=SportsMotionGeometry.strokeFacing(screenHeading:screenHeading,tvHeading:tv,previous:strokeFacing)
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
        if let swing { NSLog("[SportsMotion] tennis stroke power=%.2f lift=%.3f",swing,vertical.lift) }
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
            // the lean beside the body came from camera tracking: none now (the game had stopped reading it)
            let handSide: Float = 0
            let lift = tennis ? Float(vertical.lift) : 0
            SportsRuntime.shared().push(SportsSample(version:Int32(SportsSampleVersion),session:token,time:time,
                target:Float(filter.target),power:Float(lastPower),aim:tennis ? Float(faceAim) : 0,
                swing:Int32(swings),swingStart:Int32(filter.onsets),swingAbort:Int32(filter.aborts),flags:flags,
                handSide:handSide,lift:lift,strokeFacing:tennis ? Float(activeStrokeFacing) : 0,
                qx:Float(q.x),qy:Float(q.y),qz:Float(q.z),qw:Float(q.w),rx:Float(rate.x),ry:Float(rate.y),rz:Float(rate.z),
                gx:Float(g.x),gy:Float(g.y),gz:Float(g.z),
                onsetTime:filter.onsetTime,confirmationTime:filter.confirmationTime,abortTime:filter.abortTime))
        }
        // a stroke is over (its samples are out): its own acceleration must not read as the next one's lift
        if previousPhase == .swinging && filter.phase != .swinging { vertical.restart() }
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

    /// The TV's heading right now: through the middle of the TV the camera has just seen (it can sit anywhere in the picture), else
    /// straight out of the phone's back (the lens).
    private func captureTVHeading() {
        guard let attitude else { tvHeading=nil; return }
        let seen = SportsRuntime.shared().clock()-screenSeenAt <= Self.screenGrace
        let ray = seen ? SportsScreenFinder.ray(at:screenAt,image:screenImage,tanHalfWidth:cameraTanHalfWidth) : SIMD3<Double>(0,0,-1)
        tvHeading=SportsMotionGeometry.heading(SportsMotionGeometry.rotate(ray,by:attitude))
        faceNeutral=[0,0]; faceAim=0; aimHistory.removeAll()
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
            filter.calibrate(position:0,time:SportsRuntime.shared().clock())
            vertical.restart()
            calibrated=true
            // Ready: the TV is found and its delay timed, so play needs no camera
            runCamera(false)
            SportsDiagnostics.write("Ready captured tennis=\(tennis) sign=\(sign) tvHeading=\(tvHeading ?? .nan)")
            return nil
        }
        if let problem { if !quiet { report(problem) }; return false }
        return true
    }

    /// Snapshot the grip at the Ready tap, before the next sensor/render frame can move it.
    func golfReadyGrip() -> SIMD4<Double>? {
        queue.sync { attitude?.vector }
    }

    func stop() {
        queue.async {
            self.runCamera(false); self.stopDeviceMotion()
            self.calibrated=false; self.live=false; self.probing=false
            self.capturingAxis=false; self.gate=SportsAxisGate(); self.tvHeading=nil
            self.frameAt = -Double.infinity; self.sampleAt = -Double.infinity
            self.vertical.reset()
        }
    }

    // MARK: - AVCaptureVideoDataOutputSampleBufferDelegate (on `queue`)

    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard cameraWanted, let image=CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        frameAt=SportsRuntime.shared().clock()
        if probing, let luma=Self.screenLuma(image,at:screenAt) {
            // when the frame was taken, on the host clock: the clock the game reports its white frames on (SportsClock)
            let taken=CMSyncConvertTime(CMSampleBufferGetPresentationTimeStamp(sampleBuffer),
                                        from:capture.synchronizationClock ?? CMClockGetHostTimeClock(),to:CMClockGetHostTimeClock())
            if taken.isNumeric { probe.add(time:taken.seconds,luma:luma) }
        }
        if capturingAxis { lookForScreen(image, time:frameAt); evaluateGate(time:frameAt) }
        if capturingAxis || probing {
            // The viewfinder only matters while aiming at the TV.
            if frameAt>=nextPreview {
                nextPreview=frameAt+0.08
                let picture=SportsPixelBuffer(buffer:image)
                DispatchQueue.main.async { MainActor.assumeIsolated { self.preview?.show(picture.buffer) } }
            }
        }
    }
}

/// A camera image handed to the main thread for the viewfinder (read-only there).
private struct SportsPixelBuffer: @unchecked Sendable { let buffer: CVPixelBuffer }

/// Finds the TV in the camera image while the court direction is captured: a screen-shaped rectangle anywhere in the picture
/// (user 2026-11-08: the TV in the window should scan, no perfect aim) that is lit and shows the game, with detail and colour, not a
/// dark TV, a blank wall, a door or a window frame; or, when Vision finds no such edges (a dark bezel on a dark wall, a TV seen from
/// the side), the middle of the picture glowing with the game. The direction only locks while it is seen, so the scan starts when
/// the court is on the TV in front of the camera.
enum SportsScreenFinder {
    /// `screen`: where the TV's middle is, 0...1 in the camera image (origin top-left).
    enum Sighting: Equatable, Sendable { case screen(SIMD2<Double>), missing(String) }
    /// A patch of the camera image: mean luma (0-255), its spread, and how colourful it is (mean distance of Cb and Cr from grey).
    struct Patch: Equatable, Sendable { var mean = 0.0, spread = 0.0, colour = 0.0 }
    static let lookingMessage = "Looking for your TV. Get the screen with the court on it into the camera window."
    static let darkMessage = "Your TV looks dark. Is the court on it?"
    static let blankMessage = "That doesn't look like the game. Point at the TV showing the court."
    static let minimumMean = 35.0, minimumSpread = 10.0, minimumColour = 4.0   // lenient: a dark room can overexpose the screen
    /// How much brighter than the edge of the picture (the room) its middle must be to count as a glowing screen with no edges found.
    static let glowMargin = 15.0

    /// nil when the patch looks like a lit screen showing the game, else what the player should fix.
    static func problem(_ inside: Patch) -> String? {
        if inside.mean < minimumMean { return darkMessage }
        if inside.spread < minimumSpread || inside.colour < minimumColour { return blankMessage }
        return nil
    }
    /// `box` (0...1, origin top-left) can be the TV: anywhere in the picture, but not the whole picture.
    static func inView(_ box: CGRect) -> Bool { box.width * box.height <= 0.95 }

    /// Searches one camera image (the camera's YCbCr buffer, in the sensor's orientation). Runs Vision synchronously.
    static func find(_ buffer: CVPixelBuffer) -> Sighting {
        let request = VNDetectRectanglesRequest()
        // a 16:9 screen seen at any angle, either way up (the buffer is landscape whatever way the phone is held), near or far
        request.minimumAspectRatio = 0.2; request.maximumAspectRatio = 1
        request.minimumSize = 0.08; request.quadratureTolerance = 45
        request.minimumConfidence = 0.3; request.maximumObservations = 10
        var reason = lookingMessage
        if (try? VNImageRequestHandler(cvPixelBuffer: buffer, orientation: .up).perform([request])) != nil, let found = request.results {
            // nearest the middle first: the TV the phone is pointed at, not a door beside it
            func offCentre(_ r: VNRectangleObservation) -> Double { hypot(r.boundingBox.midX - 0.5, r.boundingBox.midY - 0.5) }
            for rectangle in found.sorted(by: { offCentre($0) < offCentre($1) }) {
                let b = rectangle.boundingBox   // Vision: origin bottom-left
                let box = CGRect(x: b.minX, y: 1 - b.maxY, width: b.width, height: b.height)
                guard inView(box) else { continue }
                // inset past the bezel: only the picture
                guard let inside = patch(buffer, in: box.insetBy(dx: box.width * 0.12, dy: box.height * 0.12)) else { continue }
                if let problem = problem(inside) { reason = problem; continue }
                return .screen(SIMD2(box.midX, box.midY))
            }
        }
        return glowing(buffer) ? .screen(SIMD2(0.5, 0.5)) : .missing(reason)
    }

    /// The middle of the picture looks like a lit screen showing the game and outshines the edge of the picture (the room).
    static func glowing(_ buffer: CVPixelBuffer) -> Bool {
        guard let middle = patch(buffer, in: CGRect(x: 0.3, y: 0.3, width: 0.4, height: 0.4)), problem(middle) == nil else { return false }
        let edges = [CGRect(x: 0, y: 0, width: 1, height: 0.12), CGRect(x: 0, y: 0.88, width: 1, height: 0.12),
                     CGRect(x: 0, y: 0, width: 0.12, height: 1), CGRect(x: 0.88, y: 0, width: 0.12, height: 1)].compactMap { patch(buffer, in: $0) }
        guard !edges.isEmpty else { return false }
        return middle.mean >= edges.map(\.mean).reduce(0, +) / Double(edges.count) + glowMargin
    }

    /// The direction from the phone through point `at` of the camera image (0...1, origin top-left) in the phone's own axes (x right
    /// across the screen, y up it, the rear lens looking down -z), for an image `image` pixels in size whose width spans
    /// 2·atan(`tanHalfWidth`). The image comes in the sensor's landscape orientation, the one the viewfinder turns `.right` for an
    /// upright phone: its rows run down the phone (-y) and its top row is at the screen's right edge (+x).
    static func ray(at: SIMD2<Double>, image: SIMD2<Double>, tanHalfWidth: Double) -> SIMD3<Double> {
        let tanHalfHeight = tanHalfWidth * image.y / max(1, image.x)
        return simd_normalize(SIMD3((0.5 - at.y) * 2 * tanHalfHeight, (0.5 - at.x) * 2 * tanHalfWidth, -1))
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
/// reports (on the shared clock) when it set each white frame. Every camera frame is stamped
/// on the host clock, that same clock, so the delay is simply when the camera saw the TV turn bright,
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
