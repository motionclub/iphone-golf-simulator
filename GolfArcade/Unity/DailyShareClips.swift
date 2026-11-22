import AVFoundation
import CoreVideo
import Foundation

// DAILY SHARE: the Daily Hole in One's three shots, filmed by Unity (ShotClips.cs → SportsShotClips.mm) and encoded here, one
// short mp4 per shot in tmp/DailyShare. The marks Unity sends (the strike, the rest, and how far and how many points) say where
// each shot's moment is; DailyShareComposer cuts the shots there and adds the title and score cards.

/// One filmed shot: its file and, in seconds from its first frame, when the club met the ball, when the ball came to rest and
/// where the file ends.
struct DailyShotClip: Equatable, Sendable {
    var shot: Int
    var url: URL
    var contact: Double?
    var rest: Double?
    var end: Double
    var feet: Double
    var points: Int
    var holed: Bool

    /// The parts the clip keeps, in seconds of the file: from just before the strike (the backswing) to just after the ball
    /// stops. A long flight keeps its start and its landing with a cut between, so a shot never runs past `longest`. A shot with
    /// no strike mark keeps the last seconds before its rest; one with no rest runs to the end of its file.
    func keep(lead: Double = 1.0, launch: Double = 1.7, landing: Double = 1.6, tail: Double = 1.3, longest: Double = 5.6) -> [ClosedRange<Double>] {
        let settle = rest ?? end
        let stop = max(0, min(end, settle + tail))
        guard let contact else { return [max(0, stop - 4.5)...stop] }
        let start = min(stop, max(0, contact - lead))
        if stop - start <= longest { return [start...stop] }
        let first = start...min(stop, contact + launch)
        let second = min(stop, max(first.upperBound, settle - landing))...stop
        return second.upperBound - second.lowerBound > 0.05 ? [first, second] : [first]
    }
    /// How long the kept parts run.
    var kept: Double { keep().reduce(0) { $0 + $1.upperBound - $1.lowerBound } }
}

/// Writes one shot's BGRA frames (bottom row first) into an H.264 mp4 as they arrive. Thread-safe: frames come on Unity's main
/// thread and are copied before `append` returns; the encoder runs on its own queue.
final class DailyShotWriter: @unchecked Sendable {
    let url: URL
    let width: Int, height: Int
    private let writer: AVAssetWriter
    private let input: AVAssetWriterInput
    private let adaptor: AVAssetWriterInputPixelBufferAdaptor
    private let queue = DispatchQueue(label: "club.daily-share.writer")
    private var start: Double?
    private var lastTime = -1.0
    private(set) var frames = 0
    private(set) var dropped = 0
    private(set) var lastFrameTime: Double?

    init(url: URL, width: Int, height: Int, fps: Int = 30) throws {
        self.url = url; self.width = width; self.height = height
        try? FileManager.default.removeItem(at: url)
        writer = try AVAssetWriter(outputURL: url, fileType: .mp4)
        input = AVAssetWriterInput(mediaType: .video, outputSettings: [
            AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: width, AVVideoHeightKey: height,
            AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 8_000_000, AVVideoExpectedSourceFrameRateKey: fps,
                                              AVVideoMaxKeyFrameIntervalKey: fps, AVVideoAllowFrameReorderingKey: false,
                                              AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel]])
        input.expectsMediaDataInRealTime = true
        adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
            kCVPixelBufferWidthKey as String: width, kCVPixelBufferHeightKey as String: height,
            kCVPixelBufferIOSurfacePropertiesKey as String: [:]])
        guard writer.canAdd(input) else { throw CocoaError(.fileWriteUnknown) }
        writer.add(input)
        guard writer.startWriting() else { throw writer.error ?? CocoaError(.fileWriteUnknown) }
        writer.startSession(atSourceTime: .zero)
    }

    /// Seconds from this shot's first frame (nil before it).
    func seconds(at time: Double) -> Double? { start.map { max(0, time - $0) } }

    /// One frame at `time` (seconds on the sender's clock). `bottomUp`: row 0 is the picture's bottom (Unity's readback).
    func append(_ bytes: UnsafeRawPointer, stride: Int, time: Double, bottomUp: Bool = true) {
        guard writer.status == .writing, time > lastTime else { return }
        guard let pool = adaptor.pixelBufferPool else { dropped += 1; return }
        var made: CVPixelBuffer?
        guard CVPixelBufferPoolCreatePixelBuffer(nil, pool, &made) == kCVReturnSuccess, let buffer = made else { dropped += 1; return }
        CVPixelBufferLockBaseAddress(buffer, [])
        if let base = CVPixelBufferGetBaseAddress(buffer) {
            let out = CVPixelBufferGetBytesPerRow(buffer), row = min(out, stride, width * 4)
            for y in 0..<height {
                let from = bytes.advanced(by: (bottomUp ? height - 1 - y : y) * stride)
                (base + y * out).copyMemory(from: from, byteCount: row)
            }
        }
        CVPixelBufferUnlockBaseAddress(buffer, [])
        if start == nil { start = time }
        lastTime = time; lastFrameTime = time
        let at = CMTime(seconds: time - (start ?? time), preferredTimescale: 600)
        queue.async { [self] in
            if input.isReadyForMoreMediaData, adaptor.append(buffer, withPresentationTime: at) { frames += 1 } else { dropped += 1 }
        }
    }

    /// Ends the file; `done` gets its length in seconds (nil: nothing usable was written).
    func finish(_ done: @escaping @Sendable (Double?) -> Void) {
        queue.async { [self] in
            guard writer.status == .writing, frames > 1, let first = start, let last = lastFrameTime else {
                writer.cancelWriting(); try? FileManager.default.removeItem(at: url); done(nil); return
            }
            input.markAsFinished()
            writer.endSession(atSourceTime: CMTime(seconds: last - first + 1.0 / 30, preferredTimescale: 600))
            writer.finishWriting { [self] in done(writer.status == .completed ? last - first + 1.0 / 30 : nil) }
        }
    }

    func cancel() {
        queue.async { [self] in
            if writer.status == .writing { writer.cancelWriting() }
            try? FileManager.default.removeItem(at: url)
        }
    }
}

