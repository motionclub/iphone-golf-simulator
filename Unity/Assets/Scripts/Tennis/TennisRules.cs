using UnityEngine;

namespace GolfArcade.Tennis
{
    public struct TennisHit
    {
        public bool Contact;
        public float Timing, Center, Positioning, Quality, Speed, ErrorDegrees;
        public string Label;
    }

    /// How cleanly a ball was struck, reported back to the player as a hitmarker.
    public enum Timing { Missed, Ok, Good, Great, Excellent, Perfect }

    /// Deterministic, independently testable gameplay tuning. Distances are metres.
    public static class TennisRules
    {
        /// Consecutive well-struck balls needed to supercharge the next one.
        public const int SuperchargeStreak = 3;
        /// A hit must grade at least this well to extend the streak.
        public const Timing StreakFloor = Timing.Great;
        /// A streak rewards pace without making the next rally ball unreturnable.
        public const float SuperchargeSpeed = 1.15f, MaxRallySpeed = 34f;

        /// Grade contact quality (0 = frame, 1 = sweet spot). Serve timing uses the same scale.
        public static Timing Grade(float timing)
        {
            if (timing <= 0) return Timing.Missed;
            if (timing >= .96f) return Timing.Perfect;
            if (timing >= .88f) return Timing.Excellent;
            if (timing >= .75f) return Timing.Great;
            if (timing >= .55f) return Timing.Good;
            return Timing.Ok;
        }

        /// Timing score (1 = dead on .. 0 = missed) for a swing that met the ball `late`
        /// real seconds after the ideal moment (negative: early). Set in milliseconds a person
        /// can actually hit with a phone and a TV picture: PERFECT within 35ms, EXCELLENT 60,
        /// GREAT 95, GOOD 140, and a scrappy playable ball out to 340 ms.
        public static float TimingScore(float late)
        {
            float t = Mathf.Abs(late);
            if (t <= .035f) return Mathf.Lerp(1f, .96f, t / .035f);
            if (t <= .06f) return Mathf.Lerp(.96f, .88f, (t - .035f) / .025f);
            if (t <= .095f) return Mathf.Lerp(.88f, .75f, (t - .06f) / .035f);
            if (t <= .14f) return Mathf.Lerp(.75f, .55f, (t - .095f) / .045f);
            return Mathf.Clamp01(Mathf.Lerp(.55f, 0f, (t - .14f) / (ContactTimingWindow - .14f)));
        }

        /// "EARLY" / "LATE" for a swing off by more than a perfect one, else "".
        public static string TimingWord(float late) => late > .035f ? "LATE" : late < -.035f ? "EARLY" : "";

        /// The grade a label stands for (the host sends the label, `GradeLabel`, with every online hit).
        public static Timing GradeFromLabel(string label) => label switch
        {
            "PERFECT!" => Timing.Perfect,
            "EXCELLENT" => Timing.Excellent,
            "GREAT" => Timing.Great,
            "GOOD" => Timing.Good,
            "OK" => Timing.Ok,
            _ => Timing.Good,
        };

        /// How hard the phone clicks for a hit of this grade, 0..1 (a cleaner hit is a crisper click).
        public static float GradeFeel(Timing grade) => grade switch
        {
            Timing.Perfect => .95f, Timing.Excellent => .85f, Timing.Great => .75f, Timing.Good => .55f, _ => .35f,
        };

        public static string GradeLabel(Timing grade) => grade switch
        {
            Timing.Perfect => "PERFECT!",
            Timing.Excellent => "EXCELLENT",
            Timing.Great => "GREAT",
            Timing.Good => "GOOD",
            Timing.Ok => "OK",
            _ => "MISS",
        };

        /// Contact is drawn once by TennisGame; rewards never add timed simulation holds.
        public static float HitStopFor(Timing grade, bool supercharged) => 0f;
        public const float HeavyHitStop = 0f;

        /// Three redundant visual tiers: muted blue, cream and gold; grading is unchanged.
        public static Color ContactColor(Timing grade) => grade >= Timing.Perfect
            ? new Color(1f, .82f, .32f) : grade >= Timing.Great
            ? new Color(1f, .97f, .86f) : new Color(.64f, .76f, .86f);

        /// Does this grade keep a streak alive?
        public static bool Extends(Timing grade) => grade >= StreakFloor;

        /// Turn a hit into its supercharged version: markedly faster and dead accurate, as
        /// the reward for three clean contacts in a row.
        public static TennisHit Supercharge(TennisHit hit)
        {
            hit.Speed = Mathf.Min(MaxRallySpeed, hit.Speed * SuperchargeSpeed);
            hit.ErrorDegrees *= .25f;
            hit.Label = "SUPERCHARGED";
            return hit;
        }

        /// Where the ball met the string bed, in string-bed coordinates (metres, x across and
        /// y up the face). Used for the impact map, so it must be a real measurement rather
        /// than an assumed centre hit: an assisted return still struck the racket somewhere.
        public static Vector2 FaceOffset(Vector3 ball, Vector3 sweetSpot, Vector3 right, Vector3 up)
        {
            Vector3 delta = ball - sweetSpot;
            return new Vector2(Vector3.Dot(delta, right), Vector3.Dot(delta, up));
        }

        /// How far off-centre a contact was, as a fraction of the string bed (0 = middle,
        /// 1 = the edge). Drives the impact map's colouring and the coaching hint.
        public static float FaceError(Vector2 offset) =>
            new Vector2(offset.x / StringHalfWidth, offset.y / StringHalfHeight).magnitude;
        public const float CourtHalfWidth = 4.115f, CourtHalfLength = 11.885f;
        /// Service line sits 6.40m from the net, and the centre line splits each side into
        /// two boxes 4.115m wide — full-size singles dimensions.
        public const float ServiceLine = 6.40f, NetHeight = .97f;
        // Reference animation time; actors stretch this timeline by strength.
        public const float StrokeDuration = .46f, SweetTime = .18f, TimingWindow = .19f;
        public const float ContactTimingWindow = .34f, ContactStart = .02f, ContactReach = 1.8f;
        /// Human movement, not a sprinter on rails: the old 28 m/s² and 9 m/s sprint got the
        /// character to every ball, which took reaching the ball out of the game. A tour player
        /// peaks around 6 m/s and takes most of a second to get there.
        ///
        /// Tuned for a phone player who cannot see where the ball is going from the phone and sees
        /// the TV a beat late: the human gets a quicker burst (16 m/s², 0.15 s reading time) and a
        /// higher top speed than the CPU, whose own pace keeps `CourtMovementScale`. A 0.9 s ball
        /// is then 3.1 m of running plus the reach, where it used to be 2.0 m.
        public const float CourtMovementScale = .88f;
        public const float PlayerMovementScale = .96f;
        public const float RunSpeed = 5.6f * PlayerMovementScale, SprintSpeed = 6.6f * PlayerMovementScale, Acceleration = 16f;
        /// Braking the auto-positioning uses to arrive at the ball instead of stopping dead.
        public const float Deceleration = 18f;

        /// Reading the ball. The character commits `ReactionTime` after the opponent strikes;
        /// a player who leans or steps toward the ball in that window gets a "good jump": an
        /// almost immediate first step and a sprint. Players on auto-pilot (phone motion, where
        /// nothing steers) earn the same jump from `EarnsAutoJump`.
        public const float ReactionTime = .15f, JumpReaction = .05f, JumpLean = .45f;

        /// A ball that cannot be reached at a plain run, after the usual reading time, earns the
        /// good jump automatically. Players who steer (touch, lean) still earn it themselves; this
        /// is for the phone-motion player, whose steering input is always zero, so the sprint and
        /// instant first step were never reachable. Easy balls are unaffected: it is a rescue for
        /// the balls that would otherwise be pure winners.
        public static bool EarnsAutoJump(InterceptPlan plan) => plan.Found && !plan.Reachable;

