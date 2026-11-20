using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

namespace GolfArcade.Tennis
{
    /// Visual puppet for a hero on top of a gameplay TennisActor (HERO_MAINSTAY: the match heroes, MatchHeroLook).
    /// The actor (hidden) stays the gameplay authority: movement, swing timing, racket contact test,
    /// scoring. This component only READS it and plays the hero's own clips so that each stroke
    /// clip's authored contact frame lands on the actor's gameplay contact. No gameplay effect.
    ///
    /// The match heroes play their FBX stroke, locomotion and emote clips on their own skeleton, as authored. The driver keeps what
    /// belongs to a puppet (contact lock, honest contact assist, the serve ritual, planted feet) and leaves out the
    /// stylised body layers and the clearance models that were measured on the old chibi body (see `Match`). The old Hero_* clips
    /// are not played by any slot. The visual overhaul adds seven Generic performance assets for Idle, point and match
    /// reactions and the whiff reaction; missing assets still fall back cleanly. (SERVE_AND_FEET: Serve plus Walk, RunForward, RunLeft and RunRight are in
    /// the set; the base layer plays them by ground speed, planted-foot speed = actor speed at `walkClipSpeed` / `runClipSpeed`.)
    [DefaultExecutionOrder(1000)]
    public sealed class HeroTennisDriver : MonoBehaviour
    {
        /// The first 17 ids are the original slots (Ready .. Walk). The match clips use Ready = ReadyIdle, Forehand, Backhand,
        /// Serve, Volley = VolleyForehand, Smash = Overhead, and the ids after Walk for the rest of the set.
        public enum Clip { Ready, Idle, Forehand, Backhand, Serve, Volley, Smash, RunForward, RunRight, RunLeft,
                           HitPerfect, MissWhiff, CelebratePoint, SadPointLost, MatchWin, MatchLose, Walk,
                           ForehandWide, ForehandShort, BackhandWide, SliceApproach, Return, VolleyBackhand,
                           ForehandOpen, SplitToForehand, SplitToBackhand, RecoverCenter,
                           EmoteScuba, EmoteThrust, EmoteSpike, IntroWave, IntroBringIt, IntroPushups,   // EMOTES: three taunts and three intros (match heroes only)
                          EmoteJumpJoy, EmoteFistPump, EmoteStomp, EmoteSlump, EmoteShock, EmoteVictory, EmoteDefeat }   // EMOTE STANDARD: joy, excited, mad, sad, shock, big win, big loss
        const int Count = 40;
        // Visual tempo only: contact remains anchored to the actor's authoritative hit time. (The match heroes play at 1.0: their
        // clips already carry the real swing speed, with the racket fastest at contact.)
        public static float AnimationTempo = 1.2f;
        /// `leftRelease`: seconds into the clip when the off hand lets go of the racket (0 = it is not on the racket at the contact).
        [Serializable] public struct ClipSlot { public Clip id; public AnimationClip clip; public float contact; public float leftRelease; }
        public ClipSlot[] slots = new ClipSlot[0];
        public TennisActor actor;
        public TennisGame game;
        /// HERO_MAINSTAY: the look of the match hero this driver puppets.
        public MatchHeroLook matchLook;
        public bool isPlayer;
        /// Serve ritual times in the Serve clip (seconds): stance with the ball held, toss arm up at the release, trophy. Written by the
        /// prefab builder from the clip's own keys (match heroes); the old Serve clip's values are the defaults.
        public float serveStanceTime = .6f, serveReleaseTime = 1.45f, serveTrophyTime = 1.80f;
        /// 11-19 (Adnan: "the off arm should stay straight launching the ball, it bends super weird multiple times"): from the wind-up
        /// to the swing the tossing arm is the clip's own (a straight arm swinging up); the routine's straight-line ball path no longer
        /// drags the hand off that arc with the toss IK (it folded the elbow ~100 deg twice). The ball rides the palm until released
        /// (HeroTossHold). Set on the male match heroes, whose serve was rebuilt (work/serve-ref-1118); the bounce ritual keeps the IK.
        public bool tossFollowsClip;
        public bool TossFollowsClip => tossFollowsClip;
        /// 11-19: the overhead clip's trophy (racket up, other arm at the ball; work/serve-ref-1118 spike.py LIFT 19 = 0.30 s);
        /// a coming smash is prepared up to here.
        public float overheadTrophyTime = .30f;
        [Tooltip("Planted-foot speed (m/s) of the run clips at 1x, measured from the baked clips (feet_report.json).")] public float runClipSpeed = 5.8f;
        [Tooltip("Planted-foot speed of Hero_Walk_v5 at 1x (2 x 0.26 m stride over 0.54 s stance).")] public float walkClipSpeed = .96f;
        [Tooltip("Match heroes: the forward run played backwards (backing away from the net) reads pivot - phase, so that its stance and swing line up with the sideways runs it is blended with. Written by ServeAndFeetWire from the clips' stance windows.")] public float runReversePivot = .2167f;
        double runPhase; bool runBack;
        float walkYaw;
        [Tooltip("Max distance the right arm is nudged so the racket meets the gameplay ball at contact.")] public float contactAssist = .5f;
        [Tooltip("Max body lunge toward the ball near contact (m).")] public float bodyReach = .3f;

        // ---- HERO_MAINSTAY: the match hero is played as authored. The stylised layers tuned to the old chibi body (kinetic-chain lead,
        // squash and stretch, chest springs, the receiving crouch, racket / arm clearance against the old torso model, hat / hair / eye
        // systems) went with the old Hero01 look (2026-11-15).
        Animator Anim => matchLook.animator;
        Transform Grip => matchLook.racketGrip;
        Transform Rig => matchLook.transform;
        /// A bone of the hero by humanoid name. The match heroes are Generic rigs (their clips play on their own skeleton, nothing is retargeted), so
        /// their bones are looked up by the same names on the rig (MatchHeroLook.bones).
        Transform Bone(HumanBodyBones b) => matchLook.Bone(b);
        /// Which of the strokes in the match set and the legacy set count as a stroke clip (the ones with a contact frame).
        static readonly bool[] strokeClip = MakeStrokeTable();
        static bool[] MakeStrokeTable()
        {
            var t = new bool[Count];
            foreach (var c in new[] { Clip.Forehand, Clip.Backhand, Clip.Serve, Clip.Volley, Clip.Smash, Clip.ForehandWide, Clip.ForehandShort, Clip.BackhandWide,
                                      Clip.SliceApproach, Clip.Return, Clip.VolleyBackhand, Clip.ForehandOpen }) t[(int)c] = true;
            return t;
        }
        /// Slots absent from the original FBX set. ResolvePerformanceClips fills these
        /// with the authored Generic visual-overhaul assets, without legacy retargeting.
        /// (SERVE_AND_FEET: Walk, RunForward, RunRight and RunLeft are in the set now and play from the base layer by ground speed; WalkMode / runClipSpeed / walkClipSpeed apply.)
        public static readonly Clip[] MissingFromMatchSet = { Clip.HitPerfect, Clip.CelebratePoint, Clip.SadPointLost, Clip.MatchWin, Clip.MatchLose, Clip.MissWhiff };

        PlayableGraph graph; AnimationMixerPlayable mixer;
        // Plan 3A: an upper-body layer (duplicate action clips, avatar-masked) so a swing can ride on running
        // legs: the arms / spine swing while the legs keep their planted run cycle (no skate into swings).
        AnimationMixerPlayable upperMixer; AnimationLayerMixerPlayable layers;
        readonly AnimationClipPlayable[] upperPlayables = new AnimationClipPlayable[Count];
        /// Editor proof only: HERO_FLUID=0 turns the Plan 3A motion layers off (before/after captures).
        public static readonly bool FluidOff = Environment.GetEnvironmentVariable("HERO_FLUID") == "0";
        float legsFromRun, actionLegs; HeroTennisPerformance performance;
        HeroGarmentPoseCorrectives garmentCorrectives;
        /// Match heroes: the upper-body layer eases out when a stroke ends (and between two strokes the clips cross-fade) instead of snapping to the base pose.
        AvatarMask strokeUpperMask,reactionUpperMask;bool usingReactionMask;
        float reactionLegShare;public float ReactionLegShare => reactionLegShare;
        readonly float[] upperBlend = new float[Count]; float upperFade; int upperFadeClip = (int)Clip.Forehand;
        const float MatchUpperOut = .16f, MatchUpperSwitch = .09f;
        readonly AnimationClipPlayable[] playables = new AnimationClipPlayable[Count];
        readonly float[] length = new float[Count], contact = new float[Count], weight = new float[Count], leftRelease = new float[Count];
        readonly double[] time = new double[Count];
        readonly bool[] valid = new bool[Count];
        readonly float[] targetBuf = new float[Count], weightVel = new float[Count];
        float actionWeightVel;
        Clip action = Clip.Ready; bool actionActive, followThrough; float actionWeight; double actionTime;
        float lead = .4f; bool wasSwinging; Clip juice; bool juiceActive; double juiceTime;
        public Clip CurrentAction => actionActive ? action : juiceActive ? juice : Clip.Ready;
        readonly string[] clipName = new string[Count];
        /// Proof / review: the action, reaction or strongest base clip actually rendered.
        /// Locomotion blends are still reported in full by WeightReport.
        int DominantBaseClip()
        {
            int result = (int)Clip.Ready; float highest = -1;
            for (int k = 0; k < Count; k++) if (valid[k] && weight[k] > highest)
            { highest = weight[k]; result = k; }
            return result;
        }
        public string PlayingClip => clipName[actionActive ? (int)action : juiceActive ? (int)juice : DominantBaseClip()] ?? "";
        public float PlayingClipTime => actionActive ? (float)actionTime : juiceActive ? TennisEmotes.SourceTime(juice,(float)Math.Max(0, juiceTime),length[(int)juice]) : (float)time[DominantBaseClip()];
        /// Proof / review: every clip slot this hero has (id, FBX clip name, contact time).
        /// Diagnostics: the base mixer's non-zero input weights, the upper layer's weight and the clip it plays (the proof trace records this every frame).
        public string WeightReport()
        {
            var sb = new System.Text.StringBuilder();
            for (int k = 0; k < Count; k++) if (valid[k] && weight[k] > .001f) sb.Append($"{(Clip)k}={weight[k]:0.00} ");
            sb.Append($"upper={UpperLayerWeight:0.00}:{(actionActive ? action.ToString() : "-")}");
            return sb.ToString();
        }
        public string SlotReport()
        {
            var sb = new System.Text.StringBuilder();
            foreach (var s in slots) if (s.clip) sb.AppendLine($"{s.id}={s.clip.name} len={s.clip.length:0.000} contact={s.contact:0.0000} human={s.clip.humanMotion}");
            return sb.ToString();
        }
        public string State { get; private set; } = "Ready";

        public void Build()
        {
            ResolvePerformanceClips();
            foreach (var s in slots) { int i = (int)s.id; if (!s.clip) continue; valid[i] = true; length[i] = s.clip.length; contact[i] = s.contact; leftRelease[i] = s.leftRelease; clipName[i] = s.clip.name; }
            var animator = Anim;
            animator.applyRootMotion = false;
            graph = PlayableGraph.Create(name + " hero driver");
            graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);
            mixer = AnimationMixerPlayable.Create(graph, Count);
            foreach (var s in slots)
            {
                if (!s.clip) continue; int i = (int)s.id;
                playables[i] = AnimationClipPlayable.Create(graph, s.clip); playables[i].SetApplyFootIK(false); playables[i].SetSpeed(0);
                graph.Connect(playables[i], 0, mixer, i);
            }
            upperMixer = AnimationMixerPlayable.Create(graph, Count);
            foreach (var s in slots)
            {
                if (!s.clip) continue; int i = (int)s.id; if (!IsStroke((Clip)i) && !IsReaction((Clip)i) && !IsEmote((Clip)i)) continue;
                upperPlayables[i] = AnimationClipPlayable.Create(graph, s.clip); upperPlayables[i].SetApplyFootIK(false); upperPlayables[i].SetSpeed(0);
                graph.Connect(upperPlayables[i], 0, upperMixer, i);
            }
            layers = AnimationLayerMixerPlayable.Create(graph, 2);
            graph.Connect(mixer, 0, layers, 0); graph.Connect(upperMixer, 0, layers, 1);
            layers.SetInputWeight(0, 1); layers.SetInputWeight(1, 0);
            var upper = new AvatarMask();
            UpperBodyMask(upper);
            strokeUpperMask=upper;
            reactionUpperMask=new AvatarMask();UpperBodyMask(reactionUpperMask,false);
            layers.SetLayerMaskFromAvatarMask(1, upper);
            AnimationPlayableOutput.Create(graph, "Hero", animator).SetSourcePlayable(layers);
            weight[(int)Clip.Ready] = 1;
            BuildContactModel();
            inertia = new HeroTennisInertia(Bone(HumanBodyBones.Hips) ? Bone(HumanBodyBones.Hips) : animator.transform);
            // The body and eye meshes shipped with frozen bind-pose bounds: with lunges, crouches and big
            // swings Unity culled them at some camera angles (the hero "went transparent"). Always skin.
            foreach (var smr in Rig.GetComponentsInChildren<SkinnedMeshRenderer>(true)) { smr.updateWhenOffscreen = true; smr.quality = SkinQuality.Bone4; }
            {
                poseSafety = new HeroPoseSafety(matchLook);
                // hand clearance, bake-first: the baked corrections of the clips this graph plays (layer 1 = the upper-body mask)
                var hips = Bone(HumanBodyBones.Hips); var spine = Bone(HumanBodyBones.Spine);
                poseSafety.UseGraph(graph, (layer, bone) => layer == 0 || bone == hips || (spine && bone.IsChildOf(spine)));
                if (!FluidOff) performance = new HeroTennisPerformance(matchLook);
            }
            if (actor)
            {
                actor.Reacted += OnReacted;
                // The racket the player sees IS the gameplay racket: contact tests, launch point,
                // contact-frame ball and planned meet points all use the hero's strings.
                actor.RedirectStrings(stringCentre, stringRight, stringUp, stringNormal);
                actor.VisualContact = VisualContact;
                actor.VisualTossPoint = VisualTossPoint;
                actor.Posed += OnActorPosed;
            }
            if (isPlayer) { TennisGame.ContactMade += OnContact; TennisGame.Whiffed += OnWhiff; }
            else TennisGame.OpponentStruck += OnRivalStruck;
            BuildTrail();
        }

