import SwiftUI

/// The phone in the pointer menu (PLAN_PointerMenu.md): the party leader moves the TV's gold highlight with an arrow pad (ARROW FOCUS,
/// Adnan 10-28: no cursor) and presses the big gold Select button; Back under it; "Selected …" says what the TV has lit. A guest's phone says who is choosing (their own
/// locker is one tap away). With no TV the menu is drawn on this phone's own screen and a finger taps it directly.
/// A detail screen the TV opened (mode options, the course picker, settings, the locker editor) shows over this, as before.
struct MenuControllerView: View {
    @Bindable var hub = HubSession.shared
    var body: some View {
        if hub.phase == .failed { HubFailedPanel(hub: hub) }
        else if hub.party != nil, hub.partyService.partyReadyCheck || (hub.station.map { HubSession.partyBays.contains($0) } ?? false) { HubPartyBayPanel(hub: hub) }
        else if hub.onlineBench != nil { HubOnlineBenchPanel(hub: hub) }
        else if hub.panelOpen { HubStationPanel(hub: hub) }
        else if hub.onPhone { MenuTouchPad(hub: hub) }
        else if !hub.menuLeader { MenuGuestView(hub: hub) }
        else { MenuPointerPad(hub: hub) }
    }
}

/// The leader's remote.
struct MenuPointerPad: View {
    let hub: HubSession
    @State private var pressed = false
    var body: some View {
        VStack(spacing: 16) {
            HStack {
                MotionWordmark(size: 30)
                Spacer()
                if let name = hub.menuPlayerName {
                    HStack(spacing: 8) {
                        Text("1").font(MotionBrand.font(.extraBold, 14)).foregroundStyle(MotionBrand.navyInk)
                            .frame(width: 26, height: 26).background(MotionBrand.glow, in: Circle())
                        Text(name).font(MotionBrand.font(.semiBold, 16))
                    }
                    .padding(.leading, 4).padding(.trailing, 12).frame(height: 36)
                    .background(MotionBrand.navyDeep, in: Capsule()).overlay(Capsule().strokeBorder(.white, lineWidth: 3))
                }
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(hub.phase == .booting ? "GETTING READY" : "SELECTED").font(MotionBrand.font(.semiBold, 15)).tracking(3.5).foregroundStyle(MotionBrand.n300)
                Text(hub.phase == .booting ? hub.loadStage : hub.menuHoverLabel.isEmpty ? "Use the arrows" : hub.menuHoverLabel)
                    .font(MotionBrand.font(.extraBoldItalic, 44)).foregroundStyle(MotionBrand.gold).lineLimit(1).minimumScaleFactor(0.6)
                    .accessibilityIdentifier("menu-pointing")
                if !hub.notice.isEmpty { Text(hub.notice).font(MotionBrand.font(.medium, 15)).foregroundStyle(.white.opacity(0.9)) }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            // the arrows step the TV's highlight: a tap is one step, holding repeats (eyes stay on the TV)
            MenuArrowPad { hub.menuMove($0) }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .accessibilityIdentifier("menu-arrows")
            // Select: a big gold button under the stick
            ZStack {
                ZStack(alignment: .bottom) {
                    RoundedRectangle(cornerRadius: 32, style: .continuous).fill(MotionBrand.goldDeep)
                    RoundedRectangle(cornerRadius: 32, style: .continuous)
                        .fill(LinearGradient(colors: [MotionBrand.gold, MotionBrand.goldWordmark], startPoint: .top, endPoint: .bottom))
                        .padding(.bottom, pressed ? 0 : 6)
                }
                Text("SELECT").font(MotionBrand.font(.extraBoldItalic, 36)).foregroundStyle(MotionBrand.navyInk)
            }
            .frame(height: 120)
            .scaleEffect(pressed ? 0.95 : 1).animation(.easeOut(duration: 0.12), value: pressed)
            .shadow(color: MotionBrand.shadowInk.opacity(0.43), radius: 14, y: 12)
            .contentShape(Rectangle())
            .gesture(DragGesture(minimumDistance: 0)
                .onChanged { _ in if !pressed { pressed = true; hub.menuSelect(true) } }
                .onEnded { _ in pressed = false; hub.menuSelect(false) })
            .accessibilityElement().accessibilityLabel("Select").accessibilityAddTraits(.isButton)
            .accessibilityAction { hub.menuSelect(true); hub.menuSelect(false) }
            .accessibilityIdentifier("menu-select")
            // in a party: its game is one tap away (Tennis or Golf with everyone; each friend taps Ready)
            if hub.party != nil {
                Button { hub.openPartyGame() } label: { Label("Party game", systemImage: "person.3.fill") }
                    .buttonStyle(MotionButtonStyle(kind: .secondary)).accessibilityIdentifier("menu-party-game")
            }
            Button { hub.menuBack() } label: { Label("Back", systemImage: "chevron.left") }
                .buttonStyle(MotionButtonStyle(kind: .secondary)).accessibilityIdentifier("menu-back")
        }
        .foregroundStyle(.white)
        .padding(.horizontal, 20).padding(.top, 16).padding(.bottom, 12)
        .background(ZStack { MotionBrand.background; RadialGradient(colors: [MotionBrand.lift.opacity(0.55), .clear], center: .center, startRadius: 0, endRadius: 360) }.ignoresSafeArea())
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("menu-controller")
    }
}

/// A guest's phone: the leader drives the TVs.
struct MenuGuestView: View {
    let hub: HubSession
    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            MotionWordmark(size: 30)
            Spacer()
            Text("\(hub.menuLeaderName) is picking a game").font(MotionBrand.font(.extraBoldItalic, 38)).fixedSize(horizontal: false, vertical: true)
            Text("You're in the party. When they start, a big Ready button shows up here.").font(MotionBrand.font(.medium, 18)).foregroundStyle(MotionBrand.n300)
            if !hub.notice.isEmpty { Text(hub.notice).font(MotionBrand.font(.medium, 15)).foregroundStyle(MotionBrand.gold) }
            Spacer()
            Button { hub.openPanel(.character) } label: { Label("Your locker", systemImage: "tshirt.fill") }
                .buttonStyle(MotionButtonStyle(kind: .secondary)).accessibilityIdentifier("menu-guest-locker")
            Button { hub.inviteFriends() } label: { Label("Friends", systemImage: "person.2.fill") }
                .buttonStyle(MotionButtonStyle(kind: .secondary))
        }
        .foregroundStyle(.white)
        .padding(24)
        .background(MotionBrand.background.ignoresSafeArea())
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("menu-guest")
    }
}

