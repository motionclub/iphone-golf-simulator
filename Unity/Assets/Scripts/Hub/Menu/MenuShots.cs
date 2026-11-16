using UnityEngine;

namespace GolfArcade.Hub.Menu
{
    /// The pointer menu's camera shot and the squad's floor slots, as plain data. The numbers were measured on the walk-around Plaza
    /// the menu first stood on (work/pointer-menu) and the ten venue plates were baked from CentreShot, so none of them may move.
    /// Every screen holds the one centred shot; the shot ids still name what a screen shows (the stage's Solo / FriendsShown logic).
    public static class MenuShots
    {
        public readonly struct Shot
        {
            public readonly string id; public readonly Vector3 position, look; public readonly float fov;
            public Shot(string id, Vector3 position, Vector3 look, float fov) { this.id = id; this.position = position; this.look = look; this.fov = fov; }
        }

        public const string Low = "low", Close = "close", Mid = "mid", Solo = "solo", Arrival = "arrival";

        /// The plaza's home shot. The camera no longer goes there: its position is what every hero faces (FaceToward) and what the
        /// squad and the centred shot are laid out from.
        public static readonly Shot LowShot = new Shot(Low, new Vector3(-.45f, .95f, -12.1f), new Vector3(-1.0f, 1.25f, -7.4f), 32f);
        /// The plaza's fly-in opening shot: only the stage's switched-off arrival move (MenuStage.PrepareArrival) still names it.
        public static readonly Shot ArrivalShot = new Shot(Arrival, new Vector3(-4f, 9f, -24f), new Vector3(-.6f, 2.2f, -4f), 42f);

        /// Where you stand (slot 0).
        static readonly Vector3 Slot0 = new Vector3(-.1f, 0, -7.6f);
        /// Floor slots, you first: the squad.
        public static Vector3[] Slots => SquadSlots;
        /// MENU SQUAD (Adnan 11-13: "lobby shooter style is best", work/menu-lineup-1113): you in the middle at the front, a friend a step back
        /// on each side, the fourth further back on the left; in metres along the camera's right and away from it, from slot 0.
        public static readonly Vector3[] SquadSlots = Squad(new Vector2(0, 0), new Vector2(-1.2f, .75f), new Vector2(1.2f, .75f), new Vector2(-2.4f, 1.75f));
        static Vector3[] Squad(params Vector2[] at)
        {
            var s0 = Slot0; var f = s0 - LowShot.position; f.y = 0; f.Normalize();
            var right = new Vector3(f.z, 0, -f.x);
            var slots = new Vector3[at.Length];
            for (int i = 0; i < at.Length; i++) slots[i] = s0 + right * at[i].x + f * at[i].y;
            return slots;
        }
        /// Where every hero faces: the home camera (they do not turn for each shot; the menu's cameras all sit close to it).
        public static Vector3 FaceToward => LowShot.position;
        /// MENU BACKDROP (Adnan 10-28: "center the character", feet on the floor): every screen holds this one shot, your hero in the
        /// middle, head to toe with floor under the feet; the venue plates were baked from exactly this pose (MenuVenueStand).
        /// `Centred` is always true since the plaza left (MenuBackdrop sets it, plate or no plate); MenuStage still reads it.
        public static bool Centred = true;
        public static readonly Shot CentreShot = Centre();
        static Shot Centre()
        {
            var s = Slot0; var d = FaceToward - s; d.y = 0; d.Normalize();
            return new Shot(Low, s + d * 4.7f + Vector3.up * .95f, s + Vector3.up * 1f, 32f);
        }

        /// The camera's shot for a screen's shot id: always the centred one (the plate's perspective holds for this one pose only).
        public static Shot For(string id) => CentreShot;
        /// The same for a party of `heroes` (1..4).
        public static Shot For(string id, int heroes) => CentreShot;

        public static float FacingYaw(Vector3 slot) { var d = FaceToward - slot; return Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg; }
    }
}
