import SwiftUI

/// Which party sheets are open (so the menus, the dock and the pause screen all open the same ones from one place).
@MainActor @Observable final class PartyUI {
    static let shared = PartyUI()
    var settingsOpen = false
}

/// Voice, chat, recording and safety settings. One screen, opened from the gear on every controller and menu, and the same sections
/// are embedded in the main Settings screen. Plain `Form` sections so they drop into any list.
struct PartySettingsView: View {
    var dismiss: () -> Void = {}
    var body: some View {
        NavigationStack {
            Form { PartySettingsSections() }
                .navigationTitle("Voice & recording").navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done", action: dismiss).accessibilityIdentifier("party-settings-done") } }
        }
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("party-settings")
    }
}

struct PartySettingsSections: View {
    @Bindable var voice = PartyVoiceCoordinator.shared
    @Bindable var recording = RecordingService.shared
    @Bindable var chat = PartyChat.shared
    var safety = PartySafety.shared
    @State private var showSetup = false
    @State private var showLibrary = false

    var body: some View {
        GameAudioSettingsSection()
        voiceSection
        chatSection
        recordingSection
        safetySection
    }

    // MARK: voice

    private var voiceSection: some View {
        Section {
            Picker("Microphone", selection: Binding(get: { voice.prefs.mode }, set: { voice.setMode($0) })) {
                Text("Off").tag(VoiceMode.off); Text("Push to talk").tag(VoiceMode.pushToTalk); Text("Open mic").tag(VoiceMode.openMic)
            }.pickerStyle(.segmented).accessibilityIdentifier("voice-mode")
            if !safety.access.canTalk, let why = safety.access.reason {
                Label(why, systemImage: "lock.fill").font(.footnote).foregroundStyle(.secondary)
                if case .quickOnly = safety.access, safety.restrictions == GameCenterRestrictions(), safety.ageBand != .under13 {
                    Button("Set up typing and voice") { showSetup = true }.accessibilityIdentifier("voice-setup")
                }
            }
            if voice.isLive {
                HStack { Text("Mic level"); Spacer(); MicLevelMeter(level: voice.micLevel, live: voice.isTransmitting) }
                HStack { Image(systemName: "mic.fill").font(.caption); Slider(value: gain, in: 0.5...2); Text("Mic volume").font(.caption).foregroundStyle(.secondary) }
                HStack { Image(systemName: "speaker.wave.2.fill").font(.caption); Slider(value: output, in: 0...1); Text("Party volume").font(.caption).foregroundStyle(.secondary) }
                Toggle("Cancel echo and noise", isOn: Binding(get: { voice.prefs.noiseSuppression }, set: { voice.setNoiseSuppression($0) })).accessibilityIdentifier("voice-noise")
                if !voice.routeName.isEmpty { LabeledContent("Heard through", value: voice.routeName).font(.footnote) }
            }
        } header: { Text("Voice chat") } footer: {
            Text("Voice goes only to the people in your party. It is off until you turn it on, and the red mic shows whenever it is live. Headphones keep the TV's sound out of your mic.")
        }
        .sheet(isPresented: $showSetup) { PartySetupView(dismiss: { showSetup = false }).presentationDetents([.large]) }
    }
    private var gain: Binding<Double> { Binding(get: { Double(voice.prefs.inputGain) }, set: { voice.setInputGain(Float($0)) }) }
    private var output: Binding<Double> { Binding(get: { Double(voice.prefs.outputVolume) }, set: { voice.setOutputVolume(Float($0)) }) }

    // MARK: chat

    private var chatSection: some View {
        Section {
            Toggle("Show typed chat from my party", isOn: $chat.incomingTextVisible).accessibilityIdentifier("chat-show-text")
            Toggle("Hide bad language", isOn: Binding(get: { safety.filterOn }, set: { safety.filterProfanity = $0 })).disabled(safety.filterLocked).accessibilityIdentifier("chat-filter")
            Toggle("Vibrate on new message", isOn: $chat.soundOnMessage)
        } header: { Text("Party chat") } footer: {
            Text(safety.filterLocked ? "Bad language is always hidden for teens. Links and contact details are hidden for everyone." : "Links and contact details are always hidden. Report, Mute and Block are on every message.")
        }
    }

    // MARK: recording

