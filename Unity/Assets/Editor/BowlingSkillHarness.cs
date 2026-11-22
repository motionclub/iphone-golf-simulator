#if UNITY_EDITOR
using System;
using System.IO;
using System.Text;
using GolfArcade.Bowling;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// Does skill show in the score? (11-21 skill pass, BowlingSkill.) Simulated human bowlers swing the phone with more or less
    /// consistency (peak swing rate, wrist turn, flick speed, release timing: what the detector reads), go through the game's own
    /// reading (BowlingSwingDetector.BallSpeed / Spin), release, lane integrator and PhysX pin deck, and bowl ten-frame games with
    /// the pass off and on. Each bowler stands where their own average ball reaches the pocket (or the leave's key pin), as a
    /// player who has learned the lane does. The CPU opponents bowl both ways too.
    ///   -executeMethod GolfArcade.EditorTools.BowlingSkillHarness.Run   BOWL_OUT=<dir>  BOWL_GAMES=<per bowler, default 16>
    public static class BowlingSkillHarness
    {
        struct Human
        {
            public string Name; public float Rate, RateSd, Twist, TwistSd, Flick, FlickSd, TimingSd, DirSd;
            public Human(string n, float rate, float rateSd, float twist, float twistSd, float flick, float flickSd, float timingSd, float dirSd)
            { Name = n; Rate = rate; RateSd = rateSd; Twist = twist; TwistSd = twistSd; Flick = flick; FlickSd = flickSd; TimingSd = timingSd; DirSd = dirSd; }
        }

        // peak swing rate rad/s (4.5 = a normal swing), wrist turn degrees, flick rad/s (revs = 120 + 24/rad/s), release timing s,
        // and the swing's direction off its own backswing line (degrees: read as aim past the 3° dead zone, AimFromSwing)
        static readonly Human[] Humans =
        {
            new Human("Very steady, big hook", 4.5f, .2f, 65, 2.5f, 16, .7f, .02f, 2),
            new Human("Very steady, straight", 4.5f, .2f, 0,  2,  2,  .5f,  .02f, 2),
            new Human("Steady, big hook",      4.5f, .4f, 65, 5,  16, 1.5f, .03f, 3),
            new Human("Steady, hook",          4.5f, .4f, 45, 5,  10, 1f,   .03f, 3),
            new Human("Steady, straight",      4.5f, .4f, 0,  3,  2,  1f,   .03f, 3),
            new Human("Average",               4.5f, 1f,  40, 12, 9,  2.5f, .07f, 7),
            new Human("Wild",                  4.5f, 1.8f,35, 20, 8,  4f,   .12f, 12),
        };

        public static void Run()
        {
            int code = 0;
            bool was = BowlingSkill.On;
            try
            {
                string dir = Path.GetFullPath(Environment.GetEnvironmentVariable("BOWL_OUT") ?? "../work/bowling-skill-1121/proof");
                Directory.CreateDirectory(dir);
                int games = int.TryParse(Environment.GetEnvironmentVariable("BOWL_GAMES"), out int g) ? g : 16;
                var md = new StringBuilder($"# Bowling skill pass: does skill show in the score? ({games} games per bowler per mode)\n\n");
                md.Append("Pocket % = first balls on a full rack whose readout is POCKET. Spare % = of the frames left open by the first ball.\n");
                foreach (bool on in new[] { false, true })
                {
                    BowlingSkill.On = on;
                    // the deck reads its tuning when it is built: one deck per mode
                    var scene = EditorSceneManager.NewPreviewScene();
                    try
                    {
                        using var deck = new BowlingPinDeck(scene);
                        md.Append($"\n## Skill pass {(on ? "ON (11-21)" : "OFF (10-27 feel)")}\n\n| Bowler | Average | Low | High | Strike % | Pocket % | Spare % | Mean mph (sd) | Mean entry ° |\n|---|---|---|---|---|---|---|---|---|\n");
                        int seed = 1;
                        foreach (var h in Humans)
                        {
                            var rng = new System.Random(11);
                            var st = new Stats();
                            for (int k = 0; k < games; k++) st.Game(PlayGame(deck, standing => HumanShot(h, standing, rng, ref seed), st));
                            md.Append(st.Row(h.Name));
                            Debug.Log($"[BowlingSkill] {(on ? "on" : "off")} {h.Name}: {st.Row(h.Name)}");
                        }
                        // (pin carry by entry angle and speed: BowlingCarryLaneHarness, proof/carry-lane.md)
                        md.Append("\n| CPU opponent | Average | Low | High | Strike % | Pocket % | Spare % | Mean mph (sd) | Mean entry ° |\n|---|---|---|---|---|---|---|---|---|\n");
                        foreach (var (name, skill) in BowlingCpu.Opponents)
                        {
                            var rng = new System.Random(7);
                            var st = new Stats();
                            for (int k = 0; k < games; k++)
                                st.Game(PlayGame(deck, standing =>
                                {
                                    var shot = BowlingCpu.Plan(skill, standing, OilPattern.House, rng);
                                    return BowlingRelease.Resolve(new BowlingSwing { Board = shot.Board, Speed = shot.Speed, RevRpm = shot.Rpm, AxisDeg = shot.Axis, TimingError = shot.Timing, Seed = seed++ });
                                }, st));
                            md.Append(st.Row($"CPU {name} ({skill:0.0})"));
                            Debug.Log($"[BowlingSkill] {(on ? "on" : "off")} CPU {name}: {st.Row(name)}");
                        }
                    }
                    finally { EditorSceneManager.ClosePreviewScene(scene); }
                }
                File.WriteAllText(Path.Combine(dir, "skill.md"), md.ToString());
                Debug.Log("[BowlingSkill]\n" + md);
            }
            catch (Exception e) { Debug.LogException(e); code = 1; }
            finally { BowlingSkill.On = was; }
            if (Application.isBatchMode) EditorApplication.Exit(code);
        }

        /// The human's ball: their average swing places them (the board whose clean average ball reaches the target), then this
        /// throw's own swing is drawn around that average and read the way the game reads a phone.
        static BowlingThrow HumanShot(Human h, int standing, System.Random rng, ref int seed)
        {
            (float speed, float rpm, float axis) Read(float rate, float twist, float flick)
            {
                float v = BowlingSwingDetector.BallSpeed(Mathf.Max(0, rate) * BowlingSwingDetector.ArmLength, 1);
                if (BowlingSkill.On) v = Mathf.Max(4.9f, v); else v = Mathf.Max(6.9f, v);   // BowlingGame.SelfTimedMin
                var (rpm, axis) = BowlingSwingDetector.Spin(twist, flick);
                return (v, rpm, axis);
            }
            // a steady bowler keeps the wrist still for a spare (a straight ball: the pocket does not matter there, only the line);
            // the average and wild ones throw their one ball at everything
            bool straightSpare = standing != BowlingLeave.All && h.TimingSd <= .03f;
            float twistMean = straightSpare ? 0 : h.Twist, twistSd = straightSpare ? 3 : h.TwistSd, flick = straightSpare ? 2 : h.Flick;
            var mean = Read(h.Rate, twistMean, flick);
            var (best, aim) = Place(mean.speed, mean.rpm, mean.axis, BowlingCpu.TargetX(standing));
            var now = Read(h.Rate + Gauss(rng) * h.RateSd, twistMean + Gauss(rng) * twistSd, flick + Gauss(rng) * h.FlickSd);
            float timing = Mathf.Clamp(Gauss(rng) * h.TimingSd, -BowlingRelease.MissWindow, BowlingRelease.MissWindow);
            float launch = Mathf.Clamp(aim + BowlingSwingDetector.AimFromSwing(Gauss(rng) * h.DirSd), -BowlingGame.MaxAim, BowlingGame.MaxAim);
            return BowlingRelease.Resolve(new BowlingSwing { Board = best, Speed = now.speed, RevRpm = now.rpm, AxisDeg = now.axis, AimDeg = launch, TimingError = timing, Seed = seed++ });
        }

        /// Where a player who knows their ball stands and aims (the phone's aim setting, 0.25° steps up to MaxAim): the smallest
        /// aim whose line, from a board at least 4 in from either gutter, reaches the target within a third of a board; failing
        /// that, the closest line found.
        static readonly System.Collections.Generic.Dictionary<(float, float, float, float, bool), (float, float)> placed = new();
        static (float board, float aim) Place(float speed, float rpm, float axis, float target)
        {
            var key = (Mathf.Round(speed * 100), rpm, axis, Mathf.Round(target * 1000), BowlingSkill.On);
            if (placed.TryGetValue(key, out var hit)) return hit;
            (float, float) best = (20, 0); float err = float.MaxValue;
            for (float a = 0; a <= BowlingGame.MaxAim + 1e-3f; a += .25f)
            {
                foreach (float sgn in a == 0 ? new[] { 1f } : new[] { Mathf.Sign(axis == 0 ? 1 : axis), -Mathf.Sign(axis == 0 ? 1 : axis) })
                    for (float b = 4; b <= 36; b += .5f)
                    {
                        var th = BowlingRelease.Resolve(new BowlingSwing { Board = b, Speed = speed, RevRpm = rpm, AxisDeg = axis, TimingError = 0, Seed = 1 });
                        th.LaunchDeg = a * sgn; th.LoftHeight = .03f;
                        var end = BowlingBall.Roll(th.Launch(), OilPattern.House);
                        if (end.Phase != BallPhase.Deck || end.Velocity.z < .1f) continue;
                        float x = end.Position.x + end.Velocity.x / end.Velocity.z * (BowlingLane.FoulToHeadPin - end.Position.z);
                        float e = Mathf.Abs(x - target);
                        if (e < err) { err = e; best = (b, a * sgn); }
                    }
                if (err < BowlingLane.BoardWidth / 3) break;
            }
            placed[key] = best;
            return best;
        }

        sealed class Stats
        {
            public int total, low = 300, high, games, strikes, firstBalls, spares, chances, pockets, balls;
            public double mph, mph2, entry; public int entries;
            public void Game(int score) { total += score; games++; low = Mathf.Min(low, score); high = Mathf.Max(high, score); }
            public string Row(string name)
            {
                float m = balls > 0 ? (float)(mph / balls) : 0, sd = balls > 0 ? Mathf.Sqrt(Mathf.Max(0, (float)(mph2 / balls) - m * m)) : 0;
                return $"| {name} | {total / (float)Mathf.Max(1, games):0} | {low} | {high} | {100f * strikes / Mathf.Max(1, firstBalls):0} | {100f * pockets / Mathf.Max(1, firstBalls):0} | " +
                       $"{100f * spares / Mathf.Max(1, chances):0} | {m:0.0} ({sd:0.0}) | {(entries > 0 ? entry / entries : 0):0.0} |\n";
            }
        }

        static int PlayGame(BowlingPinDeck deck, Func<int, BowlingThrow> shot, Stats st)
        {
            var score = new BowlingScore(); int standing = BowlingLeave.All;
            while (!score.Complete)
            {
                bool first = score.FreshRack;
                var th = shot(standing);
                int knocked = 0, after = standing;
                st.balls++; float mph = th.Speed * 2.237f; st.mph += mph; st.mph2 += mph * mph;
                if (!th.Dropped)
                {
                    var end = BowlingBall.Roll(th.Launch(), OilPattern.House);
                    var read = BowlingShotRead.From(th, end);
                    if (first && read.Valid) { if (read.Where == BowlingShotRead.Hit.Pocket) st.pockets++; st.entry += Mathf.Max(0, read.EntryDeg); st.entries++; }
                    var act = deck.Simulate(end, standing);
                    knocked = act.Knocked; after = act.StandingAfter;
                }
                int before = score.PinsStanding;
                score.Roll(Mathf.Min(knocked, before), th.Foul);
                if (first) { st.firstBalls++; if (knocked >= 10 && !th.Foul) st.strikes++; else st.chances++; }
                else if (!th.Foul && knocked >= before) st.spares++;
                standing = score.Complete || score.FreshRack ? BowlingLeave.All : after;
            }
            return score.Total;
        }

        static float Gauss(System.Random rng)
        {
            double u = 1 - rng.NextDouble(), v = rng.NextDouble();
            return (float)(Math.Sqrt(-2 * Math.Log(u)) * Math.Cos(2 * Math.PI * v));
        }
    }
}
#endif
