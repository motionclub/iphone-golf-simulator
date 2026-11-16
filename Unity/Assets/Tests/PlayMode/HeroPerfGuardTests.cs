using System.Collections;
using GolfArcade.CharacterLod;
using GolfArcade.Game;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.PlayTests
{
    /// 2026-11-15 (work/perf-1115, "the game is way laggier now"): the two things that made every frame and every match start
    /// heavier without anyone noticing must fail a test the next time they come back.
    ///   - every hero prefab's meshes are in the shipped distance-LOD cache (54 of 66 were not: every match worked its heroes'
    ///     LODs out again while it was being played);
    ///   - a cloth-corrective component whose profile is not its own switches off (it re-read and decoded a 160–250 KB profile
    ///     every frame, 0.7 MB of garbage per hero per frame);
    /// and the Daily Challenge's opening is its own (its plates, its length), not the hole's.
    public class HeroPerfGuardTests
    {
        static readonly string[] Heroes = { "PlayerMale", "PlayerFemale", "PlayerMaleGolfKit", "PlayerFemaleGolfKit", "PlayerMaleBowlingKit", "PlayerFemaleBowlingKit" };

        [UnityTest, Timeout(600000)]
        public IEnumerator EveryHeroPrefabHitsTheShippedLodCache()
        {
            if (!HeroLod.Enabled) { Assert.Ignore("CHARACTER_LOD=0"); yield break; }
            AudioListener.volume = 0;
            foreach (var name in Heroes)
            {
                var prefab = Resources.Load<GameObject>("Tennis/Customization/" + name);
                Assert.IsNotNull(prefab, name);
                int misses = HeroLodLibrary.CacheMisses, hits = HeroLodLibrary.CacheHits;
                var hero = Object.Instantiate(prefab, new Vector3(0, -400, 0), Quaternion.identity);
                HeroLod lod = null;
                for (float t = 0; t < 90 && !(lod && lod.Ready); t += Time.unscaledDeltaTime) { lod = hero.GetComponent<HeroLod>(); yield return null; }
                Assert.IsTrue(lod && lod.Ready, name + ": its distance LODs are ready");
                Assert.AreEqual(0, HeroLodLibrary.CacheMisses - misses,
                    name + ": a mesh of this hero is not in Resources/CharacterLOD/HeroLodCache.bytes, so every match would work its LODs out while it is played. " +
                    "Bake the cache again: PERF_STEPS=bake work/perf-1115/tools/run_probe.sh bake, then copy runs/bake/HeroLodCache.bytes into Resources/CharacterLOD/.");
                Assert.Greater(HeroLodLibrary.CacheHits - hits, 0, name + ": its big meshes come from the cache");
                Object.Destroy(hero);
                yield return null;
            }
        }

        [UnityTest, Timeout(240000)]
        public IEnumerator ClothCorrectivesNeverReadTheirProfileEveryFrame()
        {
            AudioListener.volume = 0;
            foreach (var name in Heroes)
            {
                var hero = Object.Instantiate(Resources.Load<GameObject>("Tennis/Customization/" + name), new Vector3(0, -400, 0), Quaternion.identity);
                for (int i = 0; i < 90; i++) yield return null;
                var correctives = hero.GetComponent<KitV2PoseCorrectives>();
                if (correctives)
                    Assert.LessOrEqual(correctives.ProfileReads, 1, name + ": KitV2PoseCorrectives read its profile " + correctives.ProfileReads + " times in 90 frames (once, or never)");
                Object.Destroy(hero);
                yield return null;
            }
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator TheDailyChallengeOpensWithItsOwnIntro()
        {
            AudioListener.volume = 0; Time.timeScale = 1;
            yield return SceneManager.LoadSceneAsync("Golf", LoadSceneMode.Single);
            var game = Object.FindFirstObjectByType<GolfGame>(); yield return null;
            float cover = GolfGame.LoadCoverMinimum; GolfGame.LoadCoverMinimum = 0;
            try
            {
                game.SetHoleInOne(DailyHoleInOne.Today());
                game.PrepareNativeAddress(DailyHoleInOne.CourseKey);
                for (float t = 0; game.Current != GolfGame.State.Aim && t < 60; t += Time.unscaledDeltaTime) { if (game.Current == GolfGame.State.Intro) game.NativeContinue(); yield return null; }
                Assert.AreEqual(GolfGame.State.Aim, game.Current, "the first shot is at address");
                // the first shot away: the second one comes up behind the Daily Challenge's loading screen, then its own opening
                game.StrikeToward(game.CurrentHole.Pin);
                bool coverSeen = false, introSeen = false;
                for (float t = 0; t < 120 && !introSeen; t += Time.unscaledDeltaTime)
                {
                    if (game.Current == GolfGame.State.Result) game.NativeContinue();
                    if (game.LoadingHole && game.LoadingCover && game.LoadingCover.Visible && !coverSeen)
                    {
                        coverSeen = true;
                        StringAssert.Contains("DAILY CHALLENGE", game.LoadingCover.Tab);
                        StringAssert.Contains("SHOT 2 OF 3", game.LoadingCover.Tab);
                        Assert.AreEqual("Daily Hole in One", game.LoadingCover.Title);
                        StringAssert.StartsWith("DAILY TIP", game.LoadingCover.TipTab);
                    }
                    if (game.Current == GolfGame.State.Intro && game.PresentationBeatIndex == 0 && game.PresentationElapsed > .2f)
                    {
                        introSeen = true;
                        Assert.AreEqual(GolfGame.DailyIntroSeconds, game.PresentationDuration, .01f, "the Daily Challenge's opening has its own length");
                        StringAssert.StartsWith("SHOT 2 OF 3", game.DailyPlateDetail);
                        StringAssert.Contains(" FT OUT", game.DailyPlateDetail);
                        StringAssert.EndsWith("PTS", game.DailyScoreTitle);
                    }
                    yield return null;
                }
                Assert.IsTrue(coverSeen, "the loading screen between two of the day's shots");
                Assert.IsTrue(introSeen, "the second shot's opening played");
            }
            finally { GolfGame.LoadCoverMinimum = cover; game.SetHoleInOne(0); }
        }
    }
}
