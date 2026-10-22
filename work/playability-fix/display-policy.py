from pathlib import Path
import json,shutil
r=Path.cwd();j=r/'work/playability-fix/changes.json';paths=json.loads(j.read_text())
def edit(path,fn):
 p=r/path;b=r/'work/playability-fix/before'/path
 if not b.exists():b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b)
 s=fn(p.read_text());p.write_text(s)
 if path not in paths:paths.append(path)
 dst=r/'work/golf-look/device/combined/Source'/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
def rep(s,a,b):
 assert a in s,a[:80];return s.replace(a,b)
def session(s):
 s=rep(s,'        let preview = preview && !displayConnected','        let preview = false')
 s=rep(s,'status="No independent external display is available. Connect AirPlay/wired display or choose preview."','status="Connect a TV or Mac with AirPlay or a wired display to play. This phone is your controller."')
 s=rep(s,'if !paused && sport == "tennis" && displayConnected && checkTimingOnResume {\n            checkTimingOnResume = false; startTimingCheck()\n        }','''if !paused && sport == "tennis" && displayConnected && !Self.benchmark && (checkTimingOnResume || timingCalibration == nil) {
            if checkTimingOnResume { checkTimingOnResume = false; startTimingCheck() }
            else { timingPrompt = true }
        }''')
 return s
edit('GolfArcade/Unity/SportsSession.swift',session)
def displays(s):
 a=s.index('        if external != nil || !usePreview');e=s.index('    private var networkOverlay',a)
 s=s[:a]+'''        guard let external else { return nil }
        showMenu()
        return external
    }
'''+s[e:]
 s=rep(s,'SportsSession.shared.status="Display disconnected. Reconnect or return to the menu for on-phone preview."','SportsSession.shared.status="Display disconnected. Reconnect your TV or Mac to continue; this phone remains your controller."')
 return s
edit('GolfArcade/Unity/SportsDisplays.swift',displays)
def menu(s):
 s=rep(s,'case .connect: return [["phone"], ["back"]]','case .connect: return [["back"]]')
 s=rep(s,'let onPhone = requestedPhone ?? !session.displayConnected','let onPhone = false')
 s=rep(s,'        guard onPhone || session.displayConnected else { show(.connect); return }','        SportsDisplays.shared.refresh()\n        guard session.displayConnected else { show(.connect); return }')
 s=rep(s,'case "phone": if let launch { begin(launch, onPhone: true, skipMap: true) }','case "phone": show(.connect)')
 s=rep(s,'if !session.active { show(previous); notice = session.status }','if !session.active, screen == .loading { launchFailed(session.status) }')
 return s
edit('GolfArcade/Unity/TennisMenu.swift',menu)
def home(s):
 s=rep(s,'if onboarding.holdsMenu { OnboardingRoot(flow: onboarding) }','if session.displayConnected && !session.active { TennisRemote() }\n            else if onboarding.holdsMenu { OnboardingRoot(flow: onboarding) }')
 s=rep(s,'else if session.active && !session.loading.finished { LoadingScreen(menu: menu, compact: true) }','else if session.active && !session.loading.finished { TennisRemote() }')
 s=rep(s,'                        Button("On-phone touch preview") { session.start(preview:true) }.accessibilityIdentifier("startUnityPreview").disabled(session.displayConnected)\n                        if session.displayConnected { Text("Disconnect the TV to use on-phone preview.").font(.caption) }','                        Text("A connected TV or Mac is required to play.")')
 s=rep(s,'        OnboardingFlow.shared.exitToMenu()\n        session.touch = true','        OnboardingFlow.shared.exitToMenu()\n        guard session.displayConnected else { SportsDiagnostics.write("PLAYABILITY CHECK requires external screen; phone gameplay disabled"); return }\n        session.touch = true')
 return s
edit('GolfArcade/Unity/SportsHome.swift',home)
def flow(s):
 s=rep(s,'        store.step = selected; step = selected','''        // The shipped app opens the menu directly. Identity editing remains in the locker.
        if arguments == ProcessInfo.processInfo.arguments && !arguments.contains("-forceOnboarding") {
            selected = .done; store.explicitRun = false
        }
        store.step = selected; step = selected''')
 s=rep(s,'func playOnPhone() { store.touch = true; SportsSession.shared.touch = true; Analytics.track("play_on_phone"); move(to: .choose) }','func playOnPhone() { move(to: .connect) }')
 return s
edit('GolfArcade/Onboarding/OnboardingFlow.swift',flow)
edit('GolfArcade/Onboarding/OnboardingConnectScreen.swift',lambda s:rep(s,'            IslandAction(title: "Play on this phone for now", focused: false, primary: !session.displayConnected) { flow.playOnPhone() }.accessibilityIdentifier("onboarding-phone")','            Text("A TV or Mac is required. This phone stays your controller.").font(IslandUI.font(15))'))
edit('GolfArcade/Unity/ClubScreens.swift',lambda s:rep(s,'                    IslandAction(title: "Play on this phone", focused: menu.isFocused("phone"), primary: true, compact: compact) { menu.tap("phone") }.frame(maxWidth: 340)','                    Text("A connected screen is required to play. Your phone stays the controller.").font(IslandUI.font(17, bold: true))'))
def playviews(s):
 s=rep(s,'case .map: "CHOOSE YOUR COURT"','case .map: menu.mapSport == .golf ? "CHOOSE YOUR COURSE" : "CHOOSE YOUR COURT"')
 s=rep(s,'        .preferredColorScheme(.dark)\n    }\n\n    /// What the TV shows', '        .preferredColorScheme(.dark)\n        .accessibilityIdentifier("phone-menu-controller")\n    }\n\n    /// What the TV shows')
 return s
edit('GolfArcade/Unity/TennisPlayViews.swift',playviews)
p='GolfArcadeTests/MenuFlowRegressionTests.swift';s=(r/p).read_text();point=s.index('    func testAirPlayWindowWins');s=s[:point]+'''    func testPhoneGameplayIsBlockedWithoutAnExternalScreen() {
        let displays = SportsDisplays.shared
        let saved = displays.external
        defer { displays.external = saved }
        displays.external = nil
        XCTAssertNil(displays.gameWindow(preview: true))
        XCTAssertNil(displays.gameWindow(preview: false))
        let menu = TennisMenu.shared
        menu.begin(MenuLaunch(sport: .golf, mode: .round), onPhone: true)
        menu.tap("map-cliffside")
        XCTAssertEqual(menu.screen, .connect)
        XCTAssertFalse(SportsSession.shared.active)
        XCTAssertFalse(menu.rows(.connect).flatMap { $0 }.contains("phone"))
        menu.goHome()
    }
'''+s[point:];edit(p,lambda _:s)
j.write_text(json.dumps(paths,indent=2))
