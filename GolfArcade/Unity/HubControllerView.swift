import SwiftUI

/// The phone as the Plaza's controller (PLAN_MenuHub_WalkableWorld §6, Explore): an analog stick with magnitude (a short push
/// walks, a full push runs, holding it full sprints), A / B, ☰ (go anywhere), Emote and Friends, and a strip saying what you are
/// standing at. With a TV the player's eyes are on the TV; with none the plaza itself is drawn in the top part of this screen
/// (Unity, under this see-through view) and the controls sit below it.
///
/// This is all the phone ever shows outside a match: a station's own panel, an online bench's panel and the Friends list open
/// over it, and nothing else replaces it.
struct HubControllerView: View {
    @Bindable var hub = HubSession.shared
    @State private var quickMenu = false
    @State private var emotes = false
    private var session: SportsSession { .shared }

    var body: some View {
        if hub.phase == .failed { HubFailedPanel(hub: hub) }
        else if hub.party != nil, hub.partyService.partyReadyCheck || (hub.station.map { HubSession.partyBays.contains($0) } ?? false) { HubPartyBayPanel(hub: hub) }
        else if hub.onlineBench != nil { HubOnlineBenchPanel(hub: hub) }
        else if hub.panelOpen { HubStationPanel(hub: hub) }
        else if hub.onPhone { phoneExplore } else { explore }
    }

