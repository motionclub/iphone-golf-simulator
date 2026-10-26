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
        void OnDestroy() { if (remotes) remotes.Override = null; }

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
            from = MenuShots.ArrivalShot; to = MenuShots.For(MenuShots.Low, Heroes); Shot = MenuShots.Low; t = 0; seconds = ArrivalSeconds; arrivalHeld = true;
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
            return (slot, MenuShots.FacingYaw(slot), !Solo);
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
            c.fieldOfView = fov; c.farClipPlane = 600f;
        }

        /// Head height of slot n's hero in the world (for name tags), false when that slot is empty or hidden.
        public bool TryHead(int slot, out Vector3 head)
        {
            head = default;
            if (slot == 0) { if (!world || !world.Player) return false; head = world.Player.transform.position + Vector3.up * 2.02f; return true; }
            if (Solo || slot - 1 >= Friends.Count) return false;
            head = MenuShots.Slots[slot] + Vector3.up * 2.02f; return true;
        }
        /// Where the "+ JOIN" seat is: the first empty slot (none when the line-up is full).
        public bool TryJoinSeat(out Vector3 at)
        {
            at = default; int n = Heroes; if (n >= MenuShots.Slots.Length || Solo) return false;
            at = MenuShots.Slots[n] + Vector3.up * 1.1f; return true;
        }
        public Vector3 CameraPosition => camPos;
    }
}
