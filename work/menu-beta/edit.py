from pathlib import Path
root=Path.cwd()
def edit(name, old, new):
 p=root/name;s=p.read_text();assert old in s,(name,old[:80]);p.write_text(s.replace(old,new))
m='GolfArcade/Unity/TennisMenu.swift'
edit(m,'case title, main, party, quickPlay, gameSelect, hub(Sport), locked(Sport)','case title, main, party, multiplayer, onlineChoice, homeEmotes, quickPlay, gameSelect, hub(Sport), locked(Sport)')
edit(m,'    var online = OnlineLobbyMenu()','''    var online = OnlineLobbyMenu()
    private(set) var homeEmote: String?
    private(set) var homeEmoteSequence = 0
    var homeSport: Sport { session.lastPlayedSport }
    var previewSport: Sport {
        Sport(rawValue: focused.replacingOccurrences(of: "sport-", with: "")) ?? homeSport
    }''')
edit(m,'case .main: return [["homeContinue"], ["play"], ["character"], ["settings"]]\n        case .party: return [["partySolo"], ["partyOnline"], ["partyNearby"], ["back"]]','''case .main: return [["play", "homeInvite"], ["character"], ["homeEmotes"], ["settings"], ["betaFeedback"]]
        case .party: return [["partySolo"], ["partyMultiplayer"], ["back"]]
        case .multiplayer: return [["partyOnline"], ["partyNearby"], ["back"]]
        case .onlineChoice: return [["onlineQuick"], ["homeInvite"], ["back"]]
        case .homeEmotes: return (player?.equippedEmotes ?? EmoteCatalog.ids).map { ["home-emote-\\($0)"] } + [["back"]]''')
edit(m,'case "quickPlay", "partySolo": show(.quickPlay)','''case "quickPlay", "partySolo": show(.gameSelect)
        case "partyMultiplayer": show(.multiplayer)
        case "partyOnline": show(.onlineChoice)
        case "onlineQuick": online.select("partyOnline", menu: self)
        case "homeInvite": online.select("net-invite", menu: self)
        case "homeEmotes": show(.homeEmotes)
        case let emote where emote.hasPrefix("home-emote-"):
            homeEmote = String(emote.dropFirst(11)); homeEmoteSequence += 1
        case "betaFeedback": BetaFeedback.open()''')
edit(m,'if screen.isOnline || id == "partyOnline" || id == "partyNearby" {','if screen.isOnline || id == "partyNearby" {')
edit(m,'case "play": show(.gameSelect)','case "play": show(.party)')
edit(m,'case .party, .quickPlay, .gameSelect, .settings: show(.main)','''case .party, .settings, .homeEmotes: show(.main)
        case .multiplayer, .quickPlay, .gameSelect: show(.party)
        case .onlineChoice: show(.multiplayer)''')
edit(m,'case .entry,.nearby: cancel(); service.stopBrowsing(); menu.openOnlineParty()','case .entry,.nearby: cancel(); service.stopBrowsing(); menu.returnFromNetworkEntry(route)')
edit(m,'    func identity(_ menu: TennisMenu) {','    func identity(_ menu: TennisMenu) {')
# Public route helper, no test-only routing used in production.
edit(m,'    var loadingOpponent: TennisOpponent? {','''    func returnFromNetworkEntry(_ route: OnlineLobbyScreen) {
        show(route == .entry ? .onlineChoice : .multiplayer)
    }

    var loadingOpponent: TennisOpponent? {''')
# Persist only actual successful launches; scoped to the selected player.
s='GolfArcade/Unity/SportsSession.swift'
edit(s,'    var sport = "golf"','''    var sport = "golf"
    var lastPlayedSport: Sport {
        guard players.indices.contains(playerIndex) else { return .tennis }
        return Sport(rawValue: UserDefaults.standard.string(forKey: "sports.lastSport.\\(players[playerIndex].id.uuidString)") ?? "tennis") ?? .tennis
    }''')
