using System;
using GolfArcade.Course;
using UnityEngine;

namespace GolfArcade.Majestic
{
    /// What falls, if anything: the camera layer's look.
    public enum WeatherFall { None, Rain, Snow, Ash }

    /// The weather track's phase (chat W, 10-17). Arriving: it rolls in at a hole / a game's start.
    /// Full: as the game drew it. Clearing: rain has just stopped (sunbeams, rainbow, last drops, drying).
    /// Held: tennis, a point is being played: what falls and flashes waits until play stops (Adnan, 10-17).
    public enum WeatherPhase { Calm, Arriving, Full, Clearing, Held }

    /// One weather look: every number the layer drives. Pure data, lerpable, no Unity state.
    [Serializable]
    public struct WeatherLook
    {
        public float Cloud;                      // the sky's _Cloud (DreamEnvironment: .08 clear .. .65 storm), raised only
        public float Precip; public WeatherFall Fall;
        public float Wet, Puddles;
        public float LavaPools, IcePools;         // ash weathers: glowing lava puddles; snow weathers: frozen puddles
        public float Cover; public Color CoverColor; public float Frost, Embers;
        public float FogDensity, FogFalloff, FogMax;   // per metre (density, height falloff); max share
        public Color FogTint; public float FogTintShare; public Color FogGlow; public float FogGlowStrength;
        public float SunDim; public Color SunTint; public float AmbientDim; public Color AmbientTint;
        public float Wind, Gust, CloudShadows, GrassWaves, Whitecaps;
        public float Aerial;                     // multiplier on the rendered sky's aerial-perspective distance (1 = clear)
        public float SkyExposure;                // multiplier on the rendered sky's exposure: the sky darkens under cloud (1 = clear)
        public Color SkyTint;                    // multiplier on the rendered horizon tint (ash: warm)
        public float StormWall, Lightning, Eruption;
        public float Shafts;                     // sunbeams through broken cloud (storm), on top of the clearing's own

        public static WeatherLook Lerp(in WeatherLook a, in WeatherLook b, float t)
        {
            float L(float x, float y) => x + (y - x) * t;
            return new WeatherLook
            {
                Cloud = L(a.Cloud, b.Cloud), Precip = L(a.Precip, b.Precip), Fall = t < .5f ? a.Fall : b.Fall,
                Wet = L(a.Wet, b.Wet), Puddles = L(a.Puddles, b.Puddles), LavaPools = L(a.LavaPools, b.LavaPools), IcePools = L(a.IcePools, b.IcePools),
                Cover = L(a.Cover, b.Cover), CoverColor = Color.Lerp(a.CoverColor, b.CoverColor, t), Frost = L(a.Frost, b.Frost), Embers = L(a.Embers, b.Embers),
                FogDensity = L(a.FogDensity, b.FogDensity), FogFalloff = L(a.FogFalloff, b.FogFalloff), FogMax = L(a.FogMax, b.FogMax),
                FogTint = Color.Lerp(a.FogTint, b.FogTint, t), FogTintShare = L(a.FogTintShare, b.FogTintShare),
                FogGlow = Color.Lerp(a.FogGlow, b.FogGlow, t), FogGlowStrength = L(a.FogGlowStrength, b.FogGlowStrength),
                SunDim = L(a.SunDim, b.SunDim), SunTint = Color.Lerp(a.SunTint, b.SunTint, t), AmbientDim = L(a.AmbientDim, b.AmbientDim), AmbientTint = Color.Lerp(a.AmbientTint, b.AmbientTint, t),
                Wind = L(a.Wind, b.Wind), Gust = L(a.Gust, b.Gust), CloudShadows = L(a.CloudShadows, b.CloudShadows), GrassWaves = L(a.GrassWaves, b.GrassWaves), Whitecaps = L(a.Whitecaps, b.Whitecaps),
                Aerial = L(a.Aerial, b.Aerial), SkyExposure = L(a.SkyExposure, b.SkyExposure), SkyTint = Color.Lerp(a.SkyTint, b.SkyTint, t), StormWall = L(a.StormWall, b.StormWall), Lightning = L(a.Lightning, b.Lightning), Eruption = L(a.Eruption, b.Eruption), Shafts = L(a.Shafts, b.Shafts),
            };
        }
    }

