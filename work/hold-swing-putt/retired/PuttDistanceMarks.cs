using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using GolfArcade.UI;

namespace GolfArcade.Game
{
    /// The putt's power-to-distance ruler, drawn on the green while a putt is lined up: a bar
    /// across the aim line where a quarter, a half, three quarters and all of the meter roll the
    /// ball on the flat (distance ∝ meter², GolfClub.MeterExponent), each labelled in feet with its
    /// share of the meter. As the putter comes back an amber bar slides out to the live reading,
    /// with its feet, and the marks it has passed turn yellow. The bars lie flat on the grass; the
    /// labels sit on the HUD above them, so they read the same size on the TV near or far.
    [DefaultExecutionOrder(9000)]   // after the camera rig has moved, so the labels sit on their bars
    public sealed class PuttDistanceMarks : MonoBehaviour
    {
        public static readonly float[] Powers = { 0.25f, 0.5f, 0.75f, 1f };
        static readonly Color White = new(1, 1, 1, 0.92f), Lit = new(1f, 0.83f, 0.1f, 0.98f);
        static readonly Color Shade = new(0.03f, 0.12f, 0.05f, 0.45f);
        static readonly Color Ink = UiKit.Hex("0A3A1A");

        Camera view;
        RectTransform labelLayer;
        readonly List<Transform> bars = new();
        readonly List<Renderer> barFaces = new();
        readonly List<(RectTransform root, Text feet, Text share, Image pill)> labels = new();
        readonly Vector3[] spots = new Vector3[Powers.Length];
        Transform live; RectTransform liveLabel; Text liveFeet;
        Vector3 liveSpot; bool liveShown;
        Vector3 across;
        MaterialPropertyBlock tint;
        float load;
        /// Whether the game still wants the ruler (in Aim with the putter); checked every frame.
        public System.Func<bool> Live;

        public static PuttDistanceMarks Create(Transform parent, Camera view, RectTransform hud)
        {
            var go = new GameObject("Putt distance marks") { layer = BallLook.OverlayLayer };
            go.transform.SetParent(parent, false);
            var m = go.AddComponent<PuttDistanceMarks>();
            m.view = view; m.tint = new MaterialPropertyBlock();
            var white = new Material(ShotEffects.ParticleMaterial()) { color = Color.white };
            var shade = new Material(ShotEffects.ParticleMaterial()) { color = Shade };
            for (int i = 0; i < Powers.Length; i++)
            {
                var bar = Bar(go.transform, $"Mark {Powers[i]:P0}", white, shade);
                m.bars.Add(bar); m.barFaces.Add(bar.GetComponent<Renderer>());
            }
            var amber = new Material(ShotEffects.ParticleMaterial()) { color = new Color(LandingZone.Amber.r, LandingZone.Amber.g, LandingZone.Amber.b, 0.98f) };
            m.live = Bar(go.transform, "Live", amber, shade);

            // the labels: on the HUD canvas, under its cards, placed by viewport like the course targets
            m.labelLayer = new GameObject("Putt distance labels").AddComponent<RectTransform>();
            m.labelLayer.SetParent(hud, false); m.labelLayer.SetAsFirstSibling();
            m.labelLayer.anchorMin = Vector2.zero; m.labelLayer.anchorMax = Vector2.one; m.labelLayer.sizeDelta = Vector2.zero;
            for (int i = 0; i < Powers.Length; i++) m.labels.Add(Label(m.labelLayer, $"{Powers[i] * 100:F0}%"));
            var (liveRoot, liveText, _, livePill) = Label(m.labelLayer, null);
            livePill.color = new Color(LandingZone.Amber.r, LandingZone.Amber.g, LandingZone.Amber.b, 0.96f);
            m.liveLabel = liveRoot; m.liveFeet = liveText;
            m.Hide();
            return m;
        }

        static Transform Bar(Transform parent, string name, Material face, Material shade)
        {
            var q = Quad(parent, name, face);
            var halo = Quad(q, "Halo", shade);
            halo.localPosition = new Vector3(0, 0, 0.01f);   // under it, as the bar lies face up
            halo.localScale = new Vector3(1.08f, 2.2f, 1);
            q.gameObject.SetActive(false);
            return q;
        }

        static Transform Quad(Transform parent, string name, Material m)
        {
            var q = GameObject.CreatePrimitive(PrimitiveType.Quad);
            q.name = name; q.layer = BallLook.OverlayLayer;
            Destroy(q.GetComponent<Collider>());
            q.transform.SetParent(parent, false);
            var r = q.GetComponent<Renderer>();
            r.sharedMaterial = m;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
            return q.transform;
        }

