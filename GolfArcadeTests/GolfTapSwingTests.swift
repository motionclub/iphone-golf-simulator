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

/// 11-20: a quick swipe up on the aim pad goes to the aerial view, a swipe down comes back; slow or sideways drags stay aim.
final class GolfLookFlickTests: XCTestCase {
    private func flick(_ dx: CGFloat, _ dy: CGFloat, vy: CGFloat, distance: CGFloat = 45) -> Bool? {
        GolfLookFlick.direction(translation: CGSize(width: dx, height: dy), velocity: CGSize(width: 0, height: vy), distance: distance)
    }
    func testAQuickSwipeUpIsAerial() {
        XCTAssertEqual(flick(5, -80, vy: -900), true)
        XCTAssertEqual(flick(0, -32, vy: -600, distance: 30), true, "the handheld pad's shorter swipe")
    }
    func testAQuickSwipeDownComesBack() {
        XCTAssertEqual(flick(-8, 90, vy: 1100), false)
    }
    func testASlowSlideIsNotAFlick() {
        XCTAssertNil(flick(0, -120, vy: -120), "a slow slide follows the finger (GolfLookSlide) rather than jumping to the top")
    }
    func testSidewaysAndShortDragsStayAim() {
        XCTAssertNil(flick(90, -60, vy: -900), "mostly sideways is aiming")
        XCTAssertNil(flick(0, -20, vy: -900), "too short to be a swipe")
    }
    func testADragThatReversesAtTheEndIsNotAFlick() {
        XCTAssertNil(flick(0, -80, vy: 500), "up then flicked back down is not a swipe up")
    }
}

/// 11-23, Adnan: "it still doesnt let you slide up" — a slow slide up the aim pad is the aerial view, following the finger.
final class GolfLookSlideTests: XCTestCase {
    func testAMostlyVerticalDragIsALookSlide() {
        XCTAssertEqual(GolfLookSlide.axis(translation: CGSize(width: 3, height: -20)), .look)
        XCTAssertEqual(GolfLookSlide.axis(translation: CGSize(width: -4, height: 25)), .look, "down too, to come back")
    }
    func testSidewaysDragsAim() {
        XCTAssertEqual(GolfLookSlide.axis(translation: CGSize(width: 20, height: -5)), .aim)
        XCTAssertEqual(GolfLookSlide.axis(translation: CGSize(width: 14, height: -14)), .aim, "a diagonal is aim")
    }
    func testTooShortIsUndecided() {
        XCTAssertNil(GolfLookSlide.axis(translation: CGSize(width: 0, height: -10)))
    }
    func testTheViewFollowsTheFinger() {
        XCTAssertEqual(GolfLookSlide.value(start: 0, dy: -85, range: 170), 0.5, accuracy: 1e-9, "half the range, half the climb")
        XCTAssertEqual(GolfLookSlide.value(start: 0, dy: -400, range: 170), 1, "stops at the full aerial view")
        XCTAssertEqual(GolfLookSlide.value(start: 1, dy: 85, range: 170), 0.5, accuracy: 1e-9, "sliding down comes back")
        XCTAssertEqual(GolfLookSlide.value(start: 0.2, dy: 300, range: 170), 0, "never below the golfer's view")
    }
}
