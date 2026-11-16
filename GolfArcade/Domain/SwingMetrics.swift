import Foundation

enum Handedness: String, CaseIterable, Identifiable, Codable, Sendable {
    case right, left
    var id: Self { self }
    var displayName: String { rawValue.capitalized }
}
