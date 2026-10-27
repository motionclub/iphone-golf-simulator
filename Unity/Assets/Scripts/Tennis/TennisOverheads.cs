using UnityEngine;

namespace GolfArcade.Tennis
{
    public static class TennisOverheads
    {
        /// A smash is still planned for a ball that has dropped this far (a late swing, or the TV running behind the game).
        public const float LowestContact = 1.55f;
        /// Swings this far ahead of contact are held and fired when the ball is in range, instead of wasted as a whiff.
        public const float EarliestSwing = 1.3f, ReadySwing = .45f, LatestLead = .15f, LungeTime = .12f;
        // Pick a descending, pre-bounce overhead rather than waiting for a waist-high return.
        public static TennisRules.InterceptPlan Plan(Vector3 p, Vector3 v, float spin, float curve,
            Vector2 player, Vector3 racketOffset, float speed, float reaction, float currentSpeed = 0)
        {
            if (v.z >= 0 || p.y + v.y*v.y/(2*9.81f) < 3.3f) return default;
            for(float t=TennisBall.Step*2; t<3; t+=TennisBall.Step*2) {
                TennisBall.Integrate(ref p,ref v,spin,TennisBall.Step*2,curve);
                if(p.y<TennisRules.BallRadius) break;
                if(v.y>=0 || p.y>Mathf.Clamp(racketOffset.y + .08f,2f,2.55f) || p.y<LowestContact || p.z> -2 || p.z< -13.5f) continue;
                var goal=new Vector2(p.x-racketOffset.x,p.z-racketOffset.z);
                if(Mathf.Abs(goal.x)>TennisRules.CourtHalfWidth+1.5f || goal.y< -14.3f || goal.y> -2.6f) continue;
                float available=Mathf.Max(0,t-reaction);
                float cover=Mathf.Max(TennisRules.Coverable(available,speed),Mathf.Min(speed,currentSpeed)*available);
                float gap=Vector2.Distance(player,goal)-cover;
                if(gap>.25f) continue;
                return new TennisRules.InterceptPlan { Found=true,Reachable=true,Point=p,Time=t,Gap=gap };
            }
            return default;
        }
    }
    public sealed partial class TennisGame
    {
        public bool TrackingOverhead { get; private set; }
        public int AutoSmashAttempts { get; private set; }
        bool overheadAttempted;
        /// Power of a smash swing made too early, waiting for the ball to come into range (-1 = none).
        float queuedOverheadPower=-1;
        void FireQueuedOverhead() {
            if(queuedOverheadPower<0) return;
            if(!TrackingOverhead) {
                // The lob came down short of a smash (it bounced, or dropped under overhead height). The swing the player
                // made still plays it: as a groundstroke when the ball arrives, never dropped (2026-10-26: it used to be
                // thrown away and the ball went by untouched).
                float due = BallDueAtRacket();
                if (Player.Swinging || due < 0 || due > TennisRules.SweetTime) return;
                float power = queuedOverheadPower; queuedOverheadPower = -1;
                StartRallySwing(power, 0, 0, 0, false);
                return;
            }
            if(overheadPlan.Time>TennisOverheads.ReadySwing) return;
            TryTrackedOverhead(queuedOverheadPower);   // keeps trying each frame until the player is close enough
        }
        Vector2 overheadStand;
        TennisRules.InterceptPlan overheadPlan;
        bool TryTrackedOverhead(float power)
        {
            if(!TrackingOverhead || overheadAttempted || Player.Swinging || Player.GroundRecovering || DiveActive
                || !incoming || Flow!=Phase.Rally || resetTimer>0 || bounces>0) return false;
            if(overheadPlan.Time>TennisOverheads.EarliestSwing) return false;
            // Early: the swing is kept, and the smash starts itself once the ball is in range.
            if(overheadPlan.Time>TennisOverheads.ReadySwing) { queuedOverheadPower=power; return true; }
            // Late: the ball has already dropped to (or past) contact height; hit it as soon as the arm can get there.
            if(overheadPlan.Time<TennisOverheads.LatestLead) {
                var p=BallPosition; var v=BallVelocity;
                for(float t=0; t<TennisOverheads.LatestLead-.0001f; t+=TennisBall.Step) TennisBall.Integrate(ref p,ref v,BallSpin,TennisBall.Step,ballCurve);
                overheadPlan.Point=p; overheadPlan.Time=TennisOverheads.LatestLead;
            }
            Vector3 cp=Player.ContactPoint(TennisActor.Stroke.Smash,false)-Player.transform.position;
            Vector2 goal=new Vector2(overheadPlan.Point.x-cp.x,overheadPlan.Point.z-cp.z);
            // Allow the last approach step during windup, leaving time for the
            // run-to-smash blend before the ball descends to contact height.
            // Not there yet: keep the swing and fire it as the player closes in; with no time left, lunge for it.
            if(overheadPlan.Time>TennisOverheads.LungeTime
                && Vector2.Distance(goal,new Vector2(Player.transform.position.x,Player.transform.position.z))>.85f) { queuedOverheadPower=power; return true; }
            queuedOverheadPower=-1;
            overheadAttempted=true; overheadStand=goal; AutoSmashAttempts++;
            Player.Swing(Mathf.Clamp01(power),false,TennisActor.Stroke.Smash);
            // A descending lob may need a slower windup than the normal rally
            // pace floor permits; otherwise the racket passes contact too early.
            float rawLate = (Player.TimeToContact - overheadPlan.Time) / SpeedScale;
            Vector2 face = TennisRules.PositionFace(overheadPlan.Point, Player.transform.position, true,
                1 - Mathf.Abs(LateralSpeed) / 10);
            Player.PaceToContact(overheadPlan.Time, .1f); Player.GuideContact(overheadPlan.Point,overheadPlan.Time,face);
            consumedStroke=false;
            // Commit the descending overhead intercept. The ordinary reach assist can
            // otherwise fire early while the ball is still above the racket, re-time
            // the smash to that unreachable point, and consume the only attempt.
            pending = new PendingHit {
                Active = true,
                Hit = TennisRules.AssistedHit(rawLate, 1-TennisRules.FaceError(face), 1, Player.Power, Stamina),
                Face = face, At = overheadPlan.Point, Age = 0, Lead = overheadPlan.Time
            };
            hitLateness = rawLate;
            Feedback="OVERHEAD!";
            return true;
        }
    }
}
