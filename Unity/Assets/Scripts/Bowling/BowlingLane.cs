using UnityEngine;

namespace GolfArcade.Bowling
{
    /// Regulation tenpin lane geometry, in metres (USBC specifications; PLAN_Bowling.md §3.2).
    ///
    /// Lane space: the foul line is z = 0 and +z runs down the lane to the pins; +x is the
    /// bowler's right; y = 0 is the lane surface. Boards are counted from the right-hand edge
    /// (a right-handed bowler's numbering): board 1 is the rightmost, board 20 the centre.
    public static class BowlingLane
    {
        public const float FoulToHeadPin = 18.288f;          // 60 ft, foul line to the centre of pin 1
        public const float Width = 1.0541f;                  // 41.5 in between the gutters
        public const float HalfWidth = Width / 2;
        public const int Boards = 39;
        public const float BoardWidth = Width / Boards;
        public const float GutterWidth = .235f;              // 9 1/4 in, each side
        public const float GutterDepth = .047f;
        public const float HeadPinToPit = .8684f;            // 34 3/16 in, pin 1 centre to the pit edge
        public const float LaneEnd = FoulToHeadPin + HeadPinToPit;
        public const float ApproachLength = 4.57f;           // at least 15 ft behind the foul line
        public const float PinSpacing = .3048f;              // 12 in, centre to centre
        public static readonly float RowSpacing = PinSpacing * Mathf.Sqrt(3) / 2;
        public const float KickbackX = HalfWidth + GutterWidth + .02f;

        // Markings.
        public const float LaneDots = 2.13f;                 // 7 ft
        public const float ArrowsNear = 3.66f, ArrowsFar = 4.88f; // 12-16 ft, centre arrow furthest
        public const float RangeFinders = 10.97f;            // 36 ft
        public static readonly int[] ArrowBoards = { 5, 10, 15, 20, 25, 30, 35 };
        public static readonly float[] ApproachDots = { .15f, 3.66f, 4.57f };

        // The club ball (one for everyone, 14 lb) and a regulation pin.
        public const float BallRadius = .1085f;
        public const float BallMass = 6.35f;
        public const float BallGyration = .0635f;            // RG 2.5 in
        public const float PinHeight = .381f;
        public const float PinMass = 1.59f;                  // 3 lb 8 oz (USBC 3 lb 6 oz – 3 lb 10 oz)
        public const float PinCentreOfMass = .1468f;         // 5 25/32 in above the base (USBC)
        public const float PinGyration = .0947f;             // radius of gyration about a horizontal axis (USBC k² = 13.90 in²)
        public const float PinAxialInertia = .0015f;         // kg m² about the pin's own axis (solid of revolution estimate)

        /// Where the deterministic lane integrator hands the ball to PhysX for the pin action.
        public const float DeckStart = FoulToHeadPin - .40f;

        public static float BoardX(float board) => HalfWidth - (board - .5f) * BoardWidth;
        public static float XBoard(float x) => (HalfWidth - x) / BoardWidth + .5f;

        /// The spot of pin 1..10 (7 at the back left, 10 at the back right).
        public static Vector3 PinSpot(int pin)
        {
            int row = pin <= 1 ? 0 : pin <= 3 ? 1 : pin <= 6 ? 2 : 3;
            int first = row * (row + 1) / 2 + 1;
            float x = ((pin - first) - row * .5f) * PinSpacing;
            return new Vector3(x, 0, FoulToHeadPin + row * RowSpacing);
        }
    }
}
