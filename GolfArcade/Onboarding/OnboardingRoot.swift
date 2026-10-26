import SwiftUI

/// The phone during onboarding: with no screen yet, how to put the game on the TV; with one, the remote for the TV's
/// onboarding (arrows, A, B) and, on the player step, the one thing typed: the name.
struct OnboardingRoot: View {
    let flow: OnboardingFlow
    @State private var session = SportsSession.shared
    var body: some View {
        Group {
            if session.displayConnected { OnboardingRemote(flow: flow) } else { OnboardingConnectScreen() }
        }
        .preferredColorScheme(.dark)
    }
}

/// First open, no TV yet: Screen Mirroring in three steps. The TV's welcome starts by itself once a screen connects.
struct OnboardingConnectScreen: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            OnbWordmark(size: 30)
            VStack(alignment: .leading, spacing: 0) {
                Text("Let's get you").foregroundStyle(.white)
                Text("on the TV").foregroundStyle(Onb.goldHi)
            }.font(Onb.font(38, 900)).italic()
            VStack(alignment: .leading, spacing: 14) {
                step(1, "Swipe down from the top right corner")
                step(2, "Tap Screen Mirroring")
                step(3, "Pick your Apple TV, AirPlay TV or Mac")
            }
            .padding(18).frame(maxWidth: .infinity, alignment: .leading).onbPanel(radius: 24)
            HStack(spacing: 10) {
                ProgressView().tint(Onb.goldHi)
                Text("Waiting for a screen…").font(Onb.font(18, 700))
            }
            .frame(maxWidth: .infinity, minHeight: 56).background(Onb.ink.opacity(0.7), in: Capsule())
            Text("The moment the TV connects, the welcome continues on the big screen and this phone becomes your controller.")
                .font(Onb.font(16, 600)).foregroundStyle(Onb.soft)
            Spacer(minLength: 0)
            Text("You need a TV or Mac to play: the phone is always the club, never the screen.")
                .font(Onb.font(15, 600)).foregroundStyle(Onb.soft)
                .padding(16).frame(maxWidth: .infinity, alignment: .leading)
                .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(Color(hex: "8FA8E8"), lineWidth: 2))
        }
        .foregroundStyle(.white).padding(26)
        .background(LinearGradient(colors: [Onb.navy, Onb.blue], startPoint: .top, endPoint: .bottom).ignoresSafeArea())
        .accessibilityIdentifier("onboarding-connect")
    }
    private func step(_ n: Int, _ text: String) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Text("\(n)").font(Onb.font(15, 900)).foregroundStyle(Onb.ink).frame(width: 30, height: 30).background(Onb.goldHi, in: Circle())
            Text(text).font(Onb.font(18, 700)).fixedSize(horizontal: false, vertical: true)
        }
    }
}

/// The remote for the TV's onboarding: what the TV shows, the arrows, A and B. The name field joins it on the player step.
struct OnboardingRemote: View {
    @Bindable var flow: OnboardingFlow
    @State private var name = ""
    @FocusState private var typing: Bool
    var body: some View {
        VStack(spacing: 18) {
            onTV
            if flow.step == .player { nameField }
            Spacer(minLength: 0)
            OnbDPad(flow: flow)
            Spacer(minLength: 0)
            HStack(alignment: .center, spacing: 30) {
                OnbRemoteButton(label: "B", caption: "Back", size: 78, filled: false) { flow.back() }
                    .accessibilityIdentifier("onboarding-back")
                OnbRemoteButton(label: "A", caption: "Select", size: 116, filled: true) { flow.select() }
                    .accessibilityIdentifier("onboarding-select")
            }
            Text("Eyes on the TV. When a lesson starts, hold this like a club or a racket.")
                .font(Onb.font(13, 600)).foregroundStyle(.white.opacity(0.55)).multilineTextAlignment(.center)
        }
        .foregroundStyle(.white).padding(24)
        .background(LinearGradient(colors: [Color(hex: "16294A"), IslandUI.dark], startPoint: .top, endPoint: .bottom).ignoresSafeArea())
        .onAppear { name = flow.player?.name == "Player 1" ? "" : flow.player?.name ?? "" }
        .onChange(of: flow.nameRequested) { _, asked in if asked { typing = true; flow.nameRequested = false } }
        .accessibilityIdentifier("onboarding-remote")
    }
    private var onTV: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("ON THE TV · \(stepName)").font(Onb.font(12, 800)).tracking(1.6).foregroundStyle(Onb.goldHi)
            Text(focusName).font(Onb.font(24, 900)).italic().lineLimit(2).minimumScaleFactor(0.6)
        }
        .frame(maxWidth: .infinity, alignment: .leading).padding(.horizontal, 18).padding(.vertical, 14)
        .background(.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).strokeBorder(.white.opacity(0.14), lineWidth: 1.5))
    }
    private var nameField: some View {
        HStack(spacing: 10) {
            TextField("Your name", text: $name)
                .font(Onb.font(22, 800)).focused($typing).submitLabel(.done)
                .textInputAutocapitalization(.words).autocorrectionDisabled()
                .padding(.horizontal, 16).frame(height: 56)
                .background(Onb.ink, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(typing ? Onb.goldHi : .white.opacity(0.4), lineWidth: 2.5))
                .onChange(of: name) { _, value in
                    if value.count > 14 { name = String(value.prefix(14)) }
                    flow.setName(name)
                }
                .onSubmit { typing = false; flow.focus("save") }
                .accessibilityIdentifier("onboarding-name")
            Menu {
                ForEach(OnboardingFlow.nameIdeas, id: \.self) { idea in Button(idea) { name = idea } }
            } label: {
                Image(systemName: "sparkles").font(.system(size: 20, weight: .bold)).frame(width: 56, height: 56)
                    .background(.white.opacity(0.1), in: RoundedRectangle(cornerRadius: 16, style: .continuous))
            }.accessibilityLabel("Name ideas")
        }
    }
    private var stepName: String {
        switch flow.step {
        case .hello: "WELCOME"; case .controller: "YOUR CONTROLLER"; case .room: "ROOM TO SWING"; case .player: "YOUR PLAYER"
        case .card: "YOUR CLUB CARD"; case .choose: "FIRST LESSON"; case .lesson(let s): "\(s.title) LESSON"
        case .reward(let s): "\(s.title) LESSON DONE"; case .done: ""
        }
    }
    private var focusName: String {
        switch flow.focused {
        case "go": "Let's go"; case "try": "Press A"; case "next": "Next"; case "ready": "I'm ready"
        case "male": "Body · Male"; case "female": "Body · Female"
        case "skin": "Skin tone · ◀ ▶ to change"; case "shirt": "Shirt colour · ◀ ▶ to change"
        case "name": "Name · type it here"; case "shuffle": "Shuffle"; case "save": "That's me!"
        case "play": flow.step == .card ? "Let's play" : "Play"; case "golf": "Golf lesson"; case "tennis": "Tennis lesson"
        case "skip": "Skip lessons"; case "resume": "Resume the lesson"; case "choose": "Pick a lesson"
        case "other": "The other lesson"; case "menu": "To the club"
        default: "…"
        }
    }
}

