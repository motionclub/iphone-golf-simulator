using System.Collections.Generic;
using GolfArcade.Game;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// DAILY SHARE: the Daily Hole in One's shot filming (ShotClips.cs) — the frame fit and the shot's marks the app cuts by.
    public class ShotClipsTests
    {
        readonly List<string> events = new();
        Camera camera;
        double clock;

        [SetUp] public void Up()
        {
            events.Clear(); clock = 100;
            ShotClips.ClockOverride = () => clock;
            ShotClips.EditorEvent = (kind, shot, time, feet, points, holed) => events.Add($"{kind} {shot} {time:0.0} {feet:0.0} {points} {holed}");
            camera = new GameObject("Shot clips test camera").AddComponent<Camera>();
        }

        [TearDown] public void Down()
        {
            ShotClips.Cancel();
            ShotClips.EditorEvent = null; ShotClips.ClockOverride = null;
            Object.DestroyImmediate(camera.gameObject);
        }

        [Test] public void FrameIs16By9AndNeverSquashed()
        {
            ShotClips.Fit(1920, 1080, out var scale, out var offset);
            Assert.AreEqual(Vector2.one, scale); Assert.AreEqual(Vector2.zero, offset);
            // a wider TV picture: the sides are cropped evenly
            ShotClips.Fit(2560, 1080, out scale, out offset);
            Assert.AreEqual(1f, scale.y, 1e-5f); Assert.AreEqual(1080f * 16 / 9 / 2560, scale.x, 1e-5f); Assert.AreEqual((1 - scale.x) / 2, offset.x, 1e-5f);
            // a taller phone picture: the top and bottom are cropped evenly
            ShotClips.Fit(1170, 880, out scale, out offset);
            Assert.AreEqual(1f, scale.x, 1e-5f); Assert.AreEqual(1170f / 880 / (16f / 9), scale.y, 1e-5f); Assert.AreEqual((1 - scale.y) / 2, offset.y, 1e-5f);
            Assert.AreEqual(1280, ShotClips.Width); Assert.AreEqual(720, ShotClips.Height); Assert.AreEqual(30, ShotClips.Fps);
        }

        [Test] public void AShotIsArmedStruckAndRested()
        {
            if (!ShotClips.Supported) Assert.Ignore("no AsyncGPUReadback on this graphics device");
            ShotClips.Arm(camera, 1);
            Assert.AreEqual(1, ShotClips.Shot); Assert.IsTrue(ShotClips.Filming);
            clock = 103.5; ShotClips.Contact();
            clock = 104; ShotClips.Contact();            // a second strike mark is ignored
            clock = 109; ShotClips.Rest(0, 9, 700, false);   // another shot's rest is ignored
            ShotClips.Rest(1, 7.9, 734, false);
            ShotClips.Rest(1, 1, 790, false);            // only the first rest counts
            CollectionAssert.AreEqual(new[] { "Arm 1 100.0 0.0 0 False", "Contact 1 103.5 0.0 0 False", "Rest 1 109.0 7.9 734 False" }, events);
        }

        [Test] public void ArmingAgainOrLeavingCancelsTheShot()
        {
            if (!ShotClips.Supported) Assert.Ignore("no AsyncGPUReadback on this graphics device");
            ShotClips.Arm(camera, 0);
            ShotClips.Arm(camera, 1);
            ShotClips.Cancel();
            CollectionAssert.AreEqual(new[] { "Arm 0 100.0 0.0 0 False", "Cancel 0 100.0 0.0 0 False", "Arm 1 100.0 0.0 0 False", "Cancel 1 100.0 0.0 0 False" }, events);
            Assert.AreEqual(-1, ShotClips.Shot); Assert.IsFalse(ShotClips.Filming);
            ShotClips.Contact(); ShotClips.Rest(1, 0, 1000, true);   // nothing armed: nothing sent
            Assert.AreEqual(4, events.Count);
        }
    }
}