    private var recordingSection: some View {
        Section {
            Picker("Quality", selection: $recording.settings.quality) {
                ForEach(CaptureSettings.Quality.allCases) { q in Text(q.title).tag(q) }
            }.accessibilityIdentifier("record-quality")
            Text(recording.settings.quality.detail).font(.footnote).foregroundStyle(.secondary)
            Toggle("Game sound", isOn: $recording.settings.gameAudio).accessibilityIdentifier("record-game-audio")
            Toggle("Party voices", isOn: $recording.settings.partyVoice).accessibilityIdentifier("record-party-voice")
            Toggle("My microphone", isOn: $recording.settings.myMic).accessibilityIdentifier("record-my-mic")
            Toggle("Save to Photos when I stop", isOn: $recording.settings.saveToPhotos).accessibilityIdentifier("record-save-photos")
            Button { showLibrary = true } label: { Label("Recordings", systemImage: "film.stack") }.accessibilityIdentifier("record-library")
        } header: { Text("Recording") } footer: {
            Text("Records what is on the TV, never this phone's screen. Your party sees a red \"recording\" notice while you record, and you must have everyone's okay to share a video with their voice in it.")
        }
        .sheet(isPresented: $showLibrary) { RecordingLibraryView(dismiss: { showLibrary = false }) }
    }

    // MARK: safety

    private var safetySection: some View {
        Section {
            LabeledContent("Typing and voice", value: safety.access.canType ? "On" : "Quick phrases only")
            Button(safety.ageBand == .unknown ? "Set up typing and voice" : "Chat rules and age") { showSetup = true }.accessibilityIdentifier("safety-setup")
            if !safety.blocked.isEmpty {
                ForEach(Array(safety.blocked).sorted(), id: \.self) { id in
                    HStack { Text(chat.name(of: id)); Spacer(); Button("Unblock") { safety.unblock(id); chat.unmute(id) }.font(.subheadline.bold()) }
                }
            }
            if let url = PartyContact.privacyURL { Link("Privacy policy", destination: url) }
            if let url = PartyContact.supportURL { Link("Support", destination: url) }
            else if !PartyContact.email.isEmpty { Link("Contact: \(PartyContact.email)", destination: URL(string: "mailto:\(PartyContact.email)")!) }
            else { Button("Contact support by text") { if let u = URL(string: "sms:\(PartyContact.smsNumber)") { UIApplication.shared.open(u) } } }
        } header: { Text("Safety") } footer: {
            Text("Parents can limit multiplayer and chat for a child's Game Center account in Screen Time. Motion Club follows those limits.")
        }
        .sheet(isPresented: $showSetup) { PartySetupView(dismiss: { showSetup = false }).presentationDetents([.large]) }
    }
}

/// Recordings: where every recording went (Photos, kept here, or not saved and why), the ones kept in the app with share and delete, and
/// the recorder log. Opened from the gear's "Recordings", a long press on the record button, or a tap on the "saved" note under it.
struct RecordingLibraryView: View {
    var recording = RecordingService.shared
    var dismiss: () -> Void = {}
    @State private var files: [URL] = []
    var body: some View {
        NavigationStack {
            List {
                Section {
                    if recording.history.isEmpty { Text("No recordings yet. Tap the red Record TV button while the game is on the TV.").foregroundStyle(.secondary) }
                    ForEach(recording.history) { entry in
                        VStack(alignment: .leading, spacing: 3) {
                            HStack {
                                Image(systemName: Self.icon(entry.place)).foregroundStyle(entry.place == .notSaved ? .red : .accentColor)
                                Text(Self.place(entry.place)).font(.subheadline.weight(.semibold))
                                Spacer()
                                Text(entry.date.formatted(date: .abbreviated, time: .shortened)).font(.caption).foregroundStyle(.secondary)
                            }
                            Text((entry.seconds > 0 ? String(format: "%d:%02d · ", Int(entry.seconds) / 60, Int(entry.seconds) % 60) : "") + entry.note)
                                .font(.footnote).foregroundStyle(.secondary)
                        }
                        .accessibilityElement(children: .combine)
                    }
                    if recording.history.contains(where: { $0.place == .photos }) {
                        Button { if let url = URL(string: "photos-redirect://") { UIApplication.shared.open(url) } } label: { Label("Open Photos", systemImage: "photo.on.rectangle") }
                            .accessibilityIdentifier("recordings-open-photos")
                    }
                } header: { Text("Recent") } footer: { Text("Recordings go to your Photos (Recents). Any that Photos could not take are kept below.") }
                Section("Kept in Motion Club") {
                    if files.isEmpty { Text("None").foregroundStyle(.secondary) }
                    ForEach(files, id: \.self) { url in
                        HStack {
                            Image(systemName: "film"); Text(url.deletingPathExtension().lastPathComponent).font(.footnote).lineLimit(1)
                            Spacer(); ShareLink(item: url) { Image(systemName: "square.and.arrow.up") }
                        }
                        .swipeActions { Button("Delete", role: .destructive) { recording.deleteKept(url); files = RecordingService.library() } }
                    }
                }
                if FileManager.default.fileExists(atPath: RecordingService.logURL.path) {
                    Section { ShareLink(item: RecordingService.logURL) { Label("Share the recorder log", systemImage: "doc.text") }.accessibilityIdentifier("recordings-log") }
                        footer: { Text("What the recorder did and why each recording stopped. Send it to us if a recording went wrong.") }
                }
            }
            .navigationTitle("Recordings").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done", action: dismiss) } }
            .onAppear { files = RecordingService.library() }
        }
    }
    static func place(_ p: RecordingEntry.Place) -> String { switch p { case .photos: "In your Photos"; case .kept: "Kept in Motion Club"; case .notSaved: "Not saved" } }
    static func icon(_ p: RecordingEntry.Place) -> String { switch p { case .photos: "photo.on.rectangle"; case .kept: "film"; case .notSaved: "exclamationmark.triangle" } }
}

