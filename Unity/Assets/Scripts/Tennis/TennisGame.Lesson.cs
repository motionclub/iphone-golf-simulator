using GolfArcade.Game;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// The tennis lesson's hook into the match (PLAN_Onboarding_GolfLesson.md): starting it. The phone runs the court setup
    /// first (station 1); the lesson's own stations here are 2–3 (TutorialLesson.Steps).
    public sealed partial class TennisGame
    {
        /// Start the lesson from a station (the phone's numbering: 0 is its court setup, 1 the first ball).
        public void BeginLesson(int station)
        {
            var lesson = GetComponent<TennisTutorial>();
            if (!lesson) lesson = gameObject.AddComponent<TennisTutorial>();
            TennisTutorial.StartIndex = Mathf.Clamp(station - 1, 0, TutorialLesson.Steps.Length - 1);
            lesson.Begin(this, coach);
        }
    }
}
