import XCTest
import simd
import SwiftUI
import UIKit
import CoreImage
@testable import GolfArcade

/// Point and fill (SportsGlow, 11-22), on synthetic camera frames: a room, a TV in it whose picture around the setup card dims and
/// brightens to the wave `delay` behind the game, a lamp that flickers on its own, hand-shake noise.
final class SportsGlowTests: XCTestCase {
    private let columns = SportsScreenFinder.columns, rows = 60

    /// 60 fps frames over `seconds` (glow clock from `start`). The TV fills `tv` (cells: x0, y0, x1, y1, exclusive ends) with the card
    /// (not glowing) in its middle third; the lamp (if any) flickers at 1.3 Hz.
    private func frames(delay: Double, tv: (Int, Int, Int, Int)? = (20, 15, 60, 42), seconds: Double = 2.0, start: Double = 100,
                        noise: Double = 3, lamp: Bool = true, scene: Double = 150, seed: UInt64 = 7) -> [SportsScreenFinder.Frame] {
        var rng = SeededGenerator(seed: seed)
        let room = (0..<(columns * rows)).map { _ in Double.random(in: 40...110, using: &rng) }
        var out = [SportsScreenFinder.Frame]()
        var t = start + 0.003
        while t < start + seconds {
            var cells = [UInt8](repeating: 0, count: columns * rows)
            for y in 0..<rows {
                for x in 0..<columns {
                    var level = room[y * columns + x]
                    if let tv, x >= tv.0, x < tv.2, y >= tv.1, y < tv.3 {
                        let w = tv.2 - tv.0, h = tv.3 - tv.1
                        let card = x >= tv.0 + w / 3 && x < tv.2 - w / 3 && y >= tv.1 + h / 3 && y < tv.3 - h / 3
                        level = card ? 215 : scene * (1 - SportsGlow.veil(t - delay))
                    }
                    if lamp, x >= 66, x < 74, y >= 5, y < 12 { level = 170 + 40 * sin(2 * .pi * 1.3 * t) }
                    level += Double.random(in: -noise...noise, using: &rng)
                    cells[y * columns + x] = UInt8(max(0, min(255, level)))
                }
            }
            out.append(.init(time: t, cells: cells, attitude: nil))
            t += 1.0 / 60
        }
        return out
    }

    func testFindsTheTVAndItsDelay() throws {
        for delay in [0.04, 0.14, 0.3, 0.52] {
            let reading = try XCTUnwrap(SportsGlowReader.read(frames(delay: delay), rows: rows), "delay \(delay)")
            XCTAssertTrue(reading.seeing, "delay \(delay): match \(reading.match)")
            XCTAssertEqual(reading.delay, delay, accuracy: 0.006, "delay \(delay)")
            XCTAssertEqual(reading.at.x, 0.5, accuracy: 0.04, "the TV's middle, across")
            XCTAssertEqual(reading.at.y, 28.5 / 60, accuracy: 0.05, "the TV's middle, down")
        }
    }

    func testAnOffCentreSmallTVIsStillFound() throws {
        let reading = try XCTUnwrap(SportsGlowReader.read(frames(delay: 0.12, tv: (4, 40, 22, 52)), rows: rows))
        XCTAssertTrue(reading.seeing)
        XCTAssertEqual(reading.delay, 0.12, accuracy: 0.008)
        XCTAssertLessThan(reading.at.x, 0.3); XCTAssertGreaterThan(reading.at.y, 0.65)
    }

    func testNoTVInViewIsNotSeen() {
        // a room with only a flickering lamp: the lamp does not follow the wave
        let reading = SportsGlowReader.read(frames(delay: 0.1, tv: nil), rows: rows)
        XCTAssertFalse(reading?.seeing ?? false, "a lamp is not a TV: match \(reading?.match ?? 0)")
    }

    func testADimRoomAndShakyHandStillRead() throws {
        let reading = try XCTUnwrap(SportsGlowReader.read(frames(delay: 0.18, noise: 7, scene: 70, seed: 3), rows: rows))
        XCTAssertTrue(reading.seeing, "match \(reading.match)")
        XCTAssertEqual(reading.delay, 0.18, accuracy: 0.012)
    }

    func testTooFewFramesWaits() {
        XCTAssertNil(SportsGlowReader.read(frames(delay: 0.1, seconds: 0.8), rows: rows), "under a second and a bit: not yet")
    }

    func testTheGlowIsGentle() {
        let veils = stride(from: 0.0, through: 20, by: 0.01).map { SportsGlow.veil($0) }
        XCTAssertGreaterThanOrEqual(veils.min()!, SportsGlow.lightest - 1e-9)
        XCTAssertLessThanOrEqual(veils.max()!, SportsGlow.dimmest + 1e-9, "never black, never a flash")
        XCTAssertGreaterThan(veils.max()! - veils.min()!, 0.25, "but enough for a camera to read")
    }

