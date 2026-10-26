using GolfArcade.Game;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// The tennis lesson's hooks into the match (PLAN_Onboarding_GolfLesson.md): starting it, and the wide feed for its dive
    /// station. The phone runs the court setup first (station 1); the lesson's own stations here are 2–8.
    public sealed partial class TennisGame
    {
        /// Start the lesson from a station (the phone's numbering: 0 is its court setup, 1 the forehand).
        public void BeginLesson(int station)
        {
            var lesson = GetComponent<TennisTutorial>();
            if (!lesson) lesson = gameObject.AddComponent<TennisTutorial>();
            TennisTutorial.StartIndex = Mathf.Clamp(station - 1, 0, TutorialLesson.Steps.Length - 1);
            lesson.Begin(this, coach);
        }

        /// The coach hits one wide of the player, out of normal reach: the dive station's ball.
        public void FeedWide(bool backhandSide, float speed = 13f)
        {
            if (!Player || !Opponent) return;
            bool left = backhandSide != NativeSportsSession.Left;
            float x = Mathf.Clamp(Player.transform.position.x + (left ? -1 : 1) * (TennisRules.DiveGap + 1.1f), -3.9f, 3.9f);
            Vector3 from = Opponent.transform.position + new Vector3(.3f, 1.15f, -.7f);
            Vector3 to = new Vector3(x, TennisRules.BallRadius, TennisRules.BaselineZ + 4.6f);
            Opponent.Swing(.45f, false, TennisActor.Stroke.Drive);
            RallyShots = 1; faultDelay = 0; serveInFlight = false; opponentShot = default;
            InjectBall(from, TennisRules.RallyVelocity(from, to, speed, .3f, .75f));
        }
    }
}
