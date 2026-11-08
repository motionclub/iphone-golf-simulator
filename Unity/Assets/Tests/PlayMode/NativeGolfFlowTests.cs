using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using GolfArcade.Game;

namespace GolfArcade.PlayTests {
    public sealed class NativeGolfFlowTests {
        GolfGame game;
        [UnityTest, Timeout(180000)] public IEnumerator PhoneCommandsAimChangeClubsPauseAndLaunchWithoutCalibration() {
            yield return UnityEngine.SceneManagement.SceneManager.LoadSceneAsync("Golf");
            yield return null;
            game=Object.FindFirstObjectByType<GolfGame>(); game.PrepareNativeAddress();
            var host = new GameObject("NativeSportsSession");
            var bridge = host.AddComponent<NativeSportsSession>();
            // This fixture supplies samples directly; the editor's native ring is
            // empty, so leave its polling/watchdog loop out of the command test.
            bridge.enabled=false;
            const string id = "golf-controller-live-check";
            // Exercise production command/sample handling on a loaded course. The
            // batch runner has no Game view, so the separate display-ready gate is
            // deliberately outside this controller regression test's fixture.
            var fields=System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic;
            typeof(NativeSportsSession).GetField("session",fields).SetValue(bridge,id);
            typeof(NativeSportsSession).GetField("golf",fields).SetValue(bridge,game);
            typeof(NativeSportsSession).GetField("touch",fields).SetValue(bridge,true);
            typeof(NativeSportsSession).GetProperty("Active").GetSetMethod(true).Invoke(null,new object[]{true});
            typeof(GolfGame).GetField("pendingNativeIntro",fields).SetValue(game,false);
            void Command(string action,float value=0,float value2=0) => bridge.Receive(JsonUtility.ToJson(
                new NativeSportsSession.Message {version=1,session=id,action=action,value=value,value2=value2}));
            try {
                Command("recalibrate"); Command("resume");
                for(int i=0;i<180 && game.Current!=GolfGame.State.Aim;i++) yield return null;
                Assert.AreEqual(GolfGame.State.Aim,game.Current);
                Assert.IsTrue(game.NativeShotReady,"Default golf must play without practice swings");
                yield return null; yield return null;
                var first=game.NativeControllerReading();
                Assert.IsNotNull(first); Assert.IsNotNull(first.ball); Assert.IsNotNull(first.pin);
                Command("club",1); var next=game.NativeControllerReading();
                Assert.AreEqual((first.clubIndex+1)%10,next.clubIndex);
                Assert.IsTrue(game.NativeShotReady,"Club selection must not disable the shot");
                Command("club",-1); Assert.AreEqual(first.clubIndex,game.NativeControllerReading().clubIndex);
                Command("golfAimDirection",.6f,.8f); yield return null; yield return null;
                var aimed=game.NativeControllerReading();
                Assert.That(aimed.direction.x,Is.EqualTo(.6f).Within(.01));
                Assert.That(aimed.direction.y,Is.EqualTo(.8f).Within(.01));
                Assert.That(aimed.landing.x,Is.GreaterThan(aimed.ball.x),"Landing preview must follow the rightward joystick");
                double heading=game.AimHeading;
                Command("pause"); Assert.AreEqual(0,Time.timeScale);
                Command("club",1); Command("golfAimDirection",-1,0);
                Assert.AreEqual(first.clubIndex,game.NativeControllerReading().clubIndex);
                Assert.That(game.AimHeading,Is.EqualTo(heading).Within(.001),"Paused controls cannot change the shot");
                Command("recalibrate"); Command("resume");
                Assert.AreEqual(1,Time.timeScale); Assert.IsTrue(game.NativeShotReady);
                yield return null;
                double now=Time.realtimeSinceStartupAsDouble;
                var sample=new NativeSportsSession.Sample {time=now,power=.65f,swing=1,flags=1};
                typeof(NativeSportsSession).GetMethod("ApplySample",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic)
                    .Invoke(bridge,new object[]{sample,now});
                Assert.AreEqual(GolfGame.State.Flight,game.Current);
                Assert.That(game.LastShot.Carry,Is.GreaterThan(1),"The selected club and heading must produce a real shot");
                Command("end"); Assert.IsFalse(NativeSportsSession.Active);
            } finally { Object.DestroyImmediate(host); Time.timeScale=1; }
        }
        /// Handheld play's aim pad is the TV controller sheet's joystick: a push turns the aim at the sheet's rate (not straight to
        /// where it points), pushing up flies the camera up the hole, and letting go (or a pause) stops both.
        [UnityTest, Timeout(180000)] public IEnumerator HandheldStickTurnsAtTheSheetsRateAndLooksUpTheHole() {
            yield return UnityEngine.SceneManagement.SceneManager.LoadSceneAsync("Golf");
            yield return null;
            game=Object.FindFirstObjectByType<GolfGame>(); game.PrepareNativeAddress();
            var host = new GameObject("NativeSportsSession");
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.enabled=false;
            const string id = "golf-handheld-stick-check";
            var fields=System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic;
            typeof(NativeSportsSession).GetField("session",fields).SetValue(bridge,id);
            typeof(NativeSportsSession).GetField("golf",fields).SetValue(bridge,game);
            typeof(NativeSportsSession).GetField("touch",fields).SetValue(bridge,true);
            typeof(NativeSportsSession).GetProperty("Active").GetSetMethod(true).Invoke(null,new object[]{true});
            typeof(GolfGame).GetField("pendingNativeIntro",fields).SetValue(game,false);
            void Command(string action,float value=0,float value2=0) => bridge.Receive(JsonUtility.ToJson(
                new NativeSportsSession.Message {version=1,session=id,action=action,value=value,value2=value2}));
            try {
                Command("recalibrate"); Command("resume");
                for(int i=0;i<180 && game.Current!=GolfGame.State.Aim;i++) yield return null;
                Assert.AreEqual(GolfGame.State.Aim,game.Current);
                // a small push inside the sheet's dead zone turns nothing
                double start=game.AimHeading;
                Command("golfStick",.15f,0); for(int i=0;i<10;i++) yield return null;
                Assert.That(game.AimHeading,Is.EqualTo(start).Within(.001),"A nudge inside the dead zone must not turn the aim");
                // a full push right for half a second: the sheet's sweep (1.5 x AimSweepDegreesPerSecond), not a jump to the side
                Command("golfStick",1,0);
                float began=Time.time; while(Time.time-began<.5f) yield return null;
                double turned=Mathf.DeltaAngle((float)start,(float)game.AimHeading), elapsed=Time.time-began;
                Assert.That(turned,Is.GreaterThan(0),"Pushing right turns the aim right");
                Assert.That(turned,Is.EqualTo(1.5*game.AimSweepDegreesPerSecond*elapsed).Within(1.5*game.AimSweepDegreesPerSecond*.1),"The turn follows the sheet's rate");
                Command("golfStick",0,0); double held=game.AimHeading;
                for(int i=0;i<10;i++) yield return null;
                Assert.That(game.AimHeading,Is.EqualTo(held).Within(.001),"Letting go stops the turn");
                // up on the stick: the camera climbs up the hole
                float before=game.GameplayCamera.transform.position.y;
                Command("golfStick",0,1);
                began=Time.time; while(Time.time-began<1f) yield return null;
                Assert.That(game.AimLook,Is.EqualTo(1).Within(.01),"Pushing up looks up the hole");
                Assert.That(game.GameplayCamera.transform.position.y,Is.GreaterThan(before+4),"The camera flies up to show where the shot goes");
                // a pause clears the stick: the view comes back down once play resumes
                Command("pause"); Command("recalibrate"); Command("resume");
                Assert.That(game.NativeStick,Is.EqualTo(Vector2.zero));
                began=Time.time; while(Time.time-began<1f) yield return null;
                Assert.That(game.AimLook,Is.EqualTo(0).Within(.01),"Let go (or paused), the view eases back to the ball");
            } finally { Object.DestroyImmediate(host); Time.timeScale=1; }
        }
        [UnityTest] public IEnumerator NativeRoundAcceptsAShotAndExitsWithoutOpeningTheLegacyMenu() {
            game = new GameObject("Native golf flow check").AddComponent<GolfGame>();
            yield return null;
            game.PrepareNativeAddress();
            yield return null;
            Assert.That(game.NativeControlled, Is.True);
            Assert.That(game.Current, Is.EqualTo(GolfGame.State.Aim));
            Assert.That(GameObject.Find("Menu"), Is.Null);
            Assert.That(game.TutorialHud.AimLeft.gameObject.activeSelf, Is.False);
            Assert.That(game.TutorialHud.SwingHold.gameObject.activeSelf, Is.False);
            Assert.That(game.Card, Is.Not.Null);
            game.NativeSwing(.65f);
            Assert.That(game.Current, Is.EqualTo(GolfGame.State.Flight));
            Assert.That(game.LastShot.Carry, Is.GreaterThan(10));
            Time.timeScale = 4;
            float deadline = Time.realtimeSinceStartup + 45;
            while (game.Current != GolfGame.State.Aim && game.Current != GolfGame.State.RoundDone && Time.realtimeSinceStartup < deadline)
            {
                if (game.Current == GolfGame.State.Result) game.NativeContinue();
                yield return null;
            }
            Assert.That(game.Current, Is.EqualTo(GolfGame.State.Aim).Or.EqualTo(GolfGame.State.RoundDone));
            // Finish a short putt through the normal shot/result/card flow, then advance
            // using the same command exposed on the phone controller.
            if (game.Current == GolfGame.State.Aim) {
                var hole = game.CurrentHole;
                var pin = hole.Pin;
                double distance = pin.DistanceTo(hole.Tee);
                game.DropBall(new GolfArcade.Course.CoursePoint(pin.X + (hole.Tee.X - pin.X) * 4 / distance, pin.D + (hole.Tee.D - pin.D) * 4 / distance));
                for (int putt = 0; putt < 4 && game.Current == GolfGame.State.Aim; putt++) {
                    game.StrikeHolingPutt();
                    deadline = Time.realtimeSinceStartup + 30;
                    while (game.Current != GolfGame.State.Aim && game.Current != GolfGame.State.RoundDone && Time.realtimeSinceStartup < deadline)
                    {
                        if (game.Current == GolfGame.State.Result) game.NativeContinue();
                        yield return null;
                    }
                }
            }
            Assert.That(game.Current, Is.EqualTo(GolfGame.State.RoundDone));
            int expectedHole = game.NativeHasNextHole ? game.TutorialHole + 1 : 0;
            game.NativeContinue();
            yield return null;
            // the next hole is built behind its loading screen (GolfGame.HoleLoading.cs)
            // and opens with its intro, which the phone's Continue skips
            for (deadline = Time.realtimeSinceStartup + 30; (game.LoadingHole || game.Current == GolfGame.State.Intro) && Time.realtimeSinceStartup < deadline;)
            {
                if (!game.LoadingHole && game.Current == GolfGame.State.Intro) game.NativeContinue();
                yield return null;
            }
            Assert.That(game.Current, Is.EqualTo(GolfGame.State.Aim));
            Assert.That(game.TutorialHole, Is.EqualTo(expectedHole));
            Assert.That(GameObject.Find("Menu"), Is.Null);
            bool exited = false;
            System.Action exit = () => exited = true;
            GolfGame.NativeExitRequested += exit;
            try {
                game.ShowMenu();
                Assert.That(exited, Is.True);
                Assert.That(game.enabled, Is.False);
                Assert.That(GameObject.Find("Menu"), Is.Null);
            } finally { GolfGame.NativeExitRequested -= exit; }
        }
        [UnityTest] public IEnumerator EveryNativeCourseStartsAtItsOwnFirstHole() {
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
        [UnityTearDown] public IEnumerator Cleanup() {
            Time.timeScale = 1;
            if (game) {
                Object.Destroy(game.GameplayCamera.gameObject);
                Object.Destroy(game.TutorialHud.gameObject);
                Object.Destroy(game.gameObject);
            }
            yield return null;
        }
    }
}
