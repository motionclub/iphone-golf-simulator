using GolfArcade.Course;
using UnityEngine;

namespace GolfArcade.Majestic
{
    /// The signature hour, light and grade of each golf course (chat 10, work/majestic-all-maps; Adnan 10-17: one
    /// signature hour per course). Targets: work/majestic-all-maps/refs/holes. Directions are relative to the hole's
    /// tee->pin forward, like MajesticLook.Golf. MajesticLook.Golf(hole) returns For(hole).
    ///   Cliffside  (7, 8, 9, 12, 15)       fresh morning sea light from the right-front (chat 9's values, a touch brighter
    ///                                       and calmer in turf saturation: the targets are L 67 / chroma 42 vs today 61 / 48)
    ///   Wild Isles (13, 14, 17, 18, 19, 20) golden afternoon, low sun front-left, warm sky (target sky b* +20)
    ///   Magma Open (10, 16, 21, 22, 23)    pre-dawn: violet-magenta sky, low orange sun on the horizon, lava bounce,
    ///                                       lifted shadows (target p10 L 18 vs today 11)
    public static class MajesticCourses
    {
        public enum Kind { Cliffside, WildIsles, Magma, None }

        public static Kind CourseOf(int hole) => hole switch
        {
            7 or 8 or 9 or 12 or 15 => Kind.Cliffside,
            13 or 14 or 17 or 18 or 19 or 20 => Kind.WildIsles,
            10 or 16 or 21 or 22 or 23 => Kind.Magma,
            _ => Kind.None,
        };

        public static MajesticLook For(int hole) => CourseOf(hole) switch
        {
            Kind.Cliffside => Cliffside(),
            Kind.WildIsles => WildIsles(hole),
            Kind.Magma => Magma(hole),
            _ => new MajesticLook { Active = false },
        };

        public static MajesticLook Cliffside() => new()
        {
            ToSun = MajesticLook.Dir(48, 34),
            SunColor = new Color(1f, .94f, .82f), SunIntensity = 2.15f, ShadowStrength = .68f,
            AmbientSky = new Color(.60f, .72f, .94f), AmbientEquator = new Color(.74f, .74f, .68f), AmbientGround = new Color(.38f, .40f, .30f),
            FogColor = new Color(.76f, .86f, .97f), FogStart = 320, FogEnd = 7000,
            SkySunset = 0, SkyDay = 1,
            WindXZ = new Vector2(.04f, .025f), Gust = .5f,
            Exposure = .28f, Contrast = 14, Saturation = 18, Temperature = 3, Tint = 1,
            Filter = new Color(1f, .99f, .97f),
            Shadows = new Vector4(.97f, 1f, 1.08f, .02f), Midtones = new Vector4(1.01f, 1f, .99f, 0), Highlights = new Vector4(1.03f, 1f, .96f, 0),
            BloomThreshold = .95f, BloomIntensity = .45f, BloomScatter = .7f, BloomTint = new Color(1f, .92f, .8f),
            Vignette = .12f,
            SeaShallow = new Color(.08f, .78f, .84f), SeaDeep = new Color(.02f, .24f, .62f), SeaSky = new Color(.20f, .46f, .84f),
            SeaSparkle = 3f, SeaSheen = 1.1f,
        };

        public static MajesticLook WildIsles(int hole) => new()
        {
            // round 3: round 2 went mustard (warm grade + strong sunset sky turned the turf olive). The target is golden
            // light on still-green turf under a blue-to-gold sky: warm key, neutral grade, moderate sunset.
            ToSun = MajesticLook.Dir(-25, 8),   // round 12: RenderedSky colours the sky from the real sun: low and just inside the tee view's left edge, as the targets
            SunColor = new Color(1f, .83f, .58f), SunIntensity = 2.35f, ShadowStrength = .75f,   // round 9: golder key (targets sky b* +20)
            AmbientSky = new Color(.55f, .65f, .86f), AmbientEquator = new Color(.76f, .70f, .60f), AmbientGround = new Color(.38f, .34f, .26f),
            FogColor = new Color(.92f, .86f, .74f), FogStart = 0, FogEnd = 0,
            SkySunset = hole == 17 ? .25f : .5f, SkyDay = 1,
            WindXZ = new Vector2(.045f, .02f), Gust = .55f,
            Exposure = .22f, Contrast = 16, Saturation = 8, Temperature = 5, Tint = 1,
            Filter = new Color(1f, .99f, .97f),
            Shadows = new Vector4(.97f, .99f, 1.08f, .02f), Midtones = new Vector4(1.01f, 1f, .99f, 0), Highlights = new Vector4(1.04f, 1f, .94f, 0),
            BloomThreshold = .9f, BloomIntensity = .55f, BloomScatter = .72f, BloomTint = new Color(1f, .86f, .64f),
            Vignette = .14f,
            SeaShallow = new Color(.10f, .74f, .80f), SeaDeep = new Color(.03f, .24f, .56f), SeaSky = new Color(.28f, .52f, .80f),
            SeaSparkle = 3.2f, SeaSheen = 1.2f,
        };

        public static MajesticLook Magma(int hole) => new()
        {
            // round 2: the target keeps the turf vivid green; the mood comes from the sky, the lava glow and the walls, so the
            // key light stays near-neutral warm and the grade only leans magenta in the shadows
            ToSun = MajesticLook.Dir(32, 9),
            SunColor = new Color(1f, .90f, .80f), SunIntensity = 1.85f, ShadowStrength = .62f,
            AmbientSky = new Color(.52f, .52f, .68f), AmbientEquator = new Color(.58f, .52f, .52f), AmbientGround = new Color(.40f, .30f, .22f),
            FogColor = new Color(.30f, .16f, .24f), FogStart = 1500, FogEnd = 12000,   // FogEnd 0 (round 6) left the scene's short fog; round 12: keep the caldera ring (~550 yd) and the volcano clear
            SkySunset = .9f, SkyDay = .5f, Night = .08f,   // round 13: .3 read as a starry night; the targets are a bright dusk
            WindXZ = new Vector2(.03f, .025f), Gust = .6f,
            // round 9: the turf measured hue 65-70 with blue crushed (targets 88): cooler and greener white balance; the
            // sky keeps its colour from the sky material, not the grade
            Exposure = .22f, Contrast = 16, Saturation = 10, Temperature = -10, Tint = -4,
            Filter = new Color(.98f, 1f, .99f),
            Shadows = new Vector4(.99f, .96f, 1.10f, .02f), Midtones = new Vector4(1.01f, 1f, 1f, 0), Highlights = new Vector4(1.05f, .99f, .92f, 0),
            BloomThreshold = .8f, BloomIntensity = 1.0f, BloomScatter = .74f, BloomTint = new Color(1f, .6f, .38f),
            Vignette = .18f,
            SeaShallow = new Color(.16f, .20f, .36f), SeaDeep = new Color(.05f, .06f, .16f), SeaSky = new Color(.92f, .50f, .44f),
            SeaSparkle = 2.2f, SeaSheen = 1.4f,
        };
    }
}
