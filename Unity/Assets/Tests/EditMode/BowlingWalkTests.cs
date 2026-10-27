using GolfArcade.Bowling;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// 10-27 (Adnan: "they walk through obstacles"): the walk between the lounge and the approach goes through the aisle the game
    /// pair's sofas leave, on the lounge floor between the dais and the settee step.
    public class BowlingWalkTests
    {
        static readonly Vector3 Seat = new Vector3(-1.1f, 0, BowlingClubLanes.LoungeZ + .3f), Stance = new Vector3(-.2f, 0, BowlingApproach.StartZ);

        [Test]
        public void LoungeToStanceCrossesTheSofaRowInTheAisle()
        {
            var path = BowlingGame.Route(Seat, Stance);
            Assert.NotNull(path);
            Assert.That(path.Count, Is.GreaterThanOrEqualTo(4));
            for (int i = 1; i < path.Count; i++) Assert.Greater(path[i].z, path[i - 1].z, "always toward the lane");
            // every leg that crosses the sofa row (kit sofas, z SofaZ +- .45) runs straight up the aisle
            var all = new System.Collections.Generic.List<Vector3>(path) { Stance };
            all.Insert(0, Seat);
            for (int i = 1; i < all.Count; i++)
            {
                Vector3 a = all[i - 1], b = all[i];
                if (Mathf.Max(a.z, b.z) < BowlingAlleyKit.SofaZ - .45f || Mathf.Min(a.z, b.z) > BowlingAlleyKit.SofaZ + .45f) continue;
                Assert.AreEqual(BowlingGame.AisleX - BowlingGame.AisleSide, a.x, 1e-4f, "going up keeps to its side of the aisle");
                Assert.AreEqual(BowlingGame.AisleX - BowlingGame.AisleSide, b.x, 1e-4f);
            }
            // on the sunken lounge floor between the dais and the step up to the approach
            foreach (var p in path)
                if (p.z < BowlingAlleyKit.ApproachBack - .1f && p.z > BowlingClubLanes.LoungeZ + 1.1f) Assert.AreEqual(BowlingAlleyKit.SetteeFloor, p.y, 1e-4f);
        }

        [Test]
        public void ComingBackKeepsToTheOtherSide()
        {
            var up = BowlingGame.Route(Seat, Stance); var back = BowlingGame.Route(Stance, Seat);
            Assert.AreEqual(up.Count, back.Count);
            for (int i = 0; i < up.Count; i++)
            {
                var u = up[i]; var b = back[back.Count - 1 - i];
                Assert.AreEqual(u.z, b.z, 1e-4f); Assert.AreEqual(u.y, b.y, 1e-4f);
                if (i > 0) Assert.AreEqual(2 * BowlingGame.AisleSide, b.x - u.x, 1e-4f, "the two ways are 54 cm apart");
            }
        }

        [Test]
        public void OnlyTheWaypointsAheadAreKept()
        {
            var mid = new Vector3(BowlingGame.AisleX, BowlingAlleyKit.SetteeFloor, -8f);
            var path = BowlingGame.Route(mid, Stance);
            foreach (var p in path) Assert.Greater(p.z, mid.z);
            Assert.IsNull(BowlingGame.Route(Stance, Stance + Vector3.right * .3f), "a side-step along the approach needs no route");
        }
    }
}
