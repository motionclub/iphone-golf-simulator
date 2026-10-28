using System.Collections;
using System.Diagnostics;
using System.IO;
using System.Linq;
using GolfArcade.Course;
using GolfArcade.Game;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    /// 10-28 clips of the golf physics pass, one per change, from the game camera with its HUD: a drive bouncing on
    /// lively turf, a shot over the island's edge, the short trail in the air, a drive into a tulip bed.
    ///   GOLF_FILM_DIR=<out dir> POINT_CAPTURE_FFMPEG=<ffmpeg> Unity -runTests -testPlatform PlayMode -testFilter GolfArcade.PlayTests.SolidPropsFilmTests
    public class SolidPropsFilmTests
    {
        const int Fps = 30;

        static IEnumerator WaitFor(System.Func<bool> done, float seconds, string what)
        {
            float until = Time.realtimeSinceStartup + seconds;
            while (!done())
            {
                if (Time.realtimeSinceStartup > until) Assert.Fail($"timed out waiting for {what}");
                yield return null;
            }
        }

        /// Strikes at `target` and films the shot from the swing to a second after it stops.
        static IEnumerator Film(GolfGame game, CoursePoint target, string path, string ffmpeg)
        {
            const string temp = "Library/Captures/golf-film-current.jpg";
            Directory.CreateDirectory(Path.GetDirectoryName(temp));
            var encoder = Process.Start(new ProcessStartInfo
            {
                FileName = ffmpeg,
                Arguments = $"-y -hide_banner -loglevel error -f image2pipe -framerate {Fps} -vcodec mjpeg -i pipe:0 -an -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p -movflags +faststart \"{path}\"",
                UseShellExecute = false, RedirectStandardInput = true, CreateNoWindow = true,
            });
            try
            {
                game.StrikeToward(target);
                int tail = 0;
                for (int frame = 0; frame < Fps * 40; frame++)
                {
                    if (frame > Fps && game.Current != GolfGame.State.Flight && ++tail > Fps * 1.2) break;
                    yield return null;
                    GameCapture.Save(temp, 540, 1170);
                    var jpg = File.ReadAllBytes(temp); encoder.StandardInput.BaseStream.Write(jpg, 0, jpg.Length);
                }
            }
            finally { encoder.StandardInput.Close(); encoder.WaitForExit(30000); }
            Assert.That(encoder.ExitCode, Is.Zero, path);
        }

        static IEnumerator Tee(GolfGame game, int number)
        {
            game.JumpToHole(number);
            yield return WaitFor(() => game.Current == GolfGame.State.Aim, 60, $"hole {number}'s tee");
            for (int i = 0; i < Fps; i++) yield return null;
        }

        [UnityTest]
        public IEnumerator FilmEachChange()
        {
            string dir = Path.GetFullPath(System.Environment.GetEnvironmentVariable("GOLF_FILM_DIR") ?? "../work/golf-bounce-1028/clips");
            string ffmpeg = System.Environment.GetEnvironmentVariable("POINT_CAPTURE_FFMPEG") ?? "/Users/adnanyonathan/tai-films/ffmpeg";
            Directory.CreateDirectory(dir);
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
            int oldRate = Time.captureFramerate; Time.captureFramerate = Fps;
            try
            {
                // 1. bounce: a drive down the open fairway, kicking up and skipping on
                yield return Tee(game, 7);
                var hole = game.CurrentHole;
                yield return Film(game, hole.RecommendedTarget(hole.Tee), Path.Combine(dir, "1-bounce.mp4"), ffmpeg);
                UnityEngine.Debug.Log($"[GolfFilm] bounce: carry {game.LastShot.Carry:F0}, total {game.LastShot.Total:F0}, rests {game.LastShot.Lie}");

                // 2. edge: a shot just past Windmill Links' shore
                yield return Tee(game, 20);
                hole = game.CurrentHole;
                CoursePoint edge = default; bool found = false;
                for (double d = 120; d <= 230 && !found; d += 10)
                    for (double x = 60; x <= 130 && !found; x += 1.5)
                        if (hole.LieAt(new CoursePoint(x, d)) == CourseLie.Water && hole.LieAt(new CoursePoint(x - 4, d)) != CourseLie.Water)
                        { edge = new CoursePoint(x + 2, d); found = true; }
                Assert.IsTrue(found, "an edge in reach");
                yield return Film(game, edge, Path.Combine(dir, "2-edge.mp4"), ffmpeg);
                UnityEngine.Debug.Log($"[GolfFilm] edge: landed {game.LastShot.Landing} ({game.LastShot.Lie})");

                // 3. trail: a long iron at Windmill Links' green, against the sky
                yield return Tee(game, 20);
                hole = game.CurrentHole;
                yield return Film(game, hole.RecommendedTarget(hole.Tee), Path.Combine(dir, "3-trail.mp4"), ffmpeg);

                // 4. tulips: a drive into a tulip bed knocks off it
                yield return Tee(game, 20);
                hole = game.CurrentHole;
                var beds = Object.FindObjectsByType<MeshCollider>(FindObjectsSortMode.None).Where(c => c.name.StartsWith(GolfSolidProps.Prefix + "FLOWERS"))
                    .OrderBy(b => HoleView.ToCourse(b.bounds.center).DistanceTo(hole.Tee));
                CoursePoint target = default; found = false;
                foreach (var bed in beds)
                {
                    foreach (var dz in new[] { 0f, -6f, 6f, -12f })
                    {
                        var p = new CoursePoint(bed.bounds.center.x, bed.bounds.center.z + dz);
                        if (game.PlanFor(p).Knocks.Any(k => k.Kind == ObstacleKind.Wall)) { target = p; found = true; break; }
                    }
                    if (found) break;
                }
                Assert.IsTrue(found, "a drive can reach a tulip bed");
                yield return Film(game, target, Path.Combine(dir, "4-tulips.mp4"), ffmpeg);
                Assert.IsTrue(game.LastShot.Knocks.Any(k => k.Kind == ObstacleKind.Wall), "it knocked off the bed");
            }
            finally { Time.captureFramerate = oldRate; }
        }
    }
}
