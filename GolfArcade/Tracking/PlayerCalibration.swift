import CoreGraphics
import Foundation

struct PlayerCalibration: Codable, Equatable, Sendable {
    static let currentVersion = 2

    let version: Int
    let capturedAt: Date
    let signature: BodySignature
    let anchor: BodyAnchor

    init(signature: BodySignature, anchor: BodyAnchor, capturedAt: Date = Date()) {
        version = Self.currentVersion
        self.capturedAt = capturedAt
        self.signature = signature
        self.anchor = anchor
    }

    #if DEBUG
    static let uiTestingFixture = PlayerCalibration(
        signature: BodySignature(
            shoulderWidth: 0.22, hipWidth: 0.16, torsoLength: 0.30,
            upperArmLength: 0.20, forearmLength: 0.18, thighLength: 0.28, shinLength: 0.27
        ),
        anchor: BodyAnchor(shoulderCenterX: 0.5, shoulderCenterY: 0.72, height: 0.72)
    )
    #endif

}

struct BodySignature: Codable, Equatable, Sendable {
    let shoulderWidth: Double
    let hipWidth: Double
    let torsoLength: Double
    let upperArmLength: Double
    let forearmLength: Double
    let thighLength: Double
    let shinLength: Double

    init(
        shoulderWidth: Double, hipWidth: Double, torsoLength: Double,
        upperArmLength: Double, forearmLength: Double, thighLength: Double, shinLength: Double
    ) {
        self.shoulderWidth = shoulderWidth
        self.hipWidth = hipWidth
        self.torsoLength = torsoLength
        self.upperArmLength = upperArmLength
        self.forearmLength = forearmLength
        self.thighLength = thighLength
        self.shinLength = shinLength
    }

}

struct BodyAnchor: Codable, Equatable, Sendable {
    let shoulderCenterX: Double
    let shoulderCenterY: Double
    let height: Double

    init(shoulderCenterX: Double, shoulderCenterY: Double, height: Double) {
        self.shoulderCenterX = shoulderCenterX
        self.shoulderCenterY = shoulderCenterY
        self.height = height
    }

}


enum PlayerCalibrationStore {
    private static let key = "playerBodyCalibration.v2"

    static func load(defaults: UserDefaults = .standard) -> PlayerCalibration? {
        guard let data = defaults.data(forKey: key),
              let calibration = try? JSONDecoder().decode(PlayerCalibration.self, from: data),
              calibration.version == PlayerCalibration.currentVersion else { return nil }
        return calibration
    }

    static func save(_ calibration: PlayerCalibration, defaults: UserDefaults = .standard) {
        guard let data = try? JSONEncoder().encode(calibration) else { return }
        defaults.set(data, forKey: key)
    }

    static func clear(defaults: UserDefaults = .standard) {
        defaults.removeObject(forKey: key)
    }
}

