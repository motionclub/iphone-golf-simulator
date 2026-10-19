using System;
using GolfArcade.Course;
using GolfArcade.Shot;
using UnityEngine;

namespace GolfArcade.Game
{
    public sealed partial class GolfGame
    {
        bool cupFeedback, lipFeedback;
        public double PresentationFlightTime => flightTime;
        public bool ResultCanContinue => Current == State.Result && Time.timeScale > 0 && stateTime >= ResultSkipAfter;
        public float ResultAge => stateTime;
        public bool CompressRunout = true;

        // Playback only: CourseShot and its final ruling are never recomputed or changed.
        float RunoutRate()
        {
            if (!CompressRunout || networkConfigured || LastShot == null || club == GolfClub.Putter
                || flightTime < LastShot.CarryTime + .2 || flightTime >= LastShot.Duration
                || LastShot.IsHoled || LastShot.LippedOut || LastShot.PenaltyStrokes > 0
                || hole.Movers != null || hole.Windmill != null) return 1;
            // Inspect the whole upcoming interval, not just its endpoints, for hazards/ledges.
            double ahead = Math.Max(.5, Time.deltaTime * 2.5);
            foreach (var knock in LastShot.Knocks)
                if (Math.Abs(knock.Time - flightTime) < ahead + .5) return 1;
            double? previousGround = null;
            for (double t = flightTime; t <= flightTime + ahead + CourseShot.SampleInterval; t += CourseShot.SampleInterval)
            {
                var p = LastShot.PositionAt(t);
                var at = new CoursePoint(p.x, p.d);
                var lie = hole.LieAt(at);
                if (p.h > .02 || at.DistanceTo(hole.Pin) < 12
                    || (lie != CourseLie.Fairway && lie != CourseLie.Rough && lie != CourseLie.Green)) return 1;
                double ground = HoleView.GroundHeight(at);
                if (previousGround.HasValue && Math.Abs(ground - previousGround.Value) > .015) return 1;
                if (t == flightTime && Math.Abs(drawnY - (ground + p.h)) > .03) return 1;
                previousGround = ground;
            }
            return 2.5f;
        }

        bool WetLandingRules(CourseLie lie) => (weather == Weather.Rain || weather == Weather.Storm)
            && hole.Rules != null && hole.Rules.Bounce < 1
            && ((lie == CourseLie.Green && hole.Rules.GreenDrag > 1)
                || ((lie == CourseLie.Fairway || lie == CourseLie.Rough) && hole.Rules.FairwayDrag > 1));
    }
}
