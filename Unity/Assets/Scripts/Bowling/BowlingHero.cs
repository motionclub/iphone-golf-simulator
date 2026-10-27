using System.Collections.Generic;
using GolfArcade.Hub;
using GolfArcade.Tennis;
using UnityEngine;

namespace GolfArcade.Bowling
{
    /// A player's real match hero in the bowling alley (replaces the P0 mannequin). The legs are the
    /// hero's own Idle / Walk / Run, blended by the ground speed the game moves the hero at
    /// (HubHeroAnimator, as in the plaza), so every move walks: side-steps to a new board, the
    /// four-step approach, walking back to the approach after the ball, and walking over to the
    /// ball return while a friend bowls. On top of the clips, the bowling arm is posed as the
    /// pendulum of the swing (straight arm, as real bowlers swing), the off arm goes out for balance,
    /// and the ball rides in the hand. The authored Bowl_* clips replace the arm pose in P2.
    [DefaultExecutionOrder(950)]   // after HubHeroAnimator (900) has posed the skeleton
    public sealed class BowlingHero : MonoBehaviour
    {
        public HubHeroAnimator Anim { get; private set; }
        public MatchHeroLook Look { get; private set; }
        public bool Female { get; private set; }

        /// The swing: pendulum angle of the bowling arm (0 = straight down, + forward), or NaN for the clip's own arm.
        public float ArmDeg = float.NaN;
        /// Off arm out to the side for balance, 0..1.
        public float Balance;
        /// The ball in the hand (null = empty-handed).
        public Transform Ball;

        Vector3 target; float targetYaw, yaw, speed;
        bool walking, driven;
        Transform upperArm, lowerArm, hand, leftUpper, leftLower, leftHand, midProx, idxProx, litProx, midDist, lMidProx, lIdxProx, lLitProx;
        float carryW;   // the two-handed carry's share of the arms (eases in and out over ~0.25 s)
        HeroBallGrip.Hand gripR, gripL;
        Vector3 holeLocal; bool holeKnown; static bool logged;
        float palmSign;

        public Vector3 Position => transform.position;
        public bool Arrived => !walking;

        public static BowlingHero Spawn(Transform parent, bool female, Vector3 at, float facingYaw)
        {
            var root = new GameObject(female ? "Bowler Female" : "Bowler Male");
            root.AddComponent<GolfArcade.CharacterLod.HeroLodExempt>();   // full detail: the LOD copies of the bowling kit bodies show holes
            root.transform.SetParent(parent, false);
            root.transform.position = at;
            var prefab = Resources.Load<GameObject>(GolfArcade.Game.HeroAssets.Bowling(female));   // the bowling kit hero
            if (!prefab) prefab = TennisCustomization.HeroBase(female);
            if (!prefab) { Debug.LogError("[Bowling] match hero prefab missing: " + TennisCustomization.HeroPath(female)); return null; }
            var go = Instantiate(prefab, root.transform, false);
            go.transform.localPosition = Vector3.zero; go.transform.localRotation = Quaternion.identity;
            var hero = root.AddComponent<BowlingHero>();
            hero.Female = female;
            hero.Look = go.GetComponent<MatchHeroLook>();
            // no racket in the alley (its grip transform stays, its renderers hide)
            if (hero.Look && hero.Look.racketGrip) foreach (var r in hero.Look.racketGrip.GetComponentsInChildren<Renderer>(true)) r.enabled = false;
            hero.Anim = HubHeroAnimator.Attach(go);
            if (hero.Anim) { hero.Anim.GameTime = true; hero.Anim.AfterPose += hero.PoseArms; }
            if (hero.Look)
            {
                hero.upperArm = hero.Look.Bone(HumanBodyBones.RightUpperArm); hero.lowerArm = hero.Look.Bone(HumanBodyBones.RightLowerArm); hero.hand = hero.Look.Bone(HumanBodyBones.RightHand);
                hero.midProx = hero.Look.Bone(HumanBodyBones.RightMiddleProximal); hero.idxProx = hero.Look.Bone(HumanBodyBones.RightIndexProximal);
                hero.litProx = hero.Look.Bone(HumanBodyBones.RightLittleProximal); hero.midDist = hero.Look.Bone(HumanBodyBones.RightMiddleDistal);
                hero.leftUpper = hero.Look.Bone(HumanBodyBones.LeftUpperArm); hero.leftLower = hero.Look.Bone(HumanBodyBones.LeftLowerArm); hero.leftHand = hero.Look.Bone(HumanBodyBones.LeftHand);
                hero.lMidProx = hero.Look.Bone(HumanBodyBones.LeftMiddleProximal); hero.lIdxProx = hero.Look.Bone(HumanBodyBones.LeftIndexProximal); hero.lLitProx = hero.Look.Bone(HumanBodyBones.LeftLittleProximal);
                hero.gripR = HeroBallGrip.Find(hero.Look.Bone, false); hero.gripL = HeroBallGrip.Find(hero.Look.Bone, true);
            }
            hero.target = at; hero.yaw = hero.targetYaw = facingYaw;
            root.transform.rotation = Quaternion.Euler(0, facingYaw, 0);
            return hero;
        }

