import XCTest
import simd
@testable import GolfArcade

/// Play → Calibration: the lesson run through the real SportsSession (the phone side of the practice court). Unity is not running, so
/// the test plays Unity's part: it reports the swing the phone read and where the ball landed for each target the session fed.
@MainActor final class AimCalibrationTests: XCTestCase {
    private func calibrationSession() -> SportsSession {
        let s = SportsSession()
        s.sport = "tennis"; s.active = true; s.ready = true; s.paused = false; s.calibrationMode = true
        return s
    }
    /// The session feeds one ball per target after a short pause; wait until it has asked for sequence `after` + 1.
    private func nextFeed(_ s: SportsSession, after: Int) async throws -> Int {
        for _ in 0..<80 {
            if s.aimWaiting, s.aimFeedSequence > after { return s.aimFeedSequence }
            try await Task.sleep(for: .milliseconds(50))
        }
        XCTFail("no aim ball was fed after sequence \(after)")
        return after
    }
    private func swing(_ s: SportsSession, angle: Double, facing: Double) {
        let now = SportsRuntime.shared().clock()
        let trace = (0..<5).map { TennisAimSample(time: now + 0.5 + Double($0) * 0.01 - 0.04, angle: angle - Double(4 - $0), rate: 6 + Double($0)) }
        s.motion.onAimSwing?(TennisAimSwing(time: now + 0.5, angle: angle, facing: facing, trace: trace))
    }

    func testFullLessonLearnsSavesAndLogsEveryTake() async throws {
        let s = calibrationSession()
        s.restartCalibration()   // forget any saved profile, then start
        XCTAssertNotNil(s.aimLesson)
        var seq = 0, takes = 0
        while let lesson = s.aimLesson, lesson.phase != .complete, takes < 60 {
            takes += 1
            seq = try await nextFeed(s, after: seq)
            let trial = try XCTUnwrap(s.aimLesson?.current)
            // the swing the phone read: the face angle for this lane (a backhand grip sits 8 degrees off); then where Unity says the ball landed
            swing(s, angle: Double(trial.lane) * 32 + Double(trial.wing) * 8, facing: trial.wing == 0 ? 1 : -1)
            s.receiveAimLanding("\(seq)|\(Double(trial.lane) * 3)|8.000|1")
        }
        XCTAssertEqual(s.aimLesson?.phase, .complete, "12 learning takes and 12 checking takes finish the lesson")
        XCTAssertEqual(takes, 24)
        XCTAssertTrue(s.calibrationComplete)
        let profile = try XCTUnwrap(s.storedAimProfile(), "the finished profile is saved for every later match")
        XCTAssertEqual(profile.forehand.left, -32, accuracy: 0.5); XCTAssertEqual(profile.forehand.right, 32, accuracy: 0.5)
        XCTAssertEqual(profile.backhand.neutral, 8, accuracy: 0.5)
        try await Task.sleep(for: .milliseconds(600))   // the log is written off the main thread
        // every take is in the diagnostics log with what the analyser needs: phase, wing, lane, angle, landing and the face trace
        let log = SportsDiagnostics.files.first.flatMap { try? String(contentsOf: $0, encoding: .utf8) } ?? ""
        let lines = log.split(separator: "\n").filter { $0.contains("aimcal take") }.suffix(24)
        XCTAssertEqual(lines.count, 24)
        XCTAssertTrue(lines.contains { $0.contains("phase=capture wing=0 lane=-1 angle=-32.00 face=nan facing=1 landingX=-3.000 legal=1 accepted=1 trace=-40:-36.0:6.00:0.00:0.00,") }, "first capture take is logged with its trace")
        XCTAssertEqual(lines.filter { $0.contains("phase=capture") }.count, 12)
        XCTAssertEqual(lines.filter { $0.contains("phase=check") }.count, 12)
        XCTAssertTrue(log.contains("aimcal saved"))
    }

    func testStaleOrMalformedLandingsAreIgnored() async throws {
        let s = calibrationSession()
        s.restartCalibration()
        let seq = try await nextFeed(s, after: 0)
        let before = s.aimLesson?.index
        s.receiveAimLanding("garbage")
        s.receiveAimLanding("\(seq + 5)|0.000|8.000|1")      // not the ball just fed
        s.receiveAimLanding("\(seq)|nan|8.000|1")
        XCTAssertEqual(s.aimLesson?.index, before)
        XCTAssertTrue(s.aimWaiting, "still waiting for the real landing")
        // a landing with no swing read tells the player to try again and feeds another ball
        s.receiveAimLanding("\(seq)|0.000|8.000|1")
        XCTAssertEqual(s.aimLesson?.index, before)
        XCTAssertEqual(s.aimLessonMessage, "Swing through toward the target and try again.")
    }

