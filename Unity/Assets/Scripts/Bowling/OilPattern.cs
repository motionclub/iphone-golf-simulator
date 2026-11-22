using UnityEngine;

namespace GolfArcade.Bowling
{
    /// Lane friction: the oil pattern. A ball skids on oil (low friction) and grips on the dry
    /// back end (high friction), which is what makes it hook late (PLAN_Bowling.md §3.3).
    ///
    /// The house shot puts more oil in the middle than on the outside boards. A ball that drifts
    /// wide meets drier boards sooner, hooks earlier and is pushed back toward the pocket. That
    /// forgiving "wall" is why ordinary bowlers strike at all.
    public sealed class OilPattern
    {
        public readonly string Name;
        public readonly float Length;          // metres of oil from the foul line
        public readonly float Inside, Outside;  // friction on the oiled middle and outside boards
        public readonly float Dry;              // friction past the oil
        public readonly float WallBoards;       // outside boards (each side) that get less oil
        public const float Taper = 1.5f;        // metres over which the oil fades out

        public OilPattern(string name, float length, float inside, float outside, float dry, float wallBoards)
        {
            Name = name; Length = length; Inside = inside; Outside = outside; Dry = dry; WallBoards = wallBoards;
        }

        /// A long, slick middle and a strong back end: the ball skids straight, then hooks late and
        /// sharply. With position-only aiming (no angle turn) a late hook keeps the hook boards in
        /// reach of the approach while the entry angle stays real (the hook boards are mostly
        /// entry angle × the distance the ball rolls after it finishes hooking).
        public static readonly OilPattern HouseEasy = new OilPattern("House", 13.5f, .006f, .03f, .28f, 8);

        /// 11-21 skill pass: the outside boards keep less of their extra grip (.03 → .012). With the old wall a ball started on
        /// boards 3 to 10 reached the pins within ~1.5 boards of the same spot (a 7-board miss erased); now the same starts spread
        /// over ~5 boards, so where you stand and aim shows. Still a house shot: a little more friction outside than in the middle.
        public static readonly OilPattern HouseSkill = new OilPattern("House", 13.5f, .006f, .012f, .28f, 8);

        /// The house pattern in play (BowlingSkill: the skill lane, or the old forgiving one).
        public static OilPattern House => BowlingSkill.On && !BowlingSkill.EasyLanes ? HouseSkill : HouseEasy;

        public float Friction(float x, float z)
        {
            float board = BowlingLane.XBoard(x);
            float edge = Mathf.Min(board, BowlingLane.Boards + 1 - board);           // boards from the nearer gutter
            float wall = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(WallBoards + 2, WallBoards - 2, edge));
            float oiled = Mathf.Lerp(Inside, Outside, wall);
            float fade = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(Length - Taper, Length, z));
            return Mathf.Lerp(oiled, Dry, fade);
        }
    }
}