    /// No TV: the plaza on the top part of the screen (see-through to Unity), the controls under it.
    private var phoneExplore: some View {
        GeometryReader { g in
            let top = g.size.height * HubSession.phoneViewShare
            VStack(spacing: 0) {
                ZStack(alignment: .top) {
                    Color.clear
                    if !hub.revealedOnPhone {
                        // the plaza is loading: its loading screen, fitted to the plaza's part of the screen
                        HubLoadingScreen(hub: hub).scaleEffect(g.size.width / 1280).frame(width: g.size.width, height: 720 * g.size.width / 1280)
                            .frame(maxWidth: .infinity, maxHeight: .infinity).background(Club.ink).transition(.opacity)
                    }
                    HStack {
                        Text(Self.placeName(hub.place)).font(IslandUI.font(12, bold: true)).tracking(1.4).foregroundStyle(IslandUI.lime)
                            .padding(.horizontal, 10).padding(.vertical, 5).background(.black.opacity(0.45), in: Capsule()).accessibilityIdentifier("hub-place")
                        Spacer()
                        Label("Phone only · AirPlay a TV to play", systemImage: "tv").font(IslandUI.font(11, bold: true)).foregroundStyle(.white)
                            .padding(.horizontal, 10).padding(.vertical, 5).background(.black.opacity(0.45), in: Capsule()).accessibilityIdentifier("hub-connection")
                    }
                    .padding(.horizontal, 12).padding(.top, 56)
                    VStack { Spacer(); phonePrompt }
                }
                .frame(height: top).clipped()
                controls(compact: true)
                    .padding(.horizontal, 18).padding(.top, 14).padding(.bottom, 6)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(IslandBrandBackground())
            }
        }
        .ignoresSafeArea(edges: .top)
        .foregroundStyle(.white)
        .preferredColorScheme(.dark)
        .modifier(sheets)
        .accessibilityIdentifier("hub-controller")
    }
    private var phonePrompt: some View {
        VStack(spacing: 3) {
            Text(hub.phase == .booting ? hub.loadStage : hub.zonePrompt ?? Self.idleHint(hub.place, onPhone: true))
                .font(IslandUI.font(17, bold: true)).lineLimit(2).minimumScaleFactor(0.7).multilineTextAlignment(.center)
                .accessibilityIdentifier("hub-prompt")
            if !hub.notice.isEmpty { Text(hub.notice).font(IslandUI.font(13, bold: true)).foregroundStyle(IslandUI.lime) }
        }
        .padding(.horizontal, 14).padding(.vertical, 8).background(.black.opacity(0.5), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .padding(.bottom, 10)
    }

    /// The stick, the buttons and the Menu / Friends pills. Compact (beside the plaza on a phone with no TV): a game-pad, the stick on
    /// the left and the buttons on the right.
    private func controls(compact: Bool) -> some View {
        VStack(spacing: compact ? 10 : 16) {
            if compact {
                HStack(alignment: .center, spacing: 6) {
                    HubStick(diameter: 196) { x, y, mag in hub.setStick(x: x, y: y, magnitude: mag) }
                        .frame(width: 204, height: 206)
                        .opacity(hub.phase == .live ? 1 : 0.4).disabled(hub.phase != .live)
                    Spacer(minLength: 0)
                    VStack(spacing: 8) {
                        HubRoundButton(label: "A", caption: aCaption, size: 82, filled: true) { hub.pressA() }
                            .opacity(hub.zone.map { $0.kind != .door } ?? false ? 1 : 0.55)
                        HStack(spacing: 12) {
                            HubRoundButton(label: "B", caption: "Back", size: 54) { hub.pressB() }
                            HubRoundButton(label: "☺", caption: "Emote", size: 54) { emotes = true }
                        }
                    }
                }
            } else {
                HubStick { x, y, mag in hub.setStick(x: x, y: y, magnitude: mag) }
                    .frame(maxWidth: .infinity, minHeight: HubStick.diameter + 10, maxHeight: .infinity)
                    .opacity(hub.phase == .live ? 1 : 0.4)
                    .disabled(hub.phase != .live)
                Text(hub.phase == .booting ? "Watch the TV · the stick wakes up at 100%" : "Thumb down anywhere here · short push walks · full push runs · hold to sprint")
                    .font(IslandUI.font(13, bold: true)).foregroundStyle(.white.opacity(0.55)).multilineTextAlignment(.center)
                HStack(alignment: .center, spacing: 22) {
                    HubRoundButton(label: "B", caption: "Back", size: 74) { hub.pressB() }
                    HubRoundButton(label: "A", caption: aCaption, size: 104, filled: true) { hub.pressA() }
                        .opacity(hub.zone.map { $0.kind != .door } ?? false ? 1 : 0.55)
                    HubRoundButton(label: "☺", caption: "Emote", size: 74) { emotes = true }
                }
            }
            HStack(spacing: 12) {
                pill("line.3.horizontal", "Menu", id: "hub-menu") { quickMenu = true }
                // one button for everything social: friends online, one-tap invites, invites you got, your party
                pill("person.2.fill", friendsTitle, id: "hub-party") { hub.inviteFriends() }
                    .overlay(alignment: .topTrailing) {
                        if ClubHub.shared.unreadInvites > 0 {
                            Text("\(ClubHub.shared.unreadInvites)").font(IslandUI.font(12, bold: true)).foregroundStyle(IslandUI.navy)
                                .frame(minWidth: 22, minHeight: 22).background(IslandUI.lime, in: Circle()).offset(x: 4, y: -6)
                                .accessibilityIdentifier("hub-invite-badge")
                        }
                    }
            }
        }
    }
    private var sheets: HubControllerSheets { HubControllerSheets(hub: hub, quickMenu: $quickMenu, emotes: $emotes, currentEmotes: currentEmotes) }

    private var explore: some View {
        VStack(spacing: 16) {
            header
            onTV
            // the whole middle of the phone is the stick: a thumb put down anywhere there walks the hero, eyes on the TV
            controls(compact: false)
        }
        .foregroundStyle(.white)
        .padding(.horizontal, 24).padding(.vertical, 18)
        .background(IslandBrandBackground().ignoresSafeArea())
        .preferredColorScheme(.dark)
        .modifier(sheets)
        .accessibilityIdentifier("hub-controller")
    }

    private var friendsTitle: String { hub.party.map { "Friends · \($0.participants.filter { !$0.isGuest }.count) in your party" } ?? "Invite friends" }
    private var currentEmotes: [String] {
        session.players.indices.contains(session.playerIndex) ? session.players[session.playerIndex].equippedEmotes : EmoteCatalog.defaults
    }
    private var aCaption: String {
        switch hub.zone?.kind { case .station: "Use"; case .bay: "Sit"; default: "A" }
    }

    private var header: some View {
        HStack {
            HStack(spacing: 8) {
                Circle().fill(hub.phase == .live ? IslandUI.lime : .orange).frame(width: 10, height: 10)
                    .shadow(color: hub.phase == .live ? IslandUI.lime : .orange, radius: 5)
                Text(hub.phase == .live ? "Connected to TV" : "Loading on the TV").font(IslandUI.font(15, bold: true))
                    .accessibilityIdentifier("hub-connection")
            }
            .padding(.horizontal, 14).padding(.vertical, 8).background(.white.opacity(0.1), in: Capsule())
            Spacer()
            Text(Self.placeName(hub.place)).font(IslandUI.font(13, bold: true)).tracking(1.4).foregroundStyle(IslandUI.lime)
                .accessibilityIdentifier("hub-place")
        }
    }

    private var onTV: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("ON THE TV · \(Self.placeName(hub.place))").font(IslandUI.font(12, bold: true)).tracking(1.6).foregroundStyle(IslandUI.lime)
            Text(hub.phase == .booting ? hub.loadStage : hub.zonePrompt ?? Self.idleHint(hub.place))
                .font(IslandUI.font(session.bigText ? 28 : 22, bold: true)).lineLimit(2).minimumScaleFactor(0.6)
                .accessibilityIdentifier("hub-prompt")
            if hub.phase == .booting {
                // the TV's loading bar, small
                HStack(spacing: 12) {
                    PacedBar(pace: hub.pace, style: .plain(IslandUI.lime)).frame(height: 10)
                    MSLoadingPercent(pace: hub.pace, font: .systemFont(ofSize: 20, weight: .heavy), color: UIColor(IslandUI.lime)).frame(width: 56, alignment: .trailing)
                }
                .accessibilityElement(children: .ignore).accessibilityLabel("Loading")
                .accessibilityIdentifier("hub-loading-bar")
            }
            if let detail = hub.zone?.detail, !detail.isEmpty, hub.zone?.kind != .door {
                Text(detail).font(IslandUI.font(14, bold: false)).foregroundStyle(.white.opacity(0.7))
            }
            if !hub.notice.isEmpty { Text(hub.notice).font(IslandUI.font(13, bold: true)).foregroundStyle(IslandUI.lime).padding(.top, 2) }
        }
        .frame(maxWidth: .infinity, alignment: .leading).padding(.horizontal, 18).padding(.vertical, 14)
        .background(.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).strokeBorder(.white.opacity(0.14), lineWidth: 1.5))
    }

    private func pill(_ icon: String, _ title: String, id: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Label(title, systemImage: icon).font(IslandUI.font(16, bold: true)).foregroundStyle(.white)
                .frame(maxWidth: .infinity, minHeight: 46)
                .background(.white.opacity(0.09), in: Capsule())
                .overlay(Capsule().strokeBorder(.white.opacity(0.22), lineWidth: 2))
        }.buttonStyle(.plain).accessibilityIdentifier(id)
    }

    static func placeName(_ place: String) -> String {
        switch place {
        case "locker": "LOCKER ROOM"; case "clubhouse": "CLUBHOUSE"; case "play": "PLAY HALL"
        case "tennis": "TENNIS"; case "golf": "GOLF"; default: "THE PLAZA"
        }
    }
    static func idleHint(_ place: String, onPhone: Bool = false) -> String {
        switch place {
        case "plaza": onPhone ? "Walk to LOCKER or CLUBHOUSE · PLAY needs a TV" : "Walk to LOCKER, CLUBHOUSE or PLAY"
        case "play": "Tennis on the left · Golf on the right"
        case "tennis", "golf": "Sit on a bench to play"
        default: "Walk up to something to use it"
        }
    }
}