        /// Puts the hero exactly here, moving at `groundSpeed` (the approach: the game drives the body).
        public void Drive(Vector3 position, float facingYaw, float groundSpeed)
        {
            walking = false; target = position; targetYaw = facingYaw; driven = true;
            transform.position = position; yaw = facingYaw; speed = groundSpeed;
            transform.rotation = Quaternion.Euler(0, yaw, 0);
        }

        /// Walks to `position`, turning to face the way it goes, then turns to `facingYaw` on arrival
        /// (and sits down there when `sit`: the lounge settee). `via`: waypoints on the way (round the lounge furniture, down
        /// the step to the lounge floor), taken only when the destination changes.
        public void WalkTo(Vector3 position, float facingYaw, bool sit = false, IList<Vector3> via = null)
        {
            SettleApproach();
            bool moved = (position - target).sqrMagnitude > .0004f;
            target = position; targetYaw = facingYaw; sitOnArrival = sit;
            if (moved) { route.Clear(); if (via != null) route.AddRange(via); }
            walking = (position - transform.position).sqrMagnitude > .0004f;
            if (walking && moved && Anim) Anim.Seated = false;   // stand up first
        }
        bool sitOnArrival;
        readonly List<Vector3> route = new List<Vector3>();
        public Vector3 Target => target;
        /// Metres still to walk (along the waypoints), 0 when there.
        public float Remaining
        {
            get
            {
                if (!walking) return 0;
                float d = 0; var at = transform.position;
                foreach (var p in route) { d += Flat(p - at).magnitude; at = p; }
                return d + Flat(target - at).magnitude;
            }
        }

        /// Skips the rest of a walk: the hero is at the destination, facing its way (and seated, if it was going to sit).
        public void Snap()
        {
            if (!walking) return;
            route.Clear(); walking = false; speed = speedVel = yawVel = 0;
            transform.position = target; yaw = targetYaw;
            transform.rotation = Quaternion.Euler(0, yaw, 0);
            if (Anim) Anim.Seated = sitOnArrival;
        }

        /// The ball carried in both hands (walking up from the lounge, before the stance clip takes it).
        public bool CarryBothHands = true;
        /// Proof films only: the hands as they were before 10-27 (one-handed carry, no palms-in), for before/after pictures.
        public static bool LegacyHands;

        /// A one-shot reaction: an Emote_* clip from the standard set (e.g. "EmoteFistPump").
        public bool React(string emote)
        {
            if (!Anim) return false;
            SettleApproach();
            bool ok = Anim.Play(emote);
            if (!ok) Debug.LogWarning($"[Bowling] {name} has no emote '{emote}' (has: {string.Join(", ", Anim.Emotes)})");
            return ok;
        }

