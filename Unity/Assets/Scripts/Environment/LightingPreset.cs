using UnityEngine;

namespace GolfArcade.EnvironmentArt
{
    public enum LightingMood { Midday, Golden, DuskNeon, Volcano, Snow }

    /// Environment-only settings. Authored colors are sRGB; distances are physical metres.
    /// Character lighting retains its independent, pre-pass presentation.
    public readonly struct LightingPreset
    {
        public readonly LightingMood Mood;
        public readonly Color SkyAmbient, EquatorAmbient, GroundAmbient, Haze;
        public readonly float Sun, Shadow, FogNear, FogFar, Contrast;
        public LightingPreset(LightingMood mood, Color sky, Color equator, Color ground,
            Color haze, float sun, float shadow, float near, float far, float contrast)
        {
            Mood=mood; SkyAmbient=sky; EquatorAmbient=equator; GroundAmbient=ground;
            Haze=haze; Sun=sun; Shadow=shadow; FogNear=near; FogFar=far; Contrast=contrast;
        }
        public static LightingPreset For(LightingMood mood) => mood switch
        {
            LightingMood.Golden => new(mood,new(.43f,.48f,.62f),new(.46f,.37f,.30f),new(.18f,.21f,.17f),new(.74f,.64f,.62f),1.48f,.88f,55,620,24),
            LightingMood.DuskNeon => new(mood,new(.30f,.31f,.48f),new(.29f,.25f,.35f),new(.14f,.16f,.23f),new(.52f,.44f,.61f),1.30f,.84f,90,1300,12),
            LightingMood.Volcano => new(mood,new(.27f,.32f,.46f),new(.27f,.28f,.34f),new(.27f,.15f,.11f),new(.38f,.31f,.40f),1.70f,.86f,75,1050,12),
            LightingMood.Snow => new(mood,new(.43f,.53f,.71f),new(.41f,.49f,.60f),new(.27f,.34f,.45f),new(.72f,.82f,.93f),1.60f,.77f,90,1050,9),
            _ => new(mood,new(.34f,.46f,.66f),new(.25f,.31f,.34f),new(.17f,.22f,.18f),new(.63f,.77f,.86f),1.85f,.85f,110,1000,10)
        };
    }
}