/// The controller's own sheets: ☰ and the emote picker.
struct HubControllerSheets: ViewModifier {
    let hub: HubSession
    @Binding var quickMenu: Bool
    @Binding var emotes: Bool
    let currentEmotes: [String]
    func body(content: Content) -> some View {
        content
            .sheet(isPresented: $quickMenu) { HubQuickMenu(hub: hub, dismiss: { quickMenu = false }).presentationDetents([.medium, .large]) }
            .confirmationDialog("Emote", isPresented: $emotes, titleVisibility: .visible) {
                ForEach(currentEmotes, id: \.self) { id in Button(EmoteCatalog.name(id)) { hub.emote(id) } }
            }
    }
}

/// The TV while the game starts and the Plaza boots (MotionSports title loading, picked 2026-10-25): the wordmark and tagline on
/// the brand's royal-to-navy spotlight with the swing arc sweeping over, and LOADING… with the bar. The bar is
/// HubSession.pace (steady, on Core Animation, so the cold Unity start cannot freeze it); at 100 % it holds a moment and fades into
/// the arrival fly-in. Drawn on the 1280×720 TV canvas (the phone with no TV shows it scaled above its controls).
struct HubLoadingScreen: View {
    let hub: HubSession
    var body: some View {
        let failed = hub.phase == .failed
        ZStack(alignment: .topLeading) {
            MSBrand.backdrop(spotlight: UnitPoint(x: 0.3, y: 0.47), radius: 820)
            MSSwingArc().frame(width: 1280, height: 720)
            VStack(alignment: .leading, spacing: 44) {
                MSWordmark(size: 96)
                Text("Swing your phone. Play on your TV.").font(MSLoadingFont.subline(30)).foregroundStyle(MSBrand.n300)
                    .shadow(color: MSBrand.textShadow.opacity(0.55), radius: 3, y: 1).padding(.leading, 6)
            }
            .position(x: 128 + 255, y: 360)
            VStack(spacing: 12) {
                HStack(alignment: .center) {
                    Text(failed ? "The Plaza didn't open · tap Try again on your phone" : "LOADING…")
                        .font(MSLoadingFont.display(failed ? 24 : 28)).foregroundStyle(.white)
                        .shadow(color: MSBrand.textShadow.opacity(0.55), radius: 3, y: 1)
                        .accessibilityLabel(failed ? "The Plaza didn't open" : hub.loadStage).accessibilityIdentifier("hub-loading-stage")
                    Spacer()
                    if !failed { MSLoadingPercent(pace: hub.pace, font: MSLoadingFont.uiDisplay(28), color: UIColor(MSBrand.gold)) }
                }
                MSLoadingBar(pace: hub.pace, fill: MSBrand.gold, height: 22)
            }
            .frame(width: 1024).position(x: 640, y: 622)
        }
        .frame(width: 1280, height: 720)
        .clipped()
        .ignoresSafeArea()
        .accessibilityIdentifier("hub-loading")
    }
}

/// An analog thumbstick that floats: direction and how far it is pushed (0…1), free in every direction. The player's eyes are on
/// the TV, so the stick is not a target to hit: a thumb put down anywhere in its area is the stick's centre, and the push is
/// measured from there (the drawn stick moves under the thumb, kept whole on the screen). At rest it sits in the middle.
/// Sends on every drag change; zero on release.
struct HubStick: View {
    /// The drawn stick: the base this wide, the knob travelling to its rim (smaller beside the plaza on a phone with no TV).
    var diameter: CGFloat = HubStick.diameter
    let send: (Double, Double, Double) -> Void
    static let diameter: CGFloat = 270
    @State private var thumb: CGSize = .zero
    /// Where the thumb came down (nil at rest).
    @State private var origin: CGPoint?
    @State private var running = false
    var body: some View {
        GeometryReader { g in
            let radius = diameter / 2
            let travel = radius - 44 * diameter / Self.diameter
            let rest = CGPoint(x: g.size.width / 2, y: g.size.height / 2)
            // the drawn base: under the thumb, but never cut off by the area's edge
            let base = origin.map { CGPoint(x: min(max($0.x, radius), max(radius, g.size.width - radius)),
                                            y: min(max($0.y, radius), max(radius, g.size.height - radius))) } ?? rest
            ZStack {
                Color.clear.contentShape(Rectangle())
                stick(radius: radius, travel: travel).frame(width: diameter, height: diameter).position(base)
            }
            .gesture(DragGesture(minimumDistance: 0, coordinateSpace: .local)
                .onChanged { drag in
                    if origin == nil { origin = drag.startLocation }
                    let start = origin ?? drag.startLocation
                    let dx = drag.location.x - start.x, dy = drag.location.y - start.y
                    let distance = hypot(dx, dy)
                    let mag = min(1, distance / max(1, travel))
                    let length = min(travel, distance)
                    thumb = distance > 0 ? CGSize(width: dx / distance * length, height: dy / distance * length) : .zero
                    let nowRunning = mag >= 0.7
                    if nowRunning != running { running = nowRunning; if SportsSession.shared.haptics { UISelectionFeedbackGenerator().selectionChanged() } }
                    if distance > 0 { send(dx / distance, -dy / distance, mag) } else { send(0, 0, 0) }
                }
                .onEnded { _ in
                    withAnimation(.spring(response: 0.18, dampingFraction: 0.7)) { thumb = .zero; origin = nil }
                    running = false; send(0, 0, 0)
                })
            .accessibilityElement()
            .accessibilityIdentifier("hub-stick")
            .accessibilityLabel("Walk stick")
        }
    }

