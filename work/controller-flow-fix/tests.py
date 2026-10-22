from pathlib import Path
import json, uuid, shutil
r=Path.cwd(); m=r/'work/controller-flow-fix/changes.json'; files=json.loads(m.read_text())
def change(path,fn):
 p=r/path;p.write_text(fn(p.read_text()))
 if path not in files:files.append(path)
change('GolfArcade/Unity/SportsSession.swift',lambda s:s.replace('guard !paused && canDive && finishedMatch == nil','guard pointControlsVisible && canDive').replace('message: "Using the saved timing for this screen."','message: timingCalibration == nil ? "The game will refine your timing as you play." : "Using the saved timing for this screen."'))
change('GolfArcade/Unity/TennisPlayViews.swift',lambda s:s.replace('''            if session.ready && session.loading.finished && session.finishedMatch == nil {
                PointClipControls''','''            if session.ready && session.loading.finished && session.finishedMatch == nil && session.setupStage == .playing && session.tennisPhase == "point" {
                PointClipControls''').replace(' : "ready",\n                      enabled:', ' : session.canDive ? "ready" : "waiting for ball",\n                      enabled:'))
change('Unity/Assets/Scripts/Tennis/TennisGame.cs',lambda s:s.replace('''        public void Toss(float accuracy = -1)
        {''','''        public void Toss(float accuracy = -1)
        {
            if (ControllerSetup) return;''').replace('''        public void Step(float dt)
        {''','''        public void Step(float dt)
        {
            if (ControllerSetup) return;'''))
change('GolfArcadeTests/MenuFlowRegressionTests.swift',lambda s:s.replace('    func testGolfHasOnePlayableRoute', '''    func testCalibrationPrecedesReadyAndDoesNotStartAPoint() {
        let session = SportsSession()
        session.active = true; session.ready = true; session.displayConnected = true
        session.sport = "tennis"; session.touch = true; session.loading.cancel()
        session.readyToPlay()
        XCTAssertTrue(session.paused)
        XCTAssertEqual(session.setupStage, .scan)
        session.offerTimingCalibration()
        XCTAssertEqual(session.setupStage, .timing)
        XCTAssertTrue(session.timingPrompt)
        session.readyToPlay(); session.resume()
        XCTAssertTrue(session.paused, "Ready/Resume must not bypass calibration")
        session.startTimingCheck()
        XCTAssertTrue(session.checkingTiming)
        XCTAssertFalse(session.paused, "Phone samples must flow during TV calibration")
        XCTAssertFalse(session.pointControlsVisible)
        session.receiveTimingResult("failed")
        XCTAssertEqual(session.setupStage, .ready)
        XCTAssertTrue(session.paused, "Calibration completion must wait for Ready")
        XCTAssertFalse(session.checkingTiming)
        session.readyToPlay()
        XCTAssertEqual(session.setupStage, .playing)
        XCTAssertFalse(session.paused)
        session.tennisPhase = "serve"
        XCTAssertTrue(session.tossVisible)
    }
    func testPointControlsAndCelebrationFollowActualPointPhase() {
        let session = SportsSession()
        session.active = true; session.ready = true; session.loading.cancel()
        session.sport = "tennis"; session.setupStage = .playing; session.paused = false
        for phase in ["serve", "toss", "receive", "rally"] {
            session.tennisPhase = phase
            XCTAssertTrue(session.pointControlsVisible)
            XCTAssertEqual(session.tossVisible, phase == "serve")
            XCTAssertFalse(session.canPlayEmote)
        }
        session.tennisPhase = "point"
        XCTAssertFalse(session.pointControlsVisible)
        session.emoteWindow = "intro"; XCTAssertFalse(session.canPlayEmote)
        session.emoteWindow = ""; XCTAssertFalse(session.canPlayEmote)
        session.emoteWindow = "point"; XCTAssertTrue(session.canPlayEmote)
        session.paused = true; XCTAssertFalse(session.canPlayEmote)
    }
    func testInterruptedTimingReturnsToCalibrationWithoutStartingPlay() {
        let session = SportsSession()
        session.active = true; session.ready = true; session.displayConnected = true
        session.sport = "tennis"; session.touch = true; session.loading.cancel()
        session.offerTimingCalibration(); session.startTimingCheck()
        session.pause(reason: "Display disconnected")
        XCTAssertTrue(session.timingPrompt)
        XCTAssertFalse(session.checkingTiming)
        XCTAssertEqual(session.setupStage, .timing)
        session.receiveTimingResult("100")
        XCTAssertEqual(session.setupStage, .timing, "Ignore late results from a cancelled check")
        session.skipTimingCheck()
        XCTAssertEqual(session.setupStage, .ready)
        XCTAssertTrue(session.paused)
    }
    func testGolfHasOnePlayableRoute''',1))
