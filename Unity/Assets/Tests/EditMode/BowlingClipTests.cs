using System.Linq;
using GolfArcade.Bowling;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// BOWLING ANIMATION (work/bowling-anim/PLAN_BowlingAnimation.md): every authored clip exists for both heroes, is a 60 fps clip of the length the Blender
    /// build wrote (gate A11), and the game's helpers pick the right variant.
    public class BowlingClipTests
    {
        [TestCase("Female")]
        [TestCase("Male")]
        public void EveryClipIsThereAt60Fps(string sex)
        {
            var clips = Resources.LoadAll<AnimationClip>("HeroMoves/" + sex).ToDictionary(c => c.name, c => c);
            foreach (var kv in BowlingClips.Frames)
            {
                Assert.IsTrue(clips.TryGetValue(kv.Key, out var c), $"{sex}/{kv.Key} is missing");
                Assert.That(c.frameRate, Is.EqualTo(60f).Within(.01f), $"{sex}/{kv.Key} frame rate");
                Assert.That(c.length * 60f, Is.EqualTo(kv.Value - 1).Within(.6f), $"{sex}/{kv.Key} length in 60 Hz frames");
            }
            foreach (var n in new[] { "Bowl_Approach4", "Bowl_FollowThrough", "Bowl_HandStraight", "Bowl_HandHook", "Bowl_HandBackup" })
            {
                Assert.IsTrue(clips.TryGetValue(n, out var c), $"{sex}/{n} is missing");
                Assert.That(c.frameRate, Is.EqualTo(60f).Within(.01f), $"{sex}/{n} frame rate");
            }
        }

        [TestCase(false)]
        [TestCase(true)]
        public void HeroPlaysTheShotAndItsVariants(bool female)
        {
            var hero = BowlingHero.Spawn(null, female, Vector3.zero, 0);
            try
            {
                Assert.IsNotNull(hero);
                Assert.IsTrue(hero.HasClips, "HubHeroAnimator loads the Bowl_ clips");
                foreach (var id in new[] { BowlingClips.Stance, BowlingClips.Shot, BowlingClips.Abort, BowlingClips.Hook, BowlingClips.Backup, BowlingClips.Early, BowlingClips.Late, BowlingClips.Foul,
                    BowlingClips.DropToe, BowlingClips.DropChase, BowlingClips.DropSpin, BowlingClips.FollowL, BowlingClips.FollowR, "BowlReactStrike", "BowlReactTurkey", "BowlIntro1" })
                    Assert.IsTrue(hero.Anim.Has(id), id);
                Assert.IsTrue(hero.PlayClip(BowlingClips.Shot, 0, false, true));
                Assert.IsTrue(hero.ApproachActive);
                Assert.IsTrue(hero.PlayClip(BowlingClips.Late, 2.2f));
                Assert.That(hero.Anim.ActionTime, Is.EqualTo(2.2f).Within(.01f), "a variant starts where the shot was");
            }
            finally { if (hero) Object.DestroyImmediate(hero.gameObject); }
        }

        [Test]
        public void ReleaseGradesPickTheirVariant()
        {
            var rng = new System.Random(1);
            BowlingThrow T(ReleaseGrade g, float axis = 0) => new BowlingThrow { Grade = g, AxisDeg = axis };
            Assert.AreEqual(BowlingClips.Straight, BowlingClips.ForRelease(T(ReleaseGrade.Perfect), 2f, rng));
            Assert.AreEqual(BowlingClips.Hook, BowlingClips.ForRelease(T(ReleaseGrade.Good, 30), 2f, rng));
            Assert.AreEqual(BowlingClips.Backup, BowlingClips.ForRelease(T(ReleaseGrade.Perfect, -30), 2f, rng));
            Assert.AreEqual(BowlingClips.Early, BowlingClips.ForRelease(T(ReleaseGrade.Early), 1.8f, rng));
            Assert.AreEqual(BowlingClips.Late, BowlingClips.ForRelease(T(ReleaseGrade.Late), 2.2f, rng));
            Assert.AreEqual(BowlingClips.Foul, BowlingClips.ForRelease(T(ReleaseGrade.Foul), 2.25f, rng));
            Assert.AreEqual(BowlingClips.DropToe, BowlingClips.ForRelease(T(ReleaseGrade.Drop), .3f, rng));
            Assert.AreEqual(BowlingClips.DropChase, BowlingClips.ForRelease(T(ReleaseGrade.Drop), .9f, rng));
            Assert.AreEqual(BowlingClips.DropSpin, BowlingClips.ForRelease(T(ReleaseGrade.Drop), 1.4f, rng));
            foreach (var kind in new[] { "Strike", "Turkey", "Spare", "ConvertedSplit", "Gutter", "Split", "SevenTen", "Foul", "Miss", "Win", "Lose" })
                Assert.IsNotNull(BowlingClips.Reaction(kind, rng), kind);
        }
    }
}
