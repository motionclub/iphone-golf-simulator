using System;
using GolfArcade.Course;
using GolfArcade.Shot;
using UnityEngine;

namespace GolfArcade.Game
{
    /// The shot as a golf broadcast covers it (Adnan, 2026-10-19; CameraRig.BroadcastShot): the post-swing hold behind the
    /// golfer, the ball followed through the air, a landing camera, the post-shot hold on the ball at rest. On a putt the
    /// camera stays behind the golfer and the golfer fades out while the ball rolls; a holed putt brings them back in the same
    /// view to react, seen from behind. No emotes after a shot that stays out (only the hole-out reaction).
    public sealed partial class GolfGame
    {
        /// The golfer has hit a full shot and is watching it go (fired at contact; the golfer holds the finish). Chat B's hook
        /// for the post-shot mannerisms (a stare after the ball, a walk off, a club twirl): play them from here.
        public event Action<GolferView, CourseShot> PostShotWatch;
        /// The ball is in the hole and the golfer reacts with `move` (HoleOutReaction), facing the cup, back to the camera.
        /// Chat B's hook for the hole-out clips.
        public event Action<GolferView, CourseShot, string> HoleOutReactionBegan;

        /// Seconds after a putt's contact the golfer starts to fade, and how long the fade takes (out, and back in on a hole-out).
        const float PuttFadeAfter = .3f, PuttFadeOut = .45f, HoleOutFadeIn = .35f;
        bool puttFaded;

        /// One frame of the shot camera, from FlyBall.
        void BroadcastFrame(Vector3 pos)
        {
            bool putting = club == GolfClub.Putter;
            float toLanding = (float)(LastShot.LandingTime - flightTime);
            rig.BroadcastShot(pos, HoleView.ToWorld(LastShot.Landing), HoleView.ToWorld(LastShot.Rest), HoleView.ToWorld(hole.Pin),
                (float)flightTime, toLanding, (float)LastShot.LandingTime, putting);
            if (putting && !puttFaded && flightTime >= PuttFadeAfter)
            {
                puttFaded = true;
                GolferFade.On(golfer).FadeTo(0, PuttFadeOut);
            }
        }

        /// Contact: a full shot's golfer holds the finish and watches it (the hook for their mannerisms).
        void BroadcastContact()
        {
            puttFaded = false;
            if (club != GolfClub.Putter) PostShotWatch?.Invoke(golfer, LastShot);
        }

        /// The golfer as they were before any putt faded them (a new shot, a new hole, a menu).
        void RestoreGolferFade() { puttFaded = false; if (golfer) { var f = golfer.GetComponent<GolferFade>(); if (f) f.Restore(); } }

        /// The hole-out: the golfer (back in, if a putt faded them) turns to the cup and reacts, seen from behind, in the view the
        /// shot was played from — a putt's camera never moved; any other shot cuts back to it from the landing camera.
        void HoleOutBroadcast(CourseShot shot)
        {
            var cup = HoleView.ToWorld(hole.Pin) - golfer.transform.position; cup.y = 0;
            if (cup.sqrMagnitude > .01f) golfer.transform.rotation = Quaternion.LookRotation(cup.normalized, Vector3.up);
            var reaction = HoleOutReaction(shot);
            golfer.Perform(reaction, loop: reaction == "Idle");
            HoleOutReactionBegan?.Invoke(golfer, shot, reaction);
            var fade = GolferFade.On(golfer);
            if (fade.Opacity < 1 || puttFaded) fade.FadeTo(1, HoleOutFadeIn);
            rig.FrameShotResult();
            if (club != GolfClub.Putter) { rig.SnapNext(); rig.ApplyFrame(); }
        }
    }
}
