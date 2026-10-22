using UnityEngine;

namespace GolfArcade.Tennis
{
    public sealed partial class TennisGame
    {
        TennisActor pendingContactActor;
        Timing pendingContactGrade;
        bool pendingContactHeavy, pendingContactSmash;
        public int PresentedContacts { get; private set; }
        public Vector3 LastPresentedContact { get; private set; }
        void QueueContactPresentation(TennisActor actor, Timing grade, bool heavy, bool smash = false)
        {
            pendingContactActor = actor; pendingContactGrade = grade;
            pendingContactHeavy = heavy; pendingContactSmash = smash;
            actor.GetComponentInChildren<HeroTennisDriver>()?.HoldContactFrame();
        }
        public void FlushContactPresentation()
        {
            if (!pendingContactActor || !fx) return;
            var actor = pendingContactActor; pendingContactActor = null;
            var offset = actor == Player && actor.Kind != TennisActor.Stroke.Serve ? LastFaceOffset : Vector2.zero;
            var at = actor.StringPoint(offset);
            LastPresentedContact = at; PresentedContacts++;
            if (actor == Player) fx.Contact(at, pendingContactGrade, pendingContactHeavy, pendingContactSmash);
            else fx.OpponentContact(at, pendingContactHeavy);
            renderedBall = at + BallVelocity.normalized * (TennisRules.BallRadius * 1.1f);
            if (ball) ball.position = renderedBall;
        }
    }
}