    /// The rules of the weather layer: pure functions of (weather, biome, place, seed, clock). Nothing here reads
    /// quality settings, frame rate, the camera or UnityEngine.Random, so every client and every quality tier gets
    /// the same weather, wind and visibility for the same seed (online determinism).
    public static class MajesticWeatherRules
    {
        public const int Version = 1;

        static readonly Color White = Color.white;
        static WeatherLook Base() => new()
        {
            Cloud = .08f, CoverColor = new Color(.95f, .97f, 1f), FogTint = new Color(.8f, .83f, .86f), FogGlow = new Color(1f, .92f, .78f),
            SunTint = White, AmbientTint = White, Aerial = 1, FogFalloff = 1f / 60f, FogMax = .9f, SkyExposure = 1, SkyTint = White,
        };

        /// The look this weather draws in this biome. Tennis keeps its court readable (thinner fog, no deep cover).
        public static WeatherLook For(Weather w, Sky family, bool tennis)
        {
            var k = Base();
            switch (w)
            {
                case Weather.Gusty:
                    k.Cloud = .26f; k.Wind = .85f; k.Gust = 1; k.CloudShadows = .28f; k.GrassWaves = 1.2f; k.Aerial = .9f;
                    k.Whitecaps = family == Sky.Rain ? .7f : 0; k.Embers = family == Sky.Ash ? .25f : 0;
                    break;
                case Weather.Rain when family == Sky.Snow:   // Snow
                    k.Cloud = .55f; k.Precip = .6f; k.Fall = WeatherFall.Snow; k.Cover = .55f; k.IcePools = .3f;
                    k.FogDensity = .0035f; k.FogFalloff = 1f / 45f; k.FogTint = new Color(.86f, .89f, .95f); k.FogTintShare = .7f;
                    k.SunDim = .1f; k.SunTint = new Color(.9f, .94f, 1f); k.AmbientTint = new Color(.92f, .96f, 1.04f); k.Wind = .3f; k.Aerial = .3f; k.SkyExposure = .95f;
                    break;
                case Weather.Storm when family == Sky.Snow:  // Blizzard: no lightning
                    k.Cloud = .85f; k.Precip = 1; k.Fall = WeatherFall.Snow; k.Cover = .85f; k.IcePools = .2f;
                    k.FogDensity = .011f; k.FogFalloff = 1f / 50f; k.FogMax = .85f; k.FogTint = new Color(.84f, .87f, .93f); k.FogTintShare = .8f;
                    k.SunDim = .25f; k.SunTint = new Color(.86f, .9f, 1f); k.AmbientDim = .05f; k.AmbientTint = new Color(.9f, .95f, 1.05f); k.SkyExposure = .82f;
                    k.Wind = 1; k.Gust = 1; k.Aerial = .12f;
                    break;
                case Weather.Fog when family == Sky.Snow:    // Freezing fog
                    k.Cloud = .35f; k.Cover = .4f; k.Frost = 1; k.IcePools = .42f; k.FogDensity = .013f; k.FogFalloff = 1f / 5f; k.FogMax = .94f;
                    k.FogTint = new Color(.87f, .91f, .97f); k.FogTintShare = .8f; k.FogGlowStrength = .35f; k.SunDim = .12f; k.Aerial = .1f;
                    break;
                case Weather.Rain when family == Sky.Ash:    // Ashfall
                    k.Cloud = .62f; k.Precip = .6f; k.Fall = WeatherFall.Ash; k.Cover = .32f; k.LavaPools = .3f; k.CoverColor = new Color(.36f, .34f, .33f); k.Embers = .6f;
                    k.FogDensity = .003f; k.FogFalloff = 1f / 40f; k.FogTint = new Color(.42f, .3f, .3f); k.FogTintShare = .4f; k.FogGlow = new Color(1f, .45f, .2f); k.FogGlowStrength = .3f;
                    k.SunDim = .12f; k.SunTint = new Color(1f, .9f, .82f); k.AmbientTint = new Color(1.03f, .96f, .94f); k.Wind = .3f; k.Aerial = .3f;
                    k.SkyExposure = .55f; k.SkyTint = new Color(1.1f, .72f, .75f); k.StormWall = 0;   // (cost: the sky tint carries the mood)
                    break;
                case Weather.Storm when family == Sky.Ash:   // Eruption
                    k.Cloud = .85f; k.Precip = .75f; k.Fall = WeatherFall.Ash; k.Cover = .42f; k.LavaPools = .45f; k.CoverColor = new Color(.34f, .32f, .31f); k.Embers = 1;
                    k.FogDensity = .004f; k.FogFalloff = 1f / 45f; k.FogTint = new Color(.5f, .28f, .22f); k.FogTintShare = .45f; k.FogGlow = new Color(1f, .4f, .15f); k.FogGlowStrength = .5f;
                    k.SunDim = .15f; k.SunTint = new Color(1f, .86f, .74f); k.AmbientDim = .03f; k.AmbientTint = new Color(1.05f, .95f, .9f);
                    k.SkyExposure = .5f; k.SkyTint = new Color(1.35f, .62f, .42f); k.StormWall = .85f;
                    k.Wind = .6f; k.Gust = .6f; k.Aerial = .2f; k.Eruption = 1;
                    break;
                case Weather.Fog when family == Sky.Ash:     // Volcanic smoke: sulphur banks lit from below
                    k.Cloud = .45f; k.Cover = .15f; k.CoverColor = new Color(.36f, .34f, .33f); k.Embers = .45f; k.LavaPools = .3f;
                    k.FogDensity = .011f; k.FogFalloff = 1f / 30f; k.FogMax = .9f; k.FogTint = new Color(.78f, .46f, .28f); k.FogTintShare = .65f;
                    k.FogGlow = new Color(1f, .5f, .2f); k.FogGlowStrength = .6f; k.SunDim = .1f; k.SunTint = new Color(1f, .88f, .76f); k.Aerial = .1f;
                    k.SkyExposure = .75f; k.SkyTint = new Color(1.4f, .66f, .4f); k.StormWall = .25f;
                    break;
                case Weather.Rain:                           // Rain
                    k.Cloud = .8f; k.Precip = .7f; k.Fall = WeatherFall.Rain; k.Wet = .85f; k.Puddles = .46f;
                    k.FogDensity = .0016f; k.FogFalloff = 1f / 45f; k.FogMax = .7f; k.FogTint = new Color(.55f, .6f, .68f); k.FogTintShare = .55f;
                    k.SunDim = -.12f; k.SunTint = new Color(.92f, .94f, .98f); k.AmbientDim = 0; k.AmbientTint = new Color(.94f, .97f, 1.04f);
                    k.Wind = .4f; k.Gust = .3f; k.Whitecaps = .3f; k.Aerial = .25f; k.StormWall = .6f; k.SkyExposure = .62f;
                    break;
                case Weather.Storm:                          // Thunderstorm
                    k.Cloud = 1; k.Precip = 1; k.Fall = WeatherFall.Rain; k.Wet = 1; k.Puddles = .56f;
                    k.FogDensity = .0024f; k.FogFalloff = 1f / 45f; k.FogMax = .75f; k.FogTint = new Color(.36f, .4f, .48f); k.FogTintShare = .6f;
                    k.SunDim = -.25f; k.SunTint = new Color(1f, .86f, .64f);   /* W03: golden sun under the storm */ k.AmbientDim = 0; k.AmbientTint = new Color(.9f, .94f, 1.06f); k.SkyExposure = .45f;
                    k.Wind = .8f; k.Gust = .8f; k.Whitecaps = .8f; k.Aerial = .15f; k.StormWall = 1; k.Lightning = 1; k.Shafts = .55f;   // W03: sun breaking through on the far side
                    break;
                case Weather.Fog:                            // Sea fog: a bright bank, low over the water
                    k.Cloud = .3f; k.Wet = .25f; k.Puddles = .15f; k.FogDensity = .016f; k.FogFalloff = 1f / 4f; k.FogMax = .96f;   // a bank: thick low, thin by 8 m
                    k.FogTint = new Color(.86f, .87f, .86f); k.FogTintShare = .55f; k.FogGlowStrength = .45f; k.SunDim = .1f; k.Aerial = .08f;
                    break;
            }
            if (tennis)
            {
                // the court is the gameplay: fog stays a haze over the far stands, cover stays off the lines (see _MajClear)
                k.FogDensity *= .7f; k.FogMax = Mathf.Min(k.FogMax, .8f); k.Cover *= .6f;
                if (w == Weather.Fog) k.StormWall = 0;   // smoke / sea fog over a court: no cloud deck overhead (reads as a ceiling)
            }
            return k;
        }