        /// Tired legs are slower, but only a little: long rallies are the fun part, so stamina
        /// trims 15% of top speed at the floor (it was 28%).
        public static float StaminaSpeedFactor(float stamina) => Mathf.Lerp(.85f, 1f, Mathf.Clamp01(stamina / .35f));
        /// Horizontal reach from where the player stands to the ball, and with a dive.
        public const float StrokeReach = 1.35f, DiveReach = 2.55f;
        /// Diving costs: on the floor for a beat, and legs.
        public const float DiveRecovery = .8f, DiveStamina = .08f, DiveQualityCap = .42f;
        /// Share of running speed available while getting up from a dive (it was 8%, a crawl).
        public const float GroundRecoverySpeed = .3f;
        /// Where a player stands between points and recovers to after a shot.
        public const float BaselineZ = -11.2f, NetZ = -5.8f, NetRushLine = -7.6f;

        /// Seconds to cover `distance` from a standstill with the acceleration above.
        public static float TimeToCover(float distance, float topSpeed)
        {
            if (distance <= 0) return 0;
            float rampDistance = topSpeed * topSpeed / (2 * Acceleration);
            return distance <= rampDistance ? Mathf.Sqrt(2 * distance / Acceleration)
                : topSpeed / Acceleration + (distance - rampDistance) / topSpeed;
        }

        /// Ground a player can cover in `seconds` from a standstill.
        public static float Coverable(float seconds, float topSpeed)
        {
            if (seconds <= 0) return 0;
            float ramp = topSpeed / Acceleration;
            return seconds <= ramp ? .5f * Acceleration * seconds * seconds
                : .5f * Acceleration * ramp * ramp + (seconds - ramp) * topSpeed;
        }

        public struct InterceptPlan
        {
            public Vector3 Point;      // where the ball will be struck
            public float Time;         // seconds from now
            public float Gap;          // how far short the player will be (<= StrokeReach: fine)
            public bool Found, Reachable, Diveable;
        }

        /// Where to meet an incoming ball, if anywhere: the ball is flown forward (bounces,
        /// spin and all) and every moment it is at a playable height on the player's side is a
        /// candidate. A candidate is reachable if the player can cover the ground in the time
        /// left after reacting. Among reachable ones, a comfortable height near where the
        /// player already stands wins -- so a short ball pulls them forward, a deep one back,
        /// and a player at the net volleys it early. Out of reach, the nearest miss is
        /// returned so they can still chase it (and perhaps dive).
        public static InterceptPlan PlanIntercept(Vector3 position, Vector3 velocity, float spin, float restitution,
            Vector2 player, float reaction, float topSpeed, bool atNet, float curve = 0)
        {
            var best = new InterceptPlan(); float bestScore = float.MaxValue;
            var nearest = new InterceptPlan { Gap = float.MaxValue };
            int bounces = 0; float time = 0, bounceZ = 0;
            const float dt = TennisBall.Step * 2;
            for (int i = 0; i < 360; i++)
            {
                Vector3 next = position, v = velocity;
                TennisBall.Integrate(ref next, ref v, spin, dt, curve);
                if (next.y < BallRadius && v.y < 0)
                {
                    next.y = BallRadius; TennisBall.Bounce(ref v, ref spin, restitution);
                    if (++bounces >= 2) break;          // a second bounce ends the point
                    bounceZ = next.z;
                }
                position = next; velocity = v; time += dt;
                if (position.z > -.6f || velocity.z > 0) continue;           // not on our side yet
                if (position.z < -15.5f) break;                            // gone past any stand
                float h = position.y;
                bool volley = bounces == 0;
                // Volleys only near the net (or a high ball anywhere); otherwise after the bounce.
                if (volley && !(atNet && position.z > -8f && h > .45f) && h < 1.9f) continue;
                if (h < .3f || h > 2.3f) continue;
                Vector2 at = new Vector2(position.x, position.z - .65f);
                float travel = Vector2.Distance(at, player);
                float cover = Coverable(time - reaction, topSpeed);
                float gap = travel - cover;
                if (gap < nearest.Gap) nearest = new InterceptPlan { Point = position, Time = time, Gap = gap, Found = true };
                if (gap > StrokeReach) continue;
                // Take a bounced ball near the top of its bounce, about 2.8 m after it lands, but
                // never from behind the baseline: a short ball draws the player in, a deep one
                // keeps them back. Volleys are met where the player already stands.
                float preferredZ = volley ? player.y : Mathf.Clamp(bounceZ - 2.8f - .65f, -12.6f, -3f);
                float comfort = Mathf.Abs(h - 1.0f) * 1.2f + Mathf.Abs(at.y - preferredZ) * .18f + travel * .06f + (volley ? 0 : .25f * (atNet ? 1 : 0));
                if (comfort < bestScore) { bestScore = comfort; best = new InterceptPlan { Point = position, Time = time, Gap = gap, Found = true, Reachable = true, Diveable = true }; }
            }
            if (best.Found) return best;
            nearest.Diveable = nearest.Found && nearest.Gap <= DiveReach;
            return nearest;
        }

        /// Shot pace comes from the quality of contact -- mostly the timing -- not how hard the phone
        /// was swung: a swing on the ball flies, a mistimed one floats. Effort only nudges it.
        public static float ShotSpeed(float quality, float power, float stamina) => TimingPace(quality, power, stamina);

        /// Where an aimed rally ball is sent. The racket face picks the side (-1...1); the
        /// contact decides how much of the court the player can use: a clean hit can go
        /// close to the lines and deep, a poor one is pulled toward the middle and lands short.
        public static Vector3 PlacementTarget(float aim, float depth) =>
            new Vector3(Mathf.Clamp(aim, -1, 1) * (CourtHalfWidth - .35f), BallRadius, Mathf.Lerp(3.2f, 10.8f, Mathf.Clamp01(depth)));

        /// Timing earns the full chosen angle and depth. A scrappy hit stays playable but
        /// drifts toward the middle with bounded scatter; a clean hit follows the aim.
        public static Vector3 TimedPlacement(Vector3 intended, float timing, float rollX, float rollZ)
        {
            float control = Mathf.SmoothStep(0, 1, Mathf.Clamp01(timing));
            float spread = Mathf.Lerp(.9f, .03f, control);
            float x = intended.x * Mathf.Lerp(.6f, 1f, control) + Mathf.Clamp(rollX, -1, 1) * spread;
            float z = Mathf.Lerp(6.5f, intended.z, Mathf.Lerp(.65f, 1f, control)) + Mathf.Clamp(rollZ, -1, 1) * spread;
            return new Vector3(Mathf.Clamp(x, -CourtHalfWidth + .12f, CourtHalfWidth - .12f), BallRadius,
                Mathf.Clamp(z, 2.8f, CourtHalfLength - .3f));
        }

        public struct ServeFlight { public Vector3 Velocity; public float Spin; }
        /// Arcade serve downforce preserves the chosen horizontal pace, net clearance and landing.
        /// All predictors use the same spin acceleration; the temporary boost ends at the bounce.
        public static ServeFlight PacedServe(Vector3 start, Vector3 landing, float speed, float baseSpin)
        {
            Vector3 delta = landing - start;
            float distance = new Vector2(delta.x, delta.z).magnitude;
            float flight = Mathf.Max(.18f, distance / Mathf.Max(12, speed));
            float horizontal = distance / flight;
            float fraction = Mathf.Abs(delta.z) > .001f ? Mathf.Clamp01(-start.z / delta.z) : .5f;
            float linearAtNet = Mathf.Lerp(start.y, landing.y, fraction);
            float denominator = flight * flight * fraction * (1 - fraction);
            float gravity = Mathf.Max(9.81f + TennisBall.Magnus * baseSpin * horizontal,
                2 * (NetHeight + NetMargin + .025f - linearAtNet) / Mathf.Max(.001f, denominator));
            return new ServeFlight {
                Velocity = delta / flight + Vector3.up * (.5f * gravity * flight),
                Spin = (gravity - 9.81f) / Mathf.Max(.001f, TennisBall.Magnus * horizontal)
            };
        }

