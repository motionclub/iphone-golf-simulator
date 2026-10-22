using UnityEngine;

namespace GolfArcade.EnvironmentArt
{
    public enum LightingMood { Midday, Golden, DuskNeon, Volcano, Snow }

    /// World and hero settings travel together. Authored colors are sRGB; hero
    /// irradiance/clamps are linear. Distance inputs are physical metres.
    public readonly struct LightingPreset
    {
        public readonly LightingMood Mood;
        public readonly Color SkyAmbient, EquatorAmbient, GroundAmbient, Haze;
        public readonly float Sun, Shadow, FogNear, FogFar, Contrast;
        public readonly Color HeroFillColor, HeroRimColor;
        public readonly float HeroFill, HeroRim, HeroAmbientMin, HeroAmbientMax;
        public LightingPreset(LightingMood mood, Color sky, Color equator, Color ground,
            Color haze, float sun, float shadow, float near, float far, float contrast,
            Color fill, Color rim, float rimStrength = .30f, float ambientMin = .12f)
        {
            Mood=mood; SkyAmbient=sky; EquatorAmbient=equator; GroundAmbient=ground;
            Haze=haze; Sun=sun; Shadow=shadow; FogNear=near; FogFar=far; Contrast=contrast;
            HeroFillColor=fill; HeroRimColor=rim; HeroFill=.35f; HeroRim=Mathf.Min(.35f,rimStrength);
            HeroAmbientMin=ambientMin; HeroAmbientMax=.60f;
        }
        public static LightingPreset For(LightingMood mood) => mood switch
        {
            LightingMood.Golden => new(mood,new(.43f,.48f,.62f),new(.46f,.37f,.30f),new(.18f,.21f,.17f),new(.74f,.64f,.62f),1.48f,.88f,55,620,24,new(1,.95f,.9f),new(1,.85f,.65f)),
            LightingMood.DuskNeon => new(mood,new(.30f,.31f,.48f),new(.29f,.25f,.35f),new(.14f,.16f,.23f),new(.52f,.44f,.61f),1.30f,.84f,90,1300,12,new(.96f,.97f,1),new(.85f,.93f,1),.35f),
            LightingMood.Volcano => new(mood,new(.27f,.32f,.46f),new(.27f,.28f,.34f),new(.27f,.15f,.11f),new(.38f,.31f,.40f),1.70f,.86f,75,1050,12,new(1,.94f,.88f),new(1,.7f,.45f),.30f),
            LightingMood.Snow => new(mood,new(.43f,.53f,.71f),new(.41f,.49f,.60f),new(.27f,.34f,.45f),new(.72f,.82f,.93f),1.60f,.77f,90,1050,9,new(.97f,.98f,1),new(.85f,.93f,1),.25f),
            _ => new(mood,new(.34f,.46f,.66f),new(.25f,.31f,.34f),new(.17f,.22f,.18f),new(.63f,.77f,.86f),1.85f,.85f,110,1000,10,new(1,.94f,.90f),new(1,.96f,.88f),.28f)
        };
    }
}
