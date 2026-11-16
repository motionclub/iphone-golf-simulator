import Foundation
import Observation
import Photos
import UIKit

/// One recording, as the Recordings screen lists it: when, how long, and where it went (so "where did my video go?" always has an answer).
struct RecordingEntry: Codable, Equatable, Identifiable, Sendable {
    enum Place: String, Codable, Sendable { case photos, kept, notSaved }
    var id = UUID()
    var date: Date
    var seconds: Double
    var place: Place
    /// Why it ended, or why it was not saved, in the words the dock showed.
    var note: String
    /// The kept file's name (place == .kept).
    var file: String?
}

/// The native recorder (Unity plugin), behind a protocol so the service is tested without a TV.
@MainActor protocol CaptureRuntime: AnyObject {
    /// Unity is loaded and the recorder is there (false until the first game of this launch).
    var available: Bool { get }
    var active: Bool { get }
    /// false = not now (the game's picture is not up yet): the service tries again.
    func start(_ configJSON: String) -> Bool
    func stop()
    func setHandler(_ handler: (@MainActor (String) -> Void)?)
}

/// The recorder in the Unity plugin, through the app's runtime bridge.
@MainActor final class LiveCaptureRuntime: CaptureRuntime {
    private var runtime: SportsRuntime { .shared() }
    var available: Bool { runtime.captureAvailable() }
    var active: Bool { runtime.captureActive() }
    func start(_ configJSON: String) -> Bool { runtime.startCapture(configJSON) }
    func stop() { runtime.stopCapture() }
    func setHandler(_ handler: (@MainActor (String) -> Void)?) {
        guard let handler else { runtime.setCaptureHandler(nil); return }
        // the bridge delivers on the main queue
        runtime.setCaptureHandler { json in MainActor.assumeIsolated { handler(json) } }
    }
}

@MainActor protocol PhotoSaving: AnyObject {
    /// Asks for add-only access (we never read the library); true when videos can be saved.
    func requestAccess() async -> Bool
    var hasAccess: Bool { get }
    func save(_ url: URL) async throws
}

@MainActor final class PhotosLibrary: PhotoSaving {
    var hasAccess: Bool { let s = PHPhotoLibrary.authorizationStatus(for: .addOnly); return s == .authorized || s == .limited }
    func requestAccess() async -> Bool {
        let s = await PHPhotoLibrary.requestAuthorization(for: .addOnly)
        return s == .authorized || s == .limited
    }
    func save(_ url: URL) async throws {
        try await PHPhotoLibrary.shared().performChanges {
            _ = PHAssetCreationRequest.creationRequestForAssetFromVideo(atFileURL: url)
        }
    }
}

/// Record the game: tap once to start, tap again to stop, and the video is in the camera roll. What is recorded is the game's
/// picture on the TV (never this phone's controller), with the game's sound; a second phone filming the player is edited in later.
///
/// Tapping record ARMS the recording wherever you are (menu, loading, a match). The native recorder is started as soon as Unity has
/// the game's picture, and the video starts with the first game frame. Only your stop ends it: menus, loading screens and pauses in
/// between are waited through (the 10-18 recorder gave up after 10 s without a game frame, so a take started from the menu ended,
/// with nothing saved, before the match was up).
@MainActor @Observable
final class RecordingService {
    static let shared = RecordingService()

    /// 1080p at 60 frames per second, always (Adnan 11-15: "recording has to be 60 fps period"): the game runs at 60 and sport
    /// footage at 30 looks choppy. A phone that cannot keep up skips frames (the recorder says so) instead of dropping to 30.
    static let width = 1920, height = 1080, fps = 60, bitrateMbps = 16

