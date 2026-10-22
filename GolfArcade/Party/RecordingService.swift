import Foundation
import Observation
import Photos
import UIKit

/// How the TV is recorded and what goes into the sound track. Stored on the phone.
struct CaptureSettings: Codable, Equatable, Sendable {
    enum Quality: String, Codable, CaseIterable, Identifiable, Sendable {
        case p720at30, p720at60, p1080at30, p1080at60
        var id: String { rawValue }
        var width: Int { self == .p720at30 || self == .p720at60 ? 1280 : 1920 }
        var height: Int { self == .p720at30 || self == .p720at60 ? 720 : 1080 }
        var fps: Int { self == .p720at30 || self == .p1080at30 ? 30 : 60 }
        var bitrateMbps: Int { switch self { case .p720at30: 5; case .p720at60: 8; case .p1080at30: 10; case .p1080at60: 15 } }
        var title: String { "\(height)p · \(fps) fps" }
        var detail: String {
            switch self {
            case .p720at30: "Smallest files, easiest on the battery"
            case .p720at60: "Smooth motion, small files"
            case .p1080at30: "Sharp picture (recommended)"
            case .p1080at60: "Sharpest and smoothest, warmest phone"
            }
        }
    }
    var quality: Quality = .p1080at30
    var gameAudio = true
    /// The other players' voices in your party (they are told you are recording).
    var partyVoice = true
    var myMic = true
    var saveToPhotos = true
}

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

/// The native TV recorder (Unity plugin), behind a protocol so the service is tested without a TV.
@MainActor protocol CaptureRuntime: AnyObject {
    /// The game is running on a TV and the recorder is there.
    var available: Bool { get }
    var active: Bool { get }
    func start(_ configJSON: String) -> Bool
    func stop()
    func setHandler(_ handler: (@MainActor (String) -> Void)?)
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

/// One-tap recording of what is on the TV (never the phone controller), with the game's sound and the party's voices, saved to the
/// camera roll when you stop. The picture and sound are made by the native recorder in the Unity plugin; this decides when, tells the
/// party, and saves the file. PLAN_PartyChat_Recording.md.
@MainActor @Observable
final class RecordingService {
    static let shared = RecordingService()