        /// The biome's weather family for a place. Golf uses Weathers.SkyOf(hole) (holes 10 and 16 draw ash once
        /// chat 6 installs the SkyOf patch); tennis: the volcano is ash, the others sea.
        public static Sky FamilyForTennis(int venue) => venue == 2 ? Sky.Ash : Sky.Rain;

        /// Wind gusts: a smooth deterministic envelope 0..1 from the session seed and the shared environment clock
        /// (DreamEnvironment.Utc, synced from the host online). Same seed + same clock = same gust on every client.
        public static float Gust(int seed, double utc, float gustiness)
        {
            if (gustiness <= 0) return 0;
            double s = (seed & 0xffff) * .001;
            double t = utc % 3600.0;
            double g = .5 + .28 * Math.Sin(t * .61 + s) + .16 * Math.Sin(t * 1.37 + s * 2.3) + .1 * Math.Sin(t * 2.9 + s * 5.1);
            double burst = Math.Max(0, Math.Sin(t * .23 + s * 1.7)); burst = burst * burst * burst * burst;   // a strong gust every ~27 s
            return Mathf.Clamp01((float)((g * .7 + burst * .6) * gustiness));
        }

        /// Wind direction (xz unit vector) a weather blows: the game's own wind (golf) or a fixed bearing per venue
        /// and game (tennis), so every client agrees.
        public static Vector2 Direction(double directionDegrees)
        {
            double r = directionDegrees * Math.PI / 180.0;
            return new Vector2((float)Math.Sin(r), (float)Math.Cos(r));
        }

