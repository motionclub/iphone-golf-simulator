using GolfArcade.Course;
using GolfArcade.Shot;
using GolfArcade.UI;
using UnityEngine;

namespace GolfArcade.Game
{
    /// Handheld golf only (no TV, the phone upright, NativeSportsSession.Handheld → GolfShotHud.Handheld): the big pin badge
    /// over the game's picture (HolePinMarker), fed every frame while aiming and through the flight. Anything else (the TV, the
    /// intro flyover, the result, a hole loading, the round's end) simply doesn't feed it, and an unfed frame hides it.
    public sealed partial class GolfGame
    {
        HolePinMarker handheldPin;
        MapSkin handheldPinSkin; int handheldPinSkinHole = -1;

        /// Called from Frame, after the map and the TV's pin locator (which handheld play leaves to this).
        void DriveHandheldPin()
        {
            if (!GolfShotHud.Handheld || !NativeControlled || hole == null || !rig || !rig.Camera || !ball) return;
            if (Current != State.Aim && Current != State.Flight) return;
            if (hud.BadgeShowing || rig.Camera.targetDisplay != 0) return;   // (a badge stamped over the picture; never on a TV)
            if (!handheldPin) handheldPin = HolePinMarker.Create(this);
            if (handheldPinSkinHole != hole.Number || handheldPinSkin == null)
            {
                handheldPinSkinHole = hole.Number;
                handheldPinSkin = MapSkin.Golf(Course.Course.Containing(hole.Number)?.Key ?? course?.Key);
            }
            // over the top of the flag when it is in; with the flag out for a short putt, over the cup
            var at = holeView && holeView.FlagTop is Vector3 flagTop ? flagTop : HoleView.ToWorld(hole.Pin, 0.05);
            // from the ball as it is now: in the air too, the number counts down to the pin
            var from = Current == State.Flight && ball.gameObject.activeSelf ? HoleView.ToCourse(ball.position) : ballAt;
            double yards = from.DistanceTo(hole.Pin);
            string distance = club == GolfClub.Putter ? $"{yards * 3:F0} ft" : $"{yards:F0} yd";
            handheldPin.Show(rig.Camera, at, distance, handheldPinSkin);
        }
    }
}
