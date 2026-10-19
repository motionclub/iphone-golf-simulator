using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.Rendering;
using GolfArcade.Game;
using GolfArcade.Course;
using GolfArcade.EnvironmentArt;

namespace GolfArcade.Tennis
{
    /// Scene-level look values. No material keywords or sport-specific shader copies.
    public static class HeroLightingProfile
    {
        static bool golf, hub;
        static int golfHole;
        static WeatherView weatherView;
        static int lastPreset = -1;
        static bool enabled, explicitHeroEnabled;
        static int environmentRevision=-1, weatherRevision=-1;
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Initialize()
        {
            // Look-dev opt-in until the visual gates and on-device cost are verified.
            explicitHeroEnabled = System.Environment.GetEnvironmentVariable("VISUAL_HERO_LIGHTING") == "1";
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
            // Runtime initializers have no relative ordering guarantee. Resolve
            // the combined-stage opt-in again after its owner has initialized.
            bool nextEnabled=explicitHeroEnabled || EnvironmentLook.Stage>=2;
            if(nextEnabled!=enabled) { enabled=nextEnabled;lastPreset=-1; }
            // Read the weather's public state; never alter its lights, fog or particles.
            if(golf && !weatherView) weatherView=Object.FindFirstObjectByType<WeatherView>();
            var weather=golf && weatherView ? weatherView.Weather : Weather.Clear;
            int preset=golf ? 10+(int)weather+(golfHole==16?100:0) : hub ? 200 : (int)TennisVenue.Selected;
            if(preset==lastPreset && environmentRevision==EnvironmentLook.Revision && weatherRevision==WeatherDirector.Revision)return;
            environmentRevision=EnvironmentLook.Revision;weatherRevision=WeatherDirector.Revision;
            lastPreset=preset;
            Color rim=new(1,.96f,.88f); float strength=.35f;
            if(golf) {
                if(golfHole==16) { rim=new(1,.7f,.45f);strength=.55f; }
                if(weather==Weather.Rain || weather==Weather.Storm) { rim=new(.8f,.88f,1);strength=.5f; }
                else if(weather==Weather.Fog) { rim=new(.85f,.93f,1);strength=.25f; }
            } else if(!hub && TennisVenue.Selected==TennisVenueKind.Skyscraper) { rim=new(.85f,.93f,1);strength=.5f; }
            else if(!hub && TennisVenue.Selected==TennisVenueKind.Volcano) { rim=new(1,.7f,.45f);strength=.55f; }
            Shader.SetGlobalFloat("_HeroLightingEnabled",enabled?1:0);
            if(enabled) Shader.SetGlobalFloat("_HeroPresentationFill",.35f);
            var fillColour=new Color(1,.92f,1);
            if(golf && (golfHole==8 || golfHole==16)) fillColour=new Color(.97f,1,1.06f);
            else if(!golf && !hub && TennisVenue.Selected==TennisVenueKind.Volcano) fillColour=new Color(1,.92f,.83f);
            float ambientMin=.12f,ambientMax=.60f;
            if(EnvironmentLook.Active) {
                var look=EnvironmentLook.Current;
                fillColour=look.HeroFillColor;rim=look.HeroRimColor;strength=look.HeroRim;
                ambientMin=look.HeroAmbientMin;ambientMax=look.HeroAmbientMax;
                if(enabled)Shader.SetGlobalFloat("_HeroPresentationFill",look.HeroFill);
                if(EnvironmentLook.Stage>=5) {
                    rim=Color.Lerp(rim,new Color(.8f,.88f,1),WeatherDirector.Precipitation);
                    strength=Mathf.Lerp(strength,.25f,WeatherDirector.Mist);
                    ambientMax=Mathf.Lerp(ambientMax,.46f,Mathf.Max(WeatherDirector.Mist,WeatherDirector.Storm));
                }
            }
            Shader.SetGlobalFloat("_HeroAmbientMin",ambientMin);
            Shader.SetGlobalFloat("_HeroAmbientMax",ambientMax);
            Colour("_HeroFillColor",fillColour);
            // Weather's translucent foreground attenuates the hero after shading.
            // Compensate the skin light only, leaving weather and the venue intact.
            // Rain's authored precipitation target is .62; it already represents
            // a fully overcast state. Normalize that blend without a second timer.
            float overcast=Mathf.Clamp01(WeatherDirector.Precipitation/.62f);
            float skinExposure=golf && weather==Weather.Storm ? 1.45f : golf && weather==Weather.Rain ? 1.28f : 1f;
            if(EnvironmentLook.Active && EnvironmentLook.Stage>=5)
                skinExposure=1+.28f*overcast+.17f*WeatherDirector.Storm;
            Shader.SetGlobalFloat("_HeroSkinLightExposure",skinExposure);
            float faceWeather=golf && (weather==Weather.Rain || weather==Weather.Storm || weather==Weather.Fog) ? 1f : 0f;
            if(EnvironmentLook.Active && EnvironmentLook.Stage>=5)
                faceWeather=Mathf.Max(overcast,WeatherDirector.Mist);
            Shader.SetGlobalFloat("_HeroFaceLiftWeather",faceWeather);
            Colour("_HeroAnalyticRimColor",rim);
            Shader.SetGlobalFloat("_HeroAnalyticRimStrength",enabled?Mathf.Min(strength,.35f):0);
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
