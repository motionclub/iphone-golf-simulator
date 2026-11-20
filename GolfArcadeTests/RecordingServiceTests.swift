import XCTest
@testable import GolfArcade

/// One-tap game recording: tap to start (anywhere, also before the game is up), tap to stop, and the video is in Photos.
/// In-memory fakes stand in for the native recorder and Photos; the real recorder is a device check.
@MainActor final class RecordingServiceTests: XCTestCase {
    @MainActor final class Runtime: CaptureRuntime {
        var available = true, active = false
        /// false = the game's picture is not up: the native recorder refuses the start
        var accept = true
        var started: [String] = [], attempts = 0, stops = 0
        var handler: (@MainActor (String) -> Void)?
        func start(_ json: String) -> Bool {
            attempts += 1
            guard accept else { handler?(#"{"type":"capture","state":"failed","reason":"notReady","message":"The TV picture is not ready yet."}"#); return false }
            started.append(json); active = true; handler?(#"{"type":"capture","state":"started"}"#); return true
        }
        func stop() { stops += 1; active = false }
        func setHandler(_ h: (@MainActor (String) -> Void)?) { handler = h }
        func roll() { handler?(#"{"type":"capture","state":"rolling"}"#) }
        func finish(_ path: String, reason: String = "user", seconds: Double = 75) {
            handler?("{\"type\":\"capture\",\"state\":\"finished\",\"url\":\"\(path)\",\"seconds\":\(seconds),\"reason\":\"\(reason)\"}")
        }
    }
    @MainActor final class Photos: PhotoSaving {
        var access = true, requests = 0, saved: [URL] = [], fail = false, isBlocked = false
        var hasAccess: Bool { access }
        var blocked: Bool { isBlocked }
        func requestAccess() async -> Bool { requests += 1; return access }
        func save(_ url: URL) async throws { if fail { throw NSError(domain: "x", code: 1) }; saved.append(url) }
    }
    private func recorder(connected: Bool = true) -> (RecordingService, Runtime, Photos) {
        let rt = Runtime(), ph = Photos()
        let svc = RecordingService(runtime: rt, photos: ph, defaults: UserDefaults(suiteName: "rec-\(UUID().uuidString)")!)
        svc.displayConnected = { connected }; svc.freeBytes = { 50_000_000_000 }; svc.armInterval = .milliseconds(10); svc.displayLostGrace = .milliseconds(40)
        return (svc, rt, ph)
    }
    private func tempVideo() -> URL {
        let dir = RecordingService.tempFolder; try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let url = dir.appendingPathComponent("MotionSports-test-\(UUID().uuidString).mp4"); FileManager.default.createFile(atPath: url.path, contents: Data([0, 0, 0, 24]))
        return url
    }
    private func settle(_ what: String = "state", _ done: @MainActor () -> Bool) async {
        for _ in 0..<300 { if done() { return }; try? await Task.sleep(for: .milliseconds(10)) }
        XCTFail("never reached: \(what)")
    }
    override func tearDown() async throws {
        try? FileManager.default.removeItem(at: RecordingService.tempFolder)
    }

    func testTapRecordTapStopAndTheVideoIsInPhotos() async {
        let (svc, rt, photos) = recorder()
        XCTAssertNil(svc.unavailableReason); XCTAssertTrue(svc.canToggle)
        await svc.start()
        XCTAssertEqual(svc.state, .recording); XCTAssertEqual(photos.requests, 1, "Photos access is asked up front, not when you stop")
        let cfg = (try? JSONSerialization.jsonObject(with: Data(rt.started[0].utf8))) as? [String: Any]
        XCTAssertEqual(cfg?["display"] as? Int, -1, "whichever display the game is on, never the phone's controller")
        XCTAssertEqual(cfg?["width"] as? Int, 1920); XCTAssertEqual(cfg?["height"] as? Int, 1080); XCTAssertEqual(cfg?["gameAudio"] as? Bool, true)
        XCTAssertEqual(cfg?["fps"] as? Int, 60, "recordings are 60 frames per second, always")
        XCTAssertFalse(svc.rolling, "the timer waits for the first game frame"); rt.roll(); XCTAssertTrue(svc.rolling)
        svc.toggle(); XCTAssertEqual(svc.state, .saving); XCTAssertEqual(rt.stops, 1)
        let file = tempVideo(); rt.finish(file.path)
        await settle("saved") { svc.state == .saved }
        XCTAssertEqual(photos.saved, [file]); XCTAssertFalse(FileManager.default.fileExists(atPath: file.path), "the temporary file is removed once it is in Photos")
        XCTAssertTrue(svc.message.contains("Saved to Photos") && svc.message.contains("1:15"), svc.message)
        XCTAssertEqual(svc.history.first?.place, .photos)
    }

    /// Adnan 11-14: "the recording would drop when they entered the game". A recording started in the menu waits for the game.
    func testARecordingStartedBeforeTheGameWaitsForItInsteadOfDropping() async {
        let (svc, rt, photos) = recorder()
        rt.available = false   // Unity is not loaded yet (no game played this launch)
        await svc.start()
        XCTAssertEqual(svc.state, .recording, "armed"); XCTAssertEqual(rt.attempts, 0)
        try? await Task.sleep(for: .milliseconds(60)); XCTAssertEqual(svc.state, .recording, "still on, however long the menu takes")
        rt.available = true; rt.accept = false   // Unity is up, but the game's picture is not on the TV yet (loading)
        await settle("tried") { rt.attempts >= 3 }
        XCTAssertEqual(svc.state, .recording, "a refused start is not a failed recording"); XCTAssertTrue(svc.history.isEmpty)
        rt.accept = true   // the match is on the TV
        await settle("started") { rt.started.count == 1 }
        try? await Task.sleep(for: .milliseconds(40)); XCTAssertEqual(rt.started.count, 1, "started once, not on every tick")
        rt.roll(); XCTAssertTrue(svc.rolling)
        svc.stop(); let file = tempVideo(); rt.finish(file.path)
        await settle("saved") { svc.state == .saved }
        XCTAssertEqual(photos.saved, [file])
    }

    func testStoppingBeforeAnyGameSaysNothingWasRecorded() async {
        let (svc, rt, photos) = recorder(); rt.accept = false
        await svc.start(); svc.stop()
        XCTAssertEqual(svc.state, .failed); XCTAssertTrue(svc.message.contains("Nothing was recorded"), svc.message)
        XCTAssertEqual(rt.stops, 0); XCTAssertTrue(photos.saved.isEmpty); XCTAssertTrue(svc.canToggle, "and the next recording can start")
        // the native recorder had a take open but never saw a game frame
        let (svc2, rt2, _) = recorder()
        await svc2.start(); svc2.stop(); XCTAssertEqual(svc2.state, .saving)
        rt2.handler?(#"{"type":"capture","state":"failed","reason":"empty","message":"Nothing was recorded: the game was not on screen while recording."}"#)
        XCTAssertEqual(svc2.state, .failed); XCTAssertTrue(svc2.message.contains("Nothing was recorded"))
    }

    func testNoTVNoRecording() async {
        let (svc, rt, _) = recorder(connected: false)
        XCTAssertNotNil(svc.unavailableReason); XCTAssertFalse(svc.canToggle)
        await svc.start(); XCTAssertEqual(svc.state, .failed); XCTAssertEqual(rt.attempts, 0)
    }
    func testLowStorageRefusesToStart() async {
        let (svc, rt, _) = recorder(); svc.freeBytes = { 300_000_000 }
        await svc.start(); XCTAssertEqual(svc.state, .failed); XCTAssertTrue(svc.message.contains("storage")); XCTAssertEqual(rt.attempts, 0)
    }
    func testPhotosDeniedKeepsTheFileInTheApp() async {
        let (svc, rt, photos) = recorder(); photos.access = false
        defer { try? FileManager.default.removeItem(at: RecordingService.folder) }
        await svc.start(); XCTAssertEqual(svc.state, .recording); XCTAssertTrue(svc.message.contains("kept in the app"), svc.message)
        let file = tempVideo(); svc.stop(); rt.finish(file.path)
        await settle("saved") { svc.state == .saved }
        XCTAssertTrue(photos.saved.isEmpty); XCTAssertNotNil(svc.keptFile); XCTAssertTrue(FileManager.default.fileExists(atPath: svc.keptFile!.path))
        XCTAssertEqual(svc.history.first?.place, .kept)
        XCTAssertEqual(RecordingService.library().first, svc.keptFile); svc.deleteKept(svc.keptFile!); XCTAssertNil(svc.keptFile)
    }
    func testPhotosTurnedDownAsksBeforeRecordingAndCanRecordWithout() async {
        let (svc, rt, photos) = recorder(); photos.access = false; photos.isBlocked = true
        await svc.start()
        XCTAssertTrue(svc.photosBlockedAsk, "iOS will not ask again, so the app asks (Open Settings / Record without Photos)")
        XCTAssertEqual(svc.state, .idle); XCTAssertTrue(rt.started.isEmpty); XCTAssertEqual(photos.requests, 0)
        svc.recordWithoutPhotos()
        await settle("recording") { svc.state == .recording && !rt.started.isEmpty }
        XCTAssertFalse(svc.photosBlockedAsk); XCTAssertTrue(svc.message.contains("kept in the app"), svc.message)
    }
    func testPhotosNotAskedYetGetsTheSystemPrompt() async {
        let (svc, _, photos) = recorder(); photos.access = true; photos.isBlocked = false
        await svc.start()
        XCTAssertFalse(svc.photosBlockedAsk); XCTAssertEqual(photos.requests, 1, "the system prompt is requested on the first Record")
    }
    func testPhotosRefusingTheFileKeepsItInTheApp() async {
        let (svc, rt, photos) = recorder(); photos.fail = true
        defer { try? FileManager.default.removeItem(at: RecordingService.folder) }
        await svc.start(); svc.stop(); rt.finish(tempVideo().path)
        await settle("saved") { svc.state == .saved }
        XCTAssertNotNil(svc.keptFile); XCTAssertEqual(svc.history.first?.place, .kept)
    }
    func testTakesEndedByThePhoneAreExplainedAndSaved() async {
        for (reason, words) in [("background", "left the screen"), ("thermal", "too warm"), ("storage", "out of storage"), ("limit", "90 minute")] {
            let (svc, rt, photos) = recorder()
            await svc.start(); let file = tempVideo(); rt.finish(file.path, reason: reason)
            await settle("saved (\(reason))") { svc.state == .saved }
            XCTAssertTrue(svc.message.contains(words), "\(reason): \(svc.message)"); XCTAssertEqual(photos.saved.count, 1, "what was recorded is saved")
        }
    }
    func testLosingTheTVStopsAndSavesTheRecording() async {
        let (svc, rt, photos) = recorder(); await svc.start(); rt.roll()
        svc.displayConnected = { false }; svc.displayLost()
        await settle("stopping") { svc.state == .saving }; XCTAssertEqual(rt.stops, 1)
        let file = tempVideo(); rt.finish(file.path); await settle("saved") { svc.state == .saved }
        XCTAssertEqual(photos.saved, [file])
    }
    /// Going into a game can make iOS report the TV as gone for a moment (its picture mode changes).
    func testATVThatBlinksDoesNotEndTheRecording() async {
        let (svc, rt, _) = recorder(); await svc.start(); rt.roll()
        svc.displayLost()   // ...and it is back before the grace runs out
        try? await Task.sleep(for: .milliseconds(120))
        XCTAssertEqual(svc.state, .recording); XCTAssertEqual(rt.stops, 0)
    }
    func testAPartialRecordingAfterAProblemIsSaved() async {
        let (svc, rt, photos) = recorder()
        await svc.start(); let file = tempVideo()
        rt.handler?("{\"type\":\"capture\",\"state\":\"finished\",\"url\":\"\(file.path)\",\"seconds\":42,\"reason\":\"error\",\"partial\":true,\"message\":\"The recording stopped because the phone's video encoder had a problem. What was recorded before it stopped was kept.\"}")
        await settle("saved") { svc.state == .saved }
        XCTAssertEqual(photos.saved, [file]); XCTAssertTrue(svc.message.contains("video encoder had a problem") && svc.message.contains("Saved to Photos"), svc.message)
        XCTAssertEqual(svc.history.first?.seconds, 42)
    }
    func testAStopThatNeverFinishesDoesNotHangOnSavingAndALateFileIsStillSaved() async {
        let (svc, rt, photos) = recorder(); svc.savingTimeout = .milliseconds(60)
        await svc.start(); svc.stop(); XCTAssertEqual(svc.state, .saving); XCTAssertFalse(svc.canToggle)
        await settle("gave up") { svc.state == .failed }
        XCTAssertTrue(svc.message.contains("did not finish saving"), svc.message); XCTAssertTrue(svc.canToggle, "and the next recording can start")
        let file = tempVideo(); rt.finish(file.path)   // the recorder finishes after all
        await settle("late save") { photos.saved == [file] }
        XCTAssertEqual(svc.history.first?.place, .photos)
    }
    func testAFinishedEventWithoutItsFileIsNotReportedAsSaved() async {
        let (svc, rt, photos) = recorder()
        await svc.start(); rt.finish("/nonexistent/MotionSports-gone.mp4")
        await settle("failed") { svc.state == .failed }
        XCTAssertTrue(photos.saved.isEmpty); XCTAssertTrue(svc.message.contains("missing"), svc.message); XCTAssertEqual(svc.history.first?.place, .notSaved)
    }
    func testARecordingLeftBehindByAClosedAppIsRecovered() async {
        let (svc, _, photos) = recorder()
        let file = tempVideo()
        await svc.recoverLeftovers()
        XCTAssertEqual(photos.saved, [file]); XCTAssertEqual(svc.history.first?.note, "Recovered after the app closed")
    }
    func testGarbageEventsAreIgnored() async {
        let (svc, _, _) = recorder(); await svc.start()
        svc.receive("garbage"); svc.receive(#"{"type":"other","state":"finished"}"#)
        XCTAssertEqual(svc.state, .recording)
    }
}
