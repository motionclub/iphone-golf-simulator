using GolfArcade.EnvironmentArt;
using NUnit.Framework;
namespace GolfArcade.Tests {
 public class LuminousCoastFrameBudgetTests {
  [Test] public void IsolatedLoadingHitchDoesNotReduceTarget() {
   var p=new FrameBudgetPolicy();Assert.AreEqual(60,p.Observe(60,110,30));
   Assert.AreEqual(60,p.Observe(60,120,0));Assert.AreEqual(60,p.Observe(60,110,30));
   Assert.AreEqual(60,p.Observe(60,110,30));
  }
  [Test] public void SixSecondsOfLateWindowsKeepsSixtyAndAsksForLowerQuality() {
   var p=new FrameBudgetPolicy();Assert.AreEqual(60,p.Observe(60,120,12));
   Assert.AreEqual(60,p.Observe(60,120,12));Assert.IsFalse(p.SustainedLate);
   Assert.AreEqual(60,p.Observe(60,120,12));Assert.IsTrue(p.SustainedLate);
  }
  [Test] public void ProMotionFallsToSixtyBeforeThirty() {
   var p=new FrameBudgetPolicy();p.Observe(120,240,30);p.Observe(120,240,30);
   Assert.AreEqual(60,p.Observe(120,240,30));Assert.AreEqual(60,p.Observe(60,120,20));
  }
  [Test] public void NeverDropsBelowSixtyAndNoAutomaticOscillation() {
   var p=new FrameBudgetPolicy();for(int i=0;i<4;i++)Assert.AreEqual(60,p.Observe(60,120,30));
   Assert.IsTrue(p.SustainedLate);Assert.AreEqual(60,p.Observe(60,120,0));Assert.IsFalse(p.SustainedLate);
  }
  [Test] public void NoFramesAndResetDiscardPartialWindows() {
   var p=new FrameBudgetPolicy();p.Observe(60,120,30);p.Observe(60,120,30);
   Assert.AreEqual(60,p.Observe(60,0,0));p.Observe(60,120,30);p.Reset();
   Assert.AreEqual(60,p.Observe(60,120,30));Assert.AreEqual(60,p.Observe(60,120,30));
  }
 }
}
