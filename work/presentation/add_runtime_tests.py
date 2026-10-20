from pathlib import Path
import uuid
p=Path('Unity/Assets/Tests/PlayMode/PresentationFlowTests.cs');p.write_text('''using System.Collections;
using System.IO;
using GolfArcade.Game;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object=UnityEngine.Object;
namespace GolfArcade.PlayTests {
    public class PresentationFlowTests {
        [UnityTest,Timeout(120000)] public IEnumerator TennisOffSettlesWithoutStartingASwing() {
            Time.timeScale=1; Time.captureFramerate=60;
            PresentationPolicy.Configure("off",false,true,false);
            yield return SceneManager.LoadSceneAsync("Tennis");
            var game=Object.FindFirstObjectByType<TennisGame>();
            for(int i=0;i<120 && !game.Initialized;i++)yield return null;
            game.NativeControlled=true;game.AutoPlay=false;game.ManualSimulation=false;
            for(int i=0;i<52 && game.IntroPlaying;i++)yield return null;
            Assert.False(game.IntroPlaying,"Off must release within the 0.8 second settle plus a frame");
            Assert.False(game.Player.Swinging,"Skipping/settling cannot strike a serve");
            Assert.That(game.Flow,Is.EqualTo(TennisGame.Phase.PlayerServeHold));
            Time.captureFramerate=0; PresentationPolicy.Configure("full",false,true,false);
        }
        [UnityTest,Timeout(120000)] public IEnumerator GolfOverviewPreservesTheExactShotAndReturnsToAddress() {
            Time.timeScale=1; Time.captureFramerate=60;
            PresentationPolicy.Configure("off",false,true,false);
            yield return SceneManager.LoadSceneAsync("Golf");
            var game=Object.FindFirstObjectByType<GolfGame>(); yield return null;
            game.PrepareNativeAddress(); game.NativeReady(); game.TryNativePresentation();
            for(int i=0;i<45 && game.PresentationBusy;i++)yield return null;
            Assert.That(game.Current,Is.EqualTo(GolfGame.State.Aim));
            var ball=game.BallPosition; double heading=game.TutorialHeading; int hole=game.TutorialHole;
            game.Overview(); Assert.True(game.PresentationBusy);
            for(int i=0;i<250 && game.PresentationBusy;i++)yield return null;
            Assert.That(game.Current,Is.EqualTo(GolfGame.State.Aim));
            Assert.That(game.BallPosition,Is.EqualTo(ball)); Assert.AreEqual(heading,game.TutorialHeading); Assert.AreEqual(hole,game.TutorialHole);
            Assert.True(game.Swing.Armed,"The unchanged shot must be armed after Overview");
            Time.captureFramerate=0; PresentationPolicy.Configure("full",false,true,false);
        }
        [UnityTest,Timeout(120000)] public IEnumerator MainCamerasRecordPostPrerequisiteAndRenderedStills() {
            Time.timeScale=1; PresentationPolicy.Configure("short",false,true,false); TennisQuality.Apply();
            string dir="Library/Captures/presentation-prerequisites";Directory.CreateDirectory(dir);
            foreach(string sport in new[]{"Tennis","Golf"}) {
                yield return SceneManager.LoadSceneAsync(sport); yield return null; yield return null;
                var tennis=Object.FindFirstObjectByType<TennisGame>();var golf=Object.FindFirstObjectByType<GolfGame>();
                if(golf){golf.PrepareNativeAddress();golf.NativeReady();}
                Camera camera=tennis?tennis.GameplayCamera:golf.GameplayCamera;
                var data=camera.GetComponent<UnityEngine.Rendering.Universal.UniversalAdditionalCameraData>();
                File.WriteAllText(Path.Combine(dir,sport+"-post.txt"),"post="+(data && data.renderPostProcessing)+" tier="+TennisQuality.Current);
                ScreenCapture.CaptureScreenshot(Path.Combine(dir,sport+".png"));
                yield return new WaitForEndOfFrame(); yield return null;
                Assert.True(camera.enabled,"Acceptance uses the actual gameplay camera");
            }
            PresentationPolicy.Configure("full",false,true,false);
        }
    }
}
''');p.with_suffix('.cs.meta').write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n')
# The prior regression required unbounded animation holds; replace it with the new hard-cap contract.
p=Path('Unity/Assets/Tests/PlayMode/MultiplayerRuntimeTests.cs');s=p.read_text().replace('EquippedIntroAcceptsLateChoiceAndHoldsUntilFinished','EquippedIntroChoiceDoesNotExtendThePresentationBudget')
s=s.replace('            typeof(TennisPresentation).GetField("t",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(presentation,TennisPresentation.Drone+TennisPresentation.RivalIntro+TennisPresentation.PlayerIntro-.005f);','')
s=s.replace('                while(driver.EmoteActive){Assert.True(game.IntroPlaying,"Intro camera waits for the whole chosen clip");yield return null;}','')
s=s.replace('                Assert.False(game.IntroPlaying,"Match proceeds after the selected intro");','                Assert.False(game.IntroPlaying,"A long equipped animation cannot extend the intro cap");')
p.write_text(s)
