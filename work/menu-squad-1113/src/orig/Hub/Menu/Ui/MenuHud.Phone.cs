using System.Collections.Generic;
using MotionSports.Brand;
using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.Hub.Menu
{
    /// No TV (Adnan 10-29): the menu fills the phone's own screen, held sideways or upright, and follows it when it turns.
    /// Sideways, the TV's 1920×1080 frame sits in the middle of a full-screen backdrop (the phone is wider than 16:9, so the sides
    /// show more venue and clear the notch). Upright, the frame is PortraitW wide and as tall as the screen: the hero stands in the
    /// top part (the camera draws there, PhoneCameraRect) and every screen's lists drop into a panel under it. Of the pop-ups right of
    /// the hero, the ones you pick from move in with the lists (the locker's swatches, the player count, the course strip); the cards
    /// that only show things (the mode clip, the venue card) hide. The chrome keeps to the safe area: wordmark and chips, then the tabs,
    /// at the top, the hint at the bottom.
    public sealed partial class MenuHud
    {
        /// The upright frame's width in canvas units (its height follows the screen): the TV's lists fit across it.
        const float PortraitW = 1000;
        /// The TV rows the upright panel holds, from the headlines down past the setup's START.
        const float PanelFrom = 110, PanelRows = 1000;

        struct PhoneFrame { public bool upright; public float scale, w, h, top, bottom, panelTop; }
        PhoneFrame fitted; bool fittedOnce;
        float tabsFrom;

        static PhoneFrame PhoneLayout()
        {
            float sw = UnityEngine.Screen.width, sh = UnityEngine.Screen.height; var safe = UnityEngine.Screen.safeArea;
            var f = new PhoneFrame { upright = sh > sw };
            if (f.upright)
            {
                f.scale = sw / PortraitW; f.w = PortraitW; f.h = sh / f.scale;
                f.top = Mathf.Max(0, sh - safe.yMax) / f.scale; f.bottom = Mathf.Max(0, safe.y) / f.scale;
                f.panelTop = Mathf.Max(f.top + 560, f.h - f.bottom - PanelRows);
            }
            else { f.scale = Mathf.Min(sh / 1080f, sw / 1920f); f.w = 1920; f.h = 1080; }
            return f;
        }

        /// Where the plaza camera draws on a phone with no TV: the whole screen sideways; upright, down to just under the panel's fade.
        public static Rect PhoneCameraRect()
        {
            if (UnityEngine.Screen.width <= 0) return new Rect(0, 0, 1, 1);
            var f = PhoneLayout();
            if (!f.upright) return new Rect(0, 0, 1, 1);
            float share = Mathf.Clamp01((f.panelTop + 80) / f.h);
            return new Rect(0, 1 - share, 1, share);
        }

        /// Every frame with no TV: the canvas to the screen, and the layout again whenever the phone turned (or its safe area changed).
        void FitPhone()
        {
            var f = PhoneLayout();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ConstantPixelSize; scaler.scaleFactor = f.scale;
            canvasRT.anchorMin = canvasRT.anchorMax = canvasRT.pivot = new Vector2(.5f, .5f);
            canvasRT.sizeDelta = new Vector2(f.w, f.h); canvasRT.anchoredPosition = Vector2.zero;
            if (fittedOnce && f.upright == fitted.upright && Mathf.Abs(f.h - fitted.h) < .5f && Mathf.Abs(f.top - fitted.top) < .5f && Mathf.Abs(f.bottom - fitted.bottom) < .5f) return;
            fittedOnce = true; fitted = f;
            Arrange();
        }

        void Arrange()
        {
            foreach (var root in new List<RectTransform>(decks.Keys)) if (root) ArrangeDeck(root);
            ArrangeChrome(); ArrangePanel();
            if (previewRoot) previewRoot.localScale = fitted.upright ? Vector3.zero : Vector3.one;
            if (wipe) wipe.sizeDelta = new Vector2(1180, fitted.upright ? fitted.h : 1080);
            LayoutLanes();
        }

        // ---- the screens: lists and pop-ups as two decks that move as one
        readonly Dictionary<RectTransform, (RectTransform lists, RectTransform pops)> decks = new Dictionary<RectTransform, (RectTransform, RectTransform)>();

        /// A screen's boxes into its lists (left of the hero) and its pop-ups (right of it, x ≥ 1000); what fills the screen (dims) stays.
        /// `fresh`: the content was just rebuilt (the setup's), and the old decks go with it at the end of the frame.
        void Split(RectTransform root, bool fresh = false)
        {
            if (fresh || !decks.TryGetValue(root, out var d) || !d.lists)
            {
                d = (BrandUi.Fill(root, "Lists"), BrandUi.Fill(root, "Pops")); decks[root] = d;
            }
            var move = new List<RectTransform>();
            foreach (Transform c in root) if (c is RectTransform rt && rt != d.lists && rt != d.pops && rt.anchorMin == rt.anchorMax) move.Add(rt);
            foreach (var rt in move) rt.SetParent(rt.anchoredPosition.x >= 1000 ? d.pops : d.lists, false);
            ArrangeDeck(root);
        }

        void ArrangeDeck(RectTransform root)
        {
            if (!decks.TryGetValue(root, out var d) || !d.lists) return;
            string id = root == setupContent ? Setup : null;
            if (id == null) foreach (var kv in screens) if (kv.Value == root) { id = kv.Key; break; }
            Vector2 lists = Vector2.zero, pops = Vector2.zero; bool hidePops = false;
            if (fitted.upright)
            {
                float dy = fitted.panelTop - PanelFrom;
                lists = new Vector2(0, dy);
                switch (id)
                {
                    case Sport: lists = new Vector2(0, SportDy); break;   // the headline under the tabs, the lanes down the screen (LayoutLanes)
                    case Locker: pops = new Vector2(400 - 1336, dy + 60); break;   // the swatches beside the rail
                    case Players: pops = new Vector2(Left - (RightEdge - 3 * 204 - 2 * 24 - 6), dy + ListTop + 130 - 308); break;   // the counts under the note
                    case Setup: pops = new Vector2(Left - RightX - 12, fitted.panelTop - 150 - (PreviewSetupY + PreviewH + 40)); break;   // the course strip just above the panel
                    default: hidePops = true; break;
                }
            }
            Shift(d.lists, lists, false); Shift(d.pops, pops, hidePops);
        }
        static void Shift(RectTransform deck, Vector2 by, bool hide)
        {
            deck.offsetMin = deck.offsetMax = new Vector2(by.x, -by.y);
            deck.localScale = hide ? Vector3.zero : Vector3.one;
        }

        // the sport lanes upright: from under the headline to above the hint (frame rows, before the deck's shift)
        float SportDy => fitted.top + 190 - 118;
        float UprightLaneTop => fitted.top + 440 - SportDy;
        float UprightLaneBottom => fitted.h - fitted.bottom - 110 - SportDy;

        // ---- the chrome
        /// How far under the frame's top a name tag may ride on a phone (clear of the tabs).
        float PlateCeiling => fitted.upright ? fitted.top + 250 : 150;
        float ChipRight => fitted.upright ? fitted.w - Left : RightEdge;
        float ChipTop => fitted.upright ? fitted.top + 22 : 30;
        readonly Dictionary<RectTransform, (Vector2 pos, Vector2 size)> tvPlace = new Dictionary<RectTransform, (Vector2, Vector2)>();
        /// A box to `upright` (x right, y down from the frame's top-left; `size` if given) on the upright phone, or back where the TV has it.
        void Put(Transform t, Vector2 upright, Vector2? size = null)
        {
            var rt = t as RectTransform; if (!rt) return;
            if (!tvPlace.TryGetValue(rt, out var tv)) tvPlace[rt] = tv = (rt.anchoredPosition, rt.sizeDelta);
            if (fitted.upright) { rt.anchoredPosition = new Vector2(upright.x, -upright.y); rt.sizeDelta = size ?? tv.size; }
            else { rt.anchoredPosition = tv.pos; rt.sizeDelta = tv.size; }
        }
        void ArrangeChrome()
        {
            var f = fitted;
            Put(chrome.Find("Wordmark"), new Vector2(Left, f.top + 18));
            Put(tabBar, new Vector2(Left - 12 - tabsFrom, f.top + 96));
            Put(chrome.Find("Settings"), new Vector2(f.w - Left - 66, f.top + 22));
            if (nameChip) nameChip.anchoredPosition = new Vector2(ChipRight - 66 - 18 - nameChip.sizeDelta.x, -ChipTop);
            Put(hint, new Vector2(Left, f.h - f.bottom - 84));
            // the phone modal in the middle of the tall frame
            float y = f.h * .3f;
            Put(phoneModal.Find("Phone"), new Vector2((f.w - 134) / 2, y));
            Put(phoneModal.Find("Title"), new Vector2(40, y + 256), new Vector2(f.w - 80, 96));
            Put(phoneModal.Find("Body"), new Vector2(40, y + 360), new Vector2(f.w - 80, 40));
            // the side scrims are for words left and right of the hero: upright, the panel behind the lists does that
            foreach (var n in new[] { "Left", "Left fade", "Right fade", "Right" })
            { var s = scrims.Find(n); if (s) s.localScale = f.upright ? Vector3.zero : Vector3.one; }
            // sideways the phone is wider than the frame: the side scrims carry on to the screen's edges, so they never end in a seam
            float wing = Mathf.Max(0, (UnityEngine.Screen.width / Mathf.Max(.01f, f.scale) - 1920) / 2) + 4;
            if (!wingL) { wingL = BrandUi.Layer(BrandUi.Box(scrims, "Wing left", 0, 0, 10, 1080), "Ink", BrandUi.Ink(.86f)); wingR = BrandUi.Layer(BrandUi.Box(scrims, "Wing right", 0, 0, 10, 1080), "Ink", BrandUi.Ink(.8f)); }
            bool wings = HubWorld.PhoneOnly && !f.upright && wing > 4;
            wingL.gameObject.SetActive(wings); wingR.gameObject.SetActive(wings);
            var top = scrims.Find("Top") as RectTransform;   // (the band under the bar too)
            if (top) { top.offsetMin = new Vector2(wings ? -wing : 0, top.offsetMin.y); top.offsetMax = new Vector2(wings ? wing : 0, top.offsetMax.y); }
            if (wings)
            {
                var l = (RectTransform)wingL.transform.parent; l.anchoredPosition = new Vector2(-wing, 0); l.sizeDelta = new Vector2(wing, 1080);
                var r = (RectTransform)wingR.transform.parent; r.anchoredPosition = new Vector2(1920, 0); r.sizeDelta = new Vector2(wing, 1080);
            }
        }
        Image wingL, wingR;

        // the panel behind the upright lists: a fade from the hero's feet into navy, solid under it
        RectTransform panelBg;
        void ArrangePanel()
        {
            if (!fitted.upright) { if (panelBg) panelBg.gameObject.SetActive(false); return; }
            if (!panelBg)
            {
                panelBg = BrandUi.Box(canvasRT, "Panel", 0, 0, PortraitW, 10); panelBg.SetAsFirstSibling();
                var fade = BrandUi.Box(panelBg, "Fade", 0, 0, PortraitW, 240).gameObject.AddComponent<Image>(); fade.raycastTarget = false;
                GolfArcade.Tennis.UiGradient.On(fade, new Color(BrandColors.NavyDeep.r, BrandColors.NavyDeep.g, BrandColors.NavyDeep.b, 0), BrandColors.NavyDeep);
                BrandUi.Layer(panelBg, "Solid", BrandColors.NavyDeep).rectTransform.offsetMax = new Vector2(0, -240);
            }
            panelBg.gameObject.SetActive(true);
            panelBg.anchoredPosition = new Vector2(0, -(fitted.panelTop - 240)); panelBg.sizeDelta = new Vector2(PortraitW, fitted.h - fitted.panelTop + 240);
        }

        // ---- points: the camera may draw in part of the phone, and the frame may not fill it
        /// A point in the plaza camera's viewport to frame units (bottom-left origin).
        Vector2 ViewToFrame(Vector3 vp)
        {
            if (!HubWorld.PhoneOnly || !world || !world.Camera) return new Vector2(vp.x * canvasRT.rect.width, vp.y * canvasRT.rect.height);
            var r = world.Camera.rect;
            return ScreenToFrame(new Vector2((r.x + vp.x * r.width) * UnityEngine.Screen.width, (r.y + vp.y * r.height) * UnityEngine.Screen.height));
        }
        /// A screen pixel to frame units (bottom-left origin).
        Vector2 ScreenToFrame(Vector2 px)
        {
            RectTransformUtility.ScreenPointToLocalPointInRectangle(canvasRT, px, null, out var local);
            return local - canvasRT.rect.min;
        }
    }
}
