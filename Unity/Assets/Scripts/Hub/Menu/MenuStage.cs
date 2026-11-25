using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Hub.Menu
{
    /// The pointer menu's 3D half: the plaza camera holds fixed shots (MenuShots) and eases between them; the party's heroes stand
    /// on the line-up's floor slots facing the camera (you in slot 0, friends after you by id), idling and playing their emotes.
    /// Nobody walks: HubWorld runs this instead of its doors, zones and follow camera when the session starts it in menu mode.
    public sealed class MenuStage : MonoBehaviour
    {
        public const float MoveSeconds = .6f, ArrivalSeconds = 1.4f;
        HubWorld world; HubRemotes remotes;
        MenuShots.Shot from, to; float t = 1, seconds = MoveSeconds; bool arrivalHeld;
        Vector3 camPos, camLook; float camFov;
        /// The shot the camera is on, or moving to.
        public string Shot { get; private set; } = MenuShots.Low;
        public bool Moving => t < 1 || arrivalHeld;
        /// Calmer menus (Settings › Reduce motion): no idle drift.
        public static bool ReduceMotion;
        /// The Locker: one hero alone in the middle (you, or on a guest's TV the hero whose locker it is).
        public bool Solo => Shot == MenuShots.Solo;
        /// Friends stand in the line-up: on the plaza everywhere but the Locker; with a venue plate (the squad) only on Home, so the lists left
        /// and the cards right of your hero never stand over a friend (Adnan 11-13: "make sure the characters don't get covered by UI").
        public bool FriendsShown => MenuShots.Centred ? Shot == MenuShots.Low : !Solo;
        /// Friends in the line-up, in slot order (slot 1 onwards).
        public readonly List<string> Friends = new List<string>();
        public int Heroes => 1 + Friends.Count;

        public static MenuStage Attach(HubWorld world)
        {
            var s = world.gameObject.GetComponent<MenuStage>(); if (!s) s = world.gameObject.AddComponent<MenuStage>();
            s.world = world; s.remotes = HubRemotes.For(world); s.remotes.Override = s.Place;
            s.from = s.to = MenuShots.LowShot; s.t = 1;
            s.Stand();
            return s;
        }
        void OnDestroy() { if (remotes) remotes.Override = null; if (world && world.Camera && tanNow >= 0) world.Camera.ResetProjectionMatrix(); }

        /// Move to a shot (`snap`: cut, no move).
        public void GoTo(string shot, bool snap = false)
        {
            var want = MenuShots.For(shot, Heroes);
            if (!snap && shot == Shot && t >= 1 && !arrivalHeld) return;
            arrivalHeld = false;
            from = snap ? want : new MenuShots.Shot("now", camPos, camLook, camFov);
            to = want; Shot = shot; seconds = MoveSeconds; t = snap ? 1 : 0;
            if (snap) Apply(want.position, want.look, want.fov);
        }

        /// A fresh boot: hold the high opening shot until Arrive (the phone's loading screen has faded off the TV).
        public void PrepareArrival()
        {
            from = MenuShots.Centred ? MenuShots.CentreShot : MenuShots.ArrivalShot; to = MenuShots.For(MenuShots.Low, Heroes);   // a backdrop has no swoop Shot = MenuShots.Low; t = 0; seconds = ArrivalSeconds; arrivalHeld = true;
            Apply(from.position, from.look, from.fov);
        }
        public void Arrive() { arrivalHeld = false; }
        public bool Arriving => arrivalHeld || (seconds == ArrivalSeconds && t < 1);

        /// The line-up's members changed (a friend joined or left): re-slot, and re-frame for 3 or 4 heroes.
        void RefreshFriends()
        {
            var ids = remotes ? remotes.Ids : null;
            bool changed = ids == null ? Friends.Count > 0 : ids.Count != Friends.Count;
            if (!changed && ids != null) for (int i = 0; i < ids.Count; i++) if (ids[i] != Friends[i]) { changed = true; break; }
            if (!changed) return;
            Friends.Clear(); if (ids != null) Friends.AddRange(ids);
            if (Friends.Count > 3) Friends.RemoveRange(3, Friends.Count - 3);
            var want = MenuShots.For(Shot, Heroes);
            if (t >= 1 && !arrivalHeld) { from = new MenuShots.Shot("now", camPos, camLook, camFov); to = want; t = 0; seconds = MoveSeconds; }
            else to = want;
        }

        /// Where friend `id` stands (HubRemotes asks every frame): their slot, facing the camera; hidden in the Locker.
        (Vector3 pos, float yaw, bool show)? Place(string id)
        {
            int i = Friends.IndexOf(id);
            if (i < 0) return (Vector3.down * 50, 0, false);
            var slot = MenuShots.Slots[Mathf.Min(i + 1, MenuShots.Slots.Length - 1)];
            return (slot, MenuShots.FacingYaw(slot), FriendsShown);
        }

        /// MENU POSE (Adnan 10-26: "give each character a pose to hold"; "look at overwatch and copy their most simple poses"): each line-up
        /// slot holds one of HubHeroAnimator's stances instead of idling: hands on hips, arms crossed, one hand on the hip, a tall heroic
        /// stand. The Locker shows the plain stand so the clothes are not covered; an emote a player asks for still plays, then the stance returns.
        /// Adnan 10-26: everyone holds the basic stance (Heroic: Soldier: 76 "Classic").
        public static readonly int[] SlotStance = { 3, 3, 3, 3 };
        static void Pose(HubHeroAnimator hero, int slot, bool solo)
        {
            if (!hero) return;
            int want = solo ? -1 : SlotStance[Mathf.Clamp(slot, 0, SlotStance.Length - 1)];
            if (hero.Stance != want) hero.SetStance(want);
        }
        void HoldPoses()
        {
            Pose(world.Player ? world.Player.hero : null, 0, Solo);
            if (remotes) for (int i = 0; i < Friends.Count; i++) Pose(remotes.HeroOf(Friends[i]), i + 1, Solo);
        }

        /// Your hero on slot 0, facing the camera, idle (the stick no longer walks it).
        void Stand()
        {
            var p = world ? world.Player : null; if (!p) return;
            p.locked = true;
            var slot = MenuShots.Slots[0];
            if ((p.transform.position - slot).sqrMagnitude > 1e-4f || Mathf.Abs(Mathf.DeltaAngle(p.Yaw, MenuShots.FacingYaw(slot))) > .5f)
                p.Teleport(slot, MenuShots.FacingYaw(slot));
        }

        /// Called from HubWorld.LateUpdate in menu mode.
        public void Tick(float dt)
        {
            if (!world || !world.Camera) return;
            RefreshFriends();
            Stand();
            if (enabled) HoldPoses();   // (a proof capture disables the stage to pick the stances itself)
            if (!arrivalHeld && t < 1) t = Mathf.Min(1, t + dt / Mathf.Max(.01f, seconds));
            float s = t * t * t * (t * (t * 6 - 15) + 10);   // smootherstep
            var pos = Vector3.Lerp(from.position, to.position, s);
            var look = Vector3.Lerp(from.look, to.look, s);
            float fov = Mathf.Lerp(from.fov, to.fov, s);
            if (!ReduceMotion && !arrivalHeld)
            {
                // breathing: a slow figure-of-eight of a centimetre or two, so a still menu never looks frozen
                float k = Time.unscaledTime;
                pos += new Vector3(Mathf.Sin(k * .37f) * .018f, Mathf.Sin(k * .53f) * .010f, 0);
                look += new Vector3(Mathf.Sin(k * .29f + 1.3f) * .012f, 0, 0);
            }
            Apply(pos, look, fov);
        }

        void Apply(Vector3 pos, Vector3 look, float fov)
        {
            camPos = pos; camLook = look; camFov = fov;
            var c = world.Camera;
            c.transform.SetPositionAndRotation(pos, Quaternion.LookRotation(look - pos, Vector3.up));
            // wider than the TV (a phone held sideways, no TV): keep the TV's width of view, so the backdrop plate (shot at 16:9) and the
            // line-up keep their size and the plate only loses a little sky and floor
            if (MenuShots.Centred && c.aspect > 16f / 9f) fov = 2 * Mathf.Atan(Mathf.Tan(fov * .5f * Mathf.Deg2Rad) * (16f / 9f) / c.aspect) * Mathf.Rad2Deg;
            // an upright phone's Home holds the whole squad (you and the + on every empty spot): the lens opens until the view is
            // UprightHalfWidth wide each side (the backdrop plate fills whatever the lens shows)
            if (MenuShots.Upright && Shot == MenuShots.Low && c.aspect < 1)
                fov = Mathf.Max(fov, 2 * Mathf.Atan(MenuShots.UprightHalfWidth / c.aspect) * Mathf.Rad2Deg);
            c.farClipPlane = 600f;
            Frame(c, fov);
        }

        /// UPRIGHT FRAMING (POLISH 11-24): an upright phone's tall view put the hero's head in the tab bar (Locker, Clubhouse) or stood the squad
        /// mid-screen over an empty floor (Home). The pose stays the one the venue plates were baked from; only the lens moves: off Home it
        /// zooms so the hero runs from just under the tabs to just above the panel, on Home (whose width holds the squad) it only slides the
        /// picture so the feet stand near PLAY. A vertical lens shift (projection [1,2]), eased, so a screen change glides instead of cutting.
        float shiftNow, tanNow = -1;
        void Frame(Camera c, float fov)
        {
            bool home = Shot == MenuShots.Low;
            if (!MenuShots.Upright || c.aspect >= 1 || !world.Player || !MenuHud.UprightHeroBand(home, out float feetVp, out float headVp))
            {
                if (tanNow >= 0) { c.ResetProjectionMatrix(); tanNow = -1; shiftNow = 0; }
                c.fieldOfView = fov; return;
            }
            var view = c.worldToCameraMatrix; var slot = world.Player.transform.position;
            Vector3 f = view.MultiplyPoint(slot), h = view.MultiplyPoint(slot + Vector3.up * 1.86f);   // the cap's top
            float uf = f.y / Mathf.Max(.01f, -f.z), uh = h.y / Mathf.Max(.01f, -h.z);
            float b = 2 * feetVp - 1, tan = Mathf.Tan(fov * .5f * Mathf.Deg2Rad), shift;
            if (home) shift = b - uf / tan;
            else
            {
                float a = 2 * headVp - 1;
                tan = Mathf.Clamp((uh - uf) / Mathf.Max(.05f, a - b), Mathf.Tan(8 * Mathf.Deg2Rad), Mathf.Tan(30 * Mathf.Deg2Rad));
                shift = a - uh / tan;
            }
            if (tanNow < 0) { tanNow = tan; shiftNow = shift; }
            else { float k = 1 - Mathf.Exp(-Time.unscaledDeltaTime * 9f); tanNow = Mathf.Lerp(tanNow, tan, k); shiftNow = Mathf.Lerp(shiftNow, shift, k); }
            float lens = 2 * Mathf.Atan(tanNow) * Mathf.Rad2Deg;
            c.fieldOfView = lens;
            var p = Matrix4x4.Perspective(lens, c.aspect, c.nearClipPlane, c.farClipPlane); p[1, 2] = -shiftNow;
            c.projectionMatrix = p;
        }

        /// Head height of slot n's hero in the world (for name tags), false when that slot is empty or hidden. With the squad the tag sits just
        /// over the cap (1.92 m), so your own tag stays under the tab bar.
        public bool TryHead(int slot, out Vector3 head)
        {
            head = default; float up = MenuShots.Centred ? 1.92f : 2.02f;
            if (slot == 0) { if (!world || !world.Player) return false; head = world.Player.transform.position + Vector3.up * up; return true; }
            if (!FriendsShown || slot - 1 >= Friends.Count) return false;
            head = MenuShots.Slots[slot] + Vector3.up * up; return true;
        }
        /// Spots in the line-up nobody stands on yet (0 when friends are not shown).
        public int EmptySeats => FriendsShown ? Mathf.Max(0, MenuShots.Slots.Length - Heroes) : 0;
        /// Where the k-th empty spot's "+ INVITE" floats (k = 0: the first empty slot).
        public bool TryJoinSeat(int k, out Vector3 at)
        {
            at = default; if (k < 0 || k >= EmptySeats) return false;
            at = MenuShots.Slots[Heroes + k] + Vector3.up * 1.1f; return true;
        }
        public bool TryJoinSeat(out Vector3 at) => TryJoinSeat(0, out at);
        public Vector3 CameraPosition => camPos;
    }
}
