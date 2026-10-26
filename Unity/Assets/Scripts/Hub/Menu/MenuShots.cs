using UnityEngine;

namespace GolfArcade.Hub.Menu
{
    /// The pointer menu's fixed camera shots and the line-up's floor slots, as plain data (EditMode tests read them without a scene).
    /// Measured on the plaza in work/pointer-menu (MenuLineupCapture): the heroes stand on the paving in front of the clubhouse arch,
    /// facing a low camera south of them, framed on the right so the menu has the left of the screen.
    public static class MenuShots
    {
        public readonly struct Shot
        {
            public readonly string id; public readonly Vector3 position, look; public readonly float fov;
            public Shot(string id, Vector3 position, Vector3 look, float fov) { this.id = id; this.position = position; this.look = look; this.fov = fov; }
            public Shot Shifted(Vector3 move, Vector3 lookMove, float fovAdd) => new Shot(id, position + move, look + lookMove, fov + fovAdd);
        }

        public const string Low = "low", Close = "close", Mid = "mid", Solo = "solo", Arrival = "arrival";

        /// Home: low and heroic, the PLAY tower over the heroes.
        public static readonly Shot LowShot = new Shot(Low, new Vector3(-.45f, .95f, -12.1f), new Vector3(-1.0f, 1.25f, -7.4f), 32f);
        /// Sport, modes, clubhouse: a little closer, chest high.
        public static readonly Shot CloseShot = new Shot(Close, new Vector3(-.5f, 1.3f, -12.4f), new Vector3(-1.0f, 1.12f, -7.4f), 30f);
        /// Loading: further back, so the plaza reads behind the ready line-up.
        public static readonly Shot MidShot = new Shot(Mid, new Vector3(-.6f, 1.6f, -14.0f), new Vector3(-1.2f, 1.2f, -7.4f), 30f);
        /// Locker: your hero alone, centred, head to toe.
        public static readonly Shot SoloShot = new Shot(Solo, new Vector3(-.1f, 1.2f, -11.8f), new Vector3(-.1f, .98f, -7.6f), 30f);
        /// The first look after a fresh boot: high behind the plaza's south edge, the whole plaza and the PLAY tower in shot; the camera
        /// then swoops down to Low.
        public static readonly Shot ArrivalShot = new Shot(Arrival, new Vector3(-4f, 9f, -24f), new Vector3(-.6f, 2.2f, -4f), 42f);

        /// Floor slots, you first. 3 and 4 heroes stand a step further back so the line-up still fits right of the menu.
        public static readonly Vector3[] Slots = { new Vector3(-.1f, 0, -7.6f), new Vector3(.78f, 0, -7.0f), new Vector3(1.6f, 0, -6.45f), new Vector3(2.38f, 0, -5.95f) };
        /// Where every hero faces: the home camera (they do not turn for each shot; the menu's cameras all sit close to it).
        public static Vector3 FaceToward => LowShot.position;

        public static Shot For(string id) => id switch
        {
            Close => CloseShot, Mid => MidShot, Solo => SoloShot, Arrival => ArrivalShot, _ => LowShot,
        };

        /// The shot for a party of `heroes` (1..4): with 3 or 4 the camera eases back and right so the whole line-up is in frame.
        public static Shot For(string id, int heroes)
        {
            var s = For(id);
            if (id == Solo || id == Arrival || heroes <= 2) return s;
            float k = heroes - 2;   // 1 or 2
            return s.Shifted(new Vector3(.55f * k, .12f * k, -1.25f * k), new Vector3(.62f * k, 0, .1f * k), 0);
        }

        public static float FacingYaw(Vector3 slot) { var d = FaceToward - slot; return Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg; }
    }
}