/// Four arrows in a plus. One click is one step; holding repeats.
struct OnbDPad: View {
    let flow: OnboardingFlow
    var body: some View {
        let cell: CGFloat = 92, gap: CGFloat = 8
        ZStack {
            arrow("arrowtriangle.up.fill", .up).offset(y: -(cell + gap))
            arrow("arrowtriangle.left.fill", .left).offset(x: -(cell + gap))
            arrow("arrowtriangle.right.fill", .right).offset(x: cell + gap)
            arrow("arrowtriangle.down.fill", .down).offset(y: cell + gap)
            Circle().strokeBorder(.white.opacity(0.14), style: StrokeStyle(lineWidth: 2, dash: [4, 5])).frame(width: 60, height: 60)
        }
        .frame(width: cell * 3 + gap * 2, height: cell * 3 + gap * 2)
    }
    private func arrow(_ icon: String, _ direction: MenuMove) -> some View {
        OnbRepeatPress(action: { flow.move(direction) }) { pressed in
            Image(systemName: icon).font(.system(size: 32, weight: .bold))
                .foregroundStyle(pressed ? Onb.goldHi : .white)
                .frame(width: 92, height: 92)
                .background(pressed ? Onb.goldHi.opacity(0.22) : .white.opacity(0.09), in: RoundedRectangle(cornerRadius: 26, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 26, style: .continuous).strokeBorder(pressed ? Onb.goldHi : .white.opacity(0.22), lineWidth: 2.5))
                .scaleEffect(pressed ? 0.95 : 1)
        }
        .accessibilityLabel("Move \(String(describing: direction))")
        .accessibilityAddTraits(.isButton)
        .accessibilityAction { flow.move(direction) }
    }
}

/// Acts on touch-down, then repeats while held (after a short pause).
struct OnbRepeatPress<Label: View>: View {
    let action: () -> Void
    @ViewBuilder let label: (Bool) -> Label
    @State private var pressed = false
    @State private var repeater: Task<Void, Never>?
    var body: some View {
        label(pressed)
            .contentShape(Rectangle())
            .gesture(DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    guard !pressed else { return }
                    pressed = true; action()
                    repeater = Task { @MainActor in
                        try? await Task.sleep(for: .milliseconds(420))
                        while !Task.isCancelled { action(); try? await Task.sleep(for: .milliseconds(140)) }
                    }
                }
                .onEnded { _ in pressed = false; repeater?.cancel(); repeater = nil })
    }
}

struct OnbRemoteButton: View {
    let label: String, caption: String
    let size: CGFloat
    let filled: Bool
    let action: () -> Void
    var body: some View {
        VStack(spacing: 6) {
            Button(action: action) {
                Text(label).font(Onb.font(size * 0.4, 900)).foregroundStyle(filled ? Onb.ink : .white)
                    .frame(width: size, height: size)
                    .background(filled ? AnyShapeStyle(LinearGradient(colors: [Onb.goldHi, Onb.gold], startPoint: .top, endPoint: .bottom)) : AnyShapeStyle(Color.white.opacity(0.09)), in: Circle())
                    .overlay(Circle().strokeBorder(filled ? .clear : .white.opacity(0.3), lineWidth: 2.5))
                    .shadow(color: .black.opacity(0.35), radius: 0, y: 4)
            }.buttonStyle(.plain)
            Text(caption).font(Onb.font(13, 800)).foregroundStyle(.white.opacity(0.7))
        }
    }
}
