from pathlib import Path
import json,shutil
R=Path.cwd(); B=R/'work/playability-fix/before'; owned=[]
def edit(path,fn):
 p=R/path; b=B/path; b.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,b); s=p.read_text(); s=fn(s); p.write_text(s); owned.append(path)
def rep(s,a,b):
 assert a in s,a[:100]; return s.replace(a,b)
def menu(s):
 s=rep(s,'["tutorial", "campaign", "exhibition", "training"]','["exhibition", "campaign", "training"]')
 s=rep(s,'["level", "coaching", "replayOnboarding", "resetTips", "resetProgress"]','["level", "resetProgress"]')
 s=rep(s,'case .map: return [TennisVenueChoice.allCases.map { "map-\\($0.rawValue)" }, ["back"]]','case .map: return [mapChoices.map { "map-\\($0.id)" }, ["back"]]')
 start=s.index('    /// Golf is immediately playable;'); end=s.index('    /// Bumped on every screen',start)
 s=s[:start]+'''    /// Both sports are available without completing a lesson.
    func hubUnlocked(_ sport: Sport, _ id: String) -> Bool {
        Self.hubItems(sport).contains(id)
    }
    var mapSport: Sport { launch?.sport ?? .tennis }
    var mapChoices: [SportMapChoice] { SportMapChoice.choices(for: mapSport) }
    var selectedMap: String { mapSport == .golf ? session.golfCourse : session.tennisVenue }

'''+s[end:]
 s=rep(s,'case .hub(let sport): row = sport == .golf ? 0 : progress.finishedTutorial(sport) ? 1 : 0; column = 0','case .hub: row = 0; column = 0')
 s=rep(s,'TennisVenueChoice.allCases.firstIndex { $0.rawValue == session.tennisVenue }','mapChoices.firstIndex { $0.id == selectedMap }')
 s=rep(s,'        if !progress.finishedTutorial(.tennis) { return ("Start here", "Your first lesson with Coach Ray") }\n','')
 s=rep(s,'        if !progress.finishedTutorial(.tennis) { startTutorial(.tennis); return }\n','')
 s=rep(s,'case "homeCampaign": if progress.finishedTutorial(.tennis) { show(.campaign) } else { startTutorial(.tennis) }','case "homeCampaign": show(.campaign)')
 s=rep(s,'            if sport == .tennis && !progress.finishedTutorial(sport) { OnboardingFlow.shared.choose(sport); return }\n','')
 s=rep(s,'Press again to erase tutorials and campaign progress','Press again to erase campaign progress')
 s=rep(s,'            session.tennisVenue = String(m.dropFirst(4))','            if mapSport == .golf { session.golfCourse = String(m.dropFirst(4)) }\n            else { session.tennisVenue = String(m.dropFirst(4)) }')
 start=s.index('    /// Ray\'s tennis lesson.'); end=s.index('    // MARK: Story',start)
 s=s[:start]+'''    /// Compatibility for saved routes and older UI: choose a map for a normal game.
    func startTutorial(_ sport: Sport) {
        begin(MenuLaunch(sport: sport, mode: sport == .golf ? .round : .exhibition, round: sport == .tennis ? 0 : nil))
    }
    func tutorialFinished() {}

'''+s[end:]
 s=rep(s,'if launch.sport == .golf && launch.mode == .tutorial { launch.mode = .round }','if launch.mode == .tutorial { launch.mode = launch.sport == .golf ? .round : .exhibition }')
 s=rep(s,'if !skipMap, launch.sport == .tennis, launch.mode != .tutorial {','if !skipMap, launch.sport.playable {')
 s=rep(s,'session.startGolf(tutorial: launch.mode == .tutorial, preview: onPhone)','session.startGolf(tutorial: false, preview: onPhone)')
 s=rep(s,'let court: [AfterMatch] = launch.sport == .tennis && launch.mode != .tutorial ? [.court] : []','let court: [AfterMatch] = launch.sport.playable ? [.court] : []')
 point=s.index('    /// A TV appeared while waiting')
 s=s[:point]+'''    /// Leave a failed startup with the chosen match available to retry.
    func launchFailed(_ message: String) {
        if let launch {
            pendingPick = (launch, !session.displayConnected)
            show(.map)
        } else { show(.main) }
        notice = message
    }

'''+s[point:]
 return s
