using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Majestic
{
    /// Fills the resort stands between TennisStandsCrowd's 36 seated fans (same authored
    /// Premium/TennisSeatedHero3 variants, same spectator material) with GPU-instanced fans: one draw per
    /// variant part, no GameObjects per fan. Motion is cheap and procedural: a breathing bob, a slow head
    /// turn, and arm claps that travel along the stand as a wave.
    public sealed class MajesticCrowd : MonoBehaviour
    {
        static readonly float[] TierX = { -13.8f, -15f, -16.2f }, TierY = { .63f, 1.28f, 1.93f };
        static readonly float[] SeatZ = { -9, -7, -5, -3, .7f, 2.7f, 4.7f, 6.7f, 10.5f, 12.5f, 14.5f, 16.5f };

        sealed class Part { public Mesh mesh; public Matrix4x4 local; public int kind; public Matrix4x4[] m; public int count; }
        sealed class Variant { public readonly List<Part> parts = new(); }
        struct Fan { public int variant; public Matrix4x4 root; public float phase, z; }

        readonly List<Variant> variants = new();
        readonly List<Fan> fans = new();
        Material material;
        RenderParams rp;
        Bounds bounds;

        /// Seats for the resort stands: between TennisStandsCrowd's seats on its three tiers, facing +X.
        public static List<(Vector3 pos, float yaw)> ResortSeats()
        {
            var list = new List<(Vector3, float)>(); int i = 0;
            for (int tier = 0; tier < 3; tier++)
                for (int s = 0; s < SeatZ.Length - 1; s++)
                {
                    float gap = SeatZ[s + 1] - SeatZ[s]; int extra = gap > 3 ? 2 : 1;
                    for (int e = 1; e <= extra; e++, i++)
                        if (SeatZ[s] + gap * e / (extra + 1) > 1)   // only the stretch the gameplay cameras see
                        list.Add((new Vector3(TierX[tier] - .04f * (i % 3), TierY[tier], SeatZ[s] + gap * e / (extra + 1)), 90f));
                }
            return list;
        }

        public static MajesticCrowd Build(Transform parent) => Build(parent, ResortSeats());
        public static MajesticCrowd Build(Transform parent, List<(Vector3 pos, float yaw)> seats)
        {
            var prefab = Resources.Load<GameObject>("Tennis/Premium/TennisSeatedHero3");
            if (!prefab) return null;
            var go = new GameObject("Majestic crowd"); go.transform.SetParent(parent, false);
            var c = go.AddComponent<MajesticCrowd>();
            c.Init(prefab, seats);
            return c;
        }

        void Init(GameObject prefab, List<(Vector3 pos, float yaw)> seats)
        {
            // reuse the stands' spectator material (it already knows how its vertex colours decode)
            foreach (var r in FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
                if (r.sharedMaterial && r.sharedMaterial.name.StartsWith("Sporting spectator")) { material = r.sharedMaterial; break; }
            if (!material)
            {
                var shader = Resources.Load<Shader>("Tennis/Shaders/TennisSpectator");
                if (!shader) { enabled = false; return; }
                material = new Material(shader) { name = "Majestic spectator", enableInstancing = true };
                if (material.HasProperty("_SurfaceRoles")) material.SetFloat("_SurfaceRoles", 1);
            }
            var template = Instantiate(prefab); template.SetActive(false);
            for (int v = 0; v < 6; v++)
            {
                Transform sel = null;
                foreach (var t in template.GetComponentsInChildren<Transform>(true)) if (t.name == "FAN_" + v) { sel = t; break; }
                var variant = new Variant(); variants.Add(variant);
                if (!sel) continue;
                // same placement as TennisStandsCrowd: the selected FAN_v sits at the instance root's origin
                sel.localPosition = Vector3.zero;
                var toFan = template.transform.worldToLocalMatrix;
                // the stands are small on screen from the court: use the authored far-LOD parts when present
                var all = sel.GetComponentsInChildren<MeshFilter>(true);
                bool hasFar = System.Array.Exists(all, x => x.sharedMesh && x.name.Contains("_FAR"));
                foreach (var mf in all)
                {
                    if (!mf.sharedMesh || mf.name.Contains("_FAR") != hasFar) continue;
                    int kind = mf.name.StartsWith("HEAD") ? 1 : mf.name.StartsWith("ARM_L") ? 2 : mf.name.StartsWith("ARM_R") ? 3 : 0;
                    variant.parts.Add(new Part { mesh = mf.sharedMesh, local = toFan * mf.transform.localToWorldMatrix, kind = kind });
                }
            }
            for (int i = 0; i < seats.Count; i++)
            {
                var (pos, yaw) = seats[i];
                var rot = Quaternion.Euler(0, yaw + (i * 37 % 21) - 10, 0) * prefab.transform.rotation;
                fans.Add(new Fan { variant = (i * 7 + 3) % 6, root = Matrix4x4.TRS(pos, rot, Vector3.one * (.96f + (i * 13 % 9) * .01f)), phase = i * 1.37f, z = pos.z });
            }
            var lo = seats.Count > 0 ? seats[0].pos : Vector3.zero; var hi = lo;
            foreach (var (pos, _) in seats) { lo = Vector3.Min(lo, pos); hi = Vector3.Max(hi, pos); }
            bounds = new Bounds((lo + hi) * .5f, hi - lo + new Vector3(4, 6, 4));
            foreach (var v in variants) foreach (var p in v.parts) p.m = new Matrix4x4[fans.Count];
            Destroy(template);
            int parts = 0; long tris = 0; foreach (var v in variants) foreach (var p in v.parts) { parts++; for (int k = 0; k < p.mesh.subMeshCount; k++) tris += p.mesh.GetIndexCount(k) / 3; }
            Debug.Log($"[Majestic] crowd fans={fans.Count} variantParts={parts} trisPerVariantSet={tris} material={(material ? material.name : "none")} instancing={material && material.enableInstancing}");
            rp = new RenderParams(material)
            {
                shadowCastingMode = ShadowCastingMode.Off, receiveShadows = true,
                worldBounds = bounds,
            };
        }

        void LateUpdate()
        {
            if (!material || fans.Count == 0) return;
            float t = Time.time;
            foreach (var v in variants) foreach (var p in v.parts) p.count = 0;
            for (int f = 0; f < fans.Count; f++)
            {
                var fan = fans[f]; var v = variants[fan.variant];
                // a wave runs along the stand every ~9 s; between waves people clap now and then
                float wave = Mathf.Clamp01(1 - Mathf.Abs(Mathf.Repeat(t * .11f - fan.z / 34f, 1) - .5f) * 7);
                float clap = Mathf.Max(wave, Mathf.Clamp01(Mathf.Sin(t * .7f + fan.phase) * 3 - 2.2f));
                float bob = Mathf.Sin(t * 1.9f + fan.phase) * .012f + wave * .09f;
                var root = Matrix4x4.Translate(new Vector3(0, bob, 0)) * fan.root;
                foreach (var p in v.parts)
                {
                    Matrix4x4 local = p.local;
                    if (p.kind == 1) local = local * Matrix4x4.Rotate(Quaternion.Euler(0, Mathf.Sin(t * .23f + fan.phase) * 18, 0));
                    else if (p.kind >= 2)
                    {
                        float side = p.kind == 2 ? 1 : -1;
                        float lift = clap * (100 + 25 * Mathf.Sin(t * 9 + fan.phase)) ;
                        local = local * Matrix4x4.Rotate(Quaternion.Euler(-lift, 0, side * clap * 12));
                    }
                    p.m[p.count++] = root * local;
                }
            }
            foreach (var v in variants)
                foreach (var p in v.parts)
                    if (p.count > 0)
                        for (int sub = 0; sub < p.mesh.subMeshCount; sub++)
                            Graphics.RenderMeshInstanced(rp, p.mesh, sub, p.m, p.count);
        }
    }
}
