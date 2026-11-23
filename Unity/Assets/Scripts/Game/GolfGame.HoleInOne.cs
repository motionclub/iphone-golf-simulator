using System;
using System.Globalization;
using GolfArcade.Course;
using GolfArcade.UI;

namespace GolfArcade.Game
{
    /// The Daily Hole in One (DailyHoleInOne.cs) on the course: the closest-to-the-pin contest's one shot a hole, played from the
    /// day's spawn instead of the tee, scored in points, and at the end a card of the three shots, the total out of 3000 and where
    /// it ranks in the world (the phone fetches that from Game Center and sends it back: SetHoleInOneBoard).
    public sealed partial class GolfGame
    {
        /// The day's challenge (yyyymmdd, UTC), set by the app before the round; 0 any other round.
        public int HoleInOneDay { get; private set; }
        bool HoleInOne => HoleInOneDay > 0;
        readonly int[] hioPoints = new int[DailyHoleInOne.Shots];
        readonly double[] hioFeet = new double[DailyHoleInOne.Shots];
        readonly bool[] hioHoled = new bool[DailyHoleInOne.Shots];
        HoleInOneBoard hioBoard;
        bool hioCardUp, hioReported;

        /// The three shots' result, "total=..;s1=..;f1=..;day=.." (the app's DailyHoleInOne.finished).
        public static event Action<string> HoleInOneDone;
        public int HoleInOneTotal { get { int t = 0; foreach (var p in hioPoints) t += p; return t; } }

        /// The next round started here is the day's Daily Hole in One (0: an ordinary round).
        public void SetHoleInOne(int day)
        {
            HoleInOneDay = Math.Max(0, day);
            Array.Clear(hioPoints, 0, hioPoints.Length); Array.Clear(hioHoled, 0, hioHoled.Length);
            for (int i = 0; i < hioFeet.Length; i++) hioFeet[i] = -1;
            hioBoard = null; hioCardUp = hioReported = false;
            if (HoleInOne) SetRoundEvents(false, true, false);   // no twists, rings or bounties: the same three shots for everyone
        }

        /// The world's standing for today's card, from the phone (DailyHoleInOne.swift boardJSON).
        public void SetHoleInOneBoard(string json)
        {
            var board = HoleInOneBoard.Parse(json);
            if (board == null || !HoleInOne) return;
            hioBoard = board;
            if (hioCardUp && Current == State.RoundDone) ShowHoleInOneCard(false);
        }

        /// The setup for the day: one golfer, the day as the seed (the wind and weather everyone gets), one shot a hole.
        void HoleInOneSetup()
        {
            setup = GameSetup.Solo(GolfArcade.Profile.ProfileStore.Active, DailyHoleInOne.CourseKey);
            setup.Seed = HoleInOneDay;
            setup.Format = MatchFormat.ClosestToPin;
        }

        /// One shot scored: where it stopped (feet from the cup; -1 in a hazard or out), its points, and its badge.
        void ScoreHoleInOneShot(CourseShot shot)
        {
            int i = Math.Min(holeIndex, hioPoints.Length - 1);
            double feet = HoleInOneFeet(shot, out bool lost);
            hioHoled[i] = shot.IsHoled; hioFeet[i] = feet; hioPoints[i] = DailyHoleInOne.Score(feet, shot.IsHoled);
            string points = $"+{hioPoints[i].ToString("N0", CultureInfo.InvariantCulture)} POINTS";
            string detail = $"Shot {i + 1} of {DailyHoleInOne.Shots}   ·   {HoleInOneTotal.ToString("N0", CultureInfo.InvariantCulture)} so far";
            if (shot.IsHoled) hud.ShowLanding(LandingBadge.Kind.Holed, "HOLE IN ONE!", detail, points, 3.5f);
            else if (lost) hud.ShowLanding(LandingBadge.Kind.Rough, "No score", detail, shot.Lie == CourseLie.Water ? "In the water" : "Out of bounds", 3f);
            else hud.ShowLanding(feet < 30 ? LandingBadge.Kind.Fairway : LandingBadge.Kind.Rough, $"{feet:F1} ft", detail, points, 3f);
        }

        /// Where a shot stopped, in feet from the cup: 0 holed, -1 in the water or out of bounds.
        double HoleInOneFeet(CourseShot shot, out bool lost)
        {
            lost = shot.Lie is CourseLie.Water or CourseLie.OutOfBounds;
            return shot.IsHoled ? 0 : lost ? -1 : shot.Rest.DistanceTo(hole.Pin) * 3;
        }