        public static Vector3 AimedTarget(float aim, float quality, float lift)
        {
            float q = Mathf.Clamp01(quality);
            // The face picks the side and it stays picked: even a scrappy contact goes most of
            // the way to where it was aimed (it used to collapse toward the middle); a poor hit
            // pays in pace and depth instead.
            float width = Mathf.Lerp(2.6f, 3.9f, q);
            float depth = Mathf.Lerp(6.4f, 10.4f, q) + Mathf.Clamp(lift, 0, .4f) * 2f;
            return new Vector3(Mathf.Clamp(aim, -1, 1) * width, BallRadius, Mathf.Min(depth, 11.2f));
        }
        /// Opponent difficulty. It covers the court at a human pace with a limited reach and
        /// a real miss rate, so wide, deep and well-struck balls actually win points.
        public const float OpponentSpeed = 4.6f, OpponentReach = 1.75f, OpponentErrorRate = .24f;
        // Arcade racket: a genuinely bigger string bed than a real one, because the player is
        // aiming with a phone they cannot see while looking at a TV. The hit box IS the visible head:
        // the hero racket is drawn at HeroRacketScale (1.3x its 0.29 x 0.40 m sculpt), so the head is
        // 0.38 x 0.52 m and these half-extents match it (the ball's own radius is added on contact).
        public const float HeroRacketScale = 1.3f;
        public const float StringHalfWidth = .19f, StringHalfHeight = .26f, BallRadius = .10f;
        /// Movement assist. The character leans toward where the ball is actually going, but
        /// only while it is further away than `AssistDeadBand` — the last stretch is the
        /// player's own job, so positioning still matters.
        public const float AssistDeadBand = 1.0f, AssistAuthority = .55f;
        public static bool UseBackhand(float facing,bool fallbackLeft,bool leftHanded) =>
            (Mathf.Abs(facing)>.5f ? facing<0 : fallbackLeft) != leftHanded;
        public static float StrokePhase(float age)
        {
            if (age <= SweetTime) return .5f * Mathf.Pow(Mathf.Clamp01(age / SweetTime), 1.7f);
            float finish = Mathf.Clamp01((age - SweetTime) / (StrokeDuration - SweetTime));
            return .5f + .5f * (1 - (1 - finish) * (1 - finish));
        }
        /// Contact quality is the timing, trimmed a little by spacing (a crowded or stretched ball comes off
        /// the frame) and balance. Timing dominates: it is the skill the player controls.
        public static float ContactQuality(float timing, float center, float positioning) =>
            Mathf.Max(.05f, Mathf.Clamp01(timing) * Mathf.Lerp(.85f, 1f, Mathf.Clamp01(center)) * Mathf.Lerp(.95f, 1f, Mathf.Clamp01(positioning)));

        /// Timing chooses the pace (through quality); the swing's direction chooses the side, elsewhere.
        public static TennisHit AssistedHit(float late, float center, float balance, float power, float stamina)
        {
            // A return that physically connects is at least a scrappy OK hit.
            float timing = Mathf.Max(.01f, TimingScore(late));
            float quality = ContactQuality(timing, center, balance);
            return new TennisHit {
                Contact = true, Timing = timing, Center = center, Positioning = balance, Quality = quality,
                Speed = ShotSpeed(quality, power, stamina),
                ErrorDegrees = Mathf.Lerp(7, .6f, quality), Label = quality >= .96f ? "SWEET SPOT" : quality >= .63f ? "CLEAN HIT" : timing < .55f ? "MISTIMED" : "OFF CENTER"
            };
        }

        /// Outer share of the string bed that counts as the frame for a real string contact.
        public const float FrameRing = .85f;

        public static TennisHit Evaluate(float swingAge, Vector2 faceOffset, float balance, float reachQuality, float power, float stamina)
        {
            float radial = new Vector2(faceOffset.x / StringHalfWidth, faceOffset.y / StringHalfHeight).magnitude;
            float timing = TimingScore(swingAge - SweetTime);
            bool contact = new Vector2(faceOffset.x / (StringHalfWidth + BallRadius), faceOffset.y / (StringHalfHeight + BallRadius)).magnitude <= 1 && swingAge >= ContactStart && timing > 0;
            float center = Mathf.Clamp01(1 - radial);
            float positioning = Mathf.Clamp01(balance) * Mathf.Clamp01(reachQuality);
            float quality = contact ? ContactQuality(timing, center, positioning) : 0;
            // The ball visibly met the frame: a weak return whatever the timing.
            if (radial > FrameRing) quality = Mathf.Min(quality, .5f);
            return new TennisHit {
                Contact = contact, Timing = timing, Center = center, Positioning = positioning, Quality = quality,
                Speed = contact ? ShotSpeed(quality, power, stamina) : 0,
                // Contact quality (mostly timing) sets control as well as pace.
                ErrorDegrees = contact ? Mathf.Lerp(.6f, 13f, 1 - quality) + (1 - Mathf.Clamp01(stamina)) * 4 : 0,
                Label = !contact ? "MISS" : quality > .86f ? "SWEET SPOT" : quality > .63f ? "CLEAN HIT" : radial > .72f ? "OFF CENTER" : "OFF BALANCE"
            };
        }

        public static float StaminaStep(float value, float speed, float dt)
        {
            float exertion = Mathf.Pow(Mathf.Clamp01(Mathf.Abs(speed) / SprintSpeed), 2);
            return Mathf.Clamp01(value + (Mathf.Abs(speed) < .15f ? .13f : -.11f * exertion) * dt);
        }

        /// Heights a player can play the ball at without it being a miss: from a scoop off the
        /// court to a high backhand; overheads reach higher.
        public const float ReachLow = .28f, ReachHigh = 2.05f, ReachOverhead = 2.75f;

        /// Comfortable spacing, not distance to the torso: crowding and stretching both
        /// move contact toward the frame. A broad central zone keeps ordinary rallies easy.
        /// Timing is deliberately absent. Height chooses the upper/lower strings.
        public static Vector2 PositionFace(Vector3 ball, Vector3 player, bool overhead = false, float balance = 1)
        {
            Vector3 delta = ball - player;
            float side = Mathf.Abs(delta.x);
            float inside = overhead ? 0 : .4f, outside = overhead ? .75f : .9f;
            float horizontal = side < inside ? (side - inside) / inside : side > outside ? (side - outside) / .9f : 0;
            // Reaching far forward or letting the ball get behind the hip is awkward too.
            float depth = delta.z < .1f ? (.1f - delta.z) / .8f : delta.z > 1.2f ? (delta.z - 1.2f) / 1.2f : 0;
            horizontal = (horizontal < 0 ? -1 : 1) * Mathf.Sqrt(horizontal * horizontal + depth * depth);
            float low = overhead ? 2f : .7f, high = overhead ? 2.65f : 1.6f;
            float vertical = delta.y < low ? (delta.y - low) / .8f : delta.y > high ? (delta.y - high) / .8f : 0;
            var offset = new Vector2(horizontal * (delta.x < 0 ? -1 : 1), vertical);
            // Running through the shot adds a small, visible string-bed error.
            float unbalanced = (1 - Mathf.Clamp01(balance)) * .12f;
            offset.y += offset.y > 0 ? unbalanced : -unbalanced;
            offset = Vector2.ClampMagnitude(offset, .95f);
            return new Vector2(offset.x * StringHalfWidth, offset.y * StringHalfHeight);
        }

