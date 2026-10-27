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
    ///   * if the swing plane turns between backswing and forward swing, that is aim: swinging through toward the right sends
    ///     the ball right, in proportion (SwingAimDeg → AimFromSwing), measured against the player's own backswing line.
    /// Pure maths (no Unity types beyond Mathf/Vector3), so it is testable offline.
    public sealed class BowlingSwingDetector
    {
        public const float ArmLength = .65f;          // shoulder to the ball, metres
        public const float FullBackswingDeg = 150;    // stance (ball at the chest) to the top of a full backswing
        public const float FlickWindow = .18f;
        /// Slowest horizontal spin (rad/s) that teaches the swing axis. 10-27 feel pass: was 1.2, so a gentle phone swing (peaking
        /// near 1.5-2.5 rad/s) learned its axis from only a few samples, or none, and read as no swing at all.
        const float LearnRate = .7f;
        /// The arm must go this far back from the stance (degrees) before turning forward counts as the forward swing (was 30).
        const float MinBackswing = 18;

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
        float angle, minAngle, peakForward, peakSpeed, backPeak, backPeakAngle; double peakTime;
        bool forwardPhase;

        public bool Active => active;
        /// Swing angle in degrees since Ready: 0 = stance, negative = back, positive = forward.
        public float AngleDeg => angle;
        /// How far back the swing went, 0..1 of a full backswing.
        public float Load => Mathf.Clamp01(-minAngle / FullBackswingDeg);
        public float PeakForwardRate => peakForward;
        /// Where the forward swing is heading so far against the backswing's line, degrees (+ = toward the bowler's right).
        public float SwingAimDeg => forwardPhase ? Heading(backAxis, forwardAxis) : 0;
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
            angle = minAngle = peakForward = peakSpeed = backPeak = backPeakAngle = 0; forwardPhase = false; topTime = bottomTime = -1; lastRate = 0;
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
                if (hMag > LearnRate) axisSum += horizontal * dt;
            }
            Vector3 axis = axisSum.sqrMagnitude > 1e-6f ? axisSum.normalized : Vector3.zero;
            // Positive = the backswing direction while we learn it, flipped so back is negative.
            float rate = -Vector3.Dot(horizontal, axis);
            angle += rate * dt * Mathf.Rad2Deg;
            if (angle < minAngle) minAngle = angle;
            // Forward phase starts once the arm turns forward from the top of the backswing.
            if (!forwardPhase && minAngle < -MinBackswing && angle > minAngle + 10) { forwardPhase = true; backAxis = axis; topTime = time; }
            lastRate = rate;
            // the backswing's fastest moment is the arm hanging straight down: remember that angle as the bottom
            if (!forwardPhase && -rate > backPeak) { backPeak = -rate; backPeakAngle = angle; }
            if (forwardPhase)
            {
                if (rate > peakForward) { peakForward = rate; peakTime = time; }
                // A wrist turn spins about the forearm. Off the bottom the forearm leans (by the arm's angle from hanging, along the
                // swing's line), so part of that spin is horizontal and points along the line: it would read as the swing turning.
                // Its vertical part is measured (w.z), so the leaning part is w.z·tan(lean): take it back out. Only near the bottom,
                // where the wrist turns: high in the swing a turn about vertical is the whole arm changing its line (that is aim).
                float lean = (angle - BottomAngle) * Mathf.Deg2Rad, near = Mathf.InverseLerp(50, 30, Mathf.Abs(lean) * Mathf.Rad2Deg);
                var line = new Vector3(backAxis.y, -backAxis.x, 0);   // the backswing's forward direction (up x forward-swing axis)
                horizontal += line * (w.z * Mathf.Tan(lean) * near);
                hMag = horizontal.magnitude;
                // the hand's speed: the whole horizontal spin (a swing aimed off the backswing line is not slower for it)
                if (rate > 0 && hMag > peakSpeed) peakSpeed = hMag;
                // past the bottom: the rate has fallen 15 % from a real swing's peak (or the arm is already well past the bottom angle)
                if (bottomTime < 0 && peakForward > 1.8f && (rate < peakForward * .85f || angle > BottomAngle + 25)) bottomTime = peakTime;
                // the forward swing's line, weighted toward its fast part: the arm hangs near vertical there, so a wrist turn (about
                // the forearm) barely tilts it, and that is where the ball leaves the hand
                if (hMag > LearnRate && rate > 0) forwardAxis += horizontal * (hMag * dt);
            }

            ringTime[ringHead] = time; ringYaw[ringHead] = w.z;
            ringHead = (ringHead + 1) % Ring; ringCount = Mathf.Min(ringCount + 1, Ring);
        }

        public struct Reading
        {
            public float HandSpeed, BallSpeed, Load, TwistDeg, TwistRate, RevRpm, AxisDeg, DriftDeg;
            /// The forward swing's direction against the backswing's line (degrees, + = right), and the launch it aims (AimFromSwing).
            public float SwingAimDeg, AimDeg;
        }

        /// The swing as measured at the thumb lift.
        public Reading Measure(double liftTime)
        {
            var r = new Reading { Load = Load };
            r.HandSpeed = Mathf.Max(0, peakForward, peakSpeed) * ArmLength;
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

            r.SwingAimDeg = forwardPhase ? Heading(backAxis, forwardAxis) : 0;
            r.DriftDeg = Mathf.Abs(r.SwingAimDeg);
            r.AimDeg = AimFromSwing(r.SwingAimDeg);
            active = false;
            return r;
        }

        /// Phone hand speed → ball speed (m/s): a soft curve, so a flailing phone cannot throw
        /// an absurd ball and a gentle swing still reaches the pins. Shorter backswings cap it a little.
        /// 10-27 (Adnan: "make it easier to get velocity, way more sensitivity"): was 4 + 5.5 (1 - e^(-v/3.5)) x 0.75-1 by load
        /// (a full phone swing ~16 mph, an easy one ~12), then 5.2 + 4.6 (1 - e^(-v/2.2)) x 0.9-1.
        /// 10-27 feel pass (Adnan: "make sure it's easy to put a good amount of power"): the curve rises sooner and flattens below
        /// the top, so the speed is mostly made by any real swing, not by swinging harder. Peak rate at the bottom → mph:
        /// a lazy 1.5 rad/s ~16.5, a gentle 2.5 ~18.3, a normal 4 ~19.8, a brisk 6 ~20.7, a hard 9 ~21.1 (the top is 21.25);
        /// a short backswing costs at most 5 %.
        public static float BallSpeed(float handSpeed, float load)
        {
            float s = 5.25f + 4.25f * (1 - Mathf.Exp(-handSpeed / 1.4f));
            return Mathf.Clamp(s * Mathf.Lerp(.95f, 1f, Mathf.Clamp01(load / .4f)), BowlingRelease.MinSpeed, BowlingRelease.MaxSpeed);
        }

        /// Swing aim: degrees the forward swing turns off the backswing's line that change nothing (nobody swings a phone dead
        /// straight), the launch turn per degree past that, and the most it can turn the ball. 1° of launch is ~32 cm at the head
        /// pin (12 boards): a 10° swing to the right moves the ball ~8 boards right, a 20° one ~15; 2.5° (the cap) is gutter to pocket.
        public const float AimDeadZone = 3, AimPerDeg = .12f, MaxSwingAim = 2.5f;

        /// Launch angle (degrees, + = right) for a forward swing `swingDeg` off the backswing's line: proportional past a small
        /// dead zone, continuous (no jump at its edge), capped.
        public static float AimFromSwing(float swingDeg)
        {
            float past = Mathf.Max(0, Mathf.Abs(swingDeg) - AimDeadZone);
            return Mathf.Sign(swingDeg) * Mathf.Min(MaxSwingAim, past * AimPerDeg);
        }

        /// Signed turn (degrees, + = clockwise seen from above: toward the bowler's right) from the backswing's line to the forward
        /// swing's. backAxis is the backswing's spin axis (horizontal); forward is the summed forward-swing spin, which turns the
        /// other way, so the backswing's forward direction is -backAxis. z is up (CoreMotion), so counter-clockwise is +, hence the minus.
        static float Heading(Vector3 backAxis, Vector3 forward)
        {
            if (backAxis.sqrMagnitude < 1e-8f || forward.sqrMagnitude < 1e-8f) return 0;
            Vector3 a = -backAxis.normalized, b = forward.normalized;
            return -Mathf.Atan2(a.x * b.y - a.y * b.x, a.x * b.x + a.y * b.y) * Mathf.Rad2Deg;
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
