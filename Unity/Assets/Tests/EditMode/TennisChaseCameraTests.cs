using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    public class TennisChaseCameraTests
    {
        [Test] public void OrdinaryViewMatchesShotAWithLeftOfCentrePlayer()
        {
            var player = new Vector3(0, .035f, -11.2f);
            TennisShoulderCamera.Frame(player, false, new Vector3(1, 1, 8), false, 16f/9,
                out var eye, out var look, out var fov);
            Assert.That(eye.z, Is.EqualTo(player.z - 5.6f).Within(.001f));
            Assert.That(eye.y, Is.EqualTo(3.3f));
            Assert.That(eye.x, Is.EqualTo(.9f));
            Assert.That(fov, Is.EqualTo(48));
            Assert.That(Vector3.Angle(look-eye, Vector3.forward), Is.LessThan(8));
            var cam = new GameObject("Projection test").AddComponent<Camera>();
            try {
                cam.aspect = 16f/9; cam.fieldOfView = fov; cam.transform.position = eye; cam.transform.LookAt(look);
                Assert.That(cam.WorldToViewportPoint(player + Vector3.up).x, Is.InRange(.3f, .49f));
            } finally { Object.DestroyImmediate(cam.gameObject); }
        }

        [Test] public void DeepBallRetreatsOneMetreAndBothHandsKeepTheSightline()
        {
            var player = new Vector3(2, .035f, -11.2f);
            TennisShoulderCamera.Frame(player, false, new Vector3(3, 1, -11), false, 16f/9,
                out var eye, out var look, out var fov);
            Assert.That(player.z-eye.z, Is.EqualTo(6.6f).Within(.001f));
            TennisShoulderCamera.Frame(player, true, new Vector3(3, 1, -11), false, 16f/9,
                out var leftEye, out var leftLook, out var leftFov);
            Assert.AreEqual(eye, leftEye); Assert.AreEqual(look, leftLook); Assert.AreEqual(fov, leftFov);
        }

        [Test] public void CrossCourtBallFitsANarrowSplitScreenHalf()
        {
            var player = new Vector3(-4, .035f, -11.2f);
            var ball = new Vector3(4, 1.5f, -6);
            TennisShoulderCamera.Frame(player, false, ball, false, 8f/9,
                out var eye, out var look, out var fov);
            var cam = new GameObject("Narrow projection test").AddComponent<Camera>();
            try {
                cam.aspect = 8f/9; cam.fieldOfView = fov; cam.transform.position = eye; cam.transform.LookAt(look);
                var v = cam.WorldToViewportPoint(ball);
                Assert.That(v.x, Is.InRange(.04f, .96f)); Assert.Greater(v.z, 0);
            } finally { Object.DestroyImmediate(cam.gameObject); }
        }

        [TestCase(-11.2f, -5f, 8f)]
        [TestCase(-11.2f, -10f, 9f)]
        [TestCase(-2f, -1f, 1.3f)]
        public void LobAndNetBallKeepGroundDepthCueInTheSameFrame(float playerZ, float ballZ, float height)
        {
            var player = new Vector3(0, .035f, playerZ);
            var ball = new Vector3(.95f, height, ballZ);
            var landing = new Vector3(.95f, 0, playerZ + 1);
            TennisShoulderCamera.Frame(player, false, ball, false, 16f/9,
                out var eye, out var look, out var fov, false, landing);
            var cam = new GameObject("Lob projection test").AddComponent<Camera>();
            try {
                cam.aspect = 16f/9; cam.fieldOfView = fov; cam.transform.position = eye; cam.transform.LookAt(look);
                foreach (var point in new[] {ball, new Vector3(ball.x, 0, ball.z), landing}) {
                    var v = cam.WorldToViewportPoint(point);
                    Assert.Greater(v.z, 0); Assert.That(v.y, Is.InRange(.04f, .96f), point.ToString());
                }
                Assert.AreEqual(48, fov, "Lobs dolly smoothly instead of switching lenses");
            } finally { Object.DestroyImmediate(cam.gameObject); }
        }
    }
}