edit('GolfArcade/Unity/TennisMenu.swift',menu)
def maps(s):
 return s+'''
/// Keys match Unity's Course.All(); every listed course has modelled playable holes.
enum GolfCourseChoice: String, CaseIterable {
    case cliffside, postcards, wildisles, magma
    var title: String {
        switch self { case .cliffside: "Cliffside"; case .postcards: "Postcards"; case .wildisles: "Wild Isles"; case .magma: "Magma Open" }
    }
    var detail: String {
        switch self {
        case .cliffside: "Ocean cliffs and island carries"
        case .postcards: "Needle, The Steps and Volcano Rim"
        case .wildisles: "A tour through the wild islands"
        case .magma: "Lava hazards and volcanic greens"
        }
    }
}
struct SportMapChoice: Identifiable {
    let id: String
    let title: String
    let detail: String
    let art: String
    static func choices(for sport: Sport) -> [Self] {
        if sport == .golf {
            return GolfCourseChoice.allCases.map { Self(id: $0.rawValue, title: $0.title, detail: $0.detail, art: "club-golf") }
        }
        return TennisVenueChoice.allCases.map { Self(id: $0.rawValue, title: $0.title, detail: $0.tagline, art: $0.art) }
    }
}
'''
edit('GolfArcade/Unity/TennisMapScreen.swift',maps)
def club(s):
 s=rep(s,'IslandShell(title: "Choose a court", compact: compact)','IslandShell(title: menu.mapSport == .golf ? "Choose a course" : "Choose a court", compact: compact)')
 s=rep(s,'ForEach(TennisVenueChoice.allCases) { venue in','ForEach(menu.mapChoices) { venue in')
 s=rep(s,'"map-\\(venue.rawValue)"','"map-\\(venue.id)"')
 s=rep(s,'UIImage(named: "\\(venue.art).jpg") ?? UIImage()','UIImage(named: "\\(venue.art).jpg") ?? UIImage(named: "\\(venue.art).png") ?? UIImage()')
 s=rep(s,'Text(SportsSession.shared.tennisVenue == venue.rawValue ? "Selected court" : "Select court")','Text(venue.detail)')
 s=rep(s,'.accessibilityLabel("Play at \\(venue.title)")','.accessibilityLabel("Play at \\(venue.title)").accessibilityIdentifier(id)')
 s=rep(s,'case "pm-court", "court": "Change Court"','case "pm-court", "court": menu.launch?.sport == .golf ? "Change Course" : "Change Court"')
 s=rep(s,'subtitle: "A round at Cliffside"','subtitle: "Choose your course"')
 return s
edit('GolfArcade/Unity/ClubScreens.swift',club)
def onboard(s):
 s=rep(s,'if selected == .tutorial(.golf) { selected = .choose; store.explicitRun = false }','switch selected {\n        case .tutorial, .reward, .motionPrimer: selected = .choose; store.explicitRun = false\n        default: break\n        }')
 s=rep(s,'store.touch = false; move(to: .motionPrimer)','store.touch = false; SportsSession.shared.touch = false; move(to: .choose)')
 start=s.index('        if sport == .golf {',s.index('    func choose(')); end=s.index('    func tutorialStarted(',start)
 s=s[:start]+'''        store.explicitRun = false; launched = false; coachIntro = false
        move(to: .done)
        TennisMenu.shared.begin(MenuLaunch(sport: sport, mode: sport == .golf ? .round : .exhibition, round: sport == .tennis ? 0 : nil))
    }
    func launchTutorialIfNeeded() {
        if case .tutorial = step { move(to: .choose) }
    }
'''+s[end:]
 s=rep(s,'destination = store.touch ? .connect : .motionPrimer','destination = .connect')
 return s
