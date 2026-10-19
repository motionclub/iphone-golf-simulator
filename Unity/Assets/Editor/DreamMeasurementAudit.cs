using System;
using System.IO;
using System.Text;
using GolfArcade.Course;
using GolfArcade.Shot;
using GolfArcade.Swing;
using UnityEditor;
namespace GolfArcade.EditorTools
{
    public static class DreamMeasurementAudit
    {
        public static void Run()
        {
            string root=Path.GetFullPath("../work/dream-worlds-20261015/proof/measurements");Directory.CreateDirectory(root);
            var h=new Hole{Number=99,Par=4,Centerline=new[]{CoursePoint.Zero,new CoursePoint(0,400)},FairwayWidth=200,RoughWidth=100,Ground=_=>0};
            var shots=new StringBuilder("profile,repeat,carry_yards,roll_yards,rest_x_yards,rest_d_yards,penalties\n");
            foreach(string profile in new[]{"dry","rain","snow","ash","crosswind_8mph","crosswind_14mph","crosswind_24mph"}){
                h.Rules=new PlayRules();
                if(profile=="rain"||profile=="snow"||profile=="ash")Weather.Rain.Bend(h.Rules,profile=="snow"?Sky.Snow:profile=="ash"?Sky.Ash:Sky.Rain);
                var wind=profile.StartsWith("crosswind")?new Wind(profile.Contains("24")?24:profile.Contains("14")?14:8,90):Wind.Calm;
                for(int repeat=0;repeat<10;repeat++){
                    var shot=new CourseShot(GolfClub.Iron,new SwingImpact{Power=.8},0,h.Tee,h,1,wind);
                    shots.AppendLine(FormattableString.Invariant($"{profile},{repeat},{shot.Carry:R},{shot.Roll:R},{shot.Rest.X:R},{shot.Rest.D:R},{shot.PenaltyStrokes}"));
                }
            }
            File.WriteAllText(Path.Combine(root,"repeat-shots.csv"),shots.ToString());
            var fog=new StringBuilder("elevation_yards,distance_yards,transmission,exact_marker_visible\n");
            foreach(double y in new[]{0.0,80,200})foreach(double d in new[]{0.0,10,15,40,60,80,120}){
                double t=DreamConditions.Visibility(0,y,d,0,y,0);fog.AppendLine(FormattableString.Invariant($"{y},{d},{t:R},{t>=.24}"));
            }
            File.WriteAllText(Path.Combine(root,"fog-distance.csv"),fog.ToString());
            var clock=new StringBuilder("utc,est_hour,daylight,sunset\n");
            foreach(string day in new[]{"2026-01-15","2026-07-15"})foreach(double hour in new[]{0.0,4.99,5,6,7,16.5,17.99,18,19.5,20.99,21,23.99}){
                double utc=DateTimeOffset.Parse(day+"T00:00:00Z").ToUnixTimeSeconds()+(hour+5)*3600;
                clock.AppendLine(FormattableString.Invariant($"{utc},{DreamConditions.EstHour(utc):R},{DreamConditions.Daylight(utc):R},{DreamConditions.Sunset(utc):R}"));
            }
            File.WriteAllText(Path.Combine(root,"clock.csv"),clock.ToString());
            var vent=new DreamHazard{Kind=DreamHazardKind.LavaVent,Centre=CoursePoint.Zero,Height=0,Radius=4};
            var timeline=new StringBuilder("seconds,stage,burns_at_centre,seconds_to_change\n");
            for(double t=0;t<=24;t+=.25)timeline.AppendLine(FormattableString.Invariant($"{t},{vent.Stage(t)},{vent.Burns(0,1,0,t)},{vent.UntilChange(t):R}"));
            File.WriteAllText(Path.Combine(root,"vent-cycle.csv"),timeline.ToString());
            EditorApplication.Exit(0);
        }
    }
}
