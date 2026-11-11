import AVFoundation
import CoreMotion
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
    /// Two blinks of the TV must put it in the same direction, this closely, for the court direction to lock (radians).
    private static let flashAgreement=6.0*Double.pi/180

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
    private var capturingAxis=false, lastRotation=0.0, captureStartedAt=0.0, nextGateNotice=0.0
    private var gate = SportsAxisGate()
    /// The scan (SportsScreenFinder): the last few seconds of camera frames, shrunk, each with the phone's attitude when it was taken;
    /// where each blink of the TV put it (a heading) with the delay it showed; and, once two agree, their delays for the session.
    private var scanFrames=[SportsScreenFinder.Frame](), scanRows=0
    private var flashSightings=[(heading:Double,delay:Double)](), scanDelays=[Double]()
    /// Where the TV was last seen (0...1 in the camera image, origin top-left) and the image's shape: the delay probe watches it
    /// there. The middle until it is found.
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
            self.capturingAxis=true; self.captureStartedAt=SportsRuntime.shared().clock(); self.nextGateNotice=0
            self.scanFrames.removeAll(); self.flashSightings.removeAll(); self.scanDelays.removeAll()
            self.screenAt=SIMD2(0.5,0.5)
            self.gate=SportsAxisGate(); self.gate.message=SportsScreenFinder.lookingMessage; self.publish(self.gate)
            self.runCamera(true)
            self.startDeviceMotion()
            SportsDiagnostics.write("axis capture begin")
        }
    }

    func cancelAxisCapture() {
        queue.async { self.capturingAxis=false; self.scanFrames.removeAll(); if !self.probing { self.runCamera(false) } }
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
            capturingAxis=false; scanFrames.removeAll(); scanDelays.removeAll()
            SportsDiagnostics.write("axis forced tvHeading=\(tvHeading ?? .nan) sign=\(sign)")
            publish(gate)
            return nil
        }
        if let problem { report(problem); return false }
        return true
    }

    /// On each camera frame while the direction is captured: kept, shrunk, for the blink search, with the phone's attitude then.
    private func scanFrame(_ buffer: CVPixelBuffer, taken: Double, time: Double) {
        if let grid=SportsScreenFinder.grid(buffer) {
            if grid.rows != scanRows { scanRows=grid.rows; scanFrames.removeAll() }
            scanFrames.append(.init(time:taken,cells:grid.cells,attitude:attitude))
            if scanFrames.count > 240 { scanFrames.removeFirst(60) }   // 4 s at 60 fps
            screenImage=SIMD2(Double(CVPixelBufferGetWidth(buffer)),Double(CVPixelBufferGetHeight(buffer)))
        }
        guard time >= nextGateNotice else { return }
        nextGateNotice=time+0.2
        if attitude == nil { gate.message="Motion is starting…" }
        gate.stalledFor=time-captureStartedAt
        publish(gate)
    }

    /// The game turned the TV white at `rendered` (shared clock), after a second of black: find what part of the camera's picture
    /// turned bright with it. That is the TV, wherever it sits in the picture and whatever else is in the room; its direction is taken
    /// through it with the attitude the phone had in that very frame, so the hand need not hold still; and how long after `rendered`
    /// it turned is the TV's delay. Two blinks that agree lock the court direction.
    func scanFlash(rendered: Double) {
        queue.async { [self] in
            guard capturingAxis else { return }
            guard let seen=SportsScreenFinder.sighting(scanFrames,rows:scanRows,rendered:rendered), let pose=scanFrames[seen.frame].attitude,
                  let heading=SportsMotionGeometry.heading(SportsMotionGeometry.rotate(
                    SportsScreenFinder.ray(at:seen.at,image:screenImage,tanHalfWidth:cameraTanHalfWidth),by:pose)) else {
                gate.message=SportsScreenFinder.missedMessage; gate.detail="blink not seen"
                SportsDiagnostics.write("scan blink missed frames=\(scanFrames.count) rendered=\(rendered) newest=\(scanFrames.last?.time ?? .nan)")
                publish(gate); return
            }
            screenAt=seen.at
            SportsDiagnostics.write(String(format:"scan blink at=%.2f,%.2f heading=%.1f delay=%.0fms",seen.at.x,seen.at.y,heading*180/Double.pi,seen.delay*1000))
            let agreeing=flashSightings.filter { abs(SportsMotionGeometry.wrap(heading-$0.heading)) <= Self.flashAgreement }
            flashSightings.append((heading,seen.delay))
            gate.detail=String(format:"TV delay %.0f ms",seen.delay*1000)
            guard let mate=agreeing.last else {
                gate.progress=0.5; gate.message="TV found. Keep it in the window for one more blink…"
                publish(gate); return
            }
            strokeFacing = -1
            tvHeading=mate.heading+SportsMotionGeometry.wrap(heading-mate.heading)/2
            faceNeutral=[0,0]; faceAim=0; aimHistory.removeAll()
            scanDelays=agreeing.map(\.delay)+[seen.delay]
            gate.locked=true; gate.progress=1; gate.message="Court direction locked."; capturingAxis=false; scanFrames.removeAll()
            // (the camera stays on until Ready turns it off)
            SportsDiagnostics.write("axis locked sign=\(sign) tvHeading=\(tvHeading ?? .nan) delays=\(scanDelays)")
            publish(gate)
        }
    }
    /// The TV's delay as each agreeing blink of the scan showed it (seconds); empty when the direction was set by hand.
    var scannedDelays: [Double] { queue.sync { scanDelays } }

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

    /// The TV's heading taken by hand: straight out of the phone's back (the lens), now.
    private func captureTVHeading() {
        guard let attitude else { tvHeading=nil; return }
        tvHeading=SportsMotionGeometry.heading(SportsMotionGeometry.rotate(SIMD3<Double>(0,0,-1),by:attitude))
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
            self.capturingAxis=false; self.scanFrames.removeAll(); self.gate=SportsAxisGate(); self.tvHeading=nil
            self.frameAt = -Double.infinity; self.sampleAt = -Double.infinity
            self.vertical.reset()
        }
    }

    // MARK: - AVCaptureVideoDataOutputSampleBufferDelegate (on `queue`)

    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard cameraWanted, let image=CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        frameAt=SportsRuntime.shared().clock()
        // when the frame was taken, on the host clock: the clock the game reports its white frames on (SportsClock)
        let stamp=CMSyncConvertTime(CMSampleBufferGetPresentationTimeStamp(sampleBuffer),
                                    from:capture.synchronizationClock ?? CMClockGetHostTimeClock(),to:CMClockGetHostTimeClock())
        let taken=stamp.isNumeric ? stamp.seconds : frameAt
        if probing, let luma=Self.screenLuma(image,at:screenAt) { probe.add(time:taken,luma:luma) }
        if capturingAxis { scanFrame(image,taken:taken,time:frameAt) }
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