        /// DAILY SHARE (ShotClips.cs): each shot is filmed from address to a moment after the ball stops, for the phone's
        /// one-tap share of the day's three shots. Called from Enter.
        void FilmHoleInOne(State s)
        {
            if (!HoleInOne) return;
            int i = Math.Min(holeIndex, DailyHoleInOne.Shots - 1);
            if (s == State.Aim && ShotClips.Shot != i) ShotClips.Arm(GameplayCamera, i);
            else if (s == State.Result && LastShot != null)
            {
                double feet = HoleInOneFeet(LastShot, out _);
                ShotClips.Rest(i, feet, DailyHoleInOne.Score(feet, LastShot.IsHoled), LastShot.IsHoled);
            }
            else if (s is State.Menu or State.Golfer) ShotClips.Cancel();
        }

        /// The round's card: each shot, the total out of 3000 and, once the phone has it, where that stands in the world.
        void ShowHoleInOneCard(bool first)
        {
            hioCardUp = true;
            var inv = CultureInfo.InvariantCulture;
            int total = HoleInOneTotal, n = course.Holes.Length;
            var cells = new string[n];
            for (int h = 0; h < n; h++) cells[h] = h < hioPoints.Length ? hioPoints[h].ToString("N0", inv) : null;
            var rows = new[] { new RoundCard.Row { Name = Match.Current.Name, Color = Lobby.PlayerColor(0), Strokes = new int?[n], Cells = cells } };
            var tiles = new RoundCard.Highlight[Math.Min(n, DailyHoleInOne.Shots) + 1];
            for (int h = 0; h < tiles.Length - 1; h++)
                tiles[h] = new RoundCard.Highlight
                {
                    Icon = hioHoled[h] ? "trophy" : hioFeet[h] < 0 ? "flag" : "target",
                    Title = $"Shot {h + 1}  ·  {course.Holes[h].Name}",
                    Value = $"{DailyHoleInOne.Words(hioFeet[h], hioHoled[h])}  ·  {hioPoints[h].ToString("N0", inv)}",
                };
            tiles[tiles.Length - 1] = new RoundCard.Highlight { Icon = "star", Title = "World ranking", Value = WorldWords() };
            hud.ShowScorecard(Card, "Daily Hole in One", $"{total.ToString("N0", inv)} / {DailyHoleInOne.MaxTotal.ToString("N0", inv)}", tiles, false, rows, "FINISH", showTotal: false);
            hud.PlayAgain.Pressed = () => { };   // one go a day: the phone's Finish ends the round
            hud.RoundMenu.Pressed = ShowMenu;
            if (first) { ReportHoleInOne(); RecordRound(); sounds.PlayReady(); }
        }

        string WorldWords()
        {
            var b = hioBoard;
            if (b == null) return "Ranking you…";
            if (b.Ranked) return $"Top {b.top}%  ·  #{b.rank.ToString("N0", CultureInfo.InvariantCulture)} of {b.players.ToString("N0", CultureInfo.InvariantCulture)}";
            return b.state == "signedOut" ? "Sign in to Game Center" : b.state == "unavailable" ? "Offline" : "Ranking you…";
        }

        /// The day's result to the app, once.
        void ReportHoleInOne()
        {
            if (hioReported) return;
            hioReported = true;
            var inv = CultureInfo.InvariantCulture;
            var parts = new System.Collections.Generic.List<string> { "day=" + HoleInOneDay.ToString(inv), "total=" + HoleInOneTotal.ToString(inv) };
            for (int i = 0; i < hioPoints.Length; i++)
            {
                parts.Add($"s{i + 1}=" + hioPoints[i].ToString(inv));
                parts.Add($"f{i + 1}=" + hioFeet[i].ToString("0.0", inv));
                parts.Add($"h{i + 1}=" + (i < course.Holes.Length ? course.Holes[i].Number : 0).ToString(inv));
            }
            HoleInOneDone?.Invoke(string.Join(";", parts));
        }

        // ----- The Daily Challenge's own opening (2026-11-15, Adnan: "should be different than the regular intros, should mention
        // daily challenge, be focused towards daily challenge"). A hole's flyover glides from its tee down the whole hole under
        // "HOLE n · PAR · YD"; the day's shot starts from a chip to 175 yd out, so its opening is the shot itself: from behind the
        // day's spot toward the flag, then the green close, under a DAILY CHALLENGE plate (which shot, how far, the wind) and a
        // second one with the points (what is up for grabs, then the score so far).