        // ---- the authored Bowl_* clips (BowlingClips). The approach clips carry the body's travel inside the clip (the hips run 3.55 m from the stance),
        // so while one plays the game leaves the root at the stance spot; when it ends the root moves where the bowler finished.
        string clipId; float clipStarted; bool approachClip, shiftPending;
        float followYaw, followFrom = -1;      // the follow-through is turned toward the path of the ball (SetFollowThrough)
        public bool HasClips => Anim && Anim.Has(BowlingClips.Shot);
        public bool ClipPlaying => Anim && Anim.Playing != null && Anim.Playing.StartsWith("Bowl");
        public bool ApproachClipPlaying => approachClip && ClipPlaying;
        /// An approach clip is in progress or has not yet settled the root (the game keeps the root at the stance until then).
        public bool ApproachActive => shiftPending;
        /// Seconds into the playing bowling clip.
        public float ClipTime => ClipPlaying ? Anim.ActionTime : 0;

        /// The ball's real heading (degrees about the vertical, + = toward the bowler's right) once it is released at clip time `releaseClipTime`: from then on the bowling arm is turned
        /// that way about the shoulder (the clip's own follow-through goes straight up the lane), so the hand follows through along the ball's path, whatever it is.
        public void SetFollowThrough(float headingDeg, float releaseClipTime)
        {
            followYaw = Mathf.Clamp(headingDeg * 2.5f, -25f, 25f); followFrom = releaseClipTime;
        }

        /// Plays a bowling clip (BowlingClips ids) from `at` seconds. `approach` marks the shot clips, whose root travel is applied on their end.
        public bool PlayClip(string id, float at = 0, bool loop = false, bool approach = false)
        {
            if (!Anim || !Anim.Has(id)) return false;
            if (!approach && !IsShotVariant(id)) SettleApproach();   // a reaction / walk clip starts from the stand where the shot ended
            if (!Anim.Play(id, loop, at)) return false;
            Anim.ActionRate = 1;
            clipId = id; clipStarted = Time.time - at;
            if (approach) followFrom = -1;
            if (approach) { approachClip = true; shiftPending = true; }
            return true;
        }

        static bool IsShotVariant(string id) => id.StartsWith("BowlRelease") || id.StartsWith("BowlDrop") || id.StartsWith("BowlFollow") || id == BowlingClips.Foul || id == BowlingClips.Shot;

        /// The stance at the start spot: a looping ready hold (the ball in both hands at the chest). Returns false when the clips are missing.
        public bool EnsureStance()
        {
            if (!HasClips) return false;
            if (ClipPlaying && Anim.Playing == BowlingClips.Stance) return true;
            if (ClipPlaying && (Anim.Playing == BowlingClips.Abort || approachClip)) return true;
            return PlayClip(BowlingClips.Stance, 0, true);
        }

        /// The approach clip has ended or the bowler starts walking: the root takes the position the clip finished at.
        void SettleApproach()
        {
            if (!shiftPending) return;
            shiftPending = false; approachClip = false;
            var p = transform.position + transform.forward * BowlingClips.EndForward(clipId);
            transform.position = p; target = p;
        }

        public const float WalkSpeed = 1.25f, SideStepSpeed = .8f;
        /// How far ahead along the route the walker steers (corners become arcs of about this radius), how long the heading takes to
        /// settle into a turn, and the fastest it turns (deg/s).
        const float LookAhead = .55f, TurnTime = .16f, MaxTurn = 300, StopDecel = 1.4f;
        float yawVel, speedVel;
        /// The floor height under a point (BowlingGame: the approach, the lounge floor one step down, the players' dais).
        public static System.Func<Vector3, float> Ground;