    private func stick(radius: CGFloat, travel: CGFloat) -> some View {
        ZStack {
            Circle().fill(Color(hex: "1F3B6E"))
                .overlay(Circle().stroke(Color(hex: "B4E5FF").opacity(0.55), lineWidth: 5))
                .overlay(Circle().stroke(.white.opacity(0.35), lineWidth: 1.5).padding(4))
            // the run ring: past it you run
            let knob = 44 * diameter / Self.diameter
            Circle().strokeBorder(IslandUI.lime.opacity(running ? 0.75 : 0.25), style: StrokeStyle(lineWidth: 2, dash: [5, 6]))
                .frame(width: (knob + travel * 0.7) * 2, height: (knob + travel * 0.7) * 2)
            ForEach(0..<4) { i in
                Image(systemName: "triangle.fill").font(.system(size: 12, weight: .bold)).foregroundStyle(.white.opacity(0.5))
                    .offset(y: -(radius - 16)).rotationEffect(.degrees(Double(i) * 90))
            }
            Circle().fill(LinearGradient(colors: [.white, Color(hex: "D0E9FA")], startPoint: .top, endPoint: .bottom))
                .frame(width: 88 * diameter / Self.diameter, height: 88 * diameter / Self.diameter)
                .overlay(Circle().stroke(running ? IslandUI.lime : .white, lineWidth: 3))
                .shadow(color: .black.opacity(0.45), radius: 0, y: 5)
                .offset(thumb)
        }
        .allowsHitTesting(false)
    }
}

private struct HubRoundButton: View {
    let label: String
    let caption: String
    let size: CGFloat
    var filled = false
    var action: () -> Void
    var body: some View {
        VStack(spacing: 7) {
            Button(action: action) {
                Text(label).font(IslandUI.font(size * 0.42, bold: true)).foregroundStyle(filled ? IslandUI.navy : .white)
                    .frame(width: size, height: size)
                    .background(filled ? IslandUI.lime : .clear, in: Circle())
                    .overlay(Circle().strokeBorder(filled ? .clear : .white.opacity(0.42), lineWidth: 3))
                    .shadow(color: filled ? .black.opacity(0.4) : .clear, radius: 0, y: filled ? 5 : 0)
            }.buttonStyle(.plain).accessibilityLabel(caption).accessibilityIdentifier("hub-\(caption.lowercased())")
            Text(caption.uppercased()).font(IslandUI.font(12, bold: true)).tracking(1.6).foregroundStyle(.white.opacity(0.6))
        }
    }
}

/// ☰: the Destiny-style launcher. Jump to any room, or straight to a shortcut.
struct HubQuickMenu: View {
    let hub: HubSession
    let dismiss: () -> Void
    @State private var leavingParty = false
    static let places: [(id: String, title: String, icon: String)] = [
        ("plaza", "The Plaza", "sun.horizon.fill"), ("locker", "Locker Room", "tshirt.fill"), ("clubhouse", "Clubhouse", "crown.fill"),
        ("play", "PLAY Hall", "flag.checkered"), ("tennis", "Tennis room", "tennis.racket"), ("golf", "Golf room", "figure.golf")]
    /// One tap to the thing you came for (ROUTE_ALL: every old menu destination in two presses).
    static let shortcuts: [(id: String, title: String, icon: String)] = [
        ("bay-tennis-exhibition", "Exhibition vs CPU", "bolt.fill"), ("bay-tennis-training", "Training", "figure.tennis"),
        ("bay-tennis-nearby", "Local tennis", "person.2.fill"), ("bay-golf-round", "Golf round", "figure.golf"),
        ("bay-tennis-online", "Play online", "globe"), ("bay-golf-pass", "Local golf", "iphone.and.arrow.forward"),
        ("look-mirror", "Locker", "tshirt.fill"), ("desk-settings", "Settings", "gearshape.fill"), ("screen-howto", "How to play", "questionmark.circle.fill"),
        ("board-invite", "Friends", "person.badge.plus")]
    /// Without a TV the PLAY hall and its benches are shut: they are not offered.
    private static let playOnly: Set<String> = ["play", "tennis", "golf", "bay-tennis-exhibition", "bay-tennis-training", "bay-tennis-nearby",
                                                "bay-golf-round", "bay-tennis-online", "bay-golf-pass"]
    var body: some View {
        NavigationStack {
            List {
                if hub.onPhone {
                    Section { Label("Connect a TV with AirPlay to play: the Plaza moves onto it and the PLAY hall opens.", systemImage: "tv").font(.footnote) }
                }
                Section("Go to") {
                    ForEach(Self.places.filter { !hub.onPhone || !Self.playOnly.contains($0.id) }, id: \.id) { place in
                        Button { hub.go(place.id); dismiss() } label: { Label(place.title, systemImage: place.icon) }
                            .accessibilityIdentifier("hub-go-\(place.id)")
                    }
                }
                Section("Shortcuts") {
                    ForEach(Self.shortcuts.filter { !hub.onPhone || !Self.playOnly.contains($0.id) }, id: \.id) { s in
                        Button {
                            // inviting needs no walk to the board: the Friends list opens at once
                            if s.id == "board-invite" { dismiss(); hub.inviteFriends(afterSheet: true) } else { hub.openStation(s.id); dismiss() }
                        } label: { Label(s.title, systemImage: s.icon) }
                            .accessibilityIdentifier("hub-use-\(s.id)")
                    }
                }
                if hub.inParty {
                    Section {
                        Button(role: .destructive) { leavingParty = true } label: { Label("Leave party", systemImage: "person.2.slash") }
                            .accessibilityIdentifier("hub-leave-party")
                    } footer: { Text(hub.leavePartyLine) }
                }
                Section {
                    Button { dismiss(); BetaFeedback.open() } label: { Label("Send feedback", systemImage: "envelope") }
                }
            }
            .confirmationDialog("Leave the party?", isPresented: $leavingParty, titleVisibility: .visible) {
                Button("Leave party", role: .destructive) { hub.leaveParty(); dismiss() }
                Button("Stay", role: .cancel) {}
            }
            .navigationTitle("Menu").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done", action: dismiss) } }
        }
    }
}

