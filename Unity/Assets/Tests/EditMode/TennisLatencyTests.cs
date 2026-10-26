using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// Latency plan P1 (docs/PLAN_Tennis_Latency_Online_Local.md): rally onset compensation, the paced catch-up that
    /// replaced the one-frame jump onto the ball, and the lag learner fed with a camera prior.
    public class TennisLatencyTests
    {
        [Test] public void RallyStrokesCarryTheDetectorsDelayLikeTheServe()
        {
            Assert.AreEqual(TennisRules.ServeOnsetLatency, TennisRules.SwingDetectionLatency(true, true));
            Assert.AreEqual(TennisRules.ServeOnsetLatency, TennisRules.SwingDetectionLatency(true, false), "onset is only ever reported by the phone");
            Assert.AreEqual(TennisRules.ServeLatency, TennisRules.SwingDetectionLatency(false, true));
            Assert.AreEqual(0, TennisRules.SwingDetectionLatency(false, false), "keys and tests are instant");
        }

        [Test] public void SmallShiftIsStillOnePlainJump()
        {
            float jump = TennisRules.CatchUp(.2f, .03f, out float pace, out float late);
            Assert.AreEqual(.03f, jump, 1e-5f);
            Assert.AreEqual(1, pace, 1e-5f);
            Assert.AreEqual(0, late, 1e-5f);
            Assert.AreEqual(0, TennisRules.CatchUp(.2f, 0, out pace, out late));
            Assert.AreEqual(1, pace);
        }

        [Test] public void BigShiftJumpsLittleAndPacesTheRestWithoutChangingTheGrade()
        {
            for (float left = .1f; left <= .26f; left += .02f)
                for (float shift = 0; shift <= .4f; shift += .01f)
                {
                    float jump = TennisRules.CatchUp(left, shift, out float pace, out float late);
                    float arrive = (left - jump) / pace;
                    float oldArrive = left - Mathf.Max(0, Mathf.Min(shift, left - TennisRules.CatchUpOldFloor));
                    string at = $"left={left:0.00} shift={shift:0.00} jump={jump:0.000} pace={pace:0.00}";
                    Assert.GreaterOrEqual(jump, 0, at);
                    Assert.GreaterOrEqual(pace, 1 - 1e-4f, at);
                    Assert.LessOrEqual(pace, TennisRules.CatchUpPace + 1e-4f, at);
                    Assert.GreaterOrEqual(arrive, Mathf.Min(left, TennisRules.CatchUpFloor) - 1e-4f, at + " never sooner than the floor");
                    Assert.LessOrEqual(arrive, left + 1e-4f, at);
                    // Grading takes `late` back off: the swing is judged on the old one-jump timeline exactly.
                    Assert.AreEqual(oldArrive, arrive - late, 1e-4f, at);
                    if (shift > TennisRules.CatchUpJump && left - shift < TennisRules.CatchUpFloor)
                        Assert.Less(jump, left - TennisRules.CatchUpOldFloor - 1e-3f, at + " no longer skips the approach");
                }
        }

        [Test] public void TypicalAirPlayDelayKeepsAVisibleApproach()
        {
            // A fast forehand (0.157 s to contact) with 150 ms of TV delay, 30 ms of delivery and the 40 ms onset.
            float left = TennisRules.SweetTime * .40f / TennisRules.StrokeDuration, shift = (.15f + .03f + .04f) * 1.1f;
            float jump = TennisRules.CatchUp(left, shift, out float pace, out _);
            Assert.LessOrEqual(jump, TennisRules.CatchUpJump + 1e-4f);
            Assert.AreEqual(TennisRules.CatchUpFloor, (left - jump) / pace, 1e-4f, "the racket still travels for ~4 frames at 60 Hz");
        }

        /// P1b (B2): feed (seconds after onset, rad/s) samples of one stroke; the time of the sample that proves it, or -1.
        static float ProvenAfter(params (float t, float rate)[] samples)
        {
            var strength = new TennisRules.OnsetStrength();
            float at = -1;
            foreach (var s in samples)
                if (strength.Add(1, 100, 100 + s.t, s.rate)) { Assert.AreEqual(-1, at, "proven once per stroke"); at = s.t; }
            return at;
        }

        [Test] public void AStrongDeviceSwingIsProvenBeforeThePhoneConfirmsIt()
        {
            // A real forehand from the swingtrace log (work/timing-point-fix/phone-before.log). Today's detector confirms it at
            // its peak, 51 ms after onset (work/tennis-latency-p1b/replay_swingtrace.py); it has proven itself by 30 ms.
            float at = ProvenAfter((0, 9.6f), (.01f, 11.8f), (.021f, 13.5f), (.03f, 14.7f), (.042f, 15.4f), (.051f, 15.6f));
            Assert.AreEqual(.03f, at, 1e-4f);
        }

        [Test] public void StepsAndFlinchesAreNeverProven()
        {
            // The one candidate in the device log the phone wrote off: it never gets near the rate or the turn.
            Assert.AreEqual(-1, ProvenAfter((0, 4.8f), (.01f, 4.5f), (.02f, 4.1f), (.03f, 3.7f), (.04f, 3.2f), (.05f, 2.7f), (.06f, 2.1f),
                (.07f, 1.7f), (.08f, 1.4f), (.09f, 1.2f), (.1f, 1.2f), (.11f, 1.3f), (.12f, 1.5f), (.13f, 1.7f), (.14f, 1.9f), (.15f, 2f),
                (.16f, 2.2f), (.17f, 2.4f), (.18f, 2.5f), (.19f, 2.6f)));
            // A brisk step: plenty of turn, never a stroke's rate.
            var step = new (float, float)[30];
            for (int i = 0; i < step.Length; i++) step[i] = (i * .01f, 6.5f);
            Assert.AreEqual(-1, ProvenAfter(step));
            // A flinch: one fast sample, not enough turn behind it.
            Assert.AreEqual(-1, ProvenAfter((0, 5f), (.01f, 12f), (.02f, 3f), (.03f, 1f), (.04f, .5f)));
        }

        [Test] public void OnsetStrengthStartsAgainForEachStrokeAndIgnoresOlderSamples()
        {
            var strength = new TennisRules.OnsetStrength();
            Assert.IsFalse(strength.Add(0, 0, 99, 20), "no onset yet");
            Assert.IsFalse(strength.Add(1, 100, 99.99, 20), "a sample from before the onset does not count");
            Assert.IsFalse(strength.Add(1, 100, 100.02, 10));
            Assert.IsTrue(strength.Add(1, 100, 100.04, 10));
            Assert.IsFalse(strength.Add(1, 100, 100.06, 10), "reported once");
            Assert.IsFalse(strength.Add(2, 101, 101.02, 10), "the next stroke builds its own turn");
            Assert.IsTrue(strength.Add(2, 101, 101.04, 10));
        }

        [Test] public void ProvenThresholdsMatchThePhonesPeakConfirmation()
        {
            string filter = System.IO.File.ReadAllText(System.IO.Path.Combine(Application.dataPath, "../../GolfArcade/Unity/SteeringFilter.swift"));
            StringAssert.Contains($"peakConfirmRate = {TennisRules.ProvenRate:0.0}", filter);
            StringAssert.Contains($"peakArc = {TennisRules.ProvenArc:0.0}", filter);
        }

        [Test] public void SlowTvTossFallsSlowlyEnoughForTheOnTimeSwing()
        {
            // The serve's toss tops out ~1.9 m above the hand; the strike point is ~0.9 m above it.
            const float drop = 1f, pace = TennisRules.ServePace;
            Assert.AreEqual(9.81f, TennisRules.ServeFallGravity(0, drop, pace), "no delay: the toss as it was");
            Assert.AreEqual(9.81f, TennisRules.ServeFallGravity(.25f, drop, pace), "AirPlay-like delays: the toss as it was");
            float before = 9.81f;
            for (float lag = .3f; lag <= TennisLagLearner.Max + 1e-4f; lag += .05f)
            {
                float g = TennisRules.ServeFallGravity(lag, drop, pace);
                Assert.LessOrEqual(g, before, $"lag {lag:0.00}: a longer delay never falls faster");
                float fall = Mathf.Sqrt(2 * drop / g), swing = (lag + TennisRules.ServeSwingReport) * pace;
                Assert.GreaterOrEqual(fall, swing + TennisRules.ServeLateReach - 1e-4f, $"lag {lag:0.00}: the ball is still above the strike point when the swing arrives");
                before = g;
            }
            Assert.AreEqual(TennisRules.ServeFallGravity(TennisLagLearner.Max, drop, pace), TennisRules.ServeFallGravity(3, drop, pace), "capped at the longest delay compensated");
        }

        [Test] public void LagLearnerKeepsLearningWithACameraPrior()
        {
            var learner = new TennisLagLearner { Prior = .15f };
            for (int i = 0; i < 9; i++) learner.Observe(.21f + (i % 3 - 1) * .02f);
            Assert.AreEqual(.21f, learner.Estimate, .021f, "rally evidence outvotes the two prior votes");
            learner.Observe(.9f);
            Assert.AreEqual(.21f, learner.Estimate, .021f, "a panicked swing is ignored");
        }
    }
}
