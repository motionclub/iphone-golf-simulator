using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Tennis
{
    /// Male eye finish (2026-10-18 face pass, male reference pack sheet 17): the original-seam eye layers get the eye-depth path
    /// the female uses in TennisCharacter (upper-lid shadow on the sclera, socket corners, deeper iris, near-black pupil ring).
    /// Same bind-pose eye frame as FemaleGarmentFinish.EyeFrame; `_FemaleEyeRole` 1 sclera, 2 iris, 3 pupil/limbal, and
    /// `_FemaleSurface` 3 = the male tuning of that path. Geometry, gaze, blend shapes and the authored colours are unchanged.
    [DefaultExecutionOrder(1216), DisallowMultipleComponent]
    public sealed class MaleFaceFinish : MonoBehaviour
    {
        MatchHeroLook look;
        readonly HashSet<Material> configured = new();
        float nextScan;
        Mesh eyeFrameMesh; Vector4 eyeL, eyeR, eyeRight, eyeUp;
        public static void Attach(MatchHeroLook hero)
        {
            if (!hero || hero.female || hero.GetComponent<MaleFaceFinish>()) return;
            hero.gameObject.AddComponent<MaleFaceFinish>().look = hero;
        }
        public void Apply()
        {
            if (!look || look.female) return;
            if (Application.isPlaying && Time.unscaledTime < nextScan) return;
            nextScan = Time.unscaledTime + .5f;
            if (look.body) foreach (var m in look.body.sharedMaterials)
                if (m && m.HasProperty("_MaleFormPass")) m.SetFloat("_MaleFormPass", 1);
            foreach (var r in look.GetComponentsInChildren<Renderer>(true))
            {
                if (r.name.StartsWith("Kit_")) { Knit(r); continue; }
                if (!(r is SkinnedMeshRenderer eyes) || eyes.name != "OriginalSeamFeatures") continue;
                EyeFrame(eyes);
                foreach (var m in eyes.sharedMaterials)
                {
                    if (!m || !m.name.Contains("(hero)") || !m.HasProperty("_FemaleEyeRole")) continue;
                    if (eyeUp.w > .5f) { m.SetVector("_FemaleEyeL", eyeL); m.SetVector("_FemaleEyeR", eyeR); m.SetVector("_FemaleEyeRight", eyeRight); m.SetVector("_FemaleEyeUp", eyeUp); }
                    if (!configured.Add(m)) continue;
                    if (m.name.Contains("Sclera") || m.name.Contains("Iris"))
                    {
                        bool iris = m.name.Contains("Iris");
                        m.SetFloat("_FemaleSurface", 3); m.SetFloat("_FemaleEyeRole", iris ? 2 : 1);
                        m.SetFloat("_Smoothness", iris ? .92f : .84f);
                        m.SetFloat("_EnvironmentStrength", iris ? .30f : .34f);   // 10-19 repair: iris .60 -> .30, foliage showed as a green crescent on the iris
                    }
                    else if (m.name.Contains("Pupil") || m.name.Contains("Limbal")) { m.SetFloat("_FemaleSurface", 3); m.SetFloat("_FemaleEyeRole", 3); }
                }
            }
        }
        /// Male garments (2026-10-19 repair, Adnan "smooth clothes, add shaders and quality"): the female knit response of TennisCloth
        /// (`_FemaleSurface` 1: matte Lambert form so folds read, light-through-fibre terminator band, Charlie velvet sheen, deeper fold
        /// ambient, knit grain) with the female numbers of FemaleGarmentFinish. Colours, maps and geometry are unchanged, so every swatch keeps its hue.
        void Knit(Renderer r)
        {
            foreach (var m in r.sharedMaterials)
            {
                if (!m || !m.name.Contains("(hero)") || !m.HasProperty("_WeaveThread") || !configured.Add(m)) continue;
                m.SetFloat("_FemaleSurface", 1);
                m.SetFloat("_WeaveNormal", .22f); m.SetFloat("_WeaveThread", .16f);
                m.SetFloat("_WeaveTile", m.GetFloat("_WeaveTile") * 1.5f);   // configured once per material instance
                m.SetFloat("_SheenStrength", .32f); m.SetFloat("_Smoothness", .08f);
                m.SetFloat("_NormalStrength", .80f); m.SetFloat("_Wrap", .30f);
                m.SetFloat("_RimStrength", .025f);
            }
        }
        /// As FemaleGarmentFinish.EyeFrame: bind-pose positions in UV1 and an eye frame measured from the sclera, "up" toward the brows.
        void EyeFrame(SkinnedMeshRenderer r)
        {
            var mesh = r.sharedMesh; if (!mesh || mesh == eyeFrameMesh || !mesh.isReadable) return;
            var mats = r.sharedMaterials; var v = mesh.vertices;
            Bounds? sclL = null, sclR = null, brow = null; float mid = mesh.bounds.center.x;
            for (int s = 0; s < mats.Length && s < mesh.subMeshCount; s++)
            {
                if (!mats[s]) continue; bool sclera = mats[s].name.Contains("Sclera"), isBrow = mats[s].name.Contains("Brow");
                if (!sclera && !isBrow) continue;
                foreach (int i in mesh.GetTriangles(s))
                {
                    var p = v[i];
                    if (isBrow) { if (brow is Bounds b) { b.Encapsulate(p); brow = b; } else brow = new Bounds(p, Vector3.zero); continue; }
                    if (p.x < mid) { if (sclL is Bounds b) { b.Encapsulate(p); sclL = b; } else sclL = new Bounds(p, Vector3.zero); }
                    else { if (sclR is Bounds b) { b.Encapsulate(p); sclR = b; } else sclR = new Bounds(p, Vector3.zero); }
                }
            }
            if (!(sclL is Bounds l) || !(sclR is Bounds rr) || !(brow is Bounds bw)) return;
            var right = (rr.center - l.center).normalized;
            var up = Vector3.ProjectOnPlane(bw.center - (l.center + rr.center) * .5f, right).normalized;
            float HalfAlong(Bounds b, Vector3 axis) { float lo = float.MaxValue, hi = float.MinValue; foreach (var c in new[] { -1, 1 }) foreach (var d in new[] { -1, 1 }) foreach (var e in new[] { -1, 1 }) { float t = Vector3.Dot(b.center + Vector3.Scale(b.extents, new Vector3(c, d, e)), axis); lo = Mathf.Min(lo, t); hi = Mathf.Max(hi, t); } return (hi - lo) * .5f; }
            if (!mesh.HasVertexAttribute(VertexAttribute.TexCoord1))
            {
                var copy = Instantiate(mesh); copy.name = mesh.name + " (male eye frame)";
                copy.SetUVs(1, new List<Vector3>(v)); r.sharedMesh = copy; mesh = copy;
            }
            eyeFrameMesh = mesh;
            eyeL = new Vector4(l.center.x, l.center.y, l.center.z, HalfAlong(l, up));
            eyeR = new Vector4(rr.center.x, rr.center.y, rr.center.z, HalfAlong(rr, up));
            eyeRight = new Vector4(right.x, right.y, right.z, (HalfAlong(l, right) + HalfAlong(rr, right)) * .5f);
            eyeUp = new Vector4(up.x, up.y, up.z, 1);
        }
        void LateUpdate() => Apply();
    }
}
