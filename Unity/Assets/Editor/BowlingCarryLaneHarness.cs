#if UNITY_EDITOR
using System;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using GolfArcade.Bowling;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// Pin carry at the speeds the game really delivers (11-21 skill pass). The 10-26 carry gate tuned the deck on balls
    /// reaching the pins at 6.0-6.8 m/s; a lane-rolled ball released at 16-22 mph gets there at ~6.0-8.8 (7.2-7.9 for a normal
    /// 19.5 mph ball), and at those speeds a hook in the pocket barely out-carried a straight one. Buckets: board ±0.75, entry
    /// ±0.5°, speed 6.5-8.5 m/s, rolling. Sweeps `BowlingPinDeck.Tuning` (and BowlingSkill.On) like the old gate.
    ///   -executeMethod GolfArcade.EditorTools.BowlingCarryLaneHarness.Run  BOWL_OUT=<dir> BOWL_N=<per bucket, 150> BOWL_TUNE="a=1,b=2;c=3"
    public static class BowlingCarryLaneHarness
    {
        public struct Bucket
        {
            public string Name; public float Board, Angle, Lo, Hi, SpeedLo, SpeedHi;
            public Bucket(string n, float board, float angle, float lo, float hi, float sLo = 6.5f, float sHi = 8.5f)
            { Name = n; Board = board; Angle = angle; Lo = lo; Hi = hi; SpeedLo = sLo; SpeedHi = sHi; }
        }

        /// Targets: real-world carry rates for these hits (a good hook in the pocket strikes most of the time, a straight ball in
        /// the same spot about a third), plus the old gate's off-pocket ranges.
        public static readonly Bucket[] Buckets =
        {
            new Bucket("Pocket 5.5-6.5° (big hook)", 17.5f, 6f, 78, 92),
            new Bucket("Pocket 4-5°", 17.5f, 4.5f, 70, 85),
            new Bucket("Pocket 2-3°", 17.5f, 2.5f, 45, 65),
            new Bucket("Pocket straight 0-1°", 17.5f, .5f, 25, 45),
            new Bucket("Pocket 4-5°, slow 6.0-6.6", 17.5f, 4.5f, 60, 85, 6.0f, 6.6f),
            new Bucket("Pocket 4-5°, fast 8.0-8.8", 17.5f, 4.5f, 65, 92, 8.0f, 8.8f),
            new Bucket("Light pocket", 16.0f, 5f, 25, 45),
            new Bucket("Brooklyn", 22.5f, 5f, 12, 32),
            new Bucket("Head-on", 20f, 3f, 3, 17),
        };

        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

        /// Lane-rolled buckets (BOWL_LANE=1): real throws (release → lane integrator) whose start board is solved continuously
        /// (bisection) so they meet the head-pin line on target board ±0.75; checks the lane's arrivals carry like the rolling ones.
        static readonly (string name, float target, float mph, float rpm, float axis, float aim)[] LaneBuckets =
        {
            ("Lane: straight 19.5 mph into the pocket", 17.5f, 19.5f, 160, 0, 0),
            ("Lane: hook 360/45 into the pocket", 17.5f, 19.5f, 360, 45, 0),
            ("Lane: big hook 500/65 into the pocket", 17.5f, 19.5f, 500, 65, .75f),
            ("Lane: straight, dead on board 17.5", 17.5f, 19.5f, 160, 0, 0),
        };

        static BallState LaneBall(float target, float mph, float rpm, float axis, float aim)
        {
            BallState Throw(float board)
            {
                var th = BowlingRelease.Resolve(new BowlingSwing { Board = board, Speed = mph / 2.237f, RevRpm = rpm, AxisDeg = axis, AimDeg = aim, TimingError = 0, Seed = 1 });
                return BowlingBall.Roll(th.Launch(), OilPattern.House);
            }
            float At(in BallState e) => e.Phase != BallPhase.Deck || e.Velocity.z < .1f ? float.NaN
                : BowlingLane.XBoard(e.Position.x + e.Velocity.x / e.Velocity.z * (BowlingLane.FoulToHeadPin - e.Position.z));
            float lo = 1, hi = 39;   // the arrival board rises with the start board
            for (int i = 0; i < 30; i++)
            {
                float mid = (lo + hi) / 2, a = At(Throw(mid));
                if (float.IsNaN(a) || a < target) lo = mid; else hi = mid;
            }
            return Throw((lo + hi) / 2);
        }

        public static void Run()
        {
            int code = 0;
            bool skillWas = BowlingSkill.On;
            try
            {
                string dir = Path.GetFullPath(Environment.GetEnvironmentVariable("BOWL_OUT") ?? "../work/bowling-skill-1121/proof");
                Directory.CreateDirectory(dir);
                int n = int.TryParse(Environment.GetEnvironmentVariable("BOWL_N"), out int nn) ? nn : 150;
                var fields = typeof(BowlingPinDeck.Tuning).GetFields(BindingFlags.Public | BindingFlags.Static);
                var defaults = new object[fields.Length];
                for (int i = 0; i < fields.Length; i++) defaults[i] = fields[i].GetValue(null);
                var md = new StringBuilder($"# Pin carry at lane speeds (N = {n} per bucket)\n\n");
                var summary = new StringBuilder("| Tuning | Pass | " + string.Join(" | ", Array.ConvertAll(Buckets, b => b.Name)) + " |\n|---|---|" + new string('-', 0) + string.Concat(Array.ConvertAll(Buckets, b => "---|")) + "\n");
                foreach (var tune in (Environment.GetEnvironmentVariable("BOWL_TUNE") ?? "").Split(';'))
                {
                    for (int i = 0; i < fields.Length; i++) fields[i].SetValue(null, defaults[i]);
                    BowlingSkill.On = skillWas;
                    foreach (var part in tune.Split(','))
                    {
                        var kv = part.Split('='); if (kv.Length != 2) continue;
                        string k = kv[0].Trim();
                        if (k == "Skill") { BowlingSkill.On = kv[1].Trim() == "1"; continue; }
                        var f = Array.Find(fields, x => x.Name == k);
                        if (f == null) { Debug.LogWarning("[BowlingCarryLane] unknown " + k); continue; }
                        f.SetValue(null, f.FieldType == typeof(int) ? (object)int.Parse(kv[1], Inv) : float.Parse(kv[1], Inv));
                    }
                    var scene = EditorSceneManager.NewPreviewScene();
                    var t0 = DateTime.Now;
                    md.Append($"## `{(tune == "" ? "default" : tune)}`\n\n| Bucket | Strike % | Target | Pass | Mean pins | Top leaves |\n|---|---|---|---|---|---|\n");
                    summary.Append($"| `{(tune == "" ? "default" : tune)}` |");
                    var cells = new StringBuilder(); int pass = 0;
                    try
                    {
                        using var deck = new BowlingPinDeck(scene);
                        foreach (var b in Buckets)
                        {
                            var rng = new System.Random(4321);
                            int strikes = 0; float pins = 0;
                            var leaves = new System.Collections.Generic.Dictionary<string, int>();
                            for (int i = 0; i < n; i++)
                            {
                                float board = b.Board + (float)(rng.NextDouble() * 1.5 - .75);
                                float angle = Mathf.Max(0, b.Angle + (float)(rng.NextDouble() - .5));
                                float speed = b.SpeedLo + (float)rng.NextDouble() * (b.SpeedHi - b.SpeedLo);
                                var act = deck.Simulate(BowlingPinDeck.Arrival(board, angle, speed), BowlingLeave.All);
                                if (act.StandingAfter == 0) strikes++;
                                else { string key = BowlingLeave.Numbers(act.StandingAfter); leaves[key] = leaves.TryGetValue(key, out int c) ? c + 1 : 1; }
                                pins += act.Knocked;
                            }
                            float rate = 100f * strikes / n;
                            bool ok = rate >= b.Lo - .01f && rate <= b.Hi + .01f; if (ok) pass++;
                            var top = new System.Collections.Generic.List<System.Collections.Generic.KeyValuePair<string, int>>(leaves);
                            top.Sort((x, y) => y.Value.CompareTo(x.Value));
                            var lt = new StringBuilder();
                            for (int li = 0; li < Mathf.Min(4, top.Count); li++) lt.Append(li > 0 ? ", " : "").Append(top[li].Key).Append(" ×").Append(top[li].Value);
                            md.Append($"| {b.Name} | {rate.ToString("0", Inv)} | {b.Lo}-{b.Hi} | {(ok ? "PASS" : "FAIL")} | {(pins / n).ToString("0.00", Inv)} | {lt} |\n");
                            cells.Append($" {rate.ToString("0", Inv)}{(ok ? "" : "✗")} |");
                        }
                        if (Environment.GetEnvironmentVariable("BOWL_LANE") == "1")
                            foreach (var lb in LaneBuckets)
                            {
                                var rng = new System.Random(99); int strikes = 0; float pins = 0, entry = 0;
                                bool dead = lb.name.Contains("dead on");
                                for (int i = 0; i < n; i++)
                                {
                                    var end = LaneBall(lb.target + (dead ? 0 : (float)(rng.NextDouble() * 1.5 - .75)), lb.mph, lb.rpm, lb.axis, lb.aim);
                                    entry += Mathf.Atan2(-end.Velocity.x, end.Velocity.z) * Mathf.Rad2Deg;
                                    var act = deck.Simulate(end, BowlingLeave.All);
                                    if (act.StandingAfter == 0) strikes++; pins += act.Knocked;
                                }
                                md.Append($"| {lb.name} (entry {(entry / n).ToString("0.0", Inv)}°) | {(100f * strikes / n).ToString("0", Inv)} | - | - | {(pins / n).ToString("0.00", Inv)} | |\n");
                                cells.Append($" {lb.name}: {(100f * strikes / n).ToString("0", Inv)} |");
                            }
                    }
                    finally { EditorSceneManager.ClosePreviewScene(scene); }
                    md.Append($"\n{pass}/{Buckets.Length} in range, {(DateTime.Now - t0).TotalSeconds:0} s\n\n");
                    summary.Append($" {pass}/{Buckets.Length} |{cells}\n");
                    Debug.Log($"[BowlingCarryLane] {tune}: {pass}/{Buckets.Length} {cells}");
                    File.WriteAllText(Path.Combine(dir, "carry-lane.md"), "# Summary (✗ = out of range)\n\n" + summary + "\n" + md);
                }
            }
            catch (Exception e) { Debug.LogException(e); code = 1; }
            finally { BowlingSkill.On = skillWas; }
            if (Application.isBatchMode) EditorApplication.Exit(code);
        }
    }
}
#endif
