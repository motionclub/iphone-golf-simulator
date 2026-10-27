using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Bowling
{
    public enum BowlingVenueKind { ClubLanes, NeonNights, TikiShores, MagmaLanes }

    /// Which bowling centre the game is played in (PLAN_BowlingVenues.md). Every venue builds the
    /// same five regulation lanes from the shared lane kit (BowlingClubLanes.Lanes) at the same
    /// coordinates, with the same cameras, light budget and probes; what changes is the room, the
    /// light and the grade:
    ///
    ///   ClubLanes   a sky lounge at the top of the club tower, sunset through the glass
    ///   NeonNights  cosmic bowling at midnight: a black room where everything glows
    ///   TikiShores  open-air lanes under a thatched beach pavilion, late-afternoon sun off the sea
    ///   MagmaLanes  lanes carved into a volcano: lava gutters, lavafalls, moonlight from the crater
    public static class BowlingVenue
    {
        /// What the menu picked (launch message "venue"). BOWL_VENUE=neon|tiki|magma|club forces one for tests.
        public static BowlingVenueKind Selected = BowlingVenueKind.ClubLanes;

        public static BowlingVenueKind Current
        {
            get
            {
                var forced = System.Environment.GetEnvironmentVariable("BOWL_VENUE");
                return string.IsNullOrEmpty(forced) ? Selected : Parse(forced, Selected);
            }
        }

        public static BowlingVenueKind Parse(string key, BowlingVenueKind fallback = BowlingVenueKind.ClubLanes)
        {
            switch ((key ?? "").Trim().ToLowerInvariant().Replace(" ", "").Replace("_", ""))
            {
                case "club": case "clublanes": case "sky": case "lounge": return BowlingVenueKind.ClubLanes;
                case "neon": case "neonnights": case "cosmic": return BowlingVenueKind.NeonNights;
                case "tiki": case "tikishores": case "beach": case "resort": case "tropical": return BowlingVenueKind.TikiShores;
                case "magma": case "magmalanes": case "volcano": case "lava": return BowlingVenueKind.MagmaLanes;
                default: return fallback;
            }
        }

        public static string Title => Current switch
        {
            BowlingVenueKind.NeonNights => "NEON NIGHTS",
            BowlingVenueKind.TikiShores => "TIKI SHORES",
            BowlingVenueKind.MagmaLanes => "MAGMA LANES",
            _ => "CLUB LANES",
        };

        /// Triangles per venue renderer, counted before static batching merged their meshes.
        public static readonly Dictionary<Renderer, long> Built = new Dictionary<Renderer, long>();

        public static BowlingClubLanes.Venue Build(Transform parent, Camera camera)
        {
            AlleyShadows();
            var venue = Current switch
            {
                BowlingVenueKind.NeonNights => BowlingNeonNights.Build(parent, camera),
                BowlingVenueKind.TikiShores => BowlingTikiShores.Build(parent, camera),
                BowlingVenueKind.MagmaLanes => BowlingMagmaLanes.Build(parent, camera),
                _ => BowlingClubLanes.Build(parent, camera),
            };
            // what each renderer drew before batching (the proof film's triangle budget)
            Built.Clear();
            foreach (var r in venue.Root.GetComponentsInChildren<MeshRenderer>(true))
                if (r.TryGetComponent<MeshFilter>(out var mf) && mf.sharedMesh)
                {
                    long t = 0; for (int k = 0; k < mf.sharedMesh.subMeshCount; k++) t += mf.sharedMesh.GetIndexCount(k) / 3;
                    Built[r] = t;
                }
            // the room never moves: batch its hundreds of boxes by material
            if (Application.isPlaying) StaticBatchingUtility.Combine(venue.Root.gameObject);
            return venue;
        }

        // ------------------------------------------------------------------ shared dressing meshes

        /// A faceted boulder: a low-poly sphere pushed in and out by seeded noise, flat-shaded.
        public static Mesh Rock(int seed, int rings = 6, int segments = 9, float roughness = .28f)
        {
            var rng = new System.Random(seed);
            var bumps = new Vector3[5]; var weights = new float[5];
            for (int i = 0; i < bumps.Length; i++) { bumps[i] = Random(rng).normalized; weights[i] = ((float)rng.NextDouble() - .4f) * roughness * 2; }
            var ring = new List<Vector3>();
            for (int r = 0; r <= rings; r++)
            {
                float v = r / (float)rings * Mathf.PI;
                for (int s = 0; s < segments; s++)
                {
                    float u = (s + (r % 2) * .5f) / segments * Mathf.PI * 2;
                    var d = new Vector3(Mathf.Sin(v) * Mathf.Cos(u), Mathf.Cos(v), Mathf.Sin(v) * Mathf.Sin(u));
                    float k = 1 + ((float)rng.NextDouble() - .5f) * roughness;
                    for (int i = 0; i < bumps.Length; i++) k += weights[i] * Mathf.Max(0, Vector3.Dot(d, bumps[i]));
                    ring.Add(d * k);
                    if (r == 0 || r == rings) break;   // the poles are one vertex
                }
            }
            // triangles between the rings (pole, rings 1..n-1, pole), then un-shared for flat shading
            var tris = new List<int>();
            int Ring(int r, int s) => r == 0 ? 0 : r == rings ? ring.Count - 1 : 1 + (r - 1) * segments + ((s % segments) + segments) % segments;
            for (int s = 0; s < segments; s++) { tris.Add(Ring(0, 0)); tris.Add(Ring(1, s + 1)); tris.Add(Ring(1, s)); }
            for (int r = 1; r < rings - 1; r++)
                for (int s = 0; s < segments; s++)
                {
                    int a = Ring(r, s), b = Ring(r, s + 1), c = Ring(r + 1, s), d = Ring(r + 1, s + 1);
                    tris.Add(a); tris.Add(b); tris.Add(c); tris.Add(b); tris.Add(d); tris.Add(c);
                }
            for (int s = 0; s < segments; s++) { tris.Add(Ring(rings - 1, s)); tris.Add(Ring(rings - 1, s + 1)); tris.Add(Ring(rings, 0)); }
            return Flat("Rock" + seed, ring, tris);
        }

        static Vector3 Random(System.Random rng) => new Vector3((float)rng.NextDouble() - .5f, (float)rng.NextDouble() - .5f, (float)rng.NextDouble() - .5f);

        static Mesh Flat(string name, List<Vector3> v, List<int> tris)
        {
            var verts = new Vector3[tris.Count]; var idx = new int[tris.Count];
            for (int i = 0; i < tris.Count; i++) { verts[i] = v[tris[i]]; idx[i] = i; }
            var m = new Mesh { name = name };
            m.vertices = verts; m.triangles = idx;
            m.RecalculateNormals(); m.RecalculateBounds();
            return m;
        }

        /// The alley's own shadow reach (10-27, "parts of the alley flicker"). The shadow settings live on the shared pipeline asset, and the
        /// alley never set them: after a golf round it kept golf's 260-320 m, 4 cascades (as the plaza did, menu-background 10-26), and even
        /// the tier default (32-60 m, one cascade) spreads the map over a reach twice the alley's. Shadow texels of 5-15 cm swim as the camera
        /// moves (the shadow map refits every frame), and the step and sofa shadows on the lounge floor flickered. The alley fits in 34 m from
        /// the lounge cameras to the pins: two cascades, the near one over the approach and the lounge.
        public static void AlleyShadows()
        {
            var urp = GolfArcade.Tennis.TennisQuality.Pipeline;
            if (!urp) return;
            urp.shadowDistance = 34; urp.shadowCascadeCount = 2; urp.cascade2Split = .3f;
        }

        public static GameObject Place(Transform parent, string name, Mesh mesh, Vector3 pos, Vector3 scale, float yaw, Material mat, bool shadows = true)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos; go.transform.localRotation = Quaternion.Euler(0, yaw, 0); go.transform.localScale = scale;
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.AddComponent<MeshRenderer>(); r.sharedMaterial = mat;
            r.shadowCastingMode = shadows ? UnityEngine.Rendering.ShadowCastingMode.On : UnityEngine.Rendering.ShadowCastingMode.Off;
            return go;
        }

        static readonly Dictionary<PrimitiveType, Mesh> primitives = new Dictionary<PrimitiveType, Mesh>();
        /// The built-in primitive's mesh (cube, cylinder, sphere...), for combining.
        public static Mesh Primitive(PrimitiveType type)
        {
            if (primitives.TryGetValue(type, out var m) && m) return m;
            var go = GameObject.CreatePrimitive(type);
            m = go.GetComponent<MeshFilter>().sharedMesh;
            if (Application.isPlaying) Object.Destroy(go); else Object.DestroyImmediate(go);
            return primitives[type] = m;
        }

        public static CombineInstance Part(Mesh mesh, Vector3 pos, Quaternion rot, Vector3 scale) =>
            new CombineInstance { mesh = mesh, transform = Matrix4x4.TRS(pos, rot, scale) };

        /// Many small pieces as one mesh and one draw (palms, rocks, lantern strings).
        public static GameObject Combine(Transform parent, string name, List<CombineInstance> parts, Material mat, bool shadows = true)
        {
            var mesh = new Mesh { name = name, indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            mesh.CombineMeshes(parts.ToArray(), true, true);
            mesh.RecalculateBounds();
            return Place(parent, name, mesh, Vector3.zero, Vector3.one, 0, mat, shadows);
        }

        /// A coconut palm: a curving, tapering trunk and a crown of arched fronds, added to two part
        /// lists (trunk, leaves) so a whole grove is two draws.
        public static void Palm(List<CombineInstance> trunk, List<CombineInstance> leaves, Vector3 at, float height, float lean, float yaw, int seed)
        {
            var rng = new System.Random(seed);
            var cyl = Primitive(PrimitiveType.Cylinder); var cube = Primitive(PrimitiveType.Cube);
            const int Segments = 7;
            float seg = height / Segments;
            var p = at; var up = Vector3.up;
            var bend = Quaternion.Euler(0, yaw, 0) * Vector3.forward;
            for (int i = 0; i < Segments; i++)
            {
                float u = (i + .5f) / Segments;
                var dir = Vector3.Slerp(Vector3.up, bend, lean * u * u).normalized;
                float r = Mathf.Lerp(.2f, .13f, u);
                trunk.Add(Part(cyl, p + dir * seg / 2, Quaternion.FromToRotation(Vector3.up, dir), new Vector3(2 * r, seg / 2 * 1.04f, 2 * r)));
                p += dir * seg; up = dir;
            }
            int fronds = 8 + rng.Next(3);
            for (int f = 0; f < fronds; f++)
            {
                float az = f * 360f / fronds + (float)rng.NextDouble() * 20;
                float len = 2.1f + (float)rng.NextDouble() * .8f;
                var yawQ = Quaternion.AngleAxis(az, Vector3.up);
                // an arch in two pieces: rising a little out of the crown, then drooping
                float pitch1 = -10 - (float)rng.NextDouble() * 15, pitch2 = pitch1 + 38;
                var q1 = yawQ * Quaternion.Euler(pitch1, 0, 0); var q2 = yawQ * Quaternion.Euler(pitch2, 0, 0);
                var a = p + q1 * Vector3.forward * (len * .25f);
                var b = p + q1 * Vector3.forward * (len * .5f) + q2 * Vector3.forward * (len * .25f);
                leaves.Add(Part(cube, a, q1, new Vector3(.42f, .025f, len * .5f)));
                leaves.Add(Part(cube, b, q2, new Vector3(.36f, .025f, len * .5f)));
            }
            trunk.Add(Part(Primitive(PrimitiveType.Sphere), p - up * .1f, Quaternion.identity, Vector3.one * .42f));   // the coconut cluster
        }

        /// A soft round dot (embers, lantern glow cards).
        public static Texture2D Dot(int n = 32)
        {
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, name = "Dot" };
            var px = new Color[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float dx = (x + .5f) / n * 2 - 1, dy = (y + .5f) / n * 2 - 1;
                    float a = Mathf.Pow(Mathf.Clamp01(1 - Mathf.Sqrt(dx * dx + dy * dy)), 2);
                    px[y * n + x] = new Color(1, 1, 1, a);
                }
            tex.SetPixels(px); tex.Apply();
            return tex;
        }

        /// Value noise in 0..1 (cheap, seeded): sand, rock, haze.
        public static float Noise(float x, float y, int seed) => Mathf.PerlinNoise(x + seed * 13.7f, y + seed * 7.1f);

        /// An additive unlit quad material (neon tubes, the swing arc, lavafalls).
        public static Material Additive(Texture tex, Color color)
        {
            var m = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
            if (tex) m.SetTexture("_BaseMap", tex);
            m.SetColor("_BaseColor", color);
            m.SetFloat("_Surface", 1); m.SetFloat("_Blend", 2);
            m.SetOverrideTag("RenderType", "Transparent");
            m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.One); m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.One); m.SetInt("_ZWrite", 0);
            m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            m.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
            return m;
        }

        /// Swaps the main lane's inlaid markings (arrows, dots, range finders) to another material.
        public static void Markings(Transform root, Material m)
        {
            var lane = root.Find("Lane"); if (!lane) return;
            foreach (Transform c in lane)
                if (c.name.StartsWith("Arrow") || c.name.StartsWith("Dot") || c.name.StartsWith("ApproachDot") || c.name.StartsWith("RangeFinder"))
                    if (c.TryGetComponent<MeshRenderer>(out var r)) r.sharedMaterial = m;
        }

        /// A seat for the waiting players at BowlingClubLanes.LoungeZ (where BowlingGame sends them).
        public static void Settee(Transform root, Material seat, Material trim, Material dais = null)
        {
            const float lounge = BowlingClubLanes.LoungeZ;
            // the kit's lounge floor is a step below the approach: the players' settee stands on a dais at approach level
            BowlingClubLanes.Box(root, "SetteeDais", new Vector3(0, BowlingAlleyKit.SetteeFloor / 2, lounge + .2f), new Vector3(3.8f, -BowlingAlleyKit.SetteeFloor, 1.6f), dais ?? trim);
            BowlingClubLanes.Box(root, "Settee", new Vector3(0, .25f, lounge), new Vector3(3.2f, .5f, .7f), seat);
            BowlingClubLanes.Box(root, "SetteeBack", new Vector3(0, .62f, lounge - .38f), new Vector3(3.2f, .75f, .18f), seat);
            BowlingClubLanes.Box(root, "SetteeTrim", new Vector3(0, .51f, lounge + .35f), new Vector3(3.2f, .03f, .04f), trim);
        }

        public static void Ambient(Color sky, Color equator, Color ground)
        {
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = sky; RenderSettings.ambientEquatorColor = equator; RenderSettings.ambientGroundColor = ground;
        }

        public static void Fog(Color c, float start, float end)
        {
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogColor = c; RenderSettings.fogStartDistance = start; RenderSettings.fogEndDistance = end;
        }

        /// A rotated box (the lane kit's boxes are axis-aligned).
        public static GameObject Slab(Transform parent, string name, Vector3 c, Vector3 size, Vector3 euler, Material m)
        {
            var go = BowlingClubLanes.Box(parent, name, c, size, m);
            go.transform.localRotation = Quaternion.Euler(euler);
            return go;
        }
    }

    /// The living part of a venue: scrolling lava, pulsing LEDs, flickering torches, and a flash on
    /// every strike (BowlingGame calls Strike). Materials are the venue's own instances.
    public sealed class BowlingVenueFx : MonoBehaviour
    {
        struct Scroll { public Material M; public Vector2 Speed; public string Map; }
        struct Pulse { public Material M; public Color Base; public float Rate, Depth, Phase; }
        struct Cycle { public Material M; public Color[] Colors; public float Intensity, Period, Phase; }
        struct Flicker { public Light L; public float Base; public float Seed; public Material M; public Color Emission; }
        readonly List<Scroll> scrolls = new List<Scroll>();
        readonly List<Pulse> pulses = new List<Pulse>();
        readonly List<Cycle> cycles = new List<Cycle>();
        readonly List<Flicker> flickers = new List<Flicker>();
        readonly List<(Material m, Color baseColor)> flashes = new List<(Material, Color)>();
        float flash;

        /// URP Lit samples every map with _BaseMap's tiling and offset, so scroll that.
        public void AddScroll(Material m, Vector2 speed, string map = "_BaseMap") => scrolls.Add(new Scroll { M = m, Speed = speed, Map = map });
        public void AddPulse(Material m, float rate, float depth, float phase = 0) => pulses.Add(new Pulse { M = m, Base = m.GetColor("_EmissionColor"), Rate = rate, Depth = depth, Phase = phase });
        public void AddCycle(Material m, Color[] colors, float intensity, float period, float phase = 0) => cycles.Add(new Cycle { M = m, Colors = colors, Intensity = intensity, Period = period, Phase = phase });
        public void AddFlicker(Light l, Material flame = null) => flickers.Add(new Flicker { L = l, Base = l ? l.intensity : 0, Seed = flickers.Count * 7.3f, M = flame, Emission = flame ? flame.GetColor("_EmissionColor") : Color.black });
        /// Materials that blaze up (x3) on a strike and settle over a second.
        public void AddFlash(Material m) { if (m) flashes.Add((m, m.GetColor("_EmissionColor"))); }

        public void Strike() => flash = 1;

        void Update()
        {
            float t = Time.time;
            foreach (var s in scrolls) s.M.SetTextureOffset(s.Map, s.Speed * t);
            foreach (var p in pulses) p.M.SetColor("_EmissionColor", p.Base * (1 + p.Depth * Mathf.Sin(t * p.Rate + p.Phase)));
            foreach (var c in cycles)
            {
                float u = Mathf.Repeat((t + c.Phase) / c.Period, 1) * c.Colors.Length;
                int i = Mathf.FloorToInt(u) % c.Colors.Length;
                var col = Color.Lerp(c.Colors[i], c.Colors[(i + 1) % c.Colors.Length], Mathf.SmoothStep(0, 1, u - Mathf.Floor(u)));
                c.M.SetColor("_EmissionColor", col * c.Intensity);
            }
            foreach (var f in flickers)
            {
                float k = .82f + .18f * Mathf.PerlinNoise(t * 3.1f, f.Seed) + .06f * Mathf.Sin(t * 17 + f.Seed);
                if (f.L) f.L.intensity = f.Base * k;
                if (f.M) f.M.SetColor("_EmissionColor", f.Emission * k);
            }
            if (flash > 0 || flashes.Count > 0)
            {
                float k = 1 + 2 * flash * flash;
                foreach (var (m, c) in flashes) m.SetColor("_EmissionColor", c * k);
                flash = Mathf.Max(0, flash - Time.deltaTime * .9f);
            }
        }
    }
}
