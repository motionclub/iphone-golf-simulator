using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Fine matte knit on the new female tops; color selection remains owned by MatchHeroLook.
    [DefaultExecutionOrder(1216), DisallowMultipleComponent]
    public sealed class FemaleGarmentFinish : MonoBehaviour
    {
        MatchHeroLook look; bool applied; Material[] topMaterials; Color lastColor; bool hasColor;
        public static void Attach(MatchHeroLook hero)
        {
            if (!hero || !hero.female || hero.GetComponent<FemaleGarmentFinish>()) return;
            hero.gameObject.AddComponent<FemaleGarmentFinish>().look = hero;
        }
        public void Apply()
        {
            if (applied) { UpdateBinding(); return; }
            if (!look || look.kit == null) return;
            foreach (var r in look.kit)
            {
                if (!r || r.name != "Kit_Top" || !r.sharedMesh || !r.sharedMesh.name.Contains("FemaleSoulful")) continue;
                foreach (var m in r.sharedMaterials)
                {
                    if (!m || !m.HasProperty("_WeaveThread") || !m.name.Contains("(hero)")) return;
                    m.SetFloat("_WeaveNormal", .12f); m.SetFloat("_WeaveThread", .055f);
                    m.SetFloat("_WeaveTile", m.GetFloat("_WeaveTile") * 2);
                    m.SetFloat("_SheenStrength", .22f); m.SetFloat("_Smoothness", .10f);
                    m.SetFloat("_NormalStrength", .8f);
                }
                topMaterials = r.sharedMaterials; applied = true; UpdateBinding();
            }
        }
        void UpdateBinding()
        {
            if (!look || look.golfKit || topMaterials == null || topMaterials.Length == 0 || !topMaterials[0]) return;
            var color = topMaterials[0].GetColor("_BaseColor");
            if (hasColor && color == lastColor) return;
            lastColor = color; hasColor = true;
            foreach(var m in topMaterials) if(m)m.SetOverrideTag("FemaleBindingTone","0.88");
            foreach (var m in topMaterials) if (m && m.HasProperty("_TrimColor"))
                m.SetColor("_TrimColor", new Color(color.r * .88f, color.g * .88f, color.b * .88f, color.a));
        }
        void LateUpdate() { Apply(); if (applied && look.golfKit) enabled = false; }
    }
}
