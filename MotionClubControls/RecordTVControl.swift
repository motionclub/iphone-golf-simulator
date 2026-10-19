import AppIntents
import SwiftUI
import WidgetKit

/// Motion Club's controls for Control Center, the Lock Screen and the Action button (iOS 18+).
@main
struct MotionClubControls: WidgetBundle {
    var body: some Widget { RecordTVControl() }
}

/// "Record the TV": one tap starts recording the game on the TV (never this phone); the next tap stops and saves it.
struct RecordTVControl: ControlWidget {
    static let kind = "com.motionclub.controls.record-tv"
    var body: some ControlWidgetConfiguration {
        StaticControlConfiguration(kind: Self.kind) {
            ControlWidgetButton(action: RecordTVIntent()) {
                Label("Record TV", systemImage: "record.circle")
            }
        }
        .displayName("Record the TV")
        .description("Start or stop recording the Motion Club TV picture.")
    }
}