        /// The point `ahead` metres further along the route (waypoints, then the destination) from the hero's projection on it.
        Vector3 PathPoint(float ahead)
        {
            var at = transform.position; at.y = 0;
            float left = ahead;
            foreach (var w in route)
            {
                var flat = Flat(w); float seg = (flat - at).magnitude;
                if (seg >= left) return at + (flat - at) * (left / seg);
                left -= seg; at = flat;
            }
            var t = Flat(target); float last = (t - at).magnitude;
            return last > 1e-4f ? at + (t - at) * Mathf.Min(1, left / last) : t;
        }

        /// The bowler's body x for a ball on `board` (a right-hander holds the ball outside the right hip).
        public static float BodyX(float board) => BowlingLane.BoardX(board) - .2f;

        void Update()
        {
            float dt = Time.deltaTime; if (dt <= 0) return;
            if (walking)
            {
                // 10-27 (Adnan: "walking feels clunky"): steered, not snapped. The body heads for a point LookAhead along the route, so
                // corners become arcs; the heading eases in and out of turns (it used to snap at 540 deg/s at every waypoint, and spun
                // round at the stance while already walking); the pace eases up, slows in a tight turn and settles onto the spot.
                while (route.Count > 0 && Flat(route[0] - transform.position).magnitude < LookAhead * .8f) route.RemoveAt(0);
                bool last = route.Count == 0;
                var flatTo = Flat(target - transform.position);
                float d = Remaining;
                bool sidestep = last && d < .9f && Mathf.Abs(flatTo.z) < .05f;   // a few boards across: shuffle sideways, still facing the pins
                var aim = last ? target : PathPoint(LookAhead);
                var dir = Flat(aim - transform.position);
                float wantYaw = sidestep || dir.sqrMagnitude < 1e-6f ? targetYaw : Mathf.Atan2(dir.x, dir.z) * Mathf.Rad2Deg;
                // the last steps: turn toward the way they will stand (into the seat: side-stepping round to face the room)
                bool settling = last && d < .6f;
                if (settling) wantYaw = Mathf.LerpAngle(wantYaw, targetYaw, Mathf.InverseLerp(.6f, .15f, d));
                yaw = Mathf.SmoothDampAngle(yaw, wantYaw, ref yawVel, TurnTime, MaxTurn, dt);
                float off = Mathf.Abs(Mathf.DeltaAngle(yaw, wantYaw));
                float pace = sidestep ? SideStepSpeed : WalkSpeed * Mathf.Lerp(.2f, 1, Mathf.InverseLerp(110, 25, off));   // facing away: turn first, a slow step or two
                pace = Mathf.Min(pace, Mathf.Sqrt(2 * StopDecel * d) + .02f);      // brake to arrive at walking pace zero (not stop dead from 0.4 m/s)
                if (Anim && Anim.Seated) pace = 0;                                  // still getting up
                speed = Mathf.SmoothDamp(speed, pace, ref speedVel, .12f, 6, dt);
                float step = speed * dt; if (last) step = Mathf.Min(step, flatTo.magnitude);
                var heading = sidestep || settling ? (dir.sqrMagnitude > 1e-8f ? dir.normalized : Vector3.zero) : Quaternion.Euler(0, yaw, 0) * Vector3.forward;
                var p = transform.position + heading * step;
                p.y = Ground != null ? Mathf.MoveTowards(p.y, Ground(p), .9f * dt) : target.y;   // the step down to the lounge floor and back up
                transform.position = p;
                if (last && Flat(target - p).magnitude <= .01f) { walking = false; speedVel = 0; transform.position = target; }   // (the legs settle from the last slow step: speed decays below)
            }
            else
            {
                yaw = Mathf.SmoothDampAngle(yaw, targetYaw, ref yawVel, TurnTime, MaxTurn, dt);
                if (!driven) speed = Mathf.MoveTowards(speed, 0, 6 * dt);   // the game stopped driving the body: come to rest
                if (Anim && sitOnArrival && Mathf.Abs(Mathf.DeltaAngle(yaw, targetYaw)) < 5) Anim.Seated = true;
            }
            driven = false;
            if (shiftPending && !ClipPlaying && Time.time - clipStarted > .2f) SettleApproach();
            transform.rotation = Quaternion.Euler(0, yaw, 0);
            if (Anim) Anim.Tick(speed, dt);
        }

