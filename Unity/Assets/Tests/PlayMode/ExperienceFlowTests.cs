using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.PlayTests
{
    public class ExperienceFlowTests
    {
        const BindingFlags Private = BindingFlags.NonPublic | BindingFlags.Instance;
        static readonly string Proof = "work/experience/tests";
        [UnityTearDown] public IEnumerator Restore()
        {
            Time.captureFramerate = 0; Time.timeScale = 1; ExperienceTrace.Enabled = false;
            yield return null;
        }

        [UnityTest, Timeout(180000)]
        public IEnumerator OrdinaryResultsSkipAtHalfSecondAndAutoAdvanceAtThree()
        {
            Time.captureFramerate = 60; Time.timeScale = 1;
            yield return SceneManager.LoadSceneAsync("Golf"); yield return null;
            var game = Object.FindFirstObjectByType<GolfGame>();
            game.Demo = true; game.InstantReplays = false; game.ChooseHoles(0); game.Play(); game.JumpToHole(12);
            Directory.CreateDirectory(Proof);
            var times = new List<string> { "compressed,flightSeconds,duration,restX,restD,lie,penalty,skipAt" };
            CourseShot reference = null;
            foreach (bool compress in new[] { false, true })
            {
                game.CompressRunout = compress; game.DropBall(game.CurrentHole.Tee);
                var target = game.GreenTarget(5,18,7) ?? game.CurrentHole.RecommendedTarget(game.CurrentHole.Tee);
                float start = Time.time; game.StrikeToward(target);
                var shot = game.LastShot;
                Assert.NotNull(shot); Assert.False(shot.IsHoled);
                int frames = 0;
                while (game.Current == GolfGame.State.Flight && frames++ < 1800) yield return null;
                Assert.AreEqual(GolfGame.State.Result, game.Current);
                float duration = Time.time - start;
                if (reference != null) {
                    Assert.AreEqual(reference.Rest, shot.Rest); Assert.AreEqual(reference.Lie, shot.Lie);
                    Assert.AreEqual(reference.Duration, shot.Duration); Assert.AreEqual(reference.PenaltyStrokes, shot.PenaltyStrokes);
                    for (double t = 0; t <= shot.Duration; t += CourseShot.SampleInterval)
                        Assert.AreEqual(reference.PositionAt(t), shot.PositionAt(t), "presentation must preserve every path sample");
                }
                reference = shot;
                var age = typeof(GolfGame).GetField("stateTime", Private);
                age.SetValue(game, .499f); game.ContinueShotResult();
                Assert.AreEqual(GolfGame.State.Result, game.Current, "early tap must be rejected");
                age.SetValue(game, .5f);
                Assert.True(game.ResultCanContinue);
                times.Add(FormattableString.Invariant($"{compress},{duration:F5},{shot.Duration:F5},{shot.Rest.X:F5},{shot.Rest.D:F5},{shot.Lie},{shot.PenaltyStrokes},0.5"));
                if (!compress) { game.ContinueShotResult(); Assert.AreEqual(GolfGame.State.Aim, game.Current); }
                else {
                    age.SetValue(game, 2.95f); yield return null;
                    Assert.AreEqual(GolfGame.State.Result, game.Current, "automatic reading window stays three seconds");
                    for (int i=0; i<5 && game.Current==GolfGame.State.Result; i++) yield return null;
                    Assert.AreEqual(GolfGame.State.Aim, game.Current);
                }
                Assert.AreSame(shot, game.LastShot);
            }
            File.WriteAllLines(Path.Combine(Proof,"golf-pace.csv"), times);
        }

        [UnityTest, Timeout(180000)]
        public IEnumerator ResetsPlantBothHeroesAndAcceptTossWithoutWalkOrLivePerfectEmote()
        {
            Time.timeScale = 1; Time.captureFramerate = 60;
            yield return SceneManager.LoadSceneAsync("Tennis"); yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>();
            game.NativeControlled = true; game.AutoPlay = false; game.ManualSimulation = true; game.Drill = false;
            game.GetComponent<TennisPresentation>().Finish();
            var match = typeof(TennisGame).GetField("match", Private);
            var award = typeof(TennisGame).GetMethod("AwardPoint", Private);
            var lines = new List<string> { "female,sample,serveReadySeconds,tossAccepted" };
            foreach (bool female in new[] { false, true })
            {
                game.SelectCharacter(female); yield return null;
                for (int i = 0; i < 10; i++)
                {
                    var score = TennisMatch.New(true,1,3); score.PlayerPoints = i % 2;
                    match.SetValue(game,score); game.Refeed();
                    game.Player.transform.position = new Vector3(i%2==0?-4:4, game.Player.transform.position.y, -1);
                    award.Invoke(game,new object[] { false, false });
                    int ticks=0;
                    while (!game.ServeReady && ticks < 180) { game.Step(1f/120); ticks++; }
                    Assert.True(game.ServeReady, "meter-ready server within 1.5 seconds, even from net");
                    Assert.LessOrEqual(ticks/120f,1.5f);
                    var meter = GameObject.Find("Toss meter"); Assert.True(meter && meter.activeInHierarchy);
                    var driver = game.Player.GetComponentInChildren<HeroTennisDriver>();
                    driver.PlayJuice(HeroTennisDriver.Clip.HitPerfect); yield return null;
                    Assert.AreNotEqual(HeroTennisDriver.Clip.HitPerfect,driver.PlayingClip);
                    Vector3 feet = game.Player.transform.position;
                    game.Toss(1);
                    Assert.That((float)typeof(TennisGame).GetField("windup",Private).GetValue(game), Is.EqualTo(0));
                    game.Step(1f/120); Assert.That(Vector3.Distance(feet,game.Player.transform.position), Is.LessThan(.001f));
                    lines.Add($"{female},{i},{ticks/120f:F5},True");
                }
            }
            Directory.CreateDirectory(Proof);File.WriteAllLines(Path.Combine(Proof,"tennis-reset.csv"),lines);
        }

        [UnityTest, Timeout(180000)]
        public IEnumerator CupFeedbackOccursOnceAndLocalHoleCardKeepsItsReadingWindow()
        {
            Time.captureFramerate=60; Time.timeScale=1;
            yield return SceneManager.LoadSceneAsync("Golf"); yield return null;
            var game=Object.FindFirstObjectByType<GolfGame>();
            game.Demo=true;game.InstantReplays=false;game.ChooseHoles(0);game.Play();game.JumpToHole(12);
            var pin=game.CurrentHole.Pin;
            game.DropBall(new CoursePoint(pin.X,pin.D-3));
            Assert.True(game.StrikeHolingPutt());
            int ticks=0, cupEvents=0;
            ExperienceTrace.Enabled=true;
            void Mark(ExperienceTrace.Stamp e) { if(e.stage=="cup-feedback") cupEvents++; }
            ExperienceTrace.Recorded+=Mark;
            Directory.CreateDirectory(Proof);
            try {
                while(game.Current==GolfGame.State.Flight && ticks++<1800) {
                    yield return null;
                    if(game.PresentationFlightTime >= game.LastShot.HoledAt.Value-.12)
                        GameCapture.Save(Path.Combine(Proof,$"cup-{ticks:D4}.jpg"),1280,720);
                }
                for(int i=0;i<12;i++) { GameCapture.Save(Path.Combine(Proof,$"cup-result-{i:D2}.jpg"),1280,720);yield return null; }
                Assert.AreEqual(1,cupEvents,"one sound/haptic/ring event at the live crossing");
            } finally { ExperienceTrace.Recorded-=Mark; }
            Assert.True(game.LastShot.IsHoled); Assert.AreEqual(GolfGame.State.Result,game.Current);
            Assert.True((bool)typeof(GolfGame).GetField("cupFeedback",Private).GetValue(game));
            typeof(GolfGame).GetField("stateTime",Private).SetValue(game,.5f);
            game.ContinueShotResult(); Assert.AreEqual(GolfGame.State.Result,game.Current,"local hole-out policy remains three seconds");
        }

        [UnityTest, Timeout(180000)]
        public IEnumerator CompactCuesRemainVisibleInScoreOnlyAtThirtyAndSixtyFps()
        {
            Time.timeScale=1;
            yield return SceneManager.LoadSceneAsync("Tennis"); yield return null;
            var game=Object.FindFirstObjectByType<TennisGame>();
            game.NativeControlled=true;game.AutoPlay=false;game.ManualSimulation=true;
            game.GetComponent<TennisPresentation>().Finish();
            var hud=game.GetComponent<TennisHud>();
            Directory.CreateDirectory(Proof);
            foreach(int fps in new[]{30,60}) {
                Time.captureFramerate=fps; game.SelectCharacter(fps==30); yield return null;
                game.InjectBall(new Vector3(0,1,-6),Vector3.forward*12);
                var driver=game.Player.GetComponentInChildren<HeroTennisDriver>();
                driver.PlayJuice(HeroTennisDriver.Clip.HitPerfect);yield return null;
                Assert.AreNotEqual(HeroTennisDriver.Clip.HitPerfect,driver.PlayingClip,"live Rally must never use the full-body Perfect clip");
                var m=TennisMatch.New(true,1,3);m.OpponentPoints=3;
                Assert.True(TennisHud.IsBreakPoint(m));m.Tiebreak=true;Assert.False(TennisHud.IsBreakPoint(m));m.Tiebreak=false;
                foreach(int shots in new[]{4,8,12}) {
                    hud.RefreshAs(m,false,0,true,shots);hud.ShowCause("EARLY");
                    Assert.AreEqual(shots,hud.RallyCount);Assert.AreEqual("EARLY",hud.Cause);
                    GameCapture.Save(Path.Combine(Proof,$"tennis-{fps}-rally{shots}.jpg"),1280,720);
                }
                for(int j=0;j<Mathf.CeilToInt(.62f*fps);j++) yield return null;
                Assert.AreEqual("",hud.Cause,"hint must expire without holding play");
                hud.RefreshAs(m,false,0,true,0);Assert.AreEqual(0,hud.RallyCount);
                // Controlled FX variants in the real scene; these are not scored strokes.
                foreach(Timing grade in new[]{Timing.Good,Timing.Great,Timing.Perfect}) {
                    game.InjectBall(game.Player.SweetSpot.position,Vector3.forward*12);
                    for(int settle=0;settle<fps;settle++)yield return null;
                    game.GetComponentInChildren<TennisFx>().Contact(game.BallPosition,grade,false);
                    for(int f=0;f<6;f++) {
                        yield return null;
                        if(f==0 || f==3) GameCapture.Save(Path.Combine(Proof,$"tier-{fps}-{grade}-{f}.jpg"),1280,720);
                    }
                    for(int f=0;f<fps;f++)yield return null;
                }
            }
        }

        [UnityTest, Timeout(180000)]
        public IEnumerator WindDirectionAndWetLandingFollowTheExistingRules()
        {
            Time.timeScale=1;Time.captureFramerate=60;
            yield return SceneManager.LoadSceneAsync("Golf");yield return null;
            var game=Object.FindFirstObjectByType<GolfGame>();
            game.Demo=true;game.InstantReplays=false;game.ChooseHoles(0);game.Play();game.JumpToHole(12);game.DropBall(game.CurrentHole.Tee);
            Directory.CreateDirectory(Proof);
            foreach(double direction in new[]{90.0,-90.0}) {
                game.SetWind(new Wind(12,direction));yield return null;
                var hud=Object.FindFirstObjectByType<GolfArcade.UI.GolfShotHud>();
                var arrow=(RectTransform)typeof(GolfArcade.UI.GolfShotHud).GetField("windArrow",Private).GetValue(hud);
                double heading=(double)typeof(GolfGame).GetField("heading",Private).GetValue(game);
                Assert.That(Mathf.Abs(Mathf.DeltaAngle(arrow.localEulerAngles.z,-(float)game.Wind.RelativeTo(heading))),Is.LessThan(.1f));
                GameCapture.Save(Path.Combine(Proof,$"wind-{direction}.jpg"),1280,720);
            }
            typeof(GolfGame).GetMethod("ChangeWeather",Private).Invoke(game,new object[]{Weather.Rain});
            game.SetWind(Wind.Calm);
            var wet=typeof(GolfGame).GetMethod("WetLandingRules",Private);
            Assert.True((bool)wet.Invoke(game,new object[]{CourseLie.Green}));
            Assert.False((bool)wet.Invoke(game,new object[]{CourseLie.Ice}));
            game.StrikeToward(game.GreenTarget(5,18,7) ?? game.CurrentHole.Pin);
            int frames=0;
            while(game.Current==GolfGame.State.Flight && game.Bounces==0 && frames++<1200)yield return null;
            Assert.That(game.Bounces,Is.GreaterThan(0));
            GameCapture.Save(Path.Combine(Proof,"wet-landing.jpg"),1280,720);
            typeof(GolfGame).GetMethod("ChangeWeather",Private).Invoke(game,new object[]{Weather.Clear});
            Assert.False((bool)wet.Invoke(game,new object[]{CourseLie.Green}));
        }

        [UnityTest, Timeout(180000)]
        public IEnumerator WaterOverlapsTheResultAndCanContinueInHalfSecond()
        {
            Time.timeScale=1;Time.captureFramerate=30;
            yield return SceneManager.LoadSceneAsync("Golf");yield return null;
            var game=Object.FindFirstObjectByType<GolfGame>();
            game.PrepareNativeAddress();game.JumpToHole(12);game.DropBall(game.CurrentHole.Tee);
            typeof(GolfGame).GetMethod("SelectClub",Private).Invoke(game,new object[]{GolfArcade.Shot.GolfClub.Iron});
            game.NativeReady();game.NativeSwing(.55f);
            Assert.AreEqual(CourseLie.Water,game.LastShot.Lie);
            var shot=game.LastShot;
            int frames=0;while(game.Current==GolfGame.State.Flight && frames++<1800)yield return null;
            Assert.AreEqual(GolfGame.State.Result,game.Current);Assert.That(game.ResultAge,Is.LessThan(.04f));
            Assert.That((double)typeof(GolfGame).GetField("splashedAt",Private).GetValue(game),Is.GreaterThanOrEqualTo(0));
            Directory.CreateDirectory(Proof);
            GameCapture.Save(Path.Combine(Proof,"water-result.jpg"),1280,720);
            float resultAt=Time.time;
            while(!game.ResultCanContinue && Time.time-resultAt<1)yield return null;
            Assert.That(Time.time-resultAt,Is.InRange(.49f,.55f));
            game.ContinueShotResult();Assert.AreEqual(GolfGame.State.Aim,game.Current);
            Assert.AreSame(shot,game.LastShot);Assert.AreEqual(1,shot.PenaltyStrokes);
            File.WriteAllText(Path.Combine(Proof,"water.txt"),$"resultToAcceptedContinue={Time.time-resultAt:F5}; penalty={shot.PenaltyStrokes}; next={shot.NextPosition}");
        }

        [UnityTest, Timeout(180000)]
        public IEnumerator ChosenScubaCanFinishWhileTossRemainsReady()
        {
            Time.captureFramerate=60;Time.timeScale=1;
            yield return SceneManager.LoadSceneAsync("Tennis");yield return null;
            var game=Object.FindFirstObjectByType<TennisGame>();
            game.NativeControlled=true;game.AutoPlay=false;game.ManualSimulation=true;game.Drill=false;
            game.GetComponent<TennisPresentation>().Finish();game.EquipEmotes(new[]{"scuba","wave","spike"});
            var driver=game.Player.GetComponentInChildren<HeroTennisDriver>();
            foreach(bool interrupt in new[]{false,true}) {
                typeof(TennisGame).GetField("match",Private).SetValue(game,TennisMatch.New(true,1,3));game.Refeed();
                typeof(TennisGame).GetMethod("AwardPoint",Private).Invoke(game,new object[]{true,false});
                Assert.True(game.RequestEquippedEmote(0));
                int ticks=0;while(!game.ServeReady && ticks++<180)game.Step(1f/120);
                yield return null;
                Assert.True(game.ServeReady);Assert.True(driver.EmoteActive,"a chosen emote survives the reset without holding TOSS");
                if(interrupt) {
                    game.Toss(1);yield return null;
                    Assert.False(driver.EmoteActive,"TOSS takes over immediately");
                } else {
                    float start=Time.time;
                    int budget=Mathf.CeilToInt(driver.EmoteDuration(HeroTennisDriver.Clip.EmoteScuba)*60)+30;
                    while(driver.EmoteActive && budget-->0)yield return null;
                    Assert.False(driver.EmoteActive);Assert.True(game.ServeReady);
                    Assert.That(Time.time-start,Is.GreaterThan(1f),"the voluntary animation was not truncated at reset");
                }
            }
        }
    }
}