        /// Edit-mode export also resolves the resource performances before reading slots.
        /// It does not construct a graph or touch any gameplay contacts.
        public void ResolvePerformanceClips()
        {
            var combined = new List<ClipSlot>(slots);
            string sex = matchLook.female ? "Female" : "Male";
            foreach (var id in new[] { Clip.Idle, Clip.HitPerfect, Clip.MissWhiff, Clip.CelebratePoint, Clip.SadPointLost, Clip.MatchWin, Clip.MatchLose })
            {
                var clip = Resources.Load<AnimationClip>("Tennis/Performance/" + sex + "_" + id);
                if (!clip) continue;
                combined.RemoveAll(s => s.id == id);
                combined.Add(new ClipSlot { id = id, clip = clip });
            }
            // chat 4: the approved ReadyIdle resampled to 60 Hz (the base-model FBX that carries the meshes keeps its 30 Hz take)
            var ready60=Resources.Load<AnimationClip>("Tennis/Performance/"+sex+"_ReadyIdle60");
            if(ready60)for(int i=0;i<combined.Count;i++)if(combined[i].id==Clip.Ready){var slot=combined[i];slot.clip=ready60;combined[i]=slot;break;}
            var polished=Resources.Load<AnimationClip>("Tennis/Performance/"+sex+"_ForehandPolished");
            if(polished)for(int i=0;i<combined.Count;i++)if(combined[i].id==Clip.Forehand){var slot=combined[i];slot.clip=polished;combined[i]=slot;break;}
            if(Environment.GetEnvironmentVariable("TENNIS_ARM_REPAIR")!="0")foreach(var id in new[]{Clip.Forehand,Clip.Backhand}) {
                var repaired=Resources.Load<AnimationClip>("Tennis/Performance/"+sex+"_"+id+"ArmCorrected");
                if(repaired)for(int i=0;i<combined.Count;i++)if(combined[i].id==id){var slot=combined[i];slot.clip=repaired;combined[i]=slot;break;}
            }
            // EMOTE STANDARD: the point and match reactions are the emotion set's full-body clips when the hero has them
            // (they replace the one-arm Performance gestures): won point = jump for joy / fist pump, lost point = slump (or stomp,
            // see OnReacted), whiff = hands on head, match won = victory spin, match lost = drop to the knees.
            foreach (var (to, from) in new[] { (Clip.CelebratePoint, Clip.EmoteJumpJoy), (Clip.HitPerfect, Clip.EmoteFistPump), (Clip.SadPointLost, Clip.EmoteSlump),
                                               (Clip.MissWhiff, Clip.EmoteShock), (Clip.MatchWin, Clip.EmoteVictory), (Clip.MatchLose, Clip.EmoteDefeat) })
            {
                ClipSlot src = default; foreach (var s in combined) if (s.id == from && s.clip) { src = s; break; }
                if (!src.clip) continue;
                combined.RemoveAll(s => s.id == to);
                combined.Add(new ClipSlot { id = to, clip = src.clip });
            }
            slots = combined.ToArray();
        }

        /// Upper-body layer of a Generic rig: the hips and everything from the spine up (torso, head, arms, fingers, the racket in the hand); the legs
        /// stay on the base layer. Same split the Humanoid mask made (Body + Head + arms + fingers, no legs).
        void UpperBodyMask(AvatarMask mask,bool includeHips=true)
        {
            var root = Anim.transform; var paths = new List<string>();
            string PathOf(Transform t) { var p = t.name; for (var q = t.parent; q && q != root; q = q.parent) p = q.name + "/" + p; return p; }
            if(includeHips)paths.Add(PathOf(Bone(HumanBodyBones.Hips)));
            foreach (var t in Bone(HumanBodyBones.Spine).GetComponentsInChildren<Transform>(true)) paths.Add(PathOf(t));
            mask.transformCount = paths.Count;
            for (int i = 0; i < paths.Count; i++) { mask.SetTransformPath(i, paths[i]); mask.SetTransformActive(i, true); }
        }

        static bool IsReaction(Clip c) => c>=Clip.HitPerfect&&c<=Clip.MatchLose;
        void SetUpperMask(bool reaction)
        {
            if(usingReactionMask==reaction)return;
            usingReactionMask=reaction;layers.SetLayerMaskFromAvatarMask(1,reaction?reactionUpperMask:strokeUpperMask);
        }
        void OnDestroy()
        {
            if (graph.IsValid()) graph.Destroy();
            if(strokeUpperMask)Destroy(strokeUpperMask);if(reactionUpperMask)Destroy(reactionUpperMask);
            if (actor) { actor.Reacted -= OnReacted; actor.Posed -= OnActorPosed; actor.VisualContact = null; actor.VisualTossPoint = null; }
            TennisGame.ContactMade -= OnContact; TennisGame.Whiffed -= OnWhiff; TennisGame.OpponentStruck -= OnRivalStruck;
        }