/// The small row of buttons over every phone screen: record, mic, chat, gear. Collapsed to a record dot and the mic while a motion-
/// controlled swing is on, so a swing can never open a sheet; a red pill with the time while recording. Only the party buttons show
/// when there is a party, and recording shows when a TV is connected.
struct CaptureDock: View {
    var recording = RecordingService.shared
    var voice = PartyVoiceCoordinator.shared
    var chat = PartyChat.shared
    var session = SportsSession.shared
    @State private var showSettings = false
    @State private var showRecordings = false

    private var tvOn: Bool { session.displayConnected }
    private var inParty: Bool { chat.channel.inParty }
    /// A phone swing or a golf aim is live: keep the dock tiny and out of the way.
    private var compact: Bool { Self.isCompact(session) }
    /// Golf has no free corner, so its dock is always the small one, up in the status-bar strip beside the Dynamic Island.
    private var golf: Bool { session.active && session.sport == "golf" }
    static func isCompact(_ session: SportsSession) -> Bool {
        if session.active && session.sport == "golf" { return true }
        return session.active && !session.paused && session.finishedMatch == nil && session.setupStage == .playing
    }
    var visible: Bool { tvOn || inParty || recording.isRecording || recording.showsOutcome }

    /// Room a controller's own top bar leaves free at the trailing edge so the dock never covers it (0 when there is no dock).
    @MainActor static func reservedWidth(session: SportsSession = .shared, chat: PartyChat = .shared, recording: RecordingService = .shared, voice: PartyVoiceCoordinator = .shared) -> CGFloat {
        let inParty = chat.channel.inParty
        guard session.displayConnected || inParty || recording.isRecording else { return 0 }
        let compact = isCompact(session)
        let record = session.displayConnected || recording.isRecording
        var buttons = record ? 1 : 0
        if inParty || voice.isLive { buttons += 1 }
        if !compact { buttons += (inParty ? 1 : 0) + 1 }
        // the record button is the big one: a 44 pt dot, plus its "Record TV" / time label when there is room
        return CGFloat(buttons) * 44 + 24 + (record ? 8 + (compact ? 0 : recordLabelWidth) : 0)
    }
    static let recordLabelWidth: CGFloat = 78
    /// The words beside the record dot: what a tap does, or how long it has been recording.
    static func recordLabel(_ recording: RecordingService) -> String {
        switch recording.state {
        case .recording: recording.timeText
        case .starting: "Starting"
        case .saving: "Saving"
        default: "Record TV"
        }
    }

    var body: some View {
        if visible {
            HStack(spacing: compact ? 6 : 8) {
                if tvOn || recording.isRecording || recording.showsOutcome { recordButton }
                if inParty || voice.isLive { VoiceMicButton(voice: voice, onNeedsSetup: { showSettings = true }) }
                if !compact {
                    if inParty { chatButton }
                    gear
                }
            }
            .padding(compact ? 4 : 6)
            .background(.black.opacity(0.35), in: Capsule())
            .overlay(Capsule().strokeBorder(.white.opacity(0.18), lineWidth: 1))
            .frame(maxWidth: .infinity, alignment: .trailing).padding(.trailing, 10)
            .padding(.top, golf ? -52 : 0)
            .sheet(isPresented: $showSettings) { PartySettingsView(dismiss: { showSettings = false }).presentationDetents([.large]) }
            .sheet(isPresented: $showRecordings) { RecordingLibraryView(dismiss: { showRecordings = false }).presentationDetents([.large]) }
            .accessibilityElement(children: .contain).accessibilityIdentifier("capture-dock")
        }
    }

