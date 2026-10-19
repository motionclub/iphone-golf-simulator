using NUnit.Framework;
using UnityEngine;
using GolfArcade.Tennis;

namespace GolfArcade.Tests
{
    public class AnimationSafetyTests
    {
        [Test]
        public void GolfAndTennisUseTheSameEmotePlaybackBudget()
        {
            foreach (string id in TennisEmotes.IDs)
            {
                Assert.IsTrue(TennisEmotes.TryClip(id, out var clip));
                Assert.That(TennisEmotes.PlaybackDuration(clip, 9), Is.EqualTo(TennisEmotes.Duration(id)));
                Assert.That(TennisEmotes.PlaybackDuration(TennisEmotes.ExportName(id), 9), Is.EqualTo(TennisEmotes.Duration(id)));
                Assert.That(TennisEmotes.Duration(id), Is.InRange(2f, 3.6f));
            }
        }

        [Test]
        public void ThrustTimingNeverReversesOrSkipsItsEndpoints()
        {
            float previous = -1;
            for (int i = 0; i <= 600; i++)
            {
                float time = i / 100f;
                float sampled = TennisEmotes.SourceTime(HeroTennisDriver.Clip.EmoteThrust, time, 6);
                Assert.That(sampled, Is.GreaterThan(previous)); previous = sampled;
                Assert.That(sampled, Is.EqualTo(TennisEmotes.SourceTime("Emote_Thrust", time, 6)).Within(.00001f));
            }
            Assert.That(previous, Is.EqualTo(6).Within(.00001f));
            Assert.That(TennisEmotes.SourceTime(HeroTennisDriver.Clip.EmoteThrust, 0, 6), Is.EqualTo(0));
        }

        [Test]
        public void TwoBoneCorrectionPreservesLengthsAndReachesAReachableTarget()
        {
            var root = new GameObject("Arm");
            try
            {
                var lower = new GameObject("Elbow").transform; lower.SetParent(root.transform, false); lower.localPosition = new Vector3(.2f, -.2f, 0);
                var hand = new GameObject("Hand").transform; hand.SetParent(lower, false); hand.localPosition = new Vector3(-.1f, -.2f, .1f);
                float a = lower.localPosition.magnitude, b = hand.localPosition.magnitude;
                var target = new Vector3(.25f, -.22f, .2f);
                HeroPoseSafety.Solve(root.transform, lower, hand, target);
                Assert.That(Vector3.Distance(hand.position, target), Is.LessThan(.0001f));
                Assert.That(Vector3.Distance(root.transform.position, lower.position), Is.EqualTo(a).Within(.00001f));
                Assert.That(Vector3.Distance(lower.position, hand.position), Is.EqualTo(b).Within(.00001f));
            }
            finally { Object.DestroyImmediate(root); }
        }

        [Test]
        public void OrientationChangeRetainsVisiblePoseThenArrivesAtNewPose()
        {
            var root = new GameObject("Model");
            try
            {
                var hips = new GameObject("Hips").transform; hips.SetParent(root.transform, false); hips.localPosition = Vector3.up;
                var hand = new GameObject("Hand").transform; hand.SetParent(hips, false); hand.localPosition = new Vector3(.3f, 0, .2f);
                var start = hand.position; var transition = new HeroPoseTransition(root.transform); transition.Capture(.28f);
                root.transform.rotation = Quaternion.Euler(0, 90, 0);
                transition.Apply();
                Assert.That(Vector3.Distance(start, hand.position), Is.LessThan(.00001f), "Changing the emote coordinate system must not snap the skeleton.");
                hips.localRotation = Quaternion.identity; hips.localPosition = Vector3.up;
                transition.Tick(.28f); transition.Apply();
                Assert.That(Vector3.Distance(root.transform.TransformPoint(new Vector3(.3f, 1, .2f)), hand.position), Is.LessThan(.00001f));
            }
            finally { Object.DestroyImmediate(root); }
        }
    }
}