/// Finds the TV by making it blink. During the scan the game turns the whole TV black, then white, and says when (the same flash
/// that times the TV's delay); whatever part of the camera's picture turned bright with it is the TV. Nothing else in a room does
/// that on cue, so the TV can sit anywhere in the picture, at any angle, in any light, and a window, a picture frame or a TV that
/// is off can never pass for it.
///
/// 2026-11-10 (user: "try and test different scans until one is easy to scan and actually works"): tried against the ways before it on
/// 228 rendered phone views of 12 rooms (TVs 43-75 in, 1.5-4.5 m, up to 48 deg off axis, phone upright or sideways and tilted, the TV
/// anywhere in the picture; a bright, a dim and a dark room; hand blur, shake and sensor noise). Right direction (within 3 deg) /
/// locked with no TV in view: the rectangle search this replaces 41 % / 43 % (and it took a TV that was off 91 % of the time), the
/// centred rectangle before it 0.4 % / 8 %, a QR code on the TV 66 % (89 % from a 1280 image) / 0, an Aztec code 77 % / 0, the court
/// dimmed and restored 49 % / -, this blink 90 % / 0, the rest within 6 deg.
enum SportsScreenFinder {
    static let lookingMessage = "Point the back of your phone at your TV so it shows in the window. The TV will blink twice."
    static let missedMessage = "Didn't catch the blink. Get the whole TV into the window."
    /// A camera frame for the search: shrunk to `columns` cells across (each the mean luma of its patch), when it was taken (the
    /// game's clock), and the phone's attitude then.
    struct Frame { var time: Double; var cells: [UInt8]; var attitude: simd_quatd? }
    /// The TV in one blink: its middle (0...1 in the camera image, origin top-left), its delay behind the game (seconds), and the
    /// frame it was found in.
    struct Sighting: Equatable { var at: SIMD2<Double>; var delay: Double; var frame: Int }
    static let columns = 80
    /// A cell counts as part of the blink when it rose by this much (0-255 luma) and by half the biggest rise in the picture; the
    /// cells that did must make one patch at least this share of the picture, and fill this much of the box around it (a screen,
    /// not the thin outlines a moving hand leaves around bright things).
    static let minimumRise = 40.0, minimumShare = 0.004, minimumFill = 0.4

