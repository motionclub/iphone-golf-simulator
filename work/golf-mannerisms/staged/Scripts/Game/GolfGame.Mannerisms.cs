using UnityEngine;

namespace GolfArcade.Game
{
    /// Chat B (2026-10-19, Adnan's golf notes): the golfer's mannerisms on chat A's broadcast hooks. After a full shot the golfer
    /// holds the finish, follows the ball with the head and chest, then drops the club in front of the chest
    /// (GolferView.WatchShot). At address the club gets a short waggle, a look down the line and a regrip (GolferView, by itself,
    /// cosmetic only: it never holds up the swing). The hole-out reaction is staged for the behind-the-golfer camera: no golf bag
    /// on the back (it hid the reaction and caught the raised arms), and a 3/4 back view with the lead side to the camera (whatever the cup's angle to the camera), so the
    /// lead arm's fist pump, which is made in front of the chest, is not hidden behind the back (GolferView fits the move to the
    /// clothes as it plays).
    public sealed partial class GolfGame
    {
        /// The hole-out reaction is seen this many degrees off a square back view, turned to the golfer's left (lead side to the camera).
        const float HoleOutTurn = 50f;

        void HookMannerisms()
        {
            PostShotWatch += (g, shot) => { if (g) g.WatchShot(() => ball ? ball.position : (Vector3?)null); };
            HoleOutReactionBegan += (g, shot, move) =>
            {
                if (!g || move == "Idle" || GolferView.MannerismsOff) return;
                g.SetBagCarried(false);
                if (move != "Emote_PickUp") g.TurnFromCamera(HoleOutTurn);   // (the pick-up walks to the cup, back to the camera)
            };
        }
    }
}
