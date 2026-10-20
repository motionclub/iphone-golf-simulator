from pathlib import Path
r=Path.cwd()
def edit(f,a,b):
 p=r/f;s=p.read_text();assert a in s,(f,a);p.write_text(s.replace(a,b))
edit('GolfArcade/Unity/TennisPlayViews.swift','case .party: "PLAY WITH FRIENDS"; case .quickPlay: "QUICK PLAY"','case .party: "PLAY"; case .multiplayer: "MULTIPLAYER"; case .onlineChoice: "ONLINE"; case .homeEmotes: "EMOTES"; case .quickPlay: "QUICK PLAY"')
edit('GolfArcade/Unity/MatchHeroData.swift','let base=ready.morphWeights(at:t+idleOffset,loop:true)','let base=ready.morphWeights(at:freezeIdle ? 0 : t+idleOffset,loop:true)')
edit('GolfArcade/Unity/TennisMenu.swift','    var homeSport: Sport { session.lastPlayedSport }','''    var homeSport: Sport { session.lastPlayedSport }
    var homeEmotes: [String] { homeSport == .golf ? ["wave", "cheer", "hitPerfect"] : player?.equippedEmotes ?? EmoteCatalog.defaults }
    static func homeEmoteName(_ id: String) -> String {
        switch id { case "cheer": "Cheer"; case "hitPerfect": "Fist Pump"; default: EmoteCatalog.name(id) }
    }''')
edit('GolfArcade/Unity/TennisMenu.swift','(player?.equippedEmotes ?? EmoteCatalog.ids).map','homeEmotes.map')
edit('GolfArcade/Unity/IslandScreens.swift','ForEach(menu.player?.equippedEmotes ?? EmoteCatalog.ids, id: \\.self)','ForEach(menu.homeEmotes, id: \\.self)')
edit('GolfArcade/Unity/IslandScreens.swift','title: EmoteCatalog.name(id), icon: "face.smiling"','title: TennisMenu.homeEmoteName(id), icon: "face.smiling"')
edit('GolfArcade/Unity/CharacterModelPreview.swift','let id, EmoteCatalog.ids.contains(id)','let id, (EmoteCatalog.ids + ["cheer", "hitPerfect"]).contains(id)')
edit('GolfArcade/Unity/ArcadeScreens.swift','        if id.hasPrefix("sport-")','        if id.hasPrefix("home-emote-") { return TennisMenu.homeEmoteName(String(id.dropFirst(11))) }\n        if id.hasPrefix("sport-")')
# Authenticate and then resume the exact Invite action. Game Center UI is handled at menu root.
edit('GolfArcade/Unity/TennisMenu.swift','''                sheet = OnlineAppleSheet(controller:try service.inviteFriends()); menu.showOnline(.lobby)''','''                run(menu) { [self] in
                    if !service.authenticated { try await service.authenticate { [weak self] vc in self?.sheet = OnlineAppleSheet(controller: vc) } }
                    sheet = OnlineAppleSheet(controller: try service.inviteFriends())
                    menu.showOnline(.lobby)
                }''')