edit(s,'        let p=players[min(playerIndex,players.count-1)]','''        let p=players[min(playerIndex,players.count-1)]
        UserDefaults.standard.set(sport, forKey: "sports.lastSport.\\(p.id.uuidString)")''')
# Disable automatic menu movements, while allowing explicit emotes.
c='GolfArcade/Unity/CharacterModelPreview.swift'
edit(c,'    var menuActivity: ClubPreviewActivity? = nil','''    var menuActivity: ClubPreviewActivity? = nil
    var emote: String? = nil
    var emoteSequence = 0''')
edit(c,'            context.coordinator.configureClub(menuActivity, animate: !reduceMotion && !SportsSession.shared.reduceMotion)\n            view.isPlaying = !reduceMotion && !SportsSession.shared.reduceMotion','''            context.coordinator.configureClub(menuActivity, animate: false)
            context.coordinator.playEmote(emote, sequence: emoteSequence)
            view.isPlaying = context.coordinator.motion != nil''')
edit(c,'let animate = idleSport != nil && !reduceMotion && !SportsSession.shared.reduceMotion','let animate = false')
start=(root/c).read_text().index('            guard let equipped = previous else { return }', (root/c).read_text().index('func configureClub'))
end=(root/c).read_text().index('\n        private var idleKey:',start)
p=root/c;txt=p.read_text();txt=txt[:start]+'''            clubKey = key
            racket?.isHidden = outfitSport == .golf || framing == .head
            applyFraming()
        }
        private var lastEmoteSequence = 0
        func playEmote(_ id: String?, sequence: Int) {
            guard sequence != lastEmoteSequence, let id, EmoteCatalog.ids.contains(id) else { return }
            lastEmoteSequence = sequence
            // Golf exports share the emotes that are supported by that character's rig.
            play(MenuMotion(kind: .clipOnce(id), lead: 0, fadeIn: 0.15, fadeOut: 0.25, freezeIdle: true))
        }
''' + txt[end:];p.write_text(txt)
# Stop emote's display link once it has returned to the held stance.
edit(c,'            rig.apply(motion, at: time)\n            if let zoom', '''            rig.apply(motion, at: time)
            if motion.freezeIdle, time >= motion.settledAfter(rig.data) { stopLink() }
            if let zoom''')
edit(c,'                        if state.animate && state.introduce { motion.play("wave",at:now+joinDelay,now:now) }','                        // Lobby arrivals hold their sport stance until the player chooses an emote.')
mm='GolfArcade/Unity/MatchHeroMotion.swift'
edit(mm,'    var idleOffset = 0.0','    var idleOffset = 0.0\n    var freezeIdle = false')
edit(mm,'let base = ready.pose(at: t + idleOffset, loop: true)','let base = ready.pose(at: freezeIdle ? 0 : t + idleOffset, loop: true)')
edit(mm,'        motion.idleOffset = idleOffset + (clip == nil ? 0 : startedAt)','        motion.idleOffset = idleOffset + (clip == nil ? 0 : startedAt)\n        motion.freezeIdle = true')
# Main menu and emote controls share the equipped sport/character.
f='GolfArcade/Unity/MotionClubMenus.swift'
edit(f,'private let items = [("homeContinue", "Continue", "play.circle.fill"), ("play", "Play", "play.fill"), ("character", "Locker", "tshirt"), ("settings", "Settings", "gearshape")]','private let items = [("play", "Play", "play.fill"), ("character", "Locker", "tshirt"), ("homeEmotes", "Emotes", "face.smiling"), ("settings", "Settings", "gearshape")]')
edit(f,'cameraDistance: compact ? 3.4 : 3.25, menuActivity: activity','cameraDistance: compact ? 3.4 : 3.25, outfitSport: menu.homeSport, menuActivity: .play')
edit(f,'                IslandWordmark(size: compact ? 29 : 46)','''                Button { menu.tap("homeInvite") } label: {
                    Image(systemName: "plus").font(.system(size: compact ? 24 : 32, weight: .bold))
                        .foregroundStyle(IslandUI.navy).frame(width: 54, height: 54)
                        .islandFocus(menu.isFocused("homeInvite"), radius: 27, base: IslandUI.paper)
                }.buttonStyle(.plain).accessibilityLabel("Invite friends to your lobby").accessibilityIdentifier("home-invite")
                    .position(x: w * (compact ? 0.86 : 0.92), y: h * (compact ? 0.31 : 0.53))
                IslandWordmark(size: compact ? 29 : 46)''')