/// A station or bay in use: the TV frames your hero; the phone shows that station's screen (the same screens as the phone menu).
struct HubStationPanel: View {
    let hub: HubSession
    var body: some View {
        let menu = TennisMenu.shared
        let canGoBack = menu.screen != .title && menu.screen != .main && !SportsSession.shared.menuPauseVisible
        // one bar: Back (within the menu) · where you are · Done (leave the station); the menu's own bar is hidden under it
        VStack(spacing: 0) {
            ZStack {
                Text("\(hub.onPhone ? "PLAZA" : "ON THE TV") · \(HubControllerView.placeName(hub.place))").font(IslandUI.font(12, bold: true)).tracking(1.4)
                    .foregroundStyle(IslandUI.muted).lineLimit(1).minimumScaleFactor(0.7).padding(.horizontal, 110)
                HStack {
                    if canGoBack {
                        Button { menu.back() } label: { Label("Back", systemImage: "chevron.left").font(IslandUI.font(17, bold: true)).foregroundStyle(IslandUI.ink) }
                            .buttonStyle(.plain).accessibilityIdentifier("menu-back")
                    }
                    Spacer()
                    Button { hub.leaveStation() } label: {
                        Text("Done").font(IslandUI.font(16, bold: true)).foregroundStyle(IslandUI.navy)
                            .padding(.horizontal, 18).padding(.vertical, 8).background(IslandUI.lime, in: Capsule())
                    }.buttonStyle(.plain).accessibilityIdentifier("hub-station-done")
                }
            }
            .padding(.horizontal, 20).frame(minHeight: 52)
            .background(IslandUI.dark)
            ZStack { IslandBrandBackground(); TennisMenuScreen(compact: true).environment(\.menuHostsTopBar, true) }
        }
        .foregroundStyle(.white)
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("hub-station-panel")
    }
}