    /// Adnan 11-15: aim must come from the swing's motion, not from where the phone is or which way it points.
    func testSwingDirectionIsTheMotionNotWhereThePhoneIs() throws {
        let tv = 0.7   // the TV's heading in the motion frame (radians); headings grow to the player's left
        func swing(degreesRight deg: Double, start: Double = 0) -> [TennisSwingPath.Sample] {
            let h = tv - deg * .pi / 180
            return (0..<20).map { TennisSwingPath.Sample(time: start + Double($0) * 0.01, x: 30 * cos(h), y: 30 * sin(h)) }
        }
        for deg in [0.0, 30, -25, 12] {
            XCTAssertEqual(try XCTUnwrap(TennisSwingPath.angle(swing(degreesRight: deg), from: 0, to: 0.2, tvHeading: tv)), deg, accuracy: 0.01)
        }
        // a phone held still, or moved slowly into place before the swing, has no swing direction: it cannot aim
        let still = (0..<20).map { TennisSwingPath.Sample(time: Double($0) * 0.01, x: 0.2, y: 0.1) }
        XCTAssertNil(TennisSwingPath.angle(still, from: 0, to: 0.2, tvHeading: tv))
        // the turn out of the backswing (slow) and a swing heading away from the TV have no direction: straight, never a side
        let slow = (0..<20).map { TennisSwingPath.Sample(time: Double($0) * 0.01, x: 4 * cos(tv + 1), y: 4 * sin(tv + 1)) }
        XCTAssertNil(TennisSwingPath.angle(slow, from: 0, to: 0.2, tvHeading: tv))
        XCTAssertNil(TennisSwingPath.angle(swing(degreesRight: 150), from: 0, to: 0.2, tvHeading: tv))
        XCTAssertNil(TennisSwingPath.angle(swing(degreesRight: -120), from: 0, to: 0.2, tvHeading: tv))
        // CoreMotion's userAcceleration is the opposite of the real acceleration: a phone accelerating toward the TV
        // reports userAcceleration away from it, and that must read as toward the TV (11-16: it read inverted)
        let level = simd_quatd(angle: 0, axis: SIMD3<Double>(0, 0, 1))
        let real = TennisSwingPath.roomAcceleration(user: SIMD3<Double>(-cos(tv), -sin(tv), 0), attitude: level)
        let split = TennisSwingPath.split(x: real.x, y: real.y, tvHeading: tv)
        XCTAssertEqual(split.forward, 9.81, accuracy: 1e-6); XCTAssertEqual(split.side, 0, accuracy: 1e-6)
        // moving the phone to the right before the swing (outside the swing's window) changes nothing
        let carried = (0..<30).map { TennisSwingPath.Sample(time: -0.5 + Double($0) * 0.01, x: 40 * sin(tv), y: -40 * cos(tv)) } + swing(degreesRight: 0)
        XCTAssertEqual(try XCTUnwrap(TennisSwingPath.angle(carried, from: 0, to: 0.2, tvHeading: tv)), 0, accuracy: 0.01)
        // the split used in the log: toward the TV is forward, its right is side
        let toward = TennisSwingPath.split(x: cos(tv), y: sin(tv), tvHeading: tv)
        XCTAssertEqual(toward.forward, 1, accuracy: 1e-9); XCTAssertEqual(toward.side, 0, accuracy: 1e-9)
        let right = TennisSwingPath.split(x: sin(tv), y: -cos(tv), tvHeading: tv)
        XCTAssertEqual(right.side, 1, accuracy: 1e-9); XCTAssertEqual(right.forward, 0, accuracy: 1e-9)
    }

    func testWrongGripDoesNotCountAndNothingStartsOutsideCalibration() async throws {
        let s = calibrationSession()
        s.restartCalibration()
        let seq = try await nextFeed(s, after: 0)
        let trial = try XCTUnwrap(s.aimLesson?.current)
        swing(s, angle: 0, facing: trial.wing == 0 ? -1 : 1)   // the other grip
        s.receiveAimLanding("\(seq)|0.000|8.000|1")
        XCTAssertEqual(s.aimLesson?.index, 0)
        XCTAssertTrue(s.aimLessonMessage.contains("grip"))
        let plain = SportsSession(); plain.sport = "tennis"; plain.active = true; plain.ready = true; plain.paused = false
        plain.beginAimingSetup()
        XCTAssertNil(plain.aimLesson, "a normal match never starts the lesson")
    }
}