        // ---- visible racket = gameplay racket
        Transform stringCentre, stringRight, stringUp, stringNormal; bool racketScaled;
        readonly Vector3[] contactLocal = new Vector3[Count]; readonly bool[] hasContact = new bool[Count];
        const float PathBefore = .5f, PathAfter = .55f;
        readonly Vector3[][] stringPath = new Vector3[Count][]; readonly float[] stringPathFrom = new float[Count];
        /// The clip's own strings at clip time `t` (hero space), within the table around the contact.
        Vector3 ClipStrings(int i, float t)
        {
            var p = stringPath[i]; if (p == null) return contactLocal[i];
            float x = Mathf.Clamp((t - stringPathFrom[i]) * TableRate, 0, p.Length - 1); int k = Mathf.Min((int)x, p.Length - 2);
            return Vector3.Lerp(p[k], p[k + 1], x - k);
        }
        // ---- chat 4 (2026-10-17): the game simulates in 1/120 s steps at its own pace, so the actor's time-to-contact moves in
        // steps of 2 or 3 sub-steps per displayed frame and a stroke clip driven straight off it judders (clip rate 1.0 / 1.5 / 0.5).
        // The hero reads the leftover step time and the swing's pace (private, read-only) and draws the swing where it really is.
        static readonly System.Reflection.FieldInfo StepRemainderField = typeof(TennisGame).GetField("accumulator", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        static readonly System.Reflection.FieldInfo SwingPaceField = typeof(TennisActor).GetField("swingPace", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        static readonly System.Reflection.FieldInfo PrepareTargetField = typeof(TennisActor).GetField("prepareTarget", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        static readonly System.Reflection.PropertyInfo GamePaceProperty = typeof(TennisGame).GetProperty("Pace", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        float StepRemainder => game && !game.ManualSimulation && StepRemainderField != null ? (float)StepRemainderField.GetValue(game) : 0;
        float SwingPace => actor && SwingPaceField != null ? Mathf.Max(.01f, (float)SwingPaceField.GetValue(actor)) : 1;
        float GamePace => game && GamePaceProperty != null ? Mathf.Max(.05f, (float)GamePaceProperty.GetValue(game)) : TennisGame.GameSpeed;
        /// Signed time to contact (game seconds) at this displayed frame: the last simulated step carried on by the time still in the step accumulator.
        float RenderTtc()
        {
            float ttc = actor.SignedTimeToContact, r = StepRemainder;
            if (r <= 0) return ttc;
            if (ttc > 0) return Mathf.Max(ttc - r * SwingPace, Mathf.Min(ttc, .0005f));   // contact itself is drawn on the step that makes it
            return ttc - r;
        }
        /// Real seconds to contact for a signed time to contact (game seconds): the approach runs at the swing's pace, everything at the game's pace.
        float RealToContact(float ttc) => ttc > 0 ? ttc / (SwingPace * GamePace) : ttc / GamePace;
        HeroTennisInertia inertia;
        public HeroTennisInertia Inertia => inertia;

        // ---- chat 4: contact re-timing. The approved strokes square the strings at a slow moment of the swing (the racket is fastest
        // 50-100 ms before or after the ball). Real swings (REFERENCES.md, real-time YAAUOoMbrfM 12.2-13.0: take-back held, forward swing
        // ~0.12 s, racket blurred = fastest at the ball, finish at the shoulder ~0.1 s later) are re-created on the clip's own poses:
        // the forward swing (from the end of the take-back = the slowest strings in the 0.45 s before the contact) is played by the strings'
        // path length over ForwardSwing seconds, accelerating evenly into the ball; the follow-through to the next slow point decelerates
        // evenly from that same speed; the take-back before it is stretched to fill the time the forward swing gave up. Only timing changes.
        /// HERO_CONTACT_RETIME=0: play the clip's own timing into the contact (before/after proof).
        public static bool ContactRetime = Environment.GetEnvironmentVariable("HERO_CONTACT_RETIME") != "0";
        public static float ForwardSwing = .14f;
        readonly float[][] pathS = new float[Count][];
        readonly float[] retimeBack = new float[Count], retimeFin = new float[Count], retimeL = new float[Count], retimeL2 = new float[Count],
                         retimeW = new float[Count], retimeWp = new float[Count], retimeA = new float[Count], retimeSc = new float[Count];
        void BuildRetime(int i)
        {
            var p = stringPath[i]; if (p == null || p.Length < 4) return;
            int n = p.Length; var S = new float[n];
            for (int k = 1; k < n; k++) S[k] = S[k - 1] + Vector3.Distance(p[k], p[k - 1]);
            float c = contact[i], from = stringPathFrom[i];
            int ci = Mathf.Clamp(Mathf.RoundToInt((c - from) * TableRate), 1, n - 2);
            float Speed(int k) => (S[Mathf.Clamp(k, 1, n - 1)] - S[Mathf.Clamp(k, 1, n - 1) - 1]) * TableRate;
            int k0 = Mathf.Max(1, ci - Mathf.RoundToInt(.45f * TableRate)), k1 = Mathf.Max(k0, ci - Mathf.RoundToInt(.06f * TableRate)), kb = k0;
            for (int k = k0; k <= k1; k++) if (Speed(k) < Speed(kb)) kb = k;
            int f0 = Mathf.Min(n - 1, ci + Mathf.RoundToInt(.08f * TableRate)), f1 = Mathf.Min(n - 1, ci + Mathf.RoundToInt(.5f * TableRate)), kf = f1;
            for (int k = f0; k <= f1; k++) if (Speed(k) < Speed(kf)) kf = k;
            float tBack = from + kb / TableRate, L = S[ci] - S[kb], L2 = S[kf] - S[ci];
            if (c - tBack < .05f || L < .05f || L2 < .02f) return;
            // the serve keeps its own trophy -> contact (REFERENCES.md serves); groundstrokes ~0.14 s (YAAUOoMbrfM 12.2-13.0)
            float w = i == (int)Clip.Serve ? c - tBack : Mathf.Min(ForwardSwing, c - tBack), uc = 2 * L / w;
            // the follow-through decelerates until the clip's own racket stays slower than half the contact speed (a fast finish wrap
            // later in the clip must not out-speed the hit); else to the slowest point found above
            for (int k = Mathf.Min(n - 1, ci + Mathf.RoundToInt(.1f * TableRate)); k < n; k++)
            {
                bool slow = true; for (int q = k; q < n; q++) if (Speed(q) > .5f * uc) { slow = false; break; }
                if (slow) { kf = k; break; }
            }
            L2 = S[kf] - S[ci];
            if (L2 < .02f) return;
            pathS[i] = S; retimeBack[i] = tBack; retimeFin[i] = from + kf / TableRate; retimeL[i] = L; retimeL2[i] = L2; retimeSc[i] = S[ci];
            retimeW[i] = w; retimeWp[i] = 2 * L2 / uc; retimeA[i] = Mathf.Max(from, tBack - .3f);
            if (i == (int)Clip.Serve) retimeA[i] = Mathf.Min(tBack, Mathf.Max(retimeA[i], serveTrophyTime));   // the serve ritual (stance, toss, trophy) keeps its own times
        }
        float PathTime(int i, float s)
        {
            var S = pathS[i]; int lo = 0, hi = S.Length - 1;
            while (hi - lo > 1) { int m = (lo + hi) / 2; if (S[m] < s) lo = m; else hi = m; }
            float seg = S[hi] - S[lo], u = seg > 1e-6f ? Mathf.Clamp01((s - S[lo]) / seg) : 0;
            return stringPathFrom[i] + (lo + u) / TableRate;
        }
        /// Clip time `v` on the gameplay schedule (the clip's own contact at the gameplay contact) -> the re-timed clip time (same poses).
        float Retime(int i, float v)
        {
            if (!ContactRetime || pathS[i] == null) return v;
            float c = contact[i], b = retimeBack[i], e = retimeFin[i], w = retimeW[i], wp = retimeWp[i], a = retimeA[i];
            if (v <= a) return v;
            if (v < c - w) return a + (v - a) * (b - a) / Mathf.Max(1e-4f, c - w - a);                   // take-back, stretched
            if (v < c) { float x = (v - (c - w)) / w; return PathTime(i, retimeSc[i] - retimeL[i] * (1 - x * x)); }   // forward swing, even acceleration
            if (v < c + wp) { float y = (v - c) / wp; return PathTime(i, retimeSc[i] + retimeL2[i] * (2 * y - y * y)); } // follow-through, even deceleration
            return e + (v - c - wp);
        }
        Transform[] feet = new Transform[4]; float heelRest, toeRest; Transform hips;
        Vector3 torsoFwdHips, torsoFwdChest; readonly Vector3[] handAxis = new Vector3[2];
        void BuildContactModel()
        {
            var a = Anim; var grip = Grip;
            Transform Mk(string n, Vector3 p) { var t = new GameObject(n).transform; t.SetParent(grip, false); t.localPosition = p; return t; }
            // racket-local metres (the grip socket compensates bone scale); head centre at y=.395 on the sculpt.
            // The racket is drawn TennisRules.HeroRacketScale bigger about the grip (a tennis racket, not a
            // badminton one next to the big chibi head); the contact markers move with it, so the visible
            // head, the swing's aim point and the rules' string bed are the same thing.
            // (racketGrip IS the racket mesh, pivot at the grip: scaling it scales the markers below with it)
            // Match heroes: the string bed of the classic racket, measured on its own mesh (MatchHeroLook, written by MatchHeroBuild):
            // centre, and the frame (right across the face, up along the shaft, normal to the strings) in racket-local metres.
            Vector3 centre = matchLook.stringCentreLocal, right = matchLook.stringRightLocal, up = matchLook.stringUpLocal, normal = matchLook.stringNormalLocal;
            if (!racketScaled) { grip.localScale *= TennisRules.HeroRacketScale; racketScaled = true; }
            stringCentre = Mk("Hero strings centre", centre);
            stringRight = Mk("Hero strings right", centre + right * .1f);
            stringUp = Mk("Hero strings up", centre + up * .1f);
            stringNormal = Mk("Hero strings normal", centre + normal * .1f);
            hips = Bone(HumanBodyBones.Hips);
            feet[0] = Bone(HumanBodyBones.LeftFoot); feet[1] = Bone(HumanBodyBones.LeftToes);
            feet[2] = Bone(HumanBodyBones.RightFoot); feet[3] = Bone(HumanBodyBones.RightToes);
            // The match rigs are skinned in an A-pose-like bind with their ReadyIdle as the planted stance: measure the planted
            // ankle / toe-joint heights on ReadyIdle (flat feet on the floor), not on the unevaluated rig.
            if (valid[(int)Clip.Ready])
            {
                for (int k = 0; k < Count; k++) if (valid[k]) { mixer.SetInputWeight(k, k == (int)Clip.Ready ? 1 : 0); playables[k].SetTime(0); }
                graph.Evaluate(0);
            }
            // bind pose (not yet evaluated): ankle / toe-joint heights above the soles
            heelRest = transform.InverseTransformPoint(feet[0].position).y; toeRest = transform.InverseTransformPoint(feet[1].position).y;
            if (Environment.GetEnvironmentVariable("HERO_DEBUG") == "1") Debug.Log($"[HeroDbg] {name} heelRest={heelRest:F3} toeRest={toeRest:F3}");
            BuildSoles();
            spineB = Bone(HumanBodyBones.Spine); chestB = Bone(HumanBodyBones.Chest);
            for (int h = 0; h < 2; h++) { var hb = Bone(h == 0 ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand); Transform mid = null; foreach (var t in hb.GetComponentsInChildren<Transform>()) if (t.name == (h == 0 ? "Middle1.L" : "Middle1.R") || t.name == (h == 0 ? "LeftMiddleProximal" : "RightMiddleProximal")) { mid = t; break; }
                handAxis[h] = Quaternion.Inverse(hb.rotation) * ((mid ? mid.position : hb.position + hb.up * .07f) - hb.position); }
            var chest = Bone(HumanBodyBones.Chest);
            torsoFwdHips = Quaternion.Inverse(hips.rotation) * transform.forward; torsoFwdChest = Quaternion.Inverse(chest.rotation) * transform.forward;
            // Where the strings are at each stroke's authored contact frame, in hero space (every stroke clip the hero has).
            for (int i = 0; i < Count; i++)
            {
                if (!strokeClip[i] || !valid[i]) continue;
                for (int k = 0; k < Count; k++) if (valid[k]) { mixer.SetInputWeight(k, k == i ? 1 : 0); playables[k].SetTime(k == i ? contact[i] : 0); }
                graph.Evaluate(0);
                contactLocal[i] = transform.InverseTransformPoint(stringCentre.position); hasContact[i] = true;
                // Match heroes: the clip's own string path around the contact (hero space, 60 Hz), so the contact assist can aim the
                // racket's path at the ball instead of pinning the strings on it (StringPathOffset).
                {
                    float from = Mathf.Max(0, contact[i] - PathBefore), to = Mathf.Min(length[i], contact[i] + PathAfter);
                    int n = Mathf.Max(2, Mathf.CeilToInt((to - from) * TableRate) + 1); var path = new Vector3[n];
                    for (int f = 0; f < n; f++)
                    {
                        playables[i].SetTime(Mathf.Min(to, from + f / TableRate)); graph.Evaluate(0);
                        path[f] = transform.InverseTransformPoint(stringCentre.position);
                    }
                    stringPath[i] = path; stringPathFrom[i] = from;
                    BuildRetime(i);
                }
            }
            BuildServeRitualPoints();
            for (int k = 0; k < Count; k++) if (valid[k]) mixer.SetInputWeight(k, k == (int)Clip.Ready ? 1 : 0);
            for (int k = 0; k < Count; k++) if (valid[k]) playables[k].SetTime(0);
            graph.Evaluate(0);
        }

        /// Match heroes: the serve ritual's ball points (hold, release, extended) in hero space, read off the tossing hand of the Serve
        /// clip at its own stance / release / trophy times, so the bounced and tossed ball sits in the hand the player sees.
        Vector3[] tossPoints; Vector3 carryPoint;
        void BuildServeRitualPoints()
        {
            tossPoints = null; int s = (int)Clip.Serve; if (!valid[s]) return;
            var a = Anim; var hand = Bone(HumanBodyBones.LeftHand); var mid = Bone(HumanBodyBones.LeftMiddleProximal);
            var pts = new Vector3[3]; var times = new[] { serveStanceTime, serveReleaseTime, serveTrophyTime };
            for (int p = 0; p < 3; p++)
            {
                for (int k = 0; k < Count; k++) if (valid[k]) { mixer.SetInputWeight(k, k == s ? 1 : 0); playables[k].SetTime(k == s ? Mathf.Clamp(times[p], 0, length[s]) : 0); }
                graph.Evaluate(0);
                // the palm centre: a bit past the wrist along the hand, the ball sits on it (held at the throat, then lifted and released)
                var palm = mid ? Vector3.Lerp(hand.position, mid.position, .7f) : hand.position;
                pts[p] = transform.InverseTransformPoint(palm);
            }
            // the ball sits under the palm while it is bounced and on top of it once lifted and released (TossArm's goal is +-4.5 cm of the ball)
            pts[0].y -= .045f; pts[1].y += .045f; pts[2].y += .045f;
            tossPoints = pts; carryPoint = pts[0];
        }

        // ---- Plan 3A kinetic chain: hips-, chest- and arm-segment orientations per stroke clip, sampled at 60 Hz
        const float TableRate = 60;
        Transform spineB, chestB;
        Vector3? VisualContact(TennisActor.Stroke kind, bool backhand)
        {
            if (kind == TennisActor.Stroke.Missed || kind == TennisActor.Stroke.Celebrate) return null;
            var c = ClipFor(kind, backhand, kind == TennisActor.Stroke.Smash || kind == TennisActor.Stroke.Serve);
            return hasContact[(int)c] ? actor.transform.TransformPoint(contactLocal[(int)c]) : (Vector3?)null;
        }
        /// The game poses the actor on its precise contact sub-steps: pose the hero racket for the
        /// same instant so string-crossing tests and launch points see the racket on screen.
        void OnActorPosed()
        {
            if (!graph.IsValid() || (game && game.ReplayPlaying) || !actor.Swinging) return;
            // A compensated stroke can reach contact in the simulation before LateUpdate
            // runs. Install its upper-body pose now; the previous Ready/prepare pose must
            // never decide whether that first contact sub-step hits the ball.
            if (isPlayer && (!wasSwinging || !actionActive || !IsStroke(action)))
            {
                swingClip = Playable(StrokeClip()); BeginSwingTime(swingClip,actor.SignedTimeToContact);
                action = swingClip; actionActive = true;
                juiceActive = false; followThrough = true; wasSwinging = true;
                actionWeight = 1; actionWeightVel = 0;
                upperFade = 1; upperFadeClip = (int)action;
                for (int k = 0; k < Count; k++)
                {
                    if (!upperPlayables[k].IsValid()) continue;
                    upperBlend[k] = k == (int)action ? 1 : 0;
                    upperMixer.SetInputWeight(k, upperBlend[k]);
                }
                layers.SetInputWeight(1, 1); UpperLayerWeight = 1;
            }
            if (!actionActive || !IsStroke(action)) return;
            int i = (int)action;
            playables[i].SetTime(StrokeTime(i, actor.SignedTimeToContact));
            if (upperPlayables[i].IsValid()) upperPlayables[i].SetTime(StrokeTime(i, actor.SignedTimeToContact));
            SetUpperMask(false);
            graph.Evaluate(0);
            inertia?.ApplyHeld(++posesSinceFrame / 120f);   // TennisGame steps 1/120 s per pose
            // Exact sub-step contact keeps the same guide/string solve. Its caches
            // must not become the next displayed frame's abrupt body position.
            // LateUpdate evaluates the graph again before its smooth correction.
            var visualLunge=lungeOffset;float visualCrouch=contactCrouch,visualVelocity=contactCrouchVelocity;
            int visualCrouchFrame=contactCrouchFrame,visualLungeFrame=contactLungeFrame;
            float lastRenderedCrouch=LastCrouch,lastRenderedDesired=LastDesiredCrouch;
            var renderedGuide=LastGuideGoal;float renderedAssist=LastAssistWeight;
            PostProcess(true,true);
            LastPhysicsCrouch=contactCrouch;LastPhysicsLunge=lungeOffset;
            LastPhysicsStrings=stringCentre.position;LastPhysicsTtc=actor.SignedTimeToContact;
            lungeOffset=visualLunge;contactCrouch=visualCrouch;contactCrouchVelocity=visualVelocity;
            contactCrouchFrame=visualCrouchFrame;contactLungeFrame=visualLungeFrame;
            LastCrouch=lastRenderedCrouch;LastDesiredCrouch=lastRenderedDesired;
            LastGuideGoal=renderedGuide;LastAssistWeight=renderedAssist;
            // Restoring state deliberately leaves the evaluated skeleton/socket
            // transforms intact for the game's current string-crossing test.
            PhysicsPoseRestoreError=Vector3.Distance(LastPhysicsStrings,stringCentre.position);
        }
        /// Short authored point gestures give way to the next serve. Equipped game-end
        /// taunts and the distinct match result performances have their own entry paths.
        public static bool PointEmotes = true;
        public int PointReactionsSuppressed { get; private set; }
        public int PointEmotesPlayed { get; private set; }
        /// Point / match reactions the hero has no clip for (it stays on ReadyIdle): count and the last one asked for.
        public int MissingReactions { get; private set; }
        public string LastMissingReaction { get; private set; }
        public string LastEmote { get; private set; }
        int emoteRoll;
        void OnReacted(bool won, TennisActor.Moment moment)
        {
            // The equipped game-end taunt has priority over a short point gesture.
            // A match-ending point instead plays the distinct MatchWin / MatchLose.
            if (GameEndedTaunt(won, moment != TennisActor.Moment.Match)) return;
            // Celebrations are selected from the equipped controller slots.
            if (!PointEmotes) { PointReactionsSuppressed++; return; }
            // A miss already queued its own recover while the racket finishes the stroke.
            // Keep that performance instead of replacing it with a second loss gesture.
            if (!won && moment != TennisActor.Moment.Match &&
                ((hasQueued && queued == Clip.MissWhiff) || (juiceActive && juice == Clip.MissWhiff)))
            { PointEmotesPlayed++; LastEmote = Clip.MissWhiff.ToString(); return; }
            emoteRoll++;
            var c = moment == TennisActor.Moment.Match ? (won ? Clip.MatchWin : Clip.MatchLose)
                : won ? (emoteRoll % 2 == 0 ? Clip.CelebratePoint : Clip.HitPerfect) : (emoteRoll % 2 == 0 || !valid[(int)Clip.EmoteStomp] ? Clip.SadPointLost : Clip.EmoteStomp);
            // Generic reaction assets are authored on this body's own 53-bone rig.
            if (!valid[(int)c]) { MissingReactions++; LastMissingReaction = c.ToString(); return; }
            PointEmotesPlayed++; LastEmote = c.ToString();
            // Let a whiff finish its overswing before the point reaction.
            if ((actionActive && IsStroke(action)) || (juiceActive && juice == Clip.MissWhiff))
            { queued = c; hasQueued = true; }
            else PlayJuice(c);
        }
        Clip queued; bool hasQueued;
        void OnContact(Vector2 face, Timing grade, bool super)
        {
            // Score80 B: heavy contact = the body takes the hit after the hit-stop (chest recoil + root squash);
            // Great gets a light one; routine hits stay clean.
            bool ult = isPlayer && game && game.UltimateArmed && game.PlayerUltimate >= 1;   // this contact spends the ultimate
            bool heavy = super || grade >= Timing.Perfect || actor.Kind == TennisActor.Stroke.Smash || ult;
            Trail(grade >= Timing.Perfect || super ? .32f : .2f, grade >= Timing.Perfect || super ? new Color(1, .9f, .45f, .9f) : new Color(1, 1, 1, .6f)); }
        void OnRivalStruck() => Trail(.2f, new Color(1, 1, 1, .5f));
        // ---- racket trail: lit only AFTER a confirmed contact (the follow-through) or a called whiff
        TrailRenderer trail; float trailFor;
        void BuildTrail()
        {
            if (!stringCentre) return;
            trail = stringCentre.gameObject.AddComponent<TrailRenderer>();
            trail.time = .16f; trail.startWidth = .22f; trail.endWidth = 0; trail.minVertexDistance = .03f; trail.emitting = false;
            var glow = Resources.Load<Shader>("Tennis/Shaders/TennisFxAdditive");
            trail.sharedMaterial = new Material(glow ? glow : Shader.Find("Sprites/Default")) { name = "Hero racket trail", mainTexture = TennisLook.Falloff };
            trail.textureMode = LineTextureMode.Stretch; trail.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; trail.receiveShadows = false;
        }
        void Trail(float seconds, Color c)
        {
            if (!trail) return; trailFor = seconds; trail.Clear(); trail.emitting = true;
            trail.startColor = c; trail.endColor = new Color(c.r, c.g, c.b, 0);
        }
        void OnWhiff() { if (actionActive) { queued = Clip.MissWhiff; hasQueued = valid[(int)Clip.MissWhiff]; }
            else { if (valid[(int)Clip.MissWhiff]) actionActive = false; PlayJuice(Clip.MissWhiff); }
            Trail(.4f, new Color(.75f, .88f, 1f, .75f)); }
        // ---- EMOTES: in-place full-body clips (Emote_Scuba / Emote_Thrust / Emote_Spike taunts, Intro_Wave / Intro_BringIt / Intro_Pushups intros) played on the juice path:
        // they ease in from READY, run once, and give way to the next serve / swing / run. Match heroes only; nothing else in the driver changes for the clips that exist already.
        public static readonly Clip[] Taunts = { Clip.EmoteScuba, Clip.EmoteThrust, Clip.EmoteSpike };
        public static readonly Clip[] Intros = { Clip.IntroWave, Clip.IntroBringIt, Clip.IntroPushups };
        public static bool IsEmote(Clip c) => c >= Clip.EmoteScuba && c <= Clip.EmoteDefeat;
        /// EMOTE STANDARD: the emotion set (also the match's own point / match reactions, see ResolvePerformanceClips).
        public static readonly Clip[] Standard = { Clip.EmoteJumpJoy, Clip.EmoteFistPump, Clip.EmoteStomp, Clip.EmoteSlump, Clip.EmoteShock, Clip.EmoteVictory, Clip.EmoteDefeat };
        /// The taunt the player picked (-1 = rotate through the three); set by whatever UI offers the pick.
        public static int PickedTaunt = -1;
        /// The taunts and intros this driver has played (proof / tests).
        public int EmotesPlayed { get; private set; }
        public string LastEmotePlayed { get; private set; }
        int tauntRoll, lastGameKey = 0;
        public bool EmoteActive => juiceActive && IsEmote(juice);
        public bool HasEmote(Clip c) => IsEmote(c) && valid[(int)c];
        public float EmoteDuration(Clip c) => HasEmote(c) ? TennisEmotes.PlaybackDuration(c, length[(int)c]) : 0;
        float JuiceRate(Clip c) => length[(int)c] / Mathf.Max(.1f, TennisEmotes.PlaybackDuration(c, length[(int)c]));
        HeroPoseSafety poseSafety;
        Clip fadingPose = Clip.Ready;
        bool BetweenPointsGone() { if (actor && (actor.PrepareAmount > .02f || actor.PrepareServe)) { hasPendingEmote = false; return true; } return false; }
        /// Play one emote clip now. False when this hero has no such clip or is in a stroke.
        public bool PlayEmote(Clip c)
        {
            if (!IsEmote(c) || !valid[(int)c]) return false;
            if (actionActive || (actor && actor.Swinging)) return false;
            juice = c; juiceActive = true; juiceTime = 0; hasQueued = false;
            EmotesPlayed++; LastEmotePlayed = c.ToString(); LastEmote = c.ToString();
            if (game && (Array.IndexOf(Taunts, c) >= 0 || Array.IndexOf(Standard, c) >= 0)) game.HoldNextPoint((EmoteDuration(c) + .4f) * TennisGame.GameSpeed);      // the next serve waits for the taunt / emote (the game's timers run at GameSpeed x real time)
            return true;
        }
        /// The player picks a taunt ("Scuba", "Thrust", "Spike" or 0..2) or lets the game rotate them.
        Clip NextTaunt(int index = -1) { if (index < 0) index = PickedTaunt >= 0 ? PickedTaunt : tauntRoll++ % Taunts.Length; return Taunts[Mathf.Abs(index) % Taunts.Length]; }
        public bool PlayTaunt(int index = -1) => PlayEmote(NextTaunt(index));
        /// A follow-through is still playing when the game ends: the emote waits for it (and for the next swing not to start).
        Clip pendingEmote; bool hasPendingEmote;
        public bool PlayTaunt(string name)
        {
            for (int i = 0; i < Taunts.Length; i++) if (Taunts[i].ToString().EndsWith(name, StringComparison.OrdinalIgnoreCase)) return PlayTaunt(i);
            return false;
        }
        /// The intro emote (the match presentation asks for it): the hero's own pick, else one chosen by its name (the same hero always greets the same way).
        public int IntroPick = -1;
        /// The clip PlayIntroEmote plays.
        public Clip IntroClip { get { int i = IntroPick >= 0 ? IntroPick : (isPlayer ? 0 : (int)((uint)name.GetHashCode() % (uint)Intros.Length)); return Intros[Mathf.Abs(i) % Intros.Length]; } }
        public bool PlayIntroEmote() => PlayEmote(IntroClip);
        bool GameEndedTaunt(bool won, bool allowTaunt = true)
        {
            // a taunt only after a GAME (the match's game / set counters moved), never after an ordinary point
            if (!game) return false;
            var m = game.Match;
            int key = m.PlayerGames + m.OpponentGames + 100 * (m.PlayerSets + m.OpponentSets);
            if (key < lastGameKey) { lastGameKey = key; return false; }          // a new match started with a fresh score
            if (key == lastGameKey) return false;
            lastGameKey = key;
            if (!won || !allowTaunt) return false;
            var c = NextTaunt();
            if (!PlayEmote(c)) { pendingEmote = c; hasPendingEmote = true; hasQueued = false; }
            return true;
        }

        bool chosenEmoteAtServe;
        public int TransitionsBlended { get; private set; }
        public void ResetForPoint(bool preserveChosenEmote = false, Clip? pending = null)
        {
            inertia?.Request(.15f);
            hasQueued = hasPendingEmote = false;
            actionActive = followThrough = wasSwinging = false;
            if (preserveChosenEmote && pending.HasValue) PlayEmote(pending.Value);
            chosenEmoteAtServe = preserveChosenEmote && juiceActive && IsEmote(juice);
            if (!chosenEmoteAtServe) juiceActive = false;
        }

        public void PlayJuice(Clip c) { if (!valid[(int)c] || (c == Clip.HitPerfect && !BetweenPoints())) return; juice = c; juiceActive = true; juiceTime = FluidOff || c == Clip.MissWhiff || c == Clip.HitPerfect ? 0 : -.14; }   // point emotes: a short beat to settle, then the eased lead-in

        static bool IsStroke(Clip c) => strokeClip[(int)c];

        /// The clip a stroke plays, chosen only from state the game already owns (HERO_MAINSTAY: no new wide / short classifier):
        ///   serve -> Serve, smash -> Overhead (Smash), volley -> VolleyForehand (Volley) / VolleyBackhand,
        ///   the actor's own out-of-reach stroke (Stroke.Running: TennisRules.StrokeFor, ball more than 1.1 m wide) -> ForehandWide / BackhandWide,
        ///   the first ball after a serve (TennisGame.RallyShots == 1) on the backhand wing -> Return, anything else -> Forehand / Backhand.
        /// The Return clip is a two-hand backhand-side return (WATCH section 13), so a forehand-side return plays the neutral Forehand.
        /// Low pickups and slides use the short/wide reach clips; a backhand slice uses SliceApproach.
        /// The clip a stroke plays (the match heroes' map: the actor's own wide marker Stroke.Running -> the Wide clips, a returned serve -> Return, volleys, overhead).
        public Clip ClipFor(TennisActor.Stroke kind, bool backhand, bool overhead)
        {
            switch (kind)
            {
                case TennisActor.Stroke.Serve: return Clip.Serve;
                case TennisActor.Stroke.Smash: return Clip.Smash;
                case TennisActor.Stroke.Volley: return backhand ? Clip.VolleyBackhand : Clip.Volley;
                case TennisActor.Stroke.Running:
                case TennisActor.Stroke.Dive: return backhand ? Clip.BackhandWide : Clip.ForehandWide;   // Dive: only an older online peer still sends it
                case TennisActor.Stroke.LowPickup: return backhand ? Clip.BackhandWide : Clip.ForehandShort;
                case TennisActor.Stroke.Slice: return backhand ? Clip.SliceApproach : Clip.ForehandShort;
                default:
                    if (overhead) return Clip.Smash;
                    if (backhand) return IsReturnOfServe() ? Clip.Return : Clip.Backhand;
                    return Clip.Forehand;
            }
        }
        /// The ball in flight is a serve: TennisGame.RallyShots is 1 from the serve until the receiver strikes it.
        bool IsReturnOfServe() => game && game.Flow == TennisGame.Phase.Rally && game.RallyShots == 1;
        /// The swing's clip is decided once, when the swing starts (RallyShots moves on at the strike, mid-swing).
        Clip swingClip = Clip.Forehand;
        Clip StrokeClip() => ClipFor(actor.Kind, actor.Backhand, actor.Overhead);
        /// A clip the hero has: the stroke's own, else the neutral wing's (so a hero missing a clip still swings, never silently).
        Clip Playable(Clip c)
        {
            if (valid[(int)c]) return c;
            switch (c)
            {
                case Clip.Return: case Clip.BackhandWide: case Clip.VolleyBackhand: case Clip.SliceApproach: return valid[(int)Clip.Backhand] ? Clip.Backhand : c;
                case Clip.ForehandWide: case Clip.ForehandShort: case Clip.ForehandOpen: case Clip.Volley: return valid[(int)Clip.Forehand] ? Clip.Forehand : c;
                default: return c;
            }
        }

        int displayContactFrame = -1;
        double displayContactTime;
        public void HoldContactFrame()
        {
            if (!actor || !actionActive || !IsStroke(action)) return;
            displayContactFrame = Time.frameCount;
            displayContactTime = StrokeTime((int)action, 0);   // chat 4: the contact frame shows the contact pose itself (the ball is drawn on the strings)
            displayContactVirtual = contact[(int)action];
        }
        double displayContactVirtual;

        int posesSinceFrame;
        HeroTossHold tossHold;
        void LateUpdate()
        {
            posesSinceFrame = 0;
            if (!graph.IsValid() || !actor || (game && game.ReplayPlaying)) return;
            if (!tossHold) { tossHold = GetComponent<HeroTossHold>(); if (!tossHold) tossHold = gameObject.AddComponent<HeroTossHold>(); tossHold.driver = this; }   // the ball in the tossing hand (runs after the finger polish)
            float dt = Time.deltaTime;
            // A chosen between-point emote may finish while the own-serve meter is ready.
            // TOSS/movement or receiving gives the body straight back to gameplay.
            if (chosenEmoteAtServe && (!game || !game.ServeReady || Mathf.Abs(game.LateralSpeed) > .2f)) {
                chosenEmoteAtServe = false; juiceActive = false;
            }
            // ---- action layer: prepare / swing / follow-through, contact-locked to gameplay
            bool hadAction = actionActive, hadJuice = juiceActive; Clip hadActionClip = action, hadJuiceClip = juice; double hadActionTime = actionVirtual;
            bool swinging = actor.Swinging;
            // The phone already spends time detecting a stroke and the TV transporting
            // it. Layer fades must not add another 80–150 ms to the player's response.
            // Keep locomotion/leg and emote transitions; apply the stroke arms now.
            bool responsiveStroke = isPlayer && swinging;
            if (swinging)
            {
                if (!wasSwinging) swingClip = Playable(StrokeClip());
                var c = swingClip; int i = (int)c;
                float ttc = RenderTtc();
                if (!wasSwinging || !actionActive || action != c) { BeginSwingTime(c,ttc); lead = Mathf.Lerp(lead, Mathf.Clamp(ttc, .15f, .9f), .5f); action = c; actionActive = true; juiceActive = false; }
                actionTime = displayContactFrame == Time.frameCount ? displayContactTime : StrokeTime(i, ttc);
                actionVirtual = displayContactFrame == Time.frameCount ? displayContactVirtual : MatchAuthoredTime(i, ttc);
                followThrough = true;
                State = c + (ttc > 0 ? " swing" : " follow");
            }
            else if (actionActive && followThrough && IsStroke(action))
            {
                actionVirtual += dt; actionTime = Retime((int)action, (float)actionVirtual);   // chat 4: the follow-through keeps its re-timed deceleration
                if (actionTime >= length[(int)action] - .05f || (actor.PrepareAmount > .05f && !BetweenPoints()) || Moving() > .6f || (BetweenPoints() && juiceActive)) actionActive = false;
                // Contact rewards stay in FX/audio; full-body celebrations belong between points.
                State = action + " finish";
            }
            else if (!chosenEmoteAtServe && (actor.PrepareAmount > .02f || (actor.PrepareServe && !WalkingIn())) && !BetweenPoints() && !(juiceActive && juice == Clip.MissWhiff))
            {
                var c = actor.PrepareServe ? Clip.Serve : actor.PrepareOverhead && valid[(int)Clip.Smash] ? Clip.Smash : Playable(ClipFor(TennisActor.Stroke.Drive, actor.PrepareBackhand, false)); int i = (int)c;
                action = c; actionActive = true; juiceActive = false; followThrough = false;
                if (c == Clip.Serve)
                {
                    // The server owns the whole body from stepping up to the line: the serve clip's own
                    // side-on pre-serve stance (with a slow weight sway) while the ball is bounced, its
                    // tossing-arm rise through the wind-up, then the trophy as the toss goes up.
                    float p = actor.PrepareAmount;
                    actionTime = p <= .001f ? ServeStanceT + .05f * Mathf.Sin(Time.time * 1.7f)
                        : p < .4f ? Mathf.Lerp(ServeStanceT, ServeReleaseT, p / .4f) : Mathf.Lerp(ServeReleaseT, ServeTrophyT, (p - .4f) / .6f);
                    // chat 4: the rival's serve is scripted (TennisGame OpponentServe: prepare = toss age / RivalTossToContact, swing starts at
                    // RivalSwingStart of it, contact at its end), so its swing can begin on that schedule and reach the contact at the clip's own
                    // pace instead of crushing trophy -> contact into the last 0.18 s (it played at 1.9x).
                    if (!isPlayer && game && game.Flow == TennisGame.Phase.OpponentServe && p > .4f)
                    {
                        float toss = PrepareTargetField != null ? (float)PrepareTargetField.GetValue(actor) : p;   // the toss itself (the actor's prepare amount lags it)
                        float remaining = RivalTossToContact * (1 - toss) / GamePace;
                        actionTime = Mathf.Max((float)actionTime, contact[i] - remaining);
                    }
                }
                else if (c == Clip.Smash) actionTime = actor.PrepareAmount * Mathf.Min(overheadTrophyTime, contact[i]);
                else actionTime = actor.PrepareAmount * Mathf.Max(0, contact[i] - (pathS[i] != null && ContactRetime ? retimeW[i] : lead));   // chat 4: prepared = the take-back fully loaded (racket back, waiting); the swing is the forward swing
                State = c + " prepare " + actor.PrepareAmount.ToString("0.00");
                actionVirtual = actionTime;
                actionTime = Retime(i, (float)actionVirtual);   // the take-back is shown on the same re-timed schedule the swing continues
            }
            else actionActive = false;
            wasSwinging = swinging;
            if (hasQueued && !actionActive && !swinging && !juiceActive) { hasQueued = false; PlayJuice(queued); }
            if (hasPendingEmote && !actionActive && !swinging && !BetweenPointsGone()) { hasPendingEmote = false; PlayEmote(pendingEmote); }
            // Mid-rally flourishes give way to real play: moving or preparing cancels them.
            if (juiceActive && juice == Clip.HitPerfect && !BetweenPoints()) juiceActive = false;
            if (juiceActive) { juiceTime += dt * JuiceRate(juice) * 1; if (juiceTime >= length[(int)juice]) { juiceActive = false; if (hasQueued) { hasQueued = false; PlayJuice(queued); } } else State = juice.ToString(); }
            if (!juiceActive) chosenEmoteAtServe = false;
            if (!actionActive && !juiceActive) State = Moving() > .15f ? "Run" : "Ready";
            // chat 4: whatever changed what is played this frame blends in from the pose on screen (HeroTennisInertia)
            if (inertia != null)
            {
                bool switched = hadAction != actionActive || hadJuice != juiceActive || (actionActive && hadAction && hadActionClip != action) || (juiceActive && hadJuice && hadJuiceClip != juice);
                bool jumped = actionActive && hadAction && hadActionClip == action && Math.Abs(actionVirtual - hadActionTime) > .12 + 3 * dt;
                if (switched || jumped) { inertia.Request(.12f); TransitionsBlended++; }
            }

            // ---- base layer: ready / idle / runs by ground velocity
            var target = targetBuf; Array.Clear(target, 0, Count);
            float move = Moving();
            Vector2 v = new Vector2(actor.Speed, actor.ForwardSpeed);
            float runW = Mathf.Clamp01((move - .15f) / .9f);
            var baseIdle = BetweenPoints() && valid[(int)Clip.Idle] ? Clip.Idle : Clip.Ready;
            target[(int)baseIdle] = 1 - runW;
            bool walkMode = WalkMode();
            if (runW > 0 && walkMode) target[(int)Clip.Walk] += runW;
            else if (runW > 0)
            {
                // SERVE_AND_FEET: the planted foot of a blend of two run clips moves at the blended direction only when both play the same way round (work/serve-and-feet/data/run_blend_model_*.json):
                // toward the net, RunForward + RunRight / RunLeft, the blend weight is the travel angle / 90; away from the net, the forward run played backwards + the OPPOSITE sideways run played
                // backwards (back to the right = RunLeft reversed, back to the left = RunRight reversed), the weight is (180 - angle) / 90. The family only changes past 100 / back before 80 degrees.
                float phi = Mathf.Atan2(v.x, v.y) * Mathf.Rad2Deg, a = Mathf.Abs(phi);
                bool wasBack = runBack;
                if (runBack) { if (a < 80f) runBack = false; } else if (a > 100f) runBack = true;
                if (runBack != wasBack) { inertia?.Request(.15f); TransitionsBlended++; }   // chat 4: the family flip re-maps every run clip's time at once
                float wl = Mathf.Clamp01((runBack ? 180f - a : a) / 90f);
                target[(int)Clip.RunForward] += runW * (1 - wl);
                target[(int)((phi >= 0) != runBack ? Clip.RunRight : Clip.RunLeft)] += runW * wl;
            }
            // An absent locomotion asset contributes its share to the idle pose rather
            // than leaving the previous action frozen while the actor moves.
            {
                float lost = 0;
                for (int k = 0; k < Count; k++) if (!valid[k] && target[k] > 0) { lost += target[k]; target[k] = 0; }
                target[(int)baseIdle] += lost;
            }
            // ---- overlay action or juice on top of the base
            if (actionActive || juiceActive) fadingPose = actionActive ? action : juice;
            float want = actionActive || juiceActive ? 1 : 0;
            // emotes ease in (lead-in) instead of popping; strokes stay snappy
            float rise = juiceActive && !actionActive ? .26f : .08f;
            if (responsiveStroke) { actionWeight = 1; actionWeightVel = 0; }
            else if (FluidOff || (want > 0 && actionActive)) actionWeight = Mathf.MoveTowards(actionWeight, want, dt / (want > 0 ? rise : .2f));
            // Score80 A: ease-in/ease-out (not a linear ramp) out of a follow-through and into / out of emotes.
            else { actionWeight = Mathf.SmoothDamp(actionWeight, want, ref actionWeightVel, want > 0 ? rise * .55f : .1f, Mathf.Infinity, dt); if (Mathf.Abs(actionWeight - want) < .002f) actionWeight = want; }
            // Legs: a stroke taken on the move keeps the run legs (planted cycle) and swings only the upper body;
            // standing, the stroke's own footwork plants. Legs blend slower than arms so nothing snaps.
            // Score80 A: the leg source follows the ground speed quickly (0.5 -> 1.8 m/s over 0.14 s) so a
            // follow-through while the body already runs back to the middle is carried by running legs, and a
            // swing into a stop gets the stroke's own planted footwork (no skate either way).
            // The tracked overhead meets a standing smash contact. Finish blending
            // out of running legs before impact, including the smash's hip/torso
            // contribution; an upper-body-only smash leaves the racket short.
            bool plantingOverhead = action == Clip.Smash && actor.Guiding && Mathf.Abs(actor.SignedTimeToContact) < .18f;
            bool strokeLegs = actionActive && IsStroke(action) && action != Clip.Serve && !plantingOverhead && !FluidOff;
            legsFromRun = Mathf.MoveTowards(legsFromRun, strokeLegs ? Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.5f, 1.8f, move)) : 0, dt / .14f);
            actionLegs = FluidOff ? actionWeight : Mathf.MoveTowards(actionLegs, want, dt / (want > 0 ? .16f : .2f));
            bool movingReaction=juiceActive&&!actionActive&&(IsReaction(juice)||IsEmote(juice));   // chat 4: emotes too (a Stomp / Shock on a hero walking back slid 2.7 m)
            reactionLegShare=Mathf.MoveTowards(reactionLegShare,movingReaction?Mathf.SmoothStep(0,1,Mathf.InverseLerp(.15f,.7f,move)):0,dt/.10f);
            float fullAction = FluidOff ? actionWeight : Mathf.Min(actionWeight, actionLegs) * (1 - legsFromRun);
            if(movingReaction)fullAction*=1-reactionLegShare;
            if (fullAction > 0)
            {
                for (int k = 0; k < Count; k++) target[k] *= 1 - fullAction;
                // Retain the outgoing clip throughout the fade, including point resets.
                // Dropping it here used to replace the entire body with Ready in one frame.
                target[(int)fadingPose] += fullAction;
            }
            float upperW = FluidOff || !actionActive || !IsStroke(action) ? 0 : actionWeight * Mathf.Max(legsFromRun, 1 - Mathf.Min(1, actionLegs / Mathf.Max(.01f, actionWeight)));
            if (responsiveStroke && !FluidOff) upperW = 1;
            {
                // A short reaction rides real walk/run legs during repositioning;
                // its approved full-body performance returns once planted.
                if(movingReaction&&reactionLegShare>.001f)
                {upperW=actionWeight*reactionLegShare;upperFade=upperW;upperFadeClip=(int)juice;}
                else
                // the stroke that just ended keeps its upper-body clip (frozen at its last time) while the layer eases out
                if (actionActive && IsStroke(action)) { upperFade = upperW; upperFadeClip = (int)action; }
                else { upperFade = Mathf.MoveTowards(upperFade, 0, dt / MatchUpperOut); upperW = upperFade; }
            }
            // ---- advance clip times and blend
            // SERVE_AND_FEET: the game runs at its own pace (0.75 on the serve walk-in, 1.2 in a rally) while actor.Speed is in game seconds, so the hero
            // really covers Speed * pace metres per second: the walk / run clips follow that ground speed, or the planted foot slides.
            float rateMove = move * GroundPace(move, dt);
            // the three run clips share one phase (identical foot timing); the planted foot of a coherent blend moves at 0.98 of the design speed (run_blend_model)
            float runRate = Mathf.Clamp(rateMove / (runClipSpeed * .98f), .25f, 2f);
            if (valid[(int)Clip.RunForward]) runPhase = (runPhase + dt * runRate) % length[(int)Clip.RunForward];
            for (int k = 0; k < Count; k++)
            {
                if (!valid[k]) continue;
                weight[k] = responsiveStroke || snapWeights ? target[k] : FluidOff ? Mathf.MoveTowards(weight[k], target[k], dt / .12f)
                    : Mathf.Abs(weight[k] - target[k]) < .002f ? target[k] : Mathf.SmoothDamp(weight[k], target[k], ref weightVel[k], .12f, Mathf.Infinity, dt);   // eased cross-fades (chat 4: match heroes .12 s - the run clips carry the racket wrist at another angle than ReadyIdle and a .06 s fade snapped it at 600-1000 deg/s)
                var id = (Clip)k;
                if (id == Clip.Ready || id == Clip.Idle) time[k] = (time[k] + dt) % length[k];
                else if (id == Clip.RunForward) time[k] = runBack ? Mathf.Repeat(runReversePivot - (float)runPhase, length[k]) : runPhase;
                else if (id == Clip.RunRight || id == Clip.RunLeft) time[k] = runBack ? Mathf.Repeat(runReversePivot - (float)runPhase, length[k]) : runPhase % length[k];
                else if (id == Clip.Walk) time[k] = (time[k] + dt * Mathf.Clamp(rateMove / walkClipSpeed, .3f, 1.8f)) % length[k];
                else if (actionActive && id == action) { time[k] = actionTime; if (upperPlayables[k].IsValid()) upperPlayables[k].SetTime(actionTime); }
                else if (juiceActive && id == juice) {time[k]=TennisEmotes.SourceTime(juice,(float)Math.Max(0,juiceTime),length[k]);if(upperPlayables[k].IsValid())upperPlayables[k].SetTime(time[k]);}
                playables[k].SetTime(time[k]);
            }
            // Humanoid mixers fill any missing weight with the default (muscle-zero) pose, which
            // drops the hips toward the ground: the blend must always sum to exactly 1.
            float total = 0; for (int k = 0; k < Count; k++) if (valid[k]) total += weight[k];
            if (total < 1e-4f) { weight[(int)Clip.Ready] = 1; total = 1; }
            for (int k = 0; k < Count; k++) if (valid[k]) weight[k] /= total;
            for (int k = 0; k < Count; k++) if (valid[k]) mixer.SetInputWeight(k, weight[k]);
            if (snapWeights) for (int k = 0; k < Count; k++) weightVel[k] = 0;
            {
                int wantUp = movingReaction ? (int)juice : actionActive && IsStroke(action) ? (int)action : upperFadeClip; float upSum = 0;
                for (int k = 0; k < Count; k++) { if (!upperPlayables[k].IsValid()) continue; upperBlend[k] = responsiveStroke || snapWeights ? (k == wantUp ? 1 : 0) : Mathf.MoveTowards(upperBlend[k], k == wantUp ? 1 : 0, dt / MatchUpperSwitch); upSum += upperBlend[k]; }
                for (int k = 0; k < Count; k++) if (upperPlayables[k].IsValid()) upperMixer.SetInputWeight(k, upSum > 1e-4f ? upperBlend[k] / upSum : (k == wantUp ? 1 : 0));
            }
            SetUpperMask(!actionActive&&(IsReaction((Clip)upperFadeClip)||IsEmote((Clip)upperFadeClip)));
            snapWeights = false;
            layers.SetInputWeight(1, upperW); UpperLayerWeight = upperW;
            WeightSum = total;
            // Walking in: face the direction of travel (a person walks forward, not sideways), then turn into
            // the serve stance once planted.
            float yawTo = walkMode && move > .25f ? Mathf.Atan2(v.x, v.y) * Mathf.Rad2Deg : 0;
            walkYaw = Mathf.MoveTowardsAngle(walkYaw, yawTo, dt * 420f);
            transform.localRotation = Quaternion.Euler(0, walkYaw, 0);
            SmoothRoot(dt);
            graph.Evaluate(0);
            inertia?.Apply(dt);
            PostProcess(swinging);
            if (!LocomotionOwnsFeet()) LockFeet(dt); else ReleaseFeet(dt);
            MeasureSkate(dt);
            GroundSoles();
            if (trail && trail.emitting && (trailFor -= Time.deltaTime) <= 0) trail.emitting = false;
            FinalSink = 0; for (int f = 0; f < 4; f++) if (feet[f]) FinalSink = Mathf.Max(FinalSink, -(transform.InverseTransformPoint(feet[f].position).y - (f % 2 == 0 ? heelRest : toeRest)));
            FinalizeGarments();
        }
        void FinalizeGarments()
        {
            matchLook.body?.GetComponent<HeroArmSkinning>()?.Apply();
            matchLook.GetComponent<HeroShoulderDeformation>()?.Apply();
            if (!garmentCorrectives) garmentCorrectives = matchLook.GetComponent<HeroGarmentPoseCorrectives>();
            if (garmentCorrectives) garmentCorrectives.Apply();
            matchLook.GetComponent<TailoredPoloDeformation>()?.Apply();
        }
        // ---- chat 4: shoe soles on the court. Ground() keeps the heel / toe JOINTS out of the court, but a raised heel still pushes the
        // toe cap through it and a low lunge sinks the sole (7-15 mm in the clips). The shoe's own sole points (baked once on ReadyIdle, where
        // the soles rest flat) are tested every frame: a toe cap under the court bends the toes up about the toe joint, a sole under the court
        // lifts that foot with the leg (knee bends). Feet in the air are untouched.
        readonly Vector3[][] solePts = new Vector3[4][]; readonly float[] soleRest = new float[2];
        public float SoleDipBefore { get; private set; }
        public float SoleDipAfter { get; private set; }
        void BuildSoles()
        {
            var baked = new Mesh();
            for (int f = 0; f < 2; f++)
            {
                SkinnedMeshRenderer shoe = null;
                foreach (var r in Rig.GetComponentsInChildren<SkinnedMeshRenderer>(true)) if (r.name == (f == 0 ? "Kit_Shoe_L" : "Kit_Shoe_R")) { shoe = r; break; }
                var foot = feet[f * 2]; var toe = feet[f * 2 + 1]; if (!shoe || !foot || !toe) continue;
                shoe.BakeMesh(baked, true); var m = shoe.transform.localToWorldMatrix; var v = baked.vertices;
                float low = float.MaxValue; var hs = new Vector3[v.Length];
                for (int i = 0; i < v.Length; i++) { var w = m.MultiplyPoint3x4(v[i]); hs[i] = w; low = Mathf.Min(low, transform.InverseTransformPoint(w).y); }
                soleRest[f] = low;
                var fwd = Vector3.ProjectOnPlane(toe.position - foot.position, transform.up).normalized;
                var toeList = new List<Vector3>(); var footList = new List<Vector3>();
                for (int i = 0; i < hs.Length; i++)
                {
                    if (transform.InverseTransformPoint(hs[i]).y > low + .012f) continue;
                    if (Vector3.Dot(hs[i] - toe.position, fwd) > -.01f) toeList.Add(toe.InverseTransformPoint(hs[i])); else footList.Add(foot.InverseTransformPoint(hs[i]));
                }
                List<Vector3> Thin(List<Vector3> l) { if (l.Count <= 40) return l; var o = new List<Vector3>(); for (int i = 0; i < 40; i++) o.Add(l[i * l.Count / 40]); return o; }
                solePts[f * 2] = Thin(footList).ToArray(); solePts[f * 2 + 1] = Thin(toeList).ToArray();
            }
            Destroy(baked);
        }
        float SoleLow(Transform bone, Vector3[] pts, int f, out Vector3 deepest)
        {
            float low = float.MaxValue; deepest = bone.position;
            foreach (var p in pts) { var w = bone.TransformPoint(p); float h = transform.InverseTransformPoint(w).y - soleRest[f]; if (h < low) { low = h; deepest = w; } }
            return low;
        }
        void GroundSoles()
        {
            SoleDipBefore = SoleDipAfter = 0;
            for (int f = 0; f < 2; f++)
            {
                var foot = feet[f * 2]; var toe = feet[f * 2 + 1]; var ft = solePts[f * 2]; var tt = solePts[f * 2 + 1];
                if (!foot || !toe || ft == null || tt == null || (ft.Length == 0 && tt.Length == 0)) continue;
                Vector3 pT = toe.position; float dT = tt.Length > 0 ? SoleLow(toe, tt, f, out pT) : 1, dF = ft.Length > 0 ? SoleLow(foot, ft, f, out _) : 1;
                SoleDipBefore = Mathf.Max(SoleDipBefore, -Mathf.Min(dT, dF));
                if (dT < -.002f && tt.Length > 0)
                {
                    // bend the toes up about the toe joint until the toe cap is back on the court
                    var axis = Vector3.Cross(transform.up, Vector3.ProjectOnPlane(toe.position - foot.position, transform.up)).normalized;
                    float r = Mathf.Max(.02f, Vector3.ProjectOnPlane(pT - toe.position, axis).magnitude);
                    float ang = Mathf.Asin(Mathf.Clamp01(-dT / r)) * Mathf.Rad2Deg;
                    if (HeroShoeShape.Depth) ang = Mathf.Min(ang, 15f);   // HERO DEPTH: a shoe's toe box does not fold
                    var q0 = toe.rotation;
                    toe.rotation = Quaternion.AngleAxis(ang, axis) * q0; float up1 = SoleLow(toe, tt, f, out _);
                    toe.rotation = Quaternion.AngleAxis(-ang, axis) * q0; float up2 = SoleLow(toe, tt, f, out _);
                    toe.rotation = Quaternion.AngleAxis(up1 >= up2 ? ang : -ang, axis) * q0;
                }
                if (dF < -.002f && ft.Length > 0)
                {
                    var upper = Bone(f == 0 ? HumanBodyBones.LeftUpperLeg : HumanBodyBones.RightUpperLeg); var lower = Bone(f == 0 ? HumanBodyBones.LeftLowerLeg : HumanBodyBones.RightLowerLeg);
                    if (upper && lower) { var fr = foot.rotation; TwoBone(upper, lower, foot, foot.position + transform.up * -dF); foot.rotation = fr; }
                }
            }
            // what the leg could not reach (a fully stretched leg): lift the hips by the rest, the other foot stays where it is
            float rest = 0; var low = new float[2];
            for (int f = 0; f < 2; f++)
            {
                var foot = feet[f * 2]; var toe = feet[f * 2 + 1]; var ft = solePts[f * 2]; var tt = solePts[f * 2 + 1]; low[f] = 1;
                if (!foot || !toe || ft == null || tt == null) continue;
                low[f] = Mathf.Min(tt.Length > 0 ? SoleLow(toe, tt, f, out _) : 1, ft.Length > 0 ? SoleLow(foot, ft, f, out _) : 1);
                rest = Mathf.Max(rest, -low[f]);
            }
            if (rest > .002f && hips)
            {
                var keep = new Vector3[2]; var keepR = new Quaternion[2];
                for (int f = 0; f < 2; f++) if (feet[f * 2]) { keep[f] = feet[f * 2].position; keepR[f] = feet[f * 2].rotation; }
                hips.position += transform.up * rest;
                for (int f = 0; f < 2; f++)
                {
                    var foot = feet[f * 2]; if (!foot) continue;
                    var upper = Bone(f == 0 ? HumanBodyBones.LeftUpperLeg : HumanBodyBones.RightUpperLeg); var lower = Bone(f == 0 ? HumanBodyBones.LeftLowerLeg : HumanBodyBones.RightLowerLeg);
                    // the dipping foot rises with the body, a foot on or above the court is put back where it was
                    if (upper && lower && -low[f] < rest - .001f) { TwoBone(upper, lower, foot, keep[f] + transform.up * Mathf.Max(0, -low[f])); foot.rotation = keepR[f]; }
                }
            }
            for (int f = 0; f < 2; f++)
            {
                var foot = feet[f * 2]; var toe = feet[f * 2 + 1]; var ft = solePts[f * 2]; var tt = solePts[f * 2 + 1];
                if (!foot || !toe || ft == null || tt == null) continue;
                float a1 = tt.Length > 0 ? SoleLow(toe, tt, f, out _) : 1, a2 = ft.Length > 0 ? SoleLow(foot, ft, f, out _) : 1;
                SoleDipAfter = Mathf.Max(SoleDipAfter, -Mathf.Min(a1, a2));
            }
        }
        /// Deepest sole below the court on the pose actually rendered this frame.
        public float FinalSink { get; private set; }
        /// SERVE_AND_FEET: while Walk / RunForward / RunLeft / RunRight carry the legs (>= 0.9 of the blend, no stroke), their planted foot already stands still on the court
        /// (the clip is played at the real ground speed, the hero moves smoothly): the ankle lock would pin the foot at the first touch and fight the heel-to-toe roll. The lock
        /// state is cleared so it starts clean when the hero stops.
        bool LocomotionOwnsFeet()
        {
            // chat 4: the lock is let go here and faded out by ReleaseFeet (zeroing it popped the leg 5,000 deg/s in one frame)
            if(reactionLegShare>.85f&&Moving()>.5f)
            {for(int f=0;f<2;f++){locked[f]=false;stepping[f]=false;}return true;}
            if (juiceActive && IsEmote(juice) && reactionLegShare < .5f) { for (int f = 0; f < 2; f++) { locked[f] = false; stepping[f] = false; } return true; }   // EMOTES: the clip owns the feet
            if (actionActive || juiceActive) { return false; }
            float loco = weight[(int)Clip.Walk] + weight[(int)Clip.RunForward] + weight[(int)Clip.RunLeft] + weight[(int)Clip.RunRight];
            if (loco < .9f) return false;
            for (int f = 0; f < 2; f++) { locked[f] = false; stepping[f] = false; }
            return true;
        }
        /// chat 4: the clip (or the locomotion cycle) has taken the feet back: whatever lock is still on fades out over 0.12 s.
        void ReleaseFeet(float dt)
        {
            for (int f = 0; f < 2; f++)
            {
                if (lockW[f] <= 0) continue;
                lockW[f] = Mathf.MoveTowards(lockW[f], 0, dt / .12f);
                var upper = Bone(f == 0 ? HumanBodyBones.LeftUpperLeg : HumanBodyBones.RightUpperLeg);
                var lower = Bone(f == 0 ? HumanBodyBones.LeftLowerLeg : HumanBodyBones.RightLowerLeg);
                var foot = feet[f * 2]; if (!upper || !lower || !foot || lockW[f] <= 0) continue;
                float w = Mathf.SmoothStep(0, 1, lockW[f]);
                var target = Vector3.Lerp(foot.position, new Vector3(lockPos[f].x, foot.position.y, lockPos[f].z), w);
                var footRot = foot.rotation; TwoBone(upper, lower, foot, target); foot.rotation = footRot;
            }
        }
        // ---- foot plant lock: a foot the clip has on the ground stays put in world space (leg IK)
        readonly bool[] locked = new bool[2]; readonly Vector3[] lockPos = new Vector3[2]; readonly float[] lockW = new float[2];
        readonly bool[] stepping = new bool[2]; readonly float[] stepT = new float[2]; readonly Vector3[] stepFrom = new Vector3[2];
        const float StepTime = .12f, StepDrift = .2f;
        public int StepsTaken { get; private set; }
        void LockFeet(float dt)
        {
            var a = Anim;
            for (int f = 0; f < 2; f++)
            {
                var upper = Bone(f == 0 ? HumanBodyBones.LeftUpperLeg : HumanBodyBones.RightUpperLeg);
                var lower = Bone(f == 0 ? HumanBodyBones.LeftLowerLeg : HumanBodyBones.RightLowerLeg);
                var foot = feet[f * 2]; var toe = feet[f * 2 + 1]; if (!upper || !lower || !foot || !toe) continue;
                float h = Mathf.Min(transform.InverseTransformPoint(foot.position).y - heelRest, transform.InverseTransformPoint(toe.position).y - toeRest);
                float legLen = Vector3.Distance(upper.position, lower.position) + Vector3.Distance(lower.position, foot.position);
                // Score80 A: the serve's grounded frames plant too (the stance unwinds on the feet instead of sliding
                // them round the root); the jump itself still lifts them off (h > 4.5 cm releases).
                bool plantedNow = h < .02f && (!FluidOff || !(actor.Swinging && actor.Kind == TennisActor.Stroke.Serve));
                // Score80 A: a planted foot the body has moved away from is picked up and re-planted (a quick
                // arced step), never dragged back along the court -- run -> plant -> pivot instead of skate.
                if (stepping[f] && !FluidOff)
                {
                    stepT[f] += dt / StepTime;
                    float u = Mathf.SmoothStep(0, 1, Mathf.Clamp01(stepT[f]));
                    var goal = Vector3.Lerp(stepFrom[f], new Vector3(foot.position.x, stepFrom[f].y, foot.position.z), u);
                    goal.y = foot.position.y + Mathf.Sin(Mathf.PI * Mathf.Clamp01(stepT[f])) * .065f;
                    var fr = foot.rotation; TwoBone(upper, lower, foot, goal); foot.rotation = fr;
                    if (stepT[f] >= 1) { stepping[f] = false; locked[f] = plantedNow; lockPos[f] = foot.position; lockW[f] = plantedNow ? 1 : 0; StepsTaken++; }
                    continue;
                }
                if (!locked[f] && plantedNow) { locked[f] = true; lockPos[f] = foot.position; }
                float slip = !FluidOff && actionActive && IsStroke(action) ? .6f : .35f;   // Plan 3A: plant through the stroke (stop-into-swing)
                float drift = Vector3.Distance(Flat(foot.position), Flat(lockPos[f]));
                if (!FluidOff && locked[f] && plantedNow && lockW[f] > .9f && drift > StepDrift && !stepping[1 - f] && dt > 0
                    && Vector3.Distance(upper.position, foot.position) < legLen * .985f)
                {
                    stepping[f] = true; stepT[f] = 0; stepFrom[f] = lockPos[f]; locked[f] = false; lockW[f] = 0;
                    var fr = foot.rotation; TwoBone(upper, lower, foot, lockPos[f]); foot.rotation = fr;   // this frame still on the old spot
                    continue;
                }
                if (locked[f] && (h > .045f || Vector3.Distance(upper.position, lockPos[f]) > legLen * .985f || drift > slip)) locked[f] = false;
                lockW[f] = Mathf.MoveTowards(lockW[f], locked[f] ? 1 : 0, dt / (locked[f] ? .05f : .1f));
                if (lockW[f] <= 0) continue;
                var target = Vector3.Lerp(foot.position, new Vector3(lockPos[f].x, foot.position.y, lockPos[f].z), lockW[f]);
                var footRot = foot.rotation;
                TwoBone(upper, lower, foot, target);
                foot.rotation = footRot;
            }
        }
        /// Elbow position a two-bone solve would give for `target` (pole from the current elbow), without applying it.
        static Vector3 ElbowFor(Transform up, Transform lo, Transform end, Vector3 target)
        {
            float l1 = Vector3.Distance(up.position, lo.position), l2 = Vector3.Distance(lo.position, end.position);
            var toT = target - up.position; float d = Mathf.Clamp(toT.magnitude, Mathf.Abs(l1 - l2) + 1e-3f, l1 + l2 - 1e-3f);
            var dir = toT.normalized; var pole = Vector3.ProjectOnPlane(lo.position - up.position, dir).normalized;
            float along = (l1 * l1 - l2 * l2 + d * d) / (2 * d), hh = Mathf.Sqrt(Mathf.Max(0, l1 * l1 - along * along));
            return up.position + dir * along + pole * hh;
        }
        static Vector3 Flat(Vector3 v) => new Vector3(v.x, 0, v.z);
        static void TwoBone(Transform up, Transform lo, Transform end, Vector3 target)
        {
            float l1 = Vector3.Distance(up.position, lo.position), l2 = Vector3.Distance(lo.position, end.position);
            var toT = target - up.position; float d = Mathf.Clamp(toT.magnitude, Mathf.Abs(l1 - l2) + 1e-3f, l1 + l2 - 1e-3f);
            var dir = toT.normalized; var pole = Vector3.ProjectOnPlane(lo.position - up.position, dir).normalized;
            if (pole.sqrMagnitude < 1e-6f) return;
            float along = (l1 * l1 - l2 * l2 + d * d) / (2 * d), hh = Mathf.Sqrt(Mathf.Max(0, l1 * l1 - along * along));
            var knee = up.position + dir * along + pole * hh;
            up.rotation = Quaternion.FromToRotation(lo.position - up.position, knee - up.position) * up.rotation;
            lo.rotation = Quaternion.FromToRotation(end.position - lo.position, up.position + dir * d - lo.position) * lo.rotation;
        }
        /// Real ground speed over commanded speed (the game's pace), smoothed over ~0.06 s: 1 until the hero has moved enough to measure it.
        Vector3 lastActorPos; bool haveActorPos; float paceReal, paceCmd, paceRatio = 1;
        float GroundPace(float move, float dt)
        {
            var p = actor.transform.position; p.y = 0;
            if (haveActorPos && dt > 1e-4f)
            {
                float disp = Vector3.Distance(p, lastActorPos) / dt;
                if (disp < move * 2f + 1.5f)   // a teleport (point reset, new match) is not walking
                {
                    float k = 1 - Mathf.Exp(-dt / .06f);
                    paceReal += (disp - paceReal) * k; paceCmd += (move - paceCmd) * k;
                }
            }
            lastActorPos = p; haveActorPos = true;
            if (paceCmd > .3f) paceRatio = Mathf.Clamp(paceReal / paceCmd, .6f, 1.4f);
            return paceRatio;
        }
        /// The game moves the actor in 1/120 s steps, so a rendered frame covers one, two or three of them and the hero's position along the court judders by up to
        /// a step per frame (11 mm at a walk, 40 mm at a run) while its planted feet are held still: the world position of a planted toe then seems to slide. The hero is
        /// drawn at the actor's position carried forward at the real ground velocity (the commanded velocity, at the game's pace) and eased back onto the actor, so the
        /// hero is on the actor on average and moves smoothly between the steps. Visual only: the actor, the ball and the contact are not touched.
        Vector3 smoothPos, lastRawPos, smoothLocal; bool smoothInit; int stillFrames;
        void SmoothRoot(float dt)
        {
            if (dt < 1e-4f) return;
            var raw = actor.transform.position; raw.y = 0;
            if (isPlayer && game && game.PlayerUsesTrackedMovement) {
                // Gameplay already receives the filtered tracking position. A second
                // 100 ms visual correction makes live steering appear to trail it.
                smoothPos = lastRawPos = raw; smoothInit = true; smoothLocal = Vector3.zero;
                return;
            }
            if (!smoothInit) { smoothPos = raw; lastRawPos = raw; smoothInit = true; }
            stillFrames = Vector3.Distance(raw, lastRawPos) < 1e-5f ? stillFrames + 1 : 0; lastRawPos = raw;
            var vel = actor.transform.right * actor.Speed + actor.transform.forward * actor.ForwardSpeed; vel.y = 0; vel *= paceRatio;
            // a frozen world (hit stop), a reset: sit on the actor
            if (stillFrames >= 3 || Vector3.Distance(raw, smoothPos) > .25f) smoothPos = raw;
            else { smoothPos += vel * dt; smoothPos += (raw - smoothPos) * (1 - Mathf.Exp(-dt / .1f)); }
            smoothLocal = actor.transform.InverseTransformVector(smoothPos - raw);
        }
        readonly Vector3[] lastToe = new Vector3[2];
        /// Fastest planted-toe ground slide this frame (m/s). 0 = feet locked to the court.
        public float FootSkate { get; private set; }
        void MeasureSkate(float dt)
        {
            FootSkate = 0; if (dt <= 0) return;
            for (int f = 0; f < 2; f++)
            {
                var toe = feet[f * 2 + 1]; if (!toe) continue; var p = toe.position;
                float h = transform.InverseTransformPoint(p).y - toeRest;
                var d = p - lastToe[f]; d.y = 0;
                if (h < .015f && lastToe[f] != Vector3.zero) FootSkate = Mathf.Max(FootSkate, d.magnitude / dt);
                lastToe[f] = p;
            }
        }

        Vector3 lungeOffset;
        float contactCrouch, contactCrouchVelocity;
        int contactCrouchFrame=-1, contactLungeFrame=-1;
        bool crouchApplied;
        void PostProcess(bool swinging,bool physicsSubstep=false)
        {
            crouchApplied=false;
            // Ease any contact lunge back under the actor (feet re-centre over ~0.25 s).
            if (lungeOffset != Vector3.zero && !(swinging && IsStroke(action) && Mathf.Abs(actor.SignedTimeToContact) < .16f))
            { lungeOffset = Vector3.MoveTowards(lungeOffset, Vector3.zero, Time.deltaTime * 1.2f); }
            transform.localPosition = lungeOffset + smoothLocal;
            if (!FluidOff) MatchBodyMotion();
            Ground();
            // (the match heroes' finger grip is baked into every clip)
            // (The dive's code-bent pose, which rolled the hero 66 degrees and folded chest and legs, was removed 2026-11-13:
            // it warped the body at full stretch. A wide ball is now a stretch lunge on the wide-reach clip, TennisAbilities.)
            transform.localRotation=Quaternion.Euler(0,walkYaw,0);
            if (swinging && IsStroke(action)) AssistContact(physicsSubstep);
            if(!PathAssist) ContactRecovery(physicsSubstep);
            if(!crouchApplied) ContactCrouch(0,false);
            TossArm();
            if (performance != null)
                performance.Apply(actor, game, transform, actionActive,
                    juiceActive && IsEmote(juice), juiceActive && !IsEmote(juice), Time.deltaTime);
            float poseTime = physicsSubstep && actor && actor.Swinging
                ? StrokeTime((int)action, actor.SignedTimeToContact) : (float)actionTime;
            ApplyOpenForehandClearance(actionActive ? action : Clip.Ready, poseTime,
                actionActive ? Mathf.Max(actionWeight, UpperLayerWeight) : 0);
            ApplyServeWrist(actionActive ? action : Clip.Ready, poseTime);
            // Locked-wrist elbow correction cannot change racket contact. Run it
            // on the displayed pose, not again for every 120 Hz physics sample.
            if (!physicsSubstep) {
                if (juiceActive && juice == Clip.IntroWave) poseSafety?.RelaxWaveWrist();
                float freedom = actionActive && IsStroke(action) ? Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.12f, .28f, Mathf.Abs(poseTime-contact[(int)action]))) : 0;
                poseSafety?.Apply(actionActive || actionWeight > .05f && !juiceActive, actionActive && action == Clip.Serve, freedom, TopHandOnRacket());
                if (juiceActive && juice == Clip.IntroWave) poseSafety?.LimitWaveWristFlexion();
                FinalArmPenetration = poseSafety?.ResidualDepth ?? 0;
            }

        }