        public static bool AssistedContact(Vector3 oldBall, Vector3 ball, Vector3 player, float age, bool overhead, out float quality, float power=0.5f, bool dive=false)
        {
            quality=0;
            // A dive throws the racket much further sideways than a normal stroke can reach.
            // Plan 2 party windows: a little more reach and time than before (never less) — skill is
            // when you swing and where you aim, not sniper precision.
            float forgiveness=ContactReach*(dive?1.8f:1f);
            if(age < ContactStart || Mathf.Abs(age-SweetTime) >= ContactTimingWindow) return false;
            // Closest approach measured on the ground plane, then judged against a height BAND
            // rather than a point: the old fixed 1.1m centre turned low and high balls the
            // player had timed perfectly into misses.
            Vector3 centre=player+new Vector3(0,0,.65f);
            Vector3 segment=ball-oldBall; Vector2 flat=new Vector2(segment.x,segment.z);
            Vector2 toCentre=new Vector2(centre.x-oldBall.x,centre.z-oldBall.z);
            float t=flat.sqrMagnitude>.000001f ? Mathf.Clamp01(Vector2.Dot(toCentre,flat)/flat.sqrMagnitude) : 0;
            Vector3 at=Vector3.Lerp(oldBall,ball,t);
            float height=at.y-player.y;
            float bandTop=overhead ? ReachOverhead : ReachHigh;
            float outside=height<ReachLow ? ReachLow-height : height>bandTop ? height-bandTop : 0;
            float distance=new Vector3((at.x-centre.x)/forgiveness,outside/.45f,(at.z-centre.z)/forgiveness).magnitude;
            if(distance>1 || ball.z<player.z-.5f) return false;
            quality = 1 - FaceError(PositionFace(at, player, overhead));
            return true;
        }

        /// Where an incoming ball will reach the player's baseline plane, by plain ballistics
        /// with bounces. Pure and deterministic so the movement assist can be tested without
        /// a scene.
        public static bool PredictInterceptX(Vector3 position, Vector3 velocity, float planeZ, float restitution, out float x, float spin = 0)
        {
            x = position.x;
            if (velocity.z >= 0 == position.z >= planeZ) return false;
            const float dt = TennisBall.Step;
            for (int i = 0; i < 480; i++)
            {
                Vector3 next = position, v = velocity;
                TennisBall.Integrate(ref next, ref v, spin, dt);
                // The same bounce the simulation applies, spin and all. The old prediction
                // skipped the bounce's loss of pace, so the auto-positioning aimed short.
                if (next.y < BallRadius && v.y < 0) { next.y = BallRadius; TennisBall.Bounce(ref v, ref spin, restitution); }
                if ((position.z - planeZ) * (next.z - planeZ) <= 0)
                {
                    float span = next.z - position.z;
                    float t = Mathf.Abs(span) < .000001f ? 0 : (planeZ - position.z) / span;
                    x = Mathf.Lerp(position.x, next.x, Mathf.Clamp01(t));
                    return true;
                }
                position = next; velocity = v;
            }
            return false;
        }

        /// How far to shift the player toward the predicted intercept, in court metres.
        /// Zero once the player is inside the dead band, so the final approach is always
        /// theirs: the assist closes the long gaps, never the last metre.
        public static float MovementAssist(float playerX, float interceptX)
        {
            float gap = interceptX - playerX;
            float beyond = Mathf.Abs(gap) - AssistDeadBand;
            if (beyond <= 0) return 0;
            return beyond * Mathf.Sign(gap) * AssistAuthority;
        }

        /// Serve timing. The ball is tossed, rises, and must be struck near the apex with a
        /// downward swing. Miss the window and it goes into the net — one fault is allowed.
        /// The pre-serve routine (two bounces and the wind-up, see TennisServeRoutine) fills
        /// the time before the toss.
        public const float ServeTossDelay = 2.2f, ServeApex = .62f, ServeIdealContact = .62f;
        /// Generous by design: almost any committed swing during the toss should go in. Only
        /// a wildly early or late one nets. The old +/-0.20s window was unplayable once swing
        /// detection latency was accounted for.
        public const float ServeCatch = 1.3f, ServePerfectWindow = ServePerfectRealSeconds * ServePace, ServeLegalWindow = ServePowerWindow * (1 - ServeFaultPower);

        /// Serve on a slow TV. The player swings at the top of the toss they see, which reaches the game a TV delay late:
        /// past ~0.3 s of delay the ball had already fallen through the strike point when that swing arrived, and past ~0.7 s
        /// it was caught first. So on a slow TV the toss falls more slowly after its top: the rise, the top, the power bar and
        /// the grading are untouched, and the fall from the top to the strike point lasts at least the delay, the swing's
        /// report (`ServeSwingReport`, real seconds) and `ServeLateReach` (game seconds of lateness the strike still reaches).
        /// Delays up to ~0.25 s keep full gravity.
        public const float ServeLateReach = .15f, ServeSwingReport = ServeOnsetLatency + .03f;
        /// Gravity (m/s²) for the fall after the top of a toss whose top is `drop` metres above the strike point, at a TV delay
        /// of `lag` real seconds and `pace` game seconds per real second. Full gravity unless the delay needs a slower fall.
        public static float ServeFallGravity(float lag, float drop, float pace)
        {
            const float g = 9.81f;
            if (drop <= 0) return g;
            float fall = (Mathf.Clamp(lag, 0, TennisLagLearner.Max) + ServeSwingReport) * pace + ServeLateReach;
            return Mathf.Min(g, 2 * drop / (fall * fall));
        }
        /// Motion detection needs a moment of swing before it can confirm one, so the moment
        /// it reports is always later than the moment the player actually started. Without
        /// this correction every serve reads as late.
        public const float ServeLatency = .10f;
        /// The same correction when the swing is reported at onset rather than confirmation:
        /// only the short onset hold and the rise to threshold are left.
        public const float ServeOnsetLatency = .04f;
        /// A rally stroke is detected the same way, so it carries the same delay: `ServeOnsetLatency` when the phone
        /// reports it at onset, `ServeLatency` when it is first seen at confirmation (motion only; keys and tests are instant).
        public static float SwingDetectionLatency(bool atOnset, bool motion) => atOnset ? ServeOnsetLatency : motion ? ServeLatency : 0;

        /// Swing prediction (the phone's setting): a stroke reported at onset is proven, before the phone confirms it, once
        /// its rotation has reached `ProvenRate` over `ProvenArc` of turn. That is the evidence the phone's own peak
        /// confirmation accepts (SteeringFilter.peakConfirmRate / peakArc, after an onset that already held the stroke's
        /// force), without waiting for the rate to top out. A proven stroke strikes the ball at once; confirmation no longer
        /// gates it, and a write-off before the ball leaves still cancels it. Change these with SteeringFilter's.
        public const float ProvenRate = 7f, ProvenArc = .3f;

        /// Watches the phone's samples for the stroke that proves itself (see `ProvenRate`).
        public struct OnsetStrength
        {
            int onsets; double last; float peak, arc; bool proven;
            /// Feed every sample in order: the phone's onset count and onset time, the sample's time and its rotation rate
            /// (rad/s). True once per stroke, on the sample that proves it. Like the phone, the turn counts from the onset.
            public bool Add(int onsetCount, double onsetTime, double time, float rate)
            {
                if (onsetCount != onsets) { onsets = onsetCount; last = onsetTime; peak = arc = 0; proven = false; }
                if (proven || onsetCount <= 0 || time < onsetTime || float.IsNaN(rate)) return false;
                peak = Mathf.Max(peak, rate);
                if (time > last) { arc += rate * (float)System.Math.Min(time - last, .05); last = time; }
                return proven = peak >= ProvenRate && arc >= ProvenArc;
            }
        }

        /// Display-delay catch-up (TennisGame.CompensateDisplayDelay). A stroke that should already be `shift` game seconds
        /// along used to jump there in one frame, short of contact by `CatchUpOldFloor`: with a big TV delay that skipped
        /// nearly the whole approach and the racket popped onto the ball. Now it jumps at most `CatchUpJump` and plays the
        /// rest of the approach faster (at most `CatchUpPace` times), arriving no sooner than `CatchUpFloor`. A small shift
        /// (a cable, a fast TV) is still one plain jump, exactly as before.
        public const float CatchUpJump = .05f, CatchUpPace = 3f, CatchUpFloor = .06f, CatchUpOldFloor = .02f;

