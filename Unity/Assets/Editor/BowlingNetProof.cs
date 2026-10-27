#if UNITY_EDITOR
using System;
using System.Collections;
using System.IO;
using System.Text;
using GolfArcade.Bowling;
using GolfArcade.Multiplayer;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// Two phones bowling one game (PLAN_PhonePlay §6 / gate G7), in one editor: a host game and a guest game run side by side,
    /// the peer packets each sends are handed to the other (SportsMultiplayer.TestOutput), and each bowls only its own player
    /// (a computer bowler stands in for the person). At the end both score sheets must agree frame by frame.
    ///   -executeMethod GolfArcade.EditorTools.BowlingNetProof.Run   BOWL_OUT=<dir>
    [InitializeOnLoad]
    public static class BowlingNetProof
    {
        const string Flag = "BowlingNetProof";
        static IEnumerator script;
        static int lastFrame = -1;

        static BowlingNetProof() { EditorApplication.update += Tick; }

        public static void Run()
        {
            script = null; lastFrame = -1;
            if (!File.Exists(BowlingFilm.ScenePath)) BowlingFilm.EnsureScene();
            EditorSceneManager.OpenScene(BowlingFilm.ScenePath);
            EditorUtility.audioMasterMute = true;
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount;
            try { script ??= Prove(); if (!script.MoveNext()) Finish(code); }
            catch (Exception e) { Debug.LogException(e); Finish(1); }
        }

        static int code;
        static void Finish(int c)
        {
            SessionState.SetBool(Flag, false); Time.timeScale = 1; SportsMultiplayer.TestOutput = null; SportsMultiplayer.Shutdown();
            if (Application.isBatchMode) EditorApplication.Exit(c); else EditorApplication.isPlaying = false;
        }

        static IEnumerator Prove()
        {
            string dir = Path.GetFullPath(Environment.GetEnvironmentVariable("BOWL_OUT") ?? "../work/bowling/proof/net");
            Directory.CreateDirectory(dir);
            var host = Object.FindFirstObjectByType<BowlingGame>();
            while (!host.Initialized) yield return null;
            var guest = new GameObject("Guest phone").AddComponent<BowlingGame>();
            float boot = Time.realtimeSinceStartup;
            while (!guest.Initialized)
            {
                if (Time.realtimeSinceStartup - boot > 60) throw new Exception("the guest game never started (see the log above)");
                yield return null;
            }
            // one picture and one listener: the guest's camera and its listener off (it still runs the whole game)
            if (guest.GameplayCamera) { guest.GameplayCamera.enabled = false; var l = guest.GameplayCamera.GetComponent<AudioListener>(); if (l) Object.Destroy(l); }

            NetworkConfiguration Config(string local) => new NetworkConfiguration
            {
                lobbyID = "L", matchID = "M", hostID = "A", localID = local, sport = "bowling", venue = "club", seed = 1,
                participants = new[] { new NetworkParticipant { id = "A", name = "Ana", seat = 0 }, new NetworkParticipant { id = "B", name = "Ben", seat = 1, female = true } },
            };
            SportsMultiplayer.Configure(JsonUtility.ToJson(Config("A")));   // the link (its packets come out of TestOutput)
            host.ConfigureNetwork(Config("A")); guest.ConfigureNetwork(Config("B"));
            int delivered = 0;
            SportsMultiplayer.TestOutput = json =>
            {
                var p = JsonUtility.FromJson<NetworkPacket>(json);
                if (p == null || p.kind != "peer") return;
                var m = JsonUtility.FromJson<BowlingGame.NetBall>(p.payload);
                if (m == null || m.kind != "throw") return;
                (m.seat == 0 ? guest : host).ReceiveNetwork(p.payload); delivered++;
            };

            Time.timeScale = 3;
            var rng = new System.Random(4);
            float start = Time.realtimeSinceStartup;
            while (Time.realtimeSinceStartup - start < 900)
            {
                // each phone bowls its own player (a computer bowler plays the person's part)
                foreach (var (game, me, skill) in new[] { (host, 0, .7f), (guest, 1, .45f) })
                    if (game.Flow == BowlingGame.Phase.Setup && game.Current == me && game.Autoplay.Count == 0)
                        game.Autoplay.Enqueue(BowlingCpu.Plan(skill, game.StandingPins, game.Oil, rng));
                if (host.Flow == BowlingGame.Phase.GameOver && guest.Flow == BowlingGame.Phase.GameOver) break;
                yield return null;
            }

            var md = new StringBuilder("# Two phones, one game (bowling over the network)\n\n");
            bool done = host.Flow == BowlingGame.Phase.GameOver && guest.Flow == BowlingGame.Phase.GameOver, same = done;
            for (int p = 0; p < 2; p++)
            {
                var a = host.Scores[p]; var b = guest.Scores[p];
                var sa = new StringBuilder(); var sb = new StringBuilder();
                for (int f = 0; f < 10; f++) { sa.Append('[').Append(a.Mark(f, 0)).Append(a.Mark(f, 1)).Append(f == 9 ? a.Mark(f, 2) : "").Append(']'); sb.Append('[').Append(b.Mark(f, 0)).Append(b.Mark(f, 1)).Append(f == 9 ? b.Mark(f, 2) : "").Append(']'); }
                same &= sa.ToString() == sb.ToString() && a.Total == b.Total;
                md.Append($"- {host.Players[p]}: host {sa} {a.Total} · guest {sb} {b.Total}\n");
            }
            md.Append($"\n{delivered} balls sent between the phones.\n\nGATE: G7 bowling two phones score the same game {(same ? "PASS" : "FAIL")}{(done ? "" : " (the game did not finish)")}\n");
            File.WriteAllText(Path.Combine(dir, "GATE_RESULTS.md"), md.ToString());
            Debug.Log("[BowlingNetProof]\n" + md);
            code = same ? 0 : 2;
        }
    }
}
#endif
