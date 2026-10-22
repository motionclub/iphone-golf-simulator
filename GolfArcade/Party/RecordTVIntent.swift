import AppIntents
import Foundation

/// One tap from Control Center, the Action button, the Lock Screen, Siri or Shortcuts: start or stop recording the TV.
/// The same file is compiled into the controls extension (MOTION_CLUB_CONTROLS) so the control can name the intent, but it always
/// runs here in the app (openAppWhenRun): only the app has the TV recorder. Apple's own screen recording can only capture the
/// phone, so this is the way to record what is on the TV.
struct RecordTVIntent: AppIntent {
    static let title: LocalizedStringResource = "Record the TV"
    static let description = IntentDescription("Starts recording the Motion Club TV picture with game sound and party voice, or stops and saves it to Photos.")
    static let openAppWhenRun = true

    init() {}

    #if MOTION_CLUB_CONTROLS
    func perform() async throws -> some IntentResult { .result() }
    #else
    @MainActor
    func perform() async throws -> some IntentResult & ProvidesDialog {
        let recording = RecordingService.shared
        if recording.state == .recording || recording.state == .starting {
            recording.stop(from: "the Record TV control")
            return .result(dialog: "Saving the TV recording.")
        }
        await recording.start(from: "the Record TV control")
        switch recording.state {
        case .recording, .starting: return .result(dialog: "Recording the TV. Tap again to stop.")
        default: return .result(dialog: IntentDialog(stringLiteral: recording.message.isEmpty ? "The TV recording could not start." : recording.message))
        }
    }
    #endif
}

#if !MOTION_CLUB_CONTROLS
/// Puts "Record the TV" in Shortcuts and Siri and on the Action button list without any setup.
struct MotionClubShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(intent: RecordTVIntent(),
                    phrases: ["Record the TV in \(.applicationName)", "Start recording in \(.applicationName)", "Stop recording in \(.applicationName)"],
                    shortTitle: "Record the TV", systemImageName: "record.circle")
    }
}
#endif