edit('GolfArcade/Onboarding/OnboardingFlow.swift',onboard)
def root(s):
 start=s.index('            else if flow.step == .motionPrimer'); end=s.index('            else { Text(flow.step.key)',start)
 s=s[:start]+'''            else if flow.step != .done { OnboardingGamePicker(flow: flow) }
'''+s[end:]; return s
edit('GolfArcade/Onboarding/OnboardingRoot.swift',root)
def session(s):
 point=s.index('    /// Set by the `-benchTennis`')
 s=s[:point]+'''    var golfCourse = UserDefaults.standard.string(forKey: "sports.golfCourse") ?? "cliffside" {
        didSet { UserDefaults.standard.set(golfCourse, forKey: "sports.golfCourse") }
    }
'''+s[point:]
 s=rep(s,'        sport = "tennis"\n        opponentName', '        let mode = mode == "tutorial" ? "exhibition" : mode\n        sport = "tennis"\n        opponentName')
 s=rep(s,'        if mode == "tutorial" { launchExtras["tutorialStart"] = OnboardingFlow.shared.store.tutorialStep }\n','')
 s=rep(s,'launchExtras = ["mode": "round"]','launchExtras = ["mode": "round", "course": GolfCourseChoice(rawValue: golfCourse)?.rawValue ?? "cliffside"]')
 s=rep(s,'catch { status=error.localizedDescription; active=false; pending=nil; SportsDisplays.shared.endPreview(); return }','catch { failStartup(error.localizedDescription); return }')
 s=rep(s,'self.status="Unity did not finish loading. Return to menu and retry."; self.pause()','self.failStartup("Unity did not finish loading. Choose a map to retry.")')
 # No automatic aim drills or first-time timing tutorial. Explicit settings recalibration stays available.
 s=rep(s,'launchExtras["mode"] as? String != "tutorial", !Self.benchmark, force || !aimChecked else { return }','!Self.benchmark, force else { return }')
 start=s.index('        if sport == "tennis", !touch, !Self.benchmark, !aimChecked,',s.index('    func readyToPlay'))
 end=s.index('    /// Swing along with',start)
 s=s[:start]+'''        resume()
        if aimLesson != nil { queueAimFeed(); return }
        if !paused && sport == "tennis" && displayConnected && checkTimingOnResume {
            checkTimingOnResume = false; startTimingCheck()
        }
    }
'''+s[end:]
 s=rep(s,'if touch { status="Tap Ready to play."; if SportsSession.benchmark { readyToPlay() } }','if touch { readyToPlay() }')
 s=rep(s,'case "error": pending=nil; status=event["message"] as? String ?? "Unity error"; pause(reason:status)','''case "error":
                let message = event["message"] as? String ?? "Unity error"
                if !ready { failStartup(message) }
                else { status = message; pause(reason: message) }''')
 point=s.index('    private func sendPending()')
 s=s[:point]+'''    func failStartup(_ message: String) {
        SportsDiagnostics.write("startup failed: \\(message)")
        end()
        status = message
        TennisMenu.shared.launchFailed(message)
    }
'''+s[point:]
 return s
edit('GolfArcade/Unity/SportsSession.swift',session)
def native(s):
 s=rep(s,'public string venue,courtHex,network;','public string venue,course,courtHex,network;')
 s=rep(s,': m.mode=="tutorial" ? TennisGame.Mode.Tutorial : TennisGame.Mode.Exhibition;',': TennisGame.Mode.Exhibition;')
 s=rep(s,'if(golf) golf.PrepareNativeAddress();','if(golf) golf.PrepareNativeAddress(m.course);')
 start=s.index('            if(!ConfigureDisplay(external)) yield break;')
 s=s[:start]+s[start:].replace('            if(!ConfigureDisplay(external)) yield break;','''            float attachDeadline=Time.realtimeSinceStartup+8;
            while(!ConfigureDisplay(external)) {
                if(!external || Time.realtimeSinceStartup>=attachDeadline) {
                    Emit("error", external ? "The external display could not start. Check AirPlay and choose a map to retry." : "Gameplay camera is missing.");
                    yield break;
                }
                yield return null;
            }''',1)
 s=rep(s,'[DllImport("__Internal")][return: MarshalAs(UnmanagedType.I1)] static extern bool SportsPresentExternalDisplay();','[DllImport("__Internal")] static extern int SportsPrepareExternalDisplay();')
 s=rep(s,'static bool SportsPresentExternalDisplay()=>true;','static int SportsPrepareExternalDisplay()=>1;')
 start=s.index('            int index=external?1:0;'); end=s.index('            foreach(var camera',start)
 s=s[:start]+'''            // The scene's UIScreen can appear after Unity's initial display cache was built.
            // Native code registers and activates that exact screen and returns its cache index.
            int index=external ? SportsPrepareExternalDisplay() : 0;
            if(index<0 || Display.displays.Length<=index || !gameplayCamera) return false;
'''+s[end:]
 return s
edit('Unity/Assets/Scripts/Game/NativeSportsSession.cs',native)
def golf(s):
 s=rep(s,'public void PrepareNativeAddress() {','public void PrepareNativeAddress(string courseKey = null) {')
 s=rep(s,'            if (Match == null) StartRound();','''            var selected = GolfArcade.Course.Course.ByKey(courseKey ?? "cliffside") ?? GolfArcade.Course.Course.Cliffside();
            setup = GameSetup.Solo(ProfileStore.Active, selected.Key);
            StartRound();''')
 return s
edit('Unity/Assets/Scripts/Game/GolfGame.Native.cs',golf)
edit('Unity/Assets/Resources/Tennis/TropicalV3/TropicalTennisResort.fbx.meta',lambda s:rep(s,'isReadable: 0','isReadable: 1'))
# Disable in-game pop-up coaching on every native launch while tutorials are retired.
edit('GolfArcade/Unity/SportsSession.swift',lambda s:rep(s,'"tips":coachingTips','"tips":false'))
(R/'work/playability-fix/changes.json').write_text(json.dumps(list(dict.fromkeys(owned)),indent=2))
