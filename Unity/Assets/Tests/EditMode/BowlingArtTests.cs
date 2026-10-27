using GolfArcade.Bowling;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// The installed ball and pin import the way the game assumes (work/bowling-ball-pin README):
    /// metres, +Y up, identity transforms, pin base at y = 0, ball centred, hulls readable.
    public class BowlingArtTests
    {
        static Bounds WorldBounds(GameObject go)
        {
            var rs = go.GetComponentsInChildren<Renderer>();
            var b = rs[0].bounds;
            foreach (var r in rs) b.Encapsulate(r.bounds);
            return b;
        }

        [Test]
        public void PinStandsOnItsBaseAtRegulationHeight()
        {
            Assert.IsTrue(BowlingArt.HasPin, "Resources/Bowling/Pin.fbx");
            var go = BowlingArt.Pin(null);
            try
            {
                var b = WorldBounds(go);
                Assert.AreEqual(0, b.min.y, .003f);
                Assert.AreEqual(BowlingLane.PinHeight, b.max.y, .003f);
                Assert.AreEqual(.121f, b.size.x, .004f);
                Assert.AreEqual(0, b.center.x, .002f); Assert.AreEqual(0, b.center.z, .002f);
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void BallIsCentredAndRegulationSize()
        {
            Assert.IsTrue(BowlingArt.HasBall, "Resources/Bowling/Ball_Club.fbx");
            var go = BowlingArt.Ball(null);
            try
            {
                var b = WorldBounds(go);
                Assert.AreEqual(Vector3.zero.magnitude, b.center.magnitude, .003f);
                Assert.AreEqual(BowlingLane.BallRadius * 2, b.size.y, .004f);
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void PinHullsAreTheInstalledReadableOnes()
        {
            var hulls = BowlingArt.PinHulls();
            Assert.AreEqual(3, hulls.Length);
            foreach (var h in hulls) { Assert.IsTrue(h.isReadable, h.name); Assert.That(h.name, Does.StartWith("UCX_Pin")); }
            Assert.AreEqual(0, hulls[0].bounds.min.y, .003f);
            Assert.AreEqual(BowlingLane.PinHeight, hulls[2].bounds.max.y, .003f);
        }
    }
}
