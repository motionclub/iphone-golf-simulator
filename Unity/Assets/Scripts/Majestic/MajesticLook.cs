using GolfArcade.Tennis;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace GolfArcade.Majestic
{
    /// One venue's signature light and grade (the concept targets in
    /// work/majestic-maps-research/concepts). Directions are world space; the tennis gameplay camera looks
    /// down +Z, so a sun "upper left of the picture" has negative X.
    public sealed class MajesticLook
    {
        public bool Active = true;          // false = this place keeps its own look (no grade, light or dressing)
        public Vector3 ToSun;               // relative to the place's forward (tennis +Z, golf tee->pin, hub arrival view)
        public Color SunColor; public float SunIntensity, ShadowStrength;
        public Color AmbientSky, AmbientEquator, AmbientGround;
        public Color FogColor; public float FogStart, FogEnd;
        public float SkySunset = -1, SkyDay = -1, Night = -1, SkyExposure = -1;   // -1 = leave DreamEnvironment's value
        public Vector2 WindXZ; public float Gust;
        // grade
        public float Exposure, Contrast, Saturation, Temperature, Tint;
        public Color Filter = Color.white;
        public Vector4 Shadows = new(1, 1, 1, 0), Midtones = new(1, 1, 1, 0), Highlights = new(1, 1, 1, 0);
        public float BloomThreshold = 1, BloomIntensity, BloomScatter = .7f; public Color BloomTint = Color.white;
        public float Vignette;
        // dressing palette
        public Color Court, CourtLine, Lawn, LawnStripe;
        public Color SeaShallow, SeaDeep, SeaSky; public float SeaSparkle, SeaSheen;

        public static Vector3 Dir(float azimuthFromPlusZ, float elevation)
        {
            float a = azimuthFromPlusZ * Mathf.Deg2Rad, e = elevation * Mathf.Deg2Rad;
            return new Vector3(Mathf.Sin(a) * Mathf.Cos(e), Mathf.Sin(e), Mathf.Cos(a) * Mathf.Cos(e)).normalized;
        }

        public Vector4 Wind(float t)
        {
            // one breeze for palms, bunting, flags and grass: slow gust envelope over a steady push
            float g = 1 + Gust * (.55f * Mathf.Sin(t * .37f) + .45f * Mathf.Sin(t * 1.13f + 1.7f));
            return new Vector4(WindXZ.x * g, 0, WindXZ.y * g, t);
        }

        public static MajesticLook For(TennisVenueKind venue) => venue switch
        {
            TennisVenueKind.Volcano => Volcano(),
            TennisVenueKind.Skyscraper => Skyscraper(),
            _ => Resort(),
        };

        /// Volcano: dusk storm, key light is the eruption straight down the court (low, orange), purple sky
        /// light, lava bounce from below; glossy dark court.
        public static MajesticLook Volcano() => new()
        {
            ToSun = Dir(4, 9),
            SunColor = new Color(1f, .46f, .20f), SunIntensity = 1.9f, ShadowStrength = .65f,
            AmbientSky = new Color(.34f, .33f, .52f), AmbientEquator = new Color(.46f, .34f, .36f), AmbientGround = new Color(.50f, .22f, .10f),
            FogColor = new Color(.26f, .19f, .26f), FogStart = 200, FogEnd = 1600,
            SkySunset = .85f, SkyDay = .32f, Night = .55f,
            WindXZ = new Vector2(.03f, .02f), Gust = .6f,
            Exposure = .18f, Contrast = 22, Saturation = 34, Temperature = 2, Tint = 4,
            Filter = new Color(1f, .97f, .97f),
            Shadows = new Vector4(.97f, .97f, 1.10f, .01f), Midtones = new Vector4(1.02f, 1f, 1f, 0), Highlights = new Vector4(1.08f, .98f, .88f, 0),
            BloomThreshold = .82f, BloomIntensity = 1.05f, BloomScatter = .72f, BloomTint = new Color(1f, .62f, .40f),
            Vignette = .26f,
            Court = new Color(.40f, .45f, .56f), CourtLine = new Color(.95f, .95f, .95f),
            Lawn = new Color(.22f, .23f, .29f), LawnStripe = new Color(.27f, .25f, .31f),
        };

        /// Skyscraper: blue hour as the city lights come on; cool sky key from behind, warm practicals
        /// (string lights, lamps, windows) carry the scene through bloom.
        public static MajesticLook Skyscraper() => new()
        {
            ToSun = Dir(-150, 12),
            SunColor = new Color(.62f, .68f, 1f), SunIntensity = .62f, ShadowStrength = .45f,
            AmbientSky = new Color(.24f, .29f, .54f), AmbientEquator = new Color(.46f, .34f, .40f), AmbientGround = new Color(.14f, .14f, .22f),
            FogColor = new Color(.20f, .22f, .40f), FogStart = 260, FogEnd = 2600,
            SkySunset = .8f, SkyDay = .2f, Night = .85f, SkyExposure = .5f,
            WindXZ = new Vector2(.06f, .04f), Gust = .5f,
            Exposure = .08f, Contrast = 18, Saturation = 20, Temperature = -6, Tint = 4,
            Filter = new Color(.97f, .98f, 1f),
            Shadows = new Vector4(.95f, .98f, 1.16f, .02f), Midtones = new Vector4(1f, 1f, 1.03f, 0), Highlights = new Vector4(1.08f, 1f, .90f, 0),
            BloomThreshold = .78f, BloomIntensity = 1.1f, BloomScatter = .72f, BloomTint = new Color(1f, .82f, .62f),
            Vignette = .2f,
            Court = new Color(.22f, .50f, .88f), CourtLine = new Color(.97f, .97f, .97f),
            Lawn = new Color(.13f, .19f, .38f), LawnStripe = new Color(.13f, .19f, .38f),
        };

        /// Resort: late-afternoon gold from the side-front, long palm shadows across the court, islands and
        /// stands lit (not silhouetted), lifted cool shadows.
        public static MajesticLook Resort() => new()
        {
            ToSun = Dir(-62, 21),
            SunColor = new Color(1f, .79f, .53f), SunIntensity = 2.4f, ShadowStrength = .72f,
            AmbientSky = new Color(.60f, .72f, .94f), AmbientEquator = new Color(.80f, .72f, .60f), AmbientGround = new Color(.40f, .36f, .30f),
            FogColor = new Color(.80f, .86f, .94f), FogStart = 220, FogEnd = 2600,
            SkySunset = .12f, SkyDay = 1,
            WindXZ = new Vector2(.045f, .03f), Gust = .45f,
            Exposure = .30f, Contrast = 18, Saturation = 40, Temperature = 12, Tint = 2,
            Filter = new Color(1f, .985f, .96f),
            Shadows = new Vector4(.97f, 1f, 1.08f, .02f), Midtones = new Vector4(1.02f, 1f, .98f, 0), Highlights = new Vector4(1.03f, 1f, .95f, 0),
            BloomThreshold = .95f, BloomIntensity = .5f, BloomScatter = .7f, BloomTint = new Color(1f, .88f, .72f),
            Vignette = .14f,
            Court = new Color(.17f, .40f, .86f), CourtLine = new Color(.97f, .97f, .95f),
            Lawn = new Color(.22f, .48f, .19f), LawnStripe = new Color(.27f, .55f, .22f),
            SeaShallow = new Color(.10f, .80f, .84f), SeaDeep = new Color(.05f, .38f, .78f), SeaSky = new Color(.80f, .88f, .98f),
            SeaSparkle = 3.2f, SeaSheen = 1.1f,
        };

        /// Golf, Cliffside course (7, 8, 9, 12, 15): fresh morning sea light from the right-front, bright
        /// turquoise water, crisp shadows. Other courses keep their own look until they get targets.
        public static MajesticLook Golf(int hole) => MajesticCourses.For(hole);   // chat 10: one signature hour per course

        /// Plaza hub: golden hour, sun low beyond the clock tower (front-left of the arrival view), warm stone.
        public static MajesticLook Hub() => new()
        {
            ToSun = Dir(-28, 15),
            SunColor = new Color(1f, .78f, .52f), SunIntensity = 2.2f, ShadowStrength = .72f,
            AmbientSky = new Color(.58f, .66f, .88f), AmbientEquator = new Color(.82f, .70f, .56f), AmbientGround = new Color(.42f, .36f, .28f),
            FogColor = new Color(.88f, .80f, .78f), FogStart = 220, FogEnd = 1600,
            WindXZ = new Vector2(.04f, .03f), Gust = .45f,
            Exposure = .06f, Contrast = 22, Saturation = 26, Temperature = 6, Tint = 3,
            Filter = new Color(1f, .985f, .96f),
            Shadows = new Vector4(.97f, .99f, 1.08f, .02f), Midtones = new Vector4(1.03f, 1f, .97f, 0), Highlights = new Vector4(1.05f, 1f, .92f, 0),
            BloomThreshold = .9f, BloomIntensity = .65f, BloomScatter = .72f, BloomTint = new Color(1f, .82f, .6f),
            Vignette = .16f,
        };

        public VolumeProfile Grade()
        {
            var p = ScriptableObject.CreateInstance<VolumeProfile>();
            p.name = "Majestic grade";
            var tm = p.Add<Tonemapping>(true); tm.mode.Override(TonemappingMode.Neutral);
            var ca = p.Add<ColorAdjustments>(true);
            ca.postExposure.Override(Exposure); ca.contrast.Override(Contrast); ca.saturation.Override(Saturation); ca.colorFilter.Override(Filter);
            var wb = p.Add<WhiteBalance>(true); wb.temperature.Override(Temperature); wb.tint.Override(Tint);
            var smh = p.Add<ShadowsMidtonesHighlights>(true);
            smh.shadows.Override(Shadows); smh.midtones.Override(Midtones); smh.highlights.Override(Highlights);
            var bloom = p.Add<Bloom>(true);
            bloom.threshold.Override(BloomThreshold); bloom.intensity.Override(BloomIntensity); bloom.scatter.Override(BloomScatter);
            bloom.tint.Override(BloomTint); bloom.highQualityFiltering.Override(false);
            bloom.downscale.Override(BloomDownscaleMode.Quarter); bloom.maxIterations.Override(5);
            var vig = p.Add<Vignette>(true); vig.intensity.Override(Vignette); vig.smoothness.Override(.45f); vig.color.Override(new Color(.16f, .10f, .08f));
            return p;
        }
    }
}