/// No TV: Unity draws the hero at the top of this screen and the menu's 16:9 frame under him (HubWorld.PhoneMenuView, so the words
/// never cover him); a finger on the frame points and taps. Back sits under it, in the bottom `HubSession.menuFooterShare` of the
/// screen. A screen too short for that (Unity's rule, mirrored here) keeps the frame as a band under the status bar, the hero in it.
struct MenuTouchPad: View {
    let hub: HubSession
    @State private var down = false
    var body: some View {
        GeometryReader { g in
            // Unity lays out on the whole screen: measure it the same way (HandheldFrame does too)
            let insets = g.safeAreaInsets
            let screen = CGSize(width: g.size.width + insets.leading + insets.trailing, height: g.size.height + insets.top + insets.bottom)
            let frame = screen.width * 9 / 16, footer = screen.height * HubSession.menuFooterShare
            let stacked = screen.height - footer - frame >= screen.width * 0.8
            let hero = stacked ? screen.height - footer - frame : insets.top
            VStack(spacing: 0) {
                // the hero (see-through to Unity), or the status bar over the band
                Color.clear.frame(height: hero)
                ZStack {
                    Color.clear.contentShape(Rectangle())
                        .gesture(DragGesture(minimumDistance: 0, coordinateSpace: .local)
                            .onChanged { v in touch(v.location, in: CGSize(width: screen.width, height: frame), down: true) }
                            .onEnded { v in touch(v.location, in: CGSize(width: screen.width, height: frame), down: false) })
                        .accessibilityIdentifier("menu-touch-frame")
                }
                .frame(height: frame)
                VStack(spacing: 10) {
                    if !hub.notice.isEmpty { Text(hub.notice).font(MotionBrand.font(.medium, 14)).lineLimit(2).multilineTextAlignment(.center) }
                    else {
                        Text("Golf and bowling play right here on your phone. Tennis needs a TV (AirPlay).").font(MotionBrand.font(.medium, 13))
                            .foregroundStyle(MotionBrand.n300).multilineTextAlignment(.center).lineLimit(2).minimumScaleFactor(0.8)
                    }
                    Button { hub.menuBack() } label: { Label("Back", systemImage: "chevron.left") }.buttonStyle(MotionButtonStyle(kind: .secondary))
                }
                .padding(.horizontal, 20).padding(.top, 10).padding(.bottom, insets.bottom + 6)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                .background(MotionBrand.background)
            }
            .overlay(alignment: .top) {
                if !hub.revealedOnPhone {
                    // loading: the plaza's loading screen over Unity's part of the screen
                    HubLoadingScreen(hub: hub).scaleEffect(screen.width / 1280).frame(width: screen.width, height: 720 * screen.width / 1280)
                        .frame(width: screen.width, height: stacked ? hero + frame : insets.top + frame).background(Club.ink).allowsHitTesting(false)
                }
            }
            .frame(width: screen.width, height: screen.height)
            .ignoresSafeArea()
        }
        .foregroundStyle(.white)
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("menu-touch")
    }
    private func touch(_ p: CGPoint, in size: CGSize, down: Bool) {
        let x = max(-1, min(1, p.x / size.width * 2 - 1)), y = max(-1, min(1, 1 - p.y / size.height * 2))
        hub.menuTouch(x: x, y: y, down: down)
        self.down = down
    }
}

