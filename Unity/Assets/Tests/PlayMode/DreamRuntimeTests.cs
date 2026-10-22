using System;
using System.Collections;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Tennis;
using GolfArcade.EnvironmentArt;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object=UnityEngine.Object;
namespace GolfArcade.PlayTests
{
    public sealed class DreamRuntimeTests
    {
        [UnityTest,Timeout(300000)]
        public IEnumerator GolfFogAndNightReleaseCleanlyWhenSwitchingToTennis()
        {
            bool priorEvents=RoundEvents.Enabled;RoundEvents.Enabled=true;
            var priorWeather=Environment.GetEnvironmentVariable("DREAM_WEATHER");var priorTime=Environment.GetEnvironmentVariable("DREAM_UTC");
            try {
                Environment.SetEnvironmentVariable("DREAM_WEATHER","Fog");Environment.SetEnvironmentVariable("DREAM_UTC","1792119600");
                yield return SceneManager.LoadSceneAsync("Golf");
                var game=Object.FindFirstObjectByType<GolfGame>();game.ChooseHoles(0);game.Play();game.JumpToHole(7);game.DropBall(game.CurrentHole.Tee);
                for(int i=0;i<20;i++)yield return null;
                Assert.AreEqual(1,Object.FindObjectsByType<DreamEnvironment>(FindObjectsSortMode.None).Length);
                Assert.AreEqual(Weather.Fog,DreamEnvironment.Current.Condition);Assert.IsTrue(DreamVisibility.Fog);
                Assert.Greater(Object.FindObjectsByType<DreamMapFog>(FindObjectsSortMode.None).Length,0,"The live HUD must install its observation mask.");
                var before=game.CurrentHole.Dream.Code;game.JumpToHole(7);for(int i=0;i<3;i++)yield return null;
                Assert.AreEqual(before,game.CurrentHole.Dream.Code,"retry retains hazard selection and phase");
                Environment.SetEnvironmentVariable("DREAM_WEATHER","Storm");TennisVenue.Selected=TennisVenueKind.Volcano;
                yield return SceneManager.LoadSceneAsync("Tennis");
                TennisGame tennis=null;
                for(int i=0;i<600;i++){tennis=Object.FindFirstObjectByType<TennisGame>();if(tennis&&tennis.Initialized)break;yield return null;}
                Assert.IsNotNull(tennis);Assert.IsTrue(tennis.Initialized);for(int i=0;i<10;i++)yield return null;
                Assert.AreEqual(1,Object.FindObjectsByType<DreamEnvironment>(FindObjectsSortMode.None).Length);
                Assert.AreEqual(Weather.Storm,DreamEnvironment.Current.Condition);Assert.IsFalse(DreamVisibility.Fog);
                Assert.IsTrue(TennisConditions.Active);Assert.AreEqual(0,Shader.GetGlobalFloat("_DreamGolf"));
                Assert.GreaterOrEqual(RenderSettings.fogStartDistance,40,"Both court ends must remain inside the clear sporting envelope.");
                Assert.AreEqual(102,DreamEnvironment.Session.location);
            }finally {RoundEvents.Enabled=priorEvents;Environment.SetEnvironmentVariable("DREAM_WEATHER",priorWeather);Environment.SetEnvironmentVariable("DREAM_UTC",priorTime);}
        }
    }
}
