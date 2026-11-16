using System;
using System.Collections.Generic;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Hub.Menu
{
    /// First-launch tips over the live menu (PLAN_Onboarding_v3, Adnan 2026-11-15: "an overlay type tutorial like most games have, not a
    /// dedicated screen onboarding … they are on the main menu and they see directions pop up as an overlay"). The phone decides which tip
    /// shows (OnboardingFlow.coach → menuCoach JSON); this draws it: a card beside the button it is about, a pulsing gold frame round that
    /// button, and the focus held on it.
    ///   action "next":  the card's own NEXT is the only thing Select can press (it reports menuCoach &lt;id&gt; to the phone).
    ///   action "press": only the target can be pressed (PLAY, the LOCKER tab, TUTORIAL, the next lesson); pressing it does what it always does.
    ///   action "hint":  a tip with no hold on the menu (the Locker: pick colours, then BACK).
    /// The same overlay serves the TV and, with no TV, the menu on the phone (a finger taps NEXT or the framed button).
    public sealed partial class MenuHud
    {
        [Serializable] public sealed class CoachTip { public string id = "", kicker = "", title = "", body = "", target = "", action = "next", button = "NEXT"; }
        public CoachTip Coach { get; private set; }
        /// Tests: the tip showing ("" = none).
        public string CoachId => Coach != null ? Coach.id : "";

        RectTransform coachRoot, coachCard, coachFrame, coachNotch, coachFooter, coachNextBox;
        Text coachKicker, coachTitle, coachBody, coachPress, coachNextLabel;
        Image[] coachEdges;
        MenuItem coachNext;
        const float CoachW = 660, CoachPad = 34;

        void BuildCoach()
        {
            coachRoot = BrandUi.Fill(fx, "Coach");
            coachFrame = BrandUi.Box(coachRoot, "Frame", 0, 0, 10, 10);
            coachEdges = new Image[4];
            for (int i = 0; i < 4; i++) { coachEdges[i] = BrandUi.Layer(coachFrame, "Edge " + i, BrandColors.Gold); coachEdges[i].raycastTarget = false; }
            coachCard = BrandUi.Box(coachRoot, "Card", 0, 0, CoachW, 300);
            BrandUi.Skewed(BrandUi.DropShadow(coachCard, 0), 4f, true).color = BrandUi.Ink(.5f);
            BrandUi.Skewed(BrandUi.Layer(coachCard, "Fill", BrandColors.NavyDeep), 4f, true);
            BrandUi.Skewed(BrandUi.Layer(coachCard, "Edge", BrandColors.Gold, -4), 4f, true).transform.SetAsFirstSibling();
            coachNotch = BrandUi.Box(coachCard, "Notch", 0, 0, 34, 34);
            var notch = BrandUi.Layer(coachNotch, "Gold", BrandColors.Gold); notch.raycastTarget = false;
            coachNotch.localRotation = Quaternion.Euler(0, 0, 45);
            coachKicker = BrandUi.Word(BrandUi.Box(coachCard, "Kicker", CoachPad, 26, CoachW - 2 * CoachPad, 32), "Text", "", BrandUi.SemiBold, 24, BrandColors.Gold);
            coachTitle = BrandUi.Label(BrandUi.Box(coachCard, "Title", CoachPad, 60, CoachW - 2 * CoachPad, 60), "Text", "", BrandUi.ExtraBoldItalic, 48, BrandColors.White, TextAnchor.UpperLeft);
            coachBody = BrandUi.Label(BrandUi.Box(coachCard, "Body", CoachPad, 130, CoachW - 2 * CoachPad, 100), "Text", "", BrandUi.Medium, 28, new Color(.863f, .89f, .949f), TextAnchor.UpperLeft);
            foreach (var t in new[] { coachTitle, coachBody }) { t.horizontalOverflow = HorizontalWrapMode.Wrap; t.verticalOverflow = VerticalWrapMode.Overflow; }
            coachFooter = BrandUi.Box(coachCard, "Footer", CoachPad, 240, CoachW - 2 * CoachPad, 56);
            // NEXT: Ⓐ and the word, a menu item of its own (the only one while a "next" tip is up)
            coachNextBox = BrandUi.Box(coachFooter, "Next", 0, 0, 220, 56);
            var face = BrandUi.Fill(coachNextBox, "Face");
            var slash = BrandUi.Slant(face, "Gold", BrandColors.Gold, 14); slash.raycastTarget = false;
            BrandUi.FaceButton(face, "A", 14, 10, 36, BrandColors.NavyInk, BrandColors.Gold);
            coachNextLabel = BrandUi.Word(BrandUi.Box(face, "Label", 62, 0, 150, 56), "Text", "NEXT", BrandUi.ExtraBoldItalic, 30, BrandColors.NavyInk);
            foreach (var s in coachNextLabel.GetComponents<Shadow>()) s.enabled = false;
            coachNext = Item(coachNextBox, face, "coach-next", "Next", CoachNextPressed, 0);
            coachNext.glow = k => face.anchoredPosition = new Vector2(Nudge * .6f * k, 0);
            // "press": how to press the framed button (Ⓐ SELECT on the TV, tap it on the phone)
            coachPress = BrandUi.Word(BrandUi.Box(coachFooter, "Press", 0, 0, CoachW - 2 * CoachPad, 56), "Text", "", BrandUi.SemiBold, 26, BrandColors.Gold);
            coachRoot.gameObject.SetActive(false);
        }

        /// The phone's tip ("" or a CoachTip JSON). The same tip again changes nothing.
        public void SetCoach(string json)
        {
            CoachTip tip = null;
            if (!string.IsNullOrEmpty(json)) { try { tip = JsonUtility.FromJson<CoachTip>(json); } catch (Exception) { } }
            if (tip != null && string.IsNullOrEmpty(tip.id)) tip = null;
            if (tip != null && Coach != null && tip.id == Coach.id && tip.target == Coach.target && tip.title == Coach.title) return;
            Coach = tip;
            if (!coachRoot) return;
            coachRoot.gameObject.SetActive(tip != null);
            if (tip == null) { FocusAfterShow(); return; }
            coachKicker.text = tip.kicker ?? "";
            coachTitle.text = tip.title ?? "";
            coachBody.text = tip.body ?? "";
            bool next = tip.action == "next", press = tip.action == "press";
            coachNextBox.gameObject.SetActive(next);
            coachNextLabel.text = string.IsNullOrEmpty(tip.button) ? "NEXT" : tip.button.ToUpperInvariant();
            coachNextBox.sizeDelta = new Vector2(62 + coachNextLabel.preferredWidth + 34, 56);
            coachPress.gameObject.SetActive(press);
            coachPress.text = HubWorld.PhoneOnly ? "Tap it to go on" : "Press  Ⓐ SELECT";
            LayoutCoach();
            // a tip that holds nothing (the Locker's) lets go of the button the last tip held: the screen's own first item is lit
            if (!CoachFocus() && hovered != null && hovered.id == lastHeld) { SetHovered(null); FocusAfterShow(); }
            lastHeld = CoachHolds ? (Coach.action == "next" ? coachNext.id : Coach.target) : null;
        }
        string lastHeld;

        void CoachNextPressed()
        {
            if (Coach == null || Coach.action != "next") return;
            var id = Coach.id;
            Coach = null; coachRoot.gameObject.SetActive(false);   // (at once: a second Select must not press what is behind it)
            Send("menuCoach", id);
            FocusAfterShow();
        }

        /// The framed target, if the tip has one and it is on screen.
        MenuItem CoachTarget()
        {
            if (Coach == null || string.IsNullOrEmpty(Coach.target)) return null;
            foreach (var it in chromeItems) if (it.id == Coach.target && it.Visible) return it;
            if (screenItems.TryGetValue(Screen, out var list)) foreach (var it in list) if (it.id == Coach.target && it.Visible) return it;
            return null;
        }
        /// While a "next" or "press" tip is up, only its button can be lit or pressed (arrows, a pointer or a finger).
        bool CoachHolds => Coach != null && !phoneOpen && (Coach.action == "next" || (Coach.action == "press" && CoachTarget() != null));
        void CoachRestrict(List<MenuItem> items)
        {
            if (!CoachHolds) return;
            var keep = Coach.action == "next" ? coachNext : CoachTarget();
            items.RemoveAll(it => it != keep);
        }
        /// Lights the tip's button. True when it did (FocusFirst then leaves the focus alone).
        bool CoachFocus()
        {
            if (!CoachHolds) return false;
            var it = Coach.action == "next" ? coachNext : CoachTarget();
            if (it == null) return false;
            if (hovered != it) SetHovered(it);
            return true;
        }

        /// The card beside its target (right of it, else left), or right of the hero with none; the gold frame round the target. Upright on a
        /// phone with no TV (MenuHud.Phone: a 1000-wide frame, the hero above, the lists in a panel below) the card spans the width and
        /// sits above its target (below it when there is no room), or over the hero with none.
        void LayoutCoach()
        {
            if (Coach == null || !coachRoot) return;
            float h = canvasRT.rect.height, w = canvasRT.rect.width;
            bool upright = w < 1200;
            float cw = upright ? Mathf.Min(w - 48, 940) : CoachW, bodyW = cw - 2 * CoachPad;
            foreach (var t in new[] { coachKicker, coachTitle, coachBody, coachPress })
            { var box = (RectTransform)t.transform.parent; box.sizeDelta = new Vector2(bodyW, box.sizeDelta.y); }
            coachFooter.sizeDelta = new Vector2(bodyW, 56);
            Canvas.ForceUpdateCanvases();
            float titleH = Mathf.Max(56, coachTitle.cachedTextGeneratorForLayout.GetPreferredHeight(coachTitle.text, coachTitle.GetGenerationSettings(new Vector2(bodyW, 0))) / coachTitle.pixelsPerUnit);
            float bodyH = string.IsNullOrEmpty(coachBody.text) ? 0 : coachBody.cachedTextGeneratorForLayout.GetPreferredHeight(coachBody.text, coachBody.GetGenerationSettings(new Vector2(bodyW, 0))) / coachBody.pixelsPerUnit;
            ((RectTransform)coachTitle.transform.parent).sizeDelta = new Vector2(bodyW, titleH);
            var bodyBox = (RectTransform)coachBody.transform.parent;
            bodyBox.anchoredPosition = new Vector2(CoachPad, -(64 + titleH + 8)); bodyBox.sizeDelta = new Vector2(bodyW, bodyH);
            bool footer = Coach.action != "hint";
            float cardH = 64 + titleH + 8 + bodyH + (footer ? 26 + 56 : 0) + 30;
            coachFooter.anchoredPosition = new Vector2(CoachPad, -(cardH - 30 - 56));
            coachFooter.gameObject.SetActive(footer);
            coachCard.sizeDelta = new Vector2(cw, cardH);

            var target = CoachTarget();
            coachFrame.gameObject.SetActive(target != null);
            coachNotch.gameObject.SetActive(target != null);
            float x, y;   // the card's top-left, y down
            const float top0 = 110;
            if (target == null)
            {
                x = upright ? (w - cw) / 2 : RightX;
                y = upright ? Mathf.Clamp(h * .16f, top0 + 60, h - 30 - cardH)
                    : Coach.action == "hint" ? h - 40 - cardH : Mathf.Clamp(300, top0, h - 40 - cardH);
            }
            else
            {
                var r = RectOf(target);   // bottom-left origin
                float top = h - r.yMax, bottom = h - r.yMin, mid = (top + bottom) / 2;
                const float pad = 14, gap = 48;
                coachFrame.anchoredPosition = new Vector2(r.xMin - pad, -(top - pad)); coachFrame.sizeDelta = new Vector2(r.width + 2 * pad, r.height + 2 * pad);
                float fw = r.width + 2 * pad, fh = r.height + 2 * pad, t = 5;
                Edge(0, 0, 0, fw, t); Edge(1, 0, fh - t, fw, t); Edge(2, 0, 0, t, fh); Edge(3, fw - t, 0, t, fh);
                if (upright)
                {
                    x = (w - cw) / 2;
                    bool above = top - pad - gap - cardH >= top0 + 60;
                    y = above ? top - pad - gap - cardH : Mathf.Min(bottom + pad + gap, h - 30 - cardH);
                    float nx = Mathf.Clamp((r.xMin + r.xMax) / 2 - x, 40, cw - 40);
                    coachNotch.anchoredPosition = new Vector2(nx - 17, above ? -(cardH - 10) : 10);
                }
                else
                {
                    bool right = r.xMax + pad + gap + cw <= w - 30;
                    x = right ? r.xMax + pad + gap : r.xMin - pad - gap - cw;
                    x = Mathf.Clamp(x, 30, w - 30 - cw);
                    y = Mathf.Clamp(mid - cardH / 2, top0, h - 30 - cardH);
                    float ny = Mathf.Clamp(mid - y, 30, cardH - 30);
                    coachNotch.anchoredPosition = new Vector2(right ? -10 : cw - 24, -(ny - 17));
                }
            }
            coachCard.anchoredPosition = new Vector2(x, -y);
        }
        void Edge(int i, float x, float y, float ew, float eh)
        {
            var rt = coachEdges[i].rectTransform;
            rt.anchorMin = rt.anchorMax = new Vector2(0, 1); rt.pivot = new Vector2(0, 1);
            rt.anchoredPosition = new Vector2(x, -y); rt.sizeDelta = new Vector2(ew, eh);
        }

        /// Per frame: the frame breathes, and follows its target (a screen wipe or a list that moved).
        void CoachTick(float now)
        {
            if (Coach == null || !coachRoot || !coachRoot.gameObject.activeSelf) return;
            if (phoneOpen) { coachRoot.gameObject.SetActive(false); return; }
            float a = .55f + .45f * (.5f + .5f * Mathf.Sin(now * 4.6f));
            foreach (var e in coachEdges) { var c = e.color; c.a = a; e.color = c; }
            if (Time.frameCount % 10 == 0) { LayoutCoach(); CoachFocus(); }
        }
        /// The phone panel closed or a screen changed: a tip that was hidden comes back.
        void CoachAfterShow() { if (Coach != null && coachRoot && !phoneOpen) { coachRoot.gameObject.SetActive(true); LayoutCoach(); CoachFocus(); } }
    }
}
