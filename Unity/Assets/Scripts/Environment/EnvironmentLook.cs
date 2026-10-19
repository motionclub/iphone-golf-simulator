using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using GolfArcade.Course;
using GolfArcade.Tennis;

namespace GolfArcade.EnvironmentArt
{
    /// Explicit staged look-dev. Phase 2 is Resort/hole7 only; phase 4 adds the
    /// other presets. Existing venue builders retain layout, sun direction and sky assets.
    public static class EnvironmentLook
    {
        public static int Stage { get; private set; }
        public static LightingPreset Current { get; private set; }
        public static bool Active { get; private set; }
        public static int Revision { get; private set; }
        const float MetresPerYard=.9144f;
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void Reset()
        {
            int stage=7;
#if UNITY_EDITOR || DEVELOPMENT_BUILD
            if(int.TryParse(System.Environment.GetEnvironmentVariable("VISUAL_ENVIRONMENT_STAGE"),out int reviewStage))stage=reviewStage;
#endif
            Stage=Mathf.Clamp(stage,0,7); Active=false; Current=LightingPreset.For(LightingMood.Midday); Revision=0;
            Shader.SetGlobalFloat("_EnvironmentDepthEnabled",0);
        }
        public static LightingMood GolfMood(int hole) => hole==17 ? LightingMood.Snow
            : hole==10 || hole==16 || hole>=21 ? LightingMood.Volcano
            : hole==8 ? LightingMood.Golden : LightingMood.Midday;
        public static LightingMood TennisMood(TennisVenueKind venue) => venue==TennisVenueKind.Skyscraper ? LightingMood.DuskNeon
            : venue==TennisVenueKind.Volcano ? LightingMood.Volcano : LightingMood.Midday;
        static void Select(LightingMood mood,bool active,bool golf)
        {
            Active=active;Current=LightingPreset.For(mood);Revision++;
            Shader.SetGlobalFloat("_EnvironmentDepthEnabled",active?1:0);
            Shader.SetGlobalFloat("_EnvironmentMetresPerUnit",golf?MetresPerYard:1);
            Shader.SetGlobalVector("_EnvironmentHazeColor",Current.Haze.linear);
            // World-space layer thresholds. Near gameplay remains untouched.
            Shader.SetGlobalVector("_EnvironmentDepthLayers",new Vector4(90,280,900,.72f));
        }
        public static void Tennis(Light sun,TennisVenueKind venue)
        {
            Select(TennisMood(venue),Stage>=4 || Stage>=2 && venue==TennisVenueKind.Resort,false);
            if(!Active)return;
            ApplyWorld(sun,1);
            if(venue==TennisVenueKind.Resort && RenderSettings.skybox) {
                var sky=RenderSettings.skybox;
                if(sky.HasProperty("_Exposure"))sky.SetFloat("_Exposure",1.08f);
                if(sky.HasProperty("_DayHaze"))sky.SetFloat("_DayHaze",.055f);
            }
        }
        public static GolfAtmosphere.Look Golf(GolfAtmosphere.Look source,int hole)
        {
            Select(GolfMood(hole),Stage>=4 || Stage>=2 && hole==7,true);
            if(source==null){Active=false;Shader.SetGlobalFloat("_EnvironmentDepthEnabled",0);return null;}
            if(!Active)return source;
            var look=source.Copy();var p=Current;
            look.SunIntensity=p.Sun;look.ShadowStrength=p.Shadow;
            look.AmbientSky=p.SkyAmbient;look.AmbientEquator=p.EquatorAmbient;look.AmbientGround=p.GroundAmbient;
            look.FogColor=p.Haze;look.FogStart=p.FogNear/MetresPerYard;look.FogEnd=p.FogFar/MetresPerYard;
            look.SkyExposure=Mathf.Min(1.08f,look.SkyExposure*1.06f);
            return look;
        }
        public static void Hub(Light sun)
        {
            Select(LightingMood.Golden,Stage>=4,false);
            if(Active) {
                ApplyWorld(sun,1);
                // The hub paints its sky on an Unlit dome at 760 m. Linear fog
                // would erase that painting. HubSurface/HubWater already use
                // the preset's layered distance haze on scenery, independently.
                RenderSettings.fog=false;
            }
        }
        static void ApplyWorld(Light sun,float metresPerUnit)
        {
            var p=Current;
            if(sun){sun.intensity=p.Sun;sun.shadowStrength=p.Shadow;}
            RenderSettings.ambientMode=AmbientMode.Trilight;
            RenderSettings.ambientSkyColor=p.SkyAmbient;RenderSettings.ambientEquatorColor=p.EquatorAmbient;RenderSettings.ambientGroundColor=p.GroundAmbient;
            RenderSettings.fog=true;RenderSettings.fogMode=FogMode.Linear;RenderSettings.fogColor=p.Haze;
            RenderSettings.fogStartDistance=p.FogNear/metresPerUnit;RenderSettings.fogEndDistance=p.FogFar/metresPerUnit;
        }
        public static void Post(VolumeProfile profile)
        {
            if(!Active || !profile)return;
            if(profile.TryGet(out ColorAdjustments grade))grade.contrast.Override(Current.Contrast);
            // Adnan selected ACES from the actual Unity comparison (2026-10-15).
            // Both tiers share the same mapper; the env override is diagnostic only.
            string mapper=System.Environment.GetEnvironmentVariable("VISUAL_TONEMAPPER");
            if(profile.TryGet(out Tonemapping tone))
                tone.mode.Override(mapper=="Neutral"?TonemappingMode.Neutral:TonemappingMode.ACES);
        }
        public static Color Court(Color original,TennisVenueKind venue,bool runoff)
        {
            if(Stage<2 || venue!=TennisVenueKind.Resort && Stage<4)return original;
            return venue switch {
                TennisVenueKind.Skyscraper => runoff?new(.18f,.28f,.42f):new(.15f,.48f,.78f),
                TennisVenueKind.Volcano => runoff?new(.38f,.35f,.36f):new(.70f,.68f,.69f),
                _ => runoff?new(.18f,.40f,.35f):new(.065f,.46f,.72f)
            };
        }
    }
}
