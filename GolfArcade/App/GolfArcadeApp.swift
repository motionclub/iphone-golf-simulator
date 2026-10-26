import SwiftUI

@main
struct GolfArcadeApp: App {
    @UIApplicationDelegateAdaptor(SportsAppDelegate.self) private var appDelegate
    init() { MultiplayerService.shared.prepare(); ClubSound.preload() }
    var body: some Scene {
        WindowGroup {
            SportsHome()
        }
    }
}
