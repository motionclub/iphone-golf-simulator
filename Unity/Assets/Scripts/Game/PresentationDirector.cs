using System;

namespace GolfArcade.Game
{
    public enum PresentationCut { Full, Short, Off }
    public enum PresentationBeat { None, Loading, Venue, WalkOn, Start, Point, Game, Set, HoleOut, MatchEnd, Exit }

    /// Shared timing/input policy. Sport adapters own camera and actor choreography;
    /// this clock never awards a point, advances a hole, or changes simulation speed.
    public sealed class PresentationDirector
    {
        public PresentationBeat Beat { get; private set; }
        public PresentationCut Cut { get; private set; }
        public float Elapsed { get; private set; }
        public float Duration { get; private set; }
        public float SkipFrom { get; private set; }
        public int Sequence { get; private set; }
        public bool Playing { get; private set; }
        public bool Shared { get; private set; }
        public float Fraction => Duration <= 0 ? 1 : Math.Min(1, Elapsed / Duration);
        Action cleanup, ready, markSeen;

        public static PresentationCut Select(PresentationCut preference, bool seen, bool multiplayer, bool constrained) =>
            preference == PresentationCut.Off ? PresentationCut.Off : multiplayer || constrained || seen ? PresentationCut.Short : preference;

        /// Each character's introduction gives their player this long to pick an emote on the phone; nobody emotes unless
        /// their player picks one, and a picked emote is played out (the introduction runs on to its end and a breath after).
        public const float IntroWindow = 3f, EmoteSettle = .35f;
        /// Golf: the look over the golfer's shoulder down the hole before they turn to the camera.
        public const float GolfOverShoulder = 1.2f;
        /// Tennis: each player's introduction, and the stare-down across the net after both. The whole show is 6 s since
        /// 2026-11-11 (12.9 s before: 3 s each and a 2.5 s stare); a picked emote still gets its time on top.
        public const float TennisIntroWindow = 1.2f, TennisStare = 1.0f;
        /// Tennis: the drone in to the court, the full cut and the short one, and the swoop into play.
        public const float TennisDrone = 1.6f, TennisDroneShort = 1.2f, TennisSwoop = 1.0f;
        /// When a character's introduction can end: its window, or its emote played out (`emoteStart` null: none picked).
        public static float IntroEnd(float windowStart, float? emoteStart, float emoteLength, float window = IntroWindow)
            => emoteStart is float s ? Math.Max(windowStart + window, s + emoteLength + EmoteSettle) : windowStart + window;
        public static float Budget(PresentationBeat beat, bool golf, PresentationCut cut)
        {
            bool full = cut == PresentationCut.Full;
            if (cut == PresentationCut.Off && (beat == PresentationBeat.Venue || beat == PresentationBeat.WalkOn)) return 0;
            return beat switch {
                // golf: the hole's opening and its highlights (HoleIntro); tennis: the drone in to the court
                PresentationBeat.Venue => golf ? HoleIntro.Length(full) : (full ? TennisDrone : TennisDroneShort),
                // the shortest the character introductions run (golf: over the shoulder, then the golfer's window; tennis: both
                // players' windows and the stare-down) — a picked emote is given its time on top
                PresentationBeat.WalkOn => golf ? GolfOverShoulder + IntroWindow : 2 * TennisIntroWindow + TennisStare,
                PresentationBeat.Start => golf ? (full ? 1 : .6f) : (full ? TennisSwoop : .8f),
                PresentationBeat.Point => full ? 1.2f : .8f,
                PresentationBeat.Game => full ? 2.5f : 1.5f,
                PresentationBeat.Set => full ? 4 : 2.5f,
                PresentationBeat.HoleOut => full ? 1.2f : 1f,   // 2.5 / 1.5 until 2026-11-11
                PresentationBeat.MatchEnd => full ? 6 : 3,
                PresentationBeat.Exit => full ? 1 : .8f,
                _ => 0,
            };
        }
        public static float GolfReaction(int strokesToPar, bool holeInOne, PresentationCut cut)
        {
            bool full = cut == PresentationCut.Full;
            if (holeInOne) return full ? 4 : 3;
            if (strokesToPar <= -2) return full ? 2 : 1.2f;
            if (strokesToPar == -1) return full ? 1.5f : 1;
            return strokesToPar == 0 ? (full ? .8f : .5f) : (full ? .6f : .5f);
        }
        public void Begin(PresentationBeat beat, PresentationCut cut, float duration, float skipFrom,
            Action restore, Action readyState, Action seen = null, bool shared = false)
        {
            Cancel(); Sequence++; Beat = beat; Cut = cut; Duration = Math.Max(0, duration);
            Elapsed = 0; SkipFrom = Math.Max(0, skipFrom); Shared = shared;
            cleanup = restore; ready = readyState; markSeen = seen; Playing = true;
            if (Duration == 0) Finish(false);
        }
        public void Tick(float elapsedSeconds, bool paused = false)
        {
            if (!Playing || paused || float.IsNaN(elapsedSeconds) || float.IsInfinity(elapsedSeconds) || elapsedSeconds < 0) return;
            Elapsed = Math.Min(Duration, Elapsed + elapsedSeconds);
            if (Elapsed >= Duration) Finish(false);
        }
        /// Run on to at least `duration` (a longer emote chosen while the beat plays).
        public void Extend(float duration) { if (Playing && !float.IsNaN(duration)) Duration = Math.Max(Duration, duration); }
        public bool Skip()
        {
            if (!Playing || Shared || Beat == PresentationBeat.Loading || Beat == PresentationBeat.Exit || Elapsed < SkipFrom) return false;
            Finish(true); return true;
        }
        public void Cancel()
        {
            if (!Playing) return;
            Playing = false; var restore = cleanup; cleanup = ready = markSeen = null; restore?.Invoke();
        }
        void Finish(bool skipped)
        {
            if (!Playing) return;
            Playing = false;
            var restore = cleanup; var go = ready; var seen = markSeen;
            cleanup = ready = markSeen = null;
            restore?.Invoke();
            if (!skipped && Cut == PresentationCut.Full) seen?.Invoke();
            go?.Invoke();
        }
    }
}