/// The party's game (2026-10-25 flow): the leader picks Tennis or Golf, the map and settings, and taps Start game; every other
/// phone then shows a big Ready, and the match starts on all of them when the last player taps it. The list says who is ready.
/// Leader: opened from the TV menu's Play (Tennis or Golf) or the phone's Party game button. Guests: shown while the leader's
/// Start is waiting for them.
struct HubPartyBayPanel: View {
    let hub: HubSession
    private var party: MultiplayerLobby? { hub.party }
    private var me: String { hub.partyService.localID }
    private var leader: Bool { hub.partyService.isOwner }
    private var checking: Bool { hub.partyService.partyReadyCheck }
    private var golf: Bool { party?.sport == .golf }
    private var bowling: Bool { party?.sport == .bowling }
    private var mine: MultiplayerParticipant? { party?.participants.first { $0.id == me } }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                HStack {
                    Text("PARTY GAME · \(golf ? "GOLF" : bowling ? "BOWLING" : "TENNIS")").font(IslandUI.font(13, bold: true)).tracking(1.4).foregroundStyle(IslandUI.lime)
                    Spacer()
                    if leader && !checking {
                        Button { hub.leaveStation() } label: { Text("Close").font(IslandUI.font(15, bold: true)).foregroundStyle(.white).padding(.horizontal, 14).padding(.vertical, 8).background(.white.opacity(0.12), in: Capsule()) }
                            .buttonStyle(.plain).accessibilityIdentifier("hub-party-leave-seat")
                    }
                }
                Text(headline).font(IslandUI.font(26, bold: true)).fixedSize(horizontal: false, vertical: true).accessibilityIdentifier("hub-party-waiting")
                if leader && !checking, let lobby = party { settings(lobby) }
                if !leader || checking, let lobby = party {
                    Text(golf ? GolfCourseChoice.venueTitle(lobby.venue) : bowling ? (BowlingVenueChoice(rawValue: lobby.venue)?.title ?? lobby.venue.capitalized) + " · 10 frames" : "\(lobby.venue.capitalized) · \(lobby.sets) \(lobby.sets == 1 ? "set" : "sets") · \(lobby.games) games")
                        .font(IslandUI.font(16, bold: true)).foregroundStyle(.white.opacity(0.75))
                }
                VStack(spacing: 8) {
                    ForEach(party?.participants.filter { !$0.isGuest } ?? [], id: \.id) { p in
                        HStack {
                            Circle().fill(p.ready && p.seat >= 0 ? IslandUI.lime : .white.opacity(0.25)).frame(width: 12, height: 12)
                            Text(p.name + (p.id == party?.ownerID ? " · leader" : "") + (p.id == me ? " (you)" : "")).font(IslandUI.font(17, bold: true))
                            Spacer()
                            Text(status(p)).font(IslandUI.font(14, bold: true)).foregroundStyle(p.ready && p.seat >= 0 ? IslandUI.lime : .white.opacity(0.6))
                        }
                        .padding(12).background(.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 14))
                    }
                    if hub.partyService.joiningPeers > 0 {
                        Text("A friend is joining…").font(IslandUI.font(14, bold: true)).foregroundStyle(.white.opacity(0.6)).frame(maxWidth: .infinity, alignment: .leading).padding(.horizontal, 12)
                    }
                }
                if let lobby = party, checking, !lobby.hasScreenForSport {
                    Text(lobby.startReason).font(.subheadline).foregroundStyle(IslandUI.lime).fixedSize(horizontal: false, vertical: true)
                }
                if !hub.notice.isEmpty { Text(hub.notice).font(IslandUI.font(14, bold: true)).foregroundStyle(IslandUI.lime) }
                actions
            }
            .padding(22)
        }
        .foregroundStyle(.white)
        .background(IslandBrandBackground().ignoresSafeArea())
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("hub-party-bay")
    }

    @ViewBuilder private var actions: some View {
        if leader {
            if checking {
                big("Cancel", filled: false) { hub.cancelPartyGame() }.accessibilityIdentifier("hub-party-cancel")
            } else {
                big("Start game", icon: "play.fill") { hub.forcePartyStart() }
                    .opacity(party != nil ? 1 : 0.4).disabled(party == nil).accessibilityIdentifier("hub-party-start")
            }
        } else if checking, (mine?.seat ?? -1) >= 0 {
            if mine?.ready == true {
                big("Not ready", filled: false) { hub.setPartyReady(false) }.accessibilityIdentifier("hub-party-unready")
            } else {
                big("READY", icon: "checkmark") { hub.setPartyReady(true) }.accessibilityIdentifier("hub-party-ready")
            }
        }
    }
    private func big(_ title: String, icon: String? = nil, filled: Bool = true, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 10) {
                if let icon { Image(systemName: icon) }
                Text(title)
            }
            .font(IslandUI.font(filled ? 24 : 18, bold: true)).foregroundStyle(filled ? IslandUI.navy : .white)
            .frame(maxWidth: .infinity, minHeight: filled ? 72 : 52)
            .background(filled ? IslandUI.lime : .white.opacity(0.12), in: Capsule())
        }.buttonStyle(.plain)
    }

    private func settings(_ lobby: MultiplayerLobby) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Picker("Game", selection: Binding(get: { lobby.sport }, set: { hub.setPartySport($0) })) {
                Text("Tennis").tag(MultiplayerSport.tennis); Text("Golf").tag(MultiplayerSport.golf); Text("Bowling").tag(MultiplayerSport.bowling)
            }.pickerStyle(.segmented).accessibilityIdentifier("hub-party-sport")
            HStack {
                Text(golf ? "Course" : bowling ? "Lanes" : "Court"); Spacer()
                Picker("Map", selection: Binding(get: { golf ? MultiplayerLobby.golfRoundParts(lobby.venue).course : lobby.venue }, set: { hub.configureParty(venue: $0) })) {
                    if golf {
                        ForEach(GolfCourseChoice.allCases, id: \.rawValue) { course in Text(course.title).tag(course.rawValue) }
                    } else if bowling {
                        ForEach(BowlingVenueChoice.allCases, id: \.rawValue) { venue in Text(venue.title).tag(venue.rawValue) }
                    } else {
                        Text("Resort").tag("resort"); Text("Skyscraper").tag("skyscraper"); Text("Volcano").tag("volcano")
                    }
                }.labelsHidden().accessibilityIdentifier("hub-party-map")
            }
            if bowling {
                Text("One lane, 10 frames, taking turns. Every phone shows the game: no TV needed.").font(.footnote).foregroundStyle(.white.opacity(0.7))
            } else if !golf {
                HStack {
                    Text("Sets"); Spacer()
                    Picker("Sets", selection: Binding(get: { lobby.sets }, set: { hub.configureParty(sets: $0) })) {
                        ForEach(1...3, id: \.self) { Text("\($0)").tag($0) }
                    }.labelsHidden().accessibilityIdentifier("hub-party-sets")
                }
                HStack {
                    Text("Games per set"); Spacer()
                    Picker("Games per set", selection: Binding(get: { lobby.games }, set: { hub.configureParty(games: $0) })) {
                        ForEach([1, 3, 6], id: \.self) { Text("\($0)").tag($0) }
                    }.labelsHidden().accessibilityIdentifier("hub-party-games")
                }
                Toggle("Sharing a TV", isOn: Binding(get: { lobby.sharedScreen == true }, set: { try? hub.partyService.setSharedScreen($0) }))
                    .tint(IslandUI.lime).accessibilityIdentifier("party-shared-tv")
                Text(lobby.sharedScreen == true ? "You're in the same room, watching one TV." : "Playing apart? Each player connects their own TV.")
                    .font(.footnote).foregroundStyle(.white.opacity(0.7))
                if lobby.participants.filter({ !$0.isGuest }).count > 2 {
                    Text("Tennis is one on one: the first two play, the others watch.").font(.footnote).foregroundStyle(.white.opacity(0.7))
                }
            }
        }.tint(IslandUI.lime).frame(maxWidth: .infinity).padding(14).background(.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 14))
    }

    private var headline: String {
        guard let lobby = party else { return "Waiting for your friend…" }
        if !checking { return leader ? "Pick a game, then Start" : "\(hub.menuLeaderName) is picking a game" }
        if !leader, (mine?.seat ?? -1) < 0 { return "You're watching this one" }
        if !leader, mine?.ready != true { return "\(hub.menuLeaderName) started \(golf ? "golf" : bowling ? "bowling" : "tennis")! Tap Ready" }
        let waiting = lobby.participants.filter { $0.seat >= 0 && !$0.isGuest && !$0.ready }.map(\.name)
        return waiting.isEmpty ? "Everyone's ready · starting…" : "Waiting for " + waiting.joined(separator: ", ")
    }
    private func status(_ p: MultiplayerParticipant) -> String {
        if !p.connected { return "Reconnecting…" }
        guard checking else { return p.id == party?.ownerID ? "Choosing" : "In the party" }
        if p.seat < 0 { return "Watching" }
        return p.ready ? "Ready" : "Not ready"
    }
}

