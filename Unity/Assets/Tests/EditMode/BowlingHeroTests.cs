using GolfArcade.Bowling;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    /// The bowlers are the real match heroes, with the plaza's walk/run/idle and the standard
    /// reaction emotes the bowling results play.
    public class BowlingHeroTests
    {
        [TestCase(false)]
        [TestCase(true)]
        public void HeroSpawnsWithWalkAndReactions(bool female)
        {
            var hero = BowlingHero.Spawn(null, female, Vector3.zero, 0);
            try
            {
                Assert.IsNotNull(hero, "match hero prefab");
                Assert.IsNotNull(hero.Anim, "HubHeroAnimator attached");
                foreach (var e in new[] { "EmoteFistPump", "EmoteJumpJoy", "EmoteSlump" })
                    Assert.IsTrue(hero.React(e), $"{e} (has: {string.Join(", ", hero.Anim.Emotes)})");
            }
            finally { if (hero) Object.DestroyImmediate(hero.gameObject); }
        }
    }
}
