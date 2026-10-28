using System.Collections;
using System.Linq;
using GolfArcade.Course;
using GolfArcade.Game;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    /// 10-28 (Adnan): Windmill Links' tulip beds "are a bunch of colors and the ball goes through
    /// them", and a ball going over the side near the edge sank through the ground. A drive into a
    /// tulip bed knocks off it; one over the island's edge never draws below the ground it passes;
    /// the short trail is captured on the way. Frames go to Library/Captures/solid.
    public class SolidPropsPlayTests
    {
        const string Dir = "Library/Captures/solid";

        static IEnumerator WaitFor(System.Func<bool> done, float seconds, string what)
        {
            float until = Time.realtimeSinceStartup + seconds;
            while (!done())
            {
                if (Time.realtimeSinceStartup > until) Assert.Fail($"timed out waiting for {what}");
                yield return null;
            }
        }

        static IEnumerator Round(System.Action<GolfGame> ready)
        {
            Time.timeScale = 1f;
            yield return SceneManager.LoadSceneAsync("Golf", LoadSceneMode.Single);
            var cam = Camera.main;
            if (cam) cam.aspect = GameCapture.PhoneWidth / (float)GameCapture.PhoneHeight;
            var game = Object.FindFirstObjectByType<GolfGame>();
            game.InstantReplays = false;
            yield return null;
            game.ChooseHoles(0);
            game.Play();
            yield return null;
            ready(game);
        }

        /// Plays the shot, saving frames: in the air (the trail), at `markAt` seconds, and at rest. The lowest the
        /// ball was ever drawn against the ground under it, yards.
        static IEnumerator Fly(GolfGame game, CoursePoint target, string name, double markAt, System.Action<float> lowest)
        {
            game.StrikeToward(target);
            yield return WaitFor(() => game.Current == GolfGame.State.Flight, 5, "the shot");
            var ball = GameObject.Find("Ball")?.transform;
            float least = float.MaxValue; bool trail = false, mark = false;
            while (game.Current == GolfGame.State.Flight)
            {
                if (ball)
                {
                    float under = (float)HoleView.GroundHeight(HoleView.ToCourse(ball.position));
                    least = Mathf.Min(least, ball.position.y - under);
                }
                if (!trail && game.FlightTime > 1.0) { trail = true; GameCapture.Save($"{Dir}/{name}-a-trail.png"); }
                if (!mark && game.FlightTime > markAt) { mark = true; GameCapture.Save($"{Dir}/{name}-b-contact.png"); }
                yield return null;
            }
            GameCapture.Save($"{Dir}/{name}-c-rest.png");
            lowest(least);
        }

        [UnityTest]
        public IEnumerator TulipBedsAreSolidAndEdgesHold()
        {
            GolfGame game = null;
            yield return Round(g => game = g);
            game.JumpToHole(20);
            yield return WaitFor(() => game.Current == GolfGame.State.Aim, 60, "Windmill Links' tee");
            var hole = game.CurrentHole;
            Assert.IsNotNull(hole.Solids, "the hole's solid dressing is registered");
            var beds = Object.FindObjectsByType<MeshCollider>(FindObjectsSortMode.None).Where(c => c.name.StartsWith(GolfSolidProps.Prefix + "FLOWERS")).ToArray();
            Debug.Log($"SOLID hole 20: {hole.Solids.Count} solid pieces, {beds.Length} tulip beds");
            Assert.IsNotEmpty(beds, "the tulip beds are solid");

            // a drive that comes down into a tulip bed knocks off it
            CourseShot plan = null; CoursePoint target = default;
            foreach (var bed in beds.OrderBy(b => HoleView.ToCourse(b.bounds.center).DistanceTo(hole.Tee)))
            {
                var c = bed.bounds.center;
                foreach (var dz in new[] { 0f, -6f, 6f, -12f })
                {
                    var p = new CoursePoint(c.x, c.z + dz);
                    var trial = game.PlanFor(p);
                    if (trial.Knocks.Any(k => k.Kind == ObstacleKind.Wall)) { plan = trial; target = p; break; }
                }
                if (plan != null) break;
            }
            Assert.IsNotNull(plan, "a drive can reach a tulip bed");
            var knock = plan.Knocks.First(k => k.Kind == ObstacleKind.Wall);
            float lowest = 0;
            yield return Fly(game, target, "tulips", knock.Time + 0.05, l => lowest = l);
            var shot = game.LastShot;
            Debug.Log($"SOLID tulips: knock at {knock.Time:F2}s ({knock.X:F1}, {knock.Y:F1}, {knock.D:F1}); landed {shot.Landing}, rests {shot.Rest} ({shot.Lie}); lowest drawn {lowest:F3} yd");
            Assert.IsTrue(shot.Knocks.Any(k => k.Kind == ObstacleKind.Wall), "it knocked off the bed");
            Assert.Greater(lowest, -0.02f, "never drawn under the ground");
            yield return WaitFor(() => game.Current == GolfGame.State.Aim, 15, "the next shot");

            // over the side: a ball sent just past the island's edge
            game.JumpToHole(20);
            yield return WaitFor(() => game.Current == GolfGame.State.Aim, 60, "the tee again");
            CoursePoint edge = default; bool found = false;
            for (double d = 120; d <= 230 && !found; d += 10)
                for (double x = 60; x <= 130 && !found; x += 1.5)
                {
                    var p = new CoursePoint(x, d);
                    if (hole.LieAt(p) != CourseLie.Water || hole.LieAt(new CoursePoint(x - 4, d)) == CourseLie.Water) continue;
                    edge = new CoursePoint(x + 2, d); found = true;
                }
            Assert.IsTrue(found, "an edge in reach");
            yield return Fly(game, edge, "edge", game.PlanFor(edge).LandingTime, l => lowest = l);
            shot = game.LastShot;
            Debug.Log($"SOLID edge: target {edge}, landed {shot.Landing} ({hole.LieAt(shot.Landing)}), rests {shot.Rest} ({shot.Lie}), knocks {shot.Knocks.Count}; lowest drawn {lowest:F3} yd");
            Assert.Greater(lowest, -0.02f, "over the edge it is never drawn under the ground");
        }
    }
}
