using System.Collections;
using System.IO;
using System.Reflection;
using GolfArcade.Game;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    public class TennisAbilitiesPlayTests
    {
        static void Charge(TennisGame game) => typeof(TennisGame).GetProperty("PlayerUltimate").SetValue(game, 1f);
        static void Contact(TennisGame game) => typeof(TennisGame).GetMethod("ReturnBall", BindingFlags.Instance | BindingFlags.NonPublic)
            .Invoke(game, new object[] { new TennisHit { Speed = 20, Quality = .8f, Timing = 1 }, Vector2.zero });
        static void Capture(TennisGame game, string path)
        {
            var cam = game.GameplayCamera;
            cam.transform.position = game.Player.transform.position + new Vector3(4, 2.5f, -5);
            cam.transform.LookAt(game.Player.transform.position + Vector3.up * .85f);
            cam.fieldOfView = 42;
            GameCapture.Save(path, 1280, 720);
        }
        /// STRETCH REACH 2026-11-13: the dive is gone (its code-bent pose warped the hero). A swing at a ball passing just
        /// out of reach lunges the player toward it, upright, and a well-timed one returns it through real contact.
        static void Wide(TennisGame game, float x, float vz = -8)
        {
            game.ConfigureMatch(TennisGame.Mode.Training, null, null, null);
            game.Player.CancelSwing(); game.Player.Tick(2, 0);
            game.Player.transform.position = new Vector3(0, .035f, -11.2f);
            game.InjectBall(new Vector3(x, 1, -8.5f), new Vector3(0, 2, vz));
        }
        static float Roll(TennisGame game)
        {
            var hero = game.Player.GetComponentInChildren<HeroTennisDriver>();
            return hero ? Mathf.Abs(Mathf.DeltaAngle(0, hero.transform.localEulerAngles.z)) : 0;
        }
        [UnityTest, Timeout(180000)] public IEnumerator SelectionStretchAndConfirmedContactRules()
        {
            yield return SceneManager.LoadSceneAsync("Tennis"); yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>(); game.ManualSimulation = true;
            string captures = "../ArtDir/screenshots/tennis_abilities"; Directory.CreateDirectory(captures);
            game.ConfigureMatch(TennisGame.Mode.Training, null, null, null);
            Assert.IsFalse(game.SelectUltimate(2)); game.LockLoadout();
            Assert.IsFalse(game.SelectUltimate(1), "cannot switch after Ready");
            Assert.IsNull(typeof(TennisGame).GetMethod("RequestDive"), "the dive is gone");

            // A ball within reach: an ordinary swing, no lunge.
            Wide(game, .8f); int stretches = game.Stretches;
            game.RequestSwing(.7f);
            Assert.IsFalse(game.StretchActive, "a ball within reach is not stretched for");
            Assert.AreEqual(stretches, game.Stretches);

            // A ball 2.2 m out: the swing lunges toward it, upright, about a metre, in under a quarter second.
            Wide(game, 2.2f); stretches = game.Stretches;
            var before = game.Player.transform.position;
            game.RequestSwing(.7f);
            Assert.IsTrue(game.StretchActive, "a swing at a ball just out of reach stretches for it");
            Assert.AreEqual(stretches + 1, game.Stretches);
            float maxRoll = 0;
            for (int f = 0; f < 20; f++) {
                game.Step(1f/60); yield return null;
                maxRoll = Mathf.Max(maxRoll, Roll(game));
                if (f == 6 || f == 12) Capture(game, captures + "/stretch-" + f + ".png");
            }
            Assert.IsFalse(game.StretchActive, "the lunge is over within a quarter second");
            float moved = game.Player.transform.position.x - before.x;
            Assert.That(moved, Is.InRange(.8f, 1.6f), "the lunge (plus any run) carries the player toward the ball");
            Assert.Less(maxRoll, 1f, "the hero stays upright: no dive roll");
            Capture(game, captures + "/stretch.png");

            // Too wide for anything (beyond the old dive's reach): no lunge.
            Wide(game, 3.4f); stretches = game.Stretches;
            game.RequestSwing(.7f);
            Assert.IsFalse(game.StretchActive); Assert.AreEqual(stretches, game.Stretches);

            // Exercise the real ball/racket contact path over a short timing sweep: a stretched swing returns the ball, weakly.
            bool saved = false;
            for (float at = 0; at < .3f && !saved; at += .02f) {
                Wide(game, 2.2f);
                int returns = game.Returns; bool attempted = false, stretched = false;
                for (float t = 0; t < 1.5f; t += 1f/60) {
                    if (!attempted && t >= at) { attempted = true; game.RequestSwing(.7f); stretched = game.StretchActive; }
                    game.Step(1f/60); yield return null;
                    if (game.Returns > returns) { saved = stretched; break; }
                }
                if (saved) Assert.LessOrEqual(game.LastHit.Quality, TennisRules.StretchQualityCap + 1e-4f, "a stretched return is weak");
            }
            Assert.IsTrue(saved, "a timed stretch must return a wide incoming ball through real contact");

            game.ConfigureMatch(TennisGame.Mode.Training, null, null, null);
            game.Player.CancelSwing(); game.Player.Tick(2, 0);
            game.InjectBall(game.Player.transform.position + new Vector3(.6f, 2, 1), Vector3.zero);
            Charge(game); // Even an old full meter cannot activate an ultimate.
            Assert.IsFalse(game.CanArmUltimate);
            Assert.IsFalse(game.ToggleUltimate());
            game.Player.Swing(.7f, false, TennisActor.Stroke.Drive);
            Contact(game);
            Assert.That(game.PlayerUltimate, Is.Zero);
            Assert.IsFalse(game.UltimateArmed);
            game.ConfigureMatch(TennisGame.Mode.Training, null, null, null);
            Assert.That(game.PlayerUltimate, Is.Zero); Assert.IsFalse(game.StretchActive);
        }
    }
}
