using System.Globalization;
using UnityEngine;

namespace GolfArcade.Bowling
{
    /// What the ball did, told back to the bowler after it reaches the pins (11-21 skill pass): release speed, revs, the entry
    /// angle and where it met the head pin (light / pocket / high / Brooklyn), plus one short "next ball" hint. Without it a player
    /// cannot tell which part of the swing made the result, so speed and spin could not be learned even where they mattered.
    public struct BowlingShotRead
    {
        public bool Valid;
        public float Mph, Rpm;
        public float HeadBoard;   // board under the ball's centre where it crosses the head pin's line (1 = right edge)
        public float EntryDeg;    // + = moving toward the bowler's pocket side (left for a right-hander's hook)
        public Hit Where;

        public enum Hit { Pocket, Light, High, Brooklyn, WideRight, WideLeft }

        /// The 1-3 pocket is board 17.5 at the head pin (BowlingCpu.TargetX); boards either side of it, per hit.
        public const float PocketBoard = 17.5f, PocketHalf = 1.2f, HighTo = 3.5f, Wide = 6f;

        /// Reads a ball from its release and the lane integrator's state where it reached the pin deck (any other phase: no read).
        /// A back-up ball (axis turned the other way) is read against the 1-2 pocket, mirrored.
        public static BowlingShotRead From(in BowlingThrow th, in BallState end)
        {
            var r = new BowlingShotRead { Mph = th.Speed * 2.237f, Rpm = th.RevRpm };
            if (end.Phase != BallPhase.Deck || end.Velocity.z < .1f) return r;
            float x = end.Position.x + end.Velocity.x / end.Velocity.z * (BowlingLane.FoulToHeadPin - end.Position.z);
            bool backUp = th.AxisDeg < -5;
            r.HeadBoard = BowlingLane.XBoard(x);
            r.EntryDeg = Mathf.Atan2(backUp ? end.Velocity.x : -end.Velocity.x, end.Velocity.z) * Mathf.Rad2Deg;
            float d = (backUp ? BowlingLane.Boards + 1 - r.HeadBoard : r.HeadBoard) - PocketBoard;
            r.Where = d < -Wide ? (backUp ? Hit.WideLeft : Hit.WideRight)
                : d > Wide ? (backUp ? Hit.WideRight : Hit.WideLeft)
                : d < -PocketHalf ? Hit.Light
                : d <= PocketHalf ? Hit.Pocket
                : d <= HighTo ? Hit.High : Hit.Brooklyn;
            r.Valid = true;
            return r;
        }

        public string Word => Where switch
        {
            Hit.Pocket => "POCKET", Hit.Light => "LIGHT", Hit.High => "HIGH", Hit.Brooklyn => "BROOKLYN",
            Hit.WideRight => "WIDE RIGHT", _ => "WIDE LEFT",
        };

        /// "18.4 MPH · 340 RPM · 5.2° · POCKET" (the hit word only on a full rack: on a spare the pocket means nothing).
        public string Line(bool fullRack)
        {
            var c = CultureInfo.InvariantCulture;
            string s = $"{Mph.ToString("0.0", c)} MPH · {Rpm.ToString("0", c)} RPM";
            if (!Valid) return s;
            s += $" · {Mathf.Max(0, EntryDeg).ToString("0.0", c)}°";
            return fullRack ? s + " · " + Word : s;
        }

        /// One short adjustment for a first ball that did not strike (null when there is nothing to say). Directions are the
        /// bowler's own: the ball launches along the lane, so standing left moves the whole line left. Slower = more hook (left
        /// for a right-hander), faster = less.
        public string Hint(bool backUp)
        {
            if (!Valid) return null;
            string left = backUp ? "right" : "left", right = backUp ? "left" : "right";
            return Where switch
            {
                Hit.Light => $"Light: a touch slower, or stand {left}.",
                Hit.High => $"High: a touch faster, or stand {right}.",
                Hit.Brooklyn => $"Crossed over: faster, or stand {right}.",
                // (wide hits are already in the lane's own directions)
                Hit.WideRight => "Way right: stand left.",
                Hit.WideLeft => "Way left: stand right.",
                _ => EntryDeg < 3.5f ? "Pocket, but flat: more spin carries more." : null,
            };
        }
    }
}
