using UnityEngine;

namespace GolfArcade.Bowling
{
    /// Reads the bowling swing from the phone's motion samples (PLAN_Bowling.md §4.3–4.5).
    ///
    /// The phone is held like the ball, in the bowling hand. Everything is measured in the
    /// world frame (CoreMotion's z-up reference), so it does not matter exactly how the phone
    /// sits in the hand:
    ///   * the arm swing is a pendulum about a horizontal axis: the horizontal part of the
    ///     angular velocity. Its direction during the backswing fixes that axis; the swing
    ///     angle is integrated about it (backswing height = potential power, forward-swing
    ///     speed = delivered power);
    ///   * at the bottom of the swing the forearm hangs vertical, so a wrist turn ("handshake")
    ///     is rotation about world up. Its angle over the last ~180 ms before the thumb lifts
    ///     sets the axis rotation (hook) and its speed the revs;
    ///   * if the swing plane turns between backswing and forward swing, that is drift.
    /// Pure maths (no Unity types beyond Mathf/Vector3), so it is testable offline.
    public sealed class BowlingSwingDetector
    {
        public const float ArmLength = .65f;          // shoulder to the ball, metres
        public const float FullBackswingDeg = 150;    // stance (ball at the chest) to the top of a full backswing
        public const float FlickWindow = .18f;

        // Ring of recent world-frame vertical spin (wrist turn), for the flick window.
        const int Ring = 64;
        readonly double[] ringTime = new double[Ring];
        readonly float[] ringYaw = new float[Ring];
        int ringHead, ringCount;

        bool active;
        double lastTime, topTime = -1, bottomTime = -1;
        float lastRate;
        Vector3 axisSum;               // accumulated swing axis (horizontal, world)
        Vector3 backAxis, forwardAxis;
        float angle, minAngle, peakForward, backPeak, backPeakAngle; double peakTime;
        bool forwardPhase;

        public bool Active => active;
        /// Swing angle in degrees since Ready: 0 = stance, negative = back, positive = forward.
        public float AngleDeg => angle;
        /// How far back the swing went, 0..1 of a full backswing.
        public float Load => Mathf.Clamp01(-minAngle / FullBackswingDeg);
        public float PeakForwardRate => peakForward;
        /// The backswing has started (the arm went back past ~15° from the stance).
        public bool InBackswing => angle < -15 || forwardPhase;
        /// The arm turned forward from the top of the backswing.
        public bool ForwardSwing => forwardPhase;
        /// Self-timed release (PLAN_PhonePlay §5): the arm is a pendulum, fastest where it hangs straight down (the bottom). The
        /// backswing passes the bottom too, at its fastest backward rate, so that angle is this swing's own bottom (whatever the
        /// stance and grip). On the forward swing the arm is past the bottom once it is beyond that angle, or once the rate has
        /// fallen back from its peak.
        public bool PastBottom => bottomTime >= 0 || (forwardPhase && angle >= BottomAngle);
        public double BottomTime => bottomTime;
        public double TopTime => topTime;
        /// The swing angle where the arm hangs straight down: measured on the backswing; without a real backswing, ~47 % of the way
        /// back (the stance holds the ball ~70° forward of hanging, a full backswing is 150° behind the stance).
        public float BottomAngle => backPeak > 2f ? backPeakAngle : minAngle * .47f;
        /// Forward-swing progress from the top of the backswing (0) to the bottom (1).
        public float ForwardProgress => !forwardPhase ? 0 : PastBottom ? 1 : Mathf.Clamp01((angle - minAngle) / Mathf.Max(1, BottomAngle - minAngle));
        /// Seconds since the arm passed the bottom at `now` (negative: still to go). Only meaningful on the forward swing.
        public float SinceBottom(double now)
        {
            if (!forwardPhase) return -1;
            float extra = (float)(now - lastTime);
            if (bottomTime >= 0) return (float)(now - bottomTime);
            return (angle - BottomAngle) * Mathf.Deg2Rad / Mathf.Max(1.5f, lastRate) + extra;
        }
        /// Seconds until the arm reaches the bottom (0 once past; -1 before the forward swing).
        public float BottomIn => !forwardPhase ? -1 : Mathf.Max(0, -SinceBottom(lastTime));

        public void Begin(double time)
        {
            active = true; lastTime = time;
            axisSum = Vector3.zero; backAxis = forwardAxis = Vector3.zero;
            angle = minAngle = peakForward = backPeak = backPeakAngle = 0; forwardPhase = false; topTime = bottomTime = -1; lastRate = 0;
            ringHead = ringCount = 0;
        }

        public void Cancel() => active = false;

