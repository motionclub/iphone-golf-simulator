using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.Rendering;
using GolfArcade.Game;
using GolfArcade.Course;

namespace GolfArcade.Tennis
{
    /// Scene-level look values. No material keywords or sport-specific shader copies.
    public static class HeroLightingProfile
    {
        static bool golf, hub;
        static int golfHole;
        static WeatherView weatherView;
        static int lastPreset = -1;
        static bool enabled;
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Initialize()
        {
            // Look-dev opt-in until the visual gates and on-device cost are verified.
            enabled = System.Environment.GetEnvironmentVariable("VISUAL_HERO_LIGHTING") == "1";
            Tennis();
            RenderPipelineManager.beginCameraRendering -= BeforeCamera;
            RenderPipelineManager.beginCameraRendering += BeforeCamera;
            SceneManager.sceneLoaded -= SceneLoaded;
            SceneManager.sceneLoaded += SceneLoaded;
        }
        static void SceneLoaded(Scene scene,LoadSceneMode mode)
        {
            if(scene.name!="Golf")Tennis();
        }
        static void Presentation()
        {
            Shader.SetGlobalFloat("_HeroFilmResponse",1);
            Shader.SetGlobalFloat("_HeroSkinPolish", System.Environment.GetEnvironmentVariable("VISUAL_CHARACTER_SKIN_POLISH")=="1" ? 1f : 0f);
            Shader.SetGlobalFloat("_HeroPresentationFill", System.Environment.GetEnvironmentVariable("VISUAL_CHARACTER_STAGE_LIGHT")=="0" ? 0f : .12f);
        }
        public static void Tennis()
        {
            golf=false; hub=SceneManager.GetActiveScene().name=="Hub"; weatherView=null; lastPreset=-1;
            Shader.SetGlobalFloat("_HeroProfile",0); Presentation();
            ApplyPresentationPreset();
        }
        static void BeforeCamera(ScriptableRenderContext context,Camera camera) => ApplyPresentationPreset();
        static void ApplyPresentationPreset()
        {
            // Read the weather's public state; never alter its lights, fog or particles.
            if(golf && !weatherView) weatherView=Object.FindFirstObjectByType<WeatherView>();
            var weather=golf && weatherView ? weatherView.Weather : Weather.Clear;
            int preset=golf ? 10+(int)weather+(golfHole==16?100:0) : hub ? 200 : (int)TennisVenue.Selected;
            if(preset==lastPreset)return;
            lastPreset=preset;
            Color rim=new(1,.96f,.88f); float strength=.35f;
            if(golf) {
                if(golfHole==16) { rim=new(1,.7f,.45f);strength=.55f; }
                if(weather==Weather.Rain || weather==Weather.Storm) { rim=new(.8f,.88f,1);strength=.5f; }
                else if(weather==Weather.Fog) { rim=new(.85f,.93f,1);strength=.25f; }
            } else if(!hub && TennisVenue.Selected==TennisVenueKind.Skyscraper) { rim=new(.85f,.93f,1);strength=.5f; }
            else if(!hub && TennisVenue.Selected==TennisVenueKind.Volcano) { rim=new(1,.7f,.45f);strength=.55f; }
            Shader.SetGlobalFloat("_HeroLightingEnabled",enabled?1:0);
            if(enabled) Shader.SetGlobalFloat("_HeroPresentationFill",.95f);
            var fillColour=new Color(1,.92f,1);
            if(golf && (golfHole==8 || golfHole==16)) fillColour=new Color(.97f,1,1.06f);
            else if(!golf && !hub && TennisVenue.Selected==TennisVenueKind.Volcano) fillColour=new Color(1,.92f,.83f);
            Colour("_HeroFillColor",fillColour);
            // Weather's translucent foreground attenuates the hero after shading.
            // Compensate the skin light only, leaving weather and the venue intact.
            float skinExposure=golf && weather==Weather.Storm ? 1.45f : golf && weather==Weather.Rain ? 1.28f : 1f;
            Shader.SetGlobalFloat("_HeroSkinLightExposure",skinExposure);
            Colour("_HeroAnalyticRimColor",rim);
            Shader.SetGlobalFloat("_HeroAnalyticRimStrength",enabled?strength:0);
        }
        static void Colour(string property,Color value)
        {
            var c=value.linear;
            Shader.SetGlobalVector(property,new Vector4(c.r,c.g,c.b,1));
        }
        public static void Golf(Light sun,Color sky,Color equator,Color ground,float rim,float clothExposure=3f,int holeNumber=0)
        {
            golf=true; golfHole=holeNumber; lastPreset=-1;
            Presentation(); ApplyPresentationPreset();
            Shader.SetGlobalFloat("_HeroProfile",1);
            Colour("_HeroKeyColor",sun?sun.color:Color.white);
            Shader.SetGlobalFloat("_HeroKeyStrength",sun?sun.intensity:1.1f);
            Colour("_HeroAmbientSky",sky);Colour("_HeroAmbientEquator",equator);Colour("_HeroAmbientGround",ground);
            // Material rim is a surface response, separate from the course's
            // directional rim light. Keep each authored material's strength.
            Shader.SetGlobalFloat("_HeroRim",1f);
            Shader.SetGlobalFloat("_HeroExposure",1f);
            Shader.SetGlobalFloat("_HeroShoulderKnee",.88f);
            Shader.SetGlobalFloat("_HeroShoulderCeiling",.985f);
            // Let neutral garments inherit the course lighting without inverse tint compensation.
            Shader.SetGlobalVector("_HeroClothBalance",Vector4.one);
            Shader.SetGlobalFloat("_HeroClothExposure",clothExposure);
        }
    }
}
