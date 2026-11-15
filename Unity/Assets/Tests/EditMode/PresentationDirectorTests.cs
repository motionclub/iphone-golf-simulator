using NUnit.Framework;
using GolfArcade.Game;

namespace GolfArcade.Tests
{
    public class PresentationDirectorTests
    {
        /// 2026-10-12 brief: the flyovers slowed down (golf: a tour from the tee to the green, several angles; tennis: still
        /// short), and every character's intro at least 3 s, a longer emote given its time.
        [Test] public void FirstAndRepeatedIntroBudgetsMatchTheBrief()
        {
            foreach (bool golf in new[] { false, true })
            foreach (var cut in new[] { PresentationCut.Full, PresentationCut.Short })
            {
                float duration = PresentationDirector.Budget(PresentationBeat.Venue, golf, cut)
                    + PresentationDirector.Budget(PresentationBeat.WalkOn, golf, cut)
                    + PresentationDirector.Budget(PresentationBeat.Start, golf, cut);
                // 2026-11-11 (plan Phase 1, "cut the waits"): tennis 6.0 / 5.4 s (12.9 / 11.5 before), golf 9.2 / 6.9 s (13.1 / 8.7: its
                // flyover is 4.0 s of that, 7.9 before)
                Assert.AreEqual(golf ? (cut == PresentationCut.Full ? 9.2f : 6.9f) : (cut == PresentationCut.Full ? 6.0f : 5.4f), duration, .001f);
            }
            Assert.AreEqual(HoleIntro.Opening + 3 * HoleIntro.ShotSeconds, PresentationDirector.Budget(PresentationBeat.Venue, true, PresentationCut.Full), .001f, "golf: the opening and three highlights");
            Assert.AreEqual(1.6f, PresentationDirector.Budget(PresentationBeat.Venue, false, PresentationCut.Full), .001f, "tennis's drone stays short");
            Assert.LessOrEqual(GolfArcade.Tennis.TennisPresentation.FullLength, 6f + 1e-4f, "the whole tennis show: six seconds");
            Assert.LessOrEqual(HoleIntro.Length(true), 4f + 1e-4f, "the golf flyover: four seconds");
        }
        /// Each character gets three seconds for their player to tap an emote; none plays unless one is tapped; a tapped
        /// emote is played out.
        [Test] public void EveryIntroductionGivesThreeSecondsAndPlaysAPickedEmoteOut()
        {
            Assert.AreEqual(3f, PresentationDirector.IntroEnd(0, null, 0), .001f, "no pick: the window");
            Assert.AreEqual(4.2f, PresentationDirector.IntroEnd(1.2f, 1.5f, 1f), .001f, "a short emote inside the window");
            Assert.AreEqual(1.2f + 4f + .35f, PresentationDirector.IntroEnd(1.2f, 1.2f, 4f), .001f, "a long emote plays out");
            Assert.AreEqual(2.9f + 3.5f + .35f, PresentationDirector.IntroEnd(0, 2.9f, 3.5f), .001f, "a late pick, still played out");
        }
        [Test] public void ExtendOnlyGrowsARunningBeat()
        {
            var director = new PresentationDirector(); int ready = 0;
            director.Begin(PresentationBeat.WalkOn, PresentationCut.Full, 3.2f, .3f, null, () => ready++);
            director.Tick(2); director.Extend(5); director.Extend(4); Assert.AreEqual(5, director.Duration, 1e-6);
            director.Tick(2.9f); Assert.AreEqual(0, ready); director.Tick(.2f); Assert.AreEqual(1, ready);
            director.Extend(9); Assert.AreEqual(5, director.Duration, 1e-6, "a finished beat stays finished");
        }
        [Test] public void SkippingConsumesTheBeatAndRestoresExactlyOnce()
        {
            var director = new PresentationDirector(); int restored = 0, ready = 0, seen = 0;
            director.Begin(PresentationBeat.WalkOn, PresentationCut.Full, 3, .3f, () => restored++, () => ready++, () => seen++);
            Assert.IsFalse(director.Skip()); director.Tick(.3f); Assert.IsTrue(director.Skip());
            director.Tick(10); director.Cancel(); Assert.IsFalse(director.Skip());
            Assert.AreEqual(1, restored); Assert.AreEqual(1, ready); Assert.AreEqual(0, seen);
        }
        [Test] public void PauseAndCancellationNeverMarkAnIntroSeenOrUnlockPlay()
        {
            var director = new PresentationDirector(); int restored = 0, ready = 0, seen = 0;
            director.Begin(PresentationBeat.Venue, PresentationCut.Full, 3, .3f, () => restored++, () => ready++, () => seen++);
            director.Tick(10, paused: true); Assert.AreEqual(0, director.Elapsed); Assert.IsTrue(director.Playing);
            director.Cancel(); Assert.AreEqual(1, restored); Assert.AreEqual(0, ready); Assert.AreEqual(0, seen);
        }
        [Test] public void SharedBeatsRejectIndividualSkipAndFinishAtTheirCap()
        {
            var director = new PresentationDirector(); int ready = 0;
            director.Begin(PresentationBeat.Venue, PresentationCut.Short, 1.2f, .3f, null, () => ready++, shared: true);
            director.Tick(.8f); Assert.IsFalse(director.Skip()); director.Tick(.4f);
            Assert.AreEqual(1, ready); Assert.IsFalse(director.Playing);
        }
        [Test] public void OffAndThermalFallbackRetainTheSafeStart()
        {
            Assert.AreEqual(PresentationCut.Short, PresentationDirector.Select(PresentationCut.Full, false, false, true));
            Assert.AreEqual(PresentationCut.Short, PresentationDirector.Select(PresentationCut.Full, false, true, false));
            Assert.AreEqual(PresentationCut.Short, PresentationDirector.Select(PresentationCut.Full, true, false, false));
            Assert.AreEqual(0, PresentationDirector.Budget(PresentationBeat.Venue, false, PresentationCut.Off));
            Assert.AreEqual(.8f, PresentationDirector.Budget(PresentationBeat.Start, false, PresentationCut.Off));
            Assert.AreEqual(4, PresentationDirector.GolfReaction(-3, true, PresentationCut.Full));
        }
    }
}