change('GolfArcade/Unity/SportsHome.swift',lambda s:s.replace('            OnlineLobbyProofDriver.start(menu,args:args)', '''            if let i = args.firstIndex(of: "-controllerPhaseCheck"), let phase = args[safe: i + 1] {
                SportsDisplays.shared.external = UIWindow(frame: CGRect(x: 0, y: 0, width: 1920, height: 1080))
                session.displayConnected = true; session.active = true; session.ready = true
                session.sport = "tennis"; session.touch = true; session.loading.cancel()
                session.setupStage = .playing; session.paused = false; session.tennisPhase = phase
                session.canDive = phase == "rally"; session.emoteWindow = phase == "point" ? "point" : ""
                if phase == "timing" { session.offerTimingCalibration() }
                if phase == "ready" { session.setupStage = .ready; session.paused = true }
            }
            OnlineLobbyProofDriver.start(menu,args:args)''',1))
change('GolfArcadeUITests/MenuNavigationRegressionTests.swift',lambda s:s.replace('    func testConnectedPhone', '''    func testControllerShowsSetupThenServeDiveAndWinningPointEmotes() {
        continueAfterFailure = false
        let app = XCUIApplication()
        func launch(_ phase: String) {
            app.terminate()
            app.launchArguments = ["-skipOnboarding", "-controllerPhaseCheck", phase]
            app.launch()
            XCTAssertTrue(app.buttons["controller-exit"].waitForExistence(timeout: 15))
            XCTAssertFalse(app.buttons["tutorial-skip-step"].exists)
            XCTAssertFalse(app.staticTexts["COACH RAY"].exists)
        }
        launch("timing")
        XCTAssertTrue(app.buttons["timing-start"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["controller-ready"].exists)
        app.buttons["timing-skip"].tap()
        XCTAssertTrue(app.buttons["controller-ready"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["tennisToss"].exists)
        XCTAssertFalse(app.buttons["tennisDive"].exists)
        app.buttons["controller-ready"].tap()
        XCTAssertFalse(app.buttons["controller-ready"].exists)
        launch("serve")
        XCTAssertTrue(app.buttons["tennisToss"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["tennisDive"].exists)
        XCTAssertFalse(app.buttons["controller-emote-0"].exists)
        launch("rally")
        XCTAssertTrue(app.buttons["tennisDive"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["tennisDive"].isEnabled)
        XCTAssertFalse(app.buttons["tennisToss"].exists)
        launch("point")
        XCTAssertTrue(app.buttons["controller-emote-0"].waitForExistence(timeout: 5))
        XCTAssertFalse(app.buttons["tennisDive"].exists)
        XCTAssertFalse(app.buttons["tennisToss"].exists)
    }
    func testConnectedPhone''',1))
p='Unity/Assets/Tests/PlayMode/NativeTennisSetupTests.cs'
(r/p).write_text('''using System.Collections;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests {
    public sealed class NativeTennisSetupTests {
        [UnityTest] public IEnumerator CalibrationHoldsPointPlayUntilReadyWithoutATutorial() {
            yield return SceneManager.LoadSceneAsync("Tennis", LoadSceneMode.Single);
            yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>();
            game.NativeControlled = true;
            game.ConfigureMatch(TennisGame.Mode.Tutorial, null, null, null);
            yield return null;
            Assert.That(game.PlayMode, Is.EqualTo(TennisGame.Mode.Exhibition));
            Assert.That(game.GetComponent<TennisTutorial>(), Is.Null);
            game.SetControllerSetup(true);
            Vector3 ball = game.BallPosition;
            var phase = game.Flow;
            for (int i = 0; i < 120; i++) game.Step(1f/120);
            game.Toss(1); game.RequestSwing(.8f);
            Assert.That(game.BallPosition, Is.EqualTo(ball));
            Assert.That(game.Flow, Is.EqualTo(phase));
            Assert.That(game.CanDive, Is.False);
            Assert.That(game.AimPractice, Is.False);
            game.StartTimingCheck();
            Assert.That(game.CheckingTiming, Is.True);
            game.RequestSwing(.8f); // The phone's swing reaches the timing check while play is held.
            game.CancelTimingCheck();
            Assert.That(game.ControllerSetup, Is.True);
            Assert.That(game.CheckingTiming, Is.False);
            game.SetControllerSetup(false);
            Assert.That(game.ControllerSetup, Is.False);
            game.Toss(1);
            for (int i = 0; i < 120; i++) game.Step(1f/120);
            Assert.That(game.Flow, Is.EqualTo(TennisGame.Phase.PlayerServeToss));
        }
    }
}
''');files.append(p)
meta=p+'.meta';(r/meta).write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n');files.append(meta)
m.write_text(json.dumps(files,indent=2))
a=r/'work/golf-look/device/combined/Source'
for f in files:
 dest=a/f;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r/f,dest)
print('Synced',len(files),'owned files')
