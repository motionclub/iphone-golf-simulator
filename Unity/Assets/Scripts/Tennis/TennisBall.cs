using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Ball flight with spin. One integrator for the simulation AND every prediction (landing
    /// ring, auto-positioning, the opponent's read), so what the game predicts is exactly what
    /// the ball then does.
    ///
    /// Spin used to be cosmetic: topspin and slice changed the animation and nothing else.
    /// Now `spin` runs from -1 (heavy slice/backspin) to +1 (heavy topspin):
    ///   * in flight, the Magnus force pulls a topspin ball down and holds a slice up, so
    ///     topspin dips hard into the court and slice floats;
    ///   * at the bounce, topspin kicks up and forward, slice skids low and slows.
    public static class TennisBall
    {
        /// Downward acceleration per m/s of horizontal speed at full topspin. At a rally pace
        /// of 25 m/s that is about 4 m/s^2 -- roughly 0.4g, in line with measured lift
        /// coefficients for heavily spun tennis balls.
        public const float Magnus = .16f;
        public const float Step = 1f / 120;

        public static Vector3 Acceleration(Vector3 velocity, float spin)
        {
            float horizontal = Mathf.Sqrt(velocity.x * velocity.x + velocity.z * velocity.z);
            return new Vector3(-velocity.x*TennisConditions.AirDrag, -9.81f - Magnus * spin * horizontal, -velocity.z*TennisConditions.AirDrag);
        }

        public static void Integrate(ref Vector3 position, ref Vector3 velocity, float spin, float dt, float curve = 0)
        {
            Vector3 a = Acceleration(velocity, spin) + Vector3.right * curve;
            position += velocity * dt + a * (.5f * dt * dt);
            velocity += a * dt;
        }

        /// The court's flat-ball restitution under a serve. A serve also keeps its skid through the bounce (`ServeGrip`): the
        /// return window is tuned on it. Every other ball is a rally ball and bounces by `TennisFlight`.
        public const float ServeRestitution = .60f, ServeGrip = .94f;
        public static bool IsServeBounce(float restitution) => restitution <= ServeRestitution + .005f;

        /// Bounce off the court. `restitution` is the court's flat-ball value.
        public static void Bounce(ref Vector3 velocity, ref float spin, float restitution)
        {
            bool pacedServe = spin > 1;
            float s = Mathf.Clamp(spin, -1, 1);
            bool serve = IsServeBounce(restitution);
            float vertical = Mathf.Clamp(restitution*TennisConditions.BounceScale + (s > 0 ? (serve ? .10f : TennisFlight.TopspinKick) : .14f) * s, .3f, .95f);
            float along = (serve ? ServeGrip : TennisFlight.Grip) + (s > 0 ? .05f : .04f) * s;
            velocity = new Vector3(velocity.x * along, -velocity.y * vertical, velocity.z * along);
            // The arcade net-clearance force must not turn a short fast serve into a moonball.
            if (pacedServe) velocity.y = Mathf.Min(velocity.y, 6.5f);
            spin = s * .45f; // A serve-only downforce boost must not survive the first bounce.
        }

        /// Where a ball first reaches the court, and when.
        public static bool Landing(Vector3 position, Vector3 velocity, float spin, out Vector3 landing, out float time, float curve = 0)
        {
            landing = position; time = 0;
            for (int i = 0; i < 900; i++)
            {
                Vector3 p = position, v = velocity;
                Integrate(ref p, ref v, spin, Step, curve);
                if (p.y <= TennisRules.BallRadius && v.y < 0)
                {
                    float span = position.y - p.y;
                    float t = Mathf.Abs(span) < .000001f ? 0 : (position.y - TennisRules.BallRadius) / span;
                    landing = Vector3.Lerp(position, p, Mathf.Clamp01(t)); landing.y = TennisRules.BallRadius;
                    time = (i + Mathf.Clamp01(t)) * Step;
                    return true;
                }
                position = p; velocity = v;
            }
            return false;
        }

        /// Launch velocity that lands a spun ball on `target` in the time a flat ball struck
        /// at `speed` would take. Exact, not iterated: the Magnus term here acts vertically
        /// and depends only on horizontal speed, which is constant in flight, so the vertical
        /// motion is plain ballistics under a stronger (topspin) or weaker (slice) gravity.
        public static Vector3 Solve(Vector3 start, Vector3 target, float speed, float spin)
        {
            Vector3 delta = target - start;
            float horizontal = new Vector2(delta.x, delta.z).magnitude;
            float flight = Mathf.Max(.25f, horizontal / Mathf.Max(12, speed));
            float drag=TennisConditions.AirDrag;
            float integral=drag>.00001f?(1-Mathf.Exp(-drag*flight))/drag:flight;
            var velocity=new Vector3(delta.x/integral,0,delta.z/integral);
            float horizontalSpeed=new Vector2(velocity.x,velocity.z).magnitude;
            float magnusIntegral=drag>.00001f?(flight-integral)/drag:.5f*flight*flight;
            velocity.y=(delta.y+.5f*9.81f*flight*flight+Magnus*spin*horizontalSpeed*magnusIntegral)/flight;
            return velocity;
        }
    }

    /// The rally ball's tuning in one place (2026-11-11, PLAN_FinalLook_Gameplay Phase 1: "a flatter, faster ball").
    ///
    /// The 10-26 ball was slow (10-17.5 m/s) under real gravity, so the solver had to throw it 2.6-3.8 m high to cross the
    /// court, and it kept 94% of its pace and 75% of its height through the bounce (a second arc of 1.7-2.3 m). Height
    /// above the strike point is set by time in the air alone (about g*t*t/8), so a flat ball is a fast one: this ball
    /// reaches its bounce in about a second and peaks near head height. The time to read it is given back AFTER the bounce,
    /// the way a real court does it: the court takes pace off the ball (`Grip`), it sits up to hip height (`Restitution`),
    /// and a clean ball lands a little shorter so the receiver meets it two to three metres later.
    /// Measured against the plan's gates by TennisFlightTests; work/final-plan-1111/phase1/tennis_model.py is the same
    /// arithmetic outside Unity.
    public static class TennisFlight
    {
        /// Editor comparison only (TENNIS_CLASSIC=1): the 10-26 "hang time" ball, for before/after films.
        public static readonly bool Classic = System.Environment.GetEnvironmentVariable("TENNIS_CLASSIC") == "1";

        /// The 10-26 value under TENNIS_CLASSIC=1, otherwise today's. In the Editor a value can be tried without a rebuild
        /// by setting TENNIS_<KEY> (tuning sweeps and feel sessions); a phone build has no such variables set.
        static float Pick(string key, float classic, float flat)
        {
            if (Classic) return classic;
            string s = System.Environment.GetEnvironmentVariable("TENNIS_" + key);
            return !string.IsNullOrEmpty(s) && float.TryParse(s, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float v) ? v : flat;
        }

        /// The player's pace by timing: mistimed, middle, on the ball (m/s into the shot solver).
        public static readonly float SlowPace = Pick("SLOW", 10f, 14f), MiddlePace = Pick("MIDDLE", 13f, 18.5f), FastPace = Pick("FAST", 17.5f, 21.5f);
        /// How far over the tape a clean rally ball passes (metres above the net): the player's, the rival's.
        public static readonly float NetClearance = Pick("CLEAR", 1.1f, .40f), RivalNetClearance = Pick("RIVAL_CLEAR", .9f, .40f);
        /// Where a clean ball lands (metres past the net): straight, and on a side lane.
        public static readonly float DeepLanding = Pick("DEEP", 10.4f, 9.4f), SideLanding = Pick("SIDE", 8f, 7.8f);
        /// The court under a rally ball: share of height kept, share of pace kept, and topspin's extra kick.
        public static readonly float Restitution = Pick("REST", .75f, .64f), Grip = Pick("GRIP", .94f, .54f), TopspinKick = Pick("KICK", .10f, .06f);
        /// The rival's lob: its top, and how often at most it may be chosen in a rally.
        public static readonly float RivalLobApex = Pick("LOB_APEX", 4.4f, 3.5f), RivalLobCap = Pick("LOB_CAP", .18f, 1f / 12);
        /// A rival drive reaches its bounce within this long (game seconds), whatever pace its profile asked for: a slower
        /// ball to a deep target could only get there by looping.
        public static readonly float RivalDriveFlight = Pick("RIVAL_FLIGHT", 99f, 1.05f);
        /// The rival's legs in a rally (see TennisOpponent.RallyLegs): share of its profile speed, and extra reading time.
        /// The flat ball reaches it about 0.2 s sooner, so it is given its legs back; swept so a clean angle wins about as
        /// often against each rung as it did on 10-26 (TennisFunTests, work/final-plan-1111/phase1).
        public static readonly float RivalLegs = Pick("LEGS", .76f, .97f), RivalReadDelay = Pick("READ", .085f, .085f);

        /// A rival's rally pace from its profile's (already Wii-scaled) pace. The profiles span 13-22 m/s; a flat ball has
        /// room for about 17.5-21.5, so the spread is kept in order and compressed.
        public static float RivalPace(float wiiPaced) => Classic ? wiiPaced : 17.5f + (Mathf.Max(13f, wiiPaced) - 13f) * .45f;

        /// The pace a rival drive from `start` to `landing` is actually sent at.
        public static float RivalDrivePace(Vector3 start, Vector3 landing, float speed) =>
            Mathf.Max(speed, new Vector2(landing.x - start.x, landing.z - start.z).magnitude / RivalDriveFlight);
    }
}
