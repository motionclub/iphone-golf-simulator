import SwiftUI

/// The phone in the pointer menu (PLAN_PointerMenu.md): the party leader moves the TV's cursor with a thumbstick and presses the big
/// gold Select button; Back and Center under it; "Pointing at …" says what the TV has lit. A guest's phone says who is choosing (their own
/// locker is one tap away). With no TV the menu is drawn on this phone's own screen and a finger taps it directly.
/// A detail screen the TV opened (mode options, the course picker, settings, the locker editor) shows over this, as before.
struct MenuControllerView: View {
    @Bindable var hub = HubSession.shared
    var body: some View {
        if hub.phase == .failed { HubFailedPanel(hub: hub) }
        else if let bay = hub.station, HubSession.partyBays.contains(bay), hub.party != nil { HubPartyBayPanel(hub: hub) }
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
                Text(hub.phase == .booting ? "GETTING READY" : "POINTING AT").font(MotionBrand.font(.semiBold, 15)).tracking(3.5).foregroundStyle(MotionBrand.n300)
                Text(hub.phase == .booting ? hub.loadStage : hub.menuHoverLabel.isEmpty ? "Move the stick" : hub.menuHoverLabel)
                    .font(MotionBrand.font(.extraBoldItalic, 44)).foregroundStyle(MotionBrand.gold).lineLimit(1).minimumScaleFactor(0.6)
                    .accessibilityIdentifier("menu-pointing")
                if !hub.notice.isEmpty { Text(hub.notice).font(MotionBrand.font(.medium, 15)).foregroundStyle(.white.opacity(0.9)) }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            // the stick moves the cursor on the TV; the thumb can land anywhere in its area (eyes stay on the TV)
            HubStick(diameter: 230) { x, y, m in hub.menuStick(x: x, y: y, magnitude: m) }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .accessibilityIdentifier("menu-stick")
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
            HStack(spacing: 14) {
                Button { hub.menuBack() } label: { Label("Back", systemImage: "chevron.left") }
                    .buttonStyle(MotionButtonStyle(kind: .secondary)).accessibilityIdentifier("menu-back")
                Button { hub.menuRecenter() } label: { Text(hub.recentred ? "Centred" : "Center") }
                    .buttonStyle(MotionButtonStyle(kind: .ghost)).frame(maxWidth: .infinity).accessibilityIdentifier("menu-recenter")
            }
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
            Text("\(hub.menuLeaderName) is choosing").font(MotionBrand.font(.extraBoldItalic, 38)).fixedSize(horizontal: false, vertical: true)
            Text("Watch the TV. Your phone takes over when the match starts.").font(MotionBrand.font(.medium, 18)).foregroundStyle(MotionBrand.n300)
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

/// No TV: the menu is drawn by Unity in the top band of this screen (16:9); a finger on it points and taps. Back and the loading
/// screen sit under it.
struct MenuTouchPad: View {
    let hub: HubSession
    @State private var down = false
    var body: some View {
        GeometryReader { g in
            let band = g.size.width * 9 / 16
            VStack(spacing: 0) {
                ZStack {
                    Color.clear.contentShape(Rectangle())
                        .gesture(DragGesture(minimumDistance: 0, coordinateSpace: .local)
                            .onChanged { v in touch(v.location, in: CGSize(width: g.size.width, height: band), down: true) }
                            .onEnded { v in touch(v.location, in: CGSize(width: g.size.width, height: band), down: false) })
                    if !hub.revealedOnPhone {
                        HubLoadingScreen(hub: hub).scaleEffect(g.size.width / 1280).frame(width: g.size.width, height: band).background(Club.ink).allowsHitTesting(false)
                    }
                }
                .frame(height: band)
                VStack(spacing: 14) {
                    MotionWordmark(size: 26)
                    Text("Tap the menu above. Connect a TV with AirPlay to play.").font(MotionBrand.font(.medium, 16)).foregroundStyle(MotionBrand.n300).multilineTextAlignment(.center)
                    if !hub.notice.isEmpty { Text(hub.notice).font(MotionBrand.font(.medium, 15)) }
                    Spacer()
                    Button { hub.menuBack() } label: { Label("Back", systemImage: "chevron.left") }.buttonStyle(MotionButtonStyle(kind: .secondary))
                }
                .padding(20).frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(MotionBrand.background)
            }
        }
        .ignoresSafeArea(edges: .top)
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
