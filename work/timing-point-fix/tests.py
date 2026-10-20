from pathlib import Path
import json,uuid,shutil
r=Path.cwd();m=r/'work/timing-point-fix/changes.json';fs=json.loads(m.read_text())
def update(f,fn):
 p=r/f;p.write_text(fn(p.read_text()))
 if f not in fs:fs.append(f)
update('Unity/Assets/Scripts/Tennis/TennisGame.cs',lambda s:s.replace('if (!lagPriorSet && NativeControlled', 'if ((!lagPriorSet || lag.Prior <= 0) && NativeControlled').replace('// 2B: reaction cam + auto emotes, then the next serve','// Six real seconds to see the score and select a celebration.').replace('$"{CallFor(call, toPlayer, winner)} · {Match.PointCall}"', 'gameWon ? $"{(setWon ? "SET" : "GAME")} · {Match.PlayerGames}–{Match.OpponentGames}" : $"{CallFor(call, toPlayer, winner)} · {Match.PointCall}"'))
update('GolfArcadeTests/SportsDelayProbeTests.swift',lambda s:s.replace('while t < rendered + 0.9','while t < rendered + 1.3').replace('rendered - 0.35','rendered - 1.25').replace('rendered + 0.25','rendered + 0.45').replace('[0.05, 0.12, 0.18, 0.26, 0.4]', '[0.05, 0.12, 0.18, 0.26, 0.4, 0.68, 0.9]').replace('?? 0, 0.16, accuracy: 1e-9','?? 0, 0.15, accuracy: 1e-9').replace('    func testMedianNeedsTwoReadings()', '''    func testInconsistentFlashReadingsAreRejected() {
        XCTAssertNil(SportsDelayProbe.combine([0.1, 0.4]))
        XCTAssertEqual(SportsDelayProbe.combine([0.69, 0.7, 0.71, 0.12]) ?? 0, 0.7, accuracy: 1e-9)
    }
    func testTimingStorageKeepsLongAirPlayDelayAndIgnoresOldRhythmOnlyResults() {
        let defaults = UserDefaults(suiteName: "timing-\\(UUID())")!
        defaults.set(["TV": 0.05], forKey: "sports.tv.timing.v1")
        XCTAssertNil(SportsTiming.stored(for: "TV", defaults: defaults))
        SportsTiming.store(0.72, for: "TV", defaults: defaults)
        XCTAssertEqual(SportsTiming.stored(for: "TV", defaults: defaults), 0.72)
    }
    @MainActor func testFlashesRunBeforeTheSwingCheck() {
        let session = SportsSession()
        session.active = true; session.ready = true; session.displayConnected = true
        session.sport = "tennis"; session.touch = false; session.loading.cancel()
        session.offerTimingCalibration()
        XCTAssertTrue(session.measuringDelay)
        XCTAssertFalse(session.timingPrompt)
        session.startTimingCheck()
        XCTAssertFalse(session.checkingTiming)
        XCTAssertTrue(session.paused)
        session.active = false; session.motion.setDelayProbe(false)
    }
    func testMedianNeedsTwoReadings()'''))
