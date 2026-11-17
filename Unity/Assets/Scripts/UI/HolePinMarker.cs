using UnityEngine;
using UnityEngine.UI;

namespace GolfArcade.UI
{
    /// Handheld golf (the phone held upright, the game in its top three quarters, NativeSportsSession.Handheld): the flag is a
    /// speck in that small portrait picture, so the hole gets a big pin badge drawn over the game: a flag in a cream disc with
    /// the course's ink rim, the distance on an ink pill under it ("142 yd", "18 ft" on the green), and a tail pointing down at
    /// the flag. When the pin is out of the picture (off to a side, or behind the camera) the badge waits at the edge of the
    /// game's view nearest it, clear of the corner cards and the golfer, with an arrow pointing the way.
    ///
    /// Its own canvas on the gameplay camera (Screen Space - Camera, so it sizes to the camera's viewport: only the game's part
    /// of the screen), sorted over the broadcast cards (GolfShotHud, 35) and under the result panels (ShotResultPanel 50,
    /// HoleOutCard 55). GolfGame calls `Show` every frame it wants it; a frame without that call hides it (a hole loading, the
    /// round over, the state moved on), so it can never be left standing over the wrong hole.
    [DefaultExecutionOrder(1000)]   // (LateUpdate after the camera rig's, so the badge sits on this frame's picture)
    public sealed class HolePinMarker : MonoBehaviour
    {
        const int SortOrder = 40;
        // In canvas units: the canvas is 1080 wide on an upright phone (as GolfShotHud scales its own).
        const float Disc = 128, Rim = 9, Halo = 176, TailW = 38, TailH = 28, PillH = 52, PillOverlap = 14, ArrowGap = 22, EdgeMargin = 24;
        static float R => Disc / 2 + Rim;
        /// From the disc's centre down to the pill's foot.
        static float BodyDown => R - PillOverlap + PillH;
        /// The reach of the arrow past the disc's centre, at the edge.
        static float ArrowReach => R + ArrowGap + 22;
        static readonly Color FlagRed = UiKit.Hex("E8352F");

        MonoBehaviour owner;
        Canvas canvas; CanvasScaler scaler; CanvasGroup group;
        RectTransform root, body, pill, tail, arrow, halo;
        Image ring, disc, pole, pennant, foot, pillFace, tailImage, arrowImage, haloImage;
        Outline arrowRim;
        Text label;
        MapSkin skin;

        // what GolfGame asked for this frame
        int fedFrame = -1;
        Camera view; Vector3 pin; string text;
        float shownSince;

        /// Builds the marker (hidden). It removes itself when `owner` (the golf game) is gone.
        public static HolePinMarker Create(MonoBehaviour owner)
        {
            var go = new GameObject("Hole pin marker (handheld)", typeof(RectTransform));
            var m = go.AddComponent<HolePinMarker>();
            m.owner = owner;
            m.canvas = go.AddComponent<Canvas>();
            m.canvas.renderMode = RenderMode.ScreenSpaceOverlay;   // (Screen Space - Camera once a camera is fed)
            m.canvas.sortingOrder = SortOrder;
            m.scaler = go.AddComponent<CanvasScaler>();
            m.scaler.uiScaleMode = CanvasScaler.ScaleMode.ConstantPixelSize;
            m.Build();
            return m;
        }

