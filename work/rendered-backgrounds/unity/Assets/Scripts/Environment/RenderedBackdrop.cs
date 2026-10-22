using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.EnvironmentArt
{
    /// Per-venue rendered backgrounds (work/rendered-backgrounds): which venues use the rendered sky,
    /// their sky profile, and the distant 3D scenery + cloud impostors built around them.
    /// A venue returns null from SkyProfile until it has passed its gates; it keeps its old path.
    public static class RenderedBackdrop
    {
        public const int TennisResort = 100, TennisSkyscraper = 101, TennisVolcano = 102;
        const string Root = "Environment/RenderedSky/";

        /// Venues switched to the rendered backgrounds. Each joins once it passes its gates; RENDERED_BG_VENUES
        /// (comma list: resort, skyscraper, volcano, golf) overrides for proof runs.
        static readonly string[] Live = { "resort", "skyscraper", "volcano", "golf", "hub" };
        static bool On(string venue)
        {
            var env = System.Environment.GetEnvironmentVariable("RENDERED_BG_VENUES");
            var list = string.IsNullOrEmpty(env) ? Live : env.Split(',');
            return System.Array.IndexOf(list, venue) >= 0;
        }

        public static RenderedSky.Profile SkyProfile(bool tennis, int location)
        {
            if (tennis && location == TennisResort && On("resort"))
                return new RenderedSky.Profile { FogEnd = 7000, SeaLevel = -4f };
            if (tennis && location == TennisSkyscraper && On("skyscraper"))
                // above the cloud sea: clear thin air, the cloud sea mesh fills everything below the horizon
                return new RenderedSky.Profile { FogEnd = 9000, SeaBelow = false, AerialDistance = 26000, HazeScaleHeight = 2500,
                    Cirrus = .32f, CirrusScale = .8f, Saturation = 1.35f };
            if (tennis && location == TennisVolcano && On("volcano"))
                // ash haze over the crater: dustier, warmer air, dark basalt plain below the horizon
                return new RenderedSky.Profile { DriveFogColour = false, Turbidity = 4f, AerialDistance = 4500, HazeScaleHeight = 1600, AshOvercast = .42f,
                    SeaDeep = new Color(.035f, .028f, .03f), SeaReflectance = .12f, SeaLevel = -30f, Cirrus = .2f,
                    UpperTint = new Color(.84f, .78f, .88f), HorizonTint = new Color(1.06f, .93f, .9f), NightTint = new Color(.03f, .015f, .03f) };
            if (!tennis && On("golf"))
            {
                // golf world units are yards: every distance below is metres / 0.9144
                bool magma = System.Array.IndexOf(MagmaHoles, location) >= 0;
                if (magma)
                    return new RenderedSky.Profile { DriveFogColour = false, Turbidity = 4f, AerialDistance = 4900, HazeScaleHeight = 1750, AshOvercast = .42f,
                        SeaDeep = new Color(.035f, .028f, .03f), SeaReflectance = .12f, SeaLevel = -30f, Cirrus = .2f,
                        UpperTint = new Color(.84f, .78f, .88f), HorizonTint = new Color(1.06f, .93f, .9f), NightTint = new Color(.03f, .015f, .03f) };
                return new RenderedSky.Profile { FogEnd = 7600, SeaLevel = -.3f, AerialDistance = 7650, HazeScaleHeight = 1310 };
            }
            return null;
        }

        static readonly int[] MagmaHoles = { 10, 16, 21, 22, 23 };
        const float YardsPerMetre = 1 / .9144f;

        /// Golf: the karst islands out on the open sea round a coastal hole (Backdrop.Place calls this in place
        /// of its old image-to-3D islands when golf is live). Positions follow the hole's own bounds.
        public static bool GolfIslands(Transform parent, Bounds course, Vector3 along)
        {
            if (!RenderedSky.Enabled || !On("golf")) return false;
            var view = GolfArcade.Course.HoleView.Current;
            int number = view && view.Hole != null ? view.Hole.Number : 0;
            if (System.Array.IndexOf(MagmaHoles, number) >= 0) { Landmarks.RemoveAll(l => !l.name.StartsWith("Cloud")); return true; }   // volcanic holes: the crater is the horizon, no islands
            along.y = 0; along.Normalize();
            float baseAz = Mathf.Atan2(along.x, along.z) * Mathf.Rad2Deg;
            float reach = Mathf.Max(course.extents.x, course.extents.z);
            var centre = course.center; centre.y = 0;
            var layout = new Piece[ResortIslands.Length];
            for (int i = 0; i < layout.Length; i++)
            {
                var p = ResortIslands[i];
                // metres -> yards, pushed out past the playable ground
                layout[i] = new Piece { Mesh = p.Mesh, Azimuth = p.Azimuth + baseAz, Distance = (p.Distance + reach * .9144f + 300) * YardsPerMetre, Yaw = p.Yaw, Scale = p.Scale * YardsPerMetre };
            }
            var root = new GameObject("Rendered backdrop scenery").transform; root.SetParent(parent, false);
            root.position = centre;   // layout is relative to the hole's centre
            Scenery(root, layout, -.3f, centre);
            return true;
        }

        /// The plaza hub (and its rooms' outdoor grounds): the hub draws its sky on a dome mesh, not the skybox.
        /// The dome keeps its size and place but is shaded by the rendered sky (sun disc at the real light);
        /// the plaza also gets the rendered clouds. Returns false when the hub is not switched over.
        public static bool HubDome(Transform root, Vector3 centre, float radius)
        {
            if (!RenderedSky.Enabled || !On("hub")) return false;
            // golden hour, airy and pastel like the club's art direction: warm low glow, a lighter upper sky
            var sky = RenderedSky.Install(null, new RenderedSky.Profile { SunsetOverride = .7f, SeaLevel = -.4f, AerialDistance = 6000, HazeScaleHeight = 1200,
                DriveFogColour = false, Saturation = 1.1f, MultiScatter = .4f, Exposure = 16f, UpperTint = new Color(1.4f, 1.3f, 1.12f), Cirrus = .35f });
            var dome = new GameObject("Rendered sky dome");
            dome.transform.SetParent(root, false); dome.transform.position = centre; dome.transform.localScale = Vector3.one * radius;
            dome.AddComponent<MeshFilter>().sharedMesh = Sphere();
            var r = dome.AddComponent<MeshRenderer>(); r.sharedMaterial = sky;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
            r.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off; r.reflectionProbeUsage = UnityEngine.Rendering.ReflectionProbeUsage.Off;
            if (radius > 200 && !GameObject.Find("Rendered backdrop"))
            {
                var bd = new GameObject("Rendered backdrop"); bd.transform.SetParent(root, false);
                Clouds(bd.transform, 777, 24, new Vector2(3.5f, 1.2f), new CloudLayout { FrontShare = 0, BaseMin = 500, BaseMax = 1000 });
            }
            return true;
        }

        static Mesh sphere;
        static Mesh Sphere()
        {
            if (sphere) return sphere;
            const int seg = 48, rings = 24;
            var v = new List<Vector3>(); var t = new List<int>();
            for (int i = 0; i <= rings; i++)
            {
                float e = Mathf.PI * (i / (float)rings - .5f);
                for (int j = 0; j <= seg; j++) { float a = j * Mathf.PI * 2 / seg; v.Add(new Vector3(Mathf.Cos(e) * Mathf.Sin(a), Mathf.Sin(e), Mathf.Cos(e) * Mathf.Cos(a))); }
            }
            for (int i = 0; i < rings; i++) for (int j = 0; j < seg; j++) { int a = i * (seg + 1) + j, b = a + seg + 1; t.AddRange(new[] { a, a + 1, b, a + 1, b + 1, b }); }
            sphere = new Mesh { name = "Rendered sky dome" }; sphere.SetVertices(v); sphere.SetTriangles(t, 0); sphere.RecalculateBounds();
            return sphere;
        }

        /// Called from the venue's own light setup (TennisLook / the venue builders' sky sections), so the
        /// rendered sky is up from the first frame (intro flyover) before DreamEnvironment installs.
        public static void TennisEarly()
        {
            int location = TennisResort + (int)GolfArcade.Tennis.TennisVenue.Current;
            var look = RenderedSky.Enabled ? SkyProfile(true, location) : null;
            if (look == null) return;
            var sky = RenderedSky.Install(null, look);
            if (sky) RenderSettings.skybox = sky;
            Build(null, true, location);
        }

        /// One placed piece of distant scenery: mesh name in the FBX, azimuth (deg from +z toward +x),
        /// distance (m), yaw (deg), uniform scale.
        public struct Piece { public string Mesh; public float Azimuth, Distance, Yaw, Scale; }

        static readonly Piece[] ResortIslands =
        {
            new Piece { Mesh = "Karst_00", Azimuth = 6, Distance = 1450, Yaw = 20, Scale = 1 },
            new Piece { Mesh = "Karst_01", Azimuth = -24, Distance = 1150, Yaw = 140, Scale = 1 },
            new Piece { Mesh = "Karst_02", Azimuth = 33, Distance = 2100, Yaw = 75, Scale = 1 },
            new Piece { Mesh = "Karst_03", Azimuth = -52, Distance = 1900, Yaw = 210, Scale = 1 },
            new Piece { Mesh = "Karst_04", Azimuth = 66, Distance = 1600, Yaw = 300, Scale = 1 },
            new Piece { Mesh = "Karst_05", Azimuth = -88, Distance = 2600, Yaw = 30, Scale = 1 },
            new Piece { Mesh = "Karst_Ridge_0", Azimuth = 14, Distance = 5200, Yaw = 90, Scale = 1 },
            new Piece { Mesh = "Karst_Ridge_1", Azimuth = -38, Distance = 6100, Yaw = 75, Scale = 1 },
            new Piece { Mesh = "Karst_02", Azimuth = 152, Distance = 2400, Yaw = 250, Scale = .9f },
            new Piece { Mesh = "Karst_04", Azimuth = -148, Distance = 3000, Yaw = 10, Scale = 1.1f },
            new Piece { Mesh = "Karst_01", Azimuth = 118, Distance = 1900, Yaw = 320, Scale = .85f },
            new Piece { Mesh = "Karst_Ridge_0", Azimuth = 196, Distance = 7000, Yaw = 160, Scale = 1.2f },
            new Piece { Mesh = "Karst_Ridge_1", Azimuth = 98, Distance = 6600, Yaw = 10, Scale = 1 },
        };

        [System.Serializable] class CloudInfo { public int index; public string kind; public float width_m, height_m, base_from_bottom, tight_width_m, tight_height_m, tight_base_from_bottom; public float[] uv_rect, tight_uv; }
        [System.Serializable] class CloudAtlas { public CloudInfo[] clouds; }

        public static void Build(Transform parent, bool tennis, int location)
        {
            if (SkyProfile(tennis, location) == null) return;
            var existing = GameObject.Find("Rendered backdrop");
            if (existing) return;   // DreamEnvironment re-installs each game; the backdrop stays
            var root = new GameObject("Rendered backdrop");
            root.transform.SetParent(parent, false);
            float sea = RenderedSky.Current ? RenderedSky.Current.Look.SeaLevel : 0;
            switch (location)
            {
                case TennisResort:
                    Scenery(root.transform, ResortIslands, sea);
                    Clouds(root.transform, 2026, 26, new Vector2(5.5f, 2.2f), new CloudLayout());
                    break;
                case TennisSkyscraper:
                    CloudSea();
                    Clouds(root.transform, 101, 22, new Vector2(4f, -1.5f), new CloudLayout { BaseMin = 120, BaseMax = 520, DistMin = 3500, DistMax = 11000, ScaleMin = 1.1f, ScaleMax = 2.0f });
                    break;
                case var _ when !tennis:
                    bool magma = System.Array.IndexOf(MagmaHoles, location) >= 0;
                    float y = YardsPerMetre;
                    // magma holes sit in a crater: fewer, higher ash clouds so they clear the rim
                    Clouds(root.transform, 300 + location, magma ? 22 : 26, new Vector2(5.5f, 2.2f) * y, new CloudLayout {
                        DistMin = 2600 * y, DistMax = 8800 * y, FarMin = 9000 * y, FarMax = 12500 * y, BaseMin = (magma ? 1100 : 650) * y, BaseMax = (magma ? 2200 : 1150) * y,
                        ScaleMin = .9f * y, ScaleMax = 1.6f * y, FrontShare = .3f, Tint = magma ? new Color(.62f, .56f, .55f) : Color.white });
                    break;
                case TennisVolcano:
                    Clouds(root.transform, 102, 16, new Vector2(3f, 1f), new CloudLayout { BaseMin = 700, BaseMax = 1500, DistMin = 3000, DistMax = 9000, Tint = new Color(.62f, .56f, .55f) });
                    break;
            }
        }

        /// The skyscraper's cloud sea: the venue's own 3D cloud-sea mesh keeps its shape, its surface becomes
        /// our Cycles-rendered cloud tops relit by the real light; facades lose the painted cloud texture.
        static void CloudSea()
        {
            var a = Resources.Load<Texture2D>(Root + "CloudSea_A"); var b = Resources.Load<Texture2D>(Root + "CloudSea_B");
            var tint = Resources.Load<Texture2D>(Root + "CloudSea_Tint");
            if (!a || !b) { Debug.LogWarning("[RenderedBackdrop] cloud sea maps missing"); return; }
            var sea = new Material(Resources.Load<Shader>(Root + "RenderedCloudSea")) { name = "Rendered cloud sea" };
            sea.SetTexture("_SeaA", a); sea.SetTexture("_SeaB", b); sea.SetFloat("_TileMetres", 650);   // heads of 40-80 m, like the painting's
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            {
                var mats = r.sharedMaterials; bool changed = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    var m = mats[i]; if (!m) continue;
                    if (m.shader.name == "GolfArcade/TennisCloudAtmosphere") { mats[i] = sea; changed = true; }
                    else if (r.name == "Wisp") { mats[i] = Wisp(a, b); changed = true; }   // drifting puffs under the deck: same rendered cloud, not a sand ramp
                    else if (m.HasProperty("_CloudTops") && RenderedSky.IsPainted(m.GetTexture("_CloudTops")) && tint) m.SetTexture("_CloudTops", tint);
                }
                if (changed) r.sharedMaterials = mats;
            }
        }

        static Material wisp;
        static Material Wisp(Texture2D a, Texture2D b)
        {
            if (wisp) return wisp;
            wisp = new Material(Resources.Load<Shader>(Root + "RenderedCloudSea")) { name = "Rendered cloud wisp" };
            wisp.SetTexture("_SeaA", a); wisp.SetTexture("_SeaB", b);
            wisp.SetFloat("_TileMetres", 260); wisp.SetFloat("_ShapeShade", 1f);
            return wisp;
        }

        // ------------------------------------------------------------------ scenery
        static Material scenery;

        public static void Scenery(Transform root, Piece[] layout, float seaLevel, Vector3 origin = default)
        {
            var source = Resources.Load<GameObject>(Root + "KarstIslands");
            if (!source) { Debug.LogWarning("[RenderedBackdrop] KarstIslands missing"); return; }
            var meshes = new Dictionary<string, Mesh>();
            foreach (var mf in source.GetComponentsInChildren<MeshFilter>(true)) meshes[mf.name] = mf.sharedMesh;
            if (!scenery)
            {
                scenery = new Material(Resources.Load<Shader>(Root + "DistantScenery")) { name = "Distant karst" };
                scenery.SetTexture("_BaseMap", Resources.Load<Texture2D>(Root + "Karst_Albedo"));
                scenery.SetTexture("_NormalMap", Resources.Load<Texture2D>(Root + "Karst_Normal"));
            }
            // one combined mesh = one draw call for the whole distant layer
            var combine = new List<CombineInstance>();
            foreach (var p in layout)
            {
                if (!meshes.TryGetValue(p.Mesh, out var mesh)) { Debug.LogWarning("[RenderedBackdrop] no mesh " + p.Mesh); continue; }
                float a = p.Azimuth * Mathf.Deg2Rad;
                var pos = origin + new Vector3(Mathf.Sin(a) * p.Distance, seaLevel, Mathf.Cos(a) * p.Distance);
                combine.Add(new CombineInstance { mesh = mesh, transform = Matrix4x4.TRS(pos, Quaternion.Euler(0, p.Yaw, 0), Vector3.one * p.Scale) });
            }
            var all = new Mesh { name = "Distant scenery", indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            all.CombineMeshes(combine.ToArray(), true, true, false);
            var go = new GameObject("Distant scenery");
            go.transform.SetParent(root, false); go.transform.position = Vector3.zero;
            go.AddComponent<MeshFilter>().sharedMesh = all;
            Detach(go.AddComponent<MeshRenderer>(), scenery);
            // landmark list for the proof tooling (PARALLAX): piece name + world anchor
            Landmarks.Clear();
            foreach (var p in layout)
            {
                if (!meshes.TryGetValue(p.Mesh, out var mesh)) continue;
                float a = p.Azimuth * Mathf.Deg2Rad;
                var b = mesh.bounds;
                Landmarks.Add((p.Mesh + "@" + p.Azimuth, origin + new Vector3(Mathf.Sin(a) * p.Distance, seaLevel + (b.center.y + b.extents.y * .35f) * p.Scale, Mathf.Cos(a) * p.Distance), Mathf.Max(b.extents.x, b.extents.z) * p.Scale));
            }
        }

        static Vector3 wind_;
        /// Where the cloud shader draws a card centre right now (same drift + wrap as RenderedClouds.shader).
        public static Vector3 Drifted(Vector3 c)
        {
            float half = Mathf.Max(wind_.z, 1000), t = Time.timeSinceLevelLoad;
            float Wrap(float v) { v = (v + half) % (2 * half); if (v < 0) v += 2 * half; return v - half; }
            return new Vector3(Wrap(c.x + wind_.x * t), c.y, Wrap(c.z + wind_.y * t));
        }

        /// Named world anchors of the distant pieces (proof tooling).
        public static readonly List<(string name, Vector3 at, float radius)> Landmarks = new();

        /// Far-field renderers: no shadows, no probes, and bounds that always pass culling (their true
        /// position is beyond the far clip; the vertex shader brings them inside it).
        static void Detach(MeshRenderer r, Material m)
        {
            r.sharedMaterial = m;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
            r.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off; r.reflectionProbeUsage = UnityEngine.Rendering.ReflectionProbeUsage.Off;
            r.allowOcclusionWhenDynamic = false;
            r.bounds = new Bounds(Vector3.zero, Vector3.one * 1e5f);
        }

        // ------------------------------------------------------------------ clouds
        static Material clouds;

        public sealed class CloudLayout { public float DistMin = 2600, DistMax = 8800, FarShare = .25f, FarMin = 9000, FarMax = 12500, BaseMin = 650, BaseMax = 1150, ScaleMin = .9f, ScaleMax = 1.6f, FrontShare = .55f; public Color Tint = Color.white; }

        public static void Clouds(Transform root, int seed, int count, Vector2 wind, CloudLayout L)
        {
            if (System.Environment.GetEnvironmentVariable("RENDERED_CLOUDS") == "0") return;   // dev: perf split
            var json = Resources.Load<TextAsset>(Root + "clouds");
            if (!json) { Debug.LogWarning("[RenderedBackdrop] clouds.json missing"); return; }
            var atlas = JsonUtility.FromJson<CloudAtlas>(json.text);
            if (!clouds || clouds.GetColor("_Tint") != L.Tint)
            {
                clouds = new Material(Resources.Load<Shader>(Root + "RenderedClouds")) { name = "Rendered clouds" };
                clouds.SetColor("_Tint", L.Tint);
                clouds.SetTexture("_SixWayA", Resources.Load<Texture2D>(Root + "CloudSixWay_A"));
                clouds.SetTexture("_SixWayB", Resources.Load<Texture2D>(Root + "CloudSixWay_B"));
            }
            Shader.SetGlobalVector("_RSkyWind", new Vector4(wind.x, wind.y, 14000, 0));
            var rng = new System.Random(seed);
            float R(float a, float b) => a + (float)rng.NextDouble() * (b - a);
            var verts = new List<Vector3>(); var uv = new List<Vector2>(); var centre = new List<Vector4>(); var extra = new List<Vector4>(); var tris = new List<int>();
            var cards = new List<(CloudInfo c, Vector3 pos, float w, float h, bool flip, float jitter)>();
            for (int i = 0; i < count; i++)
            {
                var c = atlas.clouds[rng.Next(atlas.clouds.Length)];
                // more of the sky behind the far baseline (what the gameplay camera sees), the rest all round
                float az = i < count * L.FrontShare ? R(-75, 75) : R(-180, 180);
                float dist = rng.NextDouble() < L.FarShare ? R(L.FarMin, L.FarMax) : R(L.DistMin, L.DistMax), scale = R(L.ScaleMin, L.ScaleMax);
                float baseAlt = R(L.BaseMin, L.BaseMax);
                // tight alpha-bounded card (half the transparent overdraw of the render cell)
                float w = c.tight_width_m * scale, h = c.tight_height_m * scale;
                // the card's bottom edge sits below the cloud base by the render margin
                float bottom = baseAlt - h * c.tight_base_from_bottom;
                var pos = new Vector3(Mathf.Sin(az * Mathf.Deg2Rad) * dist, bottom, Mathf.Cos(az * Mathf.Deg2Rad) * dist);
                cards.Add((c, pos, w, h, rng.NextDouble() < .5, R(.93f, 1.05f)));
            }
            // proof landmarks: the cloud cards' centres (drifted the way the shader drifts them)
            wind_ = new Vector3(wind.x, wind.y, 14000);
            Landmarks.RemoveAll(l => l.name.StartsWith("Cloud"));
            for (int i = 0; i < cards.Count; i++)
                Landmarks.Add(("Cloud" + i, cards[i].pos + Vector3.up * cards[i].h * .55f, 0));
            // far to near: alpha blending inside the one mesh is in triangle order
            cards.Sort((a, b) => b.pos.sqrMagnitude.CompareTo(a.pos.sqrMagnitude));
            foreach (var (c, pos, w, h, flip, jitter) in cards)
            {
                float u0 = c.tight_uv[0], v0 = c.tight_uv[1], du = c.tight_uv[2], dv = c.tight_uv[3];
                int b = verts.Count;
                for (int k = 0; k < 4; k++)
                {
                    float x = (k == 1 || k == 2) ? .5f : -.5f, y = k >= 2 ? 1 : 0;
                    verts.Add(new Vector3(flip ? -x : x, y, 0));
                    uv.Add(new Vector2(u0 + (x + .5f) * du, v0 + y * dv));
                    centre.Add(new Vector4(pos.x, pos.y, pos.z, w));
                    extra.Add(new Vector4(h, jitter, 0, 1));
                }
                tris.AddRange(new[] { b, b + 2, b + 1, b, b + 3, b + 2 });
            }
            var mesh = new Mesh { name = "Rendered cloud cards" };
            mesh.SetVertices(verts); mesh.SetUVs(0, uv); mesh.SetUVs(1, centre); mesh.SetUVs(2, extra); mesh.SetTriangles(tris, 0);
            mesh.bounds = new Bounds(Vector3.zero, Vector3.one * 1e5f);
            var go = new GameObject("Rendered clouds"); go.transform.SetParent(root, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            Detach(go.AddComponent<MeshRenderer>(), clouds);
        }
    }
}
