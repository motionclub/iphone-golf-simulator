import Foundation
@MainActor final class SportsSession { static let shared = SportsSession(); var multiplayerMatchID: String?; func startMultiplayer(_ c: MultiplayerMatchConfiguration) {}; func end() {} }
@MainActor final class SportsRuntime { static func shared() -> SportsRuntime { SportsRuntime() }; func pushNetwork(_ s: String) -> Bool { true }; func pollNetwork() -> String? { nil } }