    enum State: Equatable { case idle, starting, recording, saving, saved, failed }
    private(set) var state: State = .idle {
        didSet {
            guard state != oldValue else { return }
            // a finished take's result stays on screen for a while, whatever happened to the TV: the dock (and its note) used to vanish with it
            outcomeTask?.cancel()
            let done = state == .saving || state == .saved || state == .failed
            showsOutcome = done
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
    @ObservationIgnored private var outcomeTask: Task<Void, Never>?
    private(set) var message = ""
    private(set) var elapsed: TimeInterval = 0
    /// The last recording that could not go to Photos (access off): kept in the app so it can be shared or deleted.
    private(set) var keptFile: URL?
    var settings: CaptureSettings { didSet { if let d = try? JSONEncoder().encode(settings) { defaults.set(d, forKey: "capture.settings") } } }
    /// The last recordings, newest first (at most 30).
    private(set) var history: [RecordingEntry] = [] { didSet { if let d = try? JSONEncoder().encode(history) { defaults.set(d, forKey: "capture.history") } } }
    /// A stop that the native recorder never confirms (no "finished"/"failed" event) gives up after this long instead of saying "Saving…" forever.
    @ObservationIgnored var savingTimeout: Duration = .seconds(45)
    @ObservationIgnored private var savingWatch: Task<Void, Never>?
    /// True from the first tap until the file is saved: the dock shows the red indicator.
    var isRecording: Bool { state == .recording || state == .starting }

    @ObservationIgnored let runtime: CaptureRuntime
    @ObservationIgnored let photos: PhotoSaving
    @ObservationIgnored let chat: PartyChat
    @ObservationIgnored private let defaults: UserDefaults
    @ObservationIgnored var displayConnected: @MainActor () -> Bool = { SportsSession.shared.displayConnected }
    /// Told true just before the recorder starts and false once it has stopped: the voice engine feeds the recording only in between.
    @ObservationIgnored var captureHook: (@MainActor (Bool) -> Void)?
    @ObservationIgnored var now: @MainActor () -> Date = { Date() }
    @ObservationIgnored var freeBytes: @MainActor () -> Int64 = { RecordingService.freeDiskBytes() }
    @ObservationIgnored private var startedAt: Date?
    @ObservationIgnored private var ticker: Task<Void, Never>?
    @ObservationIgnored private var photosGranted = false
    @ObservationIgnored private var announced = false

    init(runtime: CaptureRuntime? = nil, photos: PhotoSaving? = nil, chat: PartyChat = .shared, defaults: UserDefaults = .standard) {
        self.runtime = runtime ?? LiveCaptureRuntime()
        self.photos = photos ?? PhotosLibrary()
        self.chat = chat; self.defaults = defaults
        settings = (defaults.data(forKey: "capture.settings").flatMap { try? JSONDecoder().decode(CaptureSettings.self, from: $0) }) ?? CaptureSettings()
        history = (defaults.data(forKey: "capture.history").flatMap { try? JSONDecoder().decode([RecordingEntry].self, from: $0) }) ?? []
        self.runtime.setHandler { [weak self] json in self?.receive(json) }
    }

    // MARK: can I record

    /// Why recording is not possible right now (nil = it is). Shown on the button.
    var unavailableReason: String? {
        if isRecording || state == .saving { return nil }
        guard displayConnected() else { return "Connect a TV to record. Recordings capture the TV picture, never this phone." }
        guard runtime.available else { return "Recording is ready once the game is up on the TV." }
        return nil
    }
    var canToggle: Bool { isRecording || state == .saving ? state == .recording : unavailableReason == nil }

    var timeText: String { let s = Int(elapsed); return String(format: "%d:%02d", s / 60, s % 60) }

    // MARK: start / stop

    func toggle(from source: String = "button") { if state == .recording { stop(from: source) } else if state == .idle || state == .saved || state == .failed { Task { await start(from: source) } } }

    func start(from source: String = "button") async {
        guard state == .idle || state == .saved || state == .failed else { return }
        Self.log("start requested (\(source)); tv=\(displayConnected()) recorder=\(runtime.available) free=\(freeBytes() / 1_000_000) MB settings=\(settings.quality.title)")
        if let why = unavailableReason { state = .failed; message = why; return }
        if freeBytes() < 1_200_000_000 { state = .failed; message = "Free up some storage first: recording needs about 1 GB free."; return }
        state = .starting; message = "Starting…"; elapsed = 0; keptFile = nil
        photosGranted = settings.saveToPhotos ? await photos.requestAccess() : false
        // asked up front so the system prompt never interrupts the moment you stop
        captureHook?(true)
        guard runtime.start(configJSON()) else {
            Self.log("native recorder refused to start (\(message))")
            captureHook?(false)
            if state == .starting { state = .failed; message = "The recorder could not start. Try again once the TV picture is up." }
            return
        }
        // the native recorder confirms with a "started" event; until then the dock already shows the indicator
        state = .recording; startedAt = now(); message = settings.saveToPhotos && !photosGranted ? "Photos access is off: this recording will stay in the app." : "Recording the TV"
        announced = chat.channel.inParty
        if announced { chat.announceRecording(true) }
        startTicker()
    }

    func stop(from source: String = "button") {
        guard state == .recording || state == .starting else { return }
        Self.log("stop requested (\(source)) after \(timeText)")
        state = .saving; message = "Saving…"
        runtime.stop()
        watchSaving()
        ticker?.cancel(); ticker = nil
        if announced { chat.announceRecording(false); announced = false }
    }

    /// The TV went away: finish what was recorded.
    func displayLost() { if isRecording { stop(from: "the TV disconnected") } }

    /// A stop the native recorder never answers must not leave the dock on "Saving…" (and recording blocked) forever.
    private func watchSaving() {
        savingWatch?.cancel()
        let limit = savingTimeout
        savingWatch = Task { @MainActor [weak self] in
            try? await Task.sleep(for: limit)
            guard let self, !Task.isCancelled, self.state == .saving else { return }
            Self.log("no finished/failed event \(limit) after the stop: giving up (recorder active=\(self.runtime.active))")
            self.state = .failed; self.message = "The recording did not finish saving. Anything recorded will appear in Recordings."
            self.remember(.notSaved, seconds: self.elapsed, note: "Did not finish saving")
            await self.recoverLeftovers()
        }
    }

    func configJSON() -> String {
        let q = settings.quality
        let object: [String: Any] = ["width": q.width, "height": q.height, "fps": q.fps, "bitrateMbps": q.bitrateMbps, "gameAudio": settings.gameAudio,
                                     "voice": settings.partyVoice, "mic": settings.myMic, "display": 1]
        return (try? JSONSerialization.data(withJSONObject: object)).flatMap { String(data: $0, encoding: .utf8) } ?? "{}"
    }

    private func startTicker() {
        ticker?.cancel()
        ticker = Task { @MainActor [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .milliseconds(500))
                guard let self, self.state == .recording, let t = self.startedAt else { return }
                self.elapsed = self.now().timeIntervalSince(t)
            }
        }
    }

    // MARK: events from the native recorder

    func receive(_ json: String) {
        guard let o = (try? JSONSerialization.jsonObject(with: Data(json.utf8))) as? [String: Any], o["type"] as? String == "capture" else { return }
        let text = o["message"] as? String ?? ""
        if o["state"] as? String != "started" { Self.log("event \(json) (dock was \(state))") }
        switch o["state"] as? String {
        case "started": if state == .starting { state = .recording }
        case "warning": if !text.isEmpty { message = text }
        case "failed":
            ticker?.cancel(); ticker = nil; captureHook?(false)
            if announced { chat.announceRecording(false); announced = false }
            savingWatch?.cancel()
            state = .failed; message = text.isEmpty ? "The recording could not be made." : text
            remember(.notSaved, seconds: elapsed, note: message)
        case "finished":
            savingWatch?.cancel()
            ticker?.cancel(); ticker = nil; captureHook?(false)
            if announced { chat.announceRecording(false); announced = false }
            let seconds = o["seconds"] as? Double ?? elapsed
            let reason = o["reason"] as? String ?? "user"
            if let path = o["url"] as? String { Task { await finish(URL(fileURLWithPath: path), seconds: seconds, reason: reason, nativeMessage: text) } }
            else { state = .failed; message = "The recording file is missing."; remember(.notSaved, seconds: seconds, note: message) }
        default: break
        }
    }

    private func finish(_ url: URL, seconds: TimeInterval, reason: String, nativeMessage: String = "") async {
        state = .saving; elapsed = seconds
        let why: String
        switch reason {
        case "background": why = "Recording stopped because Motion Club left the screen. "
        case "storage": why = "Recording stopped: the phone is almost out of storage. "
        case "thermal": why = "Recording stopped: the phone is too warm. "
        case "display": why = "Recording stopped: the TV picture went away. "
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
        if settings.saveToPhotos, photosGranted || photos.hasAccess {
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
        message = why + (settings.saveToPhotos ? "Photos could not save it, so it is kept in Motion Club (Recordings). Allow Photos in Settings, or tap Share." : "Saved in Motion Club · \(durationText(seconds))")
        Self.log("kept in the app: \(kept.path)")
        remember(.kept, seconds: seconds, note: note, file: kept.lastPathComponent)
    }

    private func remember(_ place: RecordingEntry.Place, seconds: Double, note: String, file: String? = nil) {
        history.insert(RecordingEntry(date: now(), seconds: seconds, place: place, note: note, file: file), at: 0)
        if history.count > 30 { history.removeLast(history.count - 30) }
    }

    // MARK: log

    /// The recorder log (the native recorder writes the same file): Documents/Recordings/recorder-log.txt. Shown in Recordings.
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

    /// A recording left behind (the app was killed while recording): saved now if Photos already allows it, kept otherwise.
    func recoverLeftovers() async {
        guard !isRecording, state != .saving else { return }
        let files = ((try? FileManager.default.contentsOfDirectory(at: Self.tempFolder, includingPropertiesForKeys: nil)) ?? []).filter { $0.pathExtension == "mp4" }
        for url in files {
            Self.log("leftover recording found: \(url.lastPathComponent)")
            if photos.hasAccess, (try? await photos.save(url)) != nil {
                try? FileManager.default.removeItem(at: url); remember(.photos, seconds: 0, note: "Recovered after the app closed")
            } else if let kept = Self.keep(url) { keptFile = kept; remember(.kept, seconds: 0, note: "Recovered after the app closed", file: kept.lastPathComponent) }
        }
    }

    func deleteKept(_ url: URL) { try? FileManager.default.removeItem(at: url); if keptFile == url { keptFile = nil } }

    #if DEBUG
    func debugReset() { ticker?.cancel(); ticker = nil; state = .idle; message = ""; elapsed = 0; keptFile = nil; announced = false }
    #endif
}
