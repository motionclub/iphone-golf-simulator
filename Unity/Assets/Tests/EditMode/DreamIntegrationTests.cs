using System;
using System.IO;
using System.Reflection;
using GolfArcade.Course;
using GolfArcade.EnvironmentArt;
using GolfArcade.Multiplayer;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
namespace GolfArcade.Tests
{
    public sealed class DreamIntegrationTests
    {
        [Test] public void CurrentReboundStillHitsLaterMovingRockDeterministically()
        {
            var movers=new CourseMovers(new[]{
                Mover.Dream(CoursePoint.Zero,20,12,0,3,0,true,new CoursePoint(0,100),1.23,12,.2),
                Mover.Dream(new CoursePoint(0,10),23,12,0,3,0)});
            var hit=new CourseMovers.Hit(0,0,0,0,20,0,0,0,30);
            var a=CourseShot.FallFromMover(hit,movers,Array.Empty<Obstacle>(),_=>0);
            var b=CourseShot.FallFromMover(hit,movers,Array.Empty<Obstacle>(),_=>0);
            Assert.AreEqual(2,a.Knocks.Count,"The current must not disable subsequent rock collision.");
            Assert.AreEqual(a.Time,b.Time);Assert.AreEqual(a.Landing.X,b.Landing.X);Assert.AreEqual(a.Landing.D,b.Landing.D);
        }
        [Test] public void CraterEffectsCannotBurnALiveRallyOrBallOnCourt()
        {
            var prior=TennisVenue.Selected;try {TennisVenue.Selected=TennisVenueKind.Volcano;
                Assert.IsFalse(TennisConditions.CraterOutIsCosmetic(TennisVenueKind.Volcano,new Vector3(30,0,30),false));
                Assert.IsFalse(TennisConditions.CraterOutIsCosmetic(TennisVenueKind.Volcano,new Vector3(0,0,10),true));
                Assert.IsTrue(TennisConditions.CraterOutIsCosmetic(TennisVenueKind.Volcano,new Vector3(30,0,30),true));
                Assert.IsFalse(TennisConditions.CraterOutIsCosmetic(TennisVenueKind.Resort,new Vector3(30,0,30),true));
            }finally{TennisVenue.Selected=prior;}
        }
        [Test] public void OfflineResumeCorrectionWaitsForBoundaryAndCannotReplaceHostTime()
        {
            var old=DreamEnvironment.Snapshot();var forced=System.Environment.GetEnvironmentVariable("DREAM_UTC");
            try {
                System.Environment.SetEnvironmentVariable("DREAM_UTC",null);
                DreamEnvironment.RestoreSession(JsonUtility.ToJson(new EnvironmentSnapshot{seed=99,utcAnchor=100000,elapsed=0}));
                DreamEnvironment.QueueOfflineClockCorrection(200000);Assert.Less(DreamEnvironment.Utc,100010);
                DreamEnvironment.CommitClockBoundary();Assert.That(DreamEnvironment.Utc,Is.InRange(200000,200010));
                DreamEnvironment.StartSession(99,300000);DreamEnvironment.QueueOfflineClockCorrection(400000);DreamEnvironment.CommitClockBoundary();
                Assert.That(DreamEnvironment.Utc,Is.InRange(300000,300010));
            }finally{if(!string.IsNullOrEmpty(old))DreamEnvironment.RestoreSession(old);System.Environment.SetEnvironmentVariable("DREAM_UTC",forced);}
        }
        [Test] public void NativeForecastMatchesAll16000GoldenDraws()
        {
            var rows=File.ReadAllLines(Path.Combine(Application.dataPath,"Tests/EditMode/Fixtures/DreamWeatherV5.csv"));
            Assert.AreEqual(1000,rows.Length);
            for(int seed=0;seed<rows.Length;seed++){
                var values=rows[seed].Split(',');Assert.AreEqual(16,values.Length);
                for(int hole=0;hole<16;hole++)Assert.AreEqual(int.Parse(values[hole]),(int)DreamConditions.WeatherFor(seed,hole),$"seed={seed},hole={hole}");
            }
        }
        [Test] public void EnvironmentResumeRestoresAnchorSeedAndHazardsAndRejectsLegacyVersion()
        {
            var old=DreamEnvironment.Snapshot();var forced=System.Environment.GetEnvironmentVariable("DREAM_UTC");
            try {
                System.Environment.SetEnvironmentVariable("DREAM_UTC",null);
                var state=new EnvironmentSnapshot{seed=77,utcAnchor=1792083600,elapsed=41,location=22,epoch=2,weather=(int)Weather.Storm,hazards="v5-22-BasaltGate@2.3"};
                Assert.IsTrue(DreamEnvironment.RestoreSession(JsonUtility.ToJson(state)));
                Assert.AreEqual(77,DreamEnvironment.Session.seed);Assert.AreEqual(state.hazards,DreamEnvironment.Session.hazards);
                Assert.That(DreamEnvironment.Utc,Is.InRange(state.utcAnchor+41,state.utcAnchor+42));
                var rejoin=JsonUtility.FromJson<EnvironmentSnapshot>(DreamEnvironment.Snapshot());Assert.AreEqual(2,rejoin.epoch);
                state.version=4;Assert.IsFalse(DreamEnvironment.RestoreSession(JsonUtility.ToJson(state)));
                DreamEnvironment.ReplayAt(1792083000);Assert.AreEqual(1792083000,DreamEnvironment.Utc);DreamEnvironment.ReplayAt(null);
            } finally {if(!string.IsNullOrEmpty(old))DreamEnvironment.RestoreSession(old);DreamEnvironment.ReplayAt(null);System.Environment.SetEnvironmentVariable("DREAM_UTC",forced);}
        }
        [Test] public void TennisPhysicsAndSolverRemainSymmetricInEveryCondition()
        {
            var active=typeof(TennisConditions).GetProperty("Active");var weather=typeof(TennisConditions).GetProperty("Weather");
            bool prior=TennisConditions.Active;var previous=TennisConditions.Weather;
            try {
                active.SetValue(null,true);
                foreach(Weather condition in Enum.GetValues(typeof(Weather))){
                    weather.SetValue(null,condition);
                    var start=new Vector3(1,2,-10);var target=new Vector3(-2,TennisRules.BallRadius,9);
                    var velocity=TennisBall.Solve(start,target,23,.5f);var mirror=new Vector3(-velocity.x,velocity.y,-velocity.z);
                    var a=TennisBall.Acceleration(velocity,.5f);var b=TennisBall.Acceleration(mirror,.5f);
                    Assert.AreEqual(a.x,-b.x);Assert.AreEqual(a.y,b.y);Assert.AreEqual(a.z,-b.z);
                    Assert.IsTrue(TennisBall.Landing(start,velocity,.5f,out var land,out _));Assert.Less(Vector3.Distance(land,target),.08f,condition.ToString());
                    float spin=.5f,other=.5f;TennisBall.Bounce(ref velocity,ref spin,.75f);TennisBall.Bounce(ref mirror,ref other,.75f);
                    Assert.AreEqual(velocity.x,-mirror.x);Assert.AreEqual(velocity.y,mirror.y);Assert.AreEqual(velocity.z,-mirror.z);
                }
            }finally {active.SetValue(null,prior);weather.SetValue(null,previous);}
        }
        [Test] public void TennisHostChangesConditionsOnlyAtGameBoundaryAndRejoinUsesSameEpoch()
        {
            var begin=typeof(NetworkTennisMatch).GetMethod("BeginPoint",BindingFlags.Instance|BindingFlags.NonPublic);
            for(int venue=0;venue<3;venue++)for(int seed=0;seed<50;seed++){
                var round=new NetworkTennisMatch(seed:seed,venue:venue);var first=round.Condition;
                for(int point=0;point<3;point++){
                    round.State.score.AwardPoint(true);begin.Invoke(round,null);Assert.AreEqual(first,round.Condition);
                }
                round.State.score.AwardPoint(true);Assert.AreEqual(first,round.Condition,"scoring cannot change the just-ended rally's condition");
                begin.Invoke(round,null);Assert.AreEqual(TennisConditions.For(seed,TennisConditions.Epoch(round.State.score),venue),round.Condition);
                var restored=NetworkTennisWire.Read(JsonUtility.ToJson(NetworkTennisWire.From(round.State)));
                Assert.AreEqual(round.Condition,TennisConditions.For(seed,TennisConditions.Epoch(restored.score),venue));
            }
        }
    }
}