        /// `left`: the approach still to play (swing seconds, pace 1); `shift`: how far ahead it should be. Returns the jump,
        /// with the pace for the rest, and `late`: how much later than the old one-frame jump the contact frame now arrives,
        /// which grading takes back off so the swing is judged exactly as before.
        public static float CatchUp(float left, float shift, out float pace, out float late)
        {
            pace = 1; late = 0;
            if (left <= 0 || shift <= 0) return 0;
            float arrive = Mathf.Max(left - shift, Mathf.Min(left, CatchUpFloor));
            late = arrive - Mathf.Max(left - shift, Mathf.Min(left, CatchUpOldFloor));
            float jump = Mathf.Min(CatchUpJump, left - arrive);
            if (left - jump > CatchUpPace * arrive) jump = left - CatchUpPace * arrive;
            pace = (left - jump) / arrive;
            return jump;
        }
        /// Contact happens above the head, not wherever the racket happens to be resting.
        public const float ServeContactHeight = 2.45f;
        /// Clearance the ball must have over the net for a serve to count as safe.
        public const float NetMargin = .22f;
        /// How far off the centre mark the server stands, and how wide the receiver waits.
        /// The server stands behind the baseline, well out toward the sideline on the side
        /// they serve from.
        public const float ServerStance = 2.35f, ReceiverStance = 1.95f, ServeDepth = 12.35f;

        public struct ServeJudgement
        {
            public bool Struck, Legal, Perfect;
            public Vector3 Landing;
            public float Speed, Accuracy, Power, Toss;
            public string Label;
        }

        // --- The controller serve -------------------------------------------------------
        //
        // The player bounces the ball until they press TOSS on the phone. A meter there swings
        // back and forth; pressing it in the middle is a perfect toss. The arm rises slowly and
        // the ball goes high; the power bar on the TV fills as it rises and peaks at the top,
        // with a small perfect window there. Swinging commits the power the bar shows. A
        // perfect toss with a perfect swing goes exactly where the player aimed on the phone,
        // as fast as a serve goes, and is harder to return. The serve plays slower than the
        // rally (ServePace) and the game returns to full pace once the ball is struck.

        /// The serve's pace against the rally's: still the slowest part of the game, but brisker than it
        /// was (.75): the toss, the apex and the swing all arrive ~17% sooner in real time.
        public const float ServePace = .9f;
        /// The tossing arm's rise once TOSS is pressed (game seconds; it was .5, a 0.67 s wait in real
        /// time before the ball even left the hand, now about a third of a second).
        public const float ServeWindUp = .3f;
        /// How far either side of the top of the toss the power bar has anything to give.
        public const float ServePowerWindow = .4f;
        /// Swings with less power than this are too early or too late to clear the net.
        public const float ServeFaultPower = .12f;
        /// Swing onset must be within 45 real milliseconds of the apex for a perfect serve (it was 25,
        /// tighter than the sensor-to-screen chain's own jitter, so a "perfect" was mostly luck).
        public const float ServePerfectRealSeconds = .045f;
        /// A perfect toss is inside the middle 12% of the meter's half-width: +/-30 ms at the ticker's
        /// speed of four half-widths a second (it was the middle 5%, +/-12.5 ms).
        public const float ServePerfectToss = .88f;
        /// Maximum landing scatter, in metres, for a press at either end of the toss meter.
        public const float ServeTossMaxSpread = 2.6f;

        /// Continuous penalty outside the perfect zone: further from centre means more error.
        public static float TossError(float accuracy) =>
            Mathf.Clamp01((ServePerfectToss - Mathf.Clamp01(accuracy)) / ServePerfectToss);

        public static Vector2 ServeTossScatter(float accuracy, float rollX, float rollZ)
        {
            float spread = ServeTossMaxSpread * TossError(accuracy);
            return new Vector2((Mathf.Clamp01(rollX) * 2 - 1) * spread,
                (Mathf.Clamp01(rollZ) * 2 - 1) * spread * .7f);
        }
        /// The fastest serve, reserved for a perfect one (m/s).
        public const float ServeTopSpeed = 53f;

        /// The power bar: 1 at the top of the toss, falling away either side. `fromApex` is
        /// when the swing began relative to the top (seconds of game time).
        public static float ServePowerAt(float fromApex) =>
            Mathf.Clamp01(1 - Mathf.Abs(fromApex) / ServePowerWindow);

        public static bool ServePerfectTiming(float fromApex) => Mathf.Abs(fromApex) <= ServePerfectWindow;

        /// Where an aimed serve lands. `aim.x` runs from the T (-1) to wide (+1) across the
        /// target box; `aim.y` from short (0) to deep (1).
        public static Vector3 ServeAimPoint(Vector2 aim, bool serverNearSide, bool deuceCourt)
        {
            float outward = ServeTargetIsPositiveX(serverNearSide, deuceCourt) ? 1 : -1;
            float x = outward * Mathf.Lerp(.35f, CourtHalfWidth - .3f, (Mathf.Clamp(aim.x, -1, 1) + 1) / 2);
            float z = ServiceLine * Mathf.Lerp(.45f, .93f, Mathf.Clamp01(aim.y));
            return new Vector3(x, BallRadius, serverNearSide ? z : -z);
        }

        /// The racket has to be swinging about this long before the ball arrives (the stroke's
        /// lead-in), so the receiver's decision is due that much earlier than the ball itself.
        public const float ServeSwingLead = .12f;

        /// Share of the rival's serves that may be left unreturnable from where the player stands
        /// (the rest are eased toward the player until they can be reached). It grows with the
        /// server's skill, but never past `MaxUnreturnableServes`.
        public const float MaxUnreturnableServes = .15f;
        public static float UnreturnableServeShare(float skill) =>
            Mathf.Min(MaxUnreturnableServes, .05f + .3f * skill * skill);

        /// Could a receiver standing at (`playerX`, `playerZ`) get a racket on this serve? Flies it
        /// to where it crosses in front of them after the bounce and compares the time it takes
        /// with the time they need: react, run the gap beyond their reach, and have the racket
        /// already swinging (`ServeSwingLead`) when the ball arrives.
        public static bool ServeReachable(Vector3 start, Vector3 velocity, float spin, float restitution, float playerX, float playerZ)
        {
            Vector3 p = start, v = velocity; int bounced = 0;
            float plane = playerZ + (velocity.z < 0 ? .65f : -.65f);
            for (float t = 0; t < 3; t += TennisBall.Step)
            {
                TennisBall.Integrate(ref p, ref v, spin, TennisBall.Step);
                if (p.y < BallRadius && v.y < 0) { p.y = BallRadius; TennisBall.Bounce(ref v, ref spin, restitution); bounced++; }
                if (bounced > 0 && (velocity.z < 0 ? p.z <= plane : p.z >= plane))
                {
                    float gap = Mathf.Abs(p.x - playerX) - StrokeReach;
                    return gap <= 0 || ReactionTime + TimeToCover(gap, RunSpeed) + ServeSwingLead <= t;
                }
            }
            return false;
        }

        /// Keep a landing inside the target box, `margin` from its lines.
        public static Vector3 IntoServiceBox(Vector3 landing, bool serverNearSide, bool deuceCourt, float margin = .15f)
        {
            float outward = ServeTargetIsPositiveX(serverNearSide, deuceCourt) ? 1 : -1;
            float x = outward * Mathf.Clamp(Mathf.Abs(landing.x) * (Mathf.Sign(landing.x) == outward ? 1 : 0), margin, CourtHalfWidth - margin);
            float z = Mathf.Clamp(Mathf.Abs(landing.z), 1.8f, ServiceLine - margin);
            return new Vector3(x, BallRadius, serverNearSide ? z : -z);
        }