        /// The ball centre in the gripping hand: a frame from bone positions only (hand, middle / index / little knuckles), see BowlingClips.GripFrame.
        Vector3 GripCentre()
        {
            var k = BowlingClips.GripFrame(Female);
            Vector3 h0 = hand.position, pm = midProx.position;
            var e1 = (pm - h0).normalized;
            var s = idxProx.position - litProx.position;
            var e2 = (s - Vector3.Dot(s, e1) * e1).normalized;
            var e3 = Vector3.Cross(e1, e2);
            // the palm side is the one the curled middle finger folds toward (decided while the hand holds the ball, then kept)
            if (palmSign == 0 && midDist) { float d = Vector3.Dot(midDist.position - pm, e3); if (Mathf.Abs(d) > .004f) palmSign = Mathf.Sign(d); }
            if (palmSign < 0) e3 = -e3;
            return h0 + e1 * k.x + e2 * k.y + e3 * k.z;
        }

        static Vector3 Flat(Vector3 v) { v.y = 0; return v; }

        static void Aim(Transform bone, Transform child, Vector3 want)
        {
            if (!bone || !child) return;
            var have = child.position - bone.position; if (have.sqrMagnitude < 1e-8f) return;
            bone.rotation = Quaternion.FromToRotation(have.normalized, want.normalized) * bone.rotation;
        }

        /// Adnan 10-27: "hands are fucked up, inverted when not holding the ball, especially female". Empty-handed, the walk, the stand
        /// and the seat left the palms facing forward or up (the female most). Each hand is rolled about its own axis (wrist to middle
        /// knuckle) so the palm faces the thigh, a little back, as a relaxed arm hangs; seated, palm down on the thigh. `w` is the share
        /// of the pose that is not an authored clip (those keep their own hands).
        void PalmsIn(float w, float seat)
        {
            if (w < .01f) return;
            Vector3 up = transform.up, fwd = transform.forward, right = transform.right;
            seat = Mathf.SmoothStep(0, 1, seat);
            RollPalm(hand, midProx, idxProx, litProx, false, Vector3.Slerp((-right - fwd * .35f).normalized, -up, seat), w, ref palmRollR);
            RollPalm(leftHand, lMidProx, lIdxProx, lLitProx, true, Vector3.Slerp((right - fwd * .35f).normalized, -up, seat), w, ref palmRollL);
        }

        float palmRollR, palmRollL;
        /// Rolls the hand by the turn that brings its palm to `want`, eased over ~0.1 s (the turn the animation needs can jump as a clip
        /// blends in or out: applied at once, the hand flicked through ~1000 deg/s for a few frames as a walk started or stopped).
        void RollPalm(Transform hd, Transform mid, Transform idx, Transform lit, bool left, Vector3 want, float w, ref float applied)
        {
            if (!hd || !mid || !idx || !lit) return;
            var axis = (mid.position - hd.position).normalized;
            var across = Vector3.ProjectOnPlane(idx.position - lit.position, axis).normalized;   // toward the thumb side
            var palm = left ? Vector3.Cross(across, axis) : Vector3.Cross(axis, across);        // the way the palm faces
            var have = Vector3.ProjectOnPlane(palm, axis); var to = Vector3.ProjectOnPlane(want, axis);
            if (have.sqrMagnitude < 1e-8f || to.sqrMagnitude < 1e-8f) return;
            float need = Vector3.SignedAngle(have, to, axis) * w;
            applied += Mathf.DeltaAngle(applied, need) * (1 - Mathf.Exp(-Time.deltaTime / .08f));
            hd.rotation = Quaternion.AngleAxis(applied, axis) * hd.rotation;
        }

