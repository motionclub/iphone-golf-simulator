using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using GolfArcade.Game;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    public sealed class ControllerTimingRegressionTests
    {
        static readonly BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
        static readonly MethodInfo RenderHero = typeof(HeroTennisDriver).GetMethod("LateUpdate", Private);
        static readonly FieldInfo TossClock = typeof(TennisGame).GetField("phaseTimer", Private);
        static readonly FieldInfo TossFall = typeof(TennisGame).GetField("tossFall", Private);
        static readonly FieldInfo Hand = typeof(NativeSportsSession).GetField("<Left>k__BackingField", BindingFlags.Static | BindingFlags.NonPublic);
        [TearDown] public void RestoreHand() => Hand.SetValue(null, false);
        static void Step(TennisGame game)
        {
            game.Step(TennisBall.Step);
            var hero = game.Player.GetComponentInChildren<HeroTennisDriver>();
            if (hero) RenderHero.Invoke(hero, null);
        }

        [UnityTest]
        public IEnumerator OnTimePhoneServeMakesRealContactAcrossScreenDelaysAndCharacters()
        {
            yield return SceneManager.LoadSceneAsync("Tennis", LoadSceneMode.Single);
            yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>();
            game.NativeControlled = true;
            // Advance manually, but retain the production conversion from real controller
            // time to the slower serve clock. Disable Update to avoid a second simulation.
            game.ManualSimulation = false; game.enabled = false;
            game.GetComponent<TennisPresentation>().Finish();
            var failures = new List<string>();
            foreach (bool female in new[] { false, true })
            foreach (bool left in new[] { false, true })
            // Up to the longest TV delay the game compensates (TennisLagLearner.Max): past ~0.3 s the toss falls more slowly
            // after its top (TennisRules.ServeFallGravity), so the on-time swing still meets it and is not caught first.
            foreach (float delay in new[] { 0f, .18f, .25f, .4f, .6f, .7f, .85f, TennisLagLearner.Max })
            foreach (float toss in new[] { 1f, .85f })
            {
                Hand.SetValue(null, left);
                game.SelectCharacter(female);
                game.ConfigureMatch(TennisGame.Mode.Exhibition, null, null, null);
                game.SetControllerSetup(true); game.SetControllerSetup(false);
                game.StartPlayerServe(); game.DisplayLatency = delay;
                game.Toss(toss);
                for (int i = 0; i < 600 && game.Flow != TennisGame.Phase.PlayerServeToss; i++) Step(game);
                Assert.That(game.Flow, Is.EqualTo(TennisGame.Phase.PlayerServeToss));
                if (delay <= .25f) Assert.That((float)TossFall.GetValue(game), Is.EqualTo(9.81f), $"normal TV delays keep the toss as it was (delay {delay})");
                int misses = game.HonestMisses;
                const float deliveryAge = .02f;
                float onset = TennisRules.ServeApex + (delay + TennisRules.ServeOnsetLatency + deliveryAge) * TennisRules.ServePace;
                while ((float)TossClock.GetValue(game) < onset && game.Flow == TennisGame.Phase.PlayerServeToss) Step(game);
                game.BeginSwing(0, .3f, 1, deliveryAge);
                Assert.That(game.Player.Swinging, Is.True, "The detected stroke must animate immediately");
                for (int i = 0; i < 8; i++) Step(game);
                game.RequestSwing(.8f, 0, .3f, 1, deliveryAge);
                for (int i = 0; i < 240 && game.Flow == TennisGame.Phase.PlayerServeToss; i++) Step(game);
                string result = $"female={female} left={left} delay={delay:F2} toss={toss:F2} fall={(float)TossFall.GetValue(game):F2} shots={game.RallyShots} misses={game.HonestMisses - misses} gap={game.LastContactGap:F3} {game.Feedback}";
                Debug.Log("[ControllerTimingRegression] " + result);
                if (game.RallyShots != 1 || game.HonestMisses != misses || game.LastContactGap > TennisGame.HonestContactGap)
                    failures.Add(result);
            }
            Assert.That(failures, Is.Empty, string.Join("\n", failures));
        }

        [UnityTest] public IEnumerator SwingCheckCanCorrectAnIncorrectFlashMeasurement()
        {
            yield return SceneManager.LoadSceneAsync("Tennis", LoadSceneMode.Single);
            yield return null;
            var game=Object.FindFirstObjectByType<TennisGame>(); game.enabled=false;
            game.SetControllerSetup(true); game.DisplayLatency=.72f;
            var check=new TennisBeatCalibration(Time.unscaledTime-20,0,.72f);
            for(int i=0;i<TennisBeatCalibration.Beats;i++) check.Swing(check.BeatTime(i)+.18f);
            typeof(TennisGame).GetField("calibration",Private).SetValue(game,check);
            typeof(TennisGame).GetMethod("TickTimingCheck",Private).Invoke(game,null);
            Assert.That(game.CheckingTiming,Is.False);
            Assert.That(game.Lag,Is.EqualTo(.18f).Within(.001f),"A consistent swing measurement must replace a bad flash result");
            Assert.That(game.ControllerSetup,Is.True);
        }

        [UnityTest] public IEnumerator EmptySwingCheckCannotReportSuccessFromAnOldFlash()
        {
            yield return SceneManager.LoadSceneAsync("Tennis", LoadSceneMode.Single);
            yield return null;
            var game=Object.FindFirstObjectByType<TennisGame>(); game.enabled=false;
            game.SetControllerSetup(true); game.DisplayLatency=.72f;
            var check=new TennisBeatCalibration(Time.unscaledTime-20,0,.72f);
            typeof(TennisGame).GetField("calibration",Private).SetValue(game,check);
            float reported=0;
            System.Action<float> receive=result=>reported=result;
            TennisGame.TimingChecked+=receive;
            try { typeof(TennisGame).GetMethod("TickTimingCheck",Private).Invoke(game,null); }
            finally { TennisGame.TimingChecked-=receive; }
            Assert.That(reported,Is.EqualTo(-1));
            Assert.That(game.Lag,Is.EqualTo(.72f).Within(.001f),"A failed check preserves the previous usable measurement");
        }

        /// Swing prediction (latency plan B2): a rally stroke reported at onset that proves itself strikes the ball without
        /// waiting for the phone's confirmation. One that is neither proven nor confirmed never hits, and one written off
        /// before it reaches the ball is cancelled: a step or a flinch cannot hit.
        [UnityTest] public IEnumerator ProvenOnsetStrikesWithoutConfirmationAndAWriteOffCancelsIt()
        {
            yield return SceneManager.LoadSceneAsync("Tennis", LoadSceneMode.Single);
            yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>();
            game.ManualSimulation = true; game.NativeControlled = true;
            game.ConfigureMatch(TennisGame.Mode.Training, null, null, null);
            game.DisplayLatency = 0;
            var failures = new List<string>();
            foreach (float at in new[] { .6f, .7f, .8f })
            foreach (string path in new[] { "proven", "onset only", "proven, written off" })
            {
                game.Player.CancelSwing(); game.Player.Tick(1, 0);
                game.Player.transform.position = new Vector3(0, .035f, -11.2f);
                game.InjectBall(new Vector3(0, 1.3f, 6), new Vector3(0, 2.2f, -16.5f));
                int before = game.Returns; bool swung = false, proven = false;
                for (float t = 0; t < 2f && game.Returns == before; t += TennisBall.Step)
                {
                    if (!swung && t >= at) { swung = true; game.BeginSwing(0, 0, 1); }
                    if (swung && !proven && t >= at + .01f)
                    {
                        proven = true;
                        if (path != "onset only") game.SwingProven();
                        if (path == "proven, written off") game.AbortSwing();
                    }
                    game.Step(TennisBall.Step);
                }
                bool returned = game.Returns > before;
                if (returned != (path == "proven")) failures.Add($"at={at:0.00} {path}: returned={returned} ({game.Feedback})");
            }
            Assert.That(failures, Is.Empty, string.Join("\n", failures));
            Assert.That(game.ProvenWriteOffs, Is.Zero, "no proven stroke was written off after it struck");
        }

        [UnityTest] public IEnumerator LatestPacketRetainsStrokeAgeAndIgnoresAnOlderAbort()
        {
            yield return SceneManager.LoadSceneAsync("Tennis", LoadSceneMode.Single);
            yield return null;
            var game=Object.FindFirstObjectByType<TennisGame>();
            game.enabled=false; game.NativeControlled=true; game.ManualSimulation=true;
            game.SetControllerSetup(true); game.SetControllerSetup(false); game.DisplayLatency=0;
            game.InjectBall(game.Player.transform.position+new Vector3(.6f,1.3f,2),new Vector3(0,0,-8));
            var root=new GameObject("Controller packet test");
            var adapter=root.AddComponent<NativeSportsSession>(); adapter.enabled=false;
            typeof(NativeSportsSession).GetField("tennis",Private).SetValue(adapter,game);
            typeof(NativeSportsSession).GetField("paused",Private).SetValue(adapter,false);
            typeof(NativeSportsSession).GetField("resumedAt",Private).SetValue(adapter,100d);
            var apply=typeof(NativeSportsSession).GetMethod("ApplySample",Private);
            var packet=new NativeSportsSession.Sample { version=NativeSportsSession.Sample.Version,session=1,time=100.2,flags=1,
                swingStart=2,swing=1,swingAbort=1,power=.8f,onsetTime=100.05,confirmationTime=100.13,abortTime=100.04 };
            apply.Invoke(adapter,new object[]{packet,100.21d});
            Assert.That(game.Player.Swinging,Is.True);
            Assert.That(game.Player.Provisional,Is.False,"An abort belonging to the previous candidate cannot cancel a newer confirmed stroke");
            // Since the paced catch-up (latency plan B5) the swing jumps at most CatchUpJump and plays the rest faster, so the
            // compensation shows in the advance it is graded with, not in how far the clip jumped.
            Assert.That((float)typeof(TennisGame).GetField("swingAdvance",Private).GetValue(game),Is.GreaterThan(.1f),"The newest packet must compensate the original onset age, rather than restamping it as zero");
            game.AbortSwing(); game.Player.CancelSwing();
            packet.time=100.24; packet.swingStart=3; packet.swing=2; packet.onsetTime=99.8; packet.confirmationTime=99.9;
            apply.Invoke(adapter,new object[]{packet,100.25d});
            Assert.That(game.Player.Swinging,Is.False,"Fresh controller state cannot revive a stroke from before Ready");
            Object.Destroy(root);
        }
    }
}