    enum State: Equatable { case idle, recording, saving, saved, failed }
    private(set) var state: State = .idle {
        didSet {
            guard state != oldValue else { return }
            // a finished take's result stays on screen for a while, whatever happened to the TV
            outcomeTask?.cancel()
            showsOutcome = state == .saving || state == .saved || state == .failed
            if state == .saved || state == .failed {
                outcomeTask = Task { @MainActor [weak self] in
                    try? await Task.sleep(for: .seconds(14))
                    if !Task.isCancelled { self?.showsOutcome = false }
                }
            }
        }
    }
    /// The dock stays up while a take saves, and for a while after it saved or failed, so its note can be read and tapped.
    private(set) var showsOutcome = false
    /// True once the first game frame is in the video (the timer runs from here); false while armed and waiting for the game.
    private(set) var rolling = false
    private(set) var message = ""
    private(set) var elapsed: TimeInterval = 0
    /// The last recording that could not go to Photos (access off): kept in the app so it can be shared or deleted.
    private(set) var keptFile: URL?
    /// The last recordings, newest first (at most 30).
    private(set) var history: [RecordingEntry] = [] { didSet { if let d = try? JSONEncoder().encode(history) { defaults.set(d, forKey: "capture.history") } } }
    var isRecording: Bool { state == .recording }

    /// A stop that the native recorder never confirms gives up after this long instead of saying "Saving…" forever.
    @ObservationIgnored var savingTimeout: Duration = .seconds(45)
    /// How long a TV may be gone before the recording is finished and saved.
    @ObservationIgnored var displayLostGrace: Duration = .seconds(6)
    @ObservationIgnored private var displayWatch: Task<Void, Never>?
    /// How often an armed recording looks for the game's picture.
    @ObservationIgnored var armInterval: Duration = .milliseconds(500)
    @ObservationIgnored let runtime: CaptureRuntime
    @ObservationIgnored let photos: PhotoSaving
    @ObservationIgnored private let defaults: UserDefaults
    @ObservationIgnored var displayConnected: @MainActor () -> Bool = { SportsSession.shared.displayConnected }
    @ObservationIgnored var now: @MainActor () -> Date = { Date() }
    @ObservationIgnored var freeBytes: @MainActor () -> Int64 = { RecordingService.freeDiskBytes() }
    @ObservationIgnored private var outcomeTask: Task<Void, Never>?
    @ObservationIgnored private var savingWatch: Task<Void, Never>?
    @ObservationIgnored private var armTask: Task<Void, Never>?
    @ObservationIgnored private var ticker: Task<Void, Never>?
    @ObservationIgnored private var rollingSince: Date?
    @ObservationIgnored private var photosGranted = false
    /// The native recorder has a take open (it accepted a start and has not finished or failed since).
    @ObservationIgnored private(set) var nativeRunning = false

    init(runtime: CaptureRuntime? = nil, photos: PhotoSaving? = nil, defaults: UserDefaults = .standard) {
        self.runtime = runtime ?? LiveCaptureRuntime()
        self.photos = photos ?? PhotosLibrary()
        self.defaults = defaults
        history = (defaults.data(forKey: "capture.history").flatMap { try? JSONDecoder().decode([RecordingEntry].self, from: $0) }) ?? []
        self.runtime.setHandler { [weak self] json in self?.receive(json) }
    }

    // MARK: can I record

    /// Why recording is not possible right now (nil = it is). Shown under the button.
    var unavailableReason: String? {
        if state == .recording || state == .saving { return nil }
        guard displayConnected() else { return "Connect a TV to record. Recordings capture the game on the TV, never this phone." }
        return nil
    }
    var canToggle: Bool { state == .saving ? false : state == .recording || unavailableReason == nil }
    var timeText: String { let s = Int(elapsed); return String(format: "%d:%02d", s / 60, s % 60) }

    // MARK: start / stop

    func toggle(from source: String = "button") {
        if state == .recording { stop(from: source) }
        else if state != .saving { Task { await start(from: source) } }
    }

