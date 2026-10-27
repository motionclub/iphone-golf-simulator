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
    /// Audio proof: real pin actions (the carry gate's deck) rendered to WAV through BowlingSynth, plus
    /// every other bowling sound, and the binary audio gates (PLAN_Bowling.md P4: the crash has 6+
    /// variants and scales with the pins). Batch:
    ///   -executeMethod GolfArcade.EditorTools.BowlingAudioProof.Run   BOWL_AUDIO_OUT=<dir>
    public static class BowlingAudioProof
    {
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

        public static void Run()
        {
            int code = 0;
            try { code = Prove(Path.GetFullPath(Environment.GetEnvironmentVariable("BOWL_AUDIO_OUT") ?? "../work/bowling/audio/proof")); }
            catch (Exception e) { Debug.LogException(e); code = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(code);
        }

        static int Prove(string dir)
        {
            Directory.CreateDirectory(dir);
            var csv = new StringBuilder("name,board,angle,speed,knocked,impacts,ball_pin,pin_pin,kickback,deck,pit,first_hit_s,rms_db,peak\n");
            // pocket strikes, light/high hits, a brooklyn, a thin 10-pin hit, a straight nose hit
            var shots = new (string name, float board, float angle, float speed)[]
            {
                ("pocket_a", 17.5f, 5.5f, 7.6f), ("pocket_b", 17.0f, 6f, 8.2f), ("light", 15.5f, 4f, 7.2f), ("high", 19.5f, 4f, 7.6f),
                ("nose", 20f, 0f, 8f), ("brooklyn", 22.5f, 3f, 7.6f), ("thin_ten", 9f, 2f, 7f), ("seven_side", 31f, 0f, 7f),
                ("ten_pin", 2.6f, 0f, 6.5f), ("seven_pin", 37.4f, 0f, 6.5f),
            };
            var rms = new float[shots.Length]; var knockedAll = new int[shots.Length]; var sigs = new float[shots.Length][];
            var kit = BowlingAudio.LoadKit(out _, out _, out _);
            Debug.Log($"[BowlingAudioProof] kit: {kit.PinHits.Length} pin hits, {kit.Crashes.Length} crashes, {kit.BallHits.Length} ball hits");
            var scene = EditorSceneManager.NewPreviewScene();
            try
            {
                using (var deck = new BowlingPinDeck(scene))
                    for (int k = 0; k < shots.Length; k++)
                    {
                        var (name, board, angle, speed) = shots[k];
                        var act = deck.Simulate(BowlingPinDeck.Arrival(board, angle, speed), BowlingLeave.All);
                        bool strike = act.StandingAfter == 0;
                        int hitStanding = 0;
                        for (int p = 1; p <= 10; p++) if (BowlingLeave.Standing(act.StandingAfter, p)) foreach (var i in act.Impacts) if (i.Pin == p && i.Kind != ImpactKind.PinPit) { hitStanding++; break; }
                        float len = Mathf.Max(1.5f, act.Frames.Count / 60f);
                        // the game's mix: real recorded grains on the physics' impacts (the synthesised crash only without the kit)
                        var buf = kit.Ready ? BowlingSynth.Mix(act.Impacts, len, act.Knocked, strike, hitStanding, BowlingSynth.Room.Club, kit, k) : BowlingSynth.Crash(act.Impacts, len, strike, BowlingSynth.Room.Club, k);
                        var ic = new StringBuilder($"{name},{act.Knocked},{hitStanding},{F(len)}\n");
                        foreach (var i in act.Impacts) ic.Append($"{F(i.Time)},{(int)i.Kind},{F(i.Strength)},{F(i.X)},{i.Pin}\n");
                        File.WriteAllText(Path.Combine(dir, $"impacts_{k}_{name}.csv"), ic.ToString());
                        File.WriteAllBytes(Path.Combine(dir, $"crash_{k}_{name}_{act.Knocked}pins.wav"), BowlingSynth.Wav(buf));
                        int[] kinds = new int[6]; float first = -1;
                        foreach (var i in act.Impacts) { kinds[(int)i.Kind]++; if (first < 0) first = i.Time; }
                        double sum = 0; float peak = 0; foreach (var v in buf) { sum += v * v; peak = Mathf.Max(peak, Mathf.Abs(v)); }
                        rms[k] = (float)(10 * Math.Log10(sum / buf.Length + 1e-12)); knockedAll[k] = act.Knocked;
                        sigs[k] = Envelope(buf);
                        csv.Append(string.Join(",", name, F(board), F(angle), F(speed), act.Knocked, act.Impacts.Count, kinds[0], kinds[1], kinds[2], kinds[3], kinds[4] + kinds[5], F(first), F(rms[k]), F(peak))).Append('\n');
                        Debug.Log($"[BowlingAudioProof] {name}: {act.Knocked} pins, {act.Impacts.Count} impacts, rms {rms[k]:0.0} dB");
                    }
            }
            finally { EditorSceneManager.ClosePreviewScene(scene); }
            File.WriteAllText(Path.Combine(dir, "crashes.csv"), csv.ToString());

            void Save(string n, float[] b) => File.WriteAllBytes(Path.Combine(dir, n + ".wav"), BowlingSynth.Wav(b));
            Save("foul_buzzer", BowlingSynth.Buzzer()); Save("whoosh", BowlingSynth.Whoosh(.8f));

            // A1: the crash scales with the pins (the more pins down, the louder: rank correlation ≥ 0.6)
            float rho = Spearman(knockedAll, rms);
            // A2: 6+ distinct crashes: the cascade's rhythm (5 ms loudness envelope over the first 0.8 s) correlates
            // below 0.9 with every other crash (whole-length envelopes all look alike: the room tail dominates them)
            int distinct = 0; for (int a = 0; a < sigs.Length; a++) { bool unique = true; for (int b = 0; b < a; b++) if (Corr(sigs[a], sigs[b]) > .9f) unique = false; if (unique) distinct++; }
            // A3: every crash with pins down has impacts and is audible (rms > -40 dB)
            bool audible = true; for (int k = 0; k < shots.Length; k++) if (knockedAll[k] > 0 && rms[k] < -40) audible = false;
            var res = new StringBuilder("# Bowling audio gates\n\n");
            res.Append($"GATE: A1 crash scales with pins (Spearman knocked vs rms = {rho:0.00} ≥ 0.6) {(rho >= .6f ? "PASS" : "FAIL")}\n");
            res.Append($"GATE: A2 ≥ 6 distinct crashes ({distinct} of {shots.Length}) {(distinct >= 6 ? "PASS" : "FAIL")}\n");
            res.Append($"GATE: A3 every pinfall is audible {(audible ? "PASS" : "FAIL")}\n");
            File.WriteAllText(Path.Combine(dir, "GATE_RESULTS.md"), res.ToString());
            Debug.Log("[BowlingAudioProof]\n" + res);
            return 0;
        }

        static float[] Envelope(float[] stereo)
        {
            int win = BowlingSynth.Rate / 200, n = Math.Min(stereo.Length / 2 / win, 160); var e = new float[n];   // 5 ms bins, first 0.8 s
            for (int i = 0; i < n; i++) { double s = 0; for (int j = 0; j < win; j++) { float v = stereo[2 * (i * win + j)]; s += v * v; } e[i] = (float)Math.Sqrt(s / win); }
            return e;
        }

        static float Corr(float[] a, float[] b)
        {
            int n = Math.Min(a.Length, b.Length); double ma = 0, mb = 0; for (int i = 0; i < n; i++) { ma += a[i]; mb += b[i]; } ma /= n; mb /= n;
            double sab = 0, saa = 0, sbb = 0; for (int i = 0; i < n; i++) { sab += (a[i] - ma) * (b[i] - mb); saa += (a[i] - ma) * (a[i] - ma); sbb += (b[i] - mb) * (b[i] - mb); }
            return (float)(sab / Math.Sqrt(saa * sbb + 1e-12));
        }

        static float Spearman(int[] x, float[] y)
        {
            float[] Rank(float[] v) { var idx = new int[v.Length]; for (int i = 0; i < v.Length; i++) idx[i] = i; Array.Sort(idx, (p, q) => v[p].CompareTo(v[q])); var r = new float[v.Length]; for (int i = 0; i < idx.Length;) { int j = i; while (j + 1 < idx.Length && v[idx[j + 1]] == v[idx[i]]) j++; for (int k = i; k <= j; k++) r[idx[k]] = (i + j) / 2f; i = j + 1; } return r; }
            var xf = new float[x.Length]; for (int i = 0; i < x.Length; i++) xf[i] = x[i];
            return Corr(Rank(xf), Rank(y));
        }

        static string F(float f) => f.ToString("0.00", Inv);
    }
}
#endif
