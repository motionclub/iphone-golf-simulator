using System;
using GolfArcade.Course;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
namespace GolfArcade.EnvironmentArt
{
    /// Final owner of environment lighting. Venue builders supply daytime art; weather only supplies state.
    [DefaultExecutionOrder(10000)]
    public sealed class DreamEnvironment : MonoBehaviour
    {
        public static DreamEnvironment Current { get; private set; }
        public static EnvironmentSnapshot Session {get; private set;}
        static EnvironmentClock clock;
        static double? replayUtc,pendingOfflineUtc;static double correctionQueuedAt;static bool hostClock;
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void Reset(){Current=null;Session=null;clock=null;replayUtc=null;pendingOfflineUtc=null;hostClock=false;DreamVisibility.Reset();Shader.SetGlobalFloat("_DreamNight",0);Shader.SetGlobalFloat("_DreamGolf",0);WeatherDirector.Reset();}
        public static void ReplayAt(double? utc)=>replayUtc=utc;
        public static void SyncClock(double utcAnchor,double elapsed){if(utcAnchor>0&&double.IsFinite(elapsed)&&elapsed>=0){hostClock=true;pendingOfflineUtc=null;clock=new EnvironmentClock(utcAnchor+elapsed,Time.realtimeSinceStartupAsDouble);}}
        public static bool Enabled {
            get {
#if UNITY_EDITOR || DEVELOPMENT_BUILD
                return System.Environment.GetEnvironmentVariable("DREAM_WORLDS")!="0";
#else
                return true;
#endif
            }
        }
        public static double Utc {
            get {
#if UNITY_EDITOR || DEVELOPMENT_BUILD
                if(double.TryParse(System.Environment.GetEnvironmentVariable("DREAM_UTC"),System.Globalization.NumberStyles.Float,System.Globalization.CultureInfo.InvariantCulture,out double forced))return forced;
#endif
                if(replayUtc.HasValue)return replayUtc.Value;
                return clock?.At(Time.realtimeSinceStartupAsDouble) ?? DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            }
        }
        public static void StartSession(int seed,double utc=0)
        {
            bool authoritative=utc>0;
            if(utc<=0 && Session!=null && Session.seed==seed)return;
            hostClock=authoritative;pendingOfflineUtc=null;
            if(utc<=0)utc=DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            var saved=PlayerPrefs.GetString("dream.environment.v5","");
            if(!authoritative&&!string.IsNullOrEmpty(saved))try{var previous=JsonUtility.FromJson<EnvironmentSnapshot>(saved);if(previous!=null&&previous.Compatible&&previous.seed==seed){RestoreSession(saved);QueueOfflineClockCorrection(utc);CommitClockBoundary();return;}}catch{}
            replayUtc=null;Session=new EnvironmentSnapshot{seed=seed,utcAnchor=utc};
            clock=new EnvironmentClock(utc,Time.realtimeSinceStartupAsDouble);
        }
        public static void QueueOfflineClockCorrection(double utc)
        {
            if(hostClock||!double.IsFinite(utc)||utc<=0)return;
            pendingOfflineUtc=utc;correctionQueuedAt=Time.realtimeSinceStartupAsDouble;
        }
        public static void CommitClockBoundary()
        {
            if(!hostClock&&pendingOfflineUtc.HasValue){
                double now=Time.realtimeSinceStartupAsDouble;
                clock=new EnvironmentClock(pendingOfflineUtc.Value+Math.Max(0,now-correctionQueuedAt),now);pendingOfflineUtc=null;
            }
        }
        public static string Snapshot()
        {
            if(Session==null)return "";Session.elapsed=Math.Max(0,Utc-Session.utcAnchor);return JsonUtility.ToJson(Session);
        }
        public static bool RestoreSession(string json)
        {
            EnvironmentSnapshot state;try{state=JsonUtility.FromJson<EnvironmentSnapshot>(json);}catch{return false;}
            if(state==null||!state.Compatible)return false;hostClock=false;pendingOfflineUtc=null;Session=state;clock=new EnvironmentClock(state.utcAnchor+state.elapsed,Time.realtimeSinceStartupAsDouble);return true;
        }
        public Weather Condition {get; private set;}
        /// Called at the end of every Apply, after the clock/weather light; RenderedSky reads the result.
        public static System.Action<DreamEnvironment> AfterApply;
        public bool IsTennis => tennis; public int Location => location;
        bool tennis, restored;int location; Light sun;Material previousSky,sky;
        Color daySun,daySky,dayEquator,dayGround,fogColor,ambient;
        float dayIntensity,shadow,fogNear,fogFar,reflection;Quaternion sunRotation;
        bool fog;FogMode fogMode;AmbientMode ambientMode;bool ownsSky=true;
        Volume volume;ColorAdjustments grade;float exposure;
        public static DreamEnvironment Install(Transform parent,bool tennis,Weather weather,int location)
        {
            if(!Enabled)return null;
            if(Current){var previous=Current;previous.Release();Destroy(previous.gameObject);}
            var go=new GameObject("Dream world environment");go.transform.SetParent(parent,false);
            var e=go.AddComponent<DreamEnvironment>();Current=e;e.tennis=tennis;e.location=location;e.Capture();e.SetWeather(weather);
            if(Session==null)StartSession(UnityEngine.Random.Range(1,int.MaxValue));
            Session.location=location;Session.weather=(int)weather;
            if(!parent.GetComponentInChildren<LuminousCoastFrameBudget>())go.AddComponent<LuminousCoastFrameBudget>();
            e.Apply();return e;
        }
        void Capture()
        {
            sun=RenderSettings.sun;if(!sun)sun=GameObject.Find("Sun")?.GetComponent<Light>();
            if(sun){daySun=sun.color;dayIntensity=sun.intensity;shadow=sun.shadowStrength;sunRotation=sun.transform.rotation;}
            daySky=RenderSettings.ambientSkyColor;dayEquator=RenderSettings.ambientEquatorColor;dayGround=RenderSettings.ambientGroundColor;
            ambient=RenderSettings.ambientLight;ambientMode=RenderSettings.ambientMode;
            fog=RenderSettings.fog;fogMode=RenderSettings.fogMode;fogColor=RenderSettings.fogColor;fogNear=RenderSettings.fogStartDistance;fogFar=RenderSettings.fogEndDistance;reflection=RenderSettings.reflectionIntensity;
            previousSky=RenderSettings.skybox;
            // Rendered backgrounds (work/rendered-backgrounds): a sky we render from the real light
            // replaces the painted panorama where a venue has a profile; DreamSky stays the fallback.
            var rendered=RenderedSky.Enabled?RenderedBackdrop.SkyProfile(tennis,location):null;
            if(rendered!=null){sky=RenderedSky.Install(transform.parent,rendered);ownsSky=false;if(sky)RenderSettings.skybox=sky;RenderedBackdrop.Build(transform.parent,tennis,location);}
            var shader=sky?null:Resources.Load<Shader>("Environment/DreamSky");
            if(shader){sky=new Material(shader){name="Dream world clock sky"};bool coastal=location==7||location==8||location==9||location==12||location==15||location==100;
                Texture panorama=coastal?Resources.Load<Texture2D>("Environment/LuminousCoast/ArchipelagoSky"):
                    previousSky&&previousSky.HasProperty("_Panorama")?previousSky.GetTexture("_Panorama"):Resources.Load<Texture2D>("Course/Resort/SkyCoastalSmall");
                sky.SetTexture("_Panorama",panorama);RenderSettings.skybox=sky;}
            volume=FindFirstObjectByType<Volume>();if(volume&&volume.profile.TryGet(out grade))exposure=grade.postExposure.value;
        }
        public void SetWeather(Weather weather){Condition=weather;if(Session!=null)Session.weather=(int)weather;}
        void LateUpdate(){if(Current==this)Apply();}
        void Apply()
        {
            float day=(float)DreamConditions.Daylight(Utc), sunset=(float)DreamConditions.Sunset(Utc);
            float cloud=Condition==Weather.Storm?.65f:Condition==Weather.Rain?.38f:Condition==Weather.Fog?.3f:.08f;
            var warm=new Color(1,.59f,.34f);var moon=tennis?new Color(.85f,.9f,1):new Color(.64f,.78f,1);
            if(sun){sun.color=Color.Lerp(Color.Lerp(moon,daySun,day),warm,sunset*.65f);sun.intensity=Mathf.Lerp(tennis?1.15f:1f,Mathf.Max(1.7f,dayIntensity),day)*(1-cloud*.5f);sun.shadowStrength=shadow*(1-cloud*.7f);
                float h=(float)DreamConditions.EstHour(Utc);sun.transform.rotation=Quaternion.Euler(Mathf.Lerp(24,58,day),-105+(h-12)*7,0);}
            RenderSettings.ambientMode=AmbientMode.Trilight;
            RenderSettings.ambientSkyColor=Color.Lerp(new Color(.28f,.36f,.48f),daySky,day)*(1-cloud*.25f);
            RenderSettings.ambientEquatorColor=Color.Lerp(new Color(.26f,.30f,.4f),dayEquator,day)*(1-cloud*.2f);
            RenderSettings.ambientGroundColor=Color.Lerp(new Color(.10f,.14f,.20f),dayGround,day);
            var haze=Color.Lerp(new Color(.09f,.14f,.24f),fogColor,day);haze=Color.Lerp(haze,new Color(.7f,.42f,.34f),sunset*.38f);
            RenderSettings.fog=true;RenderSettings.fogMode=FogMode.Linear;RenderSettings.fogColor=haze;
            // Golf uses its analytic density volume and observation mask. Tennis retains a clear court envelope.
            RenderSettings.fogStartDistance=tennis?45:Condition==Weather.Fog?12:Mathf.Max(120,fogNear);
            RenderSettings.fogEndDistance=tennis?(Condition==Weather.Fog?150:800):Condition==Weather.Fog?115:Mathf.Max(500,fogFar);
            RenderSettings.reflectionIntensity=Mathf.Lerp(.35f,.85f,day);
            if(grade)grade.postExposure.Override(Mathf.Clamp(exposure, -.25f,.35f));
            if(sky){sky.SetFloat("_Ice",Session!=null&&Session.location==17?1:0);sky.SetFloat("_Day",day);sky.SetFloat("_Sunset",sunset);sky.SetFloat("_Cloud",cloud);sky.SetFloat("_Magma",Session!=null&&(Session.location==102||Session.location==10||Session.location==16||Session.location>=21&&Session.location<=23)?1:0);RenderSettings.skybox=sky;}
            Shader.SetGlobalFloat("_DreamNight",1-day);
            Shader.SetGlobalFloat("_DreamGolf",tennis?0:1);
            Shader.SetGlobalFloat("_EnvironmentWeatherEnabled",1);
            // WeatherDirector owns biome-specific wetness and snow/ash deposition.
            AfterApply?.Invoke(this);   // venue signature-hour layers (Majestic) adjust sun/ambient/fog/sky floats here
        }
        public void Release()
        {
            if(restored)return;restored=true;
            if(Current==this){
                if(sun){sun.color=daySun;sun.intensity=dayIntensity;sun.shadowStrength=shadow;sun.transform.rotation=sunRotation;}
                RenderSettings.ambientMode=ambientMode;RenderSettings.ambientLight=ambient;RenderSettings.ambientSkyColor=daySky;RenderSettings.ambientEquatorColor=dayEquator;RenderSettings.ambientGroundColor=dayGround;
                RenderSettings.skybox=previousSky;RenderSettings.fog=fog;RenderSettings.fogMode=fogMode;RenderSettings.fogColor=fogColor;RenderSettings.fogStartDistance=fogNear;RenderSettings.fogEndDistance=fogFar;RenderSettings.reflectionIntensity=reflection;
                if(grade)grade.postExposure.Override(exposure);Current=null;DreamVisibility.Reset();Shader.SetGlobalFloat("_DreamNight",0);Shader.SetGlobalFloat("_DreamGolf",0);replayUtc=null;WeatherDirector.Reset();
            }
        }
        void OnApplicationPause(bool paused){
            if(paused&&Session!=null){PlayerPrefs.SetString("dream.environment.v5",Snapshot());PlayerPrefs.Save();}
            else if(!paused)QueueOfflineClockCorrection(DateTimeOffset.UtcNow.ToUnixTimeSeconds());
        }
        void OnDisable()=>Release();
        void OnDestroy(){Release();if(sky&&ownsSky)Destroy(sky);}
    }
}