        // ---- serve ritual: the tossing hand really bounces and tosses the ball
        float ServeStanceT => serveStanceTime; float ServeReleaseT => serveReleaseTime; float ServeTrophyT => serveTrophyTime;
        float swingStartTtc = .3f, swingStartBase;
        void BeginSwingTime(Clip next,float ttc)
        {
            BeginMatchSwing(next, ttc);
        }
        /// Match heroes (chat 4): a swing is one time-warp from the pose already on screen to the clip's contact frame, landing on the
        /// gameplay contact. The clip reaches its contact frame at its authored speed (rate 1 in real time), so the racket meets the ball as
        /// fast as it was animated; time to spare is spent holding the prepared pose (the serve's trophy), too little time is taken out of
        /// the take-back (never faster than MaxStartRate x authored at the start). After the contact the clip runs on in real time.
        float swingS0, swingT0; double actionVirtual;
        /// TennisGame's opponent serve: the toss runs 0.85 game seconds from release to the strike (prepare = toss age / 0.85).
        const float RivalTossToContact = .85f;
        const float MinWarp = .4f, HoldCorner = .06f;
        void BeginMatchSwing(Clip next, float ttc)
        {
            int i = (int)next;
            float prepared = 0;
            if (next == Clip.Serve) prepared = actionActive && action == Clip.Serve && !followThrough ? Mathf.Max((float)actionVirtual, ServeReleaseT) : ServeTrophyT;
            else if (actionActive && !followThrough && IsStroke(action))
                prepared = action == next ? (float)actionVirtual : (float)actionVirtual / Mathf.Max(.01f, contact[(int)action]) * contact[i];   // the same share of the take-back in the new clip
            swingT0 = Mathf.Max(RealToContact(ttc), .05f);
            swingS0 = Mathf.Clamp(Mathf.Max(prepared, contact[i] - swingT0 / MinWarp), 0, contact[i]);
            swingStartTtc = Mathf.Max(ttc, .05f);
            inertia?.Request(.12f);
            snapWeights = true;   // the base layer switches clip at once (a cross-fade from the prepared forehand to a backhand swept the arm through an average pose)
            SwingStarts++;
        }
        public int SwingStarts { get; private set; }
        bool snapWeights;
        float MatchStrokeTime(int i, float ttc) => Retime(i, MatchAuthoredTime(i, ttc));
        float MatchAuthoredTime(int i, float ttc)
        {
            float c = contact[i];
            if (ttc <= 0) return Mathf.Clamp(c - RealToContact(ttc), 0, length[i]);
            float tau = RealToContact(ttc), D = c - swingS0, T0 = swingT0;
            if (tau >= T0 || D <= 0) return swingS0;
            if (D <= T0)
            {
                // time to spare: hold the start pose, then the clip at its own speed into the contact (C1 corner of half-width h)
                float h = Mathf.Min(HoldCorner, T0 - D, D);
                if (tau >= D + h) return swingS0;
                if (tau <= D - h) return c - tau;
                float u = D + h - tau; return swingS0 + u * u / (4 * Mathf.Max(h, 1e-4f));
            }
            // too little time: a quadratic warp that starts fast and reaches the contact at the authored rate
            float k = T0 / D, x = 1 - tau / T0;
            return swingS0 + D * ((2 - k) * x + (k - 1) * x * x);
        }
        /// Clip time for a stroke at signed time-to-contact `ttc`: contact-locked. The serve's swing
        /// runs the clip's whole trophy -> racket drop -> unwind -> contact section (1.80 -> 2.33 s)
        /// over however long the gameplay swing takes to reach the ball, so hips lead, the torso
        /// uncoils and the arm comes last (a straight contact-minus-ttc map started it 0.15 s before
        /// contact: an arm-only chop). Contact frame and follow-through are unchanged.
        float StrokeTime(int i, float ttc, bool burst = true)
        {
            return MatchStrokeTime(i, ttc);
        }
        /// Serve stance yaw (deg) on the hero root: the clip's stance is turned ~130 deg (back to the
        /// camera-side fence); side-on to the baseline is ~90. Held through the ritual and trophy, then
        /// unwound to zero exactly at contact (so the contact model and honest hit are unchanged).
        float serveYaw;
        Vector3? VisualTossPoint(int k)
        {
            return tossPoints != null ? Quaternion.Euler(0, walkYaw, 0) * tossPoints[Mathf.Clamp(k, 0, 2)] : (Vector3?)null;   // read off the Serve clip's tossing hand (BuildServeRitualPoints)
        }
        float tossWeight; Transform leftMiddle;
        void TossArm()
        {
            float want = actor.PrepareServe || (actionActive && action == Clip.Serve && actor.Swinging) ? actor.TossReachWanted : 0;
            if (tossFollowsClip && actor.PrepareAmount > .001f) want = 0;   // wind-up and toss: the clip's straight arm
            tossWeight = Mathf.MoveTowards(tossWeight, want, Time.deltaTime / .12f);
            if (tossWeight <= .001f) return;
            var a = Anim;
            Transform up = Bone(HumanBodyBones.LeftUpperArm), lo = Bone(HumanBodyBones.LeftLowerArm), hand = Bone(HumanBodyBones.LeftHand);
            if (!leftMiddle) leftMiddle = Bone(HumanBodyBones.LeftMiddleProximal);
            if (!leftMiddle) foreach (var t in hand.GetComponentsInChildren<Transform>()) if (t.name == "Middle1.L") { leftMiddle = t; break; }
            // The routine's palm target is the ball centre while in hand: the fingers go over the ball while
            // pushing and catching bounces, under it once the wind-up lifts it and through the toss.
            Vector3 ball = actor.TossReachTarget;
            bool bouncing = actor.PrepareAmount <= .001f;
            Vector3 palm = leftMiddle ? Vector3.Lerp(hand.position, leftMiddle.position, .7f) : hand.position;
            Vector3 goal = ball + Vector3.up * (bouncing ? .045f : -.045f);
            var hr = hand.rotation;
            TwoBone(up, lo, hand, Vector3.Lerp(hand.position, hand.position + (goal - palm), tossWeight));
            hand.rotation = hr;
        }

