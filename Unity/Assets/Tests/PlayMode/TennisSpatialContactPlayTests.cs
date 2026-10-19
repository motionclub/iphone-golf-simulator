using System.Collections;
using System.Reflection;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
namespace GolfArcade.PlayTests {
 public class TennisSpatialContactPlayTests {
  const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
  [UnityTest, Timeout(180000)] public IEnumerator RallyResolutionGradesSpacingAndAimsWithTiming() {
   yield return SceneManager.LoadSceneAsync("Tennis"); yield return null;
   var game=Object.FindFirstObjectByType<TennisGame>(); game.ManualSimulation=true;
   var resolve=typeof(TennisGame).GetMethod("ReturnBall",Private);
   var lateness=typeof(TennisGame).GetField("hitLateness",Private);
   foreach(float late in new[]{-.24f,0,.24f}) foreach(float spacing in new[]{0f,.65f,1.7f}) {
    game.ConfigureMatch(TennisGame.Mode.Training,null,null,null);
    game.Player.CancelSwing(); game.Player.Tick(2,0);
    game.Player.transform.position=new Vector3(0,.035f,-11.2f);
    game.Player.Swing(.65f,false,TennisActor.Stroke.Drive); game.Player.Tick(.18f,0); game.Player.Pose();
    var face=TennisRules.PositionFace(new Vector3(spacing,1.1f,.65f),Vector3.zero);
    var hit=TennisRules.AssistedHit(late,1-TennisRules.FaceError(face),1,.65f,1);
    var point=game.Player.StringPoint(face);
    game.InjectBall(point,Vector3.back*12); lateness.SetValue(game,late);
    resolve.Invoke(game,new object[]{hit,face});
    Assert.AreEqual(TennisRules.Grade(hit.Quality),game.LastGrade);
    Assert.AreEqual(face,game.LastFaceOffset); Assert.AreEqual(hit.Speed,game.LastHit.Speed);
    Assert.That(Vector3.Distance(game.BallPosition,point),Is.LessThan(.13f));
    Assert.IsTrue(TennisBall.Landing(game.BallPosition,game.BallVelocity,game.BallSpin,out var landing,out _));
    Assert.IsTrue(TennisRules.BounceIsIn(landing));
    if(late<0) Assert.Less(landing.x,-3); else if(late>0) Assert.Greater(landing.x,3); else Assert.Less(Mathf.Abs(landing.x),.65f);
    Assert.AreEqual(spacing==.65f,game.LastGrade==Timing.Perfect);
    yield return null;
   }
  }
 }
}