update('GolfArcadeTests/TennisCampaignTests.swift',lambda s:s.replace('XCTAssertEqual(SportsTiming.stored(for: "Bedroom", defaults: defaults), 0.35, "clamped to what the game compensates")','XCTAssertEqual(SportsTiming.stored(for: "Bedroom", defaults: defaults), 0.9, "AirPlay delay is preserved")'))
update('Unity/Assets/Tests/PlayMode/NativeTennisSetupTests.cs',lambda s:s.replace('using System.Collections;','using System.Collections;\nusing System.Reflection;\nusing System.IO;').replace('''            game.SetControllerSetup(true);
            Vector3 ball = game.BallPosition;''','''            game.DisplayLatency = .72f;
            game.SetControllerSetup(true);
            Vector3 ball = game.BallPosition;''',1).replace('''            Assert.That(game.CheckingTiming, Is.False, "The TV calibration must finish without starting a point");''','''            Assert.That(game.CheckingTiming, Is.False, "The TV calibration must finish without starting a point");
            Assert.That(game.Lag, Is.EqualTo(.72f).Within(.001f), "A failed rhythm check must preserve the measured screen delay");''',1).replace('        [UnityTest] public IEnumerator CalibrationHolds', '''        [UnityTest] public IEnumerator PointWinnerStaysVisibleAndCelebrationsHoldTheNextServe() {
            yield return SceneManager.LoadSceneAsync("Tennis", LoadSceneMode.Single);
            yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>();
            game.NativeControlled = true; game.ManualSimulation = true;
            var hud = game.GetComponent<TennisHud>();
            var award = typeof(TennisGame).GetMethod("AwardPoint", BindingFlags.Instance | BindingFlags.NonPublic);
            foreach (bool won in new[] { true, false }) {
                game.ConfigureMatch(TennisGame.Mode.Exhibition, null, "RIVAL", null);
                game.SetControllerSetup(true); game.SetControllerSetup(false);
                award.Invoke(game, new object[] { won, false });
                for (int frame = 0; frame < 8; frame++) { hud.Refresh(game); yield return null; }
                Assert.That(game.ScoreOnlyText, Is.True);
                Assert.That(hud.PointResultText, Is.EqualTo((won ? hud.PlayerName : hud.OpponentName).ToUpperInvariant() + " SCORED"));
                string dir = System.Environment.GetEnvironmentVariable("GAMEPLAY_PROOF_DIR") ?? "Library/Captures/timing-point-fix";
                Directory.CreateDirectory(dir); GameCapture.Save(dir + (won ? "/point-you.png" : "/point-rival.png"), 1280, 720);
                for (int i = 0; i < 600; i++) game.Step(TennisGame.GameSpeed / 120f);
                Assert.That(game.Flow, Is.EqualTo(TennisGame.Phase.PointOver), "Point stays open for at least five real seconds");
                Assert.That(game.EmoteWindow, Is.EqualTo(won ? "point" : ""));
                game.HoldNextPoint(3f * TennisGame.GameSpeed);
                for (int i = 0; i < 240; i++) game.Step(TennisGame.GameSpeed / 120f);
                Assert.That(game.Flow, Is.EqualTo(TennisGame.Phase.PointOver), "A late celebration extends the point break");
                for (int i = 0; i < 180; i++) game.Step(TennisGame.GameSpeed / 120f);
                Assert.That(game.Flow, Is.Not.EqualTo(TennisGame.Phase.PointOver));
            }
        }
        [UnityTest] public IEnumerator CalibrationHolds''',1))
f='Unity/Assets/Tests/EditMode/ScreenTimingCalibrationTests.cs';(r/f).write_text('''using GolfArcade.Tennis;
using NUnit.Framework;

public sealed class ScreenTimingCalibrationTests {
    [Test] public void LongDisplayDelayDoesNotAssignSwingsToTheNextBounce() {
        var check = new TennisBeatCalibration(10, 0, .8f);
        for (int beat = 0; beat < TennisBeatCalibration.Beats; beat++)
            Assert.That(check.Swing(check.BeatTime(beat) + .9f), Is.EqualTo(beat));
        Assert.That(check.TryResult(out float measured), Is.True);
        Assert.That(measured, Is.EqualTo(.9f).Within(.001f));
        Assert.That(check.Finished(check.BeatTime(8) + .9f), Is.False, "Allow the final delayed bounce to be seen and swung at");
    }
    [Test] public void CompensationDoesNotTruncateLongAirPlayDelayTo350ms() {
        var lag = new TennisLagLearner { Prior = .72f };
        Assert.That(lag.Estimate, Is.EqualTo(.72f).Within(.001f));
    }
}
''');fs.append(f);meta=f+'.meta';(r/meta).write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n');fs.append(meta)
m.write_text(json.dumps(fs,indent=2));(r/'work/timing-point-fix/owned-paths.txt').write_text('\n'.join(fs)+'\n')
a=r/'work/golf-look/device/combined/Source'
for f in fs:
 p=a/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r/f,p)
p=a/'flow-tests.yml';s=p.read_text().replace('sources: [GolfArcadeTests/MenuFlowRegressionTests.swift]', 'sources: [GolfArcadeTests/MenuFlowRegressionTests.swift, GolfArcadeTests/SportsDelayProbeTests.swift]');p.write_text(s)
print('Synced',len(fs),'owned files')
