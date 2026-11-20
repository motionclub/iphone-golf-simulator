using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Golf-only surface finish. Positions, skin weights, colors and animation data stay authored.
    public static class HeroGolfSurfaceFinish
    {
        public static bool Enabled => System.Environment.GetEnvironmentVariable("GOLF_SURFACE_FINISH") != "0";
        static readonly Dictionary<Mesh, Mesh> normals = new();

        public static void Skin(Material material)
        {
            if (!Enabled || !material || !material.HasProperty("_AthleteSkin")) return;
            material.SetFloat("_AthleteSkin", 1);
        }

        public static void Cloth(Material material, string tag)
        {
            if (!Enabled || !material || (tag != "Top" && tag != "Bottom")) return;
            bool top = tag == "Top";
            // Broad, low-energy cloth response; retain the authored seam/fold maps and yarn atlas.
            material.SetFloat("_StylePass", 1);
            material.SetFloat("_StyleSmooth", top ? .46f : .34f);
            material.SetFloat("_StyleSpec", top ? .30f : .16f);
            material.SetFloat("_StyleEnv", top ? .12f : .06f);
            material.SetFloat("_StyleSheen", top ? .12f : .06f);
            material.SetFloat("_RimStrength", .075f);
            material.SetFloat("_NormalStrength", top ? .55f : .65f);
            material.SetFloat("_FabricDetail", top ? .18f : .22f);
            material.SetFloat("_FibreShine", .18f);
            material.SetFloat("_Mottle", .008f);
            // Neutral material detail leaves the palette and the user's selected color intact.
        }

        public static Mesh BodyNormals(SkinnedMeshRenderer body)
        {
            if (!Enabled || !body || !body.sharedMesh || !body.sharedMesh.isReadable) return body ? body.sharedMesh : null;
            var mesh = body.sharedMesh;
            if (mesh.name.EndsWith(" (golf body surface normals)")) return mesh;
            if (normals.TryGetValue(mesh, out var cached) && cached) return cached;
            var positions = mesh.vertices; var old = mesh.normals; var weights = mesh.boneWeights;
            if (old.Length != positions.Length || weights.Length != positions.Length) return mesh;
            bool[] bodyBone = new bool[body.bones.Length];
            for (int i = 0; i < bodyBone.Length; i++)
            {
                string name = body.bones[i] ? body.bones[i].name : "";
                bodyBone[i] = name == "Hips" || name.Contains("Spine") || name.Contains("Chest") || name.Contains("UpperArm") || name.Contains("LowerArm") || name.Contains("UpperLeg") || name.Contains("LowerLeg");
            }
            float Share(BoneWeight w) =>
                (w.boneIndex0 < bodyBone.Length && bodyBone[w.boneIndex0] ? w.weight0 : 0) +
                (w.boneIndex1 < bodyBone.Length && bodyBone[w.boneIndex1] ? w.weight1 : 0) +
                (w.boneIndex2 < bodyBone.Length && bodyBone[w.boneIndex2] ? w.weight2 : 0) +
                (w.boneIndex3 < bodyBone.Length && bodyBone[w.boneIndex3] ? w.weight3 : 0);
            const float radius = .012f;
            Vector3Int Cell(Vector3 p) => new(Mathf.FloorToInt(p.x / radius), Mathf.FloorToInt(p.y / radius), Mathf.FloorToInt(p.z / radius));
            var grid = new Dictionary<Vector3Int, List<int>>();
            var selected = new List<int>();
            for (int i = 0; i < positions.Length; i++)
            {
                if (Share(weights[i]) < .8f) continue;
                selected.Add(i); var cell = Cell(positions[i]);
                if (!grid.TryGetValue(cell, out var ids)) grid[cell] = ids = new List<int>();
                ids.Add(i);
            }
            var result = (Vector3[])old.Clone(); float maximum = 0;
            foreach (int i in selected)
            {
                var cell = Cell(positions[i]); var sum = old[i];
                for (int x = -1; x <= 1; x++) for (int y = -1; y <= 1; y++) for (int z = -1; z <= 1; z++)
                    if (grid.TryGetValue(cell + new Vector3Int(x, y, z), out var ids)) foreach (int j in ids)
                    {
                        float distance = (positions[i] - positions[j]).sqrMagnitude;
                        if (distance >= radius * radius || Vector3.Dot(old[i], old[j]) < .86f) continue;
                        sum += old[j] * Mathf.Pow(1 - distance / (radius * radius), 2);
                    }
                // Restrained shading correction; never blur away an anatomical edge.
                result[i] = Vector3.RotateTowards(old[i], sum.normalized, 10 * Mathf.Deg2Rad, 0).normalized;
                maximum = Mathf.Max(maximum, Vector3.Angle(old[i], result[i]));
            }
            cached = Object.Instantiate(mesh); cached.name = mesh.name + " (golf body surface normals)";
            cached.hideFlags = HideFlags.DontSave; cached.normals = result; normals[mesh] = cached;
            Debug.Log($"[GolfSurface] normals only: {selected.Count} body vertices, maximum {maximum:F2} degrees; positions/topology/UV/weights unchanged");
            return cached;
        }
    }
}
