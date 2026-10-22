from pathlib import Path
def edit(f,a,b):
 p=Path(f);s=p.read_text();assert a in s,(f,a[:80]);p.write_text(s.replace(a,b,1))
edit('GolfArcade/Unity/SportsSession.swift','    var presentationBigMoments =','    var holeFlyover = (UserDefaults.standard.object(forKey: "sports.holeFlyover") as? Bool) ?? true {\n        didSet { UserDefaults.standard.set(holeFlyover, forKey: "sports.holeFlyover") }\n    }\n    var presentationBigMoments =')
edit('GolfArcade/Unity/SportsSession.swift','pending=["intros":presentationIntros,','pending=["holeFlyover":holeFlyover,"intros":presentationIntros,')
edit('GolfArcade/Unity/TennisMenu.swift','["level", "presentationIntros", "presentationBigMoments",','["level", "presentationIntros", "holeFlyover", "presentationBigMoments",')
edit('GolfArcade/Unity/TennisMenu.swift','        case "presentationBigMoments": s.presentationBigMoments.toggle()','        case "holeFlyover": s.holeFlyover.toggle()\n        case "presentationBigMoments": s.presentationBigMoments.toggle()')
edit('GolfArcade/Unity/IslandScreens.swift','        case "presentationBigMoments": return Item','        case "holeFlyover": return Item(title: "Hole flyovers", detail: "Show the course before each hole. Overview stays available at address.", control: .toggle(s.holeFlyover))\n        case "presentationBigMoments": return Item')
edit('GolfArcade/Unity/SportsDisplays.swift','    func beginLoadingCover(in destination:', '''    private var exitCover: UIWindow?
    private var exitGeneration = 0
    func beginExitCover() {
        guard let destination = external ?? preview ?? phone, let scene = destination.windowScene else { return }
        exitGeneration += 1; let generation = exitGeneration
        exitCover?.isHidden = true
        let cover = UIWindow(windowScene: scene); cover.windowLevel = .alert + 1
        let host = UIHostingController(rootView: ZStack {
            Club.lagoonDeep.ignoresSafeArea()
            Text("Back to the clubhouse").font(IslandUI.font(28, bold: true)).foregroundStyle(.white)
        })
        cover.rootViewController = host; cover.backgroundColor = UIColor(Club.lagoonDeep)
        exitCover=cover; cover.isHidden=false; host.view.layoutIfNeeded()
        ClubSound.play("whoosh", volume: 0.35)
        let duration = SportsSession.shared.presentationIntros == "full" ? 1.0 : 0.8
        DispatchQueue.main.asyncAfter(deadline: .now()+duration) { [weak self] in
            guard let self, generation==self.exitGeneration else { return }
            self.external?.rootViewController?.view.layoutIfNeeded(); self.phone?.rootViewController?.view.layoutIfNeeded()
            cover.isHidden=true; self.exitCover=nil
        }
    }
    func beginLoadingCover(in destination:''')
edit('GolfArcade/Unity/SportsDisplays.swift','        finishLoadingCover()\n        guard let scene = destination.windowScene','        exitGeneration += 1; exitCover?.isHidden=true; exitCover=nil\n        finishLoadingCover()\n        guard let scene = destination.windowScene')
edit('GolfArcade/Unity/SportsSession.swift','    func end() {\n        menuPauseVisible','    func end() {\n        if active { SportsDisplays.shared.beginExitCover() }\n        menuPauseVisible')
edit('GolfArcade/Unity/SportsDisplays.swift','            LoadingScreen(menu: .shared, compact: compact)','            ZStack {\n            Club.lagoonDeep\n            LoadingScreen(menu: .shared, compact: compact)')
edit('GolfArcade/Unity/SportsDisplays.swift','                .opacity(1 - loading.transitionFraction)','            }.opacity(1 - loading.transitionFraction)')
edit('GolfArcade/Unity/SportsDisplays.swift','if phase == .transitioning { SportsDisplays.shared.revealLoadingFrame() }','if phase == .transitioning { ClubSound.play("pop", volume: 0.35); SportsDisplays.shared.revealLoadingFrame() }')
edit('GolfArcade/Unity/ArcadeScreens.swift','}.padding(compact ? 24 : 48).frame(maxWidth:', '}.padding(compact ? 24 : 64).frame(maxWidth:')
# Keep skip separate from gameplay swing, and show it while the intro owns input.
edit('GolfArcade/Unity/SportsHome.swift','        .overlay(alignment:.top) {','''        .overlay(alignment: .bottom) {
            if session.active && session.loading.finished && !session.paused && session.multiplayerMatchID == nil && (session.tennisPhase == "intro" || session.golfPhase == "Intro") {
                Button("Skip intro") { session.command("presentationSkip") }
                    .font(IslandUI.font(18, bold: true)).padding(16).background(IslandUI.lime, in: Capsule()).foregroundStyle(IslandUI.navy)
                    .accessibilityIdentifier("presentation-skip").padding(.bottom, 16)
            }
        }
        .overlay(alignment:.top) {''')
edit('GolfArcade/Unity/SportsHome.swift','                            Button("Exit round", role:', '                            if session.golfPhase == "Aim" && session.multiplayerMatchID == nil { Button("Overview") { session.command("golfOverview") } }\n                            Button("Exit round", role:')
edit('GolfArcade/Unity/SportsHome.swift','session.golfHasNextHole ? "Next Hole" : "Play Again"','session.golfHasNextHole ? "Next Hole" : "Rematch"')
edit('Unity/Assets/Scripts/Game/NativeSportsSession.cs','presentationConstrained,bigMoments=true;','presentationConstrained,bigMoments=true,holeFlyover=true;')
edit('Unity/Assets/Scripts/Game/NativeSportsSession.cs','            PresentationPolicy.Configure(m.intros','            PresentationPolicy.HoleFlyover=m.holeFlyover;\n            PresentationPolicy.Configure(m.intros')
edit('Unity/Assets/Scripts/Game/PresentationPolicy.cs','Constrained, BigMoments = true, Multiplayer;','Constrained, BigMoments = true, Multiplayer, HoleFlyover=true;')
edit('Unity/Assets/Scripts/Game/GolfGame.Presentation.cs','golfVenueCut=PresentationPolicy.Cut(GolfVenueKey);','golfVenueCut=PresentationPolicy.HoleFlyover?PresentationPolicy.Cut(GolfVenueKey):PresentationCut.Off;')