        /// The two-handed carry (Adnan 10-27: "they should carry with two hands"): the ball in front of the belly, the bowling hand
        /// under it on the right, the other hand on its left side, palms toward the ball, elbows down by the ribs. Two-bone reach for
        /// each arm, blended with the clip's arms by `w`. Returns the ball centre.
        bool Carry(float w, out Vector3 centre)
        {
            centre = default;
            if (!upperArm || !lowerArm || !hand || !leftUpper || !leftLower || !leftHand) return false;
            Vector3 up = transform.up, fwd = transform.forward, right = transform.right;
            var shoulders = .5f * (upperArm.position + leftUpper.position);
            float r = BowlingLane.BallRadius;
            centre = shoulders - up * .3f + fwd * (.2f + r);   // in front of the belly
            Reach(upperArm, lowerArm, hand, midProx, idxProx, litProx, false, centre, centre + (right * .8f - up * .55f).normalized * (r + .02f), fwd * .75f - up * .2f + right * .1f, w);
            Reach(leftUpper, leftLower, leftHand, lMidProx, lIdxProx, lLitProx, true, centre, centre + (-right * .95f + up * .2f).normalized * (r + .02f), fwd * .8f + up * .1f - right * .1f, w);
            return true;
        }

        /// One arm: the palm to `palm` (on the ball's surface), the fingers along `along`, the palm turned to face `ball`; the elbow down and out.
        void Reach(Transform ua, Transform la, Transform hd, Transform mid, Transform idx, Transform lit, bool left, Vector3 ball, Vector3 palm, Vector3 along, float w)
        {
            Quaternion r0 = ua.rotation, r1 = la.rotation, r2 = hd.rotation;
            Vector3 up = transform.up, right = transform.right, fwd = transform.forward;
            along = along.normalized;
            var wrist = palm - along * .055f;   // the wrist sits behind the palm's centre
            Vector3 s = ua.position; float a = (la.position - s).magnitude, b = (hd.position - la.position).magnitude;
            var st = wrist - s; float d = Mathf.Clamp(st.magnitude, Mathf.Abs(a - b) + 1e-3f, a + b - 1e-3f); var n = st.normalized;
            float x = (a * a - b * b + d * d) / (2 * d), h = Mathf.Sqrt(Mathf.Max(0, a * a - x * x));
            var pole = Vector3.ProjectOnPlane(-up - fwd * .25f + right * (left ? -.45f : .45f), n).normalized;
            var elbow = s + n * x + pole * h;
            Aim(ua, la, elbow - s);
            Aim(la, hd, s + n * d - elbow);
            if (mid)
            {
                Aim(hd, mid, along);
                if (idx && lit)
                {
                    // roll about the hand's axis so the palm faces the ball (palm normal by handedness, as HubHeroAnimator builds it)
                    var axis = (mid.position - hd.position).normalized;
                    var across = Vector3.ProjectOnPlane(idx.position - lit.position, axis).normalized;
                    var palmN = left ? Vector3.Cross(across, axis) : Vector3.Cross(axis, across);
                    var toBall = Vector3.ProjectOnPlane(ball - hd.position, axis);
                    if (toBall.sqrMagnitude > 1e-8f) hd.rotation = Quaternion.AngleAxis(Vector3.SignedAngle(Vector3.ProjectOnPlane(palmN, axis), toBall, axis), axis) * hd.rotation;
                }
            }
            if (w < 1)
            {
                Quaternion i0 = ua.rotation, i1 = la.rotation, i2 = hd.rotation;
                ua.rotation = Quaternion.Slerp(r0, i0, w); la.rotation = Quaternion.Slerp(r1, i1, w); hd.rotation = Quaternion.Slerp(r2, i2, w);
            }
        }