/// Sitting on an online bench with no party: Game Center finds other players of that sport (no screen of its own); the match
/// starts by itself once it has. Invite friends instead from Friends, then sit here together.
struct HubOnlineBenchPanel: View {
    let hub: HubSession
    var body: some View {
        let sport = hub.onlineBench == .golf ? "Golf" : hub.onlineBench == .bowling ? "Bowling" : "Tennis"
        let found = hub.partyService.lobby != nil && !hub.partyService.isParty
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("\(sport.uppercased()) · ONLINE").font(IslandUI.font(13, bold: true)).tracking(1.4).foregroundStyle(IslandUI.lime)
                Spacer()
                Button { hub.leaveStation() } label: { Text("Leave seat").font(IslandUI.font(15, bold: true)).foregroundStyle(.white).padding(.horizontal, 14).padding(.vertical, 8).background(.white.opacity(0.12), in: Capsule()) }
                    .buttonStyle(.plain).accessibilityIdentifier("hub-online-leave")
            }
            Text(found ? "Found a player · starting…" : hub.searching ? "Finding a \(sport.lowercased()) player…" : "Play \(sport.lowercased()) online")
                .font(IslandUI.font(26, bold: true)).accessibilityIdentifier("hub-online-status")
            if hub.searching && !found { ProgressView().tint(IslandUI.lime).scaleEffect(1.4).frame(maxWidth: .infinity) }
            if !hub.notice.isEmpty { Text(hub.notice).font(IslandUI.font(14, bold: true)).foregroundStyle(IslandUI.lime) }
            Spacer(minLength: 0)
            if !hub.searching && !found {
                Button { hub.findPlayers() } label: {
                    Text("Find a player").font(IslandUI.font(20, bold: true)).foregroundStyle(IslandUI.navy).frame(maxWidth: .infinity, minHeight: 58).background(IslandUI.lime, in: Capsule())
                }.buttonStyle(.plain).accessibilityIdentifier("hub-online-find")
            }
            Button { hub.inviteFriends() } label: {
                Label("Play with friends instead", systemImage: "person.2.fill").font(IslandUI.font(16, bold: true)).frame(maxWidth: .infinity, minHeight: 48).background(.white.opacity(0.12), in: Capsule())
            }.buttonStyle(.plain).accessibilityIdentifier("hub-online-friends")
        }
        .foregroundStyle(.white).padding(22)
        .background(IslandBrandBackground().ignoresSafeArea())
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("hub-online-bench")
    }
}

/// "Tennis with a friend nearby" (a menu entry, HubSession.useNearbyBench): this phone hosts a tennis game for a friend's phone in the
/// same room (one TV, or one each). Their phone offers "Join <you>'s tennis game?" by itself; the match starts as soon as they tap it.
/// No shared Wi-Fi network is needed. SportsHome shows it over whatever menu is up.
struct HubNearbyBenchPanel: View {
    let hub: HubSession
    var body: some View {
        let service = hub.partyService
        let friend = service.lobby?.participants.first { $0.id != service.localID && !$0.isGuest }
        let me = service.lobby?.participants.first { $0.id == service.localID }?.name ?? "you"
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("TENNIS · NEARBY").font(IslandUI.font(13, bold: true)).tracking(1.4).foregroundStyle(IslandUI.lime)
                Spacer()
                Button { hub.leaveStation() } label: { Text("Cancel").font(IslandUI.font(15, bold: true)).foregroundStyle(.white).padding(.horizontal, 14).padding(.vertical, 8).background(.white.opacity(0.12), in: Capsule()) }
                    .buttonStyle(.plain).accessibilityIdentifier("hub-nearby-leave")
            }
            Text(friend.map { "\($0.name) joined · starting…" } ?? (hub.nearbyHosting ? "Waiting for a friend nearby…" : "Two phones, one TV"))
                .font(IslandUI.font(26, bold: true)).accessibilityIdentifier("hub-nearby-status")
            if friend == nil && hub.nearbyHosting {
                ProgressView().tint(IslandUI.lime).scaleEffect(1.4).frame(maxWidth: .infinity)
                Text("Your friend opens the app on their phone: \u{201C}Join \(me)'s tennis game?\u{201D} pops up. One tap and you play.")
                    .font(IslandUI.font(16)).foregroundStyle(.white.opacity(0.85)).fixedSize(horizontal: false, vertical: true)
                Text("No shared Wi-Fi needed: keep the phones close, with Wi-Fi turned on.").font(.footnote).foregroundStyle(.white.opacity(0.6))
                if let code = service.localJoinCode {
                    Text("Code \(code)").font(IslandUI.font(15, bold: true)).foregroundStyle(.white.opacity(0.7)).accessibilityIdentifier("hub-nearby-code")
                }
            }
            if service.localNetworkDenied {
                Text(MultiplayerError.localNetworkDenied.localizedDescription).font(.subheadline).fixedSize(horizontal: false, vertical: true)
                Button("Open Settings") { if let url = URL(string: UIApplication.openSettingsURLString) { UIApplication.shared.open(url) } }
                    .tint(IslandUI.lime).accessibilityIdentifier("hub-nearby-settings")
            }
            if !hub.notice.isEmpty { Text(hub.notice).font(IslandUI.font(14, bold: true)).foregroundStyle(IslandUI.lime) }
            Spacer(minLength: 0)
            if !hub.nearbyHosting {
                Button { hub.useNearbyBench() } label: {
                    Text("Host a game").font(IslandUI.font(20, bold: true)).foregroundStyle(IslandUI.navy).frame(maxWidth: .infinity, minHeight: 58).background(IslandUI.lime, in: Capsule())
                }.buttonStyle(.plain).accessibilityIdentifier("hub-nearby-host")
            }
        }
        .foregroundStyle(.white).padding(22)
        .background(IslandBrandBackground().ignoresSafeArea())
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("hub-nearby-bench")
    }
}