        /// Judge a controller serve: `fromApex` from the swing, `toss` from the phone's meter,
        /// `aim` from the phone's box. The rolls are the caller's randomness for the scatter an
        /// imperfect serve has.
        public static ServeJudgement JudgeServeStrike(float fromApex, float toss, Vector2 aim, bool serverNearSide, bool deuceCourt,
            bool secondServe, float rollX, float rollZ)
        {
            var j = new ServeJudgement { Struck = true, Power = ServePowerAt(fromApex), Toss = Mathf.Clamp01(toss) };
            j.Perfect = ServePerfectTiming(fromApex) && j.Toss >= ServePerfectToss;
            // Two separate skills: the toss meter decides how close to the aim it lands, the
            // swing's timing (the power bar) decides how fast. Both perfect: a perfect serve.
            float quality = j.Perfect ? 1 : j.Power * Mathf.Lerp(.6f, 1, j.Toss);
            j.Accuracy = quality;
            var target = ServeAimPoint(aim, serverNearSide, deuceCourt);
            if (j.Power < ServeFaultPower)
            {
                // Swung far too early or late: struck flat into the tape.
                j.Legal = false;
                j.Landing = new Vector3(target.x * .5f, BallRadius, serverNearSide ? .6f : -.6f);
                j.Speed = 18;
                j.Label = fromApex < 0 ? "FAULT — swung too early" : "FAULT — swung too late";
                return j;
            }
            j.Legal = true;
            // Placement is the toss: dead centre on the meter lands on the aim, and it wanders
            // further the further off centre the toss was. The wander is not rescued: aim at
            // the lines with a loose toss and it can land long or wide -- a fault, called when
            // it bounces. The risk is what makes the lines worth aiming at.
            Vector2 scatter = ServeTossScatter(j.Toss, rollX, rollZ);
            var landing = IntoServiceBox(target, serverNearSide, deuceCourt)
                + new Vector3(scatter.x, 0, scatter.y);
            // Never so short it would not clear the net.
            float minZ = 1.8f;
            if (Mathf.Abs(landing.z) < minZ) landing.z = serverNearSide ? minZ : -minZ;
            j.Landing = new Vector3(landing.x, BallRadius, landing.z);
            j.Speed = j.Perfect ? ServeTopSpeed : Mathf.Lerp(22, 42, j.Power * j.Power);
            if (secondServe) j.Speed *= .82f;
            bool inBox = ServeIsIn(j.Landing, serverNearSide, deuceCourt);
            j.Label = j.Perfect ? $"PERFECT SERVE · {j.Speed * 3.6f:0} km/h" : inBox ? $"SERVE IN · {j.Speed * 3.6f:0} km/h" : $"SERVE · {j.Speed * 3.6f:0} km/h";
            return j;
        }

        /// Which half of the court a serve must land in. The server starts each game on the
        /// deuce (right-hand) court and serves diagonally, so the target box is on the
        /// opposite side of the centre line from the server.
        public static bool ServeTargetIsPositiveX(bool serverNearSide, bool deuceCourt) =>
            serverNearSide ? !deuceCourt : deuceCourt;

        /// Centre of the box a serve must land in, for aiming and for the landing marker.
        public static Vector3 ServeTargetCentre(bool serverNearSide, bool deuceCourt)
        {
            float x = (CourtHalfWidth * .5f) * (ServeTargetIsPositiveX(serverNearSide, deuceCourt) ? 1 : -1);
            return new Vector3(x, BallRadius, (ServiceLine * .55f) * (serverNearSide ? 1 : -1));
        }

        /// Did a serve land in? Must clear the net, be on the receiver's side, inside the
        /// service line, and in the correct half.
        public static bool ServeIsIn(Vector3 landing, bool serverNearSide, bool deuceCourt)
        {
            float z = landing.z;
            if (serverNearSide ? (z <= 0 || z > ServiceLine) : (z >= 0 || z < -ServiceLine)) return false;
            if (Mathf.Abs(landing.x) > CourtHalfWidth) return false;
            return (landing.x >= 0) == ServeTargetIsPositiveX(serverNearSide, deuceCourt);
        }

        /// Velocity for a serve that is guaranteed to clear the net and still land on target.
        ///
        /// The plain ballistic solution takes the flattest arc that reaches the target, and
        /// from any realistic contact height that arc passes *under* the net — which made
        /// every serve a fault no matter how well it was timed. This lofts the arc until the
        /// ball is comfortably clear at the net crossing.
        public static Vector3 ServeVelocity(Vector3 start, Vector3 landing, float speed, float spin)
        {
            if (Mathf.Abs(spin) < .01f) return ServeVelocity(start, landing, speed);
            // Spun serves are solved numerically, then lofted until they clear the net by the
            // same margin the flat solution guarantees.
            Vector3 best = Vector3.zero;
            for (float s2 = speed; s2 > 8; s2 *= .92f)
            {
                best = TennisBall.Solve(start, landing, s2, spin);
                if (NetClearance(start, best, spin) > NetHeight + NetMargin) return best;
            }
            return best;
        }

        /// A player's shot, lofted until it clears the net by a margin that grows with the
        /// quality of the contact. Weak contacts give up pace and depth while staying playable.
        public static Vector3 RallyVelocity(Vector3 start, Vector3 target, float speed, float spin, float quality)
        {
            // Even a frame contact gets a safe arc; placement and pace supply the disadvantage.
            float margin = Mathf.Lerp(.22f, LegacyFlatShots ? .32f : RallyNetClearance, Mathf.Clamp01(quality / .7f));
            Vector3 best = TennisBall.Solve(start, target, speed, spin);
            for (float s = speed; s > 9; s *= .93f)
            {
                best = TennisBall.Solve(start, target, s, spin);
                if (NetClearance(start, best, spin) > NetHeight + margin) return best;
            }
            return best;
        }

        /// How far over the tape a clean rally ball passes (metres above the net).
        public const float RallyNetClearance = .7f;
        /// Editor proof only (HERO_OLDARC=1): the pre-Plan-1B flat net-skimming rally lines.
        public static readonly bool LegacyFlatShots = System.Environment.GetEnvironmentVariable("HERO_OLDARC") == "1";

        /// A rally shot to `target`, lofted until it clears the net by `clearance`: the ball still
        /// lands where it was aimed, on a visible gravity arc instead of the flattest line.
        public static Vector3 RallyArcVelocity(Vector3 start, Vector3 target, float speed, float spin, float clearance)
        {
            Vector3 best = TennisBall.Solve(start, target, speed, spin);
            for (float s = speed; s > 8; s *= .94f)
            {
                best = TennisBall.Solve(start, target, s, spin);
                if (NetClearance(start, best, spin) > NetHeight + clearance) return best;
            }
            return best;
        }

        /// Where an assisted hit met the strings. The swing was steered onto the ball, so the
        /// ball's distance from the racket when the hit was judged says nothing about the
        /// strings (it put every dot on the frame). Instead the contact is placed by how well
        /// it was made: a well-timed, well-positioned hit lands on the sweet spot, a poor one
        /// out toward the frame. Early/late moves it across the face and a high/low ball up
        /// or down it. `quality` 0..1, `early` and `high` -1..1. Metres on the string bed.
        public static Vector2 AssistedFace(float quality, float early, float high)
        {
            float radial = Mathf.Lerp(.95f, .04f, Mathf.Clamp01(quality));
            var dir = new Vector2(Mathf.Clamp(early, -1, 1), Mathf.Clamp(high, -1, 1));
            dir = dir.sqrMagnitude > .0004f ? dir.normalized : new Vector2(0, -1);
            return new Vector2(dir.x * radial * StringHalfWidth, dir.y * radial * StringHalfHeight);
        }

        /// Clamp a contact offset onto the string bed for display: an assisted hit is measured
        /// from wherever the ball was, which can be well off the racket.
        public static Vector2 OnStringBed(Vector2 offset)
        {
            var scaled = new Vector2(offset.x / StringHalfWidth, offset.y / StringHalfHeight);
            if (scaled.magnitude <= 1.05f) return offset;
            scaled = scaled.normalized * 1.05f;
            return new Vector2(scaled.x * StringHalfWidth, scaled.y * StringHalfHeight);
        }

        /// Height of a (possibly spun) ball as it crosses the net plane, by simulation.
        public static float NetClearance(Vector3 start, Vector3 velocity, float spin)
        {
            Vector3 p = start, v = velocity;
            for (int i = 0; i < 600; i++)
            {
                Vector3 before = p;
                TennisBall.Integrate(ref p, ref v, spin, TennisBall.Step);
                if (before.z * p.z <= 0)
                {
                    float t = Mathf.Abs(p.z - before.z) < 1e-6f ? 0 : -before.z / (p.z - before.z);
                    return Mathf.Lerp(before.y, p.y, Mathf.Clamp01(t));
                }
                if (p.y < BallRadius && v.y < 0) return 0;
            }
            return 0;
        }