    /// The direction from the phone through point `at` of the camera image (0...1, origin top-left) in the phone's own axes (x right
    /// across the screen, y up it, the rear lens looking down -z), for an image `image` pixels in size whose width spans
    /// 2·atan(`tanHalfWidth`). The image comes in the sensor's landscape orientation, the one the viewfinder turns `.right` for an
    /// upright phone: its rows run down the phone (-y) and its top row is at the screen's right edge (+x).
    static func ray(at: SIMD2<Double>, image: SIMD2<Double>, tanHalfWidth: Double) -> SIMD3<Double> {
        let tanHalfHeight = tanHalfWidth * image.y / max(1, image.x)
        return simd_normalize(SIMD3((0.5 - at.y) * 2 * tanHalfHeight, (0.5 - at.x) * 2 * tanHalfWidth, -1))
    }

    /// The camera's YCbCr buffer shrunk to `columns` cells across: plane 0, sixteen samples a cell.
    static func grid(_ buffer: CVPixelBuffer) -> (cells: [UInt8], rows: Int)? {
        guard CVPixelBufferGetPlaneCount(buffer) > 0 else { return nil }
        CVPixelBufferLockBaseAddress(buffer, .readOnly); defer { CVPixelBufferUnlockBaseAddress(buffer, .readOnly) }
        guard let base = CVPixelBufferGetBaseAddressOfPlane(buffer, 0) else { return nil }
        let w = CVPixelBufferGetWidthOfPlane(buffer, 0), h = CVPixelBufferGetHeightOfPlane(buffer, 0), row = CVPixelBufferGetBytesPerRowOfPlane(buffer, 0)
        let cell = w / columns
        guard cell >= 1, h >= cell else { return nil }
        let rows = h / cell, step = max(1, cell / 4)
        let luma = base.assumingMemoryBound(to: UInt8.self)
        var cells = [UInt8](repeating: 0, count: columns * rows)
        for cy in 0..<rows {
            for cx in 0..<columns {
                var sum = 0, count = 0
                for y in stride(from: cy * cell, to: cy * cell + cell, by: step) {
                    for x in stride(from: cx * cell, to: cx * cell + cell, by: step) { sum += Int(luma[y * row + x]); count += 1 }
                }
                cells[cy * columns + cx] = UInt8(sum / max(1, count))
            }
        }
        return (cells, rows)
    }

