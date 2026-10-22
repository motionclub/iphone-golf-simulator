using System.Collections;
using System.IO;
using System.Text;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GolfArcade.PlayTests
{
    /// How often does a person-timed swing at a lob actually produce an overhead return?
    /// The swing is a phone swing (onset, then confirmation), started `offset` seconds before the ball drops to contact height.
    public class TennisOverheadProbeTests
    {
        static string Out => System.Environment.GetEnvironmentVariable("OVERHEAD_PROBE_OUT") ?? "Library/Captures/overhead-probe";

        static float ContactTime(Vector3 p, Vector3 v)
        {
            float t = 0;
            for (int i = 0; i < 1200; i++) {
                float before = p.y;
                TennisBall.Integrate(ref p, ref v, 0, TennisBall.Step, 0);
                t += TennisBall.Step;
                if (v.y < 0 && before > 2.45f && p.y <= 2.45f) return t;
            }
            return -1;
        }

        [UnityTest, Explicit, Timeout(1800000)] public IEnumerator Sweep()
        {
            LogAssert.ignoreFailingMessages = true;
            yield return SceneManager.LoadSceneAsync("Tennis"); yield return null;
            var game = Object.FindFirstObjectByType<TennisGame>(); game.ManualSimulation = true; game.NativeControlled = true;
            Directory.CreateDirectory(Out);
            var csv = new StringBuilder("apex,landX,landZ,offset,tracked,smashSwing,hit,kind,feedback,gap\n");
            var summary = new System.Collections.Generic.Dictionary<float, int[]>();
            foreach (float apex in new[] { 4.4f, 6f })
            foreach (float landZ in new[] { -8.5f, -11f })
            foreach (float landX in new[] { -2.5f, 0f, 2.5f })
            foreach (float offset in new[] { -1.5f, -1.3f, -1.0f, -0.8f, -0.6f, -0.5f, -0.4f, -0.3f, -0.2f, -0.1f, 0f, 0.1f, 0.15f, 0.2f }) {
                game.ConfigureMatch(TennisGame.Mode.Exhibition, null, null, null);
                game.AutoPlay = false; game.Player.CancelSwing(); game.Player.Tick(2, 0);
                game.Player.transform.position = new Vector3(0, .035f, -11.2f);
                var from = new Vector3(.5f, 1f, 11f);
                var vel = TennisAbilities.LobVelocity(from, new Vector3(landX, TennisRules.BallRadius, landZ), apex);
                float tC = ContactTime(from, vel);
                if (tC < 0) continue;
                game.InjectBall(from, vel);
                int hits = game.Hits; bool tracked = false, smash = false, swung = false; float swingAt = tC + offset; float t = 0;
                int confirmAt = -1;
                for (int f = 0; f < 600 && game.Flow == TennisGame.Phase.Rally && game.Hits == hits; f++) {
                    t += 1f / 60;
                    if (!swung && t >= swingAt) { game.BeginSwing(0, 0, 1); confirmAt = f + 3; swung = true; }
                    if (confirmAt == f) game.RequestSwing(.85f, 0, 0, 1);
                    game.Step(1f / 60); yield return null;
                    tracked |= game.TrackingOverhead; smash |= game.Player.Kind == TennisActor.Stroke.Smash && game.Player.Swinging;
                    if (t > tC + 1.2f) break;
                }
                bool hit = game.Hits > hits;
                var key = apex; if (!summary.ContainsKey(key)) summary[key] = new int[2];
                summary[key][0]++; if (hit) summary[key][1]++;
                csv.AppendLine($"{apex},{landX},{landZ},{offset},{tracked},{smash},{hit},{game.Player.Kind},{game.Feedback?.Replace("\n"," ")},{game.LastContactGap:F3}");
            }
            File.WriteAllText(Path.Combine(Out, "overhead-probe.csv"), csv.ToString());
            foreach (var kv in summary) Debug.Log($"[OverheadProbe] apex={kv.Key} trials={kv.Value[0]} hits={kv.Value[1]}");
        }
    }
}