        void Build()
        {
            root = new GameObject("Pin badge", typeof(RectTransform)).GetComponent<RectTransform>();
            root.SetParent(transform, false);
            root.sizeDelta = Vector2.zero;
            group = root.gameObject.AddComponent<CanvasGroup>();
            group.blocksRaycasts = false; group.interactable = false;

            // the tail first, so the disc and pill draw over its root; its tip is the root's origin
            tailImage = Shape(root, "Tail", Triangle, Color.black, new Vector2(TailW, TailH));
            tail = tailImage.rectTransform; tail.pivot = new Vector2(.5f, 1);

            body = new GameObject("Body", typeof(RectTransform)).GetComponent<RectTransform>();
            body.SetParent(root, false); body.sizeDelta = Vector2.zero;

            haloImage = Shape(body, "Halo", UiKit.Circle, new Color(1, 1, 1, .3f), new Vector2(Halo, Halo));
            halo = haloImage.rectTransform;
            ring = Shape(body, "Rim", UiKit.Circle, Color.black, new Vector2(Disc + 2 * Rim, Disc + 2 * Rim));
            var drop = ring.gameObject.AddComponent<Shadow>(); drop.effectColor = new Color(0, 0, 0, .35f); drop.effectDistance = new Vector2(0, -6);
            disc = Shape(body, "Disc", UiKit.Circle, Color.white, new Vector2(Disc, Disc));

            // the flag: a stick from a little cup up past the middle, a red pennant flying from its top
            const float poleX = -18, poleBottom = -38, poleTop = 40;
            foot = Shape(body, "Cup", UiKit.Circle, Color.black, new Vector2(40, 12));
            foot.rectTransform.anchoredPosition = new Vector2(poleX, poleBottom);
            pole = Shape(body, "Stick", null, Color.black, new Vector2(9, poleTop - poleBottom));
            pole.rectTransform.pivot = new Vector2(.5f, 0); pole.rectTransform.anchoredPosition = new Vector2(poleX, poleBottom);
            pennant = Shape(body, "Pennant", Triangle, FlagRed, new Vector2(38, 50));   // (an up triangle turned to point right)
            pennant.rectTransform.localRotation = Quaternion.Euler(0, 0, -90);
            pennant.rectTransform.anchoredPosition = new Vector2(poleX + 4 + 25, poleTop - 19);

            // the distance on an ink pill under the disc
            pillFace = Shape(body, "Distance pill", UiKit.Rounded, Color.black, new Vector2(150, PillH));
            pillFace.type = Image.Type.Sliced; pillFace.pixelsPerUnitMultiplier = .85f;
            pill = pillFace.rectTransform; pill.anchoredPosition = new Vector2(0, -R + PillOverlap - PillH / 2);
            label = new GameObject("Distance", typeof(RectTransform)).AddComponent<Text>();
            label.transform.SetParent(pill, false);
            label.font = MapSkin.Bold; label.fontSize = 40; label.alignment = TextAnchor.MiddleCenter; label.raycastTarget = false;
            label.horizontalOverflow = HorizontalWrapMode.Overflow; label.verticalOverflow = VerticalWrapMode.Overflow;
            var lr = label.rectTransform; lr.anchorMin = Vector2.zero; lr.anchorMax = Vector2.one; lr.offsetMin = lr.offsetMax = Vector2.zero;

            // the way to an out-of-sight pin: an ink arrow with a cream rim, round the disc's edge
            arrowImage = Shape(root, "Arrow", Triangle, Color.black, new Vector2(52, 44));
            arrow = arrowImage.rectTransform;
            arrowRim = arrowImage.gameObject.AddComponent<Outline>(); arrowRim.effectDistance = new Vector2(3, -3);

            Paint(MapSkin.Golf(null));
            root.gameObject.SetActive(false);
        }

        static Image Shape(Transform parent, string name, Sprite sprite, Color color, Vector2 size)
        {
            var img = new GameObject(name, typeof(RectTransform)).AddComponent<Image>();
            img.transform.SetParent(parent, false);
            img.sprite = sprite; img.color = color; img.raycastTarget = false;
            var rt = img.rectTransform; rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(.5f, .5f);
            rt.sizeDelta = size; rt.anchoredPosition = Vector2.zero;
            return img;
        }

        /// The course's colours: a cream disc, its ink rim, stick and pill, the course's light as the halo.
        void Paint(MapSkin s)
        {
            if (s == null || s == skin) return;
            skin = s;
            var ink = new Color(s.Ink.r, s.Ink.g, s.Ink.b, 1);
            ring.color = ink; pole.color = ink; foot.color = ink; pillFace.color = ink; tailImage.color = ink; arrowImage.color = ink;
            disc.color = s.Cream; label.color = s.Cream; arrowRim.effectColor = s.Cream;
            haloImage.color = new Color(s.Glow.r, s.Glow.g, s.Glow.b, .35f);
        }