        // ================================================================ Plan 3A body motion
        float dipPos; public float PlantDip => dipPos;   // (MatchHeroProof reads it; the plant dip went with the old body layers)
        float coil;
        public float ActionWeight => actionWeight;
        /// Match heroes keep the authored pose: no kinetic-chain lead, squash / stretch, breathing or chest springs. The ultimate's charge
        /// still coils the body (that is a gameplay moment, not a stylised layer).
        void MatchBodyMotion()
        {
            float udt = Time.timeScale > 0 ? Time.deltaTime : (Time.captureFramerate > 0 ? 1f / Time.captureFramerate : Time.unscaledDeltaTime);
            var j = game ? game.Juice : null;
            bool charging = j && j.UltimateActive && j.ChargeSubject == actor.transform;
            coil = Mathf.MoveTowards(coil, charging ? 1 : 0, udt / (charging ? .35f : .06f));
            if (coil <= .001f) return;
            float pulse = Mathf.Sin(Time.unscaledTime * 9) * .5f + .5f;
            var up = transform.up; var side = transform.right;
            float dir = actor.Backhand ? -1 : 1;
            hips.rotation = Quaternion.AngleAxis(-14 * dir * coil, up) * hips.rotation;
            spineB.rotation = Quaternion.AngleAxis(-10 * dir * coil, up) * Quaternion.AngleAxis(-6 * coil, side) * spineB.rotation;
            chestB.rotation = Quaternion.AngleAxis(-18 * dir * coil, up) * Quaternion.AngleAxis((-8 - 3 * pulse) * coil, side) * chestB.rotation;
        }