        public static Vector3 ServeVelocity(Vector3 start, Vector3 landing, float speed)
        {
            float distance = new Vector2(landing.x - start.x, landing.z - start.z).magnitude;
            float flight = Mathf.Max(.28f, distance / Mathf.Max(12, speed));
            Vector3 best = Velocity(start, landing, flight);
            for (int i = 0; i < 60; i++)
            {
                Vector3 candidate = Velocity(start, landing, flight);
                if (NetCrossingHeight(start, landing, candidate, flight) > NetHeight + NetMargin) return candidate;
                best = candidate;
                flight += .03f;
            }
            return best;
        }

        static Vector3 Velocity(Vector3 start, Vector3 landing, float flight) =>
            (landing - start) / flight + Vector3.up * (4.905f * flight);

        /// How high the ball is as it passes over the net, for a given launch.
        public static float NetCrossingHeight(Vector3 start, Vector3 landing, Vector3 velocity, float flight)
        {
            float span = landing.z - start.z;
            if (Mathf.Abs(span) < .0001f) return start.y;
            float t = -start.z / span * flight;
            if (t <= 0 || t >= flight) return start.y;
            return start.y + velocity.y * t - 4.905f * t * t;
        }

        /// Where the meaningful part of a stroke clip lives. Playing from `StrokeEntry`
        /// rather than 0 skips a slow ready-in that a reactive swing has no time for, so the
        /// business end runs near authored speed instead of the whole clip being crushed.
        ///
        /// The spans are chosen so the clip genuinely accelerates INTO contact and relaxes
        /// afterwards. A first attempt used .32/.50/.88, which looks reasonable but covers
        /// 0.38 of the clip after contact against 0.18 before — making the follow-through
        /// 36% faster than the approach, i.e. decelerating into the ball. The window either
        /// side of contact has to be weighted against the real time available on each side.
        public const float StrokeEntry = .26f, StrokeContact = .50f, StrokeExit = .74f;

        /// Map elapsed swing time onto the stroke clip: accelerate into contact, then relax
        /// through the follow-through. Pure so the curve can be checked without a scene.
        public static float StrokePlayhead(float swingAge, float swingDuration) =>
            StrokePlayhead(swingAge, swingDuration, StrokeContact);

        /// Same curve, centred on a particular clip's own contact frame. Every clip used to be
        /// assumed to strike the ball exactly halfway through, whatever it actually animates;
        /// the measured frame (see ClipContacts) lands the racket on the ball on time.
        public static float StrokePlayhead(float swingAge, float swingDuration, float contact)
        {
            ContactWindow(contact, out float entry, out float exit);
            float toContact = SweetTime * swingDuration / StrokeDuration;
            if (swingAge <= toContact)
                return Mathf.Lerp(entry, contact, toContact > 0 ? Mathf.Clamp01(swingAge / toContact) : 1);
            float after = (swingAge - toContact) / Mathf.Max(.01f, swingDuration - toContact);
            return Mathf.Lerp(contact, exit, Mathf.Clamp01(after));
        }

        /// The slice of a clip a stroke plays, either side of its contact frame. Keeps the
        /// same spans as the default .26/.50/.74, shifted, and kept inside the clip.
        public static void ContactWindow(float contact, out float entry, out float exit)
        {
            contact = Mathf.Clamp(contact, .2f, .8f);
            entry = Mathf.Max(.02f, contact - (StrokeContact - StrokeEntry));
            exit = Mathf.Min(.98f, contact + (StrokeExit - StrokeContact));
        }

        /// Two-handed backhand shaping, layered on top of the clip.
        ///
        /// Measurement first: the authored Forehand and Backhand clips rotate the chest and
        /// hips by *identical* amounts, so the torso does the same thing in both strokes.
        /// They are not the same stroke, so the shared motion is right for the forehand by
        /// luck and wrong for the backhand.
        ///
        /// The reference is a TWO-handed backhand: both hands stay on the grip for the whole
        /// stroke, the shoulders coil deeply in preparation -- the player's back turns most
        /// of the way to the net -- the swing runs low to high, and the finish carries up
        /// over the leading shoulder with the hands still together. That is a different shape
        /// from a one-hander, where the off arm releases and sweeps back as a counterbalance;
        /// an earlier version of this modelled the one-hander and was simply the wrong stroke.
        ///
        /// Coil therefore peaks during the BACKSWING and releases through contact, rather
        /// than being held at contact the way a one-hander holds its chest side-on.
        /// Now authored into the clips; kept as the reference the Blender fix uses.
        public const float BackhandCoil = 42f;        // extra degrees of shoulder turn, peak backswing
        public const float BackhandSecondGrip = .085f; // metres down the handle for the off hand

        /// Coil strength across the stroke: builds into the backswing, releases through the
        /// ball, gone by the finish.
        public static float BackhandCoilAt(float playhead)
        {
            float span = Mathf.InverseLerp(StrokeEntry, StrokeExit, playhead);
            // Peak just before contact, then fall away faster than it built.
            return span < .35f ? Mathf.SmoothStep(0, 1, span / .35f)
                 : Mathf.SmoothStep(1, 0, Mathf.Clamp01((span - .35f) / .5f));
        }

        /// Locomotion styling, from running and tennis-movement biomechanics.
        ///
        /// Tennis coaching draws a hard line between the two ways of covering ground: a
        /// shuffle keeps the hips square to the net and is used for short distances, while a
        /// crossover step rotates the hips and is what you use when you have to reach a wide
        /// ball. Running the character square-on at every speed is what made the movement
        /// read as artificial.
        ///
        /// Running biomechanics adds the rest: the thorax and pelvis counter-rotate to cancel
        /// the angular momentum of the swinging legs, and that rotation grows with speed --
        /// trunk transverse-plane rotation is the component that changes most between walking
        /// and running. Arm swing is the dominant upper-body motion and scales with the legs.
        ///
        /// The thresholds below are sourced; the magnitudes are tuned for readability at the
        /// gameplay camera distance rather than measured.
        public const float ShuffleSpeed = 1.9f;      // below this, stay square to the net
        public const float CrossoverYaw = 70f;       // degrees of body turn at full sprint: turn and run
        public const float TrunkCounterRotation = 13f;   // degrees, anti-phase with the stride
        public const float ArmSwing = .24f;          // metres of fore/aft hand travel at sprint

        /// 0 while shuffling square to the net, 1 at a full crossover sprint.
        public static float CrossoverBlend(float speed) =>
            Mathf.Clamp01((Mathf.Abs(speed) - ShuffleSpeed) / Mathf.Max(.01f, RunSpeed - ShuffleSpeed));

        /// How far the body turns toward the direction of travel.
        public static float BodyYaw(float speed) =>
            Mathf.Sign(speed) * CrossoverYaw * CrossoverBlend(speed);

        /// One full run cycle covers roughly this far on the ground; root motion is stripped
        /// at import so it cannot be measured from the clip.
        public const float StrideMetres = 2.1f;

        /// Run-cycle advance for a ground speed, in cycles per second. No floor: standing
        /// still must not keep the feet turning over.
        public static float CycleRate(float speed) => Mathf.Abs(speed) / StrideMetres;

        // --- Timing sets the pace, the swing sets the direction --------------------------------
        //
        // Golf separates the two jobs and is easy to read: you choose where, then the swing decides how well.
        // A rally shot does the same in one motion. WHERE you swing picks the side: the racket face (the
        // phone) turned toward the left of the TV sends the ball left, square to it straight, toward the right
        // right. WHEN you swing picks the pace and the depth: on the ball is a deep, fast drive, a little off is
        // a rally ball, well off a slow, short floater the opponent can attack. Contact itself is generous (see
        // `EarlySwingHold`), so nearly every swing meets the ball and the skill is in how good the shot is.
        //
        // The 2026-10-10 pass had timing pick the side (Wii Sports' own rule); playtests wanted timing to mean
        // power and the swing to mean direction, so that was reversed. The racket-face reading is shaped here
        // with a wide straight band and full angle well inside a comfortable wrist turn, so it is not the
        // twitchy degree-per-10-cm number it was before the timing pass.

