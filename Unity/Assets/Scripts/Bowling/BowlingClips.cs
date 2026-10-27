using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Bowling
{
    /// The authored bowling clips (work/bowling-anim/PLAN_BowlingAnimation.md): 60 fps FBX under Resources/HeroMoves/<Sex>/Bowl_*.fbx, loaded by HubHeroAnimator
    /// under the id without underscores ("Bowl_Release_Hook" -> "BowlReleaseHook"). The variants of the shot are full-length clips that are identical to
    /// Bowl_Shot until their branch time, so the game can switch to one at the moment the release grade is known.
    public static class BowlingClips
    {
        public const string Stance = "BowlStance", Shot = "BowlShot", Abort = "BowlAbort";
        public const string Straight = "BowlReleaseStraight", Hook = "BowlReleaseHook", Backup = "BowlReleaseBackup", Early = "BowlReleaseEarly", Late = "BowlReleaseLate", Foul = "BowlFoul";
        public const string DropToe = "BowlDropToe", DropChase = "BowlDropChase", DropSpin = "BowlDropSpin";
        public const string FollowL = "BowlFollowThroughL", FollowR = "BowlFollowThroughR";
        public const string SitDown = "BowlSitDown", SitIdle = "BowlSitIdle", SitIdleBall = "BowlSitIdleBall", StandUp = "BowlStandUp", CheerSeated = "BowlCheerSeated", ClapSeated = "BowlClapSeated";
        public const string Pickup = "BowlPickup", PickupLow = "BowlPickupLow", WalkWithBall = "BowlWalkWithBall", WalkBack = "BowlWalkBack", WatchPins = "BowlWatchPins";

        /// Where the hips stand at the end of the shot clips (m ahead of the stance): the game moves the root there when the clip ends, so the idle stand
        /// that follows starts where the bowler finished. (c_shot.py: hips f = 3.55.)
        public const float ShotEndForward = 3.55f;
        public const float ShotLength = 4.6f;
        /// Where the hips end up (m ahead of the stance) at the end of each approach clip: the normal shot and its release variants end at 3.55, the foul slides on over the line and the
        /// drops end much closer (the bowler chases the ball back, or sits down), so the root takes exactly the position the clip finished at.
        public static float EndForward(string clipId)
        {
            switch (clipId)
            {
                case Foul: return 4.45f;
                case DropChase: return .25f;
                case DropToe: return .63f;
                case DropSpin: return 2.79f;
                default: return ShotEndForward;
            }
        }
        /// Where the ball centre sits in the gripping hand (work/bowling-anim/build/grip_<hero>.json, gripfit.py + gripframe.py): metres along
        /// e1 = knuckle direction (hand -> middle knuckle), e2 = across the knuckles (index -> little side, orthogonalised) and e3 = the palm side, from the hand bone.
        /// The fingers (middle, ring) and the thumb are curled so their tips are inside the ball by ~2 cm in every clip that holds it.
        public static Vector3 GripFrame(bool female) => female ? new Vector3(0.0675f, -0.0490f, 0.1340f) : new Vector3(0.0487f, -0.0004f, 0.1355f);

        /// Clip time at which the ball leaves the left-over "hold" (both hands) for the right hand alone.
        public const float BallInOneHand = .50f;

        /// Every clip the game asks for, with the length in seconds the Blender build wrote (gate A11 / BowlingClipTests): name -> frames at 60 fps.
        public static readonly Dictionary<string, int> Frames = new Dictionary<string, int>
        {
            { "Bowl_Stance", 61 }, { "Bowl_Abort", 73 }, { "Bowl_Shot", 277 },
            { "Bowl_Release_Straight", 277 }, { "Bowl_Release_Hook", 277 }, { "Bowl_Release_Backup", 277 }, { "Bowl_Release_Early", 277 }, { "Bowl_Release_Late", 277 },
            { "Bowl_Foul", 277 }, { "Bowl_Drop_Toe", 277 }, { "Bowl_Drop_Chase", 277 }, { "Bowl_Drop_Spin", 277 },
            { "Bowl_FollowThrough_L", 277 }, { "Bowl_FollowThrough_R", 277 },
            { "Bowl_Pickup", 73 }, { "Bowl_PickupLow", 73 }, { "Bowl_WalkWithBall", 61 }, { "Bowl_WalkBack", 61 }, { "Bowl_WatchPins", 241 },
            { "Bowl_SitDown", 61 }, { "Bowl_SitIdle", 241 }, { "Bowl_SitIdleBall", 241 }, { "Bowl_StandUp", 55 }, { "Bowl_Cheer_Seated", 145 }, { "Bowl_Clap_Seated", 121 },
            { "Bowl_React_Strike", 145 }, { "Bowl_React_Strike2", 145 }, { "Bowl_React_Strike3", 145 }, { "Bowl_React_Turkey", 181 },
            { "Bowl_React_Spare", 109 }, { "Bowl_React_Spare2", 97 }, { "Bowl_React_Gutter", 133 }, { "Bowl_React_Split", 115 }, { "Bowl_React_SevenTen", 145 },
            { "Bowl_React_ConvertedSplit", 157 }, { "Bowl_React_Foul", 109 }, { "Bowl_React_Miss", 109 }, { "Bowl_React_Win", 193 }, { "Bowl_React_Lose", 157 },
            { "Bowl_Intro1", 193 }, { "Bowl_Intro2", 205 },
            { "Bowl_Idle", 241 }, { "Bowl_Idle1", 241 }, { "Bowl_Idle2", 241 }, { "Bowl_Idle3", 241 }, { "Bowl_Idle4", 241 }, { "Bowl_IdleWipe", 241 },
            { "Bowl_ShuffleR", 37 }, { "Bowl_ShuffleL", 37 },
        };

        public static string Id(string clipName) => clipName.Replace("_", "");

        /// The variant of the shot for a resolved release, and the clip time it branches from the shot (switch at `max(t, branch)` is not needed: the
        /// variants are identical to the shot before the branch, so switch at the game's own approach time t).
        public static string ForRelease(in BowlingThrow th, float t, System.Random rng)
        {
            switch (th.Grade)
            {
                case ReleaseGrade.Early: return Early;
                case ReleaseGrade.Late: return Late;
                case ReleaseGrade.Foul: return Foul;
                case ReleaseGrade.Drop:
                    // the three gags branch at .55 / 1.05 / 1.50 s: the first one that has not branched yet (the last one for a late slip)
                    if (t <= .55f) return DropToe;
                    if (t <= 1.05f) return DropChase;
                    return DropSpin;
                default:
                    if (th.AxisDeg > 12f) return Hook;
                    if (th.AxisDeg < -12f) return Backup;
                    return Straight;
            }
        }

        /// Body english after a good release: the variants lean and kick toward the side the ball must go (+ = right).
        public static string BodyEnglish(float launchDeg) => launchDeg > 1.2f ? FollowR : launchDeg < -1.2f ? FollowL : null;

        /// Which reaction to play for a result kind ("Strike", "Turkey", "Spare", "ConvertedSplit", "Gutter", "Split", "SevenTen", "Foul", "Miss", "Win", "Lose").
        public static string Reaction(string kind, System.Random rng)
        {
            switch (kind)
            {
                case "Strike": { int v = rng.Next(3); return v == 0 ? "BowlReactStrike" : v == 1 ? "BowlReactStrike2" : "BowlReactStrike3"; }
                case "Spare": return rng.Next(2) == 0 ? "BowlReactSpare" : "BowlReactSpare2";
                case "Turkey": return "BowlReactTurkey";
                case "ConvertedSplit": return "BowlReactConvertedSplit";
                case "Gutter": return "BowlReactGutter";
                case "Split": return "BowlReactSplit";
                case "SevenTen": return "BowlReactSevenTen";
                case "Foul": return "BowlReactFoul";
                case "Miss": return "BowlReactMiss";
                case "Win": return "BowlReactWin";
                case "Lose": return "BowlReactLose";
                default: return null;
            }
        }
    }
}