        /// Feet never below the court: lift the whole body by the deepest sole.
        void Ground()
        {
            float low = float.MaxValue;
            for (int f = 0; f < 4; f++) { if (!feet[f]) continue; float h = transform.InverseTransformPoint(feet[f].position).y - (f % 2 == 0 ? heelRest : toeRest); low = Mathf.Min(low, h); }
            SinkBeforeGround = Mathf.Max(0, -low);
            if (low < -.002f && low > -.3f) { hips.position += transform.up * -low; LastGroundLift = -low; } else LastGroundLift = 0;
        }
        public float LastGroundLift { get; private set; }
        public float WeightSum { get; private set; }
        /// Walking to the serve spot (or back into position between points): walk cycle, not the run or a frozen stance.
        bool WalkMode() => valid[(int)Clip.Walk] && game && !actor.Swinging && (WalkingIn() || BetweenPoints()) && Moving() < 2.4f;
        bool WalkingIn() => game && actor.PrepareServe && actor.PrepareAmount <= .001f && Moving() > .15f;
        public float UpperLayerWeight { get; private set; }
        public Vector3 StringCentre => stringCentre ? stringCentre.position : transform.position;
        /// Arm-in-torso depth sum for both arms on the pose actually rendered this frame.
        public float FinalArmPenetration { get; private set; }
        public float SinkBeforeGround { get; private set; }

