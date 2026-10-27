using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// The Wii Sports rules (2026-10-26). Adnan: "everytime i make contact, the computer misses, and also half the time i
    /// make a good swing it misses ... easy contact, and quality of contact depending on timing and aim ... FUN IS ALL THAT
    /// MATTERS". These are the binary gates for the rival's side of that: it never gifts a point on a comfortable ball,
    /// placement (a clean ball into a lane) is what beats it, and a mistimed ball never does. Contact itself (every swing in
    /// the window hits, the character always gets there) is in TennisGame and is checked through the real game in PlayMode.
    public class TennisFunTests
    {
        const float StrikeZ = 10.55f;

        static readonly (string name, OpponentProfile profile)[] Ladder =
        {
            ("club", OpponentProfile.FromDifficulty(0f)),
            ("standard", OpponentProfile.FromDifficulty(TennisOpponent.DefaultDifficulty)),
            ("pro", OpponentProfile.FromDifficulty(1f)),
            ("wildcard", OpponentProfile.Rival("wildcard", .1f)),
            ("sniper", OpponentProfile.Rival("sniper", .7f)),
            ("boss", OpponentProfile.Rival("boss", 1f)),
        };

        [Test] public void AimSnapsToThreeLanes()
        {
            for (float aim = -1; aim <= 1.001f; aim += .01f)
            {
                float side = TennisRules.SideFromSwing(aim);
                Assert.IsTrue(side == -1 || side == 0 || side == 1, $"aim {aim} gave {side}");
            }
            Assert.AreEqual(0, TennisRules.SideFromSwing(.25f), "a wobbly wrist goes straight");
            Assert.AreEqual(1, TennisRules.SideFromSwing(.4f));
            Assert.AreEqual(-1, TennisRules.SideFromSwing(-.4f));
        }

        [Test] public void BadlyTimedShotsGoOut()
        {
            // Inside OutTiming every rally ball lands in; past it, out: wide on the side lane aimed at, long down the middle.
            for (float late = -.3f; late <= .3f; late += .01f)
                foreach (float aim in new[] { -.8f, 0f, .8f })
                    for (float roll = -1; roll <= 1; roll += .5f)
                    {
                        bool outBall = TennisRules.MistimedOut(late);
                        Assert.AreEqual(Mathf.Abs(late) > TennisRules.OutTiming, outBall);
                        if (!outBall) continue;
                        var land = TennisRules.MistimedLanding(aim, late, roll, -roll);
                        Assert.IsFalse(TennisRules.BounceIsIn(land), $"late {late} aim {aim}: {land}");
                        float side = TennisRules.SideFromSwing(aim);
                        if (side != 0) Assert.Greater(land.x * side, TennisRules.CourtHalfWidth, "wide on the side aimed at");
                        else Assert.Greater(land.z, TennisRules.CourtHalfLength, "long down the middle");
                        Assert.Less(Mathf.Abs(land.x), TennisRules.CourtHalfWidth + 2f, "out, but not absurdly");
                    }
            Assert.IsFalse(TennisRules.MistimedOut(.14f), "a GOOD swing never goes out");
            Assert.IsFalse(TennisRules.MistimedOut(-.14f));
        }

        [Test] public void TheRivalNeverGiftsAPointOnAComfortableBall()
        {
            // Lined up beside the ball (stretch up to .35 of its reach: the game stands it with the ball at its strings,
            // .65 m from its feet), rally pace up to a GOOD ball, waist high, struck as cleanly as you like, any roll.
            foreach (var (name, p) in Ladder)
                for (float stretch = 0; stretch <= .35f; stretch += .05f)
                    for (float pace = 0; pace <= .3f; pace += .1f)
                        for (float quality = 0; quality <= 1f; quality += .25f)
                            for (float roll = 0; roll < 1; roll += .05f)
                            {
                                var r = TennisOpponent.Decide(0, stretch * p.Reach, 0, 0, 0, p, roll, .5f, .5f, pace, p.Reach, 0, quality,
                                    false, TennisRules.BaselineZ, false, 0, TennisOpponent.Fatigue(TennisOpponent.FatigueStart));
                                Assert.IsTrue(r.Reached && !r.Error, $"{name}: stretch {stretch} pace {pace} quality {quality} roll {roll}: {r.Reason}");
                            }
        }

        [Test] public void ALongRallyWearsTheRivalDown()
        {
            Assert.AreEqual(0, TennisOpponent.Fatigue(TennisOpponent.FatigueStart));
            Assert.Greater(TennisOpponent.Fatigue(20), 0);
            Assert.AreEqual(TennisOpponent.FatigueMax, TennisOpponent.Fatigue(200), 1e-6f);
            var p = OpponentProfile.FromDifficulty(TennisOpponent.DefaultDifficulty);
            var r = TennisOpponent.Decide(0, .3f, 0, 0, 0, p, .01f, .5f, .5f, .2f, p.Reach, 0, .5f, false, TennisRules.BaselineZ, false, 0,
                TennisOpponent.Fatigue(30));
            Assert.IsTrue(r.Error); Assert.AreEqual("WORN DOWN", r.Reason);
        }

        /// Share of shots that win the point outright (past the rival, or it errs) for a swing `late` seconds off the ball
        /// sent down `aim`'s lane, from across the baseline, `shot` balls into the rally. The rival recovers to the middle
        /// between shots and runs to stand beside the ball after its reaction, as TennisGame.UpdateOpponent does.
        static float WinRate(OpponentProfile p, float aim, float late, int shot, int n = 2000, int seed = 5)
        {
            var rng = new System.Random(seed);
            float R() => (float)rng.NextDouble();
            int won = 0;
            for (int i = 0; i < n; i++)
            {
                float humanX = (R() * 2 - 1) * 2f;
                var hit = TennisRules.AssistedHit(late, 1, 1, .65f, 1);
                var target = TennisRules.SwingPlacement(aim, hit.Quality, R() * 2 - 1, R() * 2 - 1);
                var start = new Vector3(humanX, 1.1f, -StrikeZ);
                Vector3 pos = start, vel = TennisRules.RallyVelocity(start, target, hit.Speed, .35f, hit.Quality);
                float spin = .35f, t = 0;
                for (int k = 0; k < 1200 && pos.z < StrikeZ; k++)
                {
                    TennisBall.Integrate(ref pos, ref vel, spin, TennisBall.Step);
                    if (pos.y < TennisRules.BallRadius && vel.y < 0) { pos.y = TennisRules.BallRadius; TennisBall.Bounce(ref vel, ref spin, .75f); }
                    t += TennisBall.Step;
                }
                float goal = pos.x + (pos.x >= 0 ? -.65f : .65f);
                float rivalX = Mathf.MoveTowards(0, goal, Mathf.Max(0, t - p.Reaction - TennisOpponent.RallyReadDelay)
                    * p.Speed * TennisRules.CourtMovementScale * TennisOpponent.RallyLegs);
                float pace = Mathf.InverseLerp(16, 32, new Vector2(vel.x, vel.z).magnitude);
                var r = TennisOpponent.Decide(rivalX, pos.x, humanX, 0, 0, p, R(), R(), R(), pace, p.Reach, 0, hit.Quality,
                    false, TennisRules.BaselineZ, false, TennisOpponent.RallyEase(shot), TennisOpponent.Fatigue(shot));
                if (!r.Reached || r.Error) won++;
            }
            return won / (float)n;
        }

        [Test] public void TheLadderGetsHarder()
        {
            float Clean(OpponentProfile p) => (WinRate(p, -.8f, 0, 7) + WinRate(p, .8f, 0, 7)) / 2;
            float club = Clean(OpponentProfile.FromDifficulty(0)), standard = Clean(OpponentProfile.FromDifficulty(TennisOpponent.DefaultDifficulty));
            float pro = Clean(OpponentProfile.FromDifficulty(1)), boss = Clean(OpponentProfile.Rival("boss", 1));
            TestContext.WriteLine($"clean angle wins: club {club:P0}, standard {standard:P0}, pro {pro:P0}, boss {boss:P0}");
            Assert.Greater(club, standard); Assert.GreaterOrEqual(standard, pro); Assert.GreaterOrEqual(pro, boss);
        }

        [Test] public void PlacementBeatsTheRivalAndAMistimedBallNeverDoes()
        {
            var report = "";
            foreach (var (name, p) in Ladder)
            {
                // Mid-rally, before fatigue: what the ball itself earns.
                float cornerClean = (WinRate(p, -.8f, 0, 7) + WinRate(p, .8f, 0, 7)) / 2;
                float middleClean = WinRate(p, 0, 0, 7);
                float cornerMistimed = (WinRate(p, -.8f, .16f, 7) + WinRate(p, .8f, -.16f, 7)) / 2;   // the worst timing that still lands in
                float middleGood = WinRate(p, 0, .12f, 7);
                report += $"{name}: corner clean {cornerClean:P0}, middle clean {middleClean:P0}, middle GOOD {middleGood:P0}, corner mistimed {cornerMistimed:P0}\n";
                Assert.LessOrEqual(cornerMistimed, .03f, $"{name}: a mistimed ball must not win points\n{report}");
                Assert.LessOrEqual(middleGood, .02f, $"{name}: an ordinary ball down the middle comes back\n{report}");
                Assert.LessOrEqual(middleClean, .05f, $"{name}: even a clean one: points come from the angles\n{report}");
                Assert.GreaterOrEqual(cornerClean, middleClean, $"{name}: the angle is where points are won\n{report}");
                // This model starts the rival in the middle every time; in the real game it is often still recovering
                // from its own shot, so the absolute rate is measured there (work/tennis-fun-1026, ZTennisFunPlay).
            }
            TestContext.WriteLine(report);
        }
    }
}
