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
        Transform upperArm, lowerArm, hand, leftUpper, leftLower, leftHand, midProx, idxProx, litProx, midDist;
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
            if (hero.Anim) hero.Anim.GameTime = true;
            if (hero.Look)
            {
                hero.upperArm = hero.Look.Bone(HumanBodyBones.RightUpperArm); hero.lowerArm = hero.Look.Bone(HumanBodyBones.RightLowerArm); hero.hand = hero.Look.Bone(HumanBodyBones.RightHand);
                hero.midProx = hero.Look.Bone(HumanBodyBones.RightMiddleProximal); hero.idxProx = hero.Look.Bone(HumanBodyBones.RightIndexProximal);
                hero.litProx = hero.Look.Bone(HumanBodyBones.RightLittleProximal); hero.midDist = hero.Look.Bone(HumanBodyBones.RightMiddleDistal);
                hero.leftUpper = hero.Look.Bone(HumanBodyBones.LeftUpperArm); hero.leftLower = hero.Look.Bone(HumanBodyBones.LeftLowerArm); hero.leftHand = hero.Look.Bone(HumanBodyBones.LeftHand);
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
        /// (and sits down there when `sit`: the lounge settee).
        public void WalkTo(Vector3 position, float facingYaw, bool sit = false)
        {
            SettleApproach();
            bool moved = (position - target).sqrMagnitude > .0004f;
            target = position; targetYaw = facingYaw; sitOnArrival = sit;
            walking = (position - transform.position).sqrMagnitude > .0004f;
            if (walking && moved && Anim) Anim.Seated = false;   // stand up first
        }
        bool sitOnArrival;

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

        /// The bowler's body x for a ball on `board` (a right-hander holds the ball outside the right hip).
        public static float BodyX(float board) => BowlingLane.BoardX(board) - .2f;

        void Update()
        {
            float dt = Time.deltaTime; if (dt <= 0) return;
            if (walking)
            {
                var to = target - transform.position; to.y = 0;
                float d = to.magnitude;
                bool sidestep = d < .9f && Mathf.Abs(to.z) < .05f;   // a few boards across: shuffle sideways, still facing the pins
                float want = sidestep ? SideStepSpeed : WalkSpeed;
                speed = Mathf.MoveTowards(speed, d < .25f ? Mathf.Min(want, d * 3) : want, 4 * dt);
                float step = Mathf.Min(d, speed * dt);
                transform.position += d > 1e-4f ? to / d * step : Vector3.zero;
                float faceTo = sidestep ? targetYaw : Mathf.Atan2(to.x, to.z) * Mathf.Rad2Deg;
                yaw = Mathf.MoveTowardsAngle(yaw, d > .05f ? faceTo : targetYaw, 540 * dt);
                if (d <= .005f) { walking = false; speed = 0; }
                if (Anim && Anim.Seated) { speed = 0; }   // still getting up
            }
            else
            {
                yaw = Mathf.MoveTowardsAngle(yaw, targetYaw, 360 * dt);
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

        static void Aim(Transform bone, Transform child, Vector3 want)
        {
            if (!bone || !child) return;
            var have = child.position - bone.position; if (have.sqrMagnitude < 1e-8f) return;
            bone.rotation = Quaternion.FromToRotation(have.normalized, want.normalized) * bone.rotation;
        }

        void LateUpdate()
        {
            Vector3 up = transform.up, fwd = transform.forward, right = transform.right;
            if (ClipPlaying && followFrom >= 0 && upperArm && Mathf.Abs(followYaw) > .05f)
            {
                float t = ClipTime - followFrom;
                float w = Mathf.SmoothStep(0, 1, t / .3f) * (1 - Mathf.SmoothStep(0, 1, (t - 1.6f) / 1.3f));   // turns in over 0.3 s after the release, stays through the swing, eases out
                if (w > 1e-3f) upperArm.RotateAround(upperArm.position, transform.up, followYaw * w);
            }
            if (ClipPlaying)
            {
                // the authored clip owns both arms; the ball sits where the fitted grip puts it (middle and ring fingers and the thumb in its holes)
                if (Ball && hand)
                {
                    float ct = ClipTime;
                    if (clipId == BowlingClips.SitIdleBall && leftHand) Ball.position = .5f * (hand.position + leftHand.position) + fwd * .045f + up * .035f;
                    else if (midProx && idxProx && litProx) Ball.position = GripCentre();
                    else Ball.position = hand.position + -up * (BowlingLane.BallRadius * .75f) + right * .02f;
                }
                return;
            }
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
            }
        }
    }
}
