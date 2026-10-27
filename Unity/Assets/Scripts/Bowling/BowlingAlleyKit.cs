using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Bowling
{
    /// The shared alley kit (work/bowling-look/blender/kit.py -> Resources/Bowling/Venue/AlleyKit.fbx): a bank of
    /// twelve lanes (game lane = 0, lanes -6..5) with gutters, capping, kickbacks, markings, the masking bank and
    /// lane numbers, plus a ball return, console, twin monitors and settee per lane pair. Meshes are named
    /// "Group__Slot"; each venue dresses the kit by giving every slot its own material.
    public static class BowlingAlleyKit
    {
        public const int FirstLane = -6, LastLane = 5;
        public const float SetteeFloor = -.18f;          // the settee/lounge floor, one step below the approach
        public const float ApproachBack = -6.4f;         // the settee step, behind the foul line
        /// x of each ball return (between the lanes of a pair), as kit.py PAIRS places them
        public static readonly float[] PairX = { -5.5f * BowlingAlley.LanePitch, -3.5f * BowlingAlley.LanePitch, -1.5f * BowlingAlley.LanePitch,
                                                  .5f * BowlingAlley.LanePitch, 2.5f * BowlingAlley.LanePitch, 4.5f * BowlingAlley.LanePitch };
        public const float SofaZ = -7.6f;
        /// The game lane's pair (kit.py PAIRS[3] = lanes 1 and 0): its two sofas and side table are left out, so the players walk
        /// between the lounge and the approach through that gap (BowlingGame.Route), not through the furniture and the crowd on it.
        public const string GamePair = "Pair3";
        static bool AisleSlot(string group, string slot) => group == GamePair && (slot == "Upholstery" || slot == "SofaBase" || slot == "TableTop" || slot == "TableBase");
        /// outer edges of the bank (it is not symmetric: six lanes left of the game lane, five right)
        public const float BankLeft = (FirstLane - .5f) * BowlingAlley.LanePitch, BankRight = (LastLane + .5f) * BowlingAlley.LanePitch;

        const string Root = "Bowling/Venue/";
        static readonly Dictionary<string, Texture2D> textures = new Dictionary<string, Texture2D>();

        public static Texture2D Tex(string name)
        {
            if (textures.TryGetValue(name, out var t) && t) return t;
            t = Resources.Load<Texture2D>(Root + "Textures/" + name);
            textures[name] = t;
            return t;
        }

        /// A PBR surface from the kit textures "<set>_Albedo/_Normal/_Mask" (any may be missing).
        /// tiling = repeats per UV unit; smoothness scales the mask's alpha.
        public static Material Pbr(string set, Color tint, float smoothness, Vector2 tiling, float normal = 1, float metallic = 0)
        {
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = "Kit " + set };
            m.SetColor("_BaseColor", tint);
            var alb = set == null ? null : Tex(set + "_Albedo");
            if (alb) { m.SetTexture("_BaseMap", alb); m.SetTextureScale("_BaseMap", tiling); }
            var nrm = set == null ? null : Tex(set + "_Normal");
            if (nrm) { m.SetTexture("_BumpMap", nrm); m.SetFloat("_BumpScale", normal); m.EnableKeyword("_NORMALMAP"); }
            var mask = set == null ? null : Tex(set + "_Mask");
            if (mask) { m.SetTexture("_MetallicGlossMap", mask); m.EnableKeyword("_METALLICSPECGLOSSMAP"); }
            m.SetFloat("_Smoothness", smoothness);
            m.SetFloat("_Metallic", metallic);
            // all maps share the base map's tiling in URP Lit
            return m;
        }

        /// Lacquered lane wood with the planar mirror (GolfArcade/BowlingLane + BowlingLaneMirror); plain Pbr if
        /// the shader is missing.
        public static Material Lane(string set, Color tint, float smoothness, float normal = .35f, float mirror = .6f, Vector2? tiling = null)
        {
            var shader = Shader.Find("GolfArcade/BowlingLane");
            if (!shader) return Pbr(set, tint, smoothness, tiling ?? Vector2.one, normal);
            var m = new Material(shader) { name = "Kit lane " + set };
            m.SetTexture("_BaseMap", Tex(set + "_Albedo")); m.SetTextureScale("_BaseMap", tiling ?? Vector2.one);
            m.SetColor("_BaseColor", tint);
            var n = Tex(set + "_Normal"); if (n) m.SetTexture("_BumpMap", n);
            var g = Tex(set + "_Mask"); if (g) m.SetTexture("_MetallicGlossMap", g);
            m.SetFloat("_BumpScale", normal); m.SetFloat("_Smoothness", smoothness); m.SetFloat("_Mirror", mirror);
            return m;
        }

        public static Material Plain(Color c, float smoothness, float metallic = 0) => Pbr(null, c, smoothness, Vector2.one, 1, metallic);

        public static Material Emissive(Color c, float intensity, Texture map = null)
        {
            var m = Plain(Color.black, .5f);
            m.SetColor("_BaseColor", c * .05f);
            m.EnableKeyword("_EMISSION"); m.SetColor("_EmissionColor", c * intensity);
            if (map) { m.SetTexture("_EmissionMap", map); m.SetTexture("_BaseMap", map); m.SetColor("_BaseColor", Color.white * .05f); }
            m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
            return m;
        }

        /// A lit sign facing the bowlers (a cut-out emissive quad: the texture's alpha is the sign's outline).
        public static GameObject Sign(Transform root, string name, string tex, Vector3 centre, Vector2 size, float intensity)
        {
            var t = Tex(tex);
            var m = Emissive(Color.white, intensity, t);
            m.SetFloat("_AlphaClip", 1); m.SetFloat("_Cutoff", .5f); m.EnableKeyword("_ALPHATEST_ON");
            m.SetColor("_BaseColor", new Color(.05f, .05f, .05f, 1));
            var go = GameObject.CreatePrimitive(PrimitiveType.Quad);
            Object.Destroy(go.GetComponent<Collider>());
            go.name = name; go.transform.SetParent(root, false);
            go.transform.localPosition = centre; go.transform.localScale = new Vector3(size.x, size.y, 1);
            var r = go.GetComponent<MeshRenderer>(); r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off;
            return go;
        }

        static readonly HashSet<string> FloorSlots = new HashSet<string> { "SofaBase", "TableBase", "ConsoleTrim", "ReturnTrim", "ReturnBody", "TrenchRock", "Iron" };

        /// Places the kit under `root` and gives each slot the venue's material (slots without one are hidden).
        /// "Ball0".."Ball3" take the venue's ball colours.
        public static GameObject Place(Transform root, Dictionary<string, Material> slots, Material[] balls = null, string asset = "AlleyKit")
        {
            var prefab = Resources.Load<GameObject>(Root + asset);
            if (!prefab) { Debug.LogWarning("[Bowling] " + asset + " missing"); return null; }
            var kit = Object.Instantiate(prefab, root, false);
            kit.name = asset;
            if (!root.GetComponent<BowlingLaneMirror>()) root.gameObject.AddComponent<BowlingLaneMirror>();
            int placed = 0, hidden = 0; long tris = 0;
            foreach (var mr in kit.GetComponentsInChildren<MeshRenderer>(true))
            {
                string n = mr.name; int cut = n.IndexOf("__", System.StringComparison.Ordinal);
                string slot = cut >= 0 ? n.Substring(cut + 2) : n;
                if (cut >= 0 && asset == "AlleyKit" && AisleSlot(n.Substring(0, cut), slot)) { mr.gameObject.SetActive(false); hidden++; continue; }
                Material m = null;
                if (slot.StartsWith("Ball") && balls != null && balls.Length > 0)
                    m = balls[(slot[slot.Length - 1] - '0') % balls.Length];
                else slots.TryGetValue(slot, out m);
                if (!m) { mr.gameObject.SetActive(false); hidden++; continue; }
                mr.sharedMaterial = m;
                // 10-27 ("parts of the alley are bugged to where they flicker"): the kit lays these exactly on a floor plane (the lane
                // markings on the lane, the sofa plinths, table and console feet on the lounge floor, the ball return's trims on the
                // approach, Magma's trench rims), and they z-fought with it as the camera moved. Lifted clear of the plane in world y.
                float lift = slot == "Ink" ? .0015f : FloorSlots.Contains(slot) ? .003f : 0;
                if (lift > 0) mr.transform.position += Vector3.up * lift;
                mr.shadowCastingMode = slot == "Upholstery" || slot.StartsWith("Return") || slot.StartsWith("Console") || slot.StartsWith("Monitor")
                    ? ShadowCastingMode.On : ShadowCastingMode.Off;
                var mf = mr.GetComponent<MeshFilter>();
                if (mf && mf.sharedMesh) for (int k = 0; k < mf.sharedMesh.subMeshCount; k++) tris += mf.sharedMesh.GetIndexCount(k) / 3;
                placed++;
            }
            Debug.Log($"[Bowling] {asset} placed={placed} hidden={hidden} tris={tris}");
            return kit;
        }

        /// A flat textured floor in game metres (tiles = metres per texture repeat).
        public static GameObject Floor(Transform root, string name, Vector3 centre, Vector2 size, Material m, float metresPerTile)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Quad);
            Object.Destroy(go.GetComponent<Collider>());
            go.name = name; go.transform.SetParent(root, false);
            go.transform.localPosition = centre; go.transform.localRotation = Quaternion.Euler(90, 0, 0);
            go.transform.localScale = new Vector3(size.x, size.y, 1);
            var inst = new Material(m);
            inst.SetTextureScale("_BaseMap", new Vector2(size.x / metresPerTile, size.y / metresPerTile));
            go.GetComponent<MeshRenderer>().sharedMaterial = inst;
            return go;
        }

        /// Seats on the kit's settee sofas (two 1.7 m sofas per lane pair), for the instanced crowd.
        public static void SetteeSeats(List<(Vector3 pos, float yaw)> seats)
        {
            int i = 0;
            foreach (float x in PairX)
                foreach (float s in new[] { -1.05f, 1.05f })
                    for (int k = -1; k <= 1; k++, i++)
                    {
                        if (x == PairX[3]) continue;      // the game pair's sofas make way for the players' aisle (GamePair)
                        if ((i * 7) % 5 == 0) continue;   // a few empty places, like a real night out
                        seats.Add((new Vector3(x + s + k * .5f, SetteeFloor + .42f, SofaZ + .02f), 0));
                    }
        }
    }
}
