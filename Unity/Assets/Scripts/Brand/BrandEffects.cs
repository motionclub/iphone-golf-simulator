using UnityEngine;
using UnityEngine.UI;

namespace MotionSports.Brand
{
    /// The brand lean (menu mock 10-28, CSS skewX(-14deg)): shears a graphic's vertices sideways, x += (y - centre) · tan(angle), so
    /// a fill becomes a forward-leaning parallelogram. A mesh effect rather than a rotated rect: the top and bottom stay level and a
    /// Mask on a skewed graphic clips its children (a picture stays upright inside a slanted card). `inside` first narrows the shape so
    /// the slant stays within the rect (CSS clip-path) instead of overhanging it (CSS skewX).
    [DisallowMultipleComponent]
    public sealed class Skew : BaseMeshEffect
    {
        public float angle = 14; public bool inside;
        public override void ModifyMesh(VertexHelper vh)
        {
            if (!IsActive() || vh.currentVertCount == 0) return;
            var r = graphic.rectTransform.rect;
            float t = Mathf.Tan(angle * Mathf.Deg2Rad), cx = r.center.x, cy = r.center.y;
            float sx = inside && r.width > 0 ? Mathf.Max(0, r.width - Mathf.Abs(t) * r.height) / r.width : 1;
            var v = new UIVertex();
            for (int i = 0; i < vh.currentVertCount; i++)
            {
                vh.PopulateUIVertex(ref v, i);
                var p = v.position; p.x = cx + (p.x - cx) * sx + (p.y - cy) * t; v.position = p;
                vh.SetUIVertex(v, i);
            }
        }
    }

    /// A left-to-right two-colour tint (the gold slash, the side scrims); colours multiply with the graphic's own.
    [DisallowMultipleComponent]
    public sealed class HGradient : BaseMeshEffect
    {
        public Color Left = Color.white, Right = Color.white;
        public static HGradient On(Graphic g, Color left, Color right)
        {
            var h = g.gameObject.GetComponent<HGradient>() ?? g.gameObject.AddComponent<HGradient>();
            h.Left = left; h.Right = right; g.SetVerticesDirty();
            return h;
        }
        public override void ModifyMesh(VertexHelper vh)
        {
            if (!IsActive() || vh.currentVertCount == 0) return;
            var r = graphic.rectTransform.rect; float span = Mathf.Max(1e-3f, r.width);
            var v = new UIVertex();
            for (int i = 0; i < vh.currentVertCount; i++)
            {
                vh.PopulateUIVertex(ref v, i);
                v.color *= Color.Lerp(Left, Right, Mathf.Clamp01((v.position.x - r.xMin) / span));
                vh.SetUIVertex(v, i);
            }
        }
    }
}