    // MARK: the circle

    func testTheCircleFillsOnlyWhileEveryoneIsOn() {
        var fill = SportsGlowFill()
        for _ in 0..<10 { fill.add(delay: 0.14, heading: 0.3); fill.step(0.1, everyoneOn: true) }
        let afterOne = fill.progress
        XCTAssertGreaterThan(afterOne, 0.25)
        for _ in 0..<10 { fill.step(0.1, everyoneOn: false) }
        XCTAssertLessThan(fill.progress, afterOne, "one phone off the TV: the circle drains")
        for _ in 0..<40 { fill.add(delay: 0.14, heading: 0.3); fill.step(0.1, everyoneOn: true) }
        XCTAssertTrue(fill.done)
        XCTAssertEqual(fill.delay ?? 0, 0.14, accuracy: 1e-9)
        XCTAssertEqual(fill.heading ?? 0, 0.3, accuracy: 1e-9)
    }

    func testSteadyReadingsFillInAboutTwoAndAHalfSeconds() {
        var fill = SportsGlowFill(), elapsed = 0.0
        while !fill.done && elapsed < 10 { fill.add(delay: 0.1 + Double.random(in: -0.004...0.004), heading: 1); fill.step(0.1, everyoneOn: true); elapsed += 0.1 }
        XCTAssertLessThan(elapsed, 3.2)
        var wobbly = SportsGlowFill(); elapsed = 0
        while !wobbly.done && elapsed < 20 { wobbly.add(delay: Double.random(in: 0.05...0.3), heading: 1); wobbly.step(0.1, everyoneOn: true); elapsed += 0.1 }
        XCTAssertGreaterThan(elapsed, 5, "readings that wander fill slowly")
    }

    func testADrainedCircleForgetsItsReadings() {
        var fill = SportsGlowFill()
        for _ in 0..<5 { fill.add(delay: 0.2, heading: 2); fill.step(0.1, everyoneOn: true) }
        for _ in 0..<30 { fill.step(0.1, everyoneOn: false) }
        XCTAssertEqual(fill.progress, 0)
        XCTAssertNil(fill.delay, "a circle that drained to nothing starts over")
    }

    func testHeadingsAverageAcrossTheBackOfTheCircle() {
        XCTAssertEqual(abs(SportsGlowFill.meanHeading([.pi - 0.1, -.pi + 0.1]) ?? 0), .pi, accuracy: 1e-9)
    }

    func testLobbySteps() {
        XCTAssertEqual(SportsGlowStep.encode(seeing: true, progress: 40), "glow:on:40")
        XCTAssertEqual(SportsGlowStep.seeing("glow:on:40"), true)
        XCTAssertEqual(SportsGlowStep.seeing("glow:off"), false)
        XCTAssertNil(SportsGlowStep.seeing("pointed"))
        XCTAssertEqual(SportsGlowStep.progress("glow:on:40") ?? 0, 0.4, accuracy: 1e-9)
        XCTAssertNil(SportsGlowStep.progress("glow:on"))
        XCTAssertTrue(SportsGlowStep.pastCircle("glowDone")); XCTAssertTrue(SportsGlowStep.pastCircle("ready"))
        XCTAssertFalse(SportsGlowStep.pastCircle("glow:on:90"))
    }
}

