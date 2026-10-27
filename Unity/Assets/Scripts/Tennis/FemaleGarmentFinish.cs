using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

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
        Mesh eyeFrameMesh; Vector4 eyeL, eyeR, eyeRight, eyeUp;
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
                    if(r is SkinnedMeshRenderer eyes && eyes.name=="OriginalSeamFeatures") EyeFrame(eyes);
                    foreach(var m in materials)
                    {
                        if(!m||!m.name.Contains("(hero)")||!configured.Add(m))continue;
                        if(m.HasProperty("_FemaleEyeRole")&&(m.name.Contains("Sclera")||m.name.Contains("Iris")))
                        {
                            bool iris=m.name.Contains("Iris");
                            m.SetFloat("_FemaleSurface",1);m.SetFloat("_FemaleEyeRole",iris?2:1);
                            m.SetFloat("_Smoothness",iris?.92f:.84f);
                            m.SetFloat("_EnvironmentStrength",iris?.60f:.34f);
                        }
                        else if(m.HasProperty("_FemaleEyeRole")&&(m.name.Contains("Pupil")||m.name.Contains("Limbal")))
                        {   // Shaded by the same upper lid as the sclera/iris; own shading otherwise.
                            m.SetFloat("_FemaleSurface",1);m.SetFloat("_FemaleEyeRole",3);
                        }
                        if(m.HasProperty("_FemaleEyeUp")&&eyeUp.w>.5f)
                        {m.SetVector("_FemaleEyeL",eyeL);m.SetVector("_FemaleEyeR",eyeR);m.SetVector("_FemaleEyeRight",eyeRight);m.SetVector("_FemaleEyeUp",eyeUp);}
                        if(!m.HasProperty("_WeaveThread"))continue;
                        m.SetFloat("_FemaleSurface",look.golfKit&&r.name=="Acc_Cap"?2:1);
                        if(look.golfKit&&r.name=="Kit_Top")m.SetFloat("_Cull",2);
                        m.SetFloat("_WeaveNormal",.22f);m.SetFloat("_WeaveThread",.16f);
                        m.SetFloat("_WeaveTile",m.GetFloat("_WeaveTile")*1.5f); // Configured once per material instance.
                        m.SetFloat("_SheenStrength",.32f);m.SetFloat("_Smoothness",.08f);
                        m.SetFloat("_NormalStrength",.80f);m.SetFloat("_Wrap",.30f);
                        m.SetFloat("_RimStrength",.025f);
                    }
                }
            }
            UpdateBinding();
        }
        /// The original-seam eye layers carry no lid frame. Give that per-hero mesh its
        /// bind-pose positions (UV1, as the body has) and measure each eye from the
        /// sclera, with "up" toward the brows. Geometry and blend shapes are unchanged.
        void EyeFrame(SkinnedMeshRenderer r)
        {
            var mesh=r.sharedMesh; if(!mesh||mesh==eyeFrameMesh||!mesh.isReadable)return;
            var mats=r.sharedMaterials; var v=mesh.vertices;
            Bounds? sclL=null, sclR=null, brow=null; float mid=mesh.bounds.center.x;
            for(int s=0;s<mats.Length&&s<mesh.subMeshCount;s++)
            {
                if(!mats[s])continue; bool sclera=mats[s].name.Contains("Sclera"), isBrow=mats[s].name.Contains("Brow");
                if(!sclera&&!isBrow)continue;
                foreach(int i in mesh.GetTriangles(s))
                {
                    var p=v[i];
                    if(isBrow){ if(brow is Bounds b){b.Encapsulate(p);brow=b;} else brow=new Bounds(p,Vector3.zero); continue; }
                    if(p.x<mid){ if(sclL is Bounds b){b.Encapsulate(p);sclL=b;} else sclL=new Bounds(p,Vector3.zero); }
                    else { if(sclR is Bounds b){b.Encapsulate(p);sclR=b;} else sclR=new Bounds(p,Vector3.zero); }
                }
            }
            if(!(sclL is Bounds l)||!(sclR is Bounds rr)||!(brow is Bounds bw))return;
            var right=(rr.center-l.center).normalized;
            var up=Vector3.ProjectOnPlane(bw.center-(l.center+rr.center)*.5f,right).normalized;
            float HalfAlong(Bounds b,Vector3 axis){float lo=float.MaxValue,hi=float.MinValue;foreach(var c in new[]{-1,1})foreach(var d in new[]{-1,1})foreach(var e in new[]{-1,1}){float t=Vector3.Dot(b.center+Vector3.Scale(b.extents,new Vector3(c,d,e)),axis);lo=Mathf.Min(lo,t);hi=Mathf.Max(hi,t);}return (hi-lo)*.5f;}
            if(!mesh.HasVertexAttribute(VertexAttribute.TexCoord1))
            {
                var copy=Instantiate(mesh); copy.name=mesh.name+" (female eye frame)";
                copy.SetUVs(1,new List<Vector3>(v)); r.sharedMesh=copy; mesh=copy;
            }
            eyeFrameMesh=mesh;
            eyeL=new Vector4(l.center.x,l.center.y,l.center.z,HalfAlong(l,up));
            eyeR=new Vector4(rr.center.x,rr.center.y,rr.center.z,HalfAlong(rr,up));
            eyeRight=new Vector4(right.x,right.y,right.z,(HalfAlong(l,right)+HalfAlong(rr,right))*.5f);
            eyeUp=new Vector4(up.x,up.y,up.z,1);
            foreach(var m in mats)if(m&&m.HasProperty("_FemaleEyeUp")){m.SetVector("_FemaleEyeL",eyeL);m.SetVector("_FemaleEyeR",eyeR);m.SetVector("_FemaleEyeRight",eyeRight);m.SetVector("_FemaleEyeUp",eyeUp);}
        }
        void UpdateBinding()
        {
            if(look.golfKit||look.kitSport=="Bowling"||topMaterials==null||topMaterials.Length==0||!topMaterials[0])return;   // bowling: own contrast panels
            var color=topMaterials[0].GetColor("_BaseColor");if(hasColor&&color==lastColor)return;
            lastColor=color;hasColor=true;
            foreach(var m in topMaterials)if(m&&m.HasProperty("_TrimColor"))
            {m.SetOverrideTag("FemaleBindingTone","0.88");m.SetColor("_TrimColor",new Color(color.r*.88f,color.g*.88f,color.b*.88f,color.a));}
        }
        void LateUpdate()=>Apply();
    }
}