# Reuse the existing managed AVPlayerLooper with explicit activity/lifecycle.
edit('GolfArcade/Unity/HowToCards.swift','private struct LoopingPlayer: UIViewRepresentable {','struct LoopingPlayer: UIViewRepresentable {')
edit('GolfArcade/Unity/HowToCards.swift','    let url: URL\n    final class PlayerView','    let url: URL\n    var playing = true\n    final class PlayerView')
edit('GolfArcade/Unity/HowToCards.swift','        player.play()\n        return view','        if playing { player.play() }\n        return view')
edit('GolfArcade/Unity/HowToCards.swift','    func updateUIView(_ view: PlayerView, context: Context) {}','    func updateUIView(_ view: PlayerView, context: Context) { if playing { view.player?.play() } else { view.player?.pause() } }')
p=r/'GolfArcade/Unity/ClubScreens.swift';s=p.read_text();start=s.index('struct IslandSportsScreen: View {');end=s.index('\nstruct IslandTrainingScreen:',start)
s=s[:start]+'''/// Preview changes as soon as the controller or pointer focuses a sport.
struct IslandSportsScreen: View {
    let menu: TennisMenu
    let compact: Bool
    var body: some View {
        IslandShell(title: "Select a sport", compact: compact) {
            VStack(spacing: compact ? 14 : 24) {
                GameplayPreview(sport: menu.previewSport, venue: menu.previewSport == .golf ? "postcards" : "resort")
                    .aspectRatio(16 / 9, contentMode: .fit).clipShape(RoundedRectangle(cornerRadius: 20))
                    .accessibilityIdentifier("sport-preview-\\(menu.previewSport.rawValue)")
                HStack(spacing: 16) {
                    ForEach(Sport.allCases.filter(\\.playable), id: \\.self) { sport in
                        IslandAction(title: sport.title.capitalized, focused: menu.isFocused("sport-\\(sport.rawValue)"), primary: menu.isFocused("sport-\\(sport.rawValue)"), compact: compact, identifier: "select-\\(sport.rawValue)") { menu.tap("sport-\\(sport.rawValue)") }
                            .onHover { if $0 { menu.focus("sport-\\(sport.rawValue)") } }
                    }
                }
                Spacer(minLength: 0)
                IslandAction(title: "Back", focused: menu.isFocused("back"), compact: compact) { menu.tap("back") }.frame(width: 170)
            }
        }
    }
}

/// Bundled captures of actual play. Venue-specific stills remain visible if a clip is unavailable.
struct GameplayPreview: View {
    let sport: Sport
    let venue: String
    @Environment(\\.scenePhase) private var scenePhase
    @Environment(\\.accessibilityReduceMotion) private var reduceMotion
    private var art: String { sport == .golf ? "map-golf-\\(venue)" : "map-\\(venue)" }
    private var clip: String { "gameplay-\\(sport.rawValue)-\\(venue)" }
    var body: some View {
        GeometryReader { g in
            ZStack(alignment: .bottomLeading) {
                Color.black
                if let poster = UIImage(named: art + ".jpg") {
                    Image(uiImage: poster).resizable().scaledToFit().frame(width: g.size.width, height: g.size.height)
                }
                if let url = Bundle.main.url(forResource: clip, withExtension: "mp4") {
                    LoopingPlayer(url: url, playing: scenePhase == .active && !reduceMotion && !SportsSession.shared.reduceMotion).id(clip)
                }
                Text("\\(sport.title.capitalized) · Gameplay preview")
                    .font(IslandUI.font(13, bold: true)).foregroundStyle(.white).padding(10)
                    .background(.black.opacity(0.65), in: Capsule()).padding(12)
            }.clipped()
        }.accessibilityLabel("\\(sport.title.capitalized) gameplay preview")
    }
}
''' +s[end:];p.write_text(s)
# Loading: a clear 16:9 gameplay/map preview, no roster blocking the scene, no looping decorative zoom.
p=r/'GolfArcade/Unity/ArcadeScreens.swift';s=p.read_text();s=s.replace('    @State private var drift = false\n','');start=s.index('                if let image = UIImage(named: art + ".jpg")',s.index('struct LoadingScreen'));end=s.index('                VStack(spacing: compact ? 18 : 24)',start);s=s[:start]+s[end:];s=s.replace('                    roster\n                    Spacer(minLength: 0)','''                    GameplayPreview(sport: sport, venue: sport == .golf ? (service.lobby?.phase == .loading ? service.lobby?.venue ?? session.golfCourse : session.golfCourse) : (service.lobby?.venue ?? session.tennisVenue))
                        .aspectRatio(16 / 9, contentMode: .fit).clipShape(RoundedRectangle(cornerRadius: 18))
                    Spacer(minLength: 0)''');s=s.replace('        .onAppear { withAnimation(.easeInOut(duration: 5).repeatForever(autoreverses: true)) { drift = true } }\n','');p.write_text(s)
