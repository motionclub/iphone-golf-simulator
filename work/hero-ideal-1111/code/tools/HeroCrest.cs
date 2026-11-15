using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// IDEAL HERO (work/hero-ideal-1111, clone only): a crest patch on the left chest of every top, drawn by TennisCloth from the garment's
    /// rest-pose position (mesh channel 5, hero space), so it needs no UV work and rides the cloth through every pose. HERO_CREST=1.
    public static class HeroCrest
    {
        public static bool On => System.Environment.GetEnvironmentVariable("HERO_CREST") == "1";
        static readonly HashSet<Mesh> tagged = new();
        public static void Apply(MatchHeroLook look)
        {
            if (!On || !look || look.kit == null) return;
            foreach (var r in look.kit)
            {
                if (!r || r.name != "Kit_Top" || !r.sharedMesh || !r.sharedMesh.isReadable) continue;
                var mesh = r.sharedMesh; var toHero = look.transform.worldToLocalMatrix * r.transform.localToWorldMatrix;
                var v = mesh.vertices; var nrm = mesh.normals; var rest = new List<Vector3>(v.Length);
                Vector3 min = Vector3.one * 9, max = -Vector3.one * 9;
                foreach (var p in v) { var q = toHero.MultiplyPoint3x4(p); rest.Add(q); min = Vector3.Min(min, q); max = Vector3.Max(max, q); }
                if (!tagged.Contains(mesh)) { mesh.SetUVs(5, rest); tagged.Add(mesh); }
                // facing and the hero's left, from the rest pose itself
                var lf = look.Bone(HumanBodyBones.LeftFoot); var lt = look.Bone(HumanBodyBones.LeftToes); var la = look.Bone(HumanBodyBones.LeftUpperArm);
                if (!lf || !lt || !la) continue;
                var fwd = look.transform.InverseTransformVector(lt.position - lf.position); fwd.y = 0; fwd.Normalize();
                float side = Mathf.Sign(look.transform.InverseTransformPoint(la.position).x);
                var target = new Vector2(side * .075f, max.y - .15f); int best = -1; float bd = 1e9f;
                for (int i = 0; i < rest.Count; i++)
                {
                    if (i < nrm.Length && Vector3.Dot(toHero.MultiplyVector(nrm[i]).normalized, fwd) < .55f) continue;
                    float d = (new Vector2(rest[i].x, rest[i].y) - target).sqrMagnitude; if (d < bd) { bd = d; best = i; }
                }
                if (best < 0) continue;
                var c = rest[best];
                foreach (var m in r.sharedMaterials) if (m && m.HasProperty("_CrestCentre")) { m.SetVector("_CrestCentre", new Vector4(c.x, c.y, c.z, .027f)); m.SetColor("_CrestColor", MatchHeroLook.KitTint(Color.white)); }
            }
        }
    }
}