/// The menu's arrow pad: four arrows in a plus (the tennis remote's layout). A tap is one step; holding repeats after a short delay.
struct MenuArrowPad: View {
    let move: (String) -> Void
    var body: some View {
        let cell: CGFloat = 92, gap: CGFloat = 8
        ZStack {
            arrow("arrowtriangle.up.fill", "up").offset(y: -(cell + gap))
            arrow("arrowtriangle.left.fill", "left").offset(x: -(cell + gap))
            arrow("arrowtriangle.right.fill", "right").offset(x: cell + gap)
            arrow("arrowtriangle.down.fill", "down").offset(y: cell + gap)
            Circle().strokeBorder(.white.opacity(0.14), style: StrokeStyle(lineWidth: 2, dash: [4, 5])).frame(width: 60, height: 60)
        }
        .frame(width: cell * 3 + gap * 2, height: cell * 3 + gap * 2)
    }
    private func arrow(_ icon: String, _ direction: String) -> some View {
        MenuRepeatButton(action: { move(direction) }) { pressed in
            Image(systemName: icon).font(.system(size: 32, weight: .bold))
                .foregroundStyle(pressed ? MotionBrand.navyInk : .white)
                .frame(width: 92, height: 92)
                .background(pressed ? MotionBrand.gold : .white.opacity(0.09), in: RoundedRectangle(cornerRadius: 24, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).strokeBorder(pressed ? MotionBrand.gold : .white.opacity(0.22), lineWidth: 2.5))
                .scaleEffect(pressed ? 0.95 : 1)
        }
        .accessibilityLabel("Move \(direction)")
        .accessibilityIdentifier("menu-arrow-\(direction)")
    }
}

/// Acts on touch-down; keeps acting while held (0.42 s, then every 0.11 s). Sliding the finger does nothing extra.
private struct MenuRepeatButton<Label: View>: View {
    let action: () -> Void
    @ViewBuilder let label: (Bool) -> Label
    @State private var pressed = false
    @State private var timer: Timer?
    var body: some View {
        label(pressed)
            .contentShape(Rectangle())
            .gesture(DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    guard !pressed else { return }
                    pressed = true; action()
                    timer?.invalidate()
                    let start = Timer(timeInterval: 0.42, repeats: false) { _ in
                        MainActor.assumeIsolated {
                            guard pressed else { return }
                            let repeater = Timer(timeInterval: 0.11, repeats: true) { _ in MainActor.assumeIsolated { action() } }
                            RunLoop.main.add(repeater, forMode: .common); timer = repeater
                        }
                    }
                    RunLoop.main.add(start, forMode: .common); timer = start
                }
                .onEnded { _ in pressed = false; timer?.invalidate(); timer = nil })
            .accessibilityAddTraits(.isButton)
            .accessibilityAction { action() }
            .onDisappear { timer?.invalidate(); timer = nil }
    }
}
