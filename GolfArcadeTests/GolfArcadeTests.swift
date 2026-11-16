import XCTest
@testable import GolfArcade

/// The saved roster and the body scan a saved player may still carry. (The rest of this file tested the old camera golf game:
/// its shot engine, flight path and body-scan accumulator. That code left the app on 2026-11-15, and those tests with it.)
final class PlayerStoreTests: XCTestCase {
    func testCalibrationStoreRoundTripsAndClears() throws {
        let suiteName = "PlayerCalibrationTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }
        let calibration = makeCalibration()

        PlayerCalibrationStore.save(calibration, defaults: defaults)
        XCTAssertEqual(PlayerCalibrationStore.load(defaults: defaults), calibration)

        PlayerCalibrationStore.clear(defaults: defaults)
        XCTAssertNil(PlayerCalibrationStore.load(defaults: defaults))
    }

    func testRosterMigratesTheSinglePlayerScan() throws {
        let suiteName = "PlayerRosterTests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }
        let calibration = makeCalibration()
        PlayerCalibrationStore.save(calibration, defaults: defaults)
        defaults.set("left", forKey: "range.handedness")

        let migrated = PlayerRosterStore.load(defaults: defaults)
        XCTAssertEqual(migrated.count, 1)
        XCTAssertEqual(migrated[0].calibration, calibration)
        XCTAssertEqual(migrated[0].handedness, .left)

        var players = migrated
        players.append(Player(name: "Sam", colorIndex: 1))
        PlayerRosterStore.save(players, defaults: defaults)
        XCTAssertEqual(PlayerRosterStore.load(defaults: defaults), players)
    }

    /// A scan as the old game saved one (a whole number of seconds, so the date survives the JSON round trip exactly).
    private func makeCalibration() -> PlayerCalibration {
        PlayerCalibration(
            signature: BodySignature(shoulderWidth: 0.2, hipWidth: 0.12, torsoLength: 0.26,
                                     upperArmLength: 0.125, forearmLength: 0.125, thighLength: 0.19, shinLength: 0.18),
            anchor: BodyAnchor(shoulderCenterX: 0.5, shoulderCenterY: 0.72, height: 0.77),
            capturedAt: Date(timeIntervalSinceReferenceDate: 780_000_000))
    }
}
