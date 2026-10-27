using System.Collections.Generic;
using System.Text;

namespace GolfArcade.Bowling
{
    /// Pins left standing, as a bit mask (bit 0 = pin 1 ... bit 9 = pin 10), and what bowlers
    /// call them. USBC split: the head pin is down, and at least one pin is down between two
    /// standing pins (7-9, 3-10) or immediately ahead of and between them (5-6).
    public static class BowlingLeave
    {
        public const int All = (1 << 10) - 1;

        // Pin positions on a half-spacing grid: x in half spacings, row 0 = head pin.
        static readonly int[] Col = { 0, -1, 1, -2, 0, 2, -3, -1, 1, 3 };
        static readonly int[] Row = { 0, 1, 1, 2, 2, 2, 3, 3, 3, 3 };

        public static bool Standing(int mask, int pin) => (mask & (1 << (pin - 1))) != 0;
        public static int Count(int mask) { int n = 0; for (int m = mask & All; m != 0; m &= m - 1) n++; return n; }
        public static int Mask(params int[] pins) { int m = 0; foreach (int p in pins) m |= 1 << (p - 1); return m; }

        static int PinAt(int col, int row)
        {
            for (int i = 0; i < 10; i++) if (Col[i] == col && Row[i] == row) return i + 1;
            return 0;
        }

        static bool Touching(int a, int b)
        {
            int dc = System.Math.Abs(Col[a - 1] - Col[b - 1]), dr = System.Math.Abs(Row[a - 1] - Row[b - 1]);
            return (dr == 0 && dc == 2) || (dr == 1 && dc == 1) || (dr == 2 && dc == 0); // neighbours, or a sleeper straight behind
        }

        public static bool IsSplit(int mask)
        {
            mask &= All;
            if (Standing(mask, 1) || Count(mask) < 2) return false;
            var pins = new List<int>();
            for (int p = 1; p <= 10; p++) if (Standing(mask, p)) pins.Add(p);

            // A pin down immediately ahead of and between two standing neighbours (4-5, 5-6, 8-9).
            foreach (int a in pins) foreach (int b in pins)
            {
                if (a >= b || Row[a - 1] != Row[b - 1] || System.Math.Abs(Col[a - 1] - Col[b - 1]) != 2) continue;
                int ahead = PinAt((Col[a - 1] + Col[b - 1]) / 2, Row[a - 1] - 1);
                if (ahead != 0 && !Standing(mask, ahead)) return true;
            }

            // Otherwise a split is a leave that falls into separate groups with fallen pins between.
            var seen = new HashSet<int> { pins[0] };
            var queue = new Queue<int>(); queue.Enqueue(pins[0]);
            while (queue.Count > 0)
            {
                int a = queue.Dequeue();
                foreach (int b in pins) if (!seen.Contains(b) && Touching(a, b)) { seen.Add(b); queue.Enqueue(b); }
            }
            return seen.Count < pins.Count;
        }

        public static string Numbers(int mask)
        {
            var sb = new StringBuilder();
            for (int p = 1; p <= 10; p++) if (Standing(mask, p)) { if (sb.Length > 0) sb.Append('-'); sb.Append(p); }
            return sb.ToString();
        }

        /// A bowler's name for the leave after the first ball, or null if it has none.
        public static string Name(int mask)
        {
            mask &= All;
            switch (Numbers(mask))
            {
                case "7-10": return "Bedposts";
                case "4-6-7-10": return "Big Four";
                case "4-6-7-9-10": case "4-6-7-8-10": return "Greek Church";
                case "2-4-5-8": case "3-5-6-9": return "Bucket";
                case "1-2-10": case "1-2-4-10": case "1-3-7": case "1-3-6-7": return "Washout";
                case "2-7": case "3-10": return "Baby Split";
                case "5-7": case "5-10": return "Dime Store";
                case "7": case "10": return Numbers(mask) + " Pin";
            }
            return IsSplit(mask) ? "Split" : null;
        }

        /// Strike-streak names for the announcer.
        public static string Streak(int strikes)
        {
            switch (strikes)
            {
                case 2: return "Double";
                case 3: return "Turkey";
                case 4: return "Hambone";
                case 6: return "Six-Pack";
                case 9: return "Golden Turkey";
                case 12: return "Perfect Game";
            }
            return strikes >= 5 ? strikes + "-Bagger" : null;
        }
    }
}
