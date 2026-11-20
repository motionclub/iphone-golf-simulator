import SwiftUI

// The menu's shared phone and TV pieces: the boot loading screen (HubLoadingScreen, LoadingShots) and the panels MenuControllerView and
// SportsHome show over the menu (a station's screen, the party's game, the online and nearby benches, match over, failed).
// (The walk-around Plaza's controller, HubControllerView with its stick, A / B and ☰ menu, was removed 2026-11-15.)

/// The TV while the game starts and the Plaza boots: the wordmark over a full-screen moment of play, the sport and venue under it,
/// and LOADING… with the bar. LOADING ACTION (Adnan 2026-11-13: "full screen action ... cycle completely random shots, not just the
/// same few"; the "Swing your phone. Play on your TV." line removed): a new shot every 3 s from LoadingShots, shuffled each boot. The
/// bar is HubSession.pace (steady, on Core Animation, so the cold Unity start cannot freeze it); at 100 % it holds a moment and fades
/// into the arrival fly-in. Drawn on the 1280×720 TV canvas (the phone with no TV shows it scaled to its screen, MenuTouchPad).
struct HubLoadingScreen: View {
    let hub: HubSession
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var reel = LoadingShots.Reel()
    var body: some View {
        let failed = hub.phase == .failed
        let shot = reel.current
        ZStack(alignment: .topLeading) {
            MSBrand.backdrop(spotlight: UnitPoint(x: 0.3, y: 0.47), radius: 820)
            ZStack { LoadingShotImage(shot: shot, settle: !reduceMotion).id(reel.step).transition(.opacity) }
                .frame(width: 1280, height: 720).clipped()
            // a navy shade from the left and the bottom: the wordmark and the bar read on any picture
            LinearGradient(stops: [.init(color: LoadingShots.ink.opacity(0.92), location: 0), .init(color: LoadingShots.ink.opacity(0.62), location: 0.34),
                                   .init(color: LoadingShots.ink.opacity(0), location: 0.62)], startPoint: .leading, endPoint: .trailing)
            LinearGradient(stops: [.init(color: LoadingShots.ink.opacity(0.9), location: 0), .init(color: LoadingShots.ink.opacity(0), location: 0.38)],
                           startPoint: .bottom, endPoint: .top)
            VStack(alignment: .leading, spacing: 34) {
                MSWordmark(size: 96)
                Text(shot.label).font(MSLoadingFont.display(24)).tracking(3).foregroundStyle(MSBrand.goldWordmark)
                    .shadow(color: MSBrand.textShadow.opacity(0.8), radius: 4, y: 1).padding(.leading, 8)
                    .id(reel.step).transition(.opacity)
                    .accessibilityIdentifier("hub-loading-shot")
            }
            .frame(width: 520, alignment: .leading)
            .position(x: 128 + 255, y: 318)
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
        .task {
            // a new shot every 3 s (Reduce Motion: the one random still)
            reel.remember()
            guard !reduceMotion, LoadingShots.pinned == nil else { return }
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(LoadingShots.seconds))
                if Task.isCancelled { break }
                withAnimation(.easeInOut(duration: 0.7)) { reel.advance() }
            }
        }
    }
}

/// The boot screen's pictures: only the 25 painted UI-overhaul loading pictures (GolfArcade/Unity/MapSkins/load-*.jpg); the 11-13 trailer
/// and in-game frames (Assets.xcassets/LoadingShots) were removed on 2026-11-16. `anchor` is which part of a picture wider than 16:9 shows
/// (0 its left edge, 1 its right).
struct LoadingShot: Equatable { let asset: String; let label: String; let anchor: CGFloat }
enum LoadingShots {
    static let seconds = 3.0
    static let ink = Color(hex: "06123F")
    /// UI OVERHAUL 11-15 (02 Loading art): the 25 painted loading pictures of our players on our maps replace the trailer frames.
    /// Map names stand alone (no sport labels); the boxing and baseball pictures have no map of ours, so they carry no label.
    static let pool: [LoadingShot] = [
        ("golf-cliffside-male", "CLIFFSIDE"), ("golf-cliffside-female", "CLIFFSIDE"), ("golf-magma-male", "MAGMA OPEN"),
        ("golf-magma-female", "MAGMA OPEN"), ("golf-wildisles-male", "WILD ISLES"),
        ("tennis-rooftop-serve", "SKY TOWER"), ("tennis-rooftop-stretch", "SKY TOWER"), ("tennis-resort-forehand", "TROPICAL RESORT"),
        ("tennis-resort-volley", "TROPICAL RESORT"), ("tennis-volcano-backhand", "MAGMA CRATER"),
        ("bowling-neon-release", "NEON NIGHTS"), ("bowling-neon-strike", "NEON NIGHTS"), ("bowling-tiki-approach", "TIKI SHORES"),
        ("bowling-magma-spare", "MAGMA LANES"), ("bowling-club-set", "CLUB LANES"),
        ("boxing-beachside-exchange", ""), ("boxing-ringside-slip", ""), ("boxing-corner-reset", ""), ("boxing-center-footwork", ""),
        ("boxing-final-bell", ""), ("baseball-infield-grounder", ""), ("baseball-plate-catch", ""), ("baseball-seaside-pitch", ""),
        ("baseball-warning-track", ""), ("baseball-first-base-lead", ""),
    ].map { LoadingShot(asset: "load-\($0.0).jpg", label: $0.1, anchor: 0.5) }
    /// Snapshots: show this shot and hold it.
    nonisolated(unsafe) static var pinned: Int?
    static let lastKey = "loading.lastShot"

