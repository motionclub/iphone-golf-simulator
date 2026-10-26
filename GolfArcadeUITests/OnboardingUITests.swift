import XCTest

/// Onboarding runs on the TV; on a phone with no screen connected it asks for one (the simulator has none).
final class OnboardingUITests: XCTestCase {
    @MainActor func testFirstLaunchWithoutATVAsksForTheScreen() {
        let app = XCUIApplication(); app.launchArguments = ["-resetOnboarding", "-forceOnboarding"]
        app.launch()
        XCTAssertTrue(app.otherElements["onboarding-connect"].waitForExistence(timeout: 10) || app.staticTexts["Waiting for a screen…"].waitForExistence(timeout: 5))
    }
    @MainActor func testEveryStepWaitsForTheTVWithoutLosingItsPlace() {
        for step in ["hello", "player", "choose", "reward:golf"] {
            let app = XCUIApplication(); app.launchArguments = ["-onboardingStep", step]
            app.launch()
            XCTAssertTrue(app.staticTexts["Waiting for a screen…"].waitForExistence(timeout: 10), step)
            app.terminate()
        }
    }
    @MainActor func testSkipOnboardingOpensTheClub() {
        let app = XCUIApplication(); app.launchArguments = ["-skipOnboarding"]
        app.launch()
        XCTAssertFalse(app.staticTexts["Waiting for a screen…"].waitForExistence(timeout: 5))
    }
}
