using System.Collections.Generic;
using System.Linq;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// The rally ball's shape (PLAN_FinalLook_Gameplay_2026-11-11, Phase 1 "Tennis: a flatter, faster ball").
    ///
    /// Until 2026-11-11 nothing pinned how high a rally ball flew, and the 10-26 "hang time" pass let ordinary shots peak at
    /// 2.6-3.8 m. These tests fly the shots the game actually sends -- the player's through TimingPace / SwingPlacement /
    /// RallyVelocity, each rival's through its own decision code and the launch TennisGame.SendFromOpponent uses -- and hold
    /// them to the plan's table. The same arithmetic outside Unity: work/final-plan-1111/phase1/tennis_model.py.
    public class TennisFlightTests
    {
        public struct Flight { public float Peak, ToBounce, SecondPeak, Kept; public Vector3 Landing; }

        /// Fly a ball to its second bounce on the game's own integrator and court.
        public static Flight Fly(Vector3 position, Vector3 velocity, float spin, float restitution)
        {
            var f = new Flight { Peak = position.y }; float t = 0; int bounces = 0;
            for (int i = 0; i < 2400; i++)
            {
                TennisBall.Integrate(ref position, ref velocity, spin, TennisBall.Step); t += TennisBall.Step;
                if (bounces == 0) f.Peak = Mathf.Max(f.Peak, position.y); else f.SecondPeak = Mathf.Max(f.SecondPeak, position.y);
                if (position.y < TennisRules.BallRadius && velocity.y < 0)
                {
                    if (++bounces == 2) break;
                    f.ToBounce = t; f.Landing = position; position.y = TennisRules.BallRadius;
                    float before = new Vector2(velocity.x, velocity.z).magnitude;
                    TennisBall.Bounce(ref velocity, ref spin, restitution);
                    f.Kept = new Vector2(velocity.x, velocity.z).magnitude / before;
                }
            }
            return f;
        }

        /// The player's rally shot as TennisGame.ReturnBall sends it: struck at hip height just inside the baseline.
        static Flight PlayerShot(float quality, float lane, float spin = .35f, float power = .6f)
        {
            var from = new Vector3(0, 1.0f, TennisRules.BaselineZ + .3f);
            Vector3 target = TennisRules.SwingPlacement(lane * .8f, quality, 0, 0);
            Vector3 v = TennisRules.RallyVelocity(from, target, TennisRules.ShotSpeed(quality, power, 1), spin, quality);
            return Fly(from, v, spin, TennisFlight.Restitution);
        }

        public struct RivalBall { public Vector3 From, Velocity; public float Spin; public TennisReturnKind Kind; }

        /// A rival's rally balls (never a serve return, never an error), launched the way TennisGame.SendFromOpponent does.
        static IEnumerable<RivalBall> RivalBalls(OpponentProfile p, int seed, int count = 400)
        {
            var rng = new System.Random(seed); float R() => (float)rng.NextDouble();
            for (int i = 0; i < count; i++)
            {
                var d = TennisOpponent.Decide(0, 0, 0, 0, 0, p, 1, R(), R(), .4f, p.Reach, 0, .5f, false, TennisRules.BaselineZ, false);
                var from = new Vector3(Mathf.Lerp(-2.5f, 2.5f, R()), Mathf.Lerp(.7f, 1.4f, R()), 10.6f);
                Vector3 v;
                if (d.Kind == TennisReturnKind.Lob) v = TennisAbilities.LobVelocity(from, d.Landing, TennisFlight.RivalLobApex);
                else
                {
                    bool drop = d.Kind == TennisReturnKind.Drop;
                    float speed = drop ? d.Speed : TennisFlight.RivalDrivePace(from, d.Landing, d.Speed);
                    v = TennisRules.RallyArcVelocity(from, d.Landing, speed, d.Spin, drop ? .18f : TennisFlight.RivalNetClearance);
                }
                yield return new RivalBall { From = from, Velocity = v, Spin = d.Kind == TennisReturnKind.Lob ? 0 : d.Spin, Kind = d.Kind };
            }
        }

        static bool IsDrive(TennisReturnKind k) => k != TennisReturnKind.Lob && k != TennisReturnKind.Drop;

        [Test]
        public void APerfectDrivePeaksNearHeadHeight()
        {
            if (TennisFlight.Classic) Assert.Ignore("TENNIS_CLASSIC=1: the 10-26 ball is not held to the 11-11 gates.");
            foreach (float lane in new[] { -1f, 0f, 1f })
            {
                var f = PlayerShot(1, lane);
                Assert.That(f.Peak, Is.LessThanOrEqualTo(1.8f), $"perfect drive, lane {lane}: peaked at {f.Peak:0.00} m (2.6 m before 11-11)");
                Assert.That(TennisRules.BounceIsIn(f.Landing) && f.Landing.z > 0, $"perfect drive, lane {lane}: landed at {f.Landing}");
            }
        }

        [Test]
        public void OrdinaryShotsStayLow()
        {
            if (TennisFlight.Classic) Assert.Ignore("TENNIS_CLASSIC=1");
            // Every timing a swing can have, on every lane, at the spins a drive, a topspin and a slice carry.
            var peaks = new List<float>();
            foreach (float spin in new[] { .35f, .8f, -.8f })
                foreach (float lane in new[] { -1f, 0f, 1f })
                    for (float q = .05f; q <= 1.001f; q += .05f) peaks.Add(PlayerShot(q, lane, spin).Peak);
            Assert.That(peaks.Average(), Is.LessThanOrEqualTo(2.2f), $"average rally peak {peaks.Average():0.00} m (3.8 m before 11-11)");
            Assert.That(peaks.Max(), Is.LessThanOrEqualTo(2.45f), $"highest rally peak {peaks.Max():0.00} m");
        }

        [Test]
        public void EveryRivalsDrivesStayLow()
        {
            if (TennisFlight.Classic) Assert.Ignore("TENNIS_CLASSIC=1");
            var report = new System.Text.StringBuilder("rival,drives,meanPeak,maxPeak,meanSecondArc,maxSecondArc\n");
            foreach (var rival in TennisRoster.All)
            {
                var flights = RivalBalls(rival.Profile, 31 + rival.Key.Length).Where(b => IsDrive(b.Kind))
                    .Select(b => Fly(b.From, b.Velocity, b.Spin, TennisFlight.Restitution)).ToList();
                float mean = flights.Average(f => f.Peak), max = flights.Max(f => f.Peak);
                report.AppendLine($"{rival.Key},{flights.Count},{mean:0.00},{max:0.00},{flights.Average(f => f.SecondPeak):0.00},{flights.Max(f => f.SecondPeak):0.00}");
                // The plan's figure is the drive a rival ordinarily hits (3.7 m before 11-11). Its heaviest topspin to the
                // baseline dips under a stronger pull, so the same second in the air carries it a little higher.
                Assert.That(mean, Is.LessThanOrEqualTo(2.2f), $"{rival.Key}: mean drive peak {mean:0.00} m");
                Assert.That(max, Is.LessThanOrEqualTo(2.5f), $"{rival.Key}: highest drive peak {max:0.00} m");
            }
            Debug.Log("[TennisFlight] rival drives\n" + report);
        }

        [Test]
        public void TheSecondArcSitsAtHipHeight()
        {
            if (TennisFlight.Classic) Assert.Ignore("TENNIS_CLASSIC=1");
            // After the bounce the ball used to climb back to 1.7-2.3 m, head height and above, which made bounced balls smashes.
            var player = new List<float>();
            foreach (float lane in new[] { -1f, 0f, 1f })
                for (float q = .05f; q <= 1.001f; q += .05f) player.Add(PlayerShot(q, lane).SecondPeak);
            Assert.That(player.Max(), Is.LessThanOrEqualTo(1.3f), $"player drive second arc {player.Max():0.00} m");
            foreach (var rival in TennisRoster.All)
            {
                var arcs = RivalBalls(rival.Profile, 47 + rival.Key.Length).Where(b => IsDrive(b.Kind))
                    .Select(b => Fly(b.From, b.Velocity, b.Spin, TennisFlight.Restitution).SecondPeak).ToList();
                Assert.That(arcs.Average(), Is.LessThanOrEqualTo(1.3f), $"{rival.Key}: mean second arc {arcs.Average():0.00} m");
                Assert.That(arcs.Max(), Is.LessThan(1.75f), $"{rival.Key}: a bounced drive reached smash height ({arcs.Max():0.00} m)");
            }
        }

        [Test]
        public void TheCourtTakesPaceOffARallyBallButNotAServe()
        {
            Vector3 rally = new Vector3(0, -6, 20), serve = rally; float s0 = 0, s1 = 0;
            TennisBall.Bounce(ref rally, ref s0, TennisFlight.Restitution);
            TennisBall.Bounce(ref serve, ref s1, TennisBall.ServeRestitution);
            Assert.That(serve.z, Is.EqualTo(20 * TennisBall.ServeGrip).Within(.001f), "a serve keeps its skid: the return window is tuned on it");
            if (TennisFlight.Classic) return;
            Assert.That(rally.z, Is.InRange(20 * .45f, 20 * .62f), "a rally ball gives up 40-55% of its pace to the court");
            Assert.That(rally.y, Is.InRange(6 * .58f, 6 * .70f));
        }

        [Test]
        public void RivalsLobAtMostOneBallInTwelveAndNoHigherThanThreeAndAHalfMetres()
        {
            if (TennisFlight.Classic) Assert.Ignore("TENNIS_CLASSIC=1");
            foreach (var rival in TennisRoster.All)
                foreach (float playerZ in new[] { TennisRules.BaselineZ, -4f })       // back on the baseline, and up at the net
                {
                    var rng = new System.Random(5 + rival.Key.Length); float R() => (float)rng.NextDouble();
                    int lobs = 0; const int n = 2400;
                    for (int i = 0; i < n; i++)
                    {
                        var d = TennisOpponent.Decide(0, 0, 0, 0, 0, rival.Profile, 1, R(), R(), .4f, rival.Profile.Reach, 0, .5f, false, playerZ, false);
                        if (d.Kind == TennisReturnKind.Lob) lobs++;
                    }
                    Assert.That(lobs / (float)n, Is.LessThanOrEqualTo(1f / 12 + .012f), $"{rival.Key} with the player at z={playerZ}: {lobs} lobs in {n}");
                }
            var from = new Vector3(0, 1.1f, 10.6f);
            var lob = Fly(from, TennisAbilities.LobVelocity(from, new Vector3(1, TennisRules.BallRadius, -10.6f), TennisFlight.RivalLobApex), 0, TennisFlight.Restitution);
            Assert.That(lob.Peak, Is.LessThanOrEqualTo(3.5f + .01f));
        }

        /// Hit-to-contact for the fastest ball the 10-26 game sent at a player on the baseline (game seconds; the fastest
        /// rival's deep drive, measured with TENNIS_CLASSIC=1 by `ReportHitToContact` below).
        public const float ClassicFastestHitToContact = 1.25f;

        static float HitToContact(RivalBall b, out bool reachable)
        {
            var plan = TennisRules.PlanIntercept(b.From, b.Velocity, b.Spin, TennisFlight.Restitution,
                new Vector2(Mathf.Clamp(b.From.x + b.Velocity.x * 1.1f, -3.5f, 3.5f), TennisRules.BaselineZ), TennisRules.ReactionTime, TennisRules.RunSpeed, false);
            reachable = plan.Found && plan.Reachable;
            return plan.Time;
        }

        [Test]
        public void ThePlayerHasAsLongToMeetTheBallAsBefore()
        {
            if (TennisFlight.Classic) Assert.Ignore("TENNIS_CLASSIC=1");
            // Flatter must not mean rushed: the ball reaches its bounce sooner, and the court gives the time back after it.
            foreach (var rival in TennisRoster.All)
            {
                var times = new List<float>();
                foreach (var b in RivalBalls(rival.Profile, 13 + rival.Key.Length).Where(b => IsDrive(b.Kind)))
                { float t = HitToContact(b, out bool ok); if (ok) times.Add(t); }
                Assert.That(times.Count, Is.GreaterThan(200), rival.Key + ": most drives are reachable from under them");
                times.Sort();
                float fastest = times[Mathf.FloorToInt(times.Count * .02f)];   // the 2nd percentile: one odd ball is not the rival's pace
                Assert.That(fastest, Is.GreaterThanOrEqualTo(ClassicFastestHitToContact - .03f),
                    $"{rival.Key}: its fastest drives are met {fastest:0.00} s after its hit ({ClassicFastestHitToContact:0.00} s for the fastest ball before 11-11)");
            }
        }

        [Test]
        public void ReportHitToContact()
        {
            var report = new System.Text.StringBuilder($"classic={TennisFlight.Classic}\nrival,p02,median,p98,meanPeak\n");
            float fastest = float.MaxValue;
            foreach (var rival in TennisRoster.All)
            {
                var times = new List<float>(); var peaks = new List<float>();
                foreach (var b in RivalBalls(rival.Profile, 13 + rival.Key.Length).Where(b => IsDrive(b.Kind)))
                {
                    float t = HitToContact(b, out bool ok); if (ok) times.Add(t);
                    peaks.Add(Fly(b.From, b.Velocity, b.Spin, TennisFlight.Restitution).Peak);
                }
                if (times.Count == 0) continue;
                times.Sort();
                float p02 = times[Mathf.FloorToInt(times.Count * .02f)];
                fastest = Mathf.Min(fastest, p02);
                report.AppendLine($"{rival.Key},{p02:0.00},{times[times.Count / 2]:0.00},{times[Mathf.FloorToInt(times.Count * .98f)]:0.00},{peaks.Average():0.00}");
            }
            report.AppendLine($"fastest p02 over the roster,{fastest:0.00}");
            report.AppendLine("player shots: quality,peak,toBounce,secondArc,paceKept");
            foreach (float q in new[] { .08f, .3f, .55f, .8f, 1f })
            { var f = PlayerShot(q, 0); report.AppendLine($"{q:0.00},{f.Peak:0.00},{f.ToBounce:0.00},{f.SecondPeak:0.00},{f.Kept:0.00}"); }
            Debug.Log("[TennisFlight] hit to contact, game seconds\n" + report);
            var dir = System.Environment.GetEnvironmentVariable("TENNIS_FLIGHT_REPORT");
            if (!string.IsNullOrEmpty(dir)) System.IO.File.WriteAllText(System.IO.Path.Combine(dir, $"hit_to_contact_{(TennisFlight.Classic ? "classic" : "flat")}.csv"), report.ToString());
            Assert.Pass();
        }
    }
}
