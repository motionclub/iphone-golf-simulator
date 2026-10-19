using System.Collections.Generic;
using GolfArcade.Course;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace GolfArcade.Majestic
{
    /// The golf dressing per course (chat 10). Replaces MajesticGolf as the golf Kit (hook lines in MajesticVenue):
    ///   life      Cliffside and Wild Isles keep chat 9's sky life (balloons, gulls, boats, whale); none on Magma Open
    ///   shore     every sea hole: shallows + foam round the island (MajesticShore)
    ///   kit       the hole's landmarks and set pieces (MajesticHoleKit, Blender kit work/majestic-landmarks)
    ///   scatter   clustered corridor and green dressing (MajesticScatter)
    ///   sea       ocean colours per course (Restyle, undone exactly when switched off)
    ///   lift      a small per-course lift volume: the targets' turf is the same hue as today's but less saturated
    ///             (blue lifted ~0.15 vs 0.02), which a channel lift gives without desaturating the sky
    ///   budget    make-room shadow proxies (MajesticBudget)
    ///   haze      round 5: EnvironmentLook's depth layers (90/280/900 m, up to 72 % toward RenderedSky's grey horizon) washed
    ///             the sea, the far islands and the caldera walls pale; the targets keep saturated colour to ~1 km, so each
    ///             frame (after RenderedSky) the layers move out and the fog colour leans to the course's own haze
    public static class MajesticCourseKit
    {
        static MajesticCourses.Kind course;
        static Volume lift;

        public static void Build(Transform root, MajesticLook look)
        {
            var hole = MajesticGolf.Hole; if (hole == null) return;
            course = MajesticCourses.CourseOf(hole.Number);
            fogStart = look != null ? look.FogStart : 0; fogEnd = look != null ? look.FogEnd : 0;
            logged = false;
            if (course != MajesticCourses.Kind.Magma) MajesticGolf.Build(root, look);
            bool sea = HasSea();
            MajesticShore.LastLines = new();
            if (sea) MajesticShore.Build(root, look, CourseBounds(), 0f);
            MajesticHoleKit.Build(root, hole, MajesticGolf.Tee, MajesticGolf.Pin, MajesticGolf.Forward, 0f);
            int coast = MajesticCoastKit.Build(root, hole, course, MajesticGolf.Tee, MajesticGolf.Pin, 0f);   // shore tiles + lie-placed set pieces
            bool back = sea && course != MajesticCourses.Kind.Magma && BackSkyline(root, (MajesticGolf.Tee + MajesticGolf.Pin) * .5f);
            foreach (var t in root.GetComponentsInChildren<Transform>(true))
                if (t.name.Contains("Lighthouse_Beam")) t.gameObject.SetActive(false);   // a daytime course: no sweeping beam
            int lavaGround = course == MajesticCourses.Kind.Magma ? MajesticLavaGround.Apply() : 0;   // ash rough -> glowing basalt seams
            if (course != MajesticCourses.Kind.Magma) MajesticLavaGround.Restore();
            var scatter = MajesticScatter.Build(root, hole, course, 0f);
            Lift(root, course);
            if (HoleView.Current) MajesticBudget.Apply(HoleView.Current.transform.root);
            Debug.Log($"[MajesticCourseKit] hole {hole.Number} {course}: sea={sea} shore={(root.Find("Majestic shore") ? "yes" : "no")} " +
                      $"kit={root.GetComponentsInChildren<LODGroup>(true).Length} lodgroups scatter={(scatter ? scatter.Instances : 0)} " +
                      $"shadowProxies={MajesticBudget.ProxiedRenderers} savedShadowTris={MajesticBudget.SavedTriangles} farTreeCells={MajesticBudget.FarCells} farSavedTris={MajesticBudget.FarSavedTriangles} lavaGround={lavaGround} coastKit={coast} backSkyline={back}");
        }

        public static void Animate(MajesticLook look, float t)
        {
            if (course != MajesticCourses.Kind.Magma) MajesticGolf.Animate(look, t);
            Haze();
        }

        static readonly int LayersId = Shader.PropertyToID("_EnvironmentDepthLayers");
        static readonly Vector4 LayersWas = new(90, 280, 900, .72f);   // EnvironmentLook.Select
        static bool hazed; static float fogStart, fogEnd;
        static readonly int HazeId = Shader.PropertyToID("_EnvironmentHazeColor");
        static bool magmaHazed; static Vector4 hazeWas; static float ashWas, sunsetWas, horSatWas; static Color horTintWas, upperWas; static bool logged; static GolfArcade.EnvironmentArt.RenderedSky ashSky;
        static void UnMagma()
        {
            if (!magmaHazed) return;
            Shader.SetGlobalVector(HazeId, hazeWas);
            if (ashSky && GolfArcade.EnvironmentArt.RenderedSky.Current == ashSky) { ashSky.Look.AshOvercast = ashWas; ashSky.Look.SunsetOverride = sunsetWas; ashSky.Look.HorizonTint = horTintWas; ashSky.Look.HorizonSaturation = horSatWas; ashSky.Look.UpperTint = upperWas; }
            magmaHazed = false; ashSky = null;
        }
        static void Haze()
        {
            var (layers, tint, lean) = course switch
            {
                MajesticCourses.Kind.Cliffside => (new Vector4(320, 1100, 4200, .72f), new Color(.58f, .74f, .95f), .7f),
                MajesticCourses.Kind.WildIsles => (new Vector4(300, 1000, 3800, .72f), new Color(.93f, .80f, .62f), .55f),
                MajesticCourses.Kind.Magma => (new Vector4(260, 900, 3000, .72f), new Color(.30f, .14f, .20f), .85f),
                _ => (LayersWas, Color.clear, 0f),
            };
            Shader.SetGlobalVector(LayersId, layers); hazed = lean > 0;
            // round 9, Magma: the far crater land hazes toward _EnvironmentHazeColor (lavender) and chat 2's Magma sky
            // profile carries AshOvercast .42, which greys the whole dusk; the clear-weather targets show a dark rim under an
            // orange-magenta sky. Both are overridden here and restored exactly when the layer switches off.
            // Wild Isles: RenderedSky reads its own sky material's _Sunset, not chat 9's, so the golden hour goes through its
            // SunsetOverride (as the hub does)
            var sky = GolfArcade.EnvironmentArt.RenderedSky.Current;
            if (course is MajesticCourses.Kind.Magma or MajesticCourses.Kind.WildIsles)
            {
                if (magmaHazed && sky != ashSky) UnMagma();   // a new hole installed a new sky: start from its own values
                if (!magmaHazed) { hazeWas = Shader.GetGlobalVector(HazeId); ashSky = sky; ashWas = sky ? sky.Look.AshOvercast : 0; sunsetWas = sky ? sky.Look.SunsetOverride : -1; if (sky) { horTintWas = sky.Look.HorizonTint; horSatWas = sky.Look.HorizonSaturation; upperWas = sky.Look.UpperTint; } magmaHazed = true; }
                bool magma = course == MajesticCourses.Kind.Magma;
                Shader.SetGlobalVector(HazeId, magma ? new Vector4(.07f, .025f, .04f, 1) : hazeWas);
                if (sky)
                {
                    sky.Look.AshOvercast = magma ? Mathf.Min(ashWas, .12f) : ashWas;
                    sky.Look.SunsetOverride = magma ? .85f : MajesticGolf.Hole != null && MajesticGolf.Hole.Number == 17 ? .3f : .6f;
                    // r21 coverage: the Magma dusk read violet-grey; the targets glow orange at the horizon under a saturated violet
                    // r23 structural score: Wild Isles sky_hour 0/30 (targets: honey-gold horizon under warm cloud); 17 stays cooler (snow)
                    bool snow = MajesticGolf.Hole != null && MajesticGolf.Hole.Number == 17;
                    sky.Look.HorizonTint = magma ? new Color(1.18f, .86f, .74f) : snow ? new Color(1.08f, .96f, .90f) : new Color(1.20f, .98f, .74f);
                    sky.Look.HorizonSaturation = magma ? 1.35f : snow ? 1.15f : 1.3f;
                    sky.Look.UpperTint = magma ? new Color(.78f, .62f, .98f) : snow ? new Color(.95f, .96f, 1.02f) : new Color(1.0f, .93f, .86f);
                }
                if (!logged) { logged = true; Debug.Log($"[MajesticCourseKit] haze {course}: sky={(sky ? sky.name : "none")} ash={(sky ? sky.Look.AshOvercast : -1)} sunsetOverride={(sky ? sky.Look.SunsetOverride : -1)} skybox={(RenderSettings.skybox ? RenderSettings.skybox.name : "none")}"); }
            }
            else UnMagma();
            if (lean > 0) RenderSettings.fogColor = Color.Lerp(RenderSettings.fogColor, tint, lean);
            if (lean > 0 && fogEnd > 0) { RenderSettings.fogStartDistance = fogStart; RenderSettings.fogEndDistance = fogEnd; }   // RenderedSky may reset the fog end
        }

        // ---- sea colours (reversible)
        static readonly Dictionary<Material, (Color sh, Color de, Color sk, float sp, float pop)> seaWas = new();
        static readonly int Sh = Shader.PropertyToID("_Shallow"), De = Shader.PropertyToID("_Deep"), Sk = Shader.PropertyToID("_Sky"), Sp = Shader.PropertyToID("_Sparkle"), Pop = Shader.PropertyToID("_ResortPop");
        public static void Restyle(bool on, MajesticLook look)
        {
            if (!on || look == null || !look.Active)
            {
                foreach (var kv in seaWas) if (kv.Key) { kv.Key.SetColor(Sh, kv.Value.sh); kv.Key.SetColor(De, kv.Value.de); kv.Key.SetColor(Sk, kv.Value.sk); kv.Key.SetFloat(Sp, kv.Value.sp); kv.Key.SetFloat(Pop, kv.Value.pop); }
                seaWas.Clear(); if (lift) lift.enabled = false;
                if (hazed) { Shader.SetGlobalVector(LayersId, LayersWas); hazed = false; }
                UnMagma(); MajesticLavaGround.Restore();
                return;
            }
            if (lift) lift.enabled = true;
            if (look.SeaDeep == default) return;
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                foreach (var m in r.sharedMaterials)
                {
                    if (!m || m.shader == null || m.shader.name != "GolfArcade/GolfOcean") continue;
                    if (!seaWas.ContainsKey(m)) seaWas[m] = (m.GetColor(Sh), m.GetColor(De), m.GetColor(Sk), m.GetFloat(Sp), m.HasProperty(Pop) ? m.GetFloat(Pop) : 0);
                    m.SetColor(Sh, look.SeaShallow); m.SetColor(De, look.SeaDeep); m.SetColor(Sk, look.SeaSky); m.SetFloat(Sp, look.SeaSparkle);
                    if (m.HasProperty(Pop)) m.SetFloat(Pop, course == MajesticCourses.Kind.Magma ? 0 : 1);
                }
        }

        static void Lift(Transform root, MajesticCourses.Kind kind)
        {
            if (!lift)
            {
                var go = new GameObject("Majestic course lift"); go.transform.SetParent(root.parent ? root.parent : root, false);
                lift = go.AddComponent<Volume>(); lift.isGlobal = true; lift.priority = 51;
                lift.profile = ScriptableObject.CreateInstance<VolumeProfile>();
            }
            var p = lift.profile;
            if (!p.TryGet(out LiftGammaGain lgg)) lgg = p.Add<LiftGammaGain>(true);
            lgg.lift.overrideState = true;
            lgg.lift.value = kind switch
            {
                MajesticCourses.Kind.Cliffside => new Vector4(.0f, .005f, .045f, 0),
                MajesticCourses.Kind.WildIsles => new Vector4(.015f, .0f, .03f, 0),
                MajesticCourses.Kind.Magma => new Vector4(0, .005f, .03f, 0),
                _ => Vector4.zero,
            };
            lift.enabled = MajesticVenue.Enabled;
        }

        /// Cover r18: every green-back view looked back at an empty horizon. Chat 2's island ring (RenderedBackdrop "Distant
        /// scenery", one combined world-space mesh) is dense ahead of the hole and sparse and far behind it; a copy turned
        /// 180 deg about the hole centre and drawn in to 85 % gives the reverse views the same layered islands.
        static bool BackSkyline(Transform root, Vector3 centre)
        {
            MeshFilter src = null;
            foreach (var mf in Object.FindObjectsByType<MeshFilter>(FindObjectsSortMode.None))
                if (mf.name == "Distant scenery" && mf.sharedMesh && mf.gameObject.activeInHierarchy) { src = mf; break; }
            if (!src) return false;
            var r = src.GetComponent<MeshRenderer>(); if (!r) return false;
            centre.y = 0;
            var pivot = new GameObject("Majestic back skyline").transform; pivot.SetParent(root, true);
            pivot.SetPositionAndRotation(centre, Quaternion.Euler(0, 180, 0)); pivot.localScale = Vector3.one * .85f;
            var go = new GameObject("Majestic back skyline mesh"); go.transform.SetParent(pivot, false);
            go.transform.localPosition = src.transform.position - centre;
            // r24 budget: the whole 360 deg copy (59 k tris) was drawn in forward views too; keep only the triangles that land
            // behind the hole (= ahead of it in the source) so forward cameras cull it
            var mesh = src.sharedMesh; if (!mesh.isReadable) return false;
            var fwd = MajesticGolf.Forward; fwd.y = 0; fwd.Normalize();
            var v = mesh.vertices; var tris = mesh.triangles; var keep = new List<int>(tris.Length / 2);
            for (int i = 0; i < tris.Length; i += 3)
            {
                var c = (v[tris[i]] + v[tris[i + 1]] + v[tris[i + 2]]) / 3f + src.transform.position - centre;
                if (Vector3.Dot(c, fwd) > 0) { keep.Add(tris[i]); keep.Add(tris[i + 1]); keep.Add(tris[i + 2]); }
            }
            var half = Object.Instantiate(mesh); half.name = "Majestic back skyline"; half.SetTriangles(keep, 0, true);
            go.AddComponent<MeshFilter>().sharedMesh = half;
            var copy = go.AddComponent<MeshRenderer>(); copy.sharedMaterials = r.sharedMaterials;
            copy.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; copy.receiveShadows = false;
            copy.lightProbeUsage = LightProbeUsage.Off; copy.reflectionProbeUsage = ReflectionProbeUsage.Off;
            return true;
        }

        static bool HasSea()
        {
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                if (r.name == "Open sea" && r.enabled && r.gameObject.activeInHierarchy) return true;
            return false;
        }

        /// The playable island: every renderer of the hole except the sea, the backdrop and anything far out.
        static Bounds CourseBounds()
        {
            var view = HoleView.Current; var b = new Bounds(MajesticGolf.Tee, Vector3.one);
            b.Encapsulate(MajesticGolf.Pin);
            if (!view) return b;
            foreach (var r in view.GetComponentsInChildren<Renderer>())
            {
                if (!r.enabled) continue;
                var n = r.name; var p = r.transform.parent ? r.transform.parent.name : "";
                if (n == "Open sea" || p == "Backdrop" || n.Contains("backdrop") || n.Contains("Backdrop") || n.StartsWith("Majestic")) continue;
                if (r.bounds.size.x > 2000 || r.bounds.size.z > 2000) continue;
                b.Encapsulate(r.bounds);
            }
            return b;
        }
    }
}