/// "Join Adnan's tennis game?": a friend's phone in the same room is hosting (it sat on the Nearby bench). One tap joins and the match
/// starts; ✕ hides that game. While joining it says so, with Cancel.
struct HubNearbyBanner: View {
    let hub: HubSession
    var body: some View {
        if let joining = hub.nearbyJoining {
            row {
                ProgressView().tint(IslandUI.lime)
                Text("Joining \(joining.name)'s game…").font(IslandUI.font(16, bold: true)).lineLimit(1).minimumScaleFactor(0.7)
                Spacer(minLength: 4)
                Button("Cancel") { hub.cancelNearbyJoin() }.font(IslandUI.font(15, bold: true)).tint(.white).accessibilityIdentifier("hub-nearby-cancel")
            }
        } else if let offer = hub.nearbyOffer {
            row {
                Image(systemName: "tennis.racket").font(.system(size: 20, weight: .bold)).foregroundStyle(IslandUI.lime)
                Text("Join \(offer.name)'s tennis game?").font(IslandUI.font(17, bold: true)).lineLimit(2).minimumScaleFactor(0.7)
                    .accessibilityIdentifier("hub-nearby-offer")
                Spacer(minLength: 4)
                Button { hub.joinNearby() } label: {
                    Text("Join").font(IslandUI.font(17, bold: true)).foregroundStyle(IslandUI.navy).padding(.horizontal, 18).frame(minHeight: 44).background(IslandUI.lime, in: Capsule())
                }.buttonStyle(.plain).accessibilityIdentifier("hub-nearby-join")
                Button { hub.dismissNearby() } label: { Image(systemName: "xmark").font(.system(size: 15, weight: .bold)).frame(width: 36, height: 44) }
                    .buttonStyle(.plain).accessibilityLabel("Not now").accessibilityIdentifier("hub-nearby-dismiss")
            }
        }
    }
    private func row<Content: View>(@ViewBuilder _ content: () -> Content) -> some View {
        HStack(spacing: 10) { content() }
            .foregroundStyle(.white).padding(.leading, 14).padding(.trailing, 6).padding(.vertical, 6)
            .background(IslandUI.dark.opacity(0.96), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(IslandUI.lime.opacity(0.7), lineWidth: 2))
            .shadow(color: .black.opacity(0.35), radius: 10, y: 4)
            .accessibilityElement(children: .contain).accessibilityIdentifier("hub-nearby-banner")
    }
}

/// An online match is over (or stopped): the result is on the TV; one button takes this phone (and a party, together) back to the
/// Plaza, on the same bench.
struct HubMatchOverPanel: View {
    let hub: HubSession
    var body: some View {
        VStack(spacing: 20) {
            Spacer()
            Text("MATCH OVER").font(IslandUI.font(14, bold: true)).tracking(2).foregroundStyle(IslandUI.lime)
            Text(hub.matchOver ?? "").font(IslandUI.font(36, bold: true)).multilineTextAlignment(.center).accessibilityIdentifier("hub-match-over-line")
            Text(hub.partyService.isParty ? "Everyone goes back to the party together. The leader picks the next game." : "Back to the menu.")
                .font(IslandUI.font(15)).foregroundStyle(.white.opacity(0.7)).multilineTextAlignment(.center)
            Spacer()
            Button { hub.leaveOnlineMatch() } label: {
                Text("Back to the Plaza").font(IslandUI.font(22, bold: true)).foregroundStyle(IslandUI.navy).frame(maxWidth: .infinity, minHeight: 62).background(IslandUI.lime, in: Capsule())
            }.buttonStyle(.plain).accessibilityIdentifier("hub-match-over-back")
            if hub.inParty {
                Button { hub.leaveParty() } label: {
                    Text("Leave party").font(IslandUI.font(17, bold: true)).foregroundStyle(.white.opacity(0.8)).frame(maxWidth: .infinity, minHeight: 48)
                }.buttonStyle(.plain).accessibilityIdentifier("hub-match-over-leave-party")
            }
        }
        .foregroundStyle(.white).padding(24)
        .background(IslandBrandBackground().ignoresSafeArea())
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("hub-match-over")
    }
}

/// The Plaza could not open: say why and try again (the phone stays the controller; the TV says the same).
struct HubFailedPanel: View {
    let hub: HubSession
    var body: some View {
        VStack(spacing: 18) {
            Spacer()
            Image(systemName: "exclamationmark.triangle.fill").font(.system(size: 44)).foregroundStyle(IslandUI.lime)
            Text("The Plaza didn't open").font(IslandUI.font(26, bold: true))
            Text(hub.notice).font(IslandUI.font(15)).foregroundStyle(.white.opacity(0.7)).multilineTextAlignment(.center)
            Spacer()
            Button { hub.retry() } label: {
                Text("Try again").font(IslandUI.font(22, bold: true)).foregroundStyle(IslandUI.navy).frame(maxWidth: .infinity, minHeight: 62).background(IslandUI.lime, in: Capsule())
            }.buttonStyle(.plain).accessibilityIdentifier("hub-retry")
        }
        .foregroundStyle(.white).padding(24)
        .background(IslandBrandBackground().ignoresSafeArea())
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("hub-failed")
    }
}