        void LateUpdate() { if (!Anim) PoseArms(); }

        /// The bowling layer on the hero's pose: the follow-through turned toward the ball's path, the ball in the hand (or carried in
        /// both), the scripted pendulum without clips, the empty hands' palms in. Runs inside HubHeroAnimator's pass (AfterPose).
        void PoseArms()
        {
            Vector3 up = transform.up, fwd = transform.forward, right = transform.right;
            if (ClipPlaying && followFrom >= 0 && upperArm && Mathf.Abs(followYaw) > .05f)
            {
                float t = ClipTime - followFrom;
                float w = Mathf.SmoothStep(0, 1, t / .3f) * (1 - Mathf.SmoothStep(0, 1, (t - 1.6f) / 1.3f));   // turns in over 0.3 s after the release, stays through the swing, eases out
                if (w > 1e-3f) upperArm.RotateAround(upperArm.position, transform.up, followYaw * w);
            }
            // walking up with the ball (no clip yet, no scripted swing): both hands carry it in front of the belly, and the carry eases out as the stance clip takes over
            bool carrying = CarryBothHands && !LegacyHands && Ball && !ClipPlaying && float.IsNaN(ArmDeg);
            carryW = Mathf.MoveTowards(carryW, carrying ? 1 : 0, Time.deltaTime / .25f);
            if (ClipPlaying)
            {
                // the authored clip owns both arms; the ball sits where the fitted grip puts it (middle and ring fingers and the thumb in its holes)
                if (Ball && hand)
                {
                    float ct = ClipTime;
                    if (clipId == BowlingClips.SitIdleBall && leftHand) Ball.position = .5f * (hand.position + leftHand.position) + fwd * .045f + up * .035f;
                    else if (midProx && idxProx && litProx) Ball.position = GripCentre();
                    else Ball.position = hand.position + -up * (BowlingLane.BallRadius * .75f) + right * .02f;
                    if (carryW > 0 && Carry(carryW, out var centre)) Ball.position = Vector3.Lerp(Ball.position, centre, carryW);
                    Hold(clipId == BowlingClips.SitIdleBall || carryW > .5f);
                }
                return;
            }
            if (carrying && Carry(carryW, out var held))
            {
                // while the carry eases in (the ball just picked up), the ball rides on the bowling hand's palm and slides to the carry point as the arms arrive
                Ball.position = carryW >= .999f || !HeroBallGrip.Valid(gripR) ? held
                    : Vector3.Lerp(HeroBallGrip.Seat(gripR, BowlingLane.BallRadius, HeroBallGrip.PalmSkin(Female)), held, Mathf.SmoothStep(0, 1, carryW));
                Hold(carryW > .5f); return;
            }
            // empty hands on the authored locomotion / stand / seat (no bowling clip): palms in
            if (!Ball && float.IsNaN(ArmDeg) && Anim && !LegacyHands) PalmsIn(1 - Anim.Weights.w, Anim.SeatWeight);
            else palmRollR = palmRollL = 0;   // (eased in again from nothing when the hands are free)
            if (!float.IsNaN(ArmDeg) && upperArm)
            {
                // the pendulum: a straight arm a little out from the hip, so the ball clears the leg
                var dir = Quaternion.AngleAxis(-ArmDeg, right) * -up;
                dir = (dir + right * .14f).normalized;
                Aim(upperArm, lowerArm, dir);
                Aim(lowerArm, hand, dir);
            }
            if (Balance > .01f && leftUpper)
            {
                // off arm out to the side, near shoulder height, palm down (REFERENCES.md §1.3)
                var side = (-right * .9f + -up * .35f + fwd * .2f).normalized;
                var hang = leftLower && leftUpper ? (leftLower.position - leftUpper.position).normalized : -up;
                Aim(leftUpper, leftLower, Vector3.Slerp(hang, side, Balance));
                if (leftLower && leftHand) Aim(leftLower, leftHand, Vector3.Slerp((leftHand.position - leftLower.position).normalized, side, Balance));
            }
            if (Ball && hand)
            {
                // the ball sits in the palm, below and a little forward of the hand bone
                var down = !float.IsNaN(ArmDeg) ? (Quaternion.AngleAxis(-ArmDeg, right) * -up) : -up;
                Ball.position = hand.position + down * (BowlingLane.BallRadius * .75f) + right * .02f;
                Hold(false);
            }
        }