        /// Racket-face aim (-1..1 as the phone sends it; its calibration tops out near 0.8) inside this
        /// band hits straight up the middle: wrist wobble must not steer a ball.
        public const float SwingAimDeadBand = .15f;
        /// Face aim at which the ball goes to the corner.
        public const float SwingAimFull = .75f;

        /// Direction from the swing, -1 (left corner) .. 1 (right corner), from the racket-face aim.
        public static float SideFromSwing(float aim)
        {
            float a = Mathf.Abs(Mathf.Clamp(aim, -1, 1));
            if (a <= SwingAimDeadBand) return 0;
            return Mathf.Sign(aim) * Mathf.Clamp01((a - SwingAimDeadBand) / (SwingAimFull - SwingAimDeadBand));
        }

        /// Rally pace from timing (`TimingScore`, 1 on the ball .. 0 at the edge of contact), in the speed the
        /// shot solver takes. Swing effort only nudges it, as in golf a smooth swing on time beats a hard one off it.
        /// The range is set against Wii Sports Tennis, measured from gameplay video: about 1.55 s from one hit to
        /// the next in a casual rally, about 0.95 s at Pro level. Through the real flight (GameSpeed included) a
        /// mistimed ball here takes about 1.6 s baseline to baseline, a GOOD one 1.35 s, a GREAT one 1.2 s and a
        /// PERFECT one 0.95 s -- Wii's Pro pace, the shot that wins points. The old range (13-30) put every clean
        /// ball under 0.9 s. See docs/tennis-timing-power-2026-10-24.md.
        public const float SlowRallyPace = 11.5f, RallyPace = 14.5f, FastRallyPace = 20.5f;
        public static float TimingPace(float timing, float power, float stamina)
        {
            float t = Mathf.Clamp01(timing);
            float pace = t < .55f ? Mathf.Lerp(SlowRallyPace, RallyPace, t / .55f)
                : Mathf.Lerp(RallyPace, FastRallyPace, Mathf.Pow((t - .55f) / .45f, 1.3f));
            return pace * Mathf.Lerp(.95f, 1.05f, Mathf.Clamp01(power)) * Mathf.Lerp(.92f, 1f, Mathf.Clamp01(stamina));
        }

        /// Where a rally ball goes. The swing's side is kept whatever the timing (it is never punished twice);
        /// the timing, through `quality`, decides the depth -- a clean hit lands deep, a poor one sits up short --
        /// how close to the line the ball can go, and how much it scatters. Always inside the lines: a rally ball
        /// is never out, so new players keep the ball in play and the challenge is beating the opponent with it.
        public static Vector3 SwingPlacement(float aim, float quality, float rollX, float rollZ)
        {
            float control = Mathf.SmoothStep(0, 1, Mathf.Clamp01(quality / .85f));
            float side = SideFromSwing(aim);
            float width = Mathf.Lerp(2.4f, CourtHalfWidth - .45f, control);
            float spread = Mathf.Lerp(.6f, .05f, control);
            float x = side * width + Mathf.Clamp(rollX, -1, 1) * spread;
            float z = Mathf.Lerp(6.2f, 10.4f, control) + Mathf.Clamp(rollZ, -1, 1) * spread;
            return new Vector3(Mathf.Clamp(x, -CourtHalfWidth + .12f, CourtHalfWidth - .12f), BallRadius,
                Mathf.Clamp(z, 2.8f, CourtHalfLength - .3f));
        }

        /// A swing this early still meets the ball: the character holds the racket back and lets it go as the
        /// ball arrives (the shot is graded on the real, early timing, so it is slow). Earlier than this is a
        /// whiff. The October audit measured every swing more than 0.10 s early missing outright.
        public const float EarlySwingHold = .32f;

        /// How long to hold a swing that started `early` game seconds before the ball will reach it (0 when it
        /// is on time or late, or so early it is a whiff).
        public static float SwingHold(float early, float speedScale = 1)
        {
            if (early <= .015f * speedScale || early > EarlySwingHold * speedScale) return 0;
            return early;
        }

        /// "LEFT", "RIGHT" or "" (straight): the hit badge's reading of the swing's direction.
        public static string SwingSideWord(float aim)
        {
            float side = SideFromSwing(aim);
            return side < -.01f ? "LEFT" : side > .01f ? "RIGHT" : "";
        }

        /// Which authored stroke suits the ball. Height and distance pick the animation, so
        /// the character visibly volleys at the net and reaches down for a low ball.
        public static string StrokeFor(float ballHeight, float ballZ, float playerZ, float lateralGap, bool highLift)
        {
            if (ballHeight > 1.75f) return "Smash";
            if (highLift) return "Lob";
            // A volley is about where the PLAYER is standing, not how near the ball has got:
            // testing ball-to-player distance made almost every rally ball a volley, because
            // the ball is always close to the player by the time they swing at it.
            if (Mathf.Abs(playerZ) < 7f && ballHeight > .8f) return "Volley";
            if (ballHeight < .55f) return "LowPickup";
            // Out of normal reach: throw the body at it. The dive clips exist in both wings.
            if (lateralGap > DiveGap) return "Dive";
            if (lateralGap > 1.1f) return "Running";
            return "Drive";
        }

        /// Lateral gap beyond which a stroke becomes a dive.
        public const float DiveGap = 1.75f;

        /// Where the server must stand: behind their own baseline, on the side of the centre
        /// mark matching the court they are serving from.
        public static float ServerStanceX(bool serverNearSide, bool deuceCourt) =>
            (serverNearSide ? 1 : -1) * (deuceCourt ? 1 : -1) * ServerStance;

        /// Where the receiver waits: on the side the serve is legally required to go, which
        /// is their own deuce side when the server is on theirs.
        public static float ReceiverStanceX(bool serverNearSide, bool deuceCourt) =>
            (ServeTargetIsPositiveX(serverNearSide, deuceCourt) ? 1 : -1) * ReceiverStance;

        /// Is a rally ball's bounce inside the singles court?
        public static bool BounceIsIn(Vector3 landing) =>
            Mathf.Abs(landing.x) <= CourtHalfWidth && Mathf.Abs(landing.z) <= CourtHalfLength;

        /// Where a ball will first touch the ground, by plain ballistics. Used for the
        /// landing marker and to judge in/out before the bounce actually happens.
        public static bool PredictLanding(Vector3 position, Vector3 velocity, out Vector3 landing, float spin = 0, float curve = 0) =>
            TennisBall.Landing(position, velocity, spin, out landing, out _, curve);

        public static Vector3 ShotTarget(float aim,float power) => new Vector3(Mathf.Clamp(aim,-1,1)*3.25f,BallRadius,Mathf.Lerp(4.5f,9.5f,Mathf.Clamp01(power)));

        public static Vector3 ShotVelocity(Vector3 start,Vector3 target,float speed)
        {
            Vector3 delta=target-start;
            float flight=Mathf.Max(.25f,new Vector2(delta.x,delta.z).magnitude/Mathf.Max(12,speed));
            return delta/flight+Vector3.up*(4.905f*flight);
        }

        // Relative sweep catches fast balls crossing the string bed between simulation steps.
        public static bool CrossStringBed(Vector3 oldBall, Vector3 ball, Vector3 oldCenter, Vector3 center,
            Vector3 normal, Vector3 right, Vector3 up, out Vector2 offset)
        {
            Vector3 a = oldBall - oldCenter, b = ball - center;
            float da = Vector3.Dot(a, normal), db = Vector3.Dot(b, normal);
            offset = default;
            if (da * db > 0 || Mathf.Abs(da - db) < .000001f) return false;
            Vector3 at = Vector3.Lerp(a, b, da / (da - db));
            offset = new Vector2(Vector3.Dot(at, right), Vector3.Dot(at, up));
            return new Vector2(offset.x / (StringHalfWidth + BallRadius), offset.y / (StringHalfHeight + BallRadius)).magnitude <= 1;
        }
    }
}
