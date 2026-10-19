using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.EnvironmentArt
{
    /// The sky we render ourselves (work/rendered-backgrounds). Replaces every painted panorama:
    /// a single-scattering atmosphere (Rayleigh + Mie + ozone, Nishita-style) is integrated on the CPU
    /// into a 48x48 sky-view LUT whenever the scene's real directional light changes elevation, and
    /// published as globals with the light's direction/colour, so the skybox, the cloud impostors, the
    /// distant scenery's aerial perspective and the sky reflections all agree with the light.
    /// DreamEnvironment keeps driving _Day/_Sunset/_Cloud on the material; this reads them back.
    [DefaultExecutionOrder(10001)]
    public sealed class RenderedSky : MonoBehaviour
    {
        /// Per-venue look. Physical values plus a light grade (saturation, highlight knee).
        public sealed class Profile
        {
            public float Exposure = 14f;            // radiance -> scene units
            public float Turbidity = .5f;           // Mie density scale (haze)
            public float MieG = .8f;
            public float MultiScatter = .2f;        // isotropic share of Rayleigh light added back (cheap multiple scattering)
            public float Saturation = 1.45f, Knee = .75f;
            public float AerialDistance = 7000f;    // m, e-folding distance of the haze at sea level
            public float HazeScaleHeight = 1200f;   // m, the haze thins with height
            public Color HorizonTint = new Color(.93f, .99f, 1.06f);
            public float HorizonSaturation = 1.05f;
            public float HazeLift = .0f;
            public float SeaLevel = -1.2f;          // world y of the open sea under the horizon
            public bool SeaBelow = true;
            public Color SeaDeep = new Color(.010f, .17f, .30f);
            public float SeaReflectance = .85f;
            public float Cirrus = .42f, CirrusScale = 1f;
            public float DiscRadiusDeg = .55f, DiscBrightness = 14f;
            public Color NightTint = new Color(.010f, .022f, .060f);
            public Color UpperTint = Color.white;
            public float FarFieldStart = .55f;      // fraction of the far clip where depth compression starts
            public bool DriveFogColour = true;      // fog colour = the rendered horizon, so near haze matches far haze
            public float FogEnd = -1;               // >0 overrides the linear fog end (clear weather only)
            public float AshOvercast = 0;
            public float SunsetOverride = -1;       // >=0: a fixed time-of-day mood where no clock drives the material (the hub's golden hour)           // a venue's own permanent haze (volcanic ash), added to the weather's
        }

        public static RenderedSky Current { get; private set; }
        public static bool Enabled => System.Environment.GetEnvironmentVariable("RENDERED_SKY") != "0";
        public Profile Look { get; private set; } = new Profile();
        public Material Sky { get; private set; }
        public RenderTexture Reflection { get; private set; }

        Texture2D rayleigh, mie; static Texture2D noise;
        float lutElevation = 999, lutKey = -1; float reflectionStamp = -1; Vector3 reflectionSun;
        Color[] rBuf, mBuf; Vector3 ambientUp, ambientHorizon;
        const int N = 48;

        static readonly int RayleighId = Shader.PropertyToID("_RSkyRayleigh"), MieId = Shader.PropertyToID("_RSkyMie"),
            NoiseId = Shader.PropertyToID("_RSkyNoise"), SunDirId = Shader.PropertyToID("_RSkySunDir"),
            SunColorId = Shader.PropertyToID("_RSkySunColor"), ScatterId = Shader.PropertyToID("_RSkyScatterDir"),
            ParamsId = Shader.PropertyToID("_RSkyParams"), AerialId = Shader.PropertyToID("_RSkyAerial"),
            GradeId = Shader.PropertyToID("_RSkyGrade"), HorizonTintId = Shader.PropertyToID("_RSkyHorizonTint"),
            AmbUpId = Shader.PropertyToID("_RSkyAmbientUp"), AmbHorId = Shader.PropertyToID("_RSkyAmbientHorizon"),
            SeaId = Shader.PropertyToID("_RSkySea"), NightId = Shader.PropertyToID("_RSkyNightTint");

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetStatics() { Current = null; }

        /// Creates (or re-profiles) the one rendered sky under `parent` and returns its skybox material.
        public static Material Install(Transform parent, Profile look)
        {
            if (!Current)
            {
                var go = new GameObject("Rendered sky");
                if (parent) go.transform.SetParent(parent, false);
                Current = go.AddComponent<RenderedSky>();
            }
            Current.Look = look ?? new Profile();
            Current.lutElevation = 999; Current.rewireIn = 3;   // new venue/hole materials appear over the next frames
            Current.Apply();
            return Current.Sky;
        }

        void Awake()
        {
            var shader = Resources.Load<Shader>("Environment/RenderedSky/RenderedSky");
            Sky = new Material(shader) { name = "Rendered sky" };
            rayleigh = NewLut("Rendered sky Rayleigh"); mie = NewLut("Rendered sky Mie");
            rBuf = new Color[N * N]; mBuf = new Color[N * N];
            if (!noise) noise = MakeNoise(256);
        }

        static Texture2D NewLut(string name) => new Texture2D(N, N, TextureFormat.RGBAHalf, false, true)
        { name = name, wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };

        void OnDestroy()
        {
            if (Current == this) Current = null;
            if (Sky) Destroy(Sky); if (rayleigh) Destroy(rayleigh); if (mie) Destroy(mie);
            if (Reflection) { Reflection.Release(); Destroy(Reflection); }
        }

        void LateUpdate() => Apply();

        /// Elevation the scattering is computed for: the light's own during the day, sliding toward a
        /// low sun as DreamEnvironment's sunset factor rises (its light stays high at "sunset"; the glow
        /// still sits at the light's azimuth), and below the horizon at night (the light is then the moon).
        static float ScatterElevation(float lightElevation, float day, float sunset)
        {
            float e = Mathf.Lerp(lightElevation, 3.5f, sunset);
            return Mathf.Lerp(-7.5f, e, Mathf.SmoothStep(0, 1, Mathf.Clamp01(day * 1.6f)));
        }

        int rewireIn = 3;

        public void Apply()
        {
            if (!Sky) return;
            if (rewireIn > 0 && --rewireIn == 0 && Reflection) RewirePaintedReflections();
            var sun = RenderSettings.sun;
            Vector3 toLight = sun ? -sun.transform.forward : new Vector3(.5f, .6f, .3f).normalized;
            float day = Sky.GetFloat("_Day"), sunset = Sky.GetFloat("_Sunset"), cloud = Sky.GetFloat("_Cloud");
            if (Look.SunsetOverride >= 0) { sunset = Look.SunsetOverride; day = 1; Sky.SetFloat("_Sunset", sunset); }
            float night = 1 - Mathf.Clamp01(day);
            float lightEl = Mathf.Asin(Mathf.Clamp(toLight.y, -1, 1)) * Mathf.Rad2Deg;
            float scatterEl = ScatterElevation(lightEl, day, sunset);
            float key = Look.Turbidity * 1000 + Look.MultiScatter;
            if (Mathf.Abs(scatterEl - lutElevation) > .2f || !Mathf.Approximately(lutKey, key))
            {
                BuildLut(scatterEl); lutElevation = scatterEl; lutKey = key;
            }
            var horiz = new Vector3(toLight.x, 0, toLight.z); if (horiz.sqrMagnitude < 1e-6) horiz = Vector3.forward; horiz.Normalize();
            float se = scatterEl * Mathf.Deg2Rad;
            var scatterDir = horiz * Mathf.Cos(se) + Vector3.up * Mathf.Sin(se);
            Color light = sun ? sun.color * sun.intensity : Color.white;
            // overcast weather (DreamEnvironment _Cloud .08 clear .. .65 storm) -> 0..1
            float overcast = Mathf.Clamp01((cloud - .1f) / .55f + Look.AshOvercast);
            float discR = Look.DiscRadiusDeg * Mathf.Deg2Rad * (night > .5f ? 1.15f : 1);
            float discB = Mathf.Lerp(Look.DiscBrightness, 2.2f, night);
            Shader.SetGlobalTexture(RayleighId, rayleigh); Shader.SetGlobalTexture(MieId, mie); Shader.SetGlobalTexture(NoiseId, noise);
            Shader.SetGlobalVector(SunDirId, new Vector4(toLight.x, toLight.y, toLight.z, discR));
            Shader.SetGlobalVector(SunColorId, new Vector4(light.r, light.g, light.b, discB));
            Shader.SetGlobalVector(ScatterId, new Vector4(scatterDir.x, scatterDir.y, scatterDir.z, Look.MieG));
            Shader.SetGlobalVector(ParamsId, new Vector4(Look.Exposure, night, overcast, Time.timeSinceLevelLoad));
            Shader.SetGlobalVector(AerialId, new Vector4(Look.AerialDistance, Look.SeaLevel, Look.HazeLift, Look.FarFieldStart));
            Shader.SetGlobalVector(GradeId, new Vector4(Look.Saturation, Look.Knee, Look.MultiScatter, Look.HazeScaleHeight));
            Shader.SetGlobalVector(HorizonTintId, new Vector4(Look.HorizonTint.r, Look.HorizonTint.g, Look.HorizonTint.b, Look.HorizonSaturation));
            var nightAmb = (Vector3)(Vector4)Look.NightTint * 2.2f;
            var up = Vector3.Lerp(Graded(ambientUp * Look.Exposure), nightAmb, night);
            var hor = Vector3.Lerp(Graded(ambientHorizon * Look.Exposure, .02f), nightAmb * 1.3f, night);
            Shader.SetGlobalVector(AmbUpId, up); Shader.SetGlobalVector(AmbHorId, hor);
            Shader.SetGlobalVector(SeaId, new Vector4(Look.SeaDeep.r, Look.SeaDeep.g, Look.SeaDeep.b, Look.SeaReflectance));
            Shader.SetGlobalVector(NightId, Look.NightTint);
            Sky.SetFloat("_SeaBelow", Look.SeaBelow ? 1 : 0);
            Sky.SetFloat("_Cirrus", Look.Cirrus); Sky.SetFloat("_CirrusScale", Look.CirrusScale);
            Sky.SetColor("_UpperTint", Look.UpperTint);
            HorizonColour = new Color(hor.x, hor.y, hor.z);
            if (Look.DriveFogColour && RenderSettings.fog)
            {
                // near-scene linear fog takes the rendered horizon (weather-greyed like the sky)
                float lum = hor.x * .3f + hor.y * .55f + hor.z * .15f;
                RenderSettings.fogColor = Color.Lerp(HorizonColour, new Color(.62f, .66f, .72f) * lum * 1.15f, overcast * .85f);
                if (Look.FogEnd > 0 && cloud < .2f) RenderSettings.fogEndDistance = Look.FogEnd;
            }
            UpdateReflection(toLight, day, sunset, cloud);
        }

        /// The rendered horizon colour (azimuth average) this frame.
        public Color HorizonColour { get; private set; }

        /// Same grade as RS_Grade in the shader, for CPU-side colours.
        Vector3 Graded(Vector3 c, float up = 1)
        {
            float k0 = Mathf.SmoothStep(0, 1, Mathf.Clamp01(up / .32f));
            var tint = Vector3.Lerp((Vector3)(Vector4)Look.HorizonTint, Vector3.one, k0);
            c = Vector3.Scale(c, tint);
            float sat = Mathf.Lerp(Look.HorizonSaturation, Look.Saturation, k0);
            float l = c.x * .2126f + c.y * .7152f + c.z * .0722f;
            c = new Vector3(Mathf.Max(0, l + (c.x - l) * sat), Mathf.Max(0, l + (c.y - l) * sat), Mathf.Max(0, l + (c.z - l) * sat));
            float k = Look.Knee;
            float Knee(float v) => v < k ? v : k + (1 - k) * (1 - Mathf.Exp(-(v - k) / (1 - k)));
            return new Vector3(Knee(c.x), Knee(c.y), Knee(c.z));
        }

        // ------------------------------------------------------------------ atmosphere
        const float Re = 6360e3f, Ra = 6420e3f, Hr = 8000f, Hm = 1200f;
        static readonly Vector3 BetaR = new Vector3(5.802e-6f, 13.558e-6f, 33.1e-6f);
        static readonly Vector3 BetaO = new Vector3(.650e-6f, 1.881e-6f, .085e-6f);
        const float BetaMs = 3.996e-6f, BetaMe = 4.40e-6f;

        static float RaySphere(Vector3 o, Vector3 d, float r)
        {
            float b = Vector3.Dot(o, d), c = Vector3.Dot(o, o) - r * r, h = b * b - c;
            if (h < 0) return -1; h = Mathf.Sqrt(h);
            float t1 = -b - h, t2 = -b + h;
            return t1 > 0 ? t1 : t2 > 0 ? t2 : -1;
        }
        static Vector3 Exp(Vector3 v) => new Vector3(Mathf.Exp(v.x), Mathf.Exp(v.y), Mathf.Exp(v.z));
        static float Ozone(float h) => Mathf.Max(0, 1 - Mathf.Abs(h - 25000f) / 15000f);

        void BuildLut(float sunElevationDeg)
        {
            float t = Look.Turbidity;
            float se = sunElevationDeg * Mathf.Deg2Rad;
            var sunDir = new Vector3(Mathf.Cos(se), Mathf.Sin(se), 0);
            var origin = new Vector3(0, Re + 2, 0);
            const int VS = 20, LS = 8;
            Vector3 accUp = Vector3.zero, accHor = Vector3.zero; float wUp = 0, wHor = 0;
            for (int y = 0; y < N; y++)
            {
                float v = (y + .5f) / N, s = v < .5f ? -1 : 1, a = Mathf.Abs(v * 2 - 1);
                float elev = s * a * a * Mathf.PI * .5f;
                for (int x = 0; x < N; x++)
                {
                    float az = (x + .5f) / N * Mathf.PI;
                    var dir = new Vector3(Mathf.Cos(elev) * Mathf.Cos(az), Mathf.Sin(elev), Mathf.Cos(elev) * Mathf.Sin(az));
                    float tMax = RaySphere(origin, dir, Ra);
                    float tGround = RaySphere(origin, dir, Re);
                    if (tGround > 0) tMax = Mathf.Min(tMax, tGround);
                    Vector3 sumR = Vector3.zero, sumM = Vector3.zero, od = Vector3.zero;
                    for (int i = 0; i < VS; i++)
                    {
                        // quadratic spacing: dense near the camera
                        float u0 = (float)i / VS, u1 = (float)(i + 1) / VS;
                        float t0 = u0 * u0 * tMax, t1 = u1 * u1 * tMax, ds = t1 - t0, tm = (t0 + t1) * .5f;
                        var p = origin + dir * tm; float h = p.magnitude - Re;
                        float dr = Mathf.Exp(-h / Hr) * ds, dm = Mathf.Exp(-h / Hm) * ds, dO = Ozone(h) * ds;
                        od += BetaR * dr + Vector3.one * (BetaMe * t * dm) + BetaO * dO;
                        if (RaySphere(p, sunDir, Re) > 0) continue;   // in the planet's shadow
                        float tl = RaySphere(p, sunDir, Ra);
                        Vector3 odl = Vector3.zero; float dsl = tl / LS;
                        for (int j = 0; j < LS; j++)
                        {
                            var q = p + sunDir * ((j + .5f) * dsl); float hl = q.magnitude - Re;
                            odl += BetaR * (Mathf.Exp(-hl / Hr) * dsl) + Vector3.one * (BetaMe * t * Mathf.Exp(-hl / Hm) * dsl) + BetaO * (Ozone(hl) * dsl);
                        }
                        var tr = Exp(-(od + odl));
                        sumR += Vector3.Scale(tr, BetaR) * dr; sumM += tr * (BetaMs * t * dm);
                    }
                    float mu = Vector3.Dot(dir, sunDir);
                    float phaseR = 3f / (16f * Mathf.PI) * (1 + mu * mu);
                    var R = sumR * phaseR + sumR * (Look.MultiScatter / (4 * Mathf.PI));
                    rBuf[y * N + x] = new Color(R.x, R.y, R.z, 1);
                    mBuf[y * N + x] = new Color(sumM.x, sumM.y, sumM.z, 1);
                    if (elev > 0)
                    {
                        float w = Mathf.Sin(elev) * Mathf.Cos(elev), phaseM = 1f / (4 * Mathf.PI);
                        accUp += (R + sumM * phaseM) * w; wUp += w;
                        if (elev < .06f) { accHor += R + sumM * phaseM; wHor += 1; }
                    }
                }
            }
            rayleigh.SetPixels(rBuf); rayleigh.Apply(false); mie.SetPixels(mBuf); mie.Apply(false);
            ambientUp = wUp > 0 ? accUp / wUp : Vector3.zero; ambientHorizon = wHor > 0 ? accHor / wHor : Vector3.zero;
            reflectionStamp = -1;
            if (System.Environment.GetEnvironmentVariable("RENDERED_SKY_LOG") == "1")
                Debug.Log($"[RenderedSky] LUT sunEl={sunElevationDeg:F1} zenith={Graded((Vector3)(Vector4)rBuf[(N - 1) * N] * Look.Exposure)} horizon={Graded(ambientHorizon * Look.Exposure, .02f)} ambUp={Graded(ambientUp * Look.Exposure)}");
        }

        // ------------------------------------------------------------------ reflections
        static readonly string[] Painted = { "ArchipelagoSky", "SummerSky", "SkyCoastalSmall", "SkyVolcanic", "SkyRooftop", "CloudTops", "clouds", "ash_cloud" };
        static readonly string[] ReflectionSlots = { "_SkyMap", "_ReflectionMap", "_SkyPanorama" };
        readonly HashSet<Material> rewired = new();

        void UpdateReflection(Vector3 toLight, float day, float sunset, float cloud)
        {
            if (!Reflection)
            {
                Reflection = new RenderTexture(256, 128, 0, RenderTextureFormat.ARGBHalf) { name = "Rendered sky reflection", useMipMap = true, autoGenerateMips = true, wrapModeU = TextureWrapMode.Repeat, wrapModeV = TextureWrapMode.Clamp, filterMode = FilterMode.Trilinear };
                Reflection.Create();
            }
            float stamp = day * 100 + sunset * 10 + cloud;
            if (reflectionStamp >= 0 && Mathf.Abs(stamp - reflectionStamp) < .05f && Vector3.Angle(toLight, reflectionSun) < .5f) return;
            reflectionStamp = stamp; reflectionSun = toLight;
            Sky.SetFloat("_Equirect", 1);
            Graphics.Blit(null, Reflection, Sky, 0);
            Sky.SetFloat("_Equirect", 0);
            RewirePaintedReflections();
        }

        /// Every sky-reflecting material that still points at a painted panorama now reflects the
        /// rendered sky (same equirect convention, heading 0).
        public void RewirePaintedReflections()
        {
            foreach (var r in FindObjectsByType<Renderer>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                foreach (var m in r.sharedMaterials) Rewire(m);
        }

        public void Rewire(Material m)
        {
            if (!m || rewired.Contains(m)) return;
            bool any = false;
            foreach (var slot in ReflectionSlots)
            {
                if (!m.HasProperty(slot)) continue;
                var t = m.GetTexture(slot); if (!t || !IsPainted(t)) continue;
                m.SetTexture(slot, Reflection); any = true;
                if (m.HasProperty("_SkyHeading")) m.SetFloat("_SkyHeading", 0);
                if (m.HasProperty("_ReflectionHeading")) m.SetFloat("_ReflectionHeading", 0);
            }
            if (any) rewired.Add(m);
        }

        public static bool IsPainted(Texture t) { if (!t) return false; foreach (var n in Painted) if (t.name == n) return true; return false; }

        // ------------------------------------------------------------------ noise
        static Texture2D MakeNoise(int size)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, true, true) { name = "Rendered sky noise", wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Trilinear };
            var rng = new System.Random(1717);
            var px = new Color32[size * size];
            float[,] Octave(int cells)
            {
                var g = new float[cells, cells]; for (int i = 0; i < cells; i++) for (int j = 0; j < cells; j++) g[i, j] = (float)rng.NextDouble();
                var o = new float[size, size];
                for (int y = 0; y < size; y++)
                    for (int x = 0; x < size; x++)
                    {
                        float fx = (float)x / size * cells, fy = (float)y / size * cells;
                        int x0 = (int)fx, y0 = (int)fy; float tx = fx - x0, ty = fy - y0;
                        tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty);
                        float a = g[x0 % cells, y0 % cells], b = g[(x0 + 1) % cells, y0 % cells], c = g[x0 % cells, (y0 + 1) % cells], d = g[(x0 + 1) % cells, (y0 + 1) % cells];
                        o[x, y] = Mathf.Lerp(Mathf.Lerp(a, b, tx), Mathf.Lerp(c, d, tx), ty);
                    }
                return o;
            }
            var oct = new[] { Octave(4), Octave(8), Octave(16), Octave(32), Octave(64) };
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float f = 0, rdg = 0, amp = .5f, norm = 0;
                    for (int k = 0; k < oct.Length; k++) { f += oct[k][x, y] * amp; rdg += (1 - Mathf.Abs(oct[k][x, y] * 2 - 1)) * amp; norm += amp; amp *= .55f; }
                    px[y * size + x] = new Color32((byte)(Mathf.Clamp01(f / norm) * 255), (byte)(Mathf.Clamp01(rdg / norm) * 255), 0, 255);
                }
            tex.SetPixels32(px); tex.Apply(true);
            return tex;
        }
    }
}