    /// The one patch of the picture that turned bright from `dark` to `bright` (two grids of `rows` rows): its middle (0...1,
    /// weighted by the rise), its cells, and how much light it gained in all. nil when nothing screen-like did.
    static func brightened(dark: [UInt8], bright: [UInt8], rows: Int) -> (at: SIMD2<Double>, cells: [Int], rise: Double)? {
        let count = columns * rows
        guard rows > 0, dark.count == count, bright.count == count else { return nil }
        var rise = [Double](repeating: 0, count: count), peak = 0.0
        for i in 0..<count { rise[i] = Double(bright[i]) - Double(dark[i]); peak = max(peak, rise[i]) }
        let threshold = max(minimumRise, peak * 0.5)
        guard peak >= threshold else { return nil }
        var visited = [Bool](repeating: false, count: count)
        var best: (cells: [Int], rise: Double)?
        for start in 0..<count where rise[start] >= threshold && !visited[start] {
            var stack = [start], patch = [Int](), total = 0.0
            visited[start] = true
            while let i = stack.popLast() {
                patch.append(i); total += rise[i]
                let x = i % columns, y = i / columns
                if x > 0, !visited[i - 1], rise[i - 1] >= threshold { visited[i - 1] = true; stack.append(i - 1) }
                if x < columns - 1, !visited[i + 1], rise[i + 1] >= threshold { visited[i + 1] = true; stack.append(i + 1) }
                if y > 0, !visited[i - columns], rise[i - columns] >= threshold { visited[i - columns] = true; stack.append(i - columns) }
                if y < rows - 1, !visited[i + columns], rise[i + columns] >= threshold { visited[i + columns] = true; stack.append(i + columns) }
            }
            if patch.count > (best?.cells.count ?? 0) { best = (patch, total) }
        }
        guard let best else { return nil }
        let xs = best.cells.map { $0 % columns }, ys = best.cells.map { $0 / columns }
        let box = Double((xs.max()! - xs.min()! + 1) * (ys.max()! - ys.min()! + 1))
        guard Double(best.cells.count) / Double(count) >= minimumShare, Double(best.cells.count) / box >= minimumFill else { return nil }
        var sx = 0.0, sy = 0.0
        for i in best.cells { sx += (Double(i % columns) + 0.5) * rise[i]; sy += (Double(i / columns) + 0.5) * rise[i] }
        return (SIMD2(sx / best.rise / Double(columns), sy / best.rise / Double(rows)), best.cells, best.rise)
    }

    /// A TV turns white in a frame or two. A bright window or lamp sliding across the picture as the hand moves brightens its patch
    /// gradually: from a quarter to three quarters of the way up must take no longer than this.
    static let snapTime = 0.1
    static func snapped(_ series: [(Double, Double)], after rendered: Double) -> Bool {
        let before = series.filter { $0.0 <= rendered }.map(\.1).sorted()
        guard !before.isEmpty, let top = series.map(\.1).max() else { return false }
        let dark = before[before.count / 2]
        let later = series.filter { $0.0 > rendered }
        guard let low = later.first(where: { $0.1 >= dark + (top - dark) * 0.25 }), let high = later.first(where: { $0.1 >= dark + (top - dark) * 0.75 }) else { return false }
        return high.0 - low.0 <= snapTime
    }

    /// The TV in the blink the game drew at `rendered`: the frame just before it (the TV black) against each frame of the second
    /// after, the one where the most light appeared; and when that patch turned bright (SportsDelayProbe). nil when no screen-like
    /// patch lit up, or not with a TV's timing and snap.
    static func sighting(_ frames: [Frame], rows: Int, rendered: Double) -> Sighting? {
        guard let before = frames.last(where: { $0.time <= rendered + 0.005 && $0.time >= rendered - 0.3 }) else { return nil }
        var best: (frame: Int, at: SIMD2<Double>, cells: [Int], rise: Double)?
        for (index, frame) in frames.enumerated() where frame.time > rendered + SportsDelayProbe.shortest && frame.time <= rendered + SportsDelayProbe.longest {
            if let lit = brightened(dark: before.cells, bright: frame.cells, rows: rows), lit.rise > (best?.rise ?? 0) { best = (index, lit.at, lit.cells, lit.rise) }
        }
        guard let best else { return nil }
        let series = frames.filter { $0.time >= rendered - 0.25 && $0.time <= rendered + SportsDelayProbe.longest + 0.05 }.map { frame in
            (frame.time, Double(best.cells.reduce(0) { $0 + Int(frame.cells[$1]) }) / Double(best.cells.count))
        }
        guard let delay = SportsDelayProbe.delay(series, rendered: rendered), snapped(series, after: rendered) else { return nil }
        return Sighting(at: best.at, delay: delay, frame: best.frame)
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