        /// One motion sample: CoreMotion attitude quaternion (device → reference, right-handed),
        /// rotation rate in the device frame (rad/s).
        public void Ingest(double time, float qx, float qy, float qz, float qw, float rx, float ry, float rz)
        {
            if (!active) return;
            float dt = (float)(time - lastTime);
            lastTime = time;
            if (dt <= 0 || dt > .1f) return;
            Vector3 w = Rotate(qx, qy, qz, qw, new Vector3(rx, ry, rz));   // world angular velocity, z up

            // Swing axis: horizontal angular velocity. Its sign is chosen so the backswing is negative.
            var horizontal = new Vector3(w.x, w.y, 0);
            float hMag = horizontal.magnitude;
            if (!forwardPhase)
            {
                if (hMag > 1.2f) axisSum += horizontal * dt;
            }
            Vector3 axis = axisSum.sqrMagnitude > 1e-6f ? axisSum.normalized : Vector3.zero;
            // Positive = the backswing direction while we learn it, flipped so back is negative.
            float rate = -Vector3.Dot(horizontal, axis);
            angle += rate * dt * Mathf.Rad2Deg;
            if (angle < minAngle) minAngle = angle;
            // Forward phase starts once the arm turns forward from the top of the backswing.
            if (!forwardPhase && minAngle < -30 && angle > minAngle + 10) { forwardPhase = true; backAxis = axis; topTime = time; }
            lastRate = rate;
            // the backswing's fastest moment is the arm hanging straight down: remember that angle as the bottom
            if (!forwardPhase && -rate > backPeak) { backPeak = -rate; backPeakAngle = angle; }
            if (forwardPhase)
            {
                if (rate > peakForward) { peakForward = rate; peakTime = time; }
                // past the bottom: the rate has fallen 15 % from a real swing's peak (or the arm is already well past the bottom angle)
                if (bottomTime < 0 && peakForward > 2.5f && (rate < peakForward * .85f || angle > BottomAngle + 25)) bottomTime = peakTime;
                if (hMag > 1.2f) forwardAxis += horizontal * dt;
            }

            ringTime[ringHead] = time; ringYaw[ringHead] = w.z;
            ringHead = (ringHead + 1) % Ring; ringCount = Mathf.Min(ringCount + 1, Ring);
        }

        public struct Reading
        {
            public float HandSpeed, BallSpeed, Load, TwistDeg, TwistRate, RevRpm, AxisDeg, DriftDeg;
        }

        /// The swing as measured at the thumb lift.
        public Reading Measure(double liftTime)
        {
            var r = new Reading { Load = Load };
            r.HandSpeed = Mathf.Max(0, peakForward) * ArmLength;
            r.BallSpeed = BallSpeed(r.HandSpeed, r.Load);

            // Wrist turn about world up over the flick window before the lift. Positive (counter-
            // clockwise seen from above) is a right-hander's handshake turn: the hook.
            float twist = 0, peak = 0;
            for (int i = 0; i < ringCount; i++)
            {
                int k = (ringHead - 1 - i + Ring) % Ring;
                int prev = (k - 1 + Ring) % Ring;
                if (i + 1 >= ringCount) break;
                double t = ringTime[k];
                if (t > liftTime + .02) continue;
                if (t < liftTime - FlickWindow) break;
                float step = (float)(ringTime[k] - ringTime[prev]);
                if (step <= 0 || step > .1f) continue;
                twist += ringYaw[k] * step;
                if (Mathf.Abs(ringYaw[k]) > Mathf.Abs(peak)) peak = ringYaw[k];
            }
            r.TwistDeg = twist * Mathf.Rad2Deg;
            r.TwistRate = peak;
            // A still wrist rolls the ball end over end (~120 rpm); a sharp flick adds revs.
            r.RevRpm = Mathf.Clamp(120 + Mathf.Abs(peak) * 24, 0, 450);
            r.AxisDeg = Mathf.Clamp(r.TwistDeg, -75, 75);
            if (Mathf.Abs(r.TwistDeg) < 8) { r.AxisDeg = 0; r.RevRpm = Mathf.Min(r.RevRpm, 160); } // dead zone: a straight ball

            // The forward swing turns the other way about the same axis, hence the minus.
            var fwd = forwardAxis.sqrMagnitude > 1e-6f ? -forwardAxis.normalized : backAxis;
            r.DriftDeg = backAxis.sqrMagnitude > 0 && fwd.sqrMagnitude > 0 ? Vector3.Angle(backAxis, fwd) : 0;
            active = false;
            return r;
        }

        /// Phone hand speed → ball speed (m/s): a soft curve, so a flailing phone cannot throw
        /// an absurd ball and a gentle swing still reaches the pins. Shorter backswings cap it.
        public static float BallSpeed(float handSpeed, float load)
        {
            float s = 4f + 5.5f * (1 - Mathf.Exp(-handSpeed / 3.5f));
            return Mathf.Clamp(s * Mathf.Lerp(.75f, 1f, Mathf.Clamp01(load / .8f)), BowlingRelease.MinSpeed, BowlingRelease.MaxSpeed);
        }

        /// Rotates a vector by a right-handed unit quaternion (Hamilton product q v q*).
        public static Vector3 Rotate(float x, float y, float z, float w, Vector3 v)
        {
            // t = 2 * cross(q.xyz, v); v' = v + w t + cross(q.xyz, t)
            float tx = 2 * (y * v.z - z * v.y), ty = 2 * (z * v.x - x * v.z), tz = 2 * (x * v.y - y * v.x);
            return new Vector3(v.x + w * tx + (y * tz - z * ty), v.y + w * ty + (z * tx - x * tz), v.z + w * tz + (x * ty - y * tx));
        }
    }
}
