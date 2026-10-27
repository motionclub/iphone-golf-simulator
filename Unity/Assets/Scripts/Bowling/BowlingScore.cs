using System;
using System.Collections.Generic;

namespace GolfArcade.Bowling
{
    /// One player's tenpin score sheet (USBC rules; PLAN_Bowling.md §3.1).
    ///
    /// 10 frames of up to two balls. A strike scores 10 plus the next two balls, a spare 10
    /// plus the next ball. The 10th frame gives a bonus ball after a strike or spare (three at
    /// most). A foul counts as a ball with a pinfall of 0.
    public sealed class BowlingScore
    {
        public const int Frames = 10;

        readonly List<int> rolls = new List<int>();
        readonly List<bool> fouls = new List<bool>();
        readonly List<int> frameStart = new List<int> { 0 };   // index into rolls of each frame's first ball

        public int Frame => frameStart.Count - 1;               // 0..9 (10 when complete)
        public int Ball => rolls.Count - frameStart[Frame];      // 0..2 within the current frame
        public bool Complete { get; private set; }
        public IReadOnlyList<int> Rolls => rolls;

        /// Pins standing for the coming ball: 10 on a fresh rack.
        public int PinsStanding
        {
            get
            {
                if (Complete) return 0;
                int s = frameStart[Frame], b = Ball;
                if (b == 0) return 10;
                if (Frame < Frames - 1) return 10 - rolls[s];
                // 10th frame: a fresh rack after each strike, and after a spare.
                if (b == 1) return rolls[s] == 10 ? 10 : 10 - rolls[s];
                if (rolls[s] == 10) return rolls[s + 1] == 10 ? 10 : 10 - rolls[s + 1];
                return 10; // spare in the first two balls
            }
        }

        public bool FreshRack => PinsStanding == 10;

        /// Records a ball. `pins` is the legal pinfall of this ball; a foul scores 0 whatever fell.
        public void Roll(int pins, bool foul = false)
        {
            if (Complete) throw new InvalidOperationException("The game is over.");
            int standing = PinsStanding;
            if (foul) pins = 0;
            if (pins < 0 || pins > standing) throw new ArgumentOutOfRangeException(nameof(pins), $"{pins} pins with {standing} standing");
            rolls.Add(pins); fouls.Add(foul);

            int s = frameStart[Frame], b = rolls.Count - s;
            bool frameOver;
            if (Frame < Frames - 1) frameOver = b == 2 || rolls[s] == 10;
            else frameOver = b == 3 || (b == 2 && rolls[s] + rolls[s + 1] < 10);
            if (!frameOver) return;
            if (Frame == Frames - 1) Complete = true;
            frameStart.Add(rolls.Count);
        }

        public bool IsStrike(int frame) => frame < frameStart.Count && Count(frame) > 0 && rolls[frameStart[frame]] == 10;
        public bool IsSpare(int frame) => Count(frame) >= 2 && rolls[frameStart[frame]] < 10 && rolls[frameStart[frame]] + rolls[frameStart[frame] + 1] == 10;

        int Count(int frame)
        {
            if (frame >= frameStart.Count) return 0;
            int end = frame + 1 < frameStart.Count ? frameStart[frame + 1] : rolls.Count;
            return end - frameStart[frame];
        }

        /// This frame's own points (with bonus), or null while a bonus ball is still to come.
        public int? FramePoints(int frame)
        {
            if (frame < 0 || frame >= Frames || frame >= frameStart.Count) return null;
            int s = frameStart[frame], n = Count(frame);
            if (frame == Frames - 1)
            {
                if (!Complete) return null;
                int t = 0; for (int i = 0; i < n; i++) t += rolls[s + i];
                return t;
            }
            if (n == 0) return null;
            if (rolls[s] == 10) return rolls.Count >= s + 3 ? 10 + rolls[s + 1] + rolls[s + 2] : (int?)null;
            if (n < 2) return null;
            if (rolls[s] + rolls[s + 1] == 10) return rolls.Count >= s + 3 ? 10 + rolls[s + 2] : (int?)null;
            return rolls[s] + rolls[s + 1];
        }

        /// The running total shown under a frame, or null while it is pending.
        public int? Cumulative(int frame)
        {
            int total = 0;
            for (int f = 0; f <= frame; f++) { var p = FramePoints(f); if (p == null) return null; total += p.Value; }
            return total;
        }

        /// Points scored so far, counting only frames whose bonus is known.
        public int Total
        {
            get { int t = 0; for (int f = 0; f < Frames; f++) { var p = FramePoints(f); if (p == null) break; t += p.Value; } return t; }
        }

        /// The score-sheet mark of a ball: "X", "/", "-", "F" or the count; "" if not bowled.
        public string Mark(int frame, int ball)
        {
            if (frame >= frameStart.Count) return "";
            int s = frameStart[frame];
            if (ball >= Count(frame)) return "";
            int i = s + ball, p = rolls[i];
            if (fouls[i]) return "F";
            if (frame < Frames - 1)
            {
                if (ball == 0) return p == 10 ? "X" : p == 0 ? "-" : p.ToString();
                return rolls[s] + p == 10 ? "/" : p == 0 ? "-" : p.ToString();
            }
            // 10th frame: a ball after a fresh rack is marked like a first ball.
            bool fresh = ball == 0
                || (ball == 1 && rolls[s] == 10)
                || (ball == 2 && (rolls[s] == 10 ? rolls[s + 1] == 10 : rolls[s] + rolls[s + 1] == 10));
            if (fresh) return p == 10 ? "X" : p == 0 ? "-" : p.ToString();
            return rolls[i - 1] + p == 10 ? "/" : p == 0 ? "-" : p.ToString();
        }

        /// Strikes in a row ending with the latest ball (for "Double", "Turkey"...).
        public int StrikeStreak
        {
            get
            {
                int n = 0;
                for (int i = rolls.Count - 1; i >= 0; i--)
                {
                    if (rolls[i] != 10 || !StrikeBall(i)) break;
                    n++;
                }
                return n;
            }
        }

        bool StrikeBall(int index)
        {
            for (int f = frameStart.Count - 1; f >= 0; f--)
            {
                int s = frameStart[f];
                if (index < s) continue;
                int ball = index - s;
                return Mark(f, ball) == "X";
            }
            return false;
        }
    }
}
