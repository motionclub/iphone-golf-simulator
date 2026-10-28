import XCTest

/// Handheld play (golf and bowling with no TV, PLAN_PhonePlay_Handheld.md) over a stand-in game frame (`-handheldCheck`; the
/// simulator has no Unity). TEST_RUNNER_HANDHELD_ASSETS names a folder with golf_game.jpg, golf_map.png and bowl_setup.jpg;
/// TEST_RUNNER_HANDHELD_PROOF, when set, is where the screenshots are written.
final class HandheldPlayTests: XCTestCase {
    private var assets: String { ProcessInfo.processInfo.environment["HANDHELD_ASSETS"] ?? "" }
    private func save(_ app: XCUIApplication, _ name: String) {
        let shot = app.screenshot()
        let attachment = XCTAttachment(screenshot: shot); attachment.name = name; attachment.lifetime = .keepAlways; add(attachment)
        if let folder = ProcessInfo.processInfo.environment["HANDHELD_PROOF"] {
            try? shot.pngRepresentation.write(to: URL(fileURLWithPath: folder).appendingPathComponent("\(name).png"))
        }
    }
    private func launchGolf(_ extra: [String] = []) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["-clubCloudOff", "-handheldCheck", "golf", "\(assets)/golf_game.jpg", "-handheldMap", "\(assets)/golf_map.png"] + extra
        app.launch(); return app
    }

    @MainActor func testGolfDeckHasClubAimAndSwingUnderTheGame() {
        let app = launchGolf()
        let next = app.buttons["golf-club-next"], swing = app.buttons["golf-start-swing"], map = app.buttons["golf-handheld-map"]
        XCTAssertTrue(next.waitForExistence(timeout: 10))
        XCTAssertTrue(map.waitForExistence(timeout: 5))
        XCTAssertTrue(swing.exists && map.exists && app.descendants(matching: .any)["golf-aim-joystick"].firstMatch.exists)
        // the deck is the bottom quarter: club left, aim middle, swing right; the map sits in the game's part, above it
        let height = app.frame.height, width = app.frame.width
        for control in [next, swing, app.descendants(matching: .any)["golf-aim-joystick"].firstMatch] {
            XCTAssertGreaterThan(control.frame.midY, height * 0.75, "\(control) is on the deck")
        }
        XCTAssertLessThan(app.buttons["golf-club-previous"].frame.midX, width * 0.4)
        XCTAssertGreaterThan(swing.frame.midX, width * 0.7)
        XCTAssertEqual(app.descendants(matching: .any)["golf-aim-joystick"].firstMatch.frame.midX, width / 2, accuracy: width * 0.05)
        XCTAssertLessThan(map.frame.maxY, height * 0.75)
        save(app, "golf_aim")
        // tap the map: it fills the screen; back to the shot closes it
        map.tap()
        XCTAssertTrue(app.descendants(matching: .any)["golf-handheld-map-open"].waitForExistence(timeout: 3))
        save(app, "golf_map_open")
        app.buttons["golf-handheld-map-close"].tap()
        XCTAssertTrue(map.waitForExistence(timeout: 3))
        XCTAssertFalse(app.descendants(matching: .any)["golf-handheld-map-open"].exists)
    }

    @MainActor func testGolfPauseCanResumeWithNoTv() {
        let app = launchGolf()
        XCTAssertTrue(app.buttons["golf-pause"].waitForExistence(timeout: 10))
        app.buttons["golf-pause"].tap()
        XCTAssertTrue(app.buttons["golf-resume"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.buttons["golf-resume"].isEnabled, "no TV is needed to resume handheld golf")
        XCTAssertFalse(app.staticTexts["Reconnect your TV to continue."].exists)
    }

    @MainActor func testBowlingDeckHasTheBallUnderTheLane() {
        let app = XCUIApplication()
        app.launchArguments = ["-clubCloudOff", "-handheldCheck", "bowling", "\(assets)/bowl_setup.jpg"]
        app.launch()
        let pause = app.buttons["bowling-pause"]
        XCTAssertTrue(pause.waitForExistence(timeout: 10))
        let ball = app.descendants(matching: .any).matching(NSPredicate(format: "label BEGINSWITH %@", "Bowling ball")).firstMatch
        XCTAssertTrue(ball.exists)
        XCTAssertGreaterThan(ball.frame.midY, app.frame.height * 0.75, "the ball is on the deck")
        XCTAssertEqual(ball.frame.midX, app.frame.width / 2, accuracy: app.frame.width * 0.05)
        XCTAssertFalse(app.buttons["controller-exit"].exists, "no bar over the lane")
        save(app, "bowling")
    }
}