        /// Wanted this frame: over `pinWorld` (the top of the flag, or the cup) on `camera`'s picture, `distance` on its pill.
        /// Call it every frame the badge should show; a frame without the call hides it.
        public void Show(Camera camera, Vector3 pinWorld, string distance, MapSkin courseSkin)
        {
            if (!camera) return;
            if (fedFrame < Time.frameCount - 1 || !root.gameObject.activeSelf) shownSince = Time.unscaledTime;
            fedFrame = Time.frameCount; view = camera; pin = pinWorld; text = distance;
            Paint(courseSkin);
        }

        void LateUpdate()
        {
            if (!owner) { Destroy(gameObject); return; }
            bool on = fedFrame == Time.frameCount && view && view.isActiveAndEnabled;
            if (root.gameObject.activeSelf != on) root.gameObject.SetActive(on);
            if (on) Place();
        }

        void Place()
        {
            // the canvas on the game's camera: its viewport is the game's part of the phone
            if (canvas.renderMode != RenderMode.ScreenSpaceCamera || canvas.worldCamera != view)
            {
                canvas.renderMode = RenderMode.ScreenSpaceCamera; canvas.worldCamera = view; canvas.planeDistance = .6f;
                canvas.sortingOrder = SortOrder;
            }
            canvas.targetDisplay = view.targetDisplay;
            var px = view.pixelRect;
            float scale = Mathf.Max(.1f, view.aspect < 1.2f ? px.width / 1080f : px.height / 1080f);
            scaler.scaleFactor = scale; canvas.scaleFactor = scale;
            float W = px.width / scale, H = px.height / scale;
            if (W < 1 || H < 1) return;

            // the phone's notch and rounded corners, where they cut into the game's view
            float top = 0, left = 0, right = 0;
            if (view.targetDisplay == 0 && !view.targetTexture)
            {
                var safe = Screen.safeArea;
                top = Mathf.Max(0, px.yMax - safe.yMax) / scale;
                left = Mathf.Max(0, safe.xMin - px.xMin) / scale;
                right = Mathf.Max(0, px.xMax - safe.xMax) / scale;
            }

            label.text = text ?? "";
            pill.sizeDelta = new Vector2(Mathf.Max(122, label.preferredWidth + 40), PillH);
            float halfW = Mathf.Max(R, pill.sizeDelta.x / 2);

            float t = Time.unscaledTime;
            group.alpha = Mathf.Clamp01((t - shownSince) / .18f);
            float pulse = .5f + .5f * Mathf.Sin(t * 3.4f);
            halo.localScale = Vector3.one * (.88f + .2f * pulse);
            haloImage.color = new Color(haloImage.color.r, haloImage.color.g, haloImage.color.b, .42f - .22f * pulse);

            var vp = view.WorldToViewportPoint(pin);
            bool behind = vp.z < 0;
            bool obscured = !GolfArcade.EnvironmentArt.DreamVisibility.Visible(pin);
            var p = new Vector2(vp.x * W, vp.y * H);
            var centre = new Vector2(W / 2, H / 2);

            // Over the pin: the whole badge must fit inside the view, a little in from the sides.
            float yTop = H - top - EdgeMargin;
            bool inView = !behind && !obscured
                && p.x > left + EdgeMargin + halfW && p.x < W - right - EdgeMargin - halfW
                && p.y > EdgeMargin && p.y < yTop;
            if (inView)
            {
                float above = TailH + BodyDown - 6;   // the disc's centre over the tip, the badge standing on the flag
                bool flip = p.y + above + R > yTop;   // too near the top: hang it under the pin, the tail pointing up
                if (flip && p.y - (TailH + R - 6) - BodyDown < EdgeMargin) flip = false;
                Anchor(p, W, H);
                tail.gameObject.SetActive(true); arrow.gameObject.SetActive(false);
                tail.localRotation = flip ? Quaternion.identity : Quaternion.Euler(0, 0, 180);
                body.anchoredPosition = new Vector2(0, flip ? -(TailH + R - 6) : above);
                return;
            }

            // At the edge, pointing the way. The way: to the pin's projection; behind the camera that projection is mirrored
            // through the middle; in fog only a rough bearing (the fog's game is not to see the pin).
            Vector2 d = p - centre;
            if (behind) d = -d;
            if (obscured)
            {
                var bearing = pin - GolfArcade.EnvironmentArt.DreamVisibility.Observer; bearing.y = 0;
                float angle = Mathf.Round(Mathf.Atan2(bearing.x, bearing.z) * Mathf.Rad2Deg / 30) * 30;
                var coarse = view.transform.InverseTransformDirection(Quaternion.Euler(0, angle, 0) * Vector3.forward);
                d = new Vector2(coarse.x, coarse.z * .55f) * W;
            }
            if (d.sqrMagnitude < 1e-4f) d = new Vector2(0, 1);
            float xMin = left + EdgeMargin + Mathf.Max(halfW, ArrowReach), xMax = W - right - EdgeMargin - Mathf.Max(halfW, ArrowReach);
            float yMin = EdgeMargin + Mathf.Max(BodyDown, ArrowReach), yMax = H - top - EdgeMargin - ArrowReach;
            if (xMax < xMin) xMin = xMax = W / 2;
            if (yMax < yMin) yMin = yMax = H / 2;
            float tx = d.x > 0 ? (xMax - centre.x) / d.x : d.x < 0 ? (xMin - centre.x) / d.x : float.MaxValue;
            float ty = d.y > 0 ? (yMax - centre.y) / d.y : d.y < 0 ? (yMin - centre.y) / d.y : float.MaxValue;
            var at = centre + d * Mathf.Max(0, Mathf.Min(tx, ty));
            // the corners' cards at the top (the hole card left, the wind dial right): down the side, under them
            const float CardsDown = 330, CardsIn = 380;
            if ((at.x < left + CardsIn || at.x > W - right - CardsIn) && at.y > H - top - CardsDown - R)
                at.y = Mathf.Max(yMin, H - top - CardsDown - R);
            // the golfer and the ball, bottom middle: off to the side of them
            float keepOut = W * .3f;
            if (at.y < H * .42f && Mathf.Abs(at.x - centre.x) < keepOut)
                at.x = Mathf.Clamp(centre.x + (d.x < 0 ? -keepOut : keepOut), xMin, xMax);
            Anchor(at, W, H);
            tail.gameObject.SetActive(false); arrow.gameObject.SetActive(true);
            body.anchoredPosition = Vector2.zero;
            // the arrow aims from where the badge sits to the pin (or the mirrored / rough way), nudging out in time
            var target = behind || obscured ? centre + d * 1e4f : p;
            var dir = target - at;
            if (dir.sqrMagnitude < 1e-4f) dir = d;
            dir.Normalize();
            arrow.anchoredPosition = dir * (R + ArrowGap + 6 * pulse);
            arrow.localRotation = Quaternion.Euler(0, 0, Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg - 90f);
        }

