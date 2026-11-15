using System;
using System.Collections.Generic;

namespace GolfArcade.Tennis
{
    /// EMOTE ENDS 2026-11-13 (Adnan: "after every emote ... it went to hold a tennis racket"). Every emote in the standard set is authored
    /// from and back to the tennis READY stance: both hands together in front of the belly, as if holding a racket. In tennis that is right
    /// (the racket is in hand). Anywhere the hands are empty (plaza, menu, bowling, golf), the stance reads as an invisible racket at the start
    /// and for the last ~0.5 s of every emote. With empty hands, the emote starts once the hands are 15 cm out of READY and fades back to
    /// the hero's own idle when they come within 20 cm of it again.
    /// Measured on the exported clips (hands and forearms, hero space; work/emote-ends-1113/table.py). Source-clip seconds.
    /// EMOTE_ENDS=0 (Editor) plays the whole clips as before.
    public static class EmoteEnds
    {
        /// Fade from the emote back to the idle (seconds), started at the trimmed end while the emote is still in its own pose.
        public const float FadeOut = .35f;

        public static bool Enabled
        {
            get
            {
#if UNITY_EDITOR
                return Environment.GetEnvironmentVariable("EMOTE_ENDS") != "0";
#else
                return true;
#endif
            }
        }

        // id -> (start, end) male, (start, end) female
        static readonly Dictionary<string, (float, float, float, float)> Table = new Dictionary<string, (float, float, float, float)>
        {
            ["jumpjoy"] = (.108f, 1.569f, .112f, 1.494f),
            ["fistpump"] = (.100f, 1.008f, .101f, 1.000f),
            ["stomp"] = (.150f, 1.771f, .156f, 1.742f),
            ["slump"] = (.175f, 2.217f, .179f, 2.192f),
            ["shock"] = (.092f, 1.668f, .090f, 1.620f),
            ["victory"] = (.135f, 2.792f, .138f, 2.775f),
            ["defeat"] = (.171f, 2.638f, .179f, 2.617f),
            ["wave"] = (.102f, 1.705f, .115f, 1.692f),
            ["bringit"] = (.192f, 2.696f, .217f, 2.683f),
            ["pushups"] = (.156f, 2.685f, .156f, 2.684f),
            ["scuba"] = (.312f, 4.381f, .320f, 4.384f),
            ["thrust"] = (.174f, 3.168f, .195f, 3.156f),
            ["spike"] = (.209f, 2.946f, .217f, 2.940f),
        };

        /// "Emote_FistPump", "EmoteFistPump", "fistPump", "Intro_Wave", "IntroBringIt" -> "fistpump" / "wave" / "bringit".
        static string Key(string clip)
        {
            if (string.IsNullOrEmpty(clip)) return null;
            var k = clip.Replace("_", "").ToLowerInvariant();
            if (k.StartsWith("emote")) k = k.Substring(5);
            else if (k.StartsWith("intro")) k = k.Substring(5);
            return k;
        }

        /// The part of an emote clip to play when the hands are empty: from `start` to `end` (source-clip seconds). False for clips
        /// that are not in the set (swings, bowling clips, idles) or when switched off.
        public static bool Window(string clip, bool female, out float start, out float end)
        {
            start = 0; end = 0;
            if (!Enabled || !Table.TryGetValue(Key(clip) ?? "", out var v)) return false;
            if (female) { start = v.Item3; end = v.Item4; } else { start = v.Item1; end = v.Item2; }
            return true;
        }
    }
}
