using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Game
{
    /// Fades a golfer (every renderer under it: body, clothes, hair, club, cap) out and back in — on a putt the golfer steps
    /// out of the picture while the ball rolls and comes back for the hole-out (Adnan, 2026-10-19). The character shaders are
    /// opaque and have no fade of their own, so while the golfer is anything but fully there each material is stood in for by a
    /// transparent copy of the pipeline's Lit material carrying its colour and albedo; at full opacity the golfer's own
    /// materials (and any property blocks) are exactly as they were.
    [DisallowMultipleComponent]
    public sealed class GolferFade : MonoBehaviour
    {
        sealed class Entry { public Renderer renderer; public Material[] own, faded; public ShadowCastingMode shadows; public MaterialPropertyBlock block; }
        readonly List<Entry> entries = new();
        float opacity = 1, target = 1, rate;
        static Material template;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor"), BaseMap = Shader.PropertyToID("_BaseMap"), Color = Shader.PropertyToID("_Color"), MainTex = Shader.PropertyToID("_MainTex");

        /// 1 fully there, 0 gone.
        public float Opacity => opacity;
        public bool Fading => opacity != target;

        public static GolferFade On(Component golfer) { var f = golfer.GetComponent<GolferFade>(); return f ? f : golfer.gameObject.AddComponent<GolferFade>(); }

        /// Ease to `opacity` (0–1) over `seconds` (0: at once).
        public void FadeTo(float opacity, float seconds)
        {
            target = Mathf.Clamp01(opacity);
            rate = seconds > 0 ? 1f / seconds : float.PositiveInfinity;
            if (seconds <= 0) Apply(target);
        }

        /// Fully there again at once, the golfer's own materials back.
        public void Restore() { target = 1; Apply(1); }

        void LateUpdate()
        {
            if (opacity != target) Apply(Mathf.MoveTowards(opacity, target, rate * Time.deltaTime));
            else if (swapped && Adopt()) Apply(opacity);   // something shown while faded (the bag on the back at the result) fades with the rest
        }
        void OnDisable() { if (opacity < 1) Restore(); }

        void Apply(float a)
        {
            opacity = a;
            if (a >= 1) { Swap(false); return; }
            Swap(true);
            foreach (var e in entries)
            {
                if (!e.renderer) continue;
                e.renderer.enabled = a > .01f;
                foreach (var m in e.faded) { if (!m) continue; var c = m.GetColor(BaseColor); c.a = a; m.SetColor(BaseColor, c); }
                // the shadow goes with the last of the golfer
                e.renderer.shadowCastingMode = a > .35f ? e.shadows : ShadowCastingMode.Off;
            }
        }

        bool swapped;
        void Swap(bool faded)
        {
            if (faded == swapped) return;
            swapped = faded;
            if (faded)
            {
                entries.Clear();
                Adopt();
            }
            else
            {
                foreach (var e in entries)
                {
                    if (!e.renderer) continue;
                    e.renderer.sharedMaterials = e.own; e.renderer.shadowCastingMode = e.shadows; e.renderer.enabled = true;
                    if (e.block != null) e.renderer.SetPropertyBlock(e.block);
                    foreach (var m in e.faded) if (m) Destroy(m);
                }
                entries.Clear();
            }
        }

        /// Takes on every shown renderer not faded yet; true when there was one.
        bool Adopt()
        {
            bool any = false;
            foreach (var r in GetComponentsInChildren<Renderer>(false))
            {
                if (!r.enabled || r is not (SkinnedMeshRenderer or MeshRenderer) || entries.Exists(e => e.renderer == r)) continue;
                any = true;
                var own = r.sharedMaterials; var copy = new Material[own.Length];
                for (int i = 0; i < own.Length; i++) copy[i] = Transparent(own[i]);
                MaterialPropertyBlock block = null;
                if (r.HasPropertyBlock()) { block = new MaterialPropertyBlock(); r.GetPropertyBlock(block); r.SetPropertyBlock(null); }   // (a block's colour would override the fade)
                entries.Add(new Entry { renderer = r, own = own, faded = copy, shadows = r.shadowCastingMode, block = block });
                r.sharedMaterials = copy;
            }
            return any;
        }

        static Material Transparent(Material own)
        {
            if (!template)
            {
                var lit = GraphicsSettings.currentRenderPipeline ? GraphicsSettings.currentRenderPipeline.defaultMaterial : null;
                template = new Material(lit ? lit.shader : Shader.Find("Universal Render Pipeline/Lit")) { name = "GolferFade" };
                template.SetFloat("_Surface", 1); template.SetFloat("_Blend", 0);
                template.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha); template.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
                template.SetFloat("_SrcBlendAlpha", (float)BlendMode.One); template.SetFloat("_DstBlendAlpha", (float)BlendMode.OneMinusSrcAlpha);
                template.SetFloat("_ZWrite", 0); template.SetFloat("_Smoothness", .2f);
                template.EnableKeyword("_SURFACE_TYPE_TRANSPARENT"); template.SetOverrideTag("RenderType", "Transparent");
                template.renderQueue = (int)RenderQueue.Transparent;
            }
            var m = new Material(template) { name = "GolferFade " + (own ? own.name : "") };
            if (own)
            {
                var c = own.HasProperty(BaseColor) ? own.GetColor(BaseColor) : own.HasProperty(Color) ? own.GetColor(Color) : UnityEngine.Color.white;
                c.a = 1; m.SetColor(BaseColor, c);
                var tex = own.HasProperty(BaseMap) ? own.GetTexture(BaseMap) : own.HasProperty(MainTex) ? own.GetTexture(MainTex) : null;
                if (tex) { m.SetTexture(BaseMap, tex); m.SetTextureScale(BaseMap, own.HasProperty(BaseMap) ? own.GetTextureScale(BaseMap) : Vector2.one); }
            }
            return m;
        }
    }
}
