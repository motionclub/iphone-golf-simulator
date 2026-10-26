import SwiftUI

/// Which party sheets are open (so the menus, the dock and the pause screen all open the same ones from one place).
@MainActor @Observable final class PartyUI {
    static let shared = PartyUI()
    var settingsOpen = false
}

/// Voice, chat and safety settings. One screen, opened from the gear on every controller and menu, and the same sections
/// are embedded in the main Settings screen. Plain `Form` sections so they drop into any list.
struct PartySettingsView: View {
    var dismiss: () -> Void = {}
    var body: some View {
        NavigationStack {
            Form { PartySettingsSections() }
                .navigationTitle("Voice & chat").navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done", action: dismiss).accessibilityIdentifier("party-settings-done") } }
        }
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("party-settings")
    }
}

struct PartySettingsSections: View {
    @Bindable var voice = PartyVoiceCoordinator.shared
    @Bindable var chat = PartyChat.shared
    var safety = PartySafety.shared
    @State private var showSetup = false

    var body: some View {
        GameAudioSettingsSection()
        voiceSection
        chatSection
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

/// The small row of buttons over every phone screen while there is a party: mic, chat, gear. Collapsed to the mic while a motion-
/// controlled swing is on, so a swing can never open a sheet.
struct CaptureDock: View {
    var voice = PartyVoiceCoordinator.shared
    var chat = PartyChat.shared
    var session = SportsSession.shared
    @State private var showSettings = false

    private var inParty: Bool { chat.channel.inParty }
    /// A phone swing or a golf aim is live: keep the dock tiny and out of the way.
    private var compact: Bool { Self.isCompact(session) }
    /// Golf has no free corner, so its dock is always the small one, up in the status-bar strip beside the Dynamic Island.
    private var golf: Bool { session.active && session.sport == "golf" }
    static func isCompact(_ session: SportsSession) -> Bool {
        if session.active && session.sport == "golf" { return true }
        return session.active && !session.paused && session.finishedMatch == nil && session.setupStage == .playing
    }
    var visible: Bool { inParty || voice.isLive }

    /// Room a controller's own top bar leaves free at the trailing edge so the dock never covers it (0 when there is no dock).
    @MainActor static func reservedWidth(session: SportsSession = .shared, chat: PartyChat = .shared, voice: PartyVoiceCoordinator = .shared) -> CGFloat {
        let inParty = chat.channel.inParty
        guard inParty || voice.isLive else { return 0 }
        var buttons = 1
        if !isCompact(session) { buttons += (inParty ? 1 : 0) + 1 }
        return CGFloat(buttons) * 44 + 24
    }

    var body: some View {
        if visible {
            HStack(spacing: compact ? 6 : 8) {
                VoiceMicButton(voice: voice, onNeedsSetup: { showSettings = true })
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
            .accessibilityElement(children: .contain).accessibilityIdentifier("capture-dock")
        }
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
        }.buttonStyle(.plain).accessibilityLabel("Voice and chat settings").accessibilityIdentifier("capture-settings")
    }
}