        /// The hands on the held ball (Adnan 10-27: "make sure it looks like they are actually holding it ... needs actual rigidness"), on the
        /// final arm pose, after the ball is placed. One-handed grip: the ball turned so its holes are under the middle and ring fingers and
        /// the thumb, the index and little fingers laid on its surface. Two hands (carry, seated): every finger and both thumbs closed on
        /// the surface. A free hand within reach of the ball (the stance's both-hands start) closes on it too.
        void Hold(bool twoHands)
        {
            if (!Ball) return;
#if UNITY_EDITOR
            if (System.Environment.GetEnvironmentVariable("BALL_GRIP") == "0") return;
#endif
            float r = BowlingLane.BallRadius, pad = HeroBallGrip.FingerPad(Female);
            var c = Ball.position;
            if (twoHands)
            {
                HeroBallGrip.Wrap(gripR, c, r, pad, 1);
                HeroBallGrip.Wrap(gripL, c, r, pad, 1);
                return;
            }
            AlignHoles(c);
            HeroBallGrip.Wrap(gripR, c, r, pad, 1, holes: true);
            if (HeroBallGrip.Valid(gripL))
            {
                HeroBallGrip.Palm(gripL, out var pc, out _, out _, out _);
                float gap = (pc - c).magnitude - r;   // palm centre to the ball's surface
                float w = 1 - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.03f, .08f, gap));
                if (w > .01f) HeroBallGrip.Wrap(gripL, c, r, pad, w);
            }
        }

        /// Turns the ball so its holes (found on its mesh: the vertices well inside the radius) face the gripping fingers' tips.
        void AlignHoles(Vector3 c)
        {
            if (!holeKnown)
            {
                holeKnown = true;
                var mf = Ball.GetComponentInChildren<MeshFilter>();
                if (mf && mf.sharedMesh && mf.sharedMesh.isReadable)
                {
                    var v = mf.sharedMesh.vertices; var sum = Vector3.zero; float rMax = 0;
                    foreach (var p in v) rMax = Mathf.Max(rMax, p.magnitude);
                    foreach (var p in v) if (p.magnitude < rMax * .9f) sum += p.normalized;
                    if (sum.sqrMagnitude > 1e-6f) holeLocal = Ball.InverseTransformDirection(mf.transform.TransformDirection(sum.normalized)).normalized;
                    if (!logged) { logged = true; Debug.Log($"[BowlingHero] ball hole axis (ball space) {holeLocal.x:0.0000},{holeLocal.y:0.0000},{holeLocal.z:0.0000} mesh {mf.sharedMesh.name}"); }
                }
            }
            if (holeLocal == Vector3.zero || !HeroBallGrip.Valid(gripR)) return;
            Transform Tip(Transform p) { var t = p; for (int i = 0; i < 2 && t && t.childCount > 0; i++) t = t.GetChild(0); return t; }
            var mid = Tip(gripR.middle); var ring = gripR.ring ? Tip(gripR.ring) : mid; var thumb = gripR.thumb ? Tip(gripR.thumb) : mid;
            if (!mid) return;
            var want = ((mid.position + ring.position + thumb.position) / 3 - c);
            if (want.sqrMagnitude < 1e-6f) return;
            var have = Ball.TransformDirection(holeLocal);
            Ball.rotation = Quaternion.FromToRotation(have, want.normalized) * Ball.rotation;
        }
    }
}
