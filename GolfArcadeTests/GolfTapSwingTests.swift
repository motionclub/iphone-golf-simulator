import XCTest
@testable import GolfArcade

/// Tap to swing on the phone: a tap starts the swing at once, a second tap before contact cancels it.
/// Unity owns the swing; GolfTapSwing keeps the finger's side and the feels.
final class GolfTapSwingTests: XCTestCase {
    func testTapStartsOnlyWhenTheShotIsLinedUp() {
        var tap = GolfTapSwing()
        XCTAssertNil(tap.tap(canArm: false, now: 0), "no swing before Ready or outside Aim")
        XCTAssertEqual(tap.face, .tap)
        XCTAssertEqual(tap.tap(canArm: true, now: 0), .start)
        XCTAssertEqual(tap.face, .swinging, "the button answers the touch before Unity does")
    }

    func testSecondTapCancelsAndIsFeltOnceUnityHasReset() {
        var tap = GolfTapSwing()
        XCTAssertEqual(tap.tap(canArm: true, now: 0), .start)
        XCTAssertNil(tap.observe(phase: "Aim", shotReady: true, unityState: 2, now: 0.1))
        XCTAssertEqual(tap.tap(canArm: true, now: 0.5), .cancel)
        XCTAssertEqual(tap.face, .tap)
        XCTAssertNil(tap.observe(phase: "Aim", shotReady: true, unityState: 2, now: 0.6), "Unity may still be in its grace for contact")
        XCTAssertEqual(tap.observe(phase: "Aim", shotReady: true, unityState: 0, now: 0.7), .reset)
        XCTAssertNil(tap.observe(phase: "Aim", shotReady: true, unityState: 0, now: 0.8), "the reset is felt once")
        XCTAssertEqual(tap.tap(canArm: true, now: 1), .start, "tap again to swing again")
    }

    func testAReportFromBeforeTheTapIsNotAReset() {
        var tap = GolfTapSwing()
        XCTAssertEqual(tap.tap(canArm: true, now: 0), .start)
        XCTAssertNil(tap.observe(phase: "Aim", shotReady: true, unityState: 0, now: 0.05), "Unity has not answered yet")
        XCTAssertEqual(tap.face, .swinging)
        XCTAssertNil(tap.observe(phase: "Aim", shotReady: true, unityState: 2, now: 0.1))
        XCTAssertEqual(tap.face, .swinging)
    }

    func testAStrikeEndsTheSwingWithNoReset() {
        var tap = GolfTapSwing()
        XCTAssertEqual(tap.tap(canArm: true, now: 0), .start)
        _ = tap.observe(phase: "Aim", shotReady: true, unityState: 2, now: 0.1)
        XCTAssertNil(tap.observe(phase: "Flight", shotReady: false, unityState: 0, now: 1), "contact is not a reset")
        XCTAssertEqual(tap.face, .tap)
        XCTAssertNil(tap.tap(canArm: false, now: 1.1), "a tap in flight does nothing")
    }

    func testACancelThatStillMakesContactIsNotAReset() {
        var tap = GolfTapSwing()
        XCTAssertEqual(tap.tap(canArm: true, now: 0), .start)
        _ = tap.observe(phase: "Aim", shotReady: true, unityState: 2, now: 0.1)
        XCTAssertEqual(tap.tap(canArm: true, now: 0.5), .cancel)
        XCTAssertNil(tap.observe(phase: "Flight", shotReady: false, unityState: 0, now: 0.6), "struck inside the grace")
        XCTAssertNil(tap.observe(phase: "Aim", shotReady: true, unityState: 0, now: 5), "the next shot starts clean")
    }

    func testUnityEndingTheSwingResetsUntilTappedAgain() {
        // a new aim, a club change or a swing left alone ends it in Unity
        var tap = GolfTapSwing()
        XCTAssertEqual(tap.tap(canArm: true, now: 0), .start)
        _ = tap.observe(phase: "Aim", shotReady: true, unityState: 2, now: 0.1)
        XCTAssertEqual(tap.observe(phase: "Aim", shotReady: true, unityState: 0, now: 3), .reset)
        XCTAssertEqual(tap.face, .tap, "the button asks to be tapped again")
        XCTAssertEqual(tap.tap(canArm: true, now: 3.1), .start)
    }

    func testATapUnityNeverAnswersFreesTheButton() {
        var tap = GolfTapSwing()
        XCTAssertEqual(tap.tap(canArm: true, now: 0), .start)
        XCTAssertNil(tap.observe(phase: "Aim", shotReady: true, unityState: 0, now: GolfTapSwing.answerSeconds + 0.1), "no buzz for a tap that never took")
        XCTAssertEqual(tap.face, .tap)
    }

    func testLeavingAimOrReadyDropsTheSwing() {
        var tap = GolfTapSwing()
        XCTAssertEqual(tap.tap(canArm: true, now: 0), .start)
        _ = tap.observe(phase: "Aim", shotReady: true, unityState: 2, now: 0.1)
        XCTAssertNil(tap.observe(phase: "Aim", shotReady: false, unityState: 0, now: 0.2), "paused back behind Ready: no buzz")
        XCTAssertEqual(tap.face, .tap)
        XCTAssertEqual(tap.tap(canArm: true, now: 0.3), .start, "a stale swing never blocks the next tap")
    }
}
