using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Majestic
{
    /// The landmark kit (work/majestic-landmarks, Blender, 34 assets) at runtime: loads Resources/Majestic/Kit/<Name>,
    /// gives every part its material by the kit's naming (<Name>_Mat -> MajesticDressing, <Name>_FX -> MajesticFX,
    /// <Name>_Impostor -> MajesticImpostor with <Name>_Impostor.png), keeps the FBX's LODGroup, no colliders, no shadows
    /// from the small or far pieces. Kit units are metres; the course is in yards.
    public static class MajesticKit
    {
        public const float YardsPerMeter = 1.0936f;
        static Material dressing, fx;
        static readonly Dictionary<string, Material> impostors = new();

        /// Tints an asset's FX cards (e.g. the volcano plume as dark ash on Magma Open instead of the kit's white steam).
        public static void TintFX(GameObject go, string part, Color tint)
        {
            if (!go) return;
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                if (!r.name.Contains(part)) continue;
                var m = new Material(r.sharedMaterial) { name = r.sharedMaterial.name + " " + part }; m.SetColor("_Tint", tint); r.sharedMaterial = m;
            }
        }

        /// A copy of the piece's meshes with the grey rock darkened (round 6: the kit's mid-grey basalt reads pale under the
        /// Magma dusk; the targets show near-black cliffs). Saturated vertices (lava rims, glow) keep their colour.
        static readonly Dictionary<Mesh, Mesh> darkened = new();
        public static void Darken(GameObject go, float k, Color tint)
        {
            if (!go) return;
            foreach (var mf in go.GetComponentsInChildren<MeshFilter>(true))
            {
                var src = mf.sharedMesh; if (!src) continue;
                if (!darkened.TryGetValue(src, out var m) || !m)
                {
                    var cols = src.colors; if (cols == null || cols.Length == 0) continue;
                    m = Object.Instantiate(src); m.name = src.name + " dark";
                    for (int i = 0; i < cols.Length; i++)
                    {
                        Color.RGBToHSV(cols[i], out _, out float sat, out _);
                        if (sat < .35f) cols[i] = new Color(cols[i].r * k * tint.r, cols[i].g * k * tint.g, cols[i].b * k * tint.b, cols[i].a);
                    }
                    m.colors = cols; darkened[src] = m;
                }
                mf.sharedMesh = m;
            }
        }

        /// One LOD at every distance (no LODGroup): for big ring pieces whose LODGroup picked the flat impostor card from
        /// every course camera (round 7: the caldera walls stayed pale cards and ignored Darken).
        public static void KeepLod(GameObject go, int lod)
        {
            if (!go) return;
            foreach (var g in go.GetComponentsInChildren<LODGroup>(true)) Object.Destroy(g);
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
                if (r.name.Contains("_LOD")) r.gameObject.SetActive(r.name.Contains("_LOD" + lod));
        }

        public static GameObject Spawn(string name, Transform parent, Vector3 position, Quaternion rotation, float scale, bool castShadows)
        {
            var prefab = Resources.Load<GameObject>("Majestic/Kit/" + name);
            if (!prefab) { Debug.LogWarning("[MajesticKit] missing " + name); return null; }
            var go = Object.Instantiate(prefab, parent);
            go.name = "Majestic " + name;
            go.transform.SetPositionAndRotation(position, rotation);
            go.transform.localScale = Vector3.one * scale * YardsPerMeter;
            foreach (var c in go.GetComponentsInChildren<Collider>(true)) Object.Destroy(c);
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++) mats[i] = For(name, mats[i] ? mats[i].name : "");
                r.sharedMaterials = mats;
                bool card = r.name.Contains("_LOD2") || r.sharedMaterials.Length > 0 && r.sharedMaterials[0] == fx;
                r.shadowCastingMode = castShadows && !card && !r.name.Contains("_LOD2") ? ShadowCastingMode.On : ShadowCastingMode.Off;
                r.lightProbeUsage = LightProbeUsage.Off; r.reflectionProbeUsage = ReflectionProbeUsage.Off;
            }
            return go;
        }

        static Material For(string asset, string matName)
        {
            if (matName.Contains("_FX"))
            {
                if (!fx) fx = new Material(Shader.Find("GolfArcade/MajesticFX")) { name = "Majestic kit FX" };
                return fx;
            }
            if (matName.Contains("_Impostor"))
            {
                if (!impostors.TryGetValue(asset, out var m) || !m)
                {
                    m = new Material(Shader.Find("GolfArcade/MajesticImpostor")) { name = asset + " impostor" };
                    var tex = Resources.Load<Texture2D>("Majestic/Kit/" + asset + "_Impostor"); if (tex) m.SetTexture("_BaseMap", tex);
                    impostors[asset] = m;
                }
                return m;
            }
            if (!dressing) dressing = new Material(Shader.Find("GolfArcade/MajesticDressing")) { name = "Majestic kit", enableInstancing = true };
            return dressing;
        }

        /// The ground under `p` (water, sea and the course's own Majestic pieces skipped); `land` false = over the sea.
        static readonly RaycastHit[] hits = new RaycastHit[8];
        public static float Ground(Vector3 p, float seaY, out bool land)
        {
            land = false; float best = seaY;
            int n = Physics.RaycastNonAlloc(new Vector3(p.x, 600, p.z), Vector3.down, hits, 1200, ~0, QueryTriggerInteraction.Ignore);
            for (int i = 0; i < n; i++)
            {
                var c = hits[i].collider; if (!c) continue;
                var nm = c.name; if (nm.Contains("sea") || nm.Contains("Sea") || nm.Contains("WATER") || nm.Contains("Water") || nm.StartsWith("Majestic")) continue;
                if (hits[i].point.y > seaY + .4f && (!land || hits[i].point.y > best)) { best = hits[i].point.y; land = true; }
            }
            return best;
        }
    }
}