# Home feedback focus id targets an always-visible button in root chrome.
# Menu routing UI.
f='GolfArcade/Unity/IslandScreens.swift';txt=(root/f).read_text();start=txt.index('struct IslandPartyScreen: View {');end=txt.index('\nstruct IslandOnlineScreen:',start)
txt=txt[:start]+'''struct IslandPartyScreen: View {
    let menu: TennisMenu
    let compact: Bool
    private var title: String {
        switch menu.screen { case .multiplayer: "Multiplayer"; case .onlineChoice: "Online"; default: "Play" }
    }
    var body: some View {
        IslandShell(title: title, compact: compact) {
            VStack(alignment: .leading, spacing: compact ? 16 : 24) {
                switch menu.screen {
                case .multiplayer:
                    IslandLobbyRow(title: "Online", subtitle: "Quick match or play with friends", icon: "globe", id: "partyOnline", menu: menu, compact: compact)
                    IslandLobbyRow(title: "Local", subtitle: "Host or join on the same Wi-Fi", icon: "wifi", id: "partyNearby", menu: menu, compact: compact)
                case .onlineChoice:
                    IslandLobbyRow(title: "Quick Match", subtitle: "Find players for golf or tennis", icon: "bolt.fill", id: "onlineQuick", menu: menu, compact: compact)
                    IslandLobbyRow(title: "Play with Friends", subtitle: "Invite friends to your lobby", icon: "person.badge.plus", id: "homeInvite", menu: menu, compact: compact)
                default:
                    IslandLobbyRow(title: "Single Player", subtitle: "Choose golf or tennis", icon: "person.fill", id: "partySolo", menu: menu, compact: compact)
                    IslandLobbyRow(title: "Multiplayer", subtitle: "Play online or locally", icon: "person.2.fill", id: "partyMultiplayer", menu: menu, compact: compact)
                }
                IslandLobbyRow(title: "Back", icon: "arrow.left", id: "back", menu: menu, compact: compact)
                if !menu.notice.isEmpty { IslandMenuNotice(menu: menu, compact: compact) }
                Spacer(minLength: 0)
            }.frame(maxWidth: 700)
        }
    }
}

struct HomeEmoteScreen: View {
    let menu: TennisMenu
    let compact: Bool
    var body: some View {
        IslandShell(title: "Emotes", compact: compact) {
            VStack(spacing: 12) {
                CharacterModelPreview(player: menu.player ?? Player(name: "Player 1", colorIndex: 0), cameraDistance: 3.4,
                    outfitSport: menu.homeSport, menuActivity: .play, emote: menu.homeEmote, emoteSequence: menu.homeEmoteSequence)
                    .frame(maxHeight: .infinity)
                ForEach(menu.player?.equippedEmotes ?? EmoteCatalog.ids, id: \\.self) { id in
                    IslandLobbyRow(title: EmoteCatalog.name(id), icon: "face.smiling", id: "home-emote-\\(id)", menu: menu, compact: compact)
                }
                IslandLobbyRow(title: "Back", icon: "arrow.left", id: "back", menu: menu, compact: compact)
            }
        }
    }
}
''' +txt[end:];(root/f).write_text(txt)
edit(f,'action("net-invite","Invite Friends",icon:"person.badge.plus")','action("net-invite","Play with Friends",icon:"person.badge.plus")')
edit(f,'Text("Your hero is warming up while we find a match.")','Text("Finding an available match…")')
v='GolfArcade/Unity/TennisMenuViews.swift'
edit(v,'ClubCameraHost(route: menu.screen, reducedMotion: reduceMotion || SportsSession.shared.reduceMotion','ClubCameraHost(route: menu.screen, reducedMotion: true')
edit(v,'case .party: IslandPartyScreen(menu: menu, compact: compact)','''case .party, .multiplayer, .onlineChoice: IslandPartyScreen(menu: menu, compact: compact)
            case .homeEmotes: HomeEmoteScreen(menu: menu, compact: compact)''')
