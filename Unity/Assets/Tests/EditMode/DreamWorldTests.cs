using System;
using System.Linq;
using GolfArcade.Course;
using GolfArcade.EnvironmentArt;
using GolfArcade.Shot;
using GolfArcade.Swing;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
namespace GolfArcade.Tests
{
    public sealed class DreamWorldTests
    {
        [Test] public void ClockUsesFixedEstAcrossDstAndContinuousBoundaries()
        {
            foreach(var date in new[]{"2026-01-15","2026-07-15","2026-11-01"})
            foreach(double h in new[]{0.0,5,7,16.5,18,19.5,21,24}){
                double utc=DateTimeOffset.Parse(date+"T00:00:00Z").ToUnixTimeSeconds()+(h+5)*3600;
                Assert.AreEqual(h%24,DreamConditions.EstHour(utc),1e-7);
                Assert.Less(Math.Abs(DreamConditions.Daylight(utc+.01)-DreamConditions.Daylight(utc-.01)),.001);
            }
            var clock=new EnvironmentClock(1000,20);Assert.AreEqual(1010,clock.At(30));Assert.AreEqual(1000,clock.At(10));
            clock.Reconcile(2000,40);Assert.AreEqual(2002,clock.At(42));
        }
        [Test] public void WeatherSeedIdentityAndSeverePacingAreStable()
        {
            var counts=new int[5];for(int seed=1;seed<=1000;seed++)for(int hole=0;hole<16;hole++){
                var w=DreamConditions.WeatherFor(seed,hole);counts[(int)w]++;
                Assert.AreEqual(w,DreamConditions.WeatherFor(seed,hole));
                if(w==Weather.Storm){if(hole>0)Assert.AreNotEqual(Weather.Storm,DreamConditions.WeatherFor(seed,hole-1));if(hole>1)Assert.AreNotEqual(Weather.Storm,DreamConditions.WeatherFor(seed,hole-2));}
            }
            Assert.That(counts.All(n=>n>500));
        }
        [Test] public void LegacyWeatherOffCannotDisableNormalRounds()
        {
            bool old=RoundEvents.Enabled;RoundEvents.Enabled=true;try{
                var events=RoundEvents.Deal(42,false,false,false);Assert.IsTrue(events.World);
                Assert.IsTrue(RoundEvents.FromCode(42,"s:").World);
                for(int h=0;h<16;h++)for(int stroke=0;stroke<20;stroke++)Assert.IsNull(events.TurnBefore(h,stroke,events.WeatherFor(h)));
            }finally{RoundEvents.Enabled=old;}
        }
        [Test] public void EveryHoleHasAProtectedAuthoredSocketFor1000Seeds()
        {
            foreach(var course in GolfArcade.Course.Course.All())foreach(var hole in course.Holes)for(int seed=0;seed<1000;seed++){
                var w=DreamConditions.WeatherFor(seed,hole.Number);var layout=DreamCourseLayout.Build(hole,seed,w);
                Assert.AreEqual(layout.Code,DreamCourseLayout.Build(hole,seed,w).Code);
                if(hole.Par==3){Assert.GreaterOrEqual(layout.ShortcutTarget.DistanceTo(hole.Pin),2);Assert.AreEqual(0,hole.LieAt(layout.ShortcutTarget).PenaltyStrokes());}
                foreach(var h in layout.Hazards){
                    Assert.GreaterOrEqual(DreamCourseLayout.CorridorDistance(h.Centre,hole.Centerline),h.Radius+h.Motion+8);
                    Assert.Greater(h.Centre.DistanceTo(hole.Tee),35);Assert.Greater(h.Centre.DistanceTo(hole.Pin),35);
                    Assert.IsTrue(h.RecoverySafe(hole.Tee));
                    if(w==Weather.Fog||w==Weather.Storm)Assert.AreNotEqual(DreamHazardKind.LavaVent,h.Kind);
                    Assert.That(h.Kind,Is.EqualTo(DreamHazardKind.LavaVent).Or.EqualTo(DreamHazardKind.IceRunway),$"hole {hole.Number}: no boost gate or lift (10-27)");
                }
            }
        }
        [Test] public void FogVisibilityIsIndependentOfCameraAndQuality()
        {
            foreach(double elevation in new[]{-20.0,0,80,200}){
                Assert.AreEqual(1,DreamConditions.Visibility(0,elevation,10,0,elevation,0),1e-6);
                Assert.Less(DreamConditions.Visibility(0,elevation,60,0,elevation,0),.24);
                Assert.Less(DreamConditions.Visibility(0,elevation,120,0,elevation,0),.04);
            }
            DreamVisibility.Set(true,new Vector3(0,120,0));Assert.IsFalse(DreamVisibility.Visible(new Vector3(0,120,100)));DreamVisibility.Reset();
        }
        [Test] public void WetSnowAndAshChangeMeasuredShotsDifferently()
        {
            var h=new Hole{Number=99,Par=4,Centerline=new[]{CoursePoint.Zero,new CoursePoint(0,400)},FairwayWidth=200,RoughWidth=100};
            var dry=new CourseShot(GolfClub.Iron,new SwingImpact{Power=.8},0,h.Tee,h);
            double[] rolls=new double[3];int i=0;foreach(var sky in new[]{Sky.Rain,Sky.Snow,Sky.Ash}){
                h.Rules=new PlayRules();Weather.Rain.Bend(h.Rules,sky);var wet=new CourseShot(GolfClub.Iron,new SwingImpact{Power=.8},0,h.Tee,h);rolls[i++]=wet.Roll;Assert.Less(wet.Roll,dry.Roll);
            }Assert.AreEqual(3,rolls.Distinct().Count());
        }
        [Test] public void VentWarnsThenBurnsOnceWithSafeRecoveryAndRepeatableImpact()
        {
            var vent=new DreamHazard{Id="test",Kind=DreamHazardKind.LavaVent,Centre=new CoursePoint(0,30),Height=0,Radius=5};
            Assert.AreEqual(VentStage.Warning,vent.Stage(7));Assert.AreEqual(VentStage.Active,vent.Stage(9.5));Assert.AreEqual(VentStage.Cooling,vent.Stage(11));
            var h=new Hole{Number=99,Centerline=new[]{CoursePoint.Zero,new CoursePoint(0,100)},FairwayWidth=100,RoughWidth=50,Ground=_=>0,Movers=new CourseMovers(Array.Empty<Mover>())};
            h.Dream=new DreamCourseLayout(new[]{vent},h.Centerline,h.Pin,"Test");
            CourseShot burned=null;
            for(int phase=0;phase<24;phase++){vent.Phase=phase*.5;var shot=new CourseShot(GolfClub.Iron,new SwingImpact{Power=1},0,h.Tee,h);if(shot.Burned){burned=shot;break;}}
            Assert.NotNull(burned,"test trajectory must cross active plume");Assert.AreEqual(1,burned.PenaltyStrokes);Assert.IsFalse(burned.IsHoled);Assert.IsTrue(vent.RecoverySafe(burned.NextPosition));
            var replay=new CourseShot(GolfClub.Iron,new SwingImpact{Power=1},0,h.Tee,h);Assert.AreEqual(burned.BurnTime,replay.BurnTime);Assert.AreEqual(burned.Rest.D,replay.Rest.D);
            var waiting=new CourseShot(GolfClub.Putter,new SwingImpact{Power=0},0,vent.Centre,h);Assert.IsFalse(waiting.Burned);
        }
        [Test] public void TennisEndSwapKeepsIdenticalAccelerationAndBounce()
        {
            var v=new Vector3(3,4,25);var opposite=new Vector3(-v.x,v.y,-v.z);var a=TennisBall.Acceleration(v,.5f);var b=TennisBall.Acceleration(opposite,.5f);
            Assert.AreEqual(a.y,b.y);Assert.AreEqual(a.x,-b.x);Assert.AreEqual(a.z,-b.z);
            float spin=.5f,other=.5f;TennisBall.Bounce(ref v,ref spin,.75f);TennisBall.Bounce(ref opposite,ref other,.75f);Assert.AreEqual(v.z,-opposite.z);Assert.AreEqual(v.y,opposite.y);
        }
    }
}
