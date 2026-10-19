using UnityEngine;
using GolfArcade.Course;

namespace GolfArcade.EnvironmentArt
{
    /// Presentation adapter only. WeatherView supplies its already-blended values;
    /// no timers, random numbers, weather selection or wind simulation live here.
    public static class WeatherDirector
    {
        public static float Precipitation { get; private set; }
        public static float Storm { get; private set; }
        public static float Mist { get; private set; }
        public static int Revision { get; private set; }
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        public static void Reset()
        {
            Precipitation=Storm=Mist=0;Revision++;
            Shader.SetGlobalFloat("_EnvironmentWetness",0);
            Shader.SetGlobalFloat("_EnvironmentSnow",0);
            Shader.SetGlobalFloat("_EnvironmentStorm",0);
            Shader.SetGlobalFloat("_EnvironmentWeatherEnabled",0);
        }
        public static void Publish(float wet,float settled,float precipitation,float darkness,float mist,Sky biome)
        {
            bool active=DreamEnvironment.Current || EnvironmentLook.Stage>=5 && EnvironmentLook.Active;
            float p=active?Mathf.Clamp01(precipitation):0;
            // WeatherView intentionally keeps snow 40% brighter. Undo only that
            // presentation scale when identifying storm strength; never change its light.
            float weatherDarkness=biome==Sky.Snow?darkness/.6f:darkness;
            float s=active?Mathf.Clamp01((weatherDarkness-.42f)/.24f):0;
            float m=active?Mathf.Clamp01(mist):0;
            if(!Mathf.Approximately(p,Precipitation)||!Mathf.Approximately(s,Storm)||!Mathf.Approximately(m,Mist))Revision++;
            Precipitation=p;Storm=s;Mist=m;
            Shader.SetGlobalFloat("_EnvironmentWeatherEnabled",active?1:0);
            Shader.SetGlobalFloat("_EnvironmentWetness",active?Mathf.Clamp01(wet):0);
            Shader.SetGlobalFloat("_EnvironmentSnow",active && biome==Sky.Snow?Mathf.Clamp01(settled):0);
            Shader.SetGlobalFloat("_EnvironmentStorm",s);
        }
    }
}
