using System;
using System.Reflection;
using GolfArcade.Course;
using GolfArcade.EnvironmentArt;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests
{
    public class EnvironmentLookTests
    {
        string previousStage;
        static void SetStage(string value)
        {
            System.Environment.SetEnvironmentVariable("VISUAL_ENVIRONMENT_STAGE",value);
            typeof(EnvironmentLook).GetMethod("Reset",BindingFlags.Static|BindingFlags.NonPublic).Invoke(null,null);
            WeatherDirector.Reset();
        }
        [SetUp] public void Setup()=>previousStage=System.Environment.GetEnvironmentVariable("VISUAL_ENVIRONMENT_STAGE");
        [TearDown] public void Cleanup()=>SetStage(previousStage);
        [Test] public void DefaultAndOutOfScopeLookDevLeaveAuthoredGolfProfileIntact()
        {
            var source=GolfAtmosphere.Holes[9];float fog=source.FogEnd;
            SetStage(null);Assert.AreSame(source,EnvironmentLook.Golf(source,7));
            SetStage("2");Assert.AreSame(source,EnvironmentLook.Golf(source,9));
            var revised=EnvironmentLook.Golf(source,7);
            Assert.AreNotSame(source,revised);Assert.AreEqual(fog,source.FogEnd);
            Assert.That(revised.FogEnd*.9144f,Is.EqualTo(EnvironmentLook.Current.FogFar).Within(.001));
            Assert.AreEqual(source.SunAzimuth,revised.SunAzimuth);
            Assert.AreEqual(source.SunElevation,revised.SunElevation);
            Assert.AreEqual(source.BallExposure,revised.BallExposure);
            Assert.AreEqual(source.FigureExposure,revised.FigureExposure);
        }
        [Test] public void SwitchingToLegacyHoleCannotLeakDepthOrWeather()
        {
            SetStage("5");EnvironmentLook.Golf(GolfAtmosphere.Holes[9],7);
            WeatherDirector.Publish(1,0,1,.66f,1,Sky.Rain);
            Assert.AreEqual(1,Shader.GetGlobalFloat("_EnvironmentWetness"));
            WeatherDirector.Reset();EnvironmentLook.Golf(null,1);
            Assert.IsFalse(EnvironmentLook.Active);
            Assert.AreEqual(0,Shader.GetGlobalFloat("_EnvironmentDepthEnabled"));
            Assert.AreEqual(0,Shader.GetGlobalFloat("_EnvironmentWetness"));
            Assert.AreEqual(0,WeatherDirector.Mist);
        }
        [Test] public void WeatherConsumesBlendedAmountsAndPreservesBiomeDeposition()
        {
            SetStage("5");EnvironmentLook.Golf(GolfAtmosphere.Holes[9],17);
            WeatherDirector.Publish(.4f,.3f,.25f,.54f*.6f,.2f,Sky.Snow);
            Assert.That(WeatherDirector.Storm,Is.EqualTo(.5f).Within(.001));
            Assert.AreEqual(.25f,WeatherDirector.Precipitation);
            Assert.AreEqual(.2f,WeatherDirector.Mist);
            Assert.AreEqual(.3f,Shader.GetGlobalFloat("_EnvironmentSnow"));
            WeatherDirector.Publish(.4f,.3f,.25f,.54f,.2f,Sky.Ash);
            Assert.AreEqual(0,Shader.GetGlobalFloat("_EnvironmentSnow"));
            WeatherDirector.Reset();
            Assert.AreEqual(0,Shader.GetGlobalFloat("_EnvironmentWeatherEnabled"));
        }
        [TestCase("M_Ground")][TestCase("M_Foliage")][TestCase("M_Prop")]
        [TestCase("M_Water")][TestCase("M_Emissive")][TestCase("M_Sky")]
        public void MasterMigrationPreservesEveryShaderDefault(string family)
        {
            SetStage("3");
            var master=Resources.Load<Material>("Environment/Materials/"+family);
            Assert.IsNotNull(master);Assert.AreEqual(family,EnvironmentMaterials.Family(master.shader.name));
            var original=new Material(master.shader);var migrated=EnvironmentMaterials.Create(master.shader);
            try {
                Assert.AreEqual(original.shader,migrated.shader);
                Assert.AreEqual(original.renderQueue,migrated.renderQueue);
                Assert.AreEqual(original.passCount,migrated.passCount);
                CollectionAssert.AreEquivalent(original.shaderKeywords,migrated.shaderKeywords);
                for(int i=0;i<master.shader.GetPropertyCount();i++) {
                    string property=master.shader.GetPropertyName(i);
                    switch(master.shader.GetPropertyType(i)) {
                        case UnityEngine.Rendering.ShaderPropertyType.Color:Assert.AreEqual(original.GetColor(property),migrated.GetColor(property),property);break;
                        case UnityEngine.Rendering.ShaderPropertyType.Vector:Assert.AreEqual(original.GetVector(property),migrated.GetVector(property),property);break;
                        case UnityEngine.Rendering.ShaderPropertyType.Float:
                        case UnityEngine.Rendering.ShaderPropertyType.Range:Assert.AreEqual(original.GetFloat(property),migrated.GetFloat(property),property);break;
                        case UnityEngine.Rendering.ShaderPropertyType.Texture:Assert.AreEqual(original.GetTexture(property),migrated.GetTexture(property),property);break;
                    }
                }
            } finally { UnityEngine.Object.DestroyImmediate(original);UnityEngine.Object.DestroyImmediate(migrated); }
        }
        [Test] public void EveryMoodCarriesBoundedHeroSettings()
        {
            foreach(LightingMood mood in Enum.GetValues(typeof(LightingMood))) {
                var p=LightingPreset.For(mood);
                Assert.That(p.HeroRim,Is.InRange(0,.35f));
                Assert.That(p.HeroAmbientMin,Is.GreaterThanOrEqualTo(.12f));
                Assert.That(p.HeroAmbientMax,Is.GreaterThan(p.HeroAmbientMin));
                Assert.That(p.FogFar,Is.GreaterThan(p.FogNear));
            }
        }
        [Test] public void ActivePresetUsesTheUserSelectedAcesMapper()
        {
            SetStage("4");EnvironmentLook.Golf(GolfAtmosphere.Holes[9],7);
            var profile=ScriptableObject.CreateInstance<UnityEngine.Rendering.VolumeProfile>();
            string previous=System.Environment.GetEnvironmentVariable("VISUAL_TONEMAPPER");
            try {
                System.Environment.SetEnvironmentVariable("VISUAL_TONEMAPPER",null);
                var tone=profile.Add<UnityEngine.Rendering.Universal.Tonemapping>();
                tone.mode.Override(UnityEngine.Rendering.Universal.TonemappingMode.Neutral);
                EnvironmentLook.Post(profile);
                Assert.AreEqual(UnityEngine.Rendering.Universal.TonemappingMode.ACES,tone.mode.value);
            } finally {
                System.Environment.SetEnvironmentVariable("VISUAL_TONEMAPPER",previous);
                foreach(var component in profile.components)UnityEngine.Object.DestroyImmediate(component);
                UnityEngine.Object.DestroyImmediate(profile);
            }
        }
        [Test] public void HubKeepsPaintedSkyOutsideLinearWorldFog()
        {
            SetStage("4");
            EnvironmentLook.Hub(null);
            Assert.IsTrue(EnvironmentLook.Active);
            Assert.AreEqual(LightingMood.Golden,EnvironmentLook.Current.Mood);
            Assert.IsFalse(RenderSettings.fog,"The Unlit sky dome must retain its painted clouds");
            Assert.AreEqual(1,Shader.GetGlobalFloat("_EnvironmentDepthEnabled"),"Scenery retains layered haze");
        }
    }
}
