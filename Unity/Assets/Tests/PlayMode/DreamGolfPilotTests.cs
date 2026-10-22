using System;
using System.Collections;
using System.Linq;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.EnvironmentArt;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object=UnityEngine.Object;
namespace GolfArcade.PlayTests {
 public class DreamGolfPilotTests {
  [UnityTest,Timeout(120000)]
  public IEnumerator DressingPreservesPhysicsAndBallReadabilityAndLeavesWithTheHole() {
   string old=Environment.GetEnvironmentVariable("LUMINOUS_COAST");
   try {
    Environment.SetEnvironmentVariable("LUMINOUS_COAST","0");
    yield return SceneManager.LoadSceneAsync("Golf");
    var game=Object.FindFirstObjectByType<GolfGame>();game.ChooseHoles(0);game.Play();game.JumpToHole(12);
    yield return null;yield return null;yield return null;
    var baseline=HoleView.Current.GetComponentsInChildren<MeshCollider>().ToDictionary(c=>c.name,c=>(c.sharedMesh,c.transform.localToWorldMatrix,c.enabled));
    var obstacles=game.CurrentHole.Obstacles.ToArray();
    Environment.SetEnvironmentVariable("LUMINOUS_COAST","1");game.JumpToHole(12);
    yield return null;yield return null;yield return null;
    var garden=Object.FindFirstObjectByType<DreamGolfGarden>();Assert.IsNotNull(garden);
    Assert.AreEqual(0,garden.GetComponentsInChildren<Collider>(true).Length);
    var current=HoleView.Current.GetComponentsInChildren<MeshCollider>();Assert.AreEqual(baseline.Count,current.Length);
    foreach(var c in current)Assert.AreEqual(baseline[c.name],(c.sharedMesh,c.transform.localToWorldMatrix,c.enabled),c.name);
    CollectionAssert.AreEqual(obstacles,game.CurrentHole.Obstacles);
    var rig=Object.FindFirstObjectByType<CameraRig>();rig.enabled=false;game.enabled=false;
    var hole=game.CurrentHole;var ball=HoleView.ToWorld(hole.Tee,.06);var aim=HoleView.ToWorld(hole.Pin)-ball;
    // Match BigScreen.PhoneFov after leaving the menu/showcase lens.
    rig.RestoreFov();rig.ResetZoom();rig.Camera.fieldOfView=60;
    rig.Camera.aspect=9f/16;rig.FrameAddress(ball,aim,false);rig.SnapNext();rig.ApplyFrame();
    var p=rig.Camera.WorldToViewportPoint(ball);
    Assert.That(p.z,Is.GreaterThan(0));Assert.That(p.x,Is.InRange(.35f,.65f));Assert.That(p.y,Is.InRange(.20f,.42f),"ball must clear the bottom controls");
    // Native landscape retains the prior camera composition.
    rig.Camera.aspect=16f/9;rig.FrameAddress(ball,aim,false);rig.SnapNext();rig.ApplyFrame();var position=rig.transform.position;
    Environment.SetEnvironmentVariable("LUMINOUS_COAST","0");rig.FrameAddress(ball,aim,false);rig.SnapNext();rig.ApplyFrame();Assert.That(Vector3.Distance(position,rig.transform.position),Is.LessThan(.001f));
    Environment.SetEnvironmentVariable("LUMINOUS_COAST","1");game.enabled=true;game.JumpToHole(7);
    yield return null;yield return null;yield return null;
    Assert.IsNull(Object.FindFirstObjectByType<DreamGolfGarden>());Assert.IsNull(Object.FindFirstObjectByType<LuminousCoastPilot>());
   } finally {Environment.SetEnvironmentVariable("LUMINOUS_COAST",old);}
  }
 }
}
