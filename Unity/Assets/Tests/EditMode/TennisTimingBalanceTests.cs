using GolfArcade.Tennis;
using GolfArcade.Multiplayer;
using NUnit.Framework;
using UnityEngine;

namespace GolfArcade.Tests {
 public class TennisTimingBalanceTests {
  [Test] public void WiderContactStillNeedsASwingWithinReach() {
   foreach(float side in new[]{-1f,1f}) {
    Vector3 b=new Vector3(side*1.72f,1.1f,.65f);
    Assert.IsTrue(TennisRules.AssistedContact(b,b,Vector3.zero,.025f,false,out _));
    Assert.IsTrue(TennisRules.AssistedContact(b,b,Vector3.zero,.48f,false,out _));
    Assert.IsFalse(TennisRules.AssistedContact(b,b,Vector3.zero,0,false,out _));
    Assert.IsFalse(TennisRules.AssistedContact(b,b,Vector3.zero,.55f,false,out _));
    b.x=side*2.5f;
    Assert.IsFalse(TennisRules.AssistedContact(b,b,Vector3.zero,.18f,false,out _));
   }
  }
  [Test] public void CenteredContactWinsPaceAndPlacementWithoutUnreturnableStreakSpeed() {
   var clean=TennisRules.AssistedHit(.02f,1,1,.2f,1);
   var scrappy=TennisRules.AssistedHit(.25f,.2f,1,1,1);
   Assert.Greater(clean.Speed,scrappy.Speed*1.4f);
   Assert.LessOrEqual(TennisRules.Supercharge(TennisRules.Evaluate(.18f,Vector2.zero,1,1,1,1)).Speed,34f);
   foreach(float aim in new[]{-1f,1f}) foreach(float depth in new[]{0f,1f}) {
    var intended=TennisRules.PlacementTarget(aim,depth);
    float cleanError=0,poorError=0;
    foreach(float x in new[]{-1f,0f,1f}) foreach(float z in new[]{-1f,0f,1f}) {
     var precise=TennisRules.TimedPlacement(intended,clean.Quality,x,z);
     var loose=TennisRules.TimedPlacement(intended,scrappy.Quality,x,z);
     cleanError+=Vector3.Distance(intended,precise);poorError+=Vector3.Distance(intended,loose);
     Assert.Less(Vector3.Distance(intended,precise),.08f);
     Assert.IsTrue(TennisRules.BounceIsIn(loose));
    }
    Assert.Greater(poorError,cleanError*5);
   }
  }
  [Test] public void TimingSetsPaceAlikeOnBothSides() {
   // Early and late by the same amount are the same shot; the further off, the slower.
   float previous=TennisRules.AssistedHit(0,.65f,1,.65f,1).Speed;
   for(float late=0;late<.34f;late+=.005f) {
    var a=TennisRules.AssistedHit(late,.65f,1,.65f,1);
    var b=TennisRules.AssistedHit(-late,.65f,1,.65f,1);
    Assert.AreEqual(a.Speed,b.Speed,1e-4f);Assert.LessOrEqual(a.Speed,previous+1e-4f);previous=a.Speed;
    Assert.Greater(a.Timing,0);
   }
  }
  [Test] public void FastestNormalRallyCanBeReachedFromAReadyPosition() {
   foreach(float aim in new[]{-1f,0f,1f}) {
    var start=new Vector3(0,1.1f,-10.5f);
    var target=TennisRules.PlacementTarget(aim,.85f);
    var velocity=TennisRules.RallyVelocity(start,target,34f,.3f,1f);
    var mirroredStart=new Vector3(-start.x,start.y,-start.z);
    var mirroredVelocity=new Vector3(-velocity.x,velocity.y,-velocity.z);
    var plan=TennisRules.PlanIntercept(mirroredStart,mirroredVelocity,.3f,.75f,
     new Vector2(0,TennisRules.BaselineZ),TennisRules.ReactionTime,TennisRules.SprintSpeed,false);
    Assert.IsTrue(plan.Reachable,"a ready receiver must have a reachable return even at the pace cap");
    Assert.Greater(plan.Time,.65f,"retain reaction time across the full court");
   }
  }
  // Landing is returned in the hitter's own frame (x to their right, z away from them), so both seats read alike.
  // `aim` is the hitter's own racket face; seat 1's is flipped into the host's frame as SportsMultiplayer.Submit does.
  static (float speed,Vector2 land,string grade) OnlineShot(int seat,float due,float power,float delay=0,float side=.65f,float aim=0) {
   var match=new NetworkTennisMatch();var s=match.State;var p=s.players[seat];float sign=seat==0?1:-1;
   s.phase="rally";s.receiver=seat;p.x=0;p.target=0;p.aim=aim*sign;p.depth=.8f;
   s.ball=new NetworkVector(side*sign,1.1f,p.z+sign*(.65f+16*due));s.velocity=new NetworkVector(0,1,-16*sign);
   for(int i=0;i<Mathf.RoundToInt(delay*120);i++)match.Step(1.0/120);
   long contact=s.contact;
   Assert.IsTrue(match.Input(seat,new NetworkInput {action="swing",eventID=1,point=s.point,contact=s.contact,time=0,power=power,aim=aim*sign},s.time));
   for(int i=0;i<65&&s.contact==contact;i++)match.Step(1.0/120);
   Assert.Greater(s.contact,contact);
   var b=s.ball;var v=s.velocity;
   float flight=(v.y+Mathf.Sqrt(v.y*v.y+19.62f*(b.y-.034f)))/9.81f;
   var land=new Vector2((b.x+v.x*flight)*sign,(b.z+v.z*flight)*sign);
   return (Mathf.Sqrt(v.x*v.x+v.z*v.z),land,s.reason);
  }
  [Test] public void OnlinePacketDelayDoesNotChangeTheTimingReward() {
   foreach(int seat in new[]{0,1}) foreach(float due in new[]{.18f,-.03f}) {
    var immediate=OnlineShot(seat,due,.65f);
    var delayed=OnlineShot(seat,due,.65f,.1f);
    Assert.AreEqual(immediate.grade,delayed.grade);
    Assert.That(Vector2.Distance(delayed.land,immediate.land),Is.LessThan(.15f));
   }
  }
  [Test] public void OnlineSpacingRewardsBothSeatsEqually() {
   foreach(int seat in new[]{0,1}) {
    var clean=OnlineShot(seat,.18f,.65f);var poor=OnlineShot(seat,-.03f,.65f,side:1.65f);
    Assert.AreEqual("PERFECT!",clean.grade);
    Assert.AreNotEqual("PERFECT!",poor.grade);
    Assert.Greater(clean.speed,poor.speed);
   }
  }
  [Test] public void OnlineSwingAimsAndTimingPowersTheBallForBothSeats() {
   // The racket face sent with the swing picks the side, the same for the seat at either end of the court; the
   // timing picks the pace and depth.
   foreach(int seat in new[]{0,1}) {
    var straight=OnlineShot(seat,.18f,.65f,aim:0);
    Assert.That(Mathf.Abs(straight.land.x),Is.LessThan(.15f),$"seat {seat} a square racket goes straight");
    var right=OnlineShot(seat,.18f,.65f,aim:.8f);
    Assert.Greater(right.land.x,2.5f,$"seat {seat} a face turned right goes to the hitter's right");
    var left=OnlineShot(seat,.18f,.65f,aim:-.8f);
    Assert.Less(left.land.x,-2.5f,$"seat {seat} a face turned left goes to the hitter's left");
    var mistimed=OnlineShot(seat,.03f,.65f,aim:0);   // about .15 s late: in, but slow and short
    Assert.Greater(straight.speed,mistimed.speed,$"seat {seat} on time is faster");
    Assert.Greater(straight.land.y,mistimed.land.y+1f,$"seat {seat} on time is deeper");
    foreach(var shot in new[]{straight,right,left,mistimed}) Assert.IsTrue(TennisRules.BounceIsIn(new Vector3(shot.land.x,TennisRules.BallRadius,shot.land.y)));
    // Past TennisRules.OutTiming it sails out (2026-10-26): long down the middle, wide on a side lane.
    var wayOff=OnlineShot(seat,-.03f,.65f,aim:0);
    Assert.IsFalse(TennisRules.BounceIsIn(new Vector3(wayOff.land.x,TennisRules.BallRadius,wayOff.land.y)),$"seat {seat} way off goes out");
    var wayOffWide=OnlineShot(seat,-.03f,.65f,aim:.8f);
    Assert.Greater(wayOffWide.land.x,TennisRules.CourtHalfWidth,$"seat {seat} way off to the right goes wide right");
   }
  }
 }
}