    /// Every shot once in a random order, then a fresh shuffle; never the same shot twice in a row, and a boot never opens on the
    /// shot the last one ended on.
    struct Reel {
        private(set) var order: [Int]
        private(set) var at = 0
        /// Counts every change (the views key their fade on it).
        private(set) var step = 0
        init(last: Int? = UserDefaults.standard.object(forKey: LoadingShots.lastKey) as? Int, count: Int = LoadingShots.pool.count) {
            order = Reel.shuffle(count, avoiding: last)
            if let p = LoadingShots.pinned, p < count { order = [p] }
        }
        /// The shot on screen, so the next boot does not open on it (SwiftUI re-runs a @State's initial value, so not in init).
        func remember() { UserDefaults.standard.set(index, forKey: LoadingShots.lastKey) }
        var index: Int { order[at] }
        var current: LoadingShot { LoadingShots.pool[min(index, LoadingShots.pool.count - 1)] }
        mutating func advance() {
            if at + 1 < order.count { at += 1 } else { order = Reel.shuffle(order.count, avoiding: order[at]); at = 0 }
            step += 1
            remember()
        }
        static func shuffle(_ count: Int, avoiding last: Int?) -> [Int] {
            var o = Array(0..<count).shuffled()
            if o.count > 1, let last, o[0] == last { o.swapAt(0, 1) }
            return o
        }
    }
}

/// One loading shot filling the 1280×720 canvas, its `anchor` choosing the part shown, with a slow push-in while it is up.
struct LoadingShotImage: View {
    let shot: LoadingShot
    var settle = true
    @State private var settled = false
    var body: some View {
        let image = UIImage(named: shot.asset)
        let size = CGSize(width: 1280, height: 720)
        let aspect = image.map { $0.size.width / max(1, $0.size.height) } ?? size.width / size.height
        let w = max(size.width, size.height * aspect), h = max(size.height, size.width / aspect)
        ZStack(alignment: .topLeading) {
            if let image {
                Image(uiImage: image).resizable().frame(width: w, height: h)
                    .offset(x: -(w - size.width) * shot.anchor, y: -(h - size.height) / 2)
            }
        }
        .frame(width: size.width, height: size.height, alignment: .topLeading)
        .scaleEffect(settle && !settled ? 1.06 : 1)
        .clipped()
        .accessibilityLabel(shot.label.capitalized)
        .onAppear { if settle { withAnimation(.linear(duration: LoadingShots.seconds + 0.4)) { settled = true } } }
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
                Text("\(hub.onPhone ? "PLAZA" : "ON THE TV") · THE PLAZA").font(IslandUI.font(12, bold: true)).tracking(1.4)
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
            } else if golf {
                Text("\(MultiplayerService.onlineGolfHoles) holes. A tie for the lowest card: one random ball drop, one hit each, closest to the hole wins.").font(.footnote).foregroundStyle(.white.opacity(0.7))
            } else if !golf {
                HStack {
                    Text("Sets"); Spacer()
                    if hub.partyService.playsOnlineRules { Text("1 (online)").foregroundStyle(.white.opacity(0.7)).accessibilityIdentifier("hub-party-sets") }
                    else {
                        Picker("Sets", selection: Binding(get: { lobby.sets }, set: { hub.configureParty(sets: $0) })) {
                            ForEach(1...3, id: \.self) { Text("\($0)").tag($0) }
                        }.labelsHidden().accessibilityIdentifier("hub-party-sets")
                    }
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
