using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Bowling
{
    public enum BallPhase { Air, Skid, Roll, Gutter, Deck, Pit }

    public struct BallState
    {
        public Vector3 Position, Velocity, Spin;   // spin = angular velocity, rad/s, lane space
        public BallPhase Phase;
        public float Time;
    }

    /// The ball from the release to the pin deck: one deterministic integrator (no PhysX), so a
    /// throw is reproducible from its inputs for replays and multiplayer.
    ///
    /// There is no scripted hook curve. The ball is a rigid sphere with a radius of gyration
    /// sliding on a surface whose friction comes from the oil pattern. While the contact point
    /// slips, friction acts against the slip and also changes the spin; once the slip reaches
    /// zero the ball rolls. On oil it skids almost straight; on the dry back end the side spin
    /// turns into sideways motion (the hook); once it rolls it stops hooking. This is the
    /// standard published model of bowling-ball motion (skid, hook, roll).
    public static class BowlingBall
    {
        public const float Step = 1f / 240;
        const float Gravity = 9.81f;
        const float Bounce = .15f;          // vertical restitution of a lofted ball landing on the lane
        const float RollingDrag = .02f;      // m/s^2 once the ball rolls
        const float YawSpinDamping = 1.5f;   // the vertical spin component dies off on the lane

        static float Inertia => BowlingLane.BallMass * BowlingLane.BallGyration * BowlingLane.BallGyration;

        /// The slip velocity of the contact point (zero = rolling).
        public static Vector3 Slip(in BallState s)
        {
            float r = BowlingLane.BallRadius;
            return new Vector3(s.Velocity.x + r * s.Spin.z, 0, s.Velocity.z - r * s.Spin.x);
        }

        public static void Integrate(ref BallState s, OilPattern oil, float dt)
        {
            float r = BowlingLane.BallRadius, m = BowlingLane.BallMass;
            s.Time += dt;
            switch (s.Phase)
            {
                case BallPhase.Air:
                    s.Velocity.y -= Gravity * dt;
                    s.Position += s.Velocity * dt;
                    if (s.Position.y <= r)
                    {
                        s.Position.y = r;
                        if (s.Velocity.y < -.4f) s.Velocity.y = -s.Velocity.y * Bounce;
                        else { s.Velocity.y = 0; s.Phase = BallPhase.Skid; }
                    }
                    CheckGutter(ref s);
                    return;

                case BallPhase.Gutter:
                    // The ball runs along the channel; it is out of play (pins it reaches do not count).
                    float side = Mathf.Sign(s.Position.x);
                    float centre = side * (BowlingLane.HalfWidth + BowlingLane.GutterWidth * .5f);
                    s.Position.x = Mathf.MoveTowards(s.Position.x, centre, .6f * dt);
                    s.Position.y = Mathf.MoveTowards(s.Position.y, r - BowlingLane.GutterDepth, .5f * dt);
                    s.Velocity = new Vector3(0, 0, Mathf.Max(0, s.Velocity.z - .3f * dt));
                    s.Spin = new Vector3(s.Velocity.z / r, 0, 0);
                    s.Position += s.Velocity * dt;
                    if (s.Position.z > BowlingLane.LaneEnd) s.Phase = BallPhase.Pit;
                    return;

                case BallPhase.Skid:
                case BallPhase.Roll:
                    break;
                default:
                    return;
            }

            Vector3 slip = Slip(s);
            float slipSpeed = slip.magnitude;
            float mu = oil.Friction(s.Position.x, s.Position.z);
            // How much the slip shrinks per unit friction impulse: linear (1/m) plus rotational (r^2/I).
            float compliance = 1 / m + r * r / Inertia;
            float impulse = mu * m * Gravity * dt;
            Vector3 j;
            if (slipSpeed > 1e-4f && impulse * compliance < slipSpeed) { j = -slip / slipSpeed * impulse; s.Phase = BallPhase.Skid; }
            else
            {
                j = -slip / compliance;                   // the exact impulse that ends the slip this step
                s.Phase = BallPhase.Roll;
                float v = s.Velocity.magnitude;
                if (v > 1e-4f) j -= s.Velocity / v * Mathf.Min(v, RollingDrag * dt) * m;
            }
            s.Velocity += j / m;
            // torque arm: the contact point is straight below the centre, (0, -r, 0) x J
            s.Spin += new Vector3(-r * j.z, 0, r * j.x) / Inertia;
            s.Spin.y *= Mathf.Exp(-YawSpinDamping * dt);
            s.Velocity.y = 0;
            s.Position += s.Velocity * dt;
            s.Position.y = r;

            CheckGutter(ref s);
            if (s.Phase != BallPhase.Gutter && s.Position.z >= BowlingLane.DeckStart) s.Phase = BallPhase.Deck;
        }

        static void CheckGutter(ref BallState s)
        {
            // Once the ball's centre is past the edge of the lane it tips into the channel.
            if (Mathf.Abs(s.Position.x) > BowlingLane.HalfWidth && s.Position.z < BowlingLane.LaneEnd) s.Phase = BallPhase.Gutter;
        }

        /// Runs a released ball until it reaches the pin deck, the pit (gutter ball) or stops.
        /// Optionally records every `recordEvery`-th step (4 = 60 Hz) for playback.
        public static BallState Roll(BallState s, OilPattern oil, List<BallState> record = null, int recordEvery = 4)
        {
            int n = 0;
            record?.Add(s);
            while (s.Phase != BallPhase.Deck && s.Phase != BallPhase.Pit && s.Time < 12)
            {
                Integrate(ref s, oil, Step);
                if (s.Phase != BallPhase.Gutter && s.Phase != BallPhase.Air && s.Velocity.z < .05f) break; // stalled
                if (record != null && ++n % recordEvery == 0) record.Add(s);
            }
            record?.Add(s);
            return s;
        }
    }
}
