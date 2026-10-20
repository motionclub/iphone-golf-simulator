using System.Collections.Generic;
using GolfArcade.Course;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Majestic
{
    /// The dressing density rule (PLAN §4.3): clustered wildflowers, shrubs, ferns and mossy boulders along both edges of the
    /// play corridor (Z1, 8-25 yd out) and round the green, thinning outward, never in play (only on rough or land outside
    /// the course lies). Meshes are the resort BotanicalKit's own (the course already uses them), coloured per course,
    /// drawn instanced and culled by the view; no shadows (small, near the ground). Biomes swap the mix (snow: drifts of
    /// laden shrubs, desert: cacti and boulders, magma: ferns and dark rock).
    public sealed class MajesticScatter : MonoBehaviour
    {
        sealed class Group { public Mesh mesh; public int sub, variant; public Material mat; public readonly List<Matrix4x4> all = new(); public readonly List<float> keep = new(); public Bounds local; }
        readonly List<Group> groups = new();
        readonly Plane[] planes = new Plane[6];
        public int Instances, Triangles;

        static readonly Dictionary<string, (Mesh mesh, int[] slots, Matrix4x4 toRoot)> kit = new();
        static Shader shader;

        public static MajesticScatter Build(Transform root, Hole hole, MajesticCourses.Kind course, float seaY)
        {
            if (!LoadKit()) return null;
            var go = new GameObject("Majestic scatter"); go.transform.SetParent(root, false);
            var s = go.AddComponent<MajesticScatter>();
            var palette = Palette(course, hole.Number);
            var mix = Mix(course, hole.Number);
            var outer = course == MajesticCourses.Kind.Magma ? new[] { "BOULDER", "FERN" } : hole.Number == 18 ? new[] { "CACTUS", "BOULDER" } : new[] { "SHRUB_0", "SHRUB_1", "BUSH_BROAD", "BOULDER" };
            var rng = new System.Random(hole.Number * 977 + 13);
            var c = hole.Centerline; float half = (float)hole.FairwayWidth * .5f;
            // round 5: r4 put the beds 8-25 yd out and they vanished at camera scale, and a 2 m boulder stood in the rough
            // beside a lie. Z1 = low flower/fern beds hugging the rough edge (3-12 yd out, nothing that blocks a stance);
            // Z2 = shrubs and smaller boulders 22-55 yd out, where no ball plays.
            var near = System.Array.FindAll(mix, n => !n.StartsWith("BOULDER") && n != "CACTUS" && n != "BUSH_BROAD");
            if (near.Length == 0) near = mix;
            for (int i = 1; i < c.Length; i++)
            {
                var a = c[i - 1]; var b = c[i]; double len = a.DistanceTo(b); if (len < 1) continue;
                double dx = (b.X - a.X) / len, dz = (b.D - a.D) / len;
                var along = new Vector3((float)dx, 0, (float)dz);
                for (double t = 2; t < len; t += 4)
                    foreach (int side in new[] { -1, 1 })
                    {
                        float out_ = half + 3 + (float)(rng.NextDouble() * rng.NextDouble()) * 9;     // denser near the corridor
                        var p = new Vector3((float)(a.X + dx * t - dz * side * out_), 0, (float)(a.D + dz * t + dx * side * out_));
                        // 10-18 (Adnan via coordinator: density + variety in the 10-30 yd edge band): a layered bed every ~11 yd
                        // instead of an even sprinkle; the spots in between stay single tufts, so beds read as clusters
                        if (((int)(t / 4) + (side > 0 ? 1 : 0)) % 3 == 0) s.Bed(p, along, new Vector3(-(float)dz * side, 0, (float)dx * side), hole, course, palette, rng, seaY, false);
                        else s.Cluster(p, hole, near, palette, rng, seaY, 1 + rng.Next(2), 1.6f, true);
                        if (rng.NextDouble() < .25)
                        {
                            float far = half + 22 + (float)rng.NextDouble() * 33;
                            var q = new Vector3((float)(a.X + dx * t - dz * side * far), 0, (float)(a.D + dz * t + dx * side * far));
                            s.Cluster(q, hole, outer, palette, rng, seaY, 2 + rng.Next(3), 3.5f, false);
                        }
                    }
            }
            // round 6: tee-side beds, the most-seen camera: low flowers either side of the first 70 yd, 7-16 yd off the line
            // (the lie filter drops any that fall on the tee or fairway)
            {
                var t0 = c[0]; var t1 = c[1]; double tl = t0.DistanceTo(t1);
                double fx = (t1.X - t0.X) / tl, fz = (t1.D - t0.D) / tl;
                for (double t = -8; t < System.Math.Min(70, tl); t += 3)
                    foreach (int side in new[] { -1, 1 })
                    {
                        // r23 structural score: near dressing 20/80; the targets frame the tee shot with beds in both near corners
                        float off = 6 + (float)rng.NextDouble() * (t < 40 ? 12 : 9);
                        var p = new Vector3((float)(t0.X + fx * t - fz * side * off), 0, (float)(t0.D + fz * t + fx * side * off));
                        // the fairway lie is allowed beside / behind the box (|t| <= 12) and, 9+ yd off the line, up to 22 yd ahead:
                        // the tee view's near corners are fairway on most holes and no tee shot comes to rest there (a topped
                        // shot stays on the line)
                        bool teeSide = System.Math.Abs(t) <= 12 || t <= 22 && off >= 9;
                        // r30: a layered bed at every tee-side spot (one in three left the tee view's near band thinner than r27)
                        s.Bed(p, new Vector3((float)fx, 0, (float)fz), new Vector3(-(float)fz * side, 0, (float)fx * side), hole, course, palette, rng, seaY, teeSide, t < 25 ? 1.6f : 1f);
                    }
            }
            // a ring round the green, broken where the approach comes in
            var pin = HoleView.ToWorld(hole.Pin); var last = HoleView.ToWorld(c[c.Length - 2]); var approach = (last - pin); approach.y = 0; approach.Normalize();
            // r26: 20 clusters (was 14). The ring stays 20+ yd from the pin: the greenside rough inside it is where chips and
            // long approaches come to rest, so beds there would hide balls in play
            float ring0 = Mathf.Max(20f, (float)(hole.GreenRadius + hole.FringeWidth) + 8);
            for (int k = 0; k < 20; k++)
            {
                float ang = k * 360f / 20 + (float)rng.NextDouble() * 9;
                var dir = Quaternion.Euler(0, ang, 0) * Vector3.forward;
                if (Vector3.Dot(dir, approach) > .7f) continue;
                var p = pin + dir * (ring0 + (float)rng.NextDouble() * 12);
                s.Bed(p, Vector3.Cross(Vector3.up, dir), dir, hole, course, palette, rng, seaY, false);
            }
            s.Finish();
            return s;
        }

        void Cluster(Vector3 centre, Hole hole, string[] mix, Dictionary<int, Color> palette, System.Random rng, float seaY, int n, float spread, bool low, bool teeSide = false)
        {
            for (int i = 0; i < n; i++)
            {
                var p = centre + new Vector3((float)(rng.NextDouble() - .5) * spread * 2, 0, (float)(rng.NextDouble() - .5) * spread * 2);
                var lie = hole.LieAt(HoleView.ToCourse(p));
                if (lie is CourseLie.Green or CourseLie.Fringe or CourseLie.Tee or CourseLie.Bunker or CourseLie.Water or CourseLie.Ice) continue;
                if (lie == CourseLie.Fairway && !teeSide) continue;
                string name = mix[rng.Next(mix.Length)];
                // sizes as the resort dresser uses them (yd): flowers ~0.9-1.2, shrubs 1.6-2.7 wide x 1.4 tall, boulders 1-2.2
                Vector3 sc = name.StartsWith("BOULDER") ? Vector3.one * (.8f + (float)rng.NextDouble() * .8f)
                           : name.StartsWith("SHRUB") || name.StartsWith("BUSH") ? new Vector3(1.6f + (float)rng.NextDouble() * 1.1f, 1.4f, 1.6f + (float)rng.NextDouble() * 1.1f)
                           : name == "CACTUS" ? Vector3.one * (1.6f + (float)rng.NextDouble() * 1.4f)
                           : Vector3.one * (1.3f + (float)rng.NextDouble() * .6f);
                if (sc.z > 1.5f && name.StartsWith("SHRUB")) sc.z = sc.x;
                if (low && name.StartsWith("SHRUB")) sc = new Vector3(sc.x * .8f, 1f, sc.z * .8f);   // knee-high in Z1
                Place(p, name, sc, 0, palette, rng, seaY);
            }
        }

        /// One instance on the ground (lie already checked); `variant` picks the bloom colour (0 = the course palette).
        void Place(Vector3 p, string name, Vector3 sc, int variant, Dictionary<int, Color> palette, System.Random rng, float seaY, float priority = 1)
        {
            float y = MajesticKit.Ground(p, seaY, out bool land); if (!land) return;
            if (!kit.TryGetValue(name, out var item)) return;
            // this instance's place in the distance thinning (Draw); bed plants (priority .45) stay to ~75 yd, r29 lost the
            // tee-side beds 35-70 yd from the tee camera
            float keepAt = (float)rng.NextDouble() * priority;
            var m = Matrix4x4.TRS(new Vector3(p.x, y - .05f, p.z), Quaternion.Euler(0, (float)rng.NextDouble() * 360, 0), sc) * item.toRoot;
            // 10-19: one ground sample under its middle left the downhill side of a boulder in the air (RockGrounding)
            if (name.StartsWith("BOULDER")) { float drop = RockGrounding.Settle("majestic " + name, item.mesh, m); if (drop > 0) m = Matrix4x4.Translate(Vector3.down * drop) * m; }
            for (int sub = 0; sub < item.mesh.subMeshCount; sub++)
            {
                var g = GroupFor(item.mesh, sub, palette, item.slots[sub], name, item.slots[sub] is 4 or 5 ? variant : 0);
                g.all.Add(m); g.keep.Add(keepAt);
            }
        }

        static readonly Color[] Blooms = { default, new(.96f, .42f, .52f), new(.98f, .78f, .26f), new(.96f, .95f, .90f), new(.64f, .46f, .92f), new(.99f, .62f, .78f) };

        /// A layered bed along the corridor edge (10-18 density + variety): elongated along `along`, rows by depth from the
        /// fairway side (`outward`): low blooms in front, ferns and small shrubs in the middle, tall shrubs / broad bushes at
        /// the back, a few small rocks; two bloom colours per bed. Biomes swap the species. Same lie rules as Cluster.
        void Bed(Vector3 centre, Vector3 along, Vector3 outward, Hole hole, MajesticCourses.Kind course, Dictionary<int, Color> palette, System.Random rng, float seaY, bool teeSide, float fullness = 1)
        {
            along.y = 0; along.Normalize(); outward.y = 0; outward.Normalize();
            bool magma = course == MajesticCourses.Kind.Magma, desert = hole.Number == 18, snow = hole.Number == 17;
            string[] front = magma ? new[] { "FERN" } : snow ? new[] { "SHRUB_1", "FERN" } : desert ? new[] { "FLOWER_GOLD", "FLOWER_CORAL" } : new[] { "FLOWER_CORAL", "FLOWER_GOLD" };
            string[] mid = magma ? new[] { "FERN", "SHRUB_1" } : desert ? new[] { "SHRUB_1", "FLOWER_GOLD" } : new[] { "FERN", "SHRUB_1", "FLOWER_CORAL" };
            string[] back = magma ? new[] { "BUSH_BROAD", "SHRUB_0" } : desert ? new[] { "CACTUS", "SHRUB_0" } : new[] { "SHRUB_0", "BUSH_BROAD", "SHRUB_1" };
            int v1 = 1 + rng.Next(5), v2 = 1 + rng.Next(5);
            float L = 5 + (float)rng.NextDouble() * 7, D = 2.5f + (float)rng.NextDouble() * 2.5f;
            int n = (int)((10 + rng.Next(11)) * fullness);   // r31: the tee view's first 25 yd 1.6x fuller
            for (int i = 0; i < n; i++)
            {
                float u = ((float)rng.NextDouble() - .5f) * L * (1 - .35f * (float)rng.NextDouble()), w = (float)rng.NextDouble();
                var p = centre + along * u + outward * (w * D - D * .2f) + new Vector3((float)rng.NextDouble() - .5f, 0, (float)rng.NextDouble() - .5f) * .6f;
                var lie = hole.LieAt(HoleView.ToCourse(p));
                if (lie is CourseLie.Green or CourseLie.Fringe or CourseLie.Tee or CourseLie.Bunker or CourseLie.Water or CourseLie.Ice) continue;
                if (lie == CourseLie.Fairway && !teeSide) continue;
                string name; Vector3 sc;
                if (rng.NextDouble() < .07 && w > .4f) { name = "BOULDER"; sc = Vector3.one * (.45f + (float)rng.NextDouble() * .45f); }   // small rock accents
                else if (w < .38f) { name = front[rng.Next(front.Length)]; sc = Vector3.one * (1.0f + (float)rng.NextDouble() * .5f); }
                else if (w < .72f) { name = mid[rng.Next(mid.Length)]; sc = name.StartsWith("SHRUB") ? new Vector3(1.1f, .8f + (float)rng.NextDouble() * .3f, 1.1f) : Vector3.one * (1.1f + (float)rng.NextDouble() * .5f); }
                else { name = back[rng.Next(back.Length)]; sc = name == "CACTUS" ? Vector3.one * (1.4f + (float)rng.NextDouble() * 1.2f) : new Vector3(1.5f + (float)rng.NextDouble() * .9f, 1.3f + (float)rng.NextDouble() * .7f, 1.5f + (float)rng.NextDouble() * .9f); }
                if (teeSide && lie == CourseLie.Fairway && sc.y > 1.2f) sc.y = 1.2f;   // nothing tall where the tee camera looks over it
                Place(p, name, sc, rng.NextDouble() < .5 ? v1 : v2, palette, rng, seaY, .45f);
            }
        }

        Group GroupFor(Mesh mesh, int sub, Dictionary<int, Color> palette, int slot, string name, int variant = 0)
        {
            foreach (var g in groups) if (g.mesh == mesh && g.sub == sub && g.variant == variant) return g;
            var mat = new Material(shader) { name = "Majestic scatter " + name + " " + sub + (variant > 0 ? " v" + variant : ""), enableInstancing = true };
            mat.SetColor("_BaseColor", variant > 0 ? Blooms[variant] : palette.TryGetValue(slot, out var c) ? c : Color.gray);
            mat.SetFloat("_Gloss", slot is >= 1 and <= 3 ? .26f : .08f); mat.SetFloat("_Leaf", slot == 0 || slot == 6 ? 0 : 1);
            mat.SetFloat("_Cull", slot == 0 || slot == 6 ? (float)CullMode.Back : (float)CullMode.Off);
            var gr = new Group { mesh = mesh, sub = sub, variant = variant, mat = mat, local = mesh.bounds }; groups.Add(gr); return gr;
        }

        void Finish()
        {
            foreach (var g in groups) { Instances += g.all.Count; Triangles += g.all.Count * (int)(g.mesh.GetIndexCount(g.sub) / 3); }
            Debug.Log($"[MajesticScatter] {Instances} instances in {groups.Count} groups, {Triangles} triangles if all were in view");
        }

        // round 5: drawn per camera from the pipeline's camera callback, so every camera that renders (the rig, a manual
        // Camera.Render() capture, the scene view) gets its own frustum cull; LateUpdate + Camera.main left the capture
        // camera with whatever the main camera had culled. Instances under ~1.5 px are skipped (no visible pop).
        void OnEnable() => RenderPipelineManager.beginCameraRendering += Draw;
        void OnDisable() => RenderPipelineManager.beginCameraRendering -= Draw;
        static readonly Matrix4x4[] batch = new Matrix4x4[1023];
        const float Near = 35, Far = 100;

        void Draw(ScriptableRenderContext ctx, Camera cam)
        {
            if (!cam || cam.cameraType == CameraType.Preview || cam.cameraType == CameraType.Reflection) return;
            GeometryUtility.CalculateFrustumPlanes(cam, planes);
            var eye = cam.transform.position;
            float minRatio = 3f / Mathf.Max(1, cam.pixelHeight) * 2f * Mathf.Tan(cam.fieldOfView * .5f * Mathf.Deg2Rad);
            foreach (var g in groups)
            {
                var rp = new RenderParams(g.mat) { camera = cam, layer = gameObject.layer, shadowCastingMode = ShadowCastingMode.Off, receiveShadows = true, lightProbeUsage = LightProbeUsage.Off };
                int n = 0;
                for (int i = 0; i < g.all.Count; i++)
                {
                    var m = g.all[i];
                    var centre = m.MultiplyPoint3x4(g.local.center); float r = m.lossyScale.x * g.local.extents.magnitude;
                    float d = Vector3.Distance(eye, centre);
                    if (r < minRatio * d) continue;
                    // round 13 budget: the dressing cost 2.5 M triangles in the worst view; past 35 yd the density thins
                    // smoothly to 10 % at 100 yd (r28), each instance at its own random distance (no band pops)
                    if (d > Near && g.keep[i] > Mathf.Lerp(1f, .1f, (d - Near) / (Far - Near))) continue;
                    if (!GeometryUtility.TestPlanesAABB(planes, new Bounds(centre, Vector3.one * r * 2))) continue;
                    batch[n++] = m;
                    if (n == batch.Length) { Graphics.RenderMeshInstanced(rp, g.mesh, g.sub, batch, n); n = 0; }
                }
                if (n > 0) Graphics.RenderMeshInstanced(rp, g.mesh, g.sub, batch, n);
            }
        }

        static bool LoadKit()
        {
            if (!shader) shader = Resources.Load<Shader>("Course/Shaders/GolfBotanical");
            if (!shader) return false;
            if (kit.Count > 0) return true;
            var k = Resources.Load<GameObject>("Course/Resort/BotanicalKit"); if (!k) return false;
            foreach (var mf in k.GetComponentsInChildren<MeshFilter>())
            {
                if (!mf.sharedMesh || mf.name.EndsWith("_FAR")) continue;
                var mats = mf.GetComponent<Renderer>() ? mf.GetComponent<Renderer>().sharedMaterials : new Material[0];
                var slots = new int[mf.sharedMesh.subMeshCount];
                for (int i = 0; i < slots.Length; i++) slots[i] = i < mats.Length && mats[i] ? PaletteIndex(mats[i].name) : Mathf.Min(i, 6);
                kit[mf.name] = (mf.sharedMesh, slots, k.transform.worldToLocalMatrix * mf.transform.localToWorldMatrix);   // the FBX's own axes/scale, as GolfResortDress
            }
            return kit.Count > 0;
        }

        // the resort dresser's material-name -> palette slot rule (GolfResortDress.PaletteIndex)
        static int PaletteIndex(string name)
        {
            if (name.Contains("LEAF_DARK")) return 1; if (name.Contains("LEAF_MID")) return 2; if (name.Contains("LEAF_LIGHT")) return 3;
            if (name.Contains("CORAL")) return 4; if (name.Contains("GOLD")) return 5; if (name.Contains("STONE")) return 6; return 0;
        }

        static string[] Mix(MajesticCourses.Kind course, int hole) => course switch
        {
            MajesticCourses.Kind.Magma => new[] { "FERN", "FERN", "BOULDER", "BOULDER", "SHRUB_0", "BUSH_BROAD" },
            _ when hole == 18 => new[] { "CACTUS", "CACTUS", "BOULDER", "BOULDER", "SHRUB_1", "FLOWER_GOLD" },
            _ when hole == 17 => new[] { "SHRUB_0", "SHRUB_1", "BOULDER", "BUSH_BROAD", "FERN" },
            _ when hole == 20 => new[] { "FLOWER_CORAL", "FLOWER_GOLD", "FLOWER_CORAL", "FLOWER_GOLD", "SHRUB_0", "BUSH_BROAD" },
            _ => new[] { "FLOWER_CORAL", "FLOWER_GOLD", "FLOWER_CORAL", "SHRUB_0", "SHRUB_1", "BUSH_BROAD", "FERN", "BOULDER" },
        };

        /// Palette slots 0 trunk/wood, 1-3 leaf dark/mid/light, 4 coral bloom, 5 gold bloom, 6 stone; per course.
        static Dictionary<int, Color> Palette(MajesticCourses.Kind course, int hole)
        {
            var p = new Dictionary<int, Color>
            {
                [0] = new(.46f, .32f, .18f), [1] = new(.11f, .34f, .17f), [2] = new(.22f, .48f, .20f), [3] = new(.44f, .64f, .26f),
                [4] = new(.96f, .42f, .52f), [5] = new(.98f, .78f, .26f), [6] = new(.48f, .52f, .42f),
            };
            if (course == MajesticCourses.Kind.Cliffside) { p[4] = new(.93f, .40f, .62f); p[5] = new(.98f, .86f, .36f); p[6] = new(.50f, .54f, .44f); }
            if (course == MajesticCourses.Kind.WildIsles) { p[4] = new(.98f, .48f, .34f); p[5] = new(1f, .74f, .22f); }
            if (hole == 17) { p[1] = new(.80f, .86f, .92f); p[2] = new(.86f, .90f, .95f); p[3] = new(.92f, .95f, .98f); p[6] = new(.62f, .70f, .76f); }
            if (hole == 18) { p[6] = new(.78f, .42f, .26f); }
            if (course == MajesticCourses.Kind.Magma) { p[0] = new(.18f, .14f, .14f); p[1] = new(.10f, .24f, .12f); p[2] = new(.18f, .36f, .16f); p[3] = new(.30f, .44f, .18f); p[6] = new(.16f, .14f, .17f); }
            return p;
        }
    }
}
