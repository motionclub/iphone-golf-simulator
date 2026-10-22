using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Shot;
using GolfArcade.Swing;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
namespace GolfArcade.EditorTools
{
    [InitializeOnLoad] public static class DreamRouteAudit
    {
        const string Key="DreamRouteAudit";static GolfGame game;static int index=-1,frame;static string output;
        static readonly int[] ids=(System.Environment.GetEnvironmentVariable("DREAM_ROUTE_HOLES")??"7,8,9,12,15,13,14,17,18,19,20,10,16,21,22,23").Split(',').Select(int.Parse).ToArray();
        static readonly GolfClub[] clubs={GolfClub.Driver,GolfClub.Hybrid,GolfClub.Iron5,GolfClub.Iron,GolfClub.Iron9,GolfClub.PitchingWedge};
        static DreamRouteAudit(){EditorApplication.update+=Tick;}
        public static void Run(){SessionState.SetBool(Key,true);EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");EditorApplication.isPlaying=true;}
        static void Tick(){
            if(!SessionState.GetBool(Key,false)||!EditorApplication.isPlaying)return;
            try{
                if(!game){game=UnityEngine.Object.FindFirstObjectByType<GolfGame>();if(!game||!HoleView.Current)return;output=Path.GetFullPath("../work/dream-worlds-20261015/proof/routes");Directory.CreateDirectory(output);game.ChooseHoles(0);game.Play();Next();return;}
                if(Time.frameCount-frame<8)return;game.enabled=false;Audit(game.CurrentHole);Next();
            }catch(Exception e){Debug.LogException(e);SessionState.SetBool(Key,false);EditorApplication.Exit(1);}
        }
        static void Next(){index++;if(index>=ids.Length){SessionState.SetBool(Key,false);EditorApplication.Exit(0);return;}game.enabled=true;game.JumpToHole(ids[index]);game.DropBall(game.CurrentHole.Tee);frame=Time.frameCount;}
        static bool Dry(CourseShot shot)=>shot.PenaltyStrokes==0;
        static bool Interacts(CourseShot shot,DreamCourseLayout layout){
            if(shot.Knocks.Any(k=>k.Kind==ObstacleKind.Twister))return true;
            if(layout.Hazards[0].Kind==DreamHazardKind.IceRunway)for(double t=shot.LandingTime;t<shot.Duration;t+=.1){var p=shot.PositionAt(t);if(layout.IceAt(new CoursePoint(p.x,p.d)))return true;}
            return false;
        }
        [Serializable] class Calibration{public int hole,misses;public double gain,lift,score,remaining;}
        [Serializable] class Report{public int hole,configurations,invalidConfigurations,candidateShots,interactions;public string hazard;public bool beneficialRouteFound,conservativeRouteFound;public double benefitYards,remainingWithRoute,remainingWithoutRoute;public double originX,originD,power,heading,phase;public string club,conservativeClub;public double conservativePower,conservativeHeading;public string limitation="Shot outcomes are simulated. Remaining-stroke estimates use an explicit distance model (170/205/240 yd approaches and 2.3/2.0/1.8 putting baseline), not human performance data. Human playtests remain required.";public Sample[] samples;}
        [Serializable] class Sample{public string skill;public int count,penalties,burns,holedOuts,conservativeHoledOuts;public double meanRemaining,meanPenalty,estimatedStrokes,conservativeEstimatedStrokes,conservativeMeanRemaining,conservativeMeanPenalty;}
        static void Audit(Hole hole){
            bool reuse=System.Environment.GetEnvironmentVariable("DREAM_ROUTE_REUSE")=="1";var path=Path.Combine(output,$"hole{hole.Number:00}.json");
            var report=reuse?JsonUtility.FromJson<Report>(File.ReadAllText(path)):new Report{hole=hole.Number};if(reuse&&!report.beneficialRouteFound){reuse=false;report=new Report{hole=hole.Number};}
            var prior=hole.Dream;var movers=hole.Movers;var rules=hole.Rules;
            for(int seed=0;seed<(reuse?0:1000);seed++){
                var layout=DreamCourseLayout.Build(hole,seed,DreamConditions.WeatherFor(seed,hole.Number));report.configurations++;
                if(layout.Hazards.Length==0||layout.Hazards.Any(h=>!h.RecoverySafe(hole.Tee)||DreamCourseLayout.CorridorDistance(h.Centre,hole.Centerline)<h.Radius+h.Motion+8))report.invalidConfigurations++;
                var recovery=layout.SafeRecovery(hole,layout.Hazards.Length>0?layout.Hazards[0].Centre:hole.Tee);
                if(hole.LieAt(recovery)==CourseLie.Water||hole.LieAt(recovery)==CourseLie.OutOfBounds||layout.Hazards.Any(h=>!h.RecoverySafe(recovery)))report.invalidConfigurations++;
            }
            hole.Rules=new PlayRules();hole.Dream=DreamCourseLayout.Build(hole,47,Weather.Clear);hole.Movers=new CourseMovers(hole.Dream.SolidMovers());var route=hole.Dream;report.hazard=route.Code;
            if(System.Environment.GetEnvironmentVariable("DREAM_ROUTE_CALIBRATE")=="1"){
                if(!hole.Movers.All.Any(m=>m.Kind==MoverKind.WindLift)){hole.Dream=prior;hole.Movers=movers;hole.Rules=rules;return;}
                var source=JsonUtility.FromJson<Report>(File.ReadAllText(path));var origin=new CoursePoint(source.originX,source.originD);
                var club=(GolfClub)Enum.Parse(typeof(GolfClub),source.club);double heading=source.heading;
                var gainField=typeof(Mover).GetField("dreamGain",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
                var liftField=typeof(Mover).GetField("dreamLiftFloor",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
                var best=new Calibration{hole=hole.Number,score=double.MaxValue};var rows=new StringBuilder("gain,lift,remaining,penalty,robustCost\n");
                bool fine=System.Environment.GetEnvironmentVariable("DREAM_ROUTE_FINE")=="1";
                var current=hole.Movers.All.First(m=>m.Kind==MoverKind.WindLift);
                double gainStart=fine?current.LiftGain-.15:hole.Par==3?.5:1,gainEnd=fine?current.LiftGain+.151:hole.Number==23?4.201:3.201;
                double liftStart=fine?current.LiftFloor-3:8,liftEnd=fine?current.LiftFloor+3:hole.Number==23?46:38;
                for(double gain=gainStart;gain<=gainEnd;gain+=fine?.01:.1)for(double lift=liftStart;lift<=liftEnd;lift+=fine?.5:2){
                    foreach(var m in hole.Movers.All)if(m.Kind==MoverKind.WindLift){gainField.SetValue(m,gain);liftField.SetValue(m,lift);}
                    hole.Movers.PhaseAtLaunch=source.phase;var nominal=new CourseShot(club,new SwingImpact{Power=source.power},heading,origin,hole);
                    double cost=nominal.NextPosition.DistanceTo(hole.Pin)+nominal.PenaltyStrokes*150;
                    if(nominal.PenaltyStrokes==0&&cost<best.score*1.5){
                        double total=cost;int lost=0;
                        foreach(var error in new[]{(-.65,-.015),(-.65,.015),(.65,-.015),(.65,.015)}){
                            var shot=new CourseShot(club,new SwingImpact{Power=Math.Clamp(source.power+error.Item2,0,1)},heading+error.Item1,origin,hole);
                            total+=shot.NextPosition.DistanceTo(hole.Pin)+shot.PenaltyStrokes*150;lost+=shot.PenaltyStrokes;
                        }
                        cost=total/5;
                        if(cost<best.score)best=new Calibration{hole=hole.Number,gain=gain,lift=lift,score=cost,remaining=nominal.Rest.DistanceTo(hole.Pin),misses=lost};
                    }
                    rows.AppendLine(FormattableString.Invariant($"{gain:F2},{lift:F1},{nominal.NextPosition.DistanceTo(hole.Pin):F2},{nominal.PenaltyStrokes},{cost:F2}"));
                }
                File.WriteAllText(Path.Combine(output,$"calibration-hole{hole.Number:00}.csv"),rows.ToString());File.WriteAllText(Path.Combine(output,$"calibration-hole{hole.Number:00}.json"),JsonUtility.ToJson(best,true));
                Debug.Log($"[DreamCalibration] hole {hole.Number}: gain {best.gain:F2}, loft {best.lift:F1}, remaining {best.remaining:F1}, robust cost {best.score:F1}");
                hole.Dream=prior;hole.Movers=movers;hole.Rules=rules;return;
            }
            CoursePoint bestOrigin=hole.Tee;GolfClub bestClub=GolfClub.Driver;double bestPower=1,bestHeading=0,bestPhase=0,bestBenefit=0;
            var target=route.Hazards[0].Centre;
            if(reuse){bestOrigin=new CoursePoint(report.originX,report.originD);bestClub=(GolfClub)Enum.Parse(typeof(GolfClub),report.club);bestPower=report.power;bestHeading=report.heading;bestPhase=report.phase;bestBenefit=report.benefitYards;}
            else foreach(double fraction in new[]{0.0,.15,.28}){
                var origin=fraction==0?hole.Tee:DreamCourseLayout.Along(hole,fraction);
                if(hole.LieAt(origin)==CourseLie.Water||hole.LieAt(origin)==CourseLie.OutOfBounds||origin.DistanceTo(target)<25)continue;
                double heading=origin.HeadingTo(target);
                foreach(var club in clubs)foreach(double power in new[]{.55,.7,.85,1.0})foreach(double offset in new[]{-5.0,-2.5,0,2.5,5})foreach(double phase in new[]{0.0,3,6,9}){
                    report.candidateShots++;hole.Movers.PhaseAtLaunch=phase;var shot=new CourseShot(club,new SwingImpact{Power=power},heading+offset,origin,hole);
                    if(!Interacts(shot,route))continue;report.interactions++;if(hole.Number==8)Debug.Log($"[NeedleShot] {club} {power} heading={heading+offset:F2} phase={phase} rest={shot.Rest} lie={shot.Lie} carry={shot.Carry:F1} window={route.Hazards[0].LiftHeight:F1} target={route.ShortcutTarget}");if(!Dry(shot))continue;
                    hole.Dream=null;var saved=hole.Movers;hole.Movers=null;var baseline=new CourseShot(club,new SwingImpact{Power=power},heading+offset,origin,hole);hole.Dream=route;hole.Movers=saved;
                    double benefit=baseline.NextPosition.DistanceTo(hole.Pin)-shot.NextPosition.DistanceTo(hole.Pin)+baseline.PenaltyStrokes*150;
                    if(benefit<=bestBenefit)continue;bestBenefit=benefit;bestOrigin=origin;bestClub=club;bestPower=power;bestHeading=heading+offset;bestPhase=phase;
                    report.remainingWithRoute=shot.Rest.DistanceTo(hole.Pin);report.remainingWithoutRoute=baseline.NextPosition.DistanceTo(hole.Pin);report.benefitYards=benefit;
                }
            }
            // Refine the previously found entry using real landing distance and small execution errors.
            // Optimizing improvement over an identical unassisted shot can select a worse actual route.
            double entryHeading=bestHeading,entryPower=bestPower,bestCost=double.MaxValue;
            for(int a=-4;a<=4;a++)for(int p=-2;p<=2;p++){
                double heading=entryHeading+a*.25,power=Math.Clamp(entryPower+p*.01,0,1);
                hole.Movers.PhaseAtLaunch=bestPhase;
                var nominal=new CourseShot(bestClub,new SwingImpact{Power=power},heading,bestOrigin,hole);
                if(!Interacts(nominal,route)||!Dry(nominal))continue;
                double cost=nominal.NextPosition.DistanceTo(hole.Pin);
                foreach(var error in new[]{(-.65,-.015),(-.65,.015),(.65,-.015),(.65,.015)}){
                    var trial=new CourseShot(bestClub,new SwingImpact{Power=Math.Clamp(power+error.Item2,0,1)},heading+error.Item1,bestOrigin,hole);
                    cost+=trial.NextPosition.DistanceTo(hole.Pin)+trial.PenaltyStrokes*150;
                }
                if(cost<bestCost){bestCost=cost;bestHeading=heading;bestPower=power;}
            }
            hole.Movers.PhaseAtLaunch=bestPhase;
            var selected=new CourseShot(bestClub,new SwingImpact{Power=bestPower},bestHeading,bestOrigin,hole);
            hole.Dream=null;var selectedMovers=hole.Movers;hole.Movers=null;
            var unassisted=new CourseShot(bestClub,new SwingImpact{Power=bestPower},bestHeading,bestOrigin,hole);
            hole.Dream=route;hole.Movers=selectedMovers;
            bestBenefit=unassisted.NextPosition.DistanceTo(hole.Pin)-selected.NextPosition.DistanceTo(hole.Pin)+unassisted.PenaltyStrokes*150;
            report.remainingWithRoute=selected.Rest.DistanceTo(hole.Pin);report.remainingWithoutRoute=unassisted.NextPosition.DistanceTo(hole.Pin);report.benefitYards=bestBenefit;
            report.beneficialRouteFound=bestBenefit>=8;report.originX=bestOrigin.X;report.originD=bestOrigin.D;report.club=bestClub.ToString();report.power=bestPower;report.heading=bestHeading;report.phase=bestPhase;
            // Find a reproducible conservative first shot from the identical origin. It must avoid the optional volume.
            GolfClub safeClub=GolfClub.Iron;double safePower=.7,safeHeading=bestOrigin.HeadingTo(hole.RecommendedTarget(bestOrigin)),safeScore=double.MaxValue;
            foreach(var aimTarget in new[]{hole.RecommendedTarget(bestOrigin),hole.Pin})foreach(var club in clubs)for(double power=.4;power<=1.001;power+=.1){
                double aim=bestOrigin.HeadingTo(aimTarget);hole.Movers.PhaseAtLaunch=bestPhase;var trial=new CourseShot(club,new SwingImpact{Power=power},aim,bestOrigin,hole);
                bool corridor=true;for(double t=0;t<trial.Duration;t+=.2){var p=trial.PositionAt(t);if(DreamCourseLayout.CorridorDistance(new CoursePoint(p.x,p.d),hole.Centerline)>hole.FairwayWidth*.5+4){corridor=false;break;}}
                if(!corridor||Interacts(trial,route)||!Dry(trial))continue;double value=ConservativeCost(club,power,aim);
                if(value<safeScore){safeScore=value;safeClub=club;safePower=power;safeHeading=aim;}
            }
            // Refine the safe shot and rank its full expert error envelope, not a lucky nominal landing.
            double safeEntryPower=safePower,safeEntryHeading=safeHeading;
            for(int a=-4;a<=4;a++)for(int p=-8;p<=8;p++){
                double power=Math.Clamp(safeEntryPower+p*.01,.2,1),heading=safeEntryHeading+a*.5;
                double cost=ConservativeCost(safeClub,power,heading);
                if(cost<safeScore){safeScore=cost;safePower=power;safeHeading=heading;}
            }
            report.conservativeRouteFound=safeScore<double.MaxValue;report.conservativeClub=safeClub.ToString();report.conservativePower=safePower;report.conservativeHeading=safeHeading;
            double ConservativeCost(GolfClub club,double power,double heading){
                double total=0;
                foreach(var error in new[]{(0.0,0.0),(-1.0,-.025),(-1.0,.025),(1.0,-.025),(1.0,.025)}){
                    hole.Movers.PhaseAtLaunch=bestPhase;
                    var trial=new CourseShot(club,new SwingImpact{Power=Math.Clamp(power+error.Item2,0,1)},heading+error.Item1,bestOrigin,hole);
                    if(Interacts(trial,route))return double.MaxValue;
                    for(double t=0;t<trial.Duration;t+=.2){var point=trial.PositionAt(t);if(DreamCourseLayout.CorridorDistance(new CoursePoint(point.x,point.d),hole.Centerline)>hole.FairwayWidth*.5+4)return double.MaxValue;}
                    total+=trial.NextPosition.DistanceTo(hole.Pin)+trial.PenaltyStrokes*300;
                }
                return total/5;
            }
            var samples=new List<Sample>();int level=0;
            foreach(var skill in new[]{"novice","intermediate","expert"}){
                var sample=new Sample{skill=skill,count=48};var rng=new System.Random(20261015);double angle=level==0?5:level==1?2.5:1,pace=level==0?.12:level==1?.06:.025;
                for(int n=0;n<sample.count;n++){
                    hole.Movers.PhaseAtLaunch=bestPhase+(rng.NextDouble()-.5)*(level==0?3:level==1?1.5:.5);
                    double powerError=(rng.NextDouble()-.5)*pace*2,angleError=(rng.NextDouble()-.5)*angle*2;
                    var shot=new CourseShot(bestClub,new SwingImpact{Power=Math.Clamp(bestPower+powerError,0,1)},bestHeading+angleError,bestOrigin,hole);
                    var safe=new CourseShot(safeClub,new SwingImpact{Power=Math.Clamp(safePower+powerError,0,1)},safeHeading+angleError,bestOrigin,hole);
                    double Remaining(CourseShot result){if(result.IsHoled)return 0;double d=result.NextPosition.DistanceTo(hole.Pin),approach=level==0?170:level==1?205:240,putts=level==0?2.3:level==1?2:1.8;return d<3?1:d<15?putts:putts+Math.Max(.35,(d-15)/approach);}
                    if(shot.IsHoled)sample.holedOuts++;if(safe.IsHoled)sample.conservativeHoledOuts++;sample.penalties+=shot.PenaltyStrokes;if(shot.Burned)sample.burns++;sample.meanRemaining+=shot.NextPosition.DistanceTo(hole.Pin);
                    sample.estimatedStrokes+=1+shot.PenaltyStrokes+Remaining(shot);
                    sample.conservativeEstimatedStrokes+=1+safe.PenaltyStrokes+Remaining(safe);sample.conservativeMeanRemaining+=safe.NextPosition.DistanceTo(hole.Pin);sample.conservativeMeanPenalty+=safe.PenaltyStrokes;
                }
                sample.estimatedStrokes/=sample.count;sample.conservativeEstimatedStrokes/=sample.count;sample.conservativeMeanRemaining/=sample.count;sample.conservativeMeanPenalty/=sample.count;sample.meanRemaining/=sample.count;sample.meanPenalty=(double)sample.penalties/sample.count;samples.Add(sample);level++;
            }
            report.samples=samples.ToArray();File.WriteAllText(Path.Combine(output,$"hole{hole.Number:00}.json"),JsonUtility.ToJson(report,true));Debug.Log($"[DreamRoutes] hole {hole.Number}: {report.interactions}/{report.candidateShots} interactions, benefit {bestBenefit:F1}yd, placement failures {report.invalidConfigurations}");
            hole.Dream=prior;hole.Movers=movers;hole.Rules=rules;
        }
    }
}
