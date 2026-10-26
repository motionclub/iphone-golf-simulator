import XCTest

final class SportsNavigationTests:XCTestCase {
    func testNativeMenuHasNoScanGateAndExplainsMissingUnity() {
        let app=XCUIApplication(); app.launch()
        XCTAssertTrue(app.navigationBars["Sports Arcade"].waitForExistence(timeout:10))
        let preview=app.buttons["startUnityPreview"]
        let form=app.collectionViews.firstMatch
        for _ in 0..<8 { if preview.exists && preview.isHittable { break }; form.swipeUp() }
        XCTAssertTrue(preview.exists)
        // The action must recheck routing rather than remain disabled by stale state.
        XCTAssertTrue(app.buttons["startExternalGame"].isEnabled)
        preview.tap()
        app.swipeDown(); app.swipeDown()
        XCTAssertTrue(app.staticTexts.containing(NSPredicate(format:"label CONTAINS %@","physical-device build")).firstMatch.waitForExistence(timeout:5))
    }
}


extension SportsNavigationTests {
    @MainActor func testGolfControllerOnlyAfterLoadingAndReady() {
        let app = XCUIApplication()
        for flag in ["-golfControllerNotReady", "-golfControllerLoading"] {
            app.launchArguments = ["-golfControllerDesign", flag]; app.launch()
            XCTAssertFalse(app.buttons["golf-club-next"].waitForExistence(timeout: 3), "Controller must be absent: \(flag)")
            XCTAssertFalse(app.descendants(matching: .any)["golf-course-preview"].exists)
            app.terminate()
        }
        app.launchArguments = ["-golfControllerDesign"]; app.launch()
        XCTAssertTrue(app.buttons["golf-club-next"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.descendants(matching: .any)["golf-course-preview"].exists)
    }
    @MainActor func testGolfPauseProvidesSettingsResumeAndLeaveWithoutCalibration() {
        let app = XCUIApplication(); app.launchArguments = ["-golfControllerDesign"]; app.launch()
        XCTAssertTrue(app.buttons["golf-club-next"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["golf-club-next"].isEnabled)
        XCTAssertTrue(app.buttons["golf-club-previous"].isEnabled)
        XCTAssertTrue(app.descendants(matching: .any)["golf-aim-joystick"].exists)
        app.buttons["golf-pause"].tap()
        XCTAssertTrue(app.buttons["golf-resume"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.buttons["controller-exit"].exists)
        XCTAssertTrue(app.switches["Sound"].exists)
        XCTAssertTrue(app.switches["Haptics"].exists)
        XCTAssertFalse(app.staticTexts["golf-calibration-status"].exists)
        app.buttons["golf-resume"].tap()
        XCTAssertTrue(app.buttons["golf-club-next"].isEnabled)
    }
}
