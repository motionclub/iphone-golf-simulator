using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using GolfArcade.Bowling;
using GolfArcade.Multiplayer;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    /// Phone casting, bowling (PLAN_PhoneCasting_GolfBowling.md Phase 4), on the real Bowling scene. One phone is the screen (it bowls
    /// for no one) and each player's phone is only their controller, with no picture of its own. So:
    /// - the screen shows a bowler lining up as it happens (board, aim, picking the ball up), walks them up on their own beat, lets
    ///   the ball go when their throw arrives (never on its own), and scores it with the bowler's pinfall (every sheet agrees);
    /// - the bowler's phone says how it is lining up, sends the throw the moment the ball leaves the hand, then its pinfall;
    /// - a game with no screen still sends one throw, with its pinfall, once the pins have settled (unchanged).
    public class PhoneCastingBowlingTests
    {
        static NetworkConfiguration Config(string local, bool screen)
        {
            var people = screen
                ? new[] { new NetworkParticipant { id = "screen", name = "Screen", seat = -1, castScreen = true }, new NetworkParticipant { id = "b", name = "Sam", seat = 0 } }
                : new[] { new NetworkParticipant { id = "b", name = "Sam", seat = 0 }, new NetworkParticipant { id = "c", name = "Ana", seat = 1 } };
            return new NetworkConfiguration { lobbyID = "lobby", matchID = "match", hostID = screen ? "screen" : "b", localID = local, sport = "bowling", venue = "club", seed = 7, participants = people };
        }
        static string Ball(string kind, int ball, float board = 0, float aim = 0, int phase = 0, int seq = 0, int after = -1, int grade = 0)
            => JsonUtility.ToJson(new BowlingGame.NetBall { kind = kind, ball = ball, seat = 0, board = board, aim = aim, phase = phase, seq = seq, after = after, grade = grade, speed = 7.4f, rpm = 250, axis = 30 });

        BowlingGame game;
        readonly List<BowlingGame.NetBall> sent = new List<BowlingGame.NetBall>();

        IEnumerator Load(NetworkConfiguration c)
        {
            yield return SceneManager.LoadSceneAsync("Bowling"); yield return null; yield return null;
            game = UnityEngine.Object.FindFirstObjectByType<BowlingGame>();
            Assert.IsNotNull(game, "the Bowling scene has a BowlingGame");
            game.MotionInput = false; game.Autoplay.Clear();
            sent.Clear();
            SportsMultiplayer.TestOutput = json =>
            {
                var p = JsonUtility.FromJson<NetworkPacket>(json);
                if (p?.kind != "peer") return;
                var m = JsonUtility.FromJson<BowlingGame.NetBall>(p.payload);
                if (m != null && m.kind != "hb") sent.Add(m);
            };
            SportsMultiplayer.Configure(JsonUtility.ToJson(c));
            // the first bowler walks up to the approach
            float until = Time.realtimeSinceStartup + 5; while (Time.realtimeSinceStartup < until) yield return null;
        }
        /// With CAST_PROOF set: the screen phone's picture (the game camera and its HUD), sideways at an iPhone Pro Max's 2556×1179.
        IEnumerator Capture(string name)
        {
            string dir = Environment.GetEnvironmentVariable("CAST_PROOF");
            if (string.IsNullOrEmpty(dir)) yield break;
            System.IO.Directory.CreateDirectory(dir);
            const int W = 2556, H = 1179;
            var cam = game.GameplayCamera; var old = cam.targetTexture;
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            cam.targetTexture = rt; cam.aspect = (float)W / H;
            yield return null; yield return null;   // (the HUD lays itself out for the new frame size)
            cam.aspect = (float)W / H; cam.Render();
            var shot = new Texture2D(W, H, TextureFormat.RGB24, false);
            var active = RenderTexture.active; RenderTexture.active = rt; shot.ReadPixels(new Rect(0, 0, W, H), 0, 0); shot.Apply(); RenderTexture.active = active;
            System.IO.File.WriteAllBytes(System.IO.Path.Combine(dir, name + ".png"), shot.EncodeToPNG());
            cam.targetTexture = old; cam.ResetAspect(); UnityEngine.Object.Destroy(shot); rt.Release();
        }
        [TearDown] public void Done() { SportsMultiplayer.TestOutput = null; SportsMultiplayer.Shutdown(); }

        static IEnumerator Until(Func<bool> done, float seconds)
        {
            float end = Time.realtimeSinceStartup + seconds;
            while (!done() && Time.realtimeSinceStartup < end) yield return null;
        }

        [UnityTest, Timeout(120000)]
        public IEnumerator TheScreenWalksTheBowlerUpLiveAndScoresWithTheirPinfall()
        {
            yield return Load(Config("screen", screen: true));
            Assert.AreEqual(-1, game.LocalPlayer, "the screen bowls for no one");
            Assert.AreEqual(BowlingGame.Phase.Setup, game.Flow);

            // the bowler slides to board 15 and aims a touch right: the screen shows it as it happens
            game.ReceiveNetwork(Ball("setup", 0, board: 15, aim: 1, phase: 0, seq: 1));
            yield return null;
            Assert.AreEqual(15f, game.Board, 1e-3f); Assert.AreEqual(1f, game.AimDeg, 1e-3f);
            yield return Capture("bowling_screen_setup");
            // an older slide that arrives late does not undo it
            game.ReceiveNetwork(Ball("setup", 0, board: 9, phase: 0, seq: 0));
            Assert.AreEqual(15f, game.Board, 1e-3f);

            // they pick the ball up: the screen holds it with them, then walks them up on the same beat as their phone
            game.ReceiveNetwork(Ball("setup", 0, board: 15, aim: 1, phase: 1, seq: 2));
            yield return null;
            Assert.AreEqual(BowlingGame.Phase.Hold, game.Flow);
            yield return Until(() => game.Flow == BowlingGame.Phase.Approach, 3);
            Assert.AreEqual(BowlingGame.Phase.Approach, game.Flow, "the walk-up starts after the hold, as on the bowler's phone");

            // the ball is theirs: the screen never lets go on its own, however long their throw takes to arrive
            yield return Until(() => game.Flow != BowlingGame.Phase.Approach, 4);
            Assert.AreEqual(BowlingGame.Phase.Approach, game.Flow, "no ball of the screen's own");
            Assert.AreEqual(0, game.Scores[0].Rolls.Count);

            // their throw, sent as it left their hand (its pinfall not known yet): the ball goes at once
            game.ReceiveNetwork(Ball("throw", 0, board: 15, grade: (int)ReleaseGrade.Perfect));
            yield return Until(() => game.Flow == BowlingGame.Phase.Rolling || game.Flow == BowlingGame.Phase.Pins, 2);
            Assert.That(game.Flow, Is.EqualTo(BowlingGame.Phase.Rolling).Or.EqualTo(BowlingGame.Phase.Pins));
            yield return Capture("bowling_screen_rolling");

            // the score waits for their pinfall: here, two pins left (7 and 10 standing)
            yield return Until(() => game.Flow == BowlingGame.Phase.Pins, 8);
            yield return Until(() => game.Scores[0].Rolls.Count > 0, 2.5f);
            Assert.AreEqual(0, game.Scores[0].Rolls.Count, "no score before the bowler's pinfall is here");
            int sevenTen = BowlingLeave.Mask(7, 10);
            game.ReceiveNetwork(Ball("pinfall", 0, after: sevenTen));
            yield return Until(() => game.Scores[0].Rolls.Count > 0, 10);
            Assert.AreEqual(1, game.Scores[0].Rolls.Count);
            Assert.AreEqual(8, game.Scores[0].Rolls[0], "scored with the bowler's own pinfall, whatever the screen's pins did");
        }

        [UnityTest, Timeout(120000)]
        public IEnumerator TheBowlersPhoneSendsItsSetupTheThrowAsItLeavesTheHandThenThePinfall()
        {
            yield return Load(Config("b", screen: true));
            Assert.AreEqual(0, game.LocalPlayer);
            game.Autoplay.Enqueue(new BowlingGame.Shot(18, 7.4f, 250, 30, 0f));
            yield return Until(() => sent.Any(m => m.kind == "pinfall"), 25);
            var kinds = sent.Select(m => m.kind).ToList();
            int hold = sent.FindIndex(m => m.kind == "setup" && m.phase == 1), thrown = kinds.IndexOf("throw"), pinfall = kinds.IndexOf("pinfall");
            Assert.GreaterOrEqual(hold, 0, "the hold went to the screen: " + string.Join(",", kinds));
            Assert.Greater(thrown, hold); Assert.Greater(pinfall, thrown);
            Assert.AreEqual(1, kinds.Count(k => k == "throw")); Assert.AreEqual(1, kinds.Count(k => k == "pinfall"));
            Assert.AreEqual(-1, sent[thrown].after, "the throw goes as the ball leaves the hand, before its pins are known");
            Assert.AreEqual(18f, sent.Last(m => m.kind == "setup").board, .51f, "the last board the screen saw is where the bowler stood");
            Assert.That(sent[pinfall].after, Is.InRange(0, (1 << 10) - 1));
            Assert.IsTrue(sent.Where(m => m.kind == "setup").Select(m => m.seq).SequenceEqual(sent.Where(m => m.kind == "setup").Select(m => m.seq).OrderBy(s => s)), "setup words go out in order");
        }

        [UnityTest, Timeout(120000)]
        public IEnumerator WithoutAScreenOneThrowGoesWithItsPinfallAsBefore()
        {
            yield return Load(Config("b", screen: false));
            game.Autoplay.Enqueue(new BowlingGame.Shot(18, 7.4f, 250, 30, 0f));
            yield return Until(() => sent.Any(m => m.kind == "throw"), 25);
            yield return Until(() => game.Scores[0].Rolls.Count > 0, 10);
            var kinds = sent.Select(m => m.kind).ToList();
            Assert.AreEqual(new[] { "throw" }, kinds.ToArray(), "no setup or pinfall words: " + string.Join(",", kinds));
            Assert.That(sent[0].after, Is.InRange(0, (1 << 10) - 1), "the throw carries its pinfall");
        }
    }
}