# Present Game Center from any route (including + on Home), so errors/auth UI cannot disappear.
edit(v,'            .safeAreaInset(edge: .top) {','''            .sheet(item: Binding(get: { menu.online.sheet }, set: { menu.online.sheet = $0 })) { sheet in
                OnlineGameCenterSheet(controller: sheet.controller).ignoresSafeArea()
            }
            .safeAreaInset(edge: .top) {''')
edit(f,'        .sheet(item:Binding(get:{online.sheet},set:{online.sheet=$0})) { sheet in OnlineGameCenterSheet(controller:sheet.controller).ignoresSafeArea() }','')
# Controller-friendly labels.
a='GolfArcade/Unity/ArcadeScreens.swift'
edit(a,'case "quickPlay", "partySolo": return "Quick Play"','''case "quickPlay", "partySolo": return "Single Player"
        case "partyMultiplayer": return "Multiplayer"
        case "partyOnline": return "Online"
        case "partyNearby": return "Local"
        case "onlineQuick": return "Quick Match"
        case "homeInvite": return "Play with Friends"
        case "homeEmotes": return "Emotes"
        case "betaFeedback": return "Beta Feedback"''')
# branding, feedback is a user-initiated SMS compose action; never sends automatically.
edit('GolfArcade/Unity/ClubDesign.swift','Text("CLUB").font','Text("CLUB · BETA").font')
edit('GolfArcade/Unity/ClubDesign.swift','.accessibilityLabel("Motion Club")','.accessibilityLabel("Motion Club Beta")')
edit('GolfArcade/Unity/SportsInfo.plist','<string>Motion Club</string>','<string>Motion Club Beta</string>')
with (root/'GolfArcade/Unity/MotionClubMenus.swift').open('a') as o:o.write('''

@MainActor enum BetaFeedback {
    static let url = URL(string: "sms:+19085909023")!
    static func open() { UIApplication.shared.open(url) }
}

struct BetaFeedbackBar: View {
    @Environment(\\.openURL) private var openURL
    @State private var unavailable = false
    var body: some View {
        HStack {
            Text("MOTION CLUB · BETA").font(IslandUI.font(11, bold: true)).tracking(1)
            Spacer()
            Button {
                openURL(BetaFeedback.url) { accepted in unavailable = !accepted }
            } label: {
                Label("Feedback", systemImage: "message.fill").font(IslandUI.font(14, bold: true))
                    .padding(.vertical, 10)
            }.accessibilityLabel("Send beta feedback by text").accessibilityIdentifier("beta-feedback")
        }.foregroundStyle(IslandUI.navy).padding(.horizontal, 18).background(IslandUI.paper)
            .alert("Text beta feedback", isPresented: $unavailable) {
                Button("Copy number") { UIPasteboard.general.string = "908-590-9023" }
                Button("Close", role: .cancel) { }
            } message: { Text("Text 908-590-9023. Messages is not available on this device.") }
    }
}
''')
edit('GolfArcade/Unity/SportsHome.swift','        .simultaneousGesture(TapGesture().onEnded {','        .safeAreaInset(edge: .bottom, spacing: 0) { BetaFeedbackBar() }\n        .simultaneousGesture(TapGesture().onEnded {')