        /// The opening's two shots, seconds: from behind the day's spot, then the green.
        public const float DailyOpening = 1.9f, DailyGreen = .9f;
        public static float DailyIntroSeconds => DailyOpening + DailyGreen;
        /// The Daily Challenge's opening plays instead of the hole's flyover (the overview button still shows the hole).
        bool DailyIntro => HoleInOne && !overviewReturn;
        IntroGraphics.Plate introScorePlate;
        int dailySide = 1;
        /// What the plates say (the tests read them).
        public string DailyPlateDetail { get; private set; } = "";
        public string DailyScoreTitle { get; private set; } = "";

        static float DailyGround(UnityEngine.Vector3 p) => (float)HoleView.GroundHeight(HoleView.ToCourse(p));

        /// Where the opening's first shot stands `e` (0–1) of the way through, on `side` of the line to the flag.
        void DailySpot(float e, int side, out UnityEngine.Vector3 at, out UnityEngine.Vector3 look)
        {
            var b = HoleView.ToWorld(ballAt); var p = HoleView.ToWorld(hole.Pin);
            var dir = p - b; dir.y = 0; dir = dir.sqrMagnitude > .01f ? dir.normalized : UnityEngine.Vector3.forward;
            var right = UnityEngine.Vector3.Cross(UnityEngine.Vector3.up, dir);
            at = b - dir * UnityEngine.Mathf.Lerp(16, 7.5f, e) + right * (side * UnityEngine.Mathf.Lerp(6, 3.4f, e)) + UnityEngine.Vector3.up * UnityEngine.Mathf.Lerp(9.5f, 4.2f, e);
            at.y = UnityEngine.Mathf.Max(at.y, DailyGround(at) + 2.2f);
            look = UnityEngine.Vector3.Lerp(b, p, .72f) + UnityEngine.Vector3.up * 1.2f;
        }

        /// The side of the line the lens flies down: the one with nothing standing in it or between it and the flag.
        void PickDailySide()
        {
            dailySide = 1;
            foreach (int side in new[] { 1, -1 })
            {
                bool clear = true;
                for (int i = 0; i <= 2 && clear; i++)
                {
                    DailySpot(i / 2f, side, out var at, out var look);
                    var to = look - at;
                    clear = !UnityEngine.Physics.CheckSphere(at, .8f, ~0, UnityEngine.QueryTriggerInteraction.Ignore)
                        && !UnityEngine.Physics.Raycast(at, to.normalized, to.magnitude - 3f, ~0, UnityEngine.QueryTriggerInteraction.Ignore);
                }
                if (clear) { dailySide = side; return; }
            }
        }

        /// The Daily Challenge's lens `s` seconds in: shot 0 from behind the day's spot, shot 1 the green (the hole intro's own
        /// green shot, which already finds a clear view of the flag).
        void DailyIntroPose(float s, float aspect, out UnityEngine.Vector3 at, out UnityEngine.Vector3 look, out float fov, out int shot, out float local, out float len)
        {
            if (s >= DailyOpening)
            {
                shot = 1; local = s - DailyOpening; len = DailyGreen;
                holeIntro.Pose(false, HoleIntro.OpeningShort + UnityEngine.Mathf.Min(local / DailyGreen, .999f) * HoleIntro.ShotSeconds, aspect, out at, out look, out fov);
                return;
            }
            shot = 0; local = s; len = DailyOpening;
            float x = UnityEngine.Mathf.Clamp01(s / DailyOpening), e = x * x * x * (x * (x * 6 - 15) + 10);
            DailySpot(e, dailySide, out at, out look);
            fov = 40; if (aspect < 1) fov = UnityEngine.Mathf.Min(78, fov * UnityEngine.Mathf.Lerp(1.6f, 1, aspect));
        }

