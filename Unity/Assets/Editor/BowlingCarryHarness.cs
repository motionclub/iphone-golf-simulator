#if UNITY_EDITOR
using System;
using System.Globalization;
using System.IO;
using System.Text;
using GolfArcade.Bowling;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// Gate P3/P4 (PLAN_Bowling.md §6.2, §12): strike rate by where and how the ball enters the
    /// pins, from real PhysX pin action. Batch:
    ///   -executeMethod GolfArcade.EditorTools.BowlingCarryHarness.Run
    ///   BOWL_OUT=<dir>  BOWL_N=<throws per bucket, default 300>  BOWL_TUNE="PinBounce=.6,KickbackBounce=.7"
    /// Writes carry.md + carry.json.
    public static class BowlingCarryHarness
    {
        public struct Bucket
        {
            public string Name; public float Board, Angle, Lo, Hi;
            public Bucket(string name, float board, float angle, float lo, float hi) { Name = name; Board = board; Angle = angle; Lo = lo; Hi = hi; }
        }

        /// Entry board at the head-pin line, entry angle (degrees, moving left), target strike % range.
        public static readonly Bucket[] Buckets =
        {
            new Bucket("Pocket 4-6°", 17.5f, 5f, 75, 85),
            new Bucket("Pocket straight 1-2°", 17.5f, 1.5f, 40, 50),
            new Bucket("Light pocket", 16.0f, 5f, 28, 42),
            new Bucket("Brooklyn", 22.5f, 5f, 18, 32),
            new Bucket("Head-on", 20f, 3f, 3, 17),
            new Bucket("Gutter-side edge", 6f, 2f, 0, 0),
        };

        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

        public static float StrikeRate(BowlingPinDeck deck, Bucket b, int n, int seed, out float meanKnocked, out int escaped, out float meanSettle)
            => StrikeRate(deck, b, n, seed, out meanKnocked, out escaped, out meanSettle, null);

        public static float StrikeRate(BowlingPinDeck deck, Bucket b, int n, int seed, out float meanKnocked, out int escaped, out float meanSettle,
            System.Collections.Generic.Dictionary<string, int> leaves)
        {
            var rng = new System.Random(seed);
            int strikes = 0; float knocked = 0, settle = 0; escaped = 0;
            for (int i = 0; i < n; i++)
            {
                float board = b.Board + (float)(rng.NextDouble() * 1.5 - .75);
                float angle = Mathf.Max(0, b.Angle + (float)(rng.NextDouble() * 2 - 1));
                float speed = 6.0f + (float)rng.NextDouble() * .8f;
                var act = deck.Simulate(BowlingPinDeck.Arrival(board, angle, speed), BowlingLeave.All);
                if (act.StandingAfter == 0) strikes++;
                else if (leaves != null) { string k = BowlingLeave.Numbers(act.StandingAfter); leaves[k] = leaves.TryGetValue(k, out int c) ? c + 1 : 1; }
                knocked += act.Knocked; escaped += act.Escaped; settle += act.SettleTime;
            }
            meanKnocked = knocked / n; meanSettle = settle / n;
            return 100f * strikes / n;
        }

        public static void ApplyTuning(string spec)
        {
            if (string.IsNullOrEmpty(spec)) return;
            foreach (var part in spec.Split(','))
            {
                var kv = part.Split('=');
                if (kv.Length != 2) continue;
                var f = typeof(BowlingPinDeck.Tuning).GetField(kv[0].Trim());
                if (f == null) { Debug.LogWarning("[BowlingCarry] unknown tuning " + kv[0]); continue; }
                if (f.FieldType == typeof(int)) f.SetValue(null, int.Parse(kv[1], Inv));
                else f.SetValue(null, float.Parse(kv[1], Inv));
            }
        }

        public static void Run()
        {
            int code = 0;
            try
            {
                string outDir = Path.GetFullPath(Environment.GetEnvironmentVariable("BOWL_OUT") ?? "../work/bowling/proof/carry");
                Directory.CreateDirectory(outDir);
                int n = int.TryParse(Environment.GetEnvironmentVariable("BOWL_N"), out int nn) ? nn : 300;
                var sweeps = (Environment.GetEnvironmentVariable("BOWL_TUNE") ?? "").Split(';');
                var fields = typeof(BowlingPinDeck.Tuning).GetFields();
                var defaults = new object[fields.Length];
                for (int i = 0; i < fields.Length; i++) defaults[i] = fields[i].GetValue(null);
                var md = new StringBuilder("# Bowling carry harness\n\n");
                var json = new StringBuilder("[");
                foreach (var tune in sweeps)
                {
                    for (int i = 0; i < fields.Length; i++) fields[i].SetValue(null, defaults[i]);
                    ApplyTuning(tune);
                    var scene = EditorSceneManager.NewPreviewScene();
                    using (var deck = new BowlingPinDeck(scene))
                    {
                        md.Append($"## Tuning `{(tune == "" ? "default" : tune)}` (N = {n} per bucket)\n\n| Bucket | Strike % | Target | Pass | Mean pins | Settle s | Escaped | Top leaves |\n|---|---|---|---|---|---|---|---|\n");
                        int pass = 0;
                        var t0 = DateTime.Now;
                        foreach (var b in Buckets)
                        {
                            var leaves = new System.Collections.Generic.Dictionary<string, int>();
                            float rate = StrikeRate(deck, b, n, 1234, out float mean, out int escaped, out float settle, leaves);
                            var top = new System.Collections.Generic.List<System.Collections.Generic.KeyValuePair<string, int>>(leaves);
                            top.Sort((x, y) => y.Value.CompareTo(x.Value));
                            var leaveText = new StringBuilder();
                            for (int li = 0; li < Mathf.Min(5, top.Count); li++) leaveText.Append(li > 0 ? ", " : "").Append(top[li].Key).Append(" ×").Append(top[li].Value);
                            bool ok = rate >= b.Lo - .01f && rate <= b.Hi + .01f && escaped == 0;
                            if (ok) pass++;
                            md.Append($"| {b.Name} | {rate.ToString("0.0", Inv)} | {b.Lo}-{b.Hi} | {(ok ? "PASS" : "FAIL")} | {mean.ToString("0.00", Inv)} | {settle.ToString("0.00", Inv)} | {escaped} | {leaveText} |\n");
                            json.Append($"{{\"tune\":\"{tune}\",\"bucket\":\"{b.Name}\",\"strike\":{rate.ToString("0.0", Inv)},\"pins\":{mean.ToString("0.00", Inv)},\"settle\":{settle.ToString("0.00", Inv)},\"escaped\":{escaped}}},");
                            Debug.Log($"[BowlingCarry] {tune} {b.Name}: {rate:0.0}% (target {b.Lo}-{b.Hi}) pins {mean:0.00} escaped {escaped} leaves {leaveText}");
                        }
                        md.Append($"\n{pass}/{Buckets.Length} buckets in range; {(DateTime.Now - t0).TotalSeconds:0} s\n\n");
                    }
                    EditorSceneManager.ClosePreviewScene(scene);
                }
                json.Length--; json.Append("]");
                File.WriteAllText(Path.Combine(outDir, "carry.md"), md.ToString());
                File.WriteAllText(Path.Combine(outDir, "carry.json"), json.ToString());
                Debug.Log("[BowlingCarry] wrote " + outDir);
            }
            catch (Exception e) { Debug.LogException(e); code = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(code);
        }
    }
}
#endif