        static (RectTransform, Text, Text, Image) Label(RectTransform layer, string share)
        {
            var root = new GameObject("Label").AddComponent<RectTransform>();
            root.SetParent(layer, false);
            root.pivot = new Vector2(0.5f, 0f); root.sizeDelta = Vector2.one;
            var pill = UiKit.Panel(root, "Pill", new Color(1, 1, 1, 0.94f), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0, 14), new Vector2(112, 44));
            pill.rectTransform.pivot = new Vector2(0.5f, 0f); pill.raycastTarget = false;
            var feet = UiKit.Label(pill.transform, "Feet", 30, TextAnchor.MiddleCenter, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, UiKit.Display, false);
            feet.color = Ink; feet.raycastTarget = false;
            Text shareText = null;
            if (share != null)
            {
                shareText = UiKit.Label(pill.transform, "Share", 22, TextAnchor.LowerCenter, new Vector2(0, 1), new Vector2(1, 1), new Vector2(0, 22), new Vector2(0, 24), UiKit.Strong, false);
                shareText.text = share; shareText.color = Color.white; shareText.raycastTarget = false;
                var o = shareText.gameObject.AddComponent<Outline>(); o.effectColor = new Color(0, 0, 0, 0.55f); o.effectDistance = new Vector2(1.5f, -1.5f);
            }
            return (root, feet, shareText, pill);
        }

        /// Lays the ruler from `ball` along `heading` (degrees): mark i at `spotsAlong[i]` (world
        /// points on the green), reading `feet[i]`.
        public void Show(IList<Vector3> spotsAlong, IList<double> feet, double heading)
        {
            gameObject.SetActive(true); labelLayer.gameObject.SetActive(true);
            float h = (float)heading;
            across = Quaternion.Euler(0, h, 0) * Vector3.right;
            for (int i = 0; i < Powers.Length; i++)
            {
                spots[i] = spotsAlong[i] + Vector3.up * 0.04f;
                bars[i].SetPositionAndRotation(spots[i], Quaternion.Euler(90, h, 0));
                bars[i].gameObject.SetActive(true);
                labels[i].feet.text = $"{feet[i]:F0} ft";
            }
        }

        /// The live reading as the putter comes back: `at` where it rolls to, `feet` how far; 0 hides it.
        public void SetLoad(float value, Vector3 at, double feet)
        {
            load = value;
            liveShown = value > 0.02f && gameObject.activeSelf;
            live.gameObject.SetActive(liveShown);
            if (liveShown)
            {
                liveSpot = at + Vector3.up * 0.06f;
                live.SetPositionAndRotation(liveSpot, bars[0].rotation);
                liveFeet.text = $"{feet:F0} ft";
            }
            for (int i = 0; i < Powers.Length; i++)
            {
                bool reached = liveShown && load >= Powers[i] - 0.004f;
                tint.SetColor("_Color", reached ? Lit : White);
                barFaces[i].SetPropertyBlock(tint);
                labels[i].pill.color = reached ? Lit : new Color(1, 1, 1, 0.94f);
            }
        }

        public void Hide()
        {
            gameObject.SetActive(false);
            if (labelLayer) labelLayer.gameObject.SetActive(false);
            load = 0; liveShown = false;
        }

        void LateUpdate()
        {
            if (Live != null && !Live()) { Hide(); return; }
            if (!view) return;
            // the bars keep a readable width and weight from the camera; a far one is thicker
            for (int i = 0; i < bars.Count; i++) Size(bars[i], spots[i], 1f);
            if (liveShown) Size(live, liveSpot, 1.15f);
            var canvas = labelLayer.rect.size;
            for (int i = 0; i < labels.Count; i++) Pin(labels[i].root, spots[i], canvas);
            liveLabel.gameObject.SetActive(liveShown);
            if (liveShown) Pin(liveLabel, liveSpot, canvas, beside: true);
        }

        void Size(Transform bar, Vector3 at, float scale)
        {
            float d = Vector3.Distance(view.transform.position, at);
            float viewHeight = 2f * d * Mathf.Tan(view.fieldOfView * Mathf.Deg2Rad / 2f);
            float width = Mathf.Max(1.4f, 0.07f * viewHeight) * scale;
            // (seen low along the green the bar is foreshortened, so it is deep along the line)
            float weight = Mathf.Max(0.32f, 0.03f * viewHeight) * scale;
            bar.localScale = new Vector3(width, weight, 1);
        }

        void Pin(RectTransform label, Vector3 at, Vector2 canvas, bool beside = false)
        {
            var vp = view.WorldToViewportPoint(at);
            bool on = vp.z > 0.3f && vp.x > -0.05f && vp.x < 1.05f && vp.y > -0.05f && vp.y < 1.05f;
            label.gameObject.SetActive(on);
            if (!on) return;
            label.anchorMin = label.anchorMax = new Vector2(vp.x, vp.y);
            // the live reading sits off to the right of its bar, so it never covers a fixed mark's label
            label.anchoredPosition = beside ? new Vector2(128, -40) : Vector2.zero;
            // a far mark's label shrinks a little, so the four don't stack into one block up the screen
            label.localScale = Vector3.one * Mathf.Lerp(0.72f, 1f, Mathf.InverseLerp(0.75f, 0.25f, vp.y));
        }
    }
}
