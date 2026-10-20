from pathlib import Path
import json,shutil
r=Path.cwd(); j=r/'work/playability-fix/changes.json'; paths=json.loads(j.read_text())
def save(path,s):
 p=r/path;b=r/'work/playability-fix/before'/path
 if not b.exists(): b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b)
 p.write_text(s)
 if path not in paths:paths.append(path)
 dst=r/'work/golf-look/device/combined/Source'/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
p='GolfArcade/Unity/IslandScreens.swift';s=(r/p).read_text().replace('let finished = menu.progress.finishedTutorial(sport)','let finished = true').replace('subtitle: "Cliffside round"','subtitle: "Choose a course, then tee off"');save(p,s)
p='GolfArcadeTests/MenuFlowRegressionTests.swift';s=(r/p).read_text();point=s.index('    func testMainMenu')
s=s[:point]+'''    func testBothSportsChooseMapsBeforeStartingTheRuntime() {
        let menu = TennisMenu()
        for sport in [Sport.golf, .tennis] {
            menu.debugShow(.hub(sport))
            menu.begin(MenuLaunch(sport: sport, mode: .tutorial), onPhone: true)
            XCTAssertEqual(menu.screen, .map)
            XCTAssertEqual(menu.launch?.mode, sport == .golf ? .round : .exhibition)
            XCTAssertEqual(menu.mapChoices.count, sport == .golf ? 4 : 3)
            XCTAssertFalse(SportsSession.shared.active)
            menu.back()
            XCTAssertEqual(menu.screen, .hub(sport))
        }
        XCTAssertEqual(TennisMenu.hubItems(.tennis), ["exhibition", "campaign", "training"])
        for id in TennisMenu.hubItems(.tennis) { XCTAssertTrue(menu.hubUnlocked(.tennis, id)) }
    }
    func testStartupFailureStopsLoadingAndOffersTheSameMapAgain() {
        let menu = TennisMenu.shared
        menu.begin(MenuLaunch(sport: .golf, mode: .round), onPhone: true)
        SportsSession.shared.loading.begin(now: Date())
        SportsSession.shared.failStartup("Display unavailable")
        XCTAssertTrue(SportsSession.shared.loading.finished)
        XCTAssertFalse(SportsSession.shared.active)
        XCTAssertEqual(menu.screen, .map)
        XCTAssertEqual(menu.mapSport, .golf)
        XCTAssertEqual(menu.notice, "Display unavailable")
        menu.goHome()
    }
    func testRetiredTennisTutorialAndRewardSavesReturnToSelection() {
        for step in [OnboardingStep.tutorial(.tennis), .reward(.tennis), .motionPrimer] {
            let defaults = UserDefaults(suiteName: "retired-\\(UUID())")!
            let store = OnboardingStore(defaults: defaults)
            store.step = step; store.explicitRun = true
            let flow = OnboardingFlow(store: store, progress: SportProgress(defaults: defaults), arguments: [])
            XCTAssertEqual(flow.step, .choose)
            XCTAssertFalse(store.rewardClaimed(.tennis))
        }
    }
'''+s[point:];save(p,s)
p='GolfArcadeUITests/MenuNavigationRegressionTests.swift';s=(r/p).read_text().replace('        app.buttons["menu-back"].tap()','''        app.buttons["hub-round"].tap()
        for key in ["cliffside", "postcards", "wildisles", "magma"] {
            XCTAssertTrue(app.buttons["map-\\(key)"].exists)
        }
        app.buttons["menu-back"].tap()
        XCTAssertTrue(app.buttons["hub-round"].waitForExistence(timeout: 5))
        app.buttons["menu-back"].tap()''');point=s.index('        app.buttons["menu-home"].tap()');s=s[:point]+'''        app.buttons["Tennis"].tap()
        XCTAssertTrue(app.buttons["hub-exhibition"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["hub-tutorial"].exists)
        app.buttons["hub-exhibition"].tap()
        let start = app.buttons["Start Match"]
        XCTAssertTrue(start.waitForExistence(timeout: 5)); start.tap()
        for key in ["resort", "skyscraper", "volcano"] { XCTAssertTrue(app.buttons["map-\\(key)"].exists) }
'''+s[point:];save(p,s)
p='Unity/Assets/Tests/PlayMode/NativeGolfFlowTests.cs';s=(r/p).read_text();point=s.index('        [UnityTearDown]');s=s[:point]+'''        [UnityTest] public IEnumerator EveryNativeCourseStartsAtItsOwnFirstHole() {
            game = new GameObject("Native course selection check").AddComponent<GolfGame>();
            yield return null;
            foreach (var course in GolfArcade.Course.Course.All()) {
                game.PrepareNativeAddress(course.Key);
                yield return null;
                Assert.That(game.CurrentHole.Number, Is.EqualTo(course.Holes[0].Number), course.Key);
                Assert.That(game.Current, Is.EqualTo(GolfGame.State.Aim), course.Key);
                Assert.That(GameObject.Find("Menu"), Is.Null);
            }
        }
'''+s[point:];save(p,s)
# Actual device-only probe, explicitly launched by argument. Uses the production menu and bridge.
p='GolfArcade/Unity/SportsHome.swift';s=(r/p).read_text().replace('if SportsSession.benchmark && !session.active {','if args.contains("--playability-check") { await PlayabilityCheck.run(); return }\n            if SportsSession.benchmark && !session.active {');s+='''
@MainActor private enum PlayabilityCheck {
    static func run() async {
        let session = SportsSession.shared, menu = TennisMenu.shared
        OnboardingFlow.shared.exitToMenu()
        session.touch = true
        for sport in [Sport.golf, .tennis] {
            menu.begin(MenuLaunch(sport: sport, mode: sport == .golf ? .round : .exhibition, round: sport == .tennis ? 0 : nil))
            guard menu.screen == .map else { SportsDiagnostics.write("PLAYABILITY FAIL map \\(sport)"); return }
            let key = sport == .golf ? "postcards" : "resort"
            menu.tap("map-\\(key)")
            for _ in 0..<400 {
                if session.ready && session.loading.finished || !session.active { break }
                try? await Task.sleep(for: .milliseconds(100))
            }
            guard session.active && session.ready && !session.paused else {
                SportsDiagnostics.write("PLAYABILITY FAIL \\(sport) \\(session.status)"); return
            }
            SportsDiagnostics.write("PLAYABILITY READY \\(sport) map=\\(key) external=\\(session.displayConnected)")
            if sport == .golf {
                session.swing(0.65)
                var flight = false
                for _ in 0..<80 {
                    flight = flight || session.golfPhase == "Flight"
                    try? await Task.sleep(for: .milliseconds(100))
                }
                SportsDiagnostics.write("PLAYABILITY \\(flight ? "PASS" : "FAIL") golf swing state=\\(session.golfPhase) feedback=\\(session.feedback)")
            } else {
                try? await Task.sleep(for: .seconds(12))
                SportsDiagnostics.write("PLAYABILITY \\(session.active && !session.paused && session.contacts.count > 0 ? "PASS" : "FAIL") tennis contacts=\\(session.contacts.count) phase=\\(session.tennisPhase)")
            }
            session.end()
            try? await Task.sleep(for: .seconds(1))
        }
        menu.goHome()
        SportsDiagnostics.write("PLAYABILITY CHECK COMPLETE")
    }
}
''';save(p,s)
j.write_text(json.dumps(paths,indent=2))
