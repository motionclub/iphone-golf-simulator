using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace GolfArcade.Course
{
    /// Light, sky and fog for the Golf scene's postcard holes (8 Needle, 9 Split, 10 Crater).
    /// The recipe is TennisLook.LightScene's (warm key ~2.3 with soft shadows, cool fill ~0.8 without,
    /// a rim, trilight ambient, linear fog, the painted TennisSky) reimplemented here WITHOUT calling it:
    /// LightScene also spawns the hero rim light, and the tennis files are frozen.
    /// NO POST-PROCESSING: the project's renderers (TennisURP_Renderer, HeroBaseStudio_Renderer) have no PostProcessData, so
    /// URP renders no post anywhere (no bloom, no ACES, no vignette). The golf look is therefore built from lights and emission
    /// alone, there is no tone mapper (lit values clip at 1.0), and this class creates no Volume and turns post OFF on the golf
    /// camera, so the look cannot change if a renderer ever gets PostProcessData. RUNTIME.md section 7 has the evidence.
    /// Every other hole number (hole 7, Cliffside, Meadow) keeps the legacy golf numbers exactly.
    /// All numbers live in `Holes` below; RUNTIME.md (work/postcard-look) explains each.
    public static class GolfAtmosphere
    {
        /// One hole's atmosphere. Angles: azimuth in degrees RELATIVE to the hole's tee->pin heading
        /// (0 = straight down the hole, -90 = left of the golfer at address), elevation above the horizon.
        /// Colours are sRGB as authored (Unity converts lights, ambient and fog in a linear project).
        public sealed class Look
        {
            public string Name;
            public float SunAzimuth, SunElevation, SunIntensity = 2.3f, ShadowStrength = .72f;
            public Color SunColor = new(1f, .90f, .76f);
            public float FillAzimuth, FillElevation, FillIntensity = .8f;
            public Color FillColor = new(.84f, .90f, 1f);
            /// True: the fill is NOT a directional light but is added to the ambient sky colour (its irradiance on flat ground, exactly).
            /// Crater needs this: every additional directional takes one of a renderer's per-object light slots (2 in TennisURP, 4 in
            /// HeroBaseStudioURP), and the LAVA_LIGHT point lights are the only thing that lights the basalt from below.
            public bool FoldFillIntoAmbient;
            public float RimAzimuth, RimElevation, RimIntensity;          // RimIntensity 0 = no rim directional
            public Color RimColor = new(1f, .8f, .58f);
            public Color AmbientSky, AmbientEquator, AmbientGround;
            public Color FogColor; public float FogStart, FogEnd;
            public string SkyTexture;                                    // Resources path of the painted panorama
            public bool CoolSky;                                         // use a cooled copy (warm haze -> blue-white); Course/Look/Sky_Split_C wins if present
            public float SkyHeadingOffset, SkyExposure = .95f;          // painting centre relative to the tee->pin heading
            public Color SkyHorizon, SkyZenith, SkySea, SkySunColor;
            public float FallbackHeading;                                // tee->pin heading when no HoleView is built yet
        }

        public static readonly Dictionary<int, Look> Holes = new()
        {
            // Needle: golden afternoon over a deep blue sea; the key low on the front-left like needle.jpg,
            // the painting's warm, sunlit left half in front of the golfer.
            [8] = new Look
            {
                Name = "Needle", FallbackHeading = -1.0f,
                SunAzimuth = -50, SunElevation = 30, SunIntensity = 2.3f, SunColor = new(1f, .86f, .66f), ShadowStrength = .72f,
                FillAzimuth = 160, FillElevation = 35, FillIntensity = .8f, FillColor = new(.80f, .88f, 1f),
                RimAzimuth = 40, RimElevation = 10, RimIntensity = .5f, RimColor = new(1f, .78f, .55f),
                AmbientSky = new(.42f, .58f, .86f), AmbientEquator = new(.68f, .60f, .52f), AmbientGround = new(.20f, .30f, .34f),
                FogColor = new(.74f, .82f, .90f), FogStart = 200, FogEnd = 1500,
                SkyTexture = "Tennis/Environment/SkyPanorama", SkyHeadingOffset = 45, SkyExposure = .95f,
                SkyHorizon = new(1f, .86f, .70f), SkyZenith = new(.18f, .45f, .90f), SkySea = new(.16f, .33f, .58f), SkySunColor = new(1f, .80f, .52f),
            },
            // Split: bright clear blue day; the sun higher, the key warm-neutral, a bluer fill; the painting's
            // blue, cumulus right half in front of the golfer.
            // (A higher sun raises N.L on the flat ground: at 55 deg / 2.2 the old flat rough rendered (102,221,79), clipped.
            //  42 deg keeps the sun "higher than Needle" (30) with the tennis key/fill numbers; ambient = the tennis trilight.)
            // The phone camera sees only the painting's lowest ~13 deg, which is warm peach haze: Split gets a cooled copy
            // (CoolPanorama) so the horizon reads clear blue-white, not sunset.
            [9] = new Look
            {
                Name = "Split", FallbackHeading = -1.2f,
                SunAzimuth = -75, SunElevation = 42, SunIntensity = 2.3f, SunColor = new(1f, .95f, .86f), ShadowStrength = .70f,
                FillAzimuth = 150, FillElevation = 40, FillIntensity = .8f, FillColor = new(.74f, .85f, 1f),
                RimAzimuth = 30, RimElevation = 14, RimIntensity = .3f, RimColor = new(1f, .92f, .80f),
                AmbientSky = new(.42f, .58f, .86f), AmbientEquator = new(.62f, .64f, .60f), AmbientGround = new(.20f, .28f, .26f),
                FogColor = new(.72f, .84f, .95f), FogStart = 220, FogEnd = 1700,
                SkyTexture = "Tennis/Environment/SkyPanorama", CoolSky = true, SkyHeadingOffset = -45, SkyExposure = 1.0f,
                SkyHorizon = new(.85f, .92f, 1f), SkyZenith = new(.16f, .46f, .92f), SkySea = new(.14f, .36f, .62f), SkySunColor = new(1f, .95f, .85f),
            },
            // Crater: volcano dusk (TennisVenueBuilder.Volcano.Light's palette): warm-orange key, purple/ember trilight,
            // smoky sky. NO rim directional: AdditionalLightsPerObjectLimit is 2, so the lava's LAVA_LIGHT_nn point
            // lights (GolfLook.DressModel) are the rim, from below, and keep a slot next to the fill.
            // Key colour: the volcano court's (1,.52,.26) at 18 deg turned the grass BROWN (measured (155,134,51) on the flat
            // tee green); crater.jpg's grass is lime. (1,.80,.58) at 32 deg still reads dusk-orange, and GolfLook.HoleTint gives
            // the crater's grass materials a greener tint so the emerald albedos land on lime instead of olive.
            [10] = new Look
            {
                Name = "Crater", FallbackHeading = 57.7f,
                SunAzimuth = 40, SunElevation = 32, SunIntensity = 2.3f, SunColor = new(1f, .80f, .58f), ShadowStrength = .78f,
                FillAzimuth = 170, FillElevation = 35, FillIntensity = .55f, FillColor = new(.62f, .55f, .90f), FoldFillIntoAmbient = true,
                RimIntensity = 0,
                AmbientSky = new(.34f, .24f, .40f), AmbientEquator = new(.55f, .30f, .22f), AmbientGround = new(.60f, .22f, .08f),
                FogColor = new(.42f, .19f, .14f), FogStart = 120, FogEnd = 1000,
                SkyTexture = "Course/Look/Sky_Crater_C", SkyHeadingOffset = 0, SkyExposure = .9f,
                SkyHorizon = new(.95f, .45f, .18f), SkyZenith = new(.14f, .09f, .14f), SkySea = new(.30f, .12f, .08f), SkySunColor = new(1f, .45f, .15f),
            },
        };

        static Light fill, rim;
        static readonly Dictionary<int, Material> skies = new();
        static Texture2D craterFallback;

        // the scene's own settings, captured before the first change, so a legacy hole gets them back
        static bool captured;
        static Material sceneSkybox;
        static AmbientMode sceneAmbientMode;
        static Light sceneSun;

        public static bool Handles(int holeNumber) => Holes.ContainsKey(holeNumber);

        /// Light the Golf scene for this hole. `camera` may be null (GolfGame.Awake runs before the rig exists;
        /// StartHole calls again with it).
        public static void Apply(Light sun, Camera camera, int holeNumber)
        {
            if (!captured) { captured = true; sceneSkybox = RenderSettings.skybox; sceneAmbientMode = RenderSettings.ambientMode; sceneSun = RenderSettings.sun; }
            if (!Holes.TryGetValue(holeNumber, out var look)) { Legacy(sun, camera); return; }
            float heading = Heading(holeNumber, look);

            if (sun)
            {
                sun.type = LightType.Directional;
                sun.transform.rotation = Quaternion.LookRotation(-Direction(heading + look.SunAzimuth, look.SunElevation));
                sun.color = look.SunColor; sun.intensity = look.SunIntensity;
                sun.shadows = LightShadows.Soft; sun.shadowStrength = look.ShadowStrength;
                sun.shadowBias = .05f; sun.shadowNormalBias = .4f;
                RenderSettings.sun = sun;
            }
            fill = Directional(fill, "Golf fill", look.FillColor, look.FoldFillIntoAmbient ? 0 : look.FillIntensity, Direction(heading + look.FillAzimuth, look.FillElevation));
            rim = Directional(rim, "Golf rim", look.RimColor, look.RimIntensity, Direction(heading + look.RimAzimuth, look.RimElevation));

            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = AmbientSkyOf(look);
            RenderSettings.ambientEquatorColor = look.AmbientEquator;
            RenderSettings.ambientGroundColor = look.AmbientGround;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogColor = look.FogColor;
            RenderSettings.fogStartDistance = look.FogStart; RenderSettings.fogEndDistance = look.FogEnd;

            var sky = Sky(holeNumber, look, heading);
            if (sky) RenderSettings.skybox = sky;

            if (camera)
            {
                camera.clearFlags = CameraClearFlags.Skybox;
                camera.backgroundColor = look.FogColor;
                SetupCamera(camera, true);
            }
        }

        /// The ambient sky colour a hole renders with: the table's, plus (FoldFillIntoAmbient) the fill's irradiance on flat ground
        /// (colour x intensity x sin(elevation), added in linear space), so the ground keeps the brightness the fill gave it.
        public static Color AmbientSkyOf(Look look)
        {
            if (!look.FoldFillIntoAmbient || look.FillIntensity <= 0) return look.AmbientSky;
            var linear = look.AmbientSky.linear + look.FillColor.linear * (look.FillIntensity * Mathf.Sin(look.FillElevation * Mathf.Deg2Rad));
            linear.a = 1;
            var c = linear.gamma; c.r = Mathf.Min(c.r, 1); c.g = Mathf.Min(c.g, 1); c.b = Mathf.Min(c.b, 1);
            return c;
        }

        /// The golf numbers from before this pass (GolfGame.Awake as it was): sun 1.1, flat grey ambient,
        /// fog 250-700, the scene's own skybox, no fill, no rim, no post.
        static void Legacy(Light sun, Camera camera)
        {
            if (sun)
            {
                sun.type = LightType.Directional;
                sun.transform.rotation = Quaternion.Euler(50, -30, 0);
                sun.color = Color.white; sun.intensity = 1.1f;
                sun.shadows = LightShadows.Soft; sun.shadowStrength = 1f;
            }
            if (fill) fill.enabled = false;
            if (rim) rim.enabled = false;
            RenderSettings.sun = sceneSun;
            RenderSettings.skybox = sceneSkybox;
            RenderSettings.ambientMode = sceneAmbientMode;
            RenderSettings.ambientLight = new Color(0.55f, 0.6f, 0.65f);
            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(0.75f, 0.85f, 0.95f);
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogStartDistance = 250; RenderSettings.fogEndDistance = 700;
            if (camera) SetupCamera(camera, false);
        }

        /// The hole's tee->pin heading in degrees (world X right, Z down the hole: atan2(x, z)).
        static float Heading(int holeNumber, Look look)
        {
            var view = HoleView.Current;
            if (view && view.Hole != null && view.Hole.Number == holeNumber)
            {
                var tee = view.Hole.Tee; var pin = view.Hole.Pin;
                return Mathf.Atan2((float)(pin.X - tee.X), (float)(pin.D - tee.D)) * Mathf.Rad2Deg;
            }
            return look.FallbackHeading;
        }

        /// A unit vector pointing TOWARD a light at this world azimuth/elevation.
        public static Vector3 Direction(float azimuth, float elevation)
        {
            float a = azimuth * Mathf.Deg2Rad, e = elevation * Mathf.Deg2Rad;
            return new Vector3(Mathf.Sin(a) * Mathf.Cos(e), Mathf.Sin(e), Mathf.Cos(a) * Mathf.Cos(e));
        }

        static Light Directional(Light light, string name, Color color, float intensity, Vector3 toward)
        {
            if (!light)
            {
                var go = GameObject.Find(name);
                if (!go) go = new GameObject(name);
                light = go.GetComponent<Light>(); if (!light) light = go.AddComponent<Light>();
            }
            light.type = LightType.Directional;
            light.shadows = LightShadows.None;
            light.color = color; light.intensity = intensity;
            light.transform.rotation = Quaternion.LookRotation(-toward);
            light.enabled = intensity > 0;
            return light;
        }

        static Material Sky(int holeNumber, Look look, float heading)
        {
            var shader = Resources.Load<Shader>("Tennis/Shaders/TennisSky");
            if (!shader || !shader.isSupported) { Debug.LogWarning("[GolfAtmosphere] GolfArcade/TennisSky missing: keeping the scene skybox"); return null; }
            if (!skies.TryGetValue(holeNumber, out var sky) || !sky)
            {
                sky = new Material(shader) { name = "Golf painted sky (" + look.Name + ")" };
                var panorama = Resources.Load<Texture2D>(look.SkyTexture);
                if (!panorama)
                {
                    Debug.LogWarning($"[GolfAtmosphere] missing Resources/{look.SkyTexture}: " + (holeNumber == 10 ? "using a generated dusk gradient" : "using the tennis panorama"));
                    panorama = holeNumber == 10 ? CraterFallback() : Resources.Load<Texture2D>("Tennis/Environment/SkyPanorama");
                }
                if (panorama && look.CoolSky) panorama = CoolPanorama(panorama);
                if (panorama) sky.SetTexture("_Panorama", panorama);
                skies[holeNumber] = sky;
            }
            sky.SetColor("_Horizon", look.SkyHorizon);
            sky.SetColor("_Zenith", look.SkyZenith);
            sky.SetColor("_Sea", look.SkySea);
            sky.SetColor("_SunColor", look.SkySunColor);
            sky.SetVector("_SunDir", Direction(heading + look.SunAzimuth, look.SunElevation));
            sky.SetFloat("_Arc", 180);
            sky.SetFloat("_Heading", heading + look.SkyHeadingOffset);
            sky.SetFloat("_Exposure", look.SkyExposure);
            return sky;
        }

        static Texture2D coolSky;

        /// Split's sky: the tennis panorama with its warm haze and peach cloud undersides turned blue-white (blue sky
        /// pixels untouched), made once on the GPU->CPU and cached (~2 MP, done at the first Split load).
        /// A hand-painted Resources/Course/Look/Sky_Split_C replaces it when present.
        static Texture2D CoolPanorama(Texture2D source)
        {
            if (coolSky) return coolSky;
            var painted = Resources.Load<Texture2D>("Course/Look/Sky_Split_C");
            if (painted) return coolSky = painted;
            int w = source.width, h = source.height;
            var rt = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            Graphics.Blit(source, rt);
            var previous = RenderTexture.active;
            RenderTexture.active = rt;
            var t = new Texture2D(w, h, TextureFormat.RGBA32, true, false) { name = "Golf sky (Split, cooled)", wrapMode = TextureWrapMode.Clamp, anisoLevel = 1 };
            t.ReadPixels(new Rect(0, 0, w, h), 0, 0, false);
            RenderTexture.active = previous;
            RenderTexture.ReleaseTemporary(rt);
            var px = t.GetPixels32();
            for (int y = 0; y < h; y++)
            {
                float haze = 1 - Mathf.SmoothStep(0, 1, y / (h * .28f));            // texture row 0 = the horizon
                Color target = Color.Lerp(new Color(.96f, .98f, 1f), new Color(.84f, .92f, 1f), haze);
                for (int x = 0; x < w; x++)
                {
                    int i = y * w + x; var p = px[i];
                    float r = p.r / 255f, g = p.g / 255f, b = p.b / 255f;
                    float warm = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(-.15f, .25f, r - b));   // 0 on blue sky, 1 on peach/gold
                    if (warm <= 0) continue;
                    float value = Mathf.Max(r, Mathf.Max(g, b));
                    float k = warm * .85f;
                    px[i] = new Color32((byte)(255 * Mathf.Lerp(r, value * target.r, k)), (byte)(255 * Mathf.Lerp(g, value * target.g, k)),
                                        (byte)(255 * Mathf.Lerp(b, value * target.b, k)), 255);
                }
            }
            t.SetPixels32(px);
            t.Apply(true, true);
            return coolSky = t;
        }

        /// Only if Sky_Crater_C.png has not arrived: a smoky ember-to-aubergine gradient (v = 0 horizon .. 1 top).
        static Texture2D CraterFallback()
        {
            if (craterFallback) return craterFallback;
            const int w = 4, h = 128;
            craterFallback = new Texture2D(w, h, TextureFormat.RGBA32, false) { name = "Crater sky (fallback)", wrapMode = TextureWrapMode.Clamp };
            var px = new Color[w * h];
            for (int y = 0; y < h; y++)
            {
                float t = y / (h - 1f);
                var c = Color.Lerp(new Color(.86f, .40f, .17f), new Color(.36f, .17f, .16f), Mathf.SmoothStep(0, 1, Mathf.Clamp01(t * 2.2f)));
                c = Color.Lerp(c, new Color(.13f, .09f, .13f), Mathf.SmoothStep(0, 1, Mathf.Clamp01((t - .35f) / .65f)));
                for (int x = 0; x < w; x++) px[y * w + x] = c;
            }
            craterFallback.SetPixels(px); craterFallback.Apply(false, true);
            return craterFallback;
        }

        /// Golf camera settings. Post-processing is OFF on purpose (class comment): no Volume is created, and `renderPostProcessing`
        /// is forced false, so a renderer that later gets PostProcessData cannot add bloom / ACES / a vignette to a look that was
        /// measured and tuned without them. `postcard` also fixes MSAA to the pipeline asset's (no per-camera AA) and keeps shadows on.
        static void SetupCamera(Camera camera, bool postcard)
        {
            var data = camera.GetUniversalAdditionalCameraData();
            data.renderPostProcessing = false;
            if (!postcard) return;
            data.antialiasing = AntialiasingMode.None;   // MSAA comes from the pipeline asset
            data.renderShadows = true;
        }
    }
}
