using System.Collections;
using System.Diagnostics;
using System.IO;
using GolfArcade.Bowling;
using GolfArcade.Game;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    /// Gameplay clips of the real Bowling scene (the game's own camera and HUD, the real match heroes with the authored Bowl_* clips), 1280x720 at 60 fps with a fixed 1/60 s step,
    /// silent. One clip per kind of delivery: a good strike, a hook, an early release, the three drops, a late release and a foul. Run explicitly:
    ///   BOWL_FILM_DIR=<out dir> POINT_CAPTURE_FFMPEG=<ffmpeg> Unity -runTests -testPlatform PlayMode -testFilter GolfArcade.PlayTests.BowlingFilmTests
    public class BowlingFilmTests
    {
        struct Plan
        {
            public string Name; public bool Female; public BowlingGame.Shot Shot; public float Bias;
            public Plan(string name, bool female, BowlingGame.Shot shot, float bias = 0) { Name = name; Female = female; Shot = shot; Bias = bias; }
        }

        static readonly Plan[] Plans =
        {
            new Plan("01_strike_male", false, new BowlingGame.Shot(20, 7.6f, 280, 30, 0f)),
            new Plan("02_hook_female", true, new BowlingGame.Shot(14, 7.2f, 300, 45, 0f)),
            new Plan("03_early_male", false, new BowlingGame.Shot(20, 7.0f, 260, 35, -.16f)),
            new Plan("04_late_female", true, new BowlingGame.Shot(20, 7.0f, 260, 35, .17f)),
            new Plan("05_foul_male", false, new BowlingGame.Shot(20, 7.2f, 260, 35, .6f)),
            new Plan("06_drop_spin_female", true, new BowlingGame.Shot(20, 7.0f, 260, 35, -.55f)),
            new Plan("07_drop_chase_male", false, new BowlingGame.Shot(20, 7.0f, 260, 35, -1.1f)),
            new Plan("08_drop_toe_female", true, new BowlingGame.Shot(20, 7.0f, 260, 35, -1.6f)),
            new Plan("09_followthrough_right_male", false, new BowlingGame.Shot(20, 7.4f, 200, 10, 0f), 5f),
            new Plan("10_followthrough_left_female", true, new BowlingGame.Shot(20, 7.4f, 200, 10, 0f), -5f),
            new Plan("11_followthrough_straight_male", false, new BowlingGame.Shot(20, 7.4f, 200, 10, 0f), 0f),
        };

        [UnityTest, Explicit, Timeout(3600000)]
        public IEnumerator FilmGameplayClips60()
        {
            yield return SceneManager.LoadSceneAsync("Bowling"); yield return null; yield return null;
            var game = Object.FindFirstObjectByType<BowlingGame>();
            Assert.IsNotNull(game, "the Bowling scene has a BowlingGame");
            string dir = Path.GetFullPath(System.Environment.GetEnvironmentVariable("BOWL_FILM_DIR") ?? "../work/bowling-anim/gameplay");
            Directory.CreateDirectory(dir);
            string ffmpeg = System.Environment.GetEnvironmentVariable("POINT_CAPTURE_FFMPEG") ?? "/Users/adnanyonathan/tai-films/ffmpeg";
            string only = System.Environment.GetEnvironmentVariable("BOWL_FILM_ONLY");
            int oldRate = Time.captureFramerate; Time.captureFramerate = 60;
            var log = new System.Text.StringBuilder();
            try
            {
                foreach (var plan in Plans)
                {
                    if (!string.IsNullOrEmpty(only) && !plan.Name.Contains(only)) continue;
                    game.PlayerFemale.Clear(); game.PlayerFemale.Add(plan.Female);
                    game.Autoplay.Clear(); game.LaunchBiasDeg = plan.Bias;
                    game.NewGame(new[] { "You" });
                    for (int i = 0; i < 90; i++) yield return null;                 // the bowler walks up and settles into the stance
                    string output = Path.Combine(dir, plan.Name + ".mp4");
                    string temp = "Library/Captures/bowling-current.jpg";
                    Directory.CreateDirectory(Path.GetDirectoryName(temp));
                    var encoder = Process.Start(new ProcessStartInfo
                    {
                        FileName = ffmpeg,
                        Arguments = "-y -hide_banner -loglevel error -f image2pipe -framerate 60 -vcodec mjpeg -i pipe:0 -an -c:v libx264 -preset veryfast -crf 19 -pix_fmt yuv420p -r 60 -movflags +faststart \"" + output + "\"",
                        UseShellExecute = false, RedirectStandardInput = true, CreateNoWindow = true,
                    });
                    game.Autoplay.Enqueue(plan.Shot);
                    int frame = 0, tail = 0; bool sawSweep = false; var grade = ReleaseGrade.Perfect; int knocked = -1;
                    game.BallFinished += (th, act) => { grade = th.Grade; knocked = act.Knocked; };
                    try
                    {
                        for (; frame < 60 * 70; frame++)
                        {
                            if (game.Flow == BowlingGame.Phase.Sweep) sawSweep = true;
                            if (sawSweep && game.Flow == BowlingGame.Phase.Setup && ++tail >= 45) break;
                            yield return null;
                            GameCapture.Save(temp, 1280, 720);
                            byte[] jpg = File.ReadAllBytes(temp); encoder.StandardInput.BaseStream.Write(jpg, 0, jpg.Length);
                        }
                    }
                    finally
                    {
                        encoder.StandardInput.Close(); encoder.WaitForExit(30000);
                    }
                    Assert.That(encoder.ExitCode, Is.Zero, plan.Name);
                    log.AppendLine($"{plan.Name}: {frame} frames at 60 fps ({frame / 60f:0.0} s); grade {grade}; pins {knocked}; hero {(plan.Female ? "female" : "male")}");
                    UnityEngine.Debug.Log("[BowlingFilm] " + log.ToString().TrimEnd().Split('\n')[^1]);
                    Assert.IsTrue(sawSweep, plan.Name + ": the delivery must run to the pin sweep");
                }
            }
            finally
            {
                Time.captureFramerate = oldRate; if (game) game.LaunchBiasDeg = 0;
                File.WriteAllText(Path.Combine(dir, "gameplay_clips.txt"), "Unity Bowling scene, game camera + HUD, 1280x720, 60 fps fixed step, autoplay inputs, silent.\n" + log);
            }
        }
    }
}
