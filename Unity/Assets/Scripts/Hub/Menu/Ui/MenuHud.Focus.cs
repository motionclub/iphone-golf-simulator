using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Hub.Menu
{
    /// ARROW FOCUS (Adnan 10-28: "pivot from the pointer to just an arrow where you can move easily" → arrow-key focus): the leader's phone
    /// sends up / down / left / right and Select instead of a cursor. The gold highlight jumps to the nearest item in that direction (on screen,
    /// chrome included: up from the top of a list reaches the tabs); each screen opens with its first item lit. A finger on a phone with no TV,
    /// and the editor's mouse, still point directly.
    public sealed partial class MenuHud
    {
        /// The TV menu is driven by arrows (the phone sends no cursor); false brings the pointer back.
        public static bool ArrowFocus = true;

        /// One step of the highlight: dx, dy in -1..1 (y up).
        public void Move(int dx, int dy)
        {
            if (!Leader || phoneOpen || (dx == 0 && dy == 0)) return;
            if (hovered == null || !hovered.Visible || !hovered.enabled) { FocusFirst(); return; }
            // Home: down from any + in the squad is PLAY (bottom left), never the tab bar
            if (dy < 0 && dx == 0 && joinSeats.Exists(j => j.item == hovered))
                foreach (var it in Visible()) if (it.id == "play" && it.enabled) { SetHovered(it); clickPulse = -9; return; }
            var from = RectOf(hovered).center; var dir = new Vector2(dx, dy).normalized;
            MenuItem best = null; float bestScore = float.MaxValue;
            foreach (var it in Visible())
            {
                if (it == hovered || !it.enabled) continue;
                var d = RectOf(it).center - from;
                float along = Vector2.Dot(d, dir);
                if (along < 8) continue;   // only what lies that way
                float across = Mathf.Abs(dir.x * d.y - dir.y * d.x);
                // straight ahead wins over a closer item off to the side (a list's next row before the tab bar's neighbour); sideways, the same
                // row wins harder (Home: Invite friends -> PLAY along the bottom, not up to the + JOIN seat between them)
                float score = along + across * (dx != 0 && dy == 0 ? 4f : 2.4f);
                if (score < bestScore) { bestScore = score; best = it; }
            }
            if (best != null) { SetHovered(best); clickPulse = -9; }
        }

        /// Select on the lit item (the phone's big gold button).
        public void SelectFocused()
        {
            if (!Leader || phoneOpen) return;
            if (hovered == null || !hovered.Visible) { FocusFirst(); return; }
            pressedItem = hovered; Click(hovered); pressedItem = null;
        }

        /// The item a screen opens on when it has one thing you came for (11-13: "it's not simple to start a game"): Home's PLAY, the setup's
        /// START and the loader's START MATCH, so Select alone goes Home -> sport -> mode -> start.
        static readonly Dictionary<string, string> Primary = new Dictionary<string, string> { { Home, "play" }, { Setup, "setup-start" }, { Loading, "start" } };

        /// The screen's primary item, else its first enabled item (its lists come first, the chrome after), lit when a screen opens under arrow focus.
        void FocusFirst()
        {
            if (!Leader || phoneOpen) return;
            MenuItem first = null;
            if (Primary.TryGetValue(Screen, out var want)) foreach (var it in Visible()) if (it.id == want && it.enabled) { SetHovered(it); return; }
            if (screenItems.TryGetValue(Screen, out var list)) foreach (var it in list) if (it.Visible && it.enabled) { first = it; break; }
            if (first == null) foreach (var it in Visible()) if (it.enabled) { first = it; break; }
            SetHovered(first);
        }

        /// After a screen change: arrows always have something lit (a pointer starts with nothing under it).
        void FocusAfterShow() { if (ArrowFocus && !touchMode) FocusFirst(); }
        /// The screen's primary item just appeared (the setup built from the phone's options, START MATCH enabled): light it.
        void FocusPrimary() { if (ArrowFocus && !touchMode) FocusFirst(); }
    }
}