        /// Hips / chest facing in hero space (deg, 0 = facing the net, +90 = facing the right sideline).
        public Vector2 BodyYaw()
        {
            var chest = Bone(HumanBodyBones.Chest);
            var frame = actor ? actor.transform : transform;   // facing relative to the court (includes the serve stance yaw)
            float Y(Quaternion q, Vector3 f) { var v = frame.InverseTransformDirection(q * f); return Mathf.Atan2(v.x, v.z) * Mathf.Rad2Deg; }
            return new Vector2(Y(hips.rotation, torsoFwdHips), Y(chest.rotation, torsoFwdChest));
        }

        /// Deterministic review: one clip at one time, with the same hands/props logic as gameplay.
        public void Sample(Clip c, float t)
        {
            // A gameplay stroke may have left the upper-body layer live. A diagnostic
            // sample must be one complete authored pose, including socket/prop keys.
            if (!graph.IsValid() || !valid[(int)c]) return;
            layers.SetInputWeight(1, 0); UpperLayerWeight = 0;
            for (int k = 0; k < Count; k++)
            {
                if (!valid[k]) continue;
                weight[k] = k == (int)c ? 1 : 0;
                mixer.SetInputWeight(k, weight[k]); playables[k].SetTime(k == (int)c ? t : 0);
            }
            graph.Evaluate(0);
            State = c + " sampled";
            ApplyOpenForehandClearance(c, t, 1);
            ApplyServeWrist(c, t);
            if (c == Clip.IntroWave) poseSafety?.RelaxWaveWrist();
            poseSafety?.Apply(IsStroke(c) || c == Clip.Ready, c == Clip.Serve, IsStroke(c) ? Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.12f,.28f,Mathf.Abs(t-contact[(int)c]))) : 0, c == Clip.Backhand || c == Clip.BackhandWide || c == Clip.Return || c == Clip.VolleyBackhand);
            if (c == Clip.IntroWave) poseSafety?.LimitWaveWristFlexion();
            FinalArmPenetration = poseSafety?.ResidualDepth ?? 0;
            FinalizeGarments();
        }
        // The male open forehand folds its forearm through the right waist at
        // contact. Swivel the elbow about the unchanged shoulder-to-wrist axis;
        // restore the wrist orientation so every finger and racket socket stays
        // on the exact original contact transform. Only this authored clip window
        // receives the correction; garment evaluation still follows the final rig.
        void ApplyOpenForehandClearance(Clip clip, float poseTime, float blend)
        {
            if (matchLook.female || matchLook.golfKit) return;
            if (Environment.GetEnvironmentVariable("VISUAL_OPEN_FOREHAND_CLEARANCE") == "0") return;
            float relative = poseTime - contact[(int)Clip.ForehandOpen];
            float window = 1 - Mathf.SmoothStep(0, 1, Mathf.Clamp01(Mathf.Abs(relative) / .16f));
            float amount = clip == Clip.ForehandOpen
                ? window * Mathf.Clamp01(blend) : 0;
            if (amount <= .00001f) return;
            var upper = Bone(HumanBodyBones.RightUpperArm);
            var lower = Bone(HumanBodyBones.RightLowerArm);
            var hand = Bone(HumanBodyBones.RightHand);
            if (!upper || !lower || !hand) return;
            var axis = hand.position - upper.position;
            if (axis.sqrMagnitude < .000001f) return;
            var handRotation = hand.rotation;
            var lowerRotation = lower.rotation;
            var swivel = Quaternion.AngleAxis(60f * amount, axis.normalized);
            upper.rotation = swivel * upper.rotation;
            lower.rotation = swivel * lowerRotation;
            hand.rotation = handRotation;
        }

        public float ContactOf(Clip c) => contact[(int)c];
        public float LengthOf(Clip c) => length[(int)c];

        void ApplyServeWrist(Clip clip, float poseTime)
        {
            if (clip != Clip.Serve) return;
            float hit = contact[(int)Clip.Serve];
            // Cock through the trophy, release before the contact window. The
            // exact authored strings/ball transform stays untouched at impact.
            float u = Mathf.InverseLerp(Mathf.Max(0, hit - .65f), hit - .12f, poseTime);
            float bend = Mathf.Sin(u * Mathf.PI) * 16;
            if (u <= 0 || u >= 1) return;
            var hand = Bone(HumanBodyBones.RightHand);
            if (hand) hand.rotation = Quaternion.AngleAxis(bend, transform.right) * hand.rotation;
        }

        float Moving() => new Vector2(actor.Speed, actor.ForwardSpeed).magnitude;
        bool BetweenPoints() => game && (game.Flow == TennisGame.Phase.PointOver || game.Flow == TennisGame.Phase.MatchOver);

        /// Near contact, nudge the right arm (two-bone, hand rotation kept) so the hero's string bed
        /// meets the gameplay racket's sweet spot, i.e. where the ball is actually struck.
        public float LastCrouch { get; private set; }
        public float LastDesiredCrouch { get; private set; }
        public Vector3 RenderedLunge => lungeOffset;
        public Vector3 LastGuideGoal { get; private set; }
        public float LastAssistWeight { get; private set; }
        public float LastPhysicsCrouch { get; private set; }
        public Vector3 LastPhysicsLunge { get; private set; }
        public Vector3 LastPhysicsStrings { get; private set; }
        public float LastPhysicsTtc { get; private set; }
        public float PhysicsPoseRestoreError { get; private set; }
        /// The off hand is still on the handle in this stroke (the two-handed backhand, and for the match set every clip whose left hand
        /// lets go only after the contact: Backhand, BackhandWide, Return, VolleyBackhand), so it rides the same nudge as the racket hand.
        bool TopHandOnRacket()
        {
            float release = leftRelease[(int)action];
            return release > 0 && actionTime < release;
        }
        void ContactCrouch(float desired,bool exactContact)
        {
            crouchApplied=true;LastDesiredCrouch=desired;
            if(exactContact) {contactCrouch=desired;contactCrouchVelocity=0;}
            else if(contactCrouchFrame!=Time.frameCount)
            {
                contactCrouchFrame=Time.frameCount;
                contactCrouch=Mathf.SmoothDamp(contactCrouch,desired,ref contactCrouchVelocity,desired>contactCrouch?.045f:.12f,4f,Time.deltaTime);
            }
            LastCrouch=contactCrouch;
            if(contactCrouch<.001f||!hips)return;
            var lu=Bone(HumanBodyBones.LeftUpperLeg);var ll=Bone(HumanBodyBones.LeftLowerLeg);var lf=Bone(HumanBodyBones.LeftFoot);
            var ru=Bone(HumanBodyBones.RightUpperLeg);var rl=Bone(HumanBodyBones.RightLowerLeg);var rf=Bone(HumanBodyBones.RightFoot);
            if(!lu||!ll||!lf||!ru||!rl||!rf)return;
            var lp=lf.position;var rp=rf.position;var lr=lf.rotation;var rr=rf.rotation;
            hips.position+=Vector3.down*contactCrouch;
            TwoBone(lu,ll,lf,lp);lf.rotation=lr;TwoBone(ru,rl,rf,rp);rf.rotation=rr;
            LastCrouch=contactCrouch;
        }
        Clip recoveryClip;bool hasRecoveryContact;
        Vector3 recoveryRight,recoveryLeft;Quaternion recoveryRightRotation,recoveryLeftRotation;
        void ContactRecovery(bool physicsSubstep)
        {
            if(!actor||!actionActive||!IsStroke(action)||!actor.Swinging){hasRecoveryContact=false;return;}
            float ttc=actor.SignedTimeToContact;
            var rh=Bone(HumanBodyBones.RightHand);var lh=Bone(HumanBodyBones.LeftHand);if(!rh||!lh)return;
            if(ttc>=-.004f&&ttc<.009f)
            {
                hasRecoveryContact=true;recoveryClip=action;
                recoveryRight=actor.transform.InverseTransformPoint(rh.position);recoveryLeft=actor.transform.InverseTransformPoint(lh.position);
                recoveryRightRotation=Quaternion.Inverse(actor.transform.rotation)*rh.rotation;recoveryLeftRotation=Quaternion.Inverse(actor.transform.rotation)*lh.rotation;
            }
            // Physics sub-steps always receive the exact contact / guide pose. Once
            // contact has passed, the rendered puppet carries that pose through a
            // short smooth release rather than snapping out of the arm correction.
            if(physicsSubstep||!hasRecoveryContact||recoveryClip!=action||ttc>=0||ttc<=-.075f)return;
            float u=Mathf.SmoothStep(0,1,-ttc/.075f);
            foreach(bool right in new[]{true,false})
            {
                var hand=right?rh:lh;var up=Bone(right?HumanBodyBones.RightUpperArm:HumanBodyBones.LeftUpperArm);var lo=Bone(right?HumanBodyBones.RightLowerArm:HumanBodyBones.LeftLowerArm);
                if(!up||!lo)continue;
                var anchor=actor.transform.TransformPoint(right?recoveryRight:recoveryLeft);
                var rotation=actor.transform.rotation*(right?recoveryRightRotation:recoveryLeftRotation);
                var wantedRotation=Quaternion.Slerp(rotation,hand.rotation,u);
                TwoBone(up,lo,hand,Vector3.Lerp(anchor,hand.position,u));hand.rotation=wantedRotation;
            }
        }

        /// chat 4: false = the old contact assist (strings pulled onto the ball, held there by ContactRecovery). HERO_PATH_ASSIST=0 for before/after proof.
        public static bool PathAssist = Environment.GetEnvironmentVariable("HERO_PATH_ASSIST") != "0";
        Vector3 aimGoal;
        void AssistContact(bool physicsSubstep)
        {
            float ttc = Mathf.Abs(actor.SignedTimeToContact);
            float w = Mathf.Clamp01(1 - ttc / .16f);
            // An assisted hit can meet the ball before or after the authored sweet frame.
            // Follow the planned contact envelope so the visible racket earns that contact,
            // while the chosen point on the strings determines shot quality.
            if (actor.Guiding) w = Mathf.Max(w, actor.ContactGuideWeight);
            LastAssistWeight=w;
            if (w <= 0 || !Grip) return;
            if (!actor.Guiding) return;
            var a = Anim;
            Transform up = Bone(HumanBodyBones.RightUpperArm), lo = Bone(HumanBodyBones.RightLowerArm), hand = Bone(HumanBodyBones.RightHand);
            // chat 4: the match heroes aim the clip's string PATH at the ball (StringPathOffset): the strings meet the ball at the
            // contact frame and keep the clip's own speed through it, instead of being pulled onto the ball and stopping there.
            bool pathAim = PathAssist;
            if (pathAim && actor.SignedTimeToContact > 0)
            {
                // the rival meets the live ball: where the ball will be at the contact (its own flight carried on), not where it is now
                if (game && actor == game.Opponent && game.Flow == TennisGame.Phase.Rally)
                { float tg = actor.SignedTimeToContact / SwingPace; aimGoal = game.BallPosition + game.BallVelocity * tg + .5f * Physics.gravity * tg * tg; }
                else aimGoal = actor.GuideSweetTarget;
            }
            Vector3 PathTravel() { int ci = (int)action; float pt = physicsSubstep ? StrokeTime(ci, actor.SignedTimeToContact) : (float)actionTime; return transform.TransformVector(contactLocal[ci] - ClipStrings(ci, pt)); }
            {
                // A reach is carried by the body too: lunge the whole hero toward the ball.
                var toBall = (pathAim ? aimGoal - (stringCentre.position + PathTravel()) : (game && actor == game.Opponent && game.Flow == TennisGame.Phase.Rally ? game.BallPosition : actor.GuideSweetTarget) - stringCentre.position); toBall.y = 0;
                float reach = isPlayer && actor.Guiding ? Mathf.Max(bodyReach, .45f) : bodyReach;
                var desiredLunge=Vector3.ClampMagnitude(toBall+actor.transform.TransformVector(lungeOffset),reach)*w;
                var desiredLocal=actor.transform.InverseTransformVector(desiredLunge);
                if(physicsSubstep&&ttc<.025f) lungeOffset=desiredLocal;
                else if(contactLungeFrame!=Time.frameCount)
                {
                    contactLungeFrame=Time.frameCount;
                    lungeOffset=Vector3.MoveTowards(lungeOffset,desiredLocal,Time.deltaTime*5.5f);
                }
                transform.localPosition=lungeOffset+smoothLocal;
                // A low ball is reached by bending the knees, not by driving the arm down through the
                // thigh: drop the hips and re-solve both legs so the feet stay planted on the court.
                Vector3 g0 = pathAim ? aimGoal : game && actor == game.Opponent && game.Flow == TennisGame.Phase.Rally ? game.BallPosition : actor.GuideSweetTarget;
                float low = (pathAim ? stringCentre.position.y + PathTravel().y : stringCentre.position.y) - g0.y - .08f;
                if(hips)
                    ContactCrouch(Mathf.Min(.34f,Mathf.Max(0,low)*.9f)*(actor.SignedTimeToContact>0?1:w),physicsSubstep&&ttc<.025f);

            }
            var sweet = pathAim ? stringCentre.position + PathTravel() : stringCentre.position;
            // The rival's racket reaches for the live ball (its planned meet point can sit off the real
            // flight), so the honest-contact check judges what is on screen.
            Vector3 goal = pathAim ? aimGoal : game && actor == game.Opponent && game.Flow == TennisGame.Phase.Rally ? game.BallPosition : actor.GuideSweetTarget;
            LastGuideGoal=goal;
            float armAssist = isPlayer && actor.Guiding ? Mathf.Max(contactAssist, .65f) : contactAssist;
            var delta = Vector3.ClampMagnitude(goal - sweet, armAssist) * w;
            if (delta.sqrMagnitude < 1e-6f) return;
            // Never buy reach by driving an arm into the torso. The hitting arm keeps the nudge only as far
            // as it stays clear (past that the honest-contact rule calls a real miss); on the two-hander the
            // top hand rides the handle only as far as it stays clear, then lets go (a stretched one-hand reach).
            // (match heroes: their clips were cleared against their own torso in Blender; the old torso model is not applied)
            if (TopHandOnRacket())
            {
                Transform lu = Bone(HumanBodyBones.LeftUpperArm), ll = Bone(HumanBodyBones.LeftLowerArm), lh = Bone(HumanBodyBones.LeftHand);
                var ld = delta;
                if (ld.sqrMagnitude > 1e-6f) { var lr = lh.rotation; TwoBone(lu, ll, lh, lh.position + ld); lh.rotation = lr; }
            }
            var handRot = hand.rotation; var target = hand.position + delta;
            float l1 = Vector3.Distance(up.position, lo.position), l2 = Vector3.Distance(lo.position, hand.position);
            var toT = target - up.position; float d = Mathf.Clamp(toT.magnitude, Mathf.Abs(l1 - l2) + 1e-3f, l1 + l2 - 1e-3f);
            var pole = Vector3.ProjectOnPlane(lo.position - up.position, toT.normalized).normalized;
            float along = (l1 * l1 - l2 * l2 + d * d) / (2 * d), h = Mathf.Sqrt(Mathf.Max(0, l1 * l1 - along * along));
            var elbow = up.position + toT.normalized * along + pole * h;
            up.rotation = Quaternion.FromToRotation(lo.position - up.position, elbow - up.position) * up.rotation;
            lo.rotation = Quaternion.FromToRotation(hand.position - lo.position, up.position + toT.normalized * d - lo.position) * lo.rotation;
            hand.rotation = handRot;
        }
    }
}
