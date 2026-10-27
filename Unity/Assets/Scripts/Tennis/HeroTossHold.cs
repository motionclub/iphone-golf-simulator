using UnityEngine;
namespace GolfArcade.Tennis
{
    /// The tennis ball in the tossing hand (Adnan 10-27: "for tennis and bowling the ball just takes over their hand, needs actual rigidness").
    /// The serve routine put the ball's centre 4.5 cm from a point on the hand bone's axis, then the toss arm, the clearance pass and the
    /// finger polish all moved the hand after the ball was drawn, with the clip's wrist roll kept: the ball sat in the palm skin and the
    /// fingers curled through it. Here, last (after HeroGripPolish, 1160), while the serve routine has the ball within a few centimetres
    /// of the palm: the palm turns toward the ball, the drawn ball sits on the palm skin (it follows the hand rigidly), the fingers and
    /// thumb close on its surface. As the ball leaves (a bounce, the toss) the hold fades over the last few centimetres, so the drawn ball
    /// slides back onto the game's own ball, whose position the toss and its physics keep using.
    [DefaultExecutionOrder(1170), DisallowMultipleComponent]
    public sealed class HeroTossHold : MonoBehaviour
    {
        public HeroTennisDriver driver;
        HeroBallGrip.Hand grip; bool found;
        float hold, small;
        /// The drawn radius while the ball is in the server's hands. The game's ball is an arcade ball (TennisRules.BallRadius .10 m, a
        /// 20 cm sphere read from the TV) that no hand can close on; in the serve routine it is drawn hand-sized, and grows back to the
        /// game's size over ~0.2 s once tossed (physics never changes).
        public const float HeldRadius = .045f;
        public float Hold => hold;

        void LateUpdate()
        {
            if (!driver || !driver.matchLook || !driver.actor || !driver.game) { hold = 0; return; }
#if UNITY_EDITOR
            if (System.Environment.GetEnvironmentVariable("TOSS_HOLD") == "0") { hold = 0; return; }
#endif
            var look = driver.matchLook; var game = driver.game; var ball = game.BallView;
            if (!ball || game.ReplayPlaying) { hold = 0; return; }
            if (!found) { found = true; grip = HeroBallGrip.Find(look.Bone, true); }
            if (!HeroBallGrip.Valid(grip)) return;
            // hand-sized while the routine holds the ball (bounces included, so it does not pulse), back to full size after the toss
            small = Mathf.MoveTowards(small, game.ServeBallHeld(driver.actor) ? 1 : 0, Time.deltaTime / .2f);
            float r = Mathf.Lerp(TennisRules.BallRadius, HeldRadius, Mathf.SmoothStep(0, 1, small)), skin = HeroBallGrip.PalmSkin(look.female), pad = HeroBallGrip.FingerPad(look.female);
            var at = game.BallPosition;
            float want = 0;
            if (driver.actor.TossReachWanted > .01f && game.BallVelocity.sqrMagnitude < 4f)
            {
                HeroBallGrip.Palm(grip, out var pc, out _, out _, out _);
                float gap = (at - pc).magnitude - r - skin;   // ball surface to palm skin
                want = 1 - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.03f, .07f, gap));
            }
            hold = want;   // no easing: the fade is in the distance itself, and an eased weight would lag the ball off the palm
            if (small > .001f) ball.localScale *= r / TennisRules.BallRadius;   // (TennisGame sets the scale every frame, squash included)
            if (hold <= .001f) return;
            HeroBallGrip.FacePalm(grip, at, hold, 75);
            var seat = HeroBallGrip.Seat(grip, r, skin);
            ball.position = Vector3.Lerp(ball.position, seat, hold);
            HeroBallGrip.Wrap(grip, ball.position, r, pad, hold, true, 80);
        }
    }
}
