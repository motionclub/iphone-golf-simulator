using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace GolfArcade.UI
{
    /// Marks a button the phone's joystick can reach on the TV's result screens (the shot result, the hole-out card, the round
    /// card). `Default` is the one that is lit first: the way on.
    public sealed class FocusItem : MonoBehaviour
    {
        public bool Default;
        public static FocusItem Mark(Component button, bool isDefault) { var m = button.GetComponent<FocusItem>() ?? button.gameObject.AddComponent<FocusItem>(); m.Default = isDefault; return m; }
    }

    /// Steers the TV's result-screen buttons from the phone: the joystick (or the pad's arrows) moves a lit ring from button to
    /// button, and the pad's centre taps the one it is on. While a result screen is up one button is always lit (the way on, until
    /// the stick moves), so the phone's tap does what it shows.
    public sealed class MenuFocus : MonoBehaviour
    {
        const float Push = .6f, Rest = .3f, Repeat = .4f;
        static MenuFocus instance;
        FocusItem focus; RectTransform ring; Image ringImage, glow;
        float armed = 1, lastStick = -9, lastMove = -9, popAt = -9;
        readonly List<FocusItem> items = new();

        /// A result screen with buttons is up: the phone's stick steers it instead of the aim.
        public static bool Wants { get { Collect(); return instance && instance.items.Count > 0; } }

        public static MenuFocus Ensure(Transform parent)
        {
            if (instance) return instance;
            instance = new GameObject("Menu focus").AddComponent<MenuFocus>();
            instance.transform.SetParent(parent, false);
            return instance;
        }

        static void Collect()
        {
            if (!instance) instance = FindFirstObjectByType<MenuFocus>();
            if (!instance) return;
            instance.items.Clear();
            foreach (var m in FindObjectsByType<FocusItem>(FindObjectsSortMode.None)) if (m.isActiveAndEnabled && m.gameObject.activeInHierarchy) instance.items.Add(m);
        }

        /// The stick's push (x right, y toward the top of the map); each push past 60% moves one button, and holding it repeats.
        public static void Move(float x, float y)
        {
            if (!Wants) return;
            var f = instance; float now = Time.unscaledTime;
            f.lastStick = now;
            float mag = Mathf.Sqrt(x * x + y * y);
            if (mag < Rest) { f.armed = 1; return; }
            if (mag < Push) return;
            if (f.armed <= 0 && now - f.lastMove < Repeat) return;
            f.armed = 0; f.lastMove = now;
            f.Step(new Vector2(x, y));
        }

        /// One step in a direction (the pad's arrows).
        public static void Step(float x, float y) { if (Wants) instance.Step(new Vector2(x, y)); }

        void Step(Vector2 dir)
        {
            Refocus();
            var positions = items.ConvertAll(i => (Vector2)i.transform.position);
            int from = items.IndexOf(focus);
            int to = Pick(positions, from, dir);
            if (to >= 0 && to != from) { focus = items[to]; popAt = Time.unscaledTime; }
        }

        /// The button the phone's tap presses; false when there is none.
        public static bool Select()
        {
            if (!Wants) return false;
            instance.Refocus();
            var hold = instance.focus ? instance.focus.GetComponent<HoldButton>() : null;
            if (!hold) return false;
            var data = new PointerEventData(EventSystem.current);
            ExecuteEvents.Execute(hold.gameObject, data, ExecuteEvents.pointerDownHandler);
            ExecuteEvents.Execute(hold.gameObject, data, ExecuteEvents.pointerUpHandler);
            instance.popAt = Time.unscaledTime;
            return true;
        }

        void Refocus()
        {
            if (focus && items.Contains(focus)) return;
            focus = items.Find(i => i.Default) ?? (items.Count > 0 ? items[0] : null);
        }

        /// The nearest button in `dir` from `from` (screen positions, y up): along the push first, off the push line counting extra. -1 when nothing is there (so the ring stays put).
        public static int Pick(IList<Vector2> positions, int from, Vector2 dir)
        {
            if (positions.Count == 0) return -1;
            if (from < 0 || from >= positions.Count) return 0;
            if (dir.sqrMagnitude < 1e-6f) return from;
            dir.Normalize();
            bool vertical = Mathf.Abs(dir.y) >= Mathf.Abs(dir.x);
            int best = -1; float bestScore = float.MaxValue;
            for (int i = 0; i < positions.Count; i++)
            {
                if (i == from) continue;
                var d = positions[i] - positions[from];
                float along = Vector2.Dot(d, dir), across = Mathf.Abs(d.x * dir.y - d.y * dir.x);
                // up and down reach any button in that direction (the buttons are wide and sit side by side); sideways keeps to the row
                if (along <= 1e-4f || (!vertical && across > along * 1.6f)) continue;
                float score = vertical ? across + along * .25f : along + across * 2f;   // (up/down: the button nearest the push line)
                if (score < bestScore) { bestScore = score; best = i; }
            }
            return best < 0 ? from : best;
        }

        void Update()
        {
            // a release the phone lost: re-arm after a pause
            if (Time.unscaledTime - lastStick > .25f) armed = 1;
            Collect();
            if (items.Count == 0) { if (ring) { ring.gameObject.SetActive(false); glow.gameObject.SetActive(false); } focus = null; return; }
            Refocus();
            if (!focus) return;
            EnsureRing();
            var rt = (RectTransform)focus.transform;
            if (ring.parent != rt) { ring.SetParent(rt, false); ring.SetAsFirstSibling(); glow.transform.SetParent(rt, false); glow.transform.SetAsFirstSibling(); }   // (both behind the button: its rim)
            var gr = glow.rectTransform; gr.anchorMin = Vector2.zero; gr.anchorMax = Vector2.one; gr.offsetMin = new Vector2(-34, -34); gr.offsetMax = new Vector2(34, 34);
            ring.gameObject.SetActive(true); glow.gameObject.SetActive(true);
            float h = rt.rect.height, pulse = .5f + .5f * Mathf.Sin(Time.unscaledTime * 6f);
            float pop = Mathf.Clamp01(1 - (Time.unscaledTime - popAt) / .25f);
            float grow = 16 + 5 * pulse + 8 * pop;
            ring.offsetMin = new Vector2(-grow, -grow); ring.offsetMax = new Vector2(grow, grow);
            Club.Round(ringImage, h / 2 + grow, false);
            ringImage.color = Color.Lerp(Color.white, new Color(1, 1, 1, 1), pulse);   // (a plain white rim: it reads on grass, sky and the gold alike)
            glow.color = new Color(1, 1, 1, .35f + .25f * pulse);
        }

        void EnsureRing()
        {
            if (ring) return;
            var go = new GameObject("Focus ring", typeof(RectTransform));
            ring = (RectTransform)go.transform;
            ring.anchorMin = Vector2.zero; ring.anchorMax = Vector2.one; ring.pivot = new Vector2(.5f, .5f);
            var g = new GameObject("Focus glow", typeof(RectTransform), typeof(Image));
            glow = g.GetComponent<Image>(); glow.raycastTarget = false; glow.sprite = GlassKit.ShadowSprite; glow.type = Image.Type.Sliced;
            ringImage = go.AddComponent<Image>(); ringImage.raycastTarget = false;
        }
    }
}