    private var recordButton: some View {
        Button { recording.toggle() } label: {
            HStack(spacing: 6) {
                // golf's dock sits in the status-bar strip beside the battery: it keeps the small dot there
                let dot: CGFloat = golf ? 36 : 44
                ZStack {
                    Circle().fill(recording.isRecording ? Color.red : Color.white.opacity(0.18)).frame(width: dot, height: dot)
                    Circle().strokeBorder(.white.opacity(recording.isRecording ? 0.9 : 0.55), lineWidth: 2).frame(width: dot, height: dot)
                    if recording.state == .recording || recording.state == .starting { RoundedRectangle(cornerRadius: 3).fill(.white).frame(width: 15, height: 15) }
                    else if recording.state == .saving { ProgressView().tint(.white).scaleEffect(0.8) }
                    else { Circle().fill(Color.red).frame(width: golf ? 16 : 20, height: golf ? 16 : 20) }
                }
                if !compact {
                    Text(Self.recordLabel(recording))
                        .font(.system(size: 14, weight: .heavy, design: recording.state == .recording ? .monospaced : .rounded))
                        .foregroundStyle(.white).lineLimit(1).minimumScaleFactor(0.8)
                        .frame(width: Self.recordLabelWidth, alignment: .leading)
                }
            }
            .padding(.trailing, compact ? 0 : 4)
            .contentShape(Capsule())
        }
        .buttonStyle(.plain).disabled(!recording.canToggle && !recording.isRecording)
        // hold for Recordings: where every recording went (a disabled button still takes the long press through this gesture)
        .simultaneousGesture(LongPressGesture(minimumDuration: 0.6).onEnded { _ in if !compact { showRecordings = true } })
        .opacity(recording.canToggle || recording.isRecording ? 1 : 0.45)
        .accessibilityLabel(recording.state == .recording ? "Stop recording" : "Record the TV").accessibilityValue(recording.state == .recording ? recording.timeText : "")
        .accessibilityIdentifier("capture-record")
        .overlay(alignment: .bottom) { RecordingToast(open: { showRecordings = true }) .offset(y: 56) }
    }

    private var chatButton: some View {
        // the inline strip (PartyChatStrip, over the game), not a sheet: chatting never leaves the controller or the Plaza
        Button { chat.stripOpen.toggle() } label: {
            Image(systemName: "bubble.left.and.bubble.right.fill").font(.system(size: 15, weight: .bold)).foregroundStyle(.white)
                .frame(width: 36, height: 36).background(.white.opacity(0.14), in: Circle())
                .overlay(alignment: .topTrailing) {
                    if chat.unread > 0 { Text("\(min(chat.unread, 9))").font(.system(size: 10, weight: .bold)).foregroundStyle(IslandUI.navy).frame(minWidth: 16, minHeight: 16).background(IslandUI.lime, in: Circle()).offset(x: 3, y: -3) }
                }
        }.buttonStyle(.plain).accessibilityLabel("Party chat").accessibilityIdentifier("capture-chat")
    }

    private var gear: some View {
        Button { showSettings = true } label: {
            Image(systemName: "gearshape.fill").font(.system(size: 15, weight: .bold)).foregroundStyle(.white).frame(width: 36, height: 36).background(.white.opacity(0.14), in: Circle())
        }.buttonStyle(.plain).accessibilityLabel("Voice and recording settings").accessibilityIdentifier("capture-settings")
    }
}

/// A short line under the record button: why it cannot record, what is happening, or that it is saved.
private struct RecordingToast: View {
    var recording = RecordingService.shared
    var open: () -> Void = {}
    @State private var shown = ""
    var body: some View {
        Group {
            if !shown.isEmpty {
                Text(shown).font(.system(size: 12, weight: .bold)).foregroundStyle(IslandUI.navy).multilineTextAlignment(.leading)
                    .padding(.horizontal, 12).padding(.vertical, 8).frame(width: 230, alignment: .leading)
                    .background(IslandUI.lime, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .transition(.opacity)
                    .onTapGesture { let wasDone = recording.state == .saved || recording.state == .failed; shown = ""; if wasDone { open() } }
                    .accessibilityIdentifier("capture-toast").accessibilityHint("Opens Recordings")
            }
        }
        .onChange(of: recording.state) { _, state in
            switch state { case .saved, .failed: show(recording.message + " Tap to see Recordings."); case .recording: show("Recording the TV. Tap again to stop. Hold for Recordings."); default: break }
        }
        .animation(.easeInOut(duration: 0.2), value: shown)
    }
    private func show(_ text: String) {
        shown = text
        // a saved/failed note stays long enough to read and tap (it used to vanish after 4 s)
        let hold: Duration = recording.state == .saved || recording.state == .failed ? .seconds(9) : .seconds(4)
        Task { try? await Task.sleep(for: hold); if shown == text { shown = "" } }
    }
}
