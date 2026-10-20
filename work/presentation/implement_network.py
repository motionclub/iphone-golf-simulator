from pathlib import Path
def edit(f,a,b):
 p=Path(f);s=p.read_text();assert a in s,(f,a);p.write_text(s.replace(a,b,1))
edit('GolfArcade/Multiplayer/MultiplayerService.swift','    @ObservationIgnored private var loadingStarted: Double = 0','    @ObservationIgnored private var loadingStarted: Double = 0\n    @ObservationIgnored private var presentationReadyAt: [String: Double] = [:]\n    @ObservationIgnored private var scheduledRunAt: Double = 0')
edit('GolfArcade/Multiplayer/MultiplayerService.swift','    func runtimeLoaded() { try? sendControl("loaded") }','    func runtimeLoaded(readyAfter: Double = 0) { try? sendControl("loaded", payload: String(networkTime + min(2, max(0, readyAfter)))) }')
edit('GolfArcade/Multiplayer/MultiplayerService.swift','        case "loaded": if p.matchID == lobby?.matchID {\n            lobby!.participants[i].loaded = true','''        case "loaded": if p.matchID == lobby?.matchID {
            let reported = Double(p.payload) ?? now
            guard reported.isFinite else { return }
            presentationReadyAt[p.sender] = max(now, min(now + 2, reported))
            lobby!.participants[i].loaded = true''')
edit('GolfArcade/Multiplayer/MultiplayerService.swift','try? transmit("run", to: [p.sender])','try? transmit("run", payload: String(scheduledRunAt), to: [p.sender])')
edit('GolfArcade/Multiplayer/MultiplayerService.swift','loadingNeedsDecision = false; lobby!.phase = .playing; lobby!.revision += 1; publishLobby(); try? broadcast("run"); pushRuntime("run")','''loadingNeedsDecision = false
            scheduledRunAt = max(now, lobby!.competitors.map { presentationReadyAt[$0.id] ?? now }.max() ?? now) + max(.5, roundTrip * 2)
            lobby!.phase = .playing; lobby!.revision += 1; publishLobby()
            try? broadcast("run", payload: String(scheduledRunAt)); pushRuntime("run", payload: String(scheduledRunAt))''')
# Each match has an independent barrier and schedule.
edit('GolfArcade/Multiplayer/MultiplayerService.swift','    func startMatch() throws {','    func startMatch() throws {\n        presentationReadyAt.removeAll(); scheduledRunAt = 0')
edit('GolfArcade/Unity/SportsSession.swift','MultiplayerService.shared.runtimeLoaded()','MultiplayerService.shared.runtimeLoaded(readyAfter: max(0, LoadingModel.multiplayerMinimum - loading.elapsed) + LoadingModel.finishDuration)',)
edit('Unity/Assets/Scripts/Multiplayer/SportsMultiplayer.cs','        double clockOffset,lastSnapshot,','        double scheduledStart = double.PositiveInfinity; bool startScheduled;\n        public double SharedClock => Clock + (IsHost ? 0 : clockOffset);\n        double clockOffset,lastSnapshot,')
edit('Unity/Assets/Scripts/Multiplayer/SportsMultiplayer.cs','            Configuration=c;Running=false;','            startScheduled=false; scheduledStart=double.PositiveInfinity;\n            Configuration=c;Running=false;')
edit('Unity/Assets/Scripts/Multiplayer/SportsMultiplayer.cs','            if(!Running)return;\n            if(IsHost) {','''            if(startScheduled && !Running && SharedClock>=scheduledStart) {
                startScheduled=false; Running=true; Time.timeScale=1;
                tennisView?.BeginSharedPresentation();
                PresentationPolicy.Event("Venue","scheduledBegin",1,scheduledStart.ToString("F3"));
                SendSnapshot(true);
            }
            if(!Running)return;
            if(IsHost) {''')
edit('Unity/Assets/Scripts/Multiplayer/SportsMultiplayer.cs','case "run":Running=true;Time.timeScale=1;SendSnapshot(true);break;','''case "run":
                    if(Running || startScheduled) break;
                    if(!double.TryParse(p.payload,System.Globalization.NumberStyles.Float,System.Globalization.CultureInfo.InvariantCulture,out scheduledStart) || double.IsNaN(scheduledStart) || double.IsInfinity(scheduledStart)) scheduledStart=SharedClock;
                    startScheduled=true; break;''')
edit('Unity/Assets/Scripts/Tennis/TennisGame.Network.cs','        public void PredictNetworkSwing','        public void BeginSharedPresentation() { if(presentation) presentation.RestartShared(); }\n        public void PredictNetworkSwing')
edit('Unity/Assets/Scripts/Tennis/TennisGame.Network.cs','string phase=networkLocalSide<0?"watching":s.complete?"finished":','string phase=s.phase=="intro"?"intro":networkLocalSide<0?"watching":s.complete?"finished":')
edit('Unity/Assets/Scripts/Multiplayer/NetworkTennisMatch.cs','public string phase="serve",reason="";','public string phase="serve",reason=""; public double presentationUntil; public string boundary="point";')
edit('Unity/Assets/Scripts/Multiplayer/NetworkTennisMatch.cs','if (intro) { State.phase="intro"; State.emoteHoldUntil=6; }','if (intro) { State.phase="intro"; State.emoteHoldUntil=State.presentationUntil=3.5; }')
edit('Unity/Assets/Scripts/Multiplayer/NetworkTennisMatch.cs','State.emoteHoldUntil = Math.Max(State.emoteHoldUntil, p.emoteUntil + .3);','p.emoteUntil = Math.Min(p.emoteUntil, State.presentationUntil); // Cosmetic; never extend the shared boundary.')
edit('Unity/Assets/Scripts/Multiplayer/NetworkTennisMatch.cs','if(State.phase=="intro") {if(State.time>=State.emoteHoldUntil)BeginPoint();return;}\n            if(State.phase=="point") {if(State.time-State.phaseAt>2 && State.time>=State.emoteHoldUntil)BeginPoint();return;}','if(State.phase=="intro" || State.phase=="point") {if(State.time>=State.presentationUntil)BeginPoint();return;}')
edit('Unity/Assets/Scripts/Multiplayer/NetworkTennisMatch.cs','            State.score.AwardPoint(winner==0);State.winner=winner;','''            int setsBefore=State.score.PlayerSets+State.score.OpponentSets;
            bool game=State.score.AwardPoint(winner==0);
            bool set=State.score.PlayerSets+State.score.OpponentSets>setsBefore;
            State.boundary=set?"set":game?"game":"point";
            State.presentationUntil=State.time+(set?2.5:game?1.5:.8);
            State.winner=winner;''')
# Restore the arm state after an optional Overview without resetting club/aim/ball.
edit('Unity/Assets/Scripts/Game/GolfGame.Presentation.cs','Current=State.Aim; hud.HideHoleIntro();','Current=State.Aim; Swing.Armed=true; hud.HideHoleIntro();')
