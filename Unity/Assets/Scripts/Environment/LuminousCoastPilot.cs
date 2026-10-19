using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using GolfArcade.Course;
using GolfArcade.Tennis;

namespace GolfArcade.EnvironmentArt
{
    /// Render-only art pilot. Exactly Resort tennis and authored golf hole 12.
    /// Owns every material it changes; the source meshes and all colliders stay intact.
    public sealed class LuminousCoastPilot : MonoBehaviour
    {
        public static bool Enabled => System.Environment.GetEnvironmentVariable("LUMINOUS_COAST") != "0";
        public static bool Active => activeInstances>0;
        static int activeInstances;
        bool registered;
        readonly List<Material> owned = new();
        static Material pilotSky;
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetSky() { if(pilotSky)Destroy(pilotSky);pilotSky=null;activeInstances=0; }
        public static Material Sky(Material sky, bool golf)
        {
            if (!Enabled || !sky) return sky;
            var texture = Resources.Load<Texture2D>("Environment/LuminousCoast/ArchipelagoSky");
            var shader=Resources.Load<Shader>("Environment/LuminousCoast/CoastalSky");
            if (!texture || !shader) return sky;
            if(!pilotSky)pilotSky=new Material(shader) {name="Luminous Coast distant panorama"};
            pilotSky.SetTexture("_Panorama", texture);
            pilotSky.SetFloat("_Rotation", -54);
            pilotSky.SetFloat("_LongitudeScale", 2.0f);
            pilotSky.SetFloat("_Exposure", 1.04f);
            pilotSky.SetFloat("_AltitudeScale", 2.8f);
            pilotSky.SetFloat("_LatitudeOffset", .033f);
            return pilotSky;
        }
        public static void TennisLight(Light sun)
        {
            if (!Enabled || !TennisVenue.IsResort) return;
            sun.color = new Color(1,.95f,.86f);
            sun.intensity = 1.65f;
            sun.shadowStrength = .70f;
            var fill=GameObject.Find("Hero fill")?.GetComponent<Light>();
            if(fill)fill.intensity=.38f;
            RenderSettings.ambientSkyColor = new Color(.51f,.64f,.80f);
            RenderSettings.ambientEquatorColor = new Color(.47f,.53f,.55f);
            RenderSettings.ambientGroundColor = new Color(.29f,.34f,.30f);
            RenderSettings.fogColor = new Color(.56f,.73f,.81f);
            RenderSettings.fogStartDistance = 210;
            RenderSettings.fogEndDistance = 1300;
            RenderSettings.skybox=Sky(RenderSettings.skybox, false);
        }
        public static GolfAtmosphere.Look GolfLight(GolfAtmosphere.Look source, int hole)
        {
            if (!Enabled || hole != 12 || source == null) return source;
            var look = source.Copy();
            look.SunColor = new Color(1,.91f,.79f);
            if(DreamGolfGarden.Enabled){look.SunAzimuth=-112;look.SunElevation=38;look.FillIntensity=.08f;look.RimIntensity=.16f;}
            look.SunIntensity = 2.1f;
            look.AmbientSky = new Color(.48f,.58f,.76f);
            look.AmbientEquator = new Color(.43f,.43f,.54f);
            look.AmbientGround = new Color(.18f,.24f,.27f);
            look.ShadowStrength = .75f;
            look.FogColor = new Color(.57f,.73f,.82f);
            look.FogStart = 260; look.FogEnd = 1800;
            return look;
        }
        public static void Build(Transform parent, bool golf)
        {
            if (!Enabled || parent.GetComponentInChildren<LuminousCoastPilot>()) return;
            var root = new GameObject("Luminous Coast pilot");
            root.transform.SetParent(parent, true);
            root.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            var owner = root.AddComponent<LuminousCoastPilot>();
            owner.Install(parent, golf);
        }
        void Install(Transform parent, bool golf)
        {
            registered=true;activeInstances++;
            gameObject.AddComponent<LuminousCoastFrameBudget>();
            if (!golf) {
                foreach (var r in parent.GetComponentsInChildren<MeshRenderer>())
                    if (r.sharedMaterial && r.sharedMaterial.shader.name=="GolfArcade/TennisHorizon2") r.enabled=false;
            }
            Style(parent, golf);
            if(golf)DreamGolfGarden.Build(parent);
            Debug.Log("[LuminousCoast] installed "+(golf?"golf12":"tennis Resort")+"; render-only pilot, no new lights/colliders, owned materials="+owned.Count);
        }
        System.Collections.IEnumerator Start()
        {
            // Backdrop water is attached after the authored golf course finishes.
            for(int i=0;i<4;i++)yield return null;
            bool golf=UnityEngine.SceneManagement.SceneManager.GetActiveScene().name=="Golf";
            if(golf) {
                foreach(var r in FindObjectsByType<Renderer>(FindObjectsInactive.Include,FindObjectsSortMode.None)) {
                    if(r.name=="Open sea" || r.name=="WATER_WAVES")Style(r.transform,true);
                    if(r.name=="WATER_WAVES" || r.name=="WATER_GLINTS" || (r.sharedMaterial && r.sharedMaterial.shader.name=="GolfArcade/GolfDistantLand"))r.enabled=false;
                }
            }
        }
        void Style(Transform parent,bool golf)
        {
            var copies = new Dictionary<Material,Material>();
            foreach (var r in parent.GetComponentsInChildren<Renderer>(true)) {
                if (r.transform.IsChildOf(transform)) continue;
                var slots=r.sharedMaterials; bool changed=false;
                for (int i=0;i<slots.Length;i++) {
                    var source=slots[i]; if (!source) continue;
                    string sn=source.shader.name;
                    bool water=sn=="GolfArcade/GolfOcean" || sn=="GolfArcade/TennisWater";
                    bool court=!golf && !TennisVenue.CourtColorOverride.HasValue && (source.name.StartsWith("TropicalV3_002") || source.name.StartsWith("TropicalV3_011"));
                    bool cliff=golf && source.name.Contains("Coastal 12 authored chalk");
                    bool wood=golf && DreamGolfGarden.Enabled && source.name.StartsWith("Course 12 Wood");
                    if (!water && !court && !cliff && !wood) continue;
                    if (!copies.TryGetValue(source,out var m)) {
                        m=new Material(source) { name=source.name+" Luminous Coast" }; owned.Add(m); copies[source]=m;
                        if (water) {
                            m.SetColor("_Shallow",new Color(.035f,.67f,.62f));
                            m.SetColor("_Deep",new Color(.025f,.35f,.50f));
                            m.SetColor("_Sky",new Color(.25f,.61f,.77f));
                            m.SetFloat("_Sparkle",golf&&DreamGolfGarden.Enabled?.28f:.80f); m.SetFloat("_WaveScale",.20f);
                            if(m.HasProperty("_ResortPop"))m.SetFloat("_ResortPop",.14f);
                            if(m.HasProperty("_DeepDistance"))m.SetFloat("_DeepDistance",110);
                            if(m.HasProperty("_WaterOrigin"))m.SetVector("_WaterOrigin",Vector4.zero);
                            if(m.HasProperty("_SkyMap"))m.SetTexture("_SkyMap",Resources.Load<Texture2D>("Environment/LuminousCoast/SummerSky"));
                        }
                        if (court) {
                            bool apron=source.name.StartsWith("TropicalV3_011");
                            m.SetColor("_BaseColor",apron?new Color(.13f,.34f,.32f):new Color(.045f,.37f,.64f));
                            m.SetFloat("_Smoothness",.16f);
                        }
                        if (wood) {
                            m.SetFloat("_PaletteMode",1);m.SetColor("_BaseColor",Color.white);
                            m.SetColor("_LowColor",new Color(.25f,.18f,.13f));m.SetColor("_HighColor",new Color(.62f,.47f,.29f));
                            m.SetFloat("_DetailContrast",.8f);
                        }
                        if (cliff) {
                            m.SetColor("_LowColor",new Color(.22f,.28f,.32f));
                            m.SetColor("_HighColor",new Color(.88f,.86f,.76f));
                            m.SetFloat("_BumpScale",.70f); m.SetFloat("_DetailContrast",5.6f);
                        }
                    }
                    slots[i]=m; changed=true;
                }
                if(changed)r.sharedMaterials=slots;
            }
        }
        void OnDestroy() { if(registered)activeInstances=Mathf.Max(0,activeInstances-1);foreach(var m in owned) if(m)Destroy(m); }
    }
}
