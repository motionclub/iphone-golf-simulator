#if UNITY_EDITOR
using System;
using System.IO;
using System.Text;
using GolfArcade.Bowling;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// Whole games, scored: the exhibition opponents (BowlingCpu) bowl ten-frame games on the real lane integrator and pin deck,
    /// scored by BowlingScore. Reports each opponent's average, strike and spare rates (the menu's "avg" numbers come from here).
    ///   -executeMethod GolfArcade.EditorTools.BowlingGameHarness.Run   BOWL_OUT=<dir>  BOWL_GAMES=<per opponent, default 12>  BOWL_TUNE=<deck tuning>
    public static class BowlingGameHarness
    {
        public static void Run()
        {
            int code = 0;
            try
            {
                string dir = Path.GetFullPath(Environment.GetEnvironmentVariable("BOWL_OUT") ?? "../work/bowling/proof/games");
                Directory.CreateDirectory(dir);
                int games = int.TryParse(Environment.GetEnvironmentVariable("BOWL_GAMES"), out int g) ? g : 12;
                BowlingCarryHarness.ApplyTuning(Environment.GetEnvironmentVariable("BOWL_TUNE"));
                var md = new StringBuilder($"# Exhibition opponents: {games} games each\n");
                // BOWL_CPU="BoardBase=1,BoardMiss=4;BoardBase=1.2": one table per CPU noise setting (BowlingCpu.Noise)
                foreach (var cpu in (Environment.GetEnvironmentVariable("BOWL_CPU") ?? "").Split(';'))
                {
                foreach (var part in cpu.Split(','))
                {
                    var kv = part.Split('='); if (kv.Length != 2) continue;
                    typeof(BowlingCpu.Noise).GetField(kv[0].Trim())?.SetValue(null, float.Parse(kv[1], System.Globalization.CultureInfo.InvariantCulture));
                }
                md.Append($"\n## CPU noise `{(cpu == "" ? "default" : cpu)}`\n\n| Opponent | Skill | Average | Low | High | Strike % | Spare % (of chances) | Fouls/drops |\n|---|---|---|---|---|---|---|---|\n");
                var scene = EditorSceneManager.NewPreviewScene();
                try
                {
                    using var deck = new BowlingPinDeck(scene);
                    var rng = new System.Random(7); int seed = 1;
                    foreach (var (name, skill) in BowlingCpu.Opponents)
                    {
                        int total = 0, low = 300, high = 0, strikes = 0, firstBalls = 0, spares = 0, chances = 0, bad = 0;
                        for (int k = 0; k < games; k++)
                        {
                            var score = new BowlingScore(); int standing = BowlingLeave.All;
                            while (!score.Complete)
                            {
                                bool first = score.FreshRack;
                                var shot = BowlingCpu.Plan(skill, standing, OilPattern.House, rng);
                                var th = BowlingRelease.Resolve(new BowlingSwing { Board = shot.Board, Speed = shot.Speed, RevRpm = shot.Rpm, AxisDeg = shot.Axis, TimingError = shot.Timing, Seed = seed++ });
                                int knocked = 0, after = standing;
                                if (!th.Dropped)
                                {
                                    var end = BowlingBall.Roll(th.Launch(), OilPattern.House);
                                    var act = deck.Simulate(end, standing);
                                    knocked = act.Knocked; after = act.StandingAfter;
                                }
                                if (th.Foul || th.Dropped) bad++;
                                int before = score.PinsStanding;
                                score.Roll(Mathf.Min(knocked, before), th.Foul);
                                if (first) { firstBalls++; if (knocked >= 10 && !th.Foul) strikes++; else chances++; }
                                else if (!th.Foul && knocked >= before) spares++;
                                standing = score.Complete || score.FreshRack ? BowlingLeave.All : after;
                            }
                            total += score.Total; low = Mathf.Min(low, score.Total); high = Mathf.Max(high, score.Total);
                        }
                        float avg = total / (float)games;
                        md.Append($"| {name} | {skill:0.00} | {avg:0} | {low} | {high} | {100f * strikes / Mathf.Max(1, firstBalls):0} | {100f * spares / Mathf.Max(1, chances):0} | {bad} |\n");
                        Debug.Log($"[BowlingGames] {name} skill {skill:0.00}: average {avg:0} ({low}-{high}), strikes {100f * strikes / Mathf.Max(1, firstBalls):0}%, spares {100f * spares / Mathf.Max(1, chances):0}%");
                    }
                }
                finally { EditorSceneManager.ClosePreviewScene(scene); }
                }
                File.WriteAllText(Path.Combine(dir, "games.md"), md.ToString());
                Debug.Log("[BowlingGames]\n" + md);
            }
            catch (Exception e) { Debug.LogException(e); code = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(code);
        }
    }
}
#endif
