using UnityEngine;
using UnityEngine.UI;

namespace MotionSports.Brand
{
    /// The swing arc (Brand Guide §7) as a UI graphic: part of an ellipse in this RectTransform, swept from `start` through `sweep`
    /// degrees (counter-clockwise, 0 = right), its width tapering from `tail` × `width` to `width` at the head, coloured from
    /// `tailColor` to `headColor` (alpha 0 → 1 by default). Used for the loader ring, the tab underline, the cursor and the wipe.
    [RequireComponent(typeof(CanvasRenderer))]
    public sealed class ArcGraphic : MaskableGraphic
    {
        public float start = 200, sweep = 140, width = 12, tail = .15f;
        public Color tailColor = new Color(1, 1, 1, 0), headColor = Color.white;
        /// The ellipse's radii as a share of the rect's half size (1 = touches the edges).
        public Vector2 radius = Vector2.one;
        [Range(8, 160)] public int segments = 64;

        public static ArcGraphic Add(RectTransform rt, float start, float sweep, float width, Color tailColor, Color headColor, float tail = .15f)
        {
            var a = rt.gameObject.AddComponent<ArcGraphic>();
            a.start = start; a.sweep = sweep; a.width = width; a.tailColor = tailColor; a.headColor = headColor; a.tail = tail; a.raycastTarget = false;
            return a;
        }
        public void Set(float start, float sweep) { if (Mathf.Approximately(start, this.start) && Mathf.Approximately(sweep, this.sweep)) return; this.start = start; this.sweep = sweep; SetVerticesDirty(); }

        protected override void OnPopulateMesh(VertexHelper vh)
        {
            vh.Clear();
            var r = rectTransform.rect; var c = r.center;
            float rx = r.width * .5f * radius.x, ry = r.height * .5f * radius.y;
            if (Mathf.Abs(sweep) < .01f || rx <= 0 || ry <= 0) return;
            int n = Mathf.Max(2, Mathf.CeilToInt(segments * Mathf.Abs(sweep) / 360f));
            var v = UIVertex.simpleVert;
            for (int i = 0; i <= n; i++)
            {
                float k = i / (float)n;
                float a = (start + sweep * k) * Mathf.Deg2Rad;
                var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                var p = c + new Vector2(dir.x * rx, dir.y * ry);
                // the normal of the ellipse at this point
                var nrm = new Vector2(dir.x / rx, dir.y / ry).normalized;
                float w = width * Mathf.Lerp(tail, 1, k) * .5f;
                var col = Color.Lerp(tailColor, headColor, k) * color;
                v.color = col;
                v.position = p + nrm * w; vh.AddVert(v);
                v.position = p - nrm * w; vh.AddVert(v);
                if (i > 0) { int b = (i - 1) * 2; vh.AddTriangle(b, b + 1, b + 2); vh.AddTriangle(b + 2, b + 1, b + 3); }
            }
            // a round head
            float hw = width * .5f; float ha = (start + sweep) * Mathf.Deg2Rad;
            var head = c + new Vector2(Mathf.Cos(ha) * rx, Mathf.Sin(ha) * ry);
            int center = vh.currentVertCount; v.color = headColor * color; v.position = head; vh.AddVert(v);
            const int cap = 12;
            for (int i = 0; i <= cap; i++) { float t = i / (float)cap * Mathf.PI * 2; v.position = head + new Vector2(Mathf.Cos(t), Mathf.Sin(t)) * hw; vh.AddVert(v); if (i > 0) vh.AddTriangle(center, center + i, center + i + 1); }
        }
    }
}
