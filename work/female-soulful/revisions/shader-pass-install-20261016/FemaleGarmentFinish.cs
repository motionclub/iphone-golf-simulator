using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Female material instances: matte fabric, restrained seam normals and
    /// palette-owned binding. The authored fabric-map encoding stays intact.
    [DefaultExecutionOrder(1216), DisallowMultipleComponent]
    public sealed class FemaleGarmentFinish : MonoBehaviour
    {
        MatchHeroLook look;
        readonly HashSet<Material> configured=new();
        Material[] topMaterials;
        Color lastColor; bool hasColor;
        float nextScan;
        public static void Attach(MatchHeroLook hero)
        {
            if (!hero || !hero.female || hero.GetComponent<FemaleGarmentFinish>()) return;
            hero.gameObject.AddComponent<FemaleGarmentFinish>().look=hero;
        }
        public void Apply()
        {
            if (!look || !look.female) return;
            if (!Application.isPlaying || Time.unscaledTime>=nextScan)
            {
                nextScan=Time.unscaledTime+.5f;
                foreach (var r in look.GetComponentsInChildren<Renderer>(true))
                {
                    var materials=r.sharedMaterials;
                    if(r.name=="Kit_Top") {topMaterials=materials;hasColor=false;}
                    foreach(var m in materials)
                    {
                        if(!m||!m.HasProperty("_WeaveThread")||!m.name.Contains("(hero)")||!configured.Add(m))continue;
                        m.SetFloat("_FemaleSurface",1);
                        m.SetFloat("_WeaveNormal",.12f);m.SetFloat("_WeaveThread",.055f);
                        m.SetFloat("_WeaveTile",m.GetFloat("_WeaveTile")*2);
                        m.SetFloat("_SheenStrength",.22f);m.SetFloat("_Smoothness",.10f);
                        m.SetFloat("_NormalStrength",.60f);m.SetFloat("_Wrap",.24f);
                        m.SetFloat("_RimStrength",.035f);
                    }
                }
            }
            UpdateBinding();
        }
        void UpdateBinding()
        {
            if(look.golfKit||topMaterials==null||topMaterials.Length==0||!topMaterials[0])return;
            var color=topMaterials[0].GetColor("_BaseColor");if(hasColor&&color==lastColor)return;
            lastColor=color;hasColor=true;
            foreach(var m in topMaterials)if(m&&m.HasProperty("_TrimColor"))
            {m.SetOverrideTag("FemaleBindingTone","0.88");m.SetColor("_TrimColor",new Color(color.r*.88f,color.g*.88f,color.b*.88f,color.a));}
        }
        void LateUpdate()=>Apply();
    }
}