    func start(from source: String = "button") async {
        guard state == .idle || state == .saved || state == .failed else { return }
        Self.log("record tapped (\(source)); tv=\(displayConnected()) unity=\(runtime.available) free=\(freeBytes() / 1_000_000) MB")
        if let why = unavailableReason { state = .failed; message = why; return }
        if freeBytes() < 1_200_000_000 { state = .failed; message = "Free up some storage first: recording needs about 1 GB free."; return }
        nativeRunning = false; rolling = false; rollingSince = nil; elapsed = 0; keptFile = nil
        state = .recording; message = "Recording starts when the game is on the TV."
        // asked up front, so the system prompt never interrupts the moment you stop
        photosGranted = await photos.requestAccess()
        guard state == .recording else { return }   // stopped, or the TV went, while the Photos prompt was up
        if !photosGranted { message = "Photos access is off: this recording will be kept in the app instead." }
        arm()
    }

    /// Starts the native recorder as soon as it will take a start, and keeps trying while the recording is on.
    private func arm() {
        armTask?.cancel()
        attemptNativeStart()
        let interval = armInterval
        armTask = Task { @MainActor [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: interval)
                guard let self, !Task.isCancelled, self.state == .recording else { return }
                self.attemptNativeStart()
            }
        }
    }

    private func attemptNativeStart() {
        guard state == .recording, !nativeRunning, runtime.available else { return }
        guard runtime.start(configJSON()) else { return }   // the game's picture is not up yet
        nativeRunning = true
        Self.log("native recorder started; waiting for the first game frame")
    }

    func stop(from source: String = "button") {
        guard state == .recording else { return }
        armTask?.cancel(); armTask = nil
        ticker?.cancel(); ticker = nil
        Self.log("stop (\(source)) after \(timeText); native=\(nativeRunning) rolling=\(rolling)")
        guard nativeRunning else {
            // armed, but the game never came up: there is nothing to save
            state = .failed; message = "Nothing was recorded: the game was not on the TV yet."
            return
        }
        state = .saving; message = "Saving…"
        runtime.stop()
        watchSaving()
    }

    /// The TV went away: finish and save what was recorded, unless it is back within a few seconds. (Going into a game can switch
    /// the TV's picture mode, which iOS may report as the screen disconnecting and reconnecting: that must not end a recording.)
    func displayLost() {
        guard state == .recording else { return }
        Self.log("the TV disconnected: waiting \(displayLostGrace) for it to come back")
        displayWatch?.cancel()
        let grace = displayLostGrace
        displayWatch = Task { @MainActor [weak self] in
            try? await Task.sleep(for: grace)
            guard let self, !Task.isCancelled, self.state == .recording else { return }
            if self.displayConnected() { Self.log("the TV is back: recording continues") }
            else { self.stop(from: "the TV disconnected") }
        }
    }

    /// A stop the native recorder never answers must not leave the dock on "Saving…" (and recording blocked) forever.
    private func watchSaving() {
        savingWatch?.cancel()
        let limit = savingTimeout
        savingWatch = Task { @MainActor [weak self] in
            try? await Task.sleep(for: limit)
            guard let self, !Task.isCancelled, self.state == .saving else { return }
            Self.log("no finished/failed event \(limit) after the stop: giving up (recorder active=\(self.runtime.active))")
            self.nativeRunning = false
            self.state = .failed; self.message = "The recording did not finish saving. Anything recorded will appear in Recordings."
            self.remember(.notSaved, seconds: self.elapsed, note: "Did not finish saving")
            await self.recoverLeftovers()
        }
    }

    func configJSON() -> String {
        // display -1: whichever display the game is on (the TV); game sound only
        let object: [String: Any] = ["width": Self.width, "height": Self.height, "fps": Self.fps, "bitrateMbps": Self.bitrateMbps,
                                     "gameAudio": true, "voice": false, "mic": false, "display": -1]
        return (try? JSONSerialization.data(withJSONObject: object)).flatMap { String(data: $0, encoding: .utf8) } ?? "{}"
    }

    private func startTicker() {
        ticker?.cancel()
        ticker = Task { @MainActor [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .milliseconds(500))
                guard let self, self.state == .recording, let t = self.rollingSince else { return }
                self.elapsed = self.now().timeIntervalSince(t)
            }
        }
    }

    // MARK: events from the native recorder

    func receive(_ json: String) {
        guard let o = (try? JSONSerialization.jsonObject(with: Data(json.utf8))) as? [String: Any], o["type"] as? String == "capture" else { return }
        let text = o["message"] as? String ?? ""
        let reason = o["reason"] as? String ?? ""
        switch o["state"] as? String {
        case "rolling":
            guard state == .recording, nativeRunning, !rolling else { return }
            rolling = true; rollingSince = now(); message = "Recording the game"
            Self.log("first game frame recorded")
            startTicker()
        case "warning": if nativeRunning, !text.isEmpty { message = text }
        case "failed":
            // a start that was refused (no game picture yet): the armed recording simply tries again
            guard nativeRunning else { return }
            Self.log("event \(json) (dock was \(state))")
            ended()
            state = .failed
            if reason == "empty" { message = "Nothing was recorded: the game was not on the TV while recording." }
            else { message = text.isEmpty ? "The recording could not be made." : text; remember(.notSaved, seconds: elapsed, note: message) }
        case "finished":
            Self.log("event \(json) (dock was \(state))")
            let seconds = o["seconds"] as? Double ?? elapsed
            let url = (o["url"] as? String).map { URL(fileURLWithPath: $0) }
            guard nativeRunning || state == .saving else {
                // a take that finished after the dock gave up waiting for it: its video is still saved
                if let url { Task { await saveLate(url, seconds: seconds) } }
                return
            }
            ended()
            if let url { Task { await finish(url, seconds: seconds, reason: reason.isEmpty ? "user" : reason, nativeMessage: text) } }
            else { state = .failed; message = "The recording file is missing."; remember(.notSaved, seconds: seconds, note: message) }
        default: break
        }
    }

    /// The native take is over (finished or failed), whoever ended it.
    private func ended() {
        nativeRunning = false
        savingWatch?.cancel(); savingWatch = nil
        armTask?.cancel(); armTask = nil
        ticker?.cancel(); ticker = nil
    }

    private func finish(_ url: URL, seconds: TimeInterval, reason: String, nativeMessage: String = "") async {
        state = .saving; elapsed = seconds
        let why: String
        switch reason {
        case "background": why = "Recording stopped because MotionSports left the screen. "
        case "storage": why = "Recording stopped: the phone is almost out of storage. "
        case "thermal": why = "Recording stopped: the phone is too warm. "
        case "limit": why = "Recording stopped at the 90 minute limit. "
        // the recorder hit a problem: its own words (it says what was kept)
        case "error": why = nativeMessage.isEmpty ? "Recording stopped because of a problem. " : nativeMessage.replacingOccurrences(of: " Your video was saved.", with: "") + " "
        default: why = ""
        }
        let note = why.trimmingCharacters(in: .whitespaces).isEmpty ? "Stopped by you" : why.trimmingCharacters(in: .whitespaces)
        guard FileManager.default.fileExists(atPath: url.path) else {
            Self.log("finished file missing at \(url.path)")
            state = .failed; message = why + "The recording file is missing."; remember(.notSaved, seconds: seconds, note: message); return
        }
        if photosGranted || photos.hasAccess {
            do {
                try await photos.save(url)
                try? FileManager.default.removeItem(at: url)
                state = .saved; message = why + "Saved to Photos · \(durationText(seconds))"
                Self.log("saved to Photos: \(url.lastPathComponent) \(durationText(seconds)) (\(reason))")
                remember(.photos, seconds: seconds, note: note)
                return
            } catch { Self.log("Photos refused \(url.lastPathComponent): \(error.localizedDescription); keeping it in the app") }
        }
        guard let kept = Self.keep(url) else {
            Self.log("could not keep \(url.path)")
            state = .failed; message = why + "The recording could not be kept."; remember(.notSaved, seconds: seconds, note: message); return
        }
        keptFile = kept
        state = .saved
        message = why + "Photos could not take it, so it is kept in MotionSports. Hold the record button for Recordings, then Share."
        Self.log("kept in the app: \(kept.path)")
        remember(.kept, seconds: seconds, note: note, file: kept.lastPathComponent)
    }

    private func saveLate(_ url: URL, seconds: TimeInterval) async {
        guard FileManager.default.fileExists(atPath: url.path) else { return }
        if photos.hasAccess, (try? await photos.save(url)) != nil {
            try? FileManager.default.removeItem(at: url); remember(.photos, seconds: seconds, note: "Finished saving late")
        } else if let kept = Self.keep(url) { keptFile = kept; remember(.kept, seconds: seconds, note: "Finished saving late", file: kept.lastPathComponent) }
    }

    private func remember(_ place: RecordingEntry.Place, seconds: Double, note: String, file: String? = nil) {
        history.insert(RecordingEntry(date: now(), seconds: seconds, place: place, note: note, file: file), at: 0)
        if history.count > 30 { history.removeLast(history.count - 30) }
    }

    // MARK: log

    /// The recorder log (the native recorder writes the same file): Documents/Recordings/recorder-log.txt. Shared from Recordings.
    static var logURL: URL { folder.appendingPathComponent("recorder-log.txt") }
    nonisolated static func log(_ line: String) {
        let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("Recordings", isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        let file = url.appendingPathComponent("recorder-log.txt")
        let text = ISO8601DateFormatter.string(from: Date(), timeZone: .current, formatOptions: [.withInternetDateTime]) + " [app] " + line + "\n"
        guard let data = text.data(using: .utf8) else { return }
        if let h = try? FileHandle(forWritingTo: file) { _ = try? h.seekToEnd(); try? h.write(contentsOf: data); try? h.close() }
        else { try? data.write(to: file) }
    }

    private func durationText(_ s: TimeInterval) -> String { String(format: "%d:%02d", Int(s) / 60, Int(s) % 60) }

    // MARK: files

    static var folder: URL { FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("Recordings", isDirectory: true) }
    /// Where the native recorder writes (SportsSessionRecorder -recordingsDirectory).
    static var tempFolder: URL { URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("MotionClubRecordings", isDirectory: true) }

    /// Moves a recording out of the temporary folder (the system may clear it) into the app's own.
    static func keep(_ url: URL) -> URL? {
        try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let dest = folder.appendingPathComponent(url.lastPathComponent)
        do { try FileManager.default.moveItem(at: url, to: dest); return dest } catch { return FileManager.default.fileExists(atPath: url.path) ? url : nil }
    }
    static func library() -> [URL] {
        ((try? FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: [.creationDateKey], options: .skipsHiddenFiles)) ?? [])
            .filter { $0.pathExtension == "mp4" || $0.pathExtension == "mov" }
            .sorted { ((try? $0.resourceValues(forKeys: [.creationDateKey]).creationDate) ?? .distantPast) > ((try? $1.resourceValues(forKeys: [.creationDateKey]).creationDate) ?? .distantPast) }
    }
    static func freeDiskBytes() -> Int64 {
        let values = try? URL(fileURLWithPath: NSTemporaryDirectory()).resourceValues(forKeys: [.volumeAvailableCapacityForImportantUsageKey])
        return values?.volumeAvailableCapacityForImportantUsage ?? .max
    }

    /// A recording left behind (the app was closed while recording, or a stop never finished): saved now if Photos already allows it,
    /// kept in the app otherwise.
    func recoverLeftovers() async {
        guard state != .recording, state != .saving, !nativeRunning else { return }
        let files = ((try? FileManager.default.contentsOfDirectory(at: Self.tempFolder, includingPropertiesForKeys: nil)) ?? []).filter { $0.pathExtension == "mp4" }
        for url in files {
            Self.log("leftover recording found: \(url.lastPathComponent)")
            if photos.hasAccess, (try? await photos.save(url)) != nil {
                try? FileManager.default.removeItem(at: url); remember(.photos, seconds: 0, note: "Recovered after the app closed")
            } else if let kept = Self.keep(url) { keptFile = kept; remember(.kept, seconds: 0, note: "Recovered after the app closed", file: kept.lastPathComponent) }
        }
    }

    func deleteKept(_ url: URL) { try? FileManager.default.removeItem(at: url); if keptFile == url { keptFile = nil } }
}
