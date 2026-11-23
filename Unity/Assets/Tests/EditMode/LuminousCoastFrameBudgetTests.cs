using GolfArcade.Game;
using NUnit.Framework;
namespace GolfArcade.Tests {
 /// FramePace's policy (every frame governor: tennis, bowling, golf, the Luminous Coast pilot).
 public class LuminousCoastFrameBudgetTests {
  static FrameWindowResult W(int rate,int frames,int late,int heavy=0,bool timing=false)=>new FrameWindowResult{DrawRate=rate,Frames=frames,Late=late,Heavy=heavy,TimingKnown=timing,Seconds=2};
  [Test] public void OneBadWindowNeverActs() {
   var p=new PacePolicy();Assert.AreEqual(PacePolicy.Decision.Hold,p.Observe(W(60,110,30),false));
   Assert.AreEqual(PacePolicy.Decision.Hold,p.Observe(W(60,120,0),false));Assert.AreEqual(PacePolicy.Decision.Hold,p.Observe(W(60,110,30),false));
  }
  [Test] public void TwoPercentInTwoWindowsInARowStepsThePictureDown() {
   var p=new PacePolicy();Assert.AreEqual(PacePolicy.Decision.Hold,p.Observe(W(60,120,3),false));
   Assert.AreEqual(PacePolicy.Decision.StepDown,p.Observe(W(60,120,3),false));
   Assert.AreEqual(PacePolicy.Decision.Hold,p.Observe(W(60,120,3),false),"the count starts again after acting");
  }
  [Test] public void UnderTwoPercentIsHeld() {
   var p=new PacePolicy();for(int i=0;i<5;i++)Assert.AreEqual(PacePolicy.Decision.Hold,p.Observe(W(60,120,2),false));
  }
  [Test] public void ProMotionFallsToSixtyBeforeThePictureSteps() {
   var p=new PacePolicy();p.Observe(W(120,240,30),false);
   Assert.AreEqual(PacePolicy.Decision.DropRate,p.Observe(W(120,240,30),false));
   p.Observe(W(60,120,20),false);Assert.AreEqual(PacePolicy.Decision.StepDown,p.Observe(W(60,120,20),false));
  }
  [Test] public void OnATvLateFramesThatWereNotHeavyAreAirPlaysNotOurs() {
   var p=new PacePolicy();
   for(int i=0;i<4;i++)Assert.AreEqual(PacePolicy.Decision.Hold,p.Observe(W(60,120,10,0,true),true));
   Assert.AreEqual(4,p.Stalls);
   p.Observe(W(60,120,10,6,true),true);Assert.AreEqual(PacePolicy.Decision.StepDown,p.Observe(W(60,120,10,6,true),true));
  }
  [Test] public void ATvWithoutFrameTimingsKeepsTheTenPercentRule() {
   Assert.IsFalse(PacePolicy.Bad(W(60,120,11),true));Assert.IsTrue(PacePolicy.Bad(W(60,120,12),true));
   Assert.IsTrue(PacePolicy.Bad(W(60,120,3),false),"the phone's own screen: 2 %");
  }
  [Test] public void NoFramesAndResetDiscardPartialWindows() {
   var p=new PacePolicy();p.Observe(W(60,120,30),false);
   Assert.AreEqual(PacePolicy.Decision.Hold,p.Observe(W(60,0,0),false));p.Observe(W(60,120,30),false);p.Reset();
   Assert.AreEqual(PacePolicy.Decision.Hold,p.Observe(W(60,120,30),false));
  }
 }
}