        /// Tennis: weather happens around play (Adnan, 10-17): on arrival (before the first serve of the match is
        /// struck), between games (from the game's last point until the next game's first ball is in play) and after
        /// the match. Never during a rally. `gamesSoFar` = games completed; `gamesAtLastRally` = games completed when
        /// the last rally began (-1 = none yet).
        public static bool TennisWeatherShows(bool rallyInPlay, bool matchOver, bool intro, int gamesSoFar, int gamesAtLastRally)
        {
            if (matchOver || intro) return true;
            if (rallyInPlay) return false;
            return gamesAtLastRally < 0 || gamesSoFar != gamesAtLastRally;
        }

        /// Gameplay visibility in golf fog (unchanged rule): the same function as DreamConditions.Visibility, the
        /// minimap and the old fog volume. The layer's fog on the ground never shows MORE than this allows.
        public static double Visibility(Vector3 p, Vector3 observer) => DreamConditions.Visibility(p.x, p.y, p.z, observer.x, observer.y, observer.z);

        /// Linear (URP) fog end so the object at `distance` gets at most `cap` fog: ball, flag and players read.
        public static float FogEndForCap(float start, float end, float distance, float cap)
        {
            if (distance <= start || end <= start) return end;
            float f = (distance - start) / (end - start);
            return f <= cap ? end : start + (distance - start) / cap;
        }
    }
}
