import XCTest
@testable import GolfArcade

/// Hold to swing on the phone: pressing arms, the swing happens while held, letting go before
/// contact resets it. Unity owns the swing; GolfHoldSwing keeps the finger's side and the feels.
final class GolfHoldSwingTests: XCTestCase {
    func testPressArmsOnlyWhenTheShotIsLinedUp() {
        var hold = GolfHoldSwing()
        XCTAssertFalse(hold.press(canArm: false), "no swing before Ready or outside Aim")
        XCTAssertEqual(hold.face, .hold)
        XCTAssertTrue(hold.press(canArm: true))
        XCTAssertFalse(hold.press(canArm: true), "one press, one golfStartSwing")
        XCTAssertEqual(hold.face, .holdStill, "the button answers the touch before Unity does")
    }

    func testHeldThroughGripAndContactStrikesWithNoReset() {
        var hold = GolfHoldSwing()
        XCTAssertTrue(hold.press(canArm: true))
        XCTAssertNil(hold.observe(phase: "Aim", shotReady: true, unityState: 0), "a report from before the press is not a reset")
        XCTAssertNil(hold.observe(phase: "Aim", shotReady: true, unityState: 1))
        XCTAssertEqual(hold.face, .holdStill)
        XCTAssertEqual(hold.observe(phase: "Aim", shotReady: true, unityState: 2), .armed, "the grip is set: one firm tap")
        XCTAssertEqual(hold.face, .swing)
        XCTAssertNil(hold.observe(phase: "Aim", shotReady: true, unityState: 2), "armed buzzes once")
        XCTAssertNil(hold.observe(phase: "Flight", shotReady: false, unityState: 0), "contact is not a reset")
        XCTAssertFalse(hold.held, "the shot ends the hold")
        XCTAssertFalse(hold.release(), "lifting the thumb after contact sends nothing")
        XCTAssertEqual(hold.face, .hold)
    }

    func testLettingGoBeforeContactResets() {
        var hold = GolfHoldSwing()
        XCTAssertTrue(hold.press(canArm: true))
        _ = hold.observe(phase: "Aim", shotReady: true, unityState: 2)
        XCTAssertTrue(hold.release(), "the lift sends golfReleaseSwing")
        XCTAssertEqual(hold.face, .hold)
        XCTAssertNil(hold.observe(phase: "Aim", shotReady: true, unityState: 2), "Unity may still be in its grace for contact")
        XCTAssertEqual(hold.observe(phase: "Aim", shotReady: true, unityState: 0), .reset)
        XCTAssertNil(hold.observe(phase: "Aim", shotReady: true, unityState: 0), "the reset is felt once")
        XCTAssertTrue(hold.press(canArm: true), "hold again to swing again")
    }

    func testLetGoInTheDownswingThatStillMakesContactIsNotAReset() {
        var hold = GolfHoldSwing()
        XCTAssertTrue(hold.press(canArm: true))
        _ = hold.observe(phase: "Aim", shotReady: true, unityState: 2)
        XCTAssertTrue(hold.release())
        XCTAssertNil(hold.observe(phase: "Flight", shotReady: false, unityState: 0), "struck inside the grace")
        XCTAssertNil(hold.observe(phase: "Aim", shotReady: true, unityState: 0), "the next shot starts clean")
    }

    func testAQuickTapIsAResetAndNeverSticks() {
        var hold = GolfHoldSwing()
        XCTAssertTrue(hold.press(canArm: true))
        XCTAssertTrue(hold.release())
        XCTAssertEqual(hold.observe(phase: "Aim", shotReady: true, unityState: 0), .reset, "a tap is not a hold: the buzz says so")
        XCTAssertFalse(hold.held)
    }

    func testUnityEndingTheSwingWhileHeldResetsUntilPressedAgain() {
        // a new aim, a club change or a swing stopped short ends it in Unity while the thumb is still down
        var hold = GolfHoldSwing()
        XCTAssertTrue(hold.press(canArm: true))
        _ = hold.observe(phase: "Aim", shotReady: true, unityState: 2)
        XCTAssertEqual(hold.observe(phase: "Aim", shotReady: true, unityState: 0), .reset)
        XCTAssertEqual(hold.face, .hold, "the button asks to be held again")
        XCTAssertFalse(hold.release(), "the old thumb's lift sends nothing: Unity is not tracking")
        XCTAssertTrue(hold.press(canArm: true))
    }

    func testLeavingAimOrReadyDropsTheHold() {
        var hold = GolfHoldSwing()
        XCTAssertTrue(hold.press(canArm: true))
        _ = hold.observe(phase: "Aim", shotReady: true, unityState: 1)
        XCTAssertNil(hold.observe(phase: "Aim", shotReady: false, unityState: 0), "paused back behind Ready: no buzz")
        XCTAssertFalse(hold.held)
        XCTAssertTrue(hold.press(canArm: true), "a stale hold never blocks the next press")
    }
}
