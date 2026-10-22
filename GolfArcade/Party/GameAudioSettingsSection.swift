import SwiftUI

/// Game sound volumes: music, effects and announcer. Stored in UserDefaults under the keys the Unity game reads
/// through PlayerPrefs (audio.music / audio.sfx / audio.voice, 0...1), so a change is heard on the TV within a second.
struct GameAudioSettingsSection: View {
    @AppStorage("audio.music") private var music = 1.0
    @AppStorage("audio.sfx") private var sfx = 1.0
    @AppStorage("audio.voice") private var voice = 1.0

    var body: some View {
        Section {
            row("music.note", "Music", $music).accessibilityIdentifier("audio-music")
            row("sportscourt.fill", "Effects", $sfx).accessibilityIdentifier("audio-sfx")
            row("mic.fill", "Announcer", $voice).accessibilityIdentifier("audio-voice")
            Button("Reset to default") { music = 1; sfx = 1; voice = 1 }.accessibilityIdentifier("audio-reset")
        } header: { Text("Game sound") } footer: {
            Text("Music plays in the plaza and during map intros. Effects are hits, bounces and the crowd. The announcer's lines come down when you turn him down; music also dips while he speaks.")
        }
    }

    private func row(_ icon: String, _ title: String, _ value: Binding<Double>) -> some View {
        HStack { Image(systemName: icon).font(.caption).frame(width: 18); Slider(value: value, in: 0...1); Text(title).font(.caption).foregroundStyle(.secondary).frame(width: 74, alignment: .leading) }
    }
}
