using GolfArcade.Tennis;
using NUnit.Framework;

/// Quick tennis start (PLAN_Onboarding_Tutorial_TennisQuickStart_1121.md): the timing check's shorter countdown and early stop, and
/// when play's learned lag is worth keeping for the next match.
public sealed class TennisQuickStartTests {
    [Test] public void SteadySwingsEndTheTimingCheckEarly() {
        var check = new TennisBeatCalibration(10, TennisBeatCalibration.Countdown);
        Assert.That(TennisBeatCalibration.Countdown, Is.EqualTo(3f), "3 s to get ready (was 5 s)");
        int last = TennisBeatCalibration.WarmUp + TennisBeatCalibration.EarlyStop - 1;
        for (int beat = 0; beat < last; beat++) {
            check.Swing(check.BeatTime(beat) + .2f);
            Assert.That(check.Finished(check.BeatTime(beat) + .25f), Is.False, $"not settled after beat {beat}");
        }
        check.Swing(check.BeatTime(last) + .2f);
        Assert.That(check.Settled, Is.True);
        Assert.That(check.Finished(check.BeatTime(last) + .25f), Is.True, "five scored swings that agree end it");
        Assert.That(check.BeatTime(last) + .25f, Is.LessThan(check.End - 2), "at least two bounces sooner than the full check");
        Assert.That(check.TryResult(out float lag), Is.True);
        Assert.That(lag, Is.EqualTo(.2f).Within(.001f));
    }

    [Test] public void ScatteredSwingsStillRunTheWholeCheck() {
        var check = new TennisBeatCalibration(0);
        float[] scatter = { 0, 0, -.3f, .3f, -.25f, .28f, .0f, -.3f, .3f };
        for (int b = 0; b < TennisBeatCalibration.Beats; b++) check.Swing(check.BeatTime(b) + .2f + scatter[b]);
        Assert.That(check.Settled, Is.False);
        Assert.That(check.Finished(check.End - .01f), Is.False);
        Assert.That(check.Finished(check.End), Is.True);
    }

    [Test] public void LearnedLagIsKeptOnlyAfterEnoughOwnSwings() {
        var lag = new TennisLagLearner { Prior = .18f };
        for (int i = 0; i < TennisLagLearner.Trusted - 1; i++) lag.Observe(.22f);
        Assert.That(lag.Count, Is.LessThan(TennisLagLearner.Trusted));
        lag.Observe(.22f);
        Assert.That(lag.Count, Is.GreaterThanOrEqualTo(TennisLagLearner.Trusted));
        Assert.That(lag.Estimate, Is.EqualTo(.22f).Within(.001f), "five of the player's own swings outvote the prior's two");
    }
}