/// Proof stills of the circle, on the TV (over the tennis court art) and on the phone, solo and with two phones on one TV. Written to
/// work/glow-setup-1122/proof/. A recorder, not a gate.
@MainActor final class SportsGlowSnapshotTests: XCTestCase {
    private let repo = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
    private var folder: URL {
        let url = repo.appendingPathComponent("work/glow-setup-1122/proof")
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }
    private func save<V: View>(_ view: V, _ name: String, _ size: CGSize) async throws {
        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        let host = UIHostingController(rootView: view); host.safeAreaRegions = []
        let window = UIWindow(windowScene: scene)
        window.frame = CGRect(origin: .zero, size: size); window.rootViewController = host; window.isHidden = false
        host.view.frame = window.bounds; host.view.layoutIfNeeded()
        try await Task.sleep(for: .seconds(1.0))
        let image = UIGraphicsImageRenderer(size: size).image { _ in host.view.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
        try XCTUnwrap(image.pngData()).write(to: folder.appendingPathComponent("\(name).png"))
        window.isHidden = true
    }
    private func court() -> some View {
        let path = repo.appendingPathComponent("ArtDir/ui/tv-results-calibration/scenes/tennis.jpg").path
        return Image(uiImage: UIImage(contentsOfFile: path) ?? UIImage()).resizable().scaledToFill()
    }
    private func tennis(_ session: SportsSession, owns: Bool = true) {
        session.timingStore = UserDefaults(suiteName: "glow-snap-\(UUID().uuidString)")!
        session.active = true; session.ready = true; session.displayConnected = owns
        session.sport = "tennis"; session.motion.fixtureSensors = true; session.loading.cancel()
        session.setupStage = .scan; session.paused = true
    }
    private func fill(_ session: SportsSession, looks: Int, seeing: Bool = true) {
        var t = 500.0
        for _ in 0..<looks { t += 0.1; session.receiveGlow(.init(time: t, seeing: seeing, delay: 0.14, match: 0.93, heading: 0.2)) }
    }

    /// A filmed demo (run with TEST_RUNNER_GLOW_DEMO=1): Adnan's phone has the TV, Sam's is a controller. Adnan finds the TV, waits for
    /// Sam, both fill, Sam looks away (it drains), both fill to the end, the match counts down. Frames of the TV and of Adnan's phone
    /// (its viewfinder fed a picture of the room with that TV frame in it) go to work/glow-setup-1122/demo/.
    func testDemoFilm() async throws {
        try XCTSkipUnless(ProcessInfo.processInfo.environment["GLOW_DEMO"] != nil, "film only on request")
        let out = repo.appendingPathComponent("work/glow-setup-1122/demo")
        try? FileManager.default.removeItem(at: out)
        try FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
        let session = SportsSession(), service = MultiplayerService.shared
        try service.enableMock(count: 2, player: Player(name: "Adnan", colorIndex: 0))
        defer { service.leave(); session.active = false }
        service.mockState(phase: .calibrating)
        service.mockOneTV(otherStep: "glow:off", mineHasTV: true)
        tennis(session)
        session.debugSetOnlineMatch("glow-demo", seat: 0)
        session.debugBeginOnlineSetup()

        let scene = try XCTUnwrap(UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.first)
        func window<V: View>(_ view: V, _ size: CGSize) -> (UIWindow, UIView) {
            let host = UIHostingController(rootView: view); host.safeAreaRegions = []
            let w = UIWindow(windowScene: scene); w.frame = CGRect(origin: .zero, size: size); w.rootViewController = host; w.isHidden = false
            host.view.frame = w.bounds; host.view.layoutIfNeeded()
            return (w, host.view)
        }
        let tvSize = CGSize(width: 1280, height: 720), phoneSize = CGSize(width: 402, height: 874)
        let (tvWindow, tvView) = window(ZStack { court(); TennisSetupTVView(session: session, service: service) }, tvSize)
        let (phoneWindow, phoneView) = window(ZStack { MapSkin.current.bottom.ignoresSafeArea(); TennisSetupFlow(session: session, service: service) }, phoneSize)
        defer { tvWindow.isHidden = true; phoneWindow.isHidden = true }
        try await Task.sleep(for: .seconds(1))

        // the room the camera sees: the TV frame on a dim wall, upright for a phone held upright (the sensor's buffer is sideways)
        let context = CIContext()
        func cameraBuffer(_ tv: UIImage, onTV: Bool, sway: Double) -> CVPixelBuffer? {
            let room = CGSize(width: 720, height: 1280)
            let picture = UIGraphicsImageRenderer(size: room).image { ctx in
                UIColor(red: 0.16, green: 0.14, blue: 0.13, alpha: 1).setFill(); ctx.fill(CGRect(origin: .zero, size: room))
                UIColor(red: 0.22, green: 0.19, blue: 0.16, alpha: 1).setFill(); ctx.fill(CGRect(x: 0, y: 820, width: 720, height: 460))
                let w = 560.0, h = w * 9 / 16, x = (onTV ? 80 : -470) + sway, y = 470.0 + sway * 0.4
                UIColor.black.setFill(); ctx.fill(CGRect(x: x - 10, y: y - 10, width: w + 20, height: h + 20))
                tv.draw(in: CGRect(x: x, y: y, width: w, height: h))
            }
            guard let cg = picture.cgImage else { return nil }
            let sideways = CIImage(cgImage: cg).oriented(.left)
            let moved = sideways.transformed(by: CGAffineTransform(translationX: -sideways.extent.minX, y: -sideways.extent.minY))
            var buffer: CVPixelBuffer?
            CVPixelBufferCreate(nil, Int(moved.extent.width), Int(moved.extent.height), kCVPixelFormatType_32BGRA,
                                [kCVPixelBufferIOSurfacePropertiesKey: [:]] as CFDictionary, &buffer)
            if let buffer { context.render(moved, to: buffer) }
            return buffer
        }

        // the scene, in tenths of a second: is Adnan's phone on the TV, is Sam's
        func adnanOn(_ k: Int) -> Bool { k >= 8 }
        func samStep(_ k: Int) -> String { (k >= 24 && k < 40) || k >= 50 ? "glow:on" : "glow:off" }
        var frame = 0, k = 0, doneAt: Int?
        var t = 2000.0
        while k < 140 {
            if doneAt == nil {
                service.mockOneTV(otherStep: samStep(k), mineHasTV: true)
                t += 0.1
                let on = adnanOn(k)
                session.receiveGlow(.init(time: t, seeing: on, delay: on ? 0.14 + Double.random(in: -0.003...0.003) : nil, match: on ? 0.93 : 0.1, heading: on ? 0.2 : nil))
                if !session.glowActive { doneAt = k }
            } else if let d = doneAt, k == d + 14 {
                t += 0.1
                service.mockOneTV(otherStep: "ready", mineHasTV: true); service.mockStartCountdown()
            } else if let d = doneAt, k > d + 48 { break } else { t += 0.1 }
            // the film plays back at 10 frames a second of the scene: the TV's glow follows the scene's clock, not the slow capture
            SportsGlow.clockOffset = t - CACurrentMediaTime()
            try await Task.sleep(for: .milliseconds(40))   // the main loop runs: the gate, the lobby, the TV's display link
            let tv = UIGraphicsImageRenderer(size: tvSize).image { _ in tvView.drawHierarchy(in: tvWindow.bounds, afterScreenUpdates: true) }
            if session.setupStage == .scan, let buffer = cameraBuffer(tv, onTV: adnanOn(k), sway: 6 * sin(Double(k) / 5)) { session.motion.preview?.show(buffer) }
            let phone = UIGraphicsImageRenderer(size: phoneSize).image { _ in phoneView.drawHierarchy(in: phoneWindow.bounds, afterScreenUpdates: true) }
            try XCTUnwrap(tv.pngData()).write(to: out.appendingPathComponent(String(format: "tv_%04d.png", frame)))
            try XCTUnwrap(phone.pngData()).write(to: out.appendingPathComponent(String(format: "phone_%04d.png", frame)))
            frame += 1; k += 1
        }
        XCTAssertNotNil(doneAt, "the circle filled")
    }

    func testSoloCircleScreens() async throws {
        let session = SportsSession(); tennis(session)
        session.beginAxisCapture()
        try await save(ZStack { court(); TennisSetupTVView(session: session) }, "01-tv-solo-looking", CGSize(width: 1280, height: 720))
        try await save(ZStack { MapSkin.current.bottom.ignoresSafeArea(); TennisSetupFlow(session: session) }, "02-phone-solo-looking", CGSize(width: 402, height: 874))
        fill(session, looks: 18)
        try await save(ZStack { court(); TennisSetupTVView(session: session) }, "03-tv-solo-filling", CGSize(width: 1280, height: 720))
        try await save(ZStack { MapSkin.current.bottom.ignoresSafeArea(); TennisSetupFlow(session: session) }, "04-phone-solo-filling", CGSize(width: 402, height: 874))
        session.active = false
    }

    func testSharedCircleScreens() async throws {
        let session = SportsSession(), service = MultiplayerService.shared
        try service.enableMock(count: 2, player: Player(name: "Adnan", colorIndex: 0))
        defer { service.leave(); session.active = false }
        service.mockState(phase: .calibrating)
        service.mockOneTV(otherStep: "glow:off", mineHasTV: true)
        tennis(session)
        session.debugSetOnlineMatch("glow-snap", seat: 0)
        session.debugBeginOnlineSetup()
        fill(session, looks: 20)
        try await save(ZStack { court(); TennisSetupTVView(session: session) }, "05-tv-shared-waiting", CGSize(width: 1280, height: 720))
        try await save(ZStack { MapSkin.current.bottom.ignoresSafeArea(); TennisSetupFlow(session: session) }, "06-phone-shared-waiting", CGSize(width: 402, height: 874))
        service.mockOneTV(otherStep: "glow:on", mineHasTV: true)
        fill(session, looks: 14)
        try await save(ZStack { court(); TennisSetupTVView(session: session) }, "07-tv-shared-filling", CGSize(width: 1280, height: 720))
    }
}

/// Repeatable noise for the synthetic frames.
private struct SeededGenerator: RandomNumberGenerator {
    var state: UInt64
    init(seed: UInt64) { state = seed &+ 0x9E3779B97F4A7C15 }
    mutating func next() -> UInt64 {
        state = state &* 6364136223846793005 &+ 1442695040888963407
        var z = state; z = (z ^ (z >> 30)) &* 0xBF58476D1CE4E5B9; z = (z ^ (z >> 27)) &* 0x94D049BB133111EB
        return z ^ (z >> 31)
    }
}
