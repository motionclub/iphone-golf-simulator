using UnityEngine;
using UnityEngine.SceneManagement;

namespace GolfArcade.Tennis
{
    /// Scene-level look values. No material keywords or sport-specific shader copies.
    public static class HeroLightingProfile
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Initialize()
        {
            Tennis();
            SceneManager.sceneLoaded -= SceneLoaded;
            SceneManager.sceneLoaded += SceneLoaded;
        }
        static void SceneLoaded(Scene scene,LoadSceneMode mode)
        {
            if(scene.name!="Golf")Tennis();
        }
        public static void Tennis() => Shader.SetGlobalFloat("_HeroProfile",0);
        static void Colour(string property,Color value)
        {
            var c=value.linear;
            Shader.SetGlobalVector(property,new Vector4(c.r,c.g,c.b,1));
        }
        public static void Golf(Light sun,Color sky,Color equator,Color ground,float rim)
        {
            Shader.SetGlobalFloat("_HeroProfile",1);
            Colour("_HeroKeyColor",sun?sun.color:Color.white);
            Shader.SetGlobalFloat("_HeroKeyStrength",sun?sun.intensity:1.1f);
            Colour("_HeroAmbientSky",sky);Colour("_HeroAmbientEquator",equator);Colour("_HeroAmbientGround",ground);
            Shader.SetGlobalFloat("_HeroRim",rim);
            Shader.SetGlobalFloat("_HeroExposure",.88f);
            Shader.SetGlobalFloat("_HeroShoulderKnee",.60f);
            Shader.SetGlobalFloat("_HeroShoulderCeiling",.90f);
        }
    }
}