        /// The plates over the Daily Challenge's opening, in the game's own UI (UI OVERHAUL, 2026-11-16, Adnan: "use the same UI we
        /// use for in game now, but just name it daily challenge"): DAILY CHALLENGE lettered into the hole's course plate where a
        /// round's map title stands, this shot's facts on its cream tab; the points on a second plate in the other corner.
        void ShowDailyPlates()
        {
            if (introGraphics == null) return;
            var inv = CultureInfo.InvariantCulture;
            var skin = GolfArcade.UI.MapSkin.Golf(Course.Course.Containing(hole.Number)?.Key ?? course?.Key);
            string wind = WeatherWords(Wind.IsCalm ? "Calm" : Wind.Describe(heading)).ToUpperInvariant();
            // (kept short: the two plates' tabs share the foot of the screen, and a storm's wind words are long)
            DailyPlateDetail = $"SHOT {holeIndex + 1} OF {DailyHoleInOne.Shots}  ·  {ballAt.DistanceTo(hole.Pin).ToString("F0", inv)} YD OUT  ·  {wind}";
            introPlate = introGraphics.ShowWordTitle(skin, "DAILY CHALLENGE", false, introClock, 250, false, DailyPlateDetail);
            bool first = holeIndex == 0;
            DailyScoreTitle = (first ? DailyHoleInOne.MaxTotal : HoleInOneTotal).ToString("N0", inv) + " PTS";
            // (on an upright phone the points stand over the challenge's corner, not beside it: the two tabs would meet)
            introScorePlate = introGraphics.ShowWordTitle(skin, DailyScoreTitle, true, introClock, 170, false,
                first ? $"UP FOR GRABS  ·  ACE {DailyHoleInOne.Holed.ToString("N0", inv)}" : "YOUR SCORE SO FAR", introGraphics.Portrait ? 440 : -1);
        }
        void HideDailyPlates() { introGraphics?.HidePlate(introScorePlate, introClock); introScorePlate = null; }

        /// What the loading screen between two of the day's shots says (HoleLoadingCover): the challenge, not the hole's par and yards.
        HoleLoadingCover.Info DailyLoadingInfo(HoleLoadingCover.Info info, int index)
        {
            var inv = CultureInfo.InvariantCulture;
            info.Tab = $"DAILY CHALLENGE  ·  SHOT {index + 1} OF {DailyHoleInOne.Shots}";
            info.Title = "Daily Hole in One";
            info.Objective = index == 0
                ? "Three shots, each longer: a chip, a 100-yard pitch, a long iron. Closest scores most: hole it for 1,000."
                : $"{HoleInOneTotal.ToString("N0", inv)} points so far. Next: {info.Course}, {info.Name}.";
            info.Chips = new[] { $"{HoleInOneTotal.ToString("N0", inv)} / {DailyHoleInOne.MaxTotal.ToString("N0", inv)} PTS", (info.Course ?? "").ToUpperInvariant(), DailyHoleInOne.BandWords(index) };
            info.TipTab = "DAILY TIP";
            info.Tips = DailyTips;
            return info;
        }
        /// The tips the Daily Challenge's loading screens show (the phone's are the same words: GameTips.daily in HowToCards.swift).
        public static readonly (string title, string text)[] DailyTips =
        {
            ("Every foot counts", "A miss scores up to 800, and every foot closer to the cup is worth more. Hole it for the full 1,000."),
            ("Same shots for everyone", "The whole world plays these three shots today. Your first go is the one that counts."),
            ("Find the flag", "The cup is cut somewhere new every day. Check the shot map before you pick your line."),
            ("Mind the wind", "On the long shot the wind moves the ball a lot. Read the arrow, then aim off."),
            ("Club up as you go", "Each shot is longer: a soft chip, a wedge from 100, then a mid iron. Pick the club for the yards."),
            ("Stay dry", "Water, lava and out of bounds score nothing for that shot. A safe miss still scores."),
        };

        /// The round's tally for the app's XP: a hole in one counts as an ace, nothing else as birdies or pars.
        string HoleInOneSummary()
        {
            var inv = CultureInfo.InvariantCulture;
            int aces = 0; foreach (var h in hioHoled) if (h) aces++;
            return string.Join(";", "toPar=0", "strokes=" + course.Holes.Length.ToString(inv), "par=" + course.Holes.Length.ToString(inv),
                "holes=" + course.Holes.Length.ToString(inv), "aces=" + aces.ToString(inv), "eagles=0", "birdies=0", "pars=0",
                "coins=0", "rings=0", "bounties=0", "bountyHoles=0", "rough=0", "twists=0", "daily=0", "course=" + DailyHoleInOne.CourseKey,
                "holeInOne=" + HoleInOneTotal.ToString(inv));
        }
    }
}
