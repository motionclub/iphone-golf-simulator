using System;
using System.Collections;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Shot;
using GolfArcade.Swing;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.PlayTests
{
    /// The ball on the modelled holes' own meshes (11-24, "the ball sometimes dies or goes straight up"). A sweep of every
    /// club, pace and line over all sixteen holes found the drawn ball going straight up after it had come down — riding up a
    /// terrace's riser or a bank's face in a frame or two, or spiking up a ledge's whole drop between two samples — on the
    /// Steps, the Wild Isles' banks and the crater holes. These are the tee shots that did it most: none may now.
    public class GolfBallTerrainPlayTests
    {
        [UnityTest, Timeout(600000)]
        public IEnumerator NoTeeShotIsDrawnGoingStraightUpOffTheGround()
        {
            LogAssert.ignoreFailingMessages = true;   // (headless runs log render-texture errors)
            yield return SceneManager.LoadSceneAsync("Golf");
            var game = Object.FindFirstObjectByType<GolfGame>();
            game.ChooseHoles(0); game.Play();
            yield return null;
            int shots = 0;
            var failures = new System.Collections.Generic.List<string>();
            foreach (int number in new[] { 14, 15, 18, 19, 22, 23 })
            {
                game.JumpToHole(number);
                yield return null; yield return null; Physics.SyncTransforms();
                var hole = game.CurrentHole;
                var movers = hole.Movers; var rules = hole.Rules;
                hole.Movers = null; hole.Rules = PlayRules.Standard;   // (today's twists launch balls on purpose)
                try
                {
                    var from = hole.Tee;
                    var target = hole.RecommendedTarget(from);
                    double aim = Math.Atan2(target.X - from.X, target.D - from.D) * 180 / Math.PI;
                    foreach (var club in new[] { GolfClub.Driver, GolfClub.Hybrid, GolfClub.Iron5, GolfClub.Iron9 })
                        for (double power = 0.5; power <= 1.001; power += 0.1)
                            for (double off = -12; off <= 12.001; off += 2)
                            {
                                shots++;
                                var shot = new CourseShot(club, new SwingImpact { Power = power }, aim + off, from, hole);
                                double up = WorstClimb(shot, hole.Ground, out double at);
                                if (up > 0.3) failures.Add($"hole {number} {club} p{power:0.0} {off:+0;-0}°: up {up:0.0} yd in a frame at {at:0.00}s (down at {shot.LandingTime:0.00}s)");
                            }
                }
                finally { hole.Movers = movers; hole.Rules = rules; }
                yield return null;
            }
            Assert.That(failures, Is.Empty, $"{failures.Count} of {shots} tee shots went straight up:\n" + string.Join("\n", failures.GetRange(0, Math.Min(20, failures.Count))));
        }

        /// The most the drawn ball rises in one frame after its first touchdown, counting only frames in which it rises over
        /// twice as far as it travels and nothing has just knocked it up (a tree, a rock).
        static double WorstClimb(CourseShot shot, Func<CoursePoint, double> ground, out double at)
        {
            double worst = 0; at = 0;
            var prev = shot.WorldAt(shot.LandingTime, ground);
            for (double t = shot.LandingTime + 1.0 / 60; t <= shot.Duration + 1e-9; t += 1.0 / 60)
            {
                var w = shot.WorldAt(t, ground);
                double across = Math.Sqrt((w.x - prev.x) * (w.x - prev.x) + (w.d - prev.d) * (w.d - prev.d)), up = w.y - prev.y;
                bool knocked = false;
                foreach (var k in shot.Knocks) if (k.Time <= t && t - k.Time < 0.5) knocked = true;
                if (!knocked && up > 2 * across && up > worst) { worst = up; at = t; }
                prev = w;
            }
            return worst;
        }
    }
}
