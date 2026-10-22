using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
namespace GolfArcade.Tests {
 public class TennisSpatialContactTests {
  [Test] public void ComfortableSpacingBeatsCrowdingAndStretchingOnEitherWing() {
   foreach(float wing in new[]{-1f,1f}) {
    float Center(float x,float h=1.1f) => 1-TennisRules.FaceError(TennisRules.PositionFace(new Vector3(x*wing,h,.65f),Vector3.zero));
    Assert.AreEqual(1,Center(.65f)); Assert.AreEqual(1,Center(.45f));
    Assert.Less(Center(0),Center(.25f)); Assert.Less(Center(.25f),Center(.65f));
    Assert.Less(Center(1.7f),Center(1.2f)); Assert.Less(Center(1.2f),Center(.65f));
    Assert.Less(Center(.65f,.3f),Center(.65f)); Assert.Less(Center(.65f,2f),Center(.65f));
   }
  }
  [Test] public void SameSpatialContactHasSameGradeSpeedAndHapticsAcrossAimWindow() {
   foreach(float spacing in new[]{0f,.3f,.65f,1.2f,1.7f}) {
    var face=TennisRules.PositionFace(new Vector3(spacing,1.1f,.65f),Vector3.zero);
    float center=1-TennisRules.FaceError(face);
    var baseline=TennisRules.AssistedHit(0,center,1,.65f,1);
    foreach(float late in new[]{-.3f,-.2f,0,.2f,.3f}) {
     var hit=TennisRules.AssistedHit(late,center,1,.65f,1);
     Assert.AreEqual(baseline.Speed,hit.Speed); Assert.AreEqual(baseline.Quality,hit.Quality);
     var grade=TennisRules.Grade(hit.Quality);
     var feel=TennisHitFeel.Rally(grade,face,late,TennisActor.Stroke.Drive,.65f,0,false,2);
     Assert.AreEqual(center,feel.Center,1e-5f); Assert.AreEqual(0,feel.Mistime);
     var target=TennisRules.TimingPlacement(late,.65f,hit.Quality,0,0);
     Assert.AreEqual(Mathf.Sign(TennisRules.AimFromTiming(late))*Mathf.Abs(target.x),target.x);
     Assert.IsTrue(TennisRules.BounceIsIn(target));
    }
   }
  }
  [Test] public void ForwardStretchAndLateBodyPositionAlsoMoveContactOffCenter() {
   var comfortable=TennisRules.PositionFace(new Vector3(.65f,1.1f,.65f),Vector3.zero);
   Assert.AreEqual(Vector2.zero,comfortable);
   foreach(float z in new[]{-.35f,2.1f})
    Assert.Greater(TennisRules.FaceError(TennisRules.PositionFace(new Vector3(.65f,1.1f,z),Vector3.zero)),.5f);
  }
  [Test] public void OverheadsHaveTheirOwnComfortableZoneAboveTheShoulder() {
   Assert.AreEqual(Vector2.zero,TennisRules.PositionFace(new Vector3(.2f,2.4f,.5f),Vector3.zero,true));
   Assert.Greater(TennisRules.FaceError(TennisRules.PositionFace(new Vector3(1.6f,2.4f,.5f),Vector3.zero,true)),.8f);
  }
  [Test] public void RealFrameContactIsAWeakReturnRatherThanAMiss() {
   var hit=TennisRules.Evaluate(.18f,new Vector2(TennisRules.StringHalfWidth,0),1,1,.65f,1);
   Assert.IsTrue(hit.Contact); Assert.AreEqual(Timing.Ok,TennisRules.Grade(hit.Quality));
   Assert.Less(hit.Speed,16);
  }
  [Test] public void FrameContactsStayPlayableAndGiveUpDepth() {
   foreach(float late in new[]{-.24f,0,.24f}) foreach(float power in new[]{0f,1f}) {
    var clean=TennisRules.TimingPlacement(late,power,1,0,0);
    var poor=TennisRules.TimingPlacement(late,power,.05f,0,0);
    Assert.Less(poor.z,clean.z); Assert.AreEqual(clean.x,poor.x);
    foreach(float height in new[]{.3f,1.1f,2f}) {
     var start=new Vector3(.65f,height,-10.5f);
     var v=TennisRules.RallyVelocity(start,poor,TennisRules.ShotSpeed(.05f,power,1),.35f,.05f);
     Assert.Greater(TennisRules.NetClearance(start,v,.35f),TennisRules.NetHeight+.15f);
     Assert.IsTrue(TennisBall.Landing(start,v,.35f,out var landing,out _));
     Assert.Less(Vector3.Distance(landing,poor),.15f);
    }
   }
  }
 }
}