        /// The root's origin at `at` (canvas units from the view's bottom left), by anchors: right however the canvas is sized.
        void Anchor(Vector2 at, float W, float H)
        {
            root.anchorMin = root.anchorMax = new Vector2(at.x / W, at.y / H);
            root.anchoredPosition = Vector2.zero;
        }

        static Sprite triangle;
        /// A plain triangle pointing up the screen, white, anti-aliased, for tinting and turning.
        static Sprite Triangle
        {
            get
            {
                if (triangle) return triangle;
                const int n = 64;
                var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear, name = "Pin marker triangle" };
                var px = new Color32[n * n];
                for (int y = 0; y < n; y++)
                    for (int x = 0; x < n; x++)
                    {
                        int inside = 0;
                        for (int sy = 0; sy < 4; sy++)
                            for (int sx = 0; sx < 4; sx++)
                            {
                                float u = (x + (sx + .5f) / 4) / n - .5f, v = (y + (sy + .5f) / 4) / n;
                                if (v >= .02f && v <= .98f && Mathf.Abs(u) <= .48f * (.98f - v) / .96f) inside++;
                            }
                        px[y * n + x] = new Color32(255, 255, 255, (byte)(inside * 255 / 16));
                    }
                tex.SetPixels32(px); tex.Apply();
                return triangle = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(.5f, .5f), 100);
            }
        }
    }
}