/// The three shots as they are filmed: Unity's marks and frames in, finished `DailyShotClip`s out.
final class DailyShareClips: @unchecked Sendable {
    static let shared = DailyShareClips()
    static var folder: URL {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("DailyShare", isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    enum Kind: Int32 { case frame = 0, arm = 1, contact = 2, rest = 3, close = 4, cancel = 5 }

    private let lock = NSLock()
    private var shot = -1
    private var writer: DailyShotWriter?
    private var armedAt = 0.0
    private var contact: Double?, rest: Double?
    private var feet = -1.0, points = 0, holed = false
    private var clips: [Int: DailyShotClip] = [:]
    /// A shot finished filming (on a background queue).
    var onClip: @Sendable (DailyShotClip) -> Void = { _ in }

    /// The finished shots so far, in order.
    var finished: [DailyShotClip] { lock.withLock { clips.keys.sorted().compactMap { clips[$0] } } }

    /// Forget every shot (a new day's challenge is starting).
    func reset() {
        lock.withLock {
            writer?.cancel(); writer = nil; shot = -1; clips = [:]
        }
        if let files = try? FileManager.default.contentsOfDirectory(at: Self.folder, includingPropertiesForKeys: nil) {
            for f in files where f.lastPathComponent.hasPrefix("shot") { try? FileManager.default.removeItem(at: f) }
        }
    }

    /// One call from Unity (any thread; frames are copied before this returns).
    func receive(kind raw: Int32, shot index: Int32, time: Double, feet f: Double, points p: Int32, holed h: Int32,
                 bgra: UnsafeRawPointer?, width: Int32, height: Int32, stride: Int32) {
        guard let kind = Kind(rawValue: raw) else { return }
        lock.lock(); defer { lock.unlock() }
        switch kind {
        case .frame:
            guard shot >= 0, let bgra, width > 0, height > 0 else { return }
            if writer == nil {
                let url = Self.folder.appendingPathComponent("shot\(shot + 1).mp4")
                writer = try? DailyShotWriter(url: url, width: Int(width), height: Int(height))
            }
            guard let writer, writer.width == Int(width), writer.height == Int(height) else { return }
            writer.append(bgra, stride: Int(stride), time: time)
        case .arm:
            writer?.cancel(); writer = nil
            shot = Int(index); armedAt = time; contact = nil; rest = nil; feet = -1; points = 0; holed = false
            clips[shot] = nil
        case .contact:
            guard Int(index) == shot else { return }
            contact = time
        case .rest:
            guard Int(index) == shot else { return }
            rest = time; feet = f; points = Int(p); holed = h != 0
        case .close:
            guard Int(index) == shot, let writer else { shot = -1; return }
            let clip = DailyShotClip(shot: shot, url: writer.url, contact: contact.flatMap(writer.seconds), rest: rest.flatMap(writer.seconds),
                                     end: 0, feet: feet, points: points, holed: holed)
            self.writer = nil; shot = -1
            writer.finish { [weak self] length in
                guard let self, let length else { return }
                var done = clip; done.end = length
                self.lock.withLock { self.clips[done.shot] = done }
                self.onClip(done)
            }
        case .cancel:
            guard Int(index) == shot else { return }
            writer?.cancel(); writer = nil; shot = -1
        }
    }

    // MARK: the plugin (UnityFramework, found with dlsym like RacketFeel: a quiet no-op until Unity is loaded)

    private typealias Sink = @convention(c) (Int32, Int32, Double, Double, Int32, Int32, UnsafeRawPointer?, Int32, Int32, Int32) -> Void
    private typealias SetSink = @convention(c) (Sink?) -> Void
    private var installed = false

    /// Hands Unity the sink (once Unity is loaded; safe to call again).
    func install() {
        guard !lock.withLock({ installed }) else { return }
        guard let pointer = dlsym(UnsafeMutableRawPointer(bitPattern: -2), "SportsShotClips_SetSink") else { return }
        let set = unsafeBitCast(pointer, to: SetSink.self)
        let sink: Sink = { kind, shot, time, feet, points, holed, bgra, w, h, stride in
            DailyShareClips.shared.receive(kind: kind, shot: shot, time: time, feet: feet, points: points, holed: holed,
                                           bgra: bgra, width: w, height: h, stride: stride)
        }
        set(sink)
        lock.withLock { installed = true }
    }
}
