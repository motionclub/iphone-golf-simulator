using System;
using System.Collections.Generic;
namespace GolfArcade.Course
{
    public enum DreamHazardKind { RockGate, LavaVent, WindLift, IceRunway, BasaltGate }
    public enum VentStage { Cooling, Warning, Active }
    public sealed class DreamHazard
    {
        public string Id;public DreamHazardKind Kind;public CoursePoint Centre, Recovery;
        public double Gain=1.23,LiftFloor=10,Preserve=.2;
        public double Height, LiftHeight=14.5, ActiveHeight=24, Radius=4, Phase, Period=12, Motion=3;
        public VentStage Stage(double time)
        {
            double t=((time+Phase)%Period+Period)%Period;
            return t<6.5?VentStage.Cooling:t<9?VentStage.Warning:t<10.5?VentStage.Active:VentStage.Cooling;
        }
        public double UntilChange(double time){double t=((time+Phase)%Period+Period)%Period;return (t<6.5?6.5:t<9?9:t<10.5?10.5:Period+6.5)-t;}
        public bool Burns(double x,double y,double d,double time)
        {
            if(Kind!=DreamHazardKind.LavaVent||Stage(time)!=VentStage.Active)return false;
            double dx=x-Centre.X,dz=d-Centre.D;return dx*dx+dz*dz<=(Radius+CourseShot.BallRadius)*(Radius+CourseShot.BallRadius)&&y>=Height-.2&&y<=Height+ActiveHeight;
        }
        public bool RecoverySafe(CoursePoint p) => Centre.DistanceTo(p)>Radius+Motion+8;
    }
    /// Explicit catalogue authored in course yards. The conservative route is the original centreline.
    /// Sockets are on one side of it with a clear 8-yard corridor for the entire motion cycle.
    public sealed class DreamCourseLayout
    {
        public readonly DreamHazard[] Hazards;public readonly CoursePoint[] Conservative;
        public readonly CoursePoint ShortcutTarget;public readonly string RouteName;
        public readonly int Version=DreamConditions.Version;
        public DreamCourseLayout(DreamHazard[] hazards,CoursePoint[] conservative,CoursePoint target,string name){Hazards=hazards;Conservative=conservative;ShortcutTarget=target;RouteName=name;}
        public string Code {get {var ids=new List<string>();foreach(var h in Hazards)ids.Add(h.Id+"@"+h.Phase.ToString("R",System.Globalization.CultureInfo.InvariantCulture));return string.Join(";",ids);}}
        readonly struct Socket
        {
            public readonly int Hole;public readonly double Along,Side,Landing;public readonly DreamHazardKind Kind;public readonly string Name;
            public Socket(int hole,double along,double side,double landing,DreamHazardKind kind,string name){Hole=hole;Along=along;Side=side;Landing=landing;Kind=kind;Name=name;}
        }
        static readonly Dictionary<int,(double gain,double lift)> Currents=new(){
            { 7, (2.60, 12.0) },
            { 8, (1.70, 30.0) },
            { 9, (3.00, 30.0) },
            { 10, (2.80, 24.0) },
            { 12, (1.31, 22.5) },
            { 13, (1.50, 34.0) },
            { 14, (1.90, 38.0) },
            { 15, (1.09, 24.0) },
            { 16, (1.40, 18.0) },
            { 18, (0.90, 41.0) },
            { 19, (2.20, 22.0) },
            { 20, (1.40, 24.0) },
            { 21, (1.01, 31.5) },
            { 22, (1.40, 38.0) },
            { 23, (4.20, 12.0) },
        };
        static readonly Socket[] Sockets={
            new(7,.43,-1,.95,DreamHazardKind.RockGate,"Sea-stack window"),new(8,.48,1,.98,DreamHazardKind.RockGate,"Needle aperture"),
            new(9,.39,-1,.95,DreamHazardKind.WindLift,"Split tailwind"),new(12,.54,1,.985,DreamHazardKind.RockGate,"Island window"),new(15,.49,-1,1,DreamHazardKind.WindLift,"Stairway current"),
            new(13,.45,-1,.94,DreamHazardKind.RockGate,"Spiral cut"),new(14,.52,1,.95,DreamHazardKind.RockGate,"Root window"),new(17,.43,1,.76,DreamHazardKind.IceRunway,"Fjord runway"),
            new(18,.48,-1,1,DreamHazardKind.WindLift,"Canyon lift"),new(19,.48,1,.95,DreamHazardKind.RockGate,"Temple aperture"),new(20,.52,-1,.95,DreamHazardKind.WindLift,"Petal current"),
            new(10,.42,-1,.95,DreamHazardKind.LavaVent,"Crater crossing"),new(16,.50,1,.95,DreamHazardKind.BasaltGate,"Rim gate"),new(21,.50,-1,.985,DreamHazardKind.LavaVent,"Quiet plume"),
            new(22,.46,-1,.94,DreamHazardKind.LavaVent,"Cooling causeway"),new(23,.42,-1,.95,DreamHazardKind.BasaltGate,"Crown crossing")};
        public static CoursePoint Along(Hole hole,double fraction)
        {
            var c=hole.Centerline;double total=0;for(int i=1;i<c.Length;i++)total+=c[i-1].DistanceTo(c[i]);
            double wanted=total*Math.Max(0,Math.Min(1,fraction));
            for(int i=1;i<c.Length;i++){double n=c[i-1].DistanceTo(c[i]);if(wanted<=n)return new CoursePoint(c[i-1].X+(c[i].X-c[i-1].X)*wanted/Math.Max(.001,n),c[i-1].D+(c[i].D-c[i-1].D)*wanted/Math.Max(.001,n));wanted-=n;}return hole.Pin;
        }
        public static double CorridorDistance(CoursePoint p,CoursePoint[] line)
        {
            double best=double.MaxValue;for(int i=1;i<line.Length;i++){var a=line[i-1];var b=line[i];double dx=b.X-a.X,dz=b.D-a.D;double t=Math.Max(0,Math.Min(1,((p.X-a.X)*dx+(p.D-a.D)*dz)/Math.Max(.001,dx*dx+dz*dz)));best=Math.Min(best,p.DistanceTo(new CoursePoint(a.X+t*dx,a.D+t*dz)));}return best;
        }
        public static DreamCourseLayout Build(Hole hole,int seed,Weather weather)
        {
            foreach(var s in Sockets)if(s.Hole==hole.Number){
                var at=Along(hole,s.Along);var next=Along(hole,s.Along+.02);double h=at.HeadingTo(next)*Math.PI/180;
                // Two authored lateral sockets; same protected conservative corridor.
                double offset=17+(RoundEvents.Mix(seed,hole.Number,0x48415A)%2)*3;
                var p=new CoursePoint(at.X+Math.Cos(h)*s.Side*offset,at.D-Math.Sin(h)*s.Side*offset);
                if(CorridorDistance(p,hole.Centerline)<12) p=new CoursePoint(at.X-Math.Cos(h)*s.Side*offset,at.D+Math.Sin(h)*s.Side*offset);
                var target=Along(hole,s.Landing);var kind=s.Kind;
                if(hole.LieAt(target).PenaltyStrokes()>0){
                    for(int station=1;station<=20;station++){
                        var candidate=Along(hole,s.Landing+(1-s.Landing)*station/20);
                        if(hole.LieAt(candidate).PenaltyStrokes()==0){target=candidate;break;}
                    }
                }
                // Par-3 currents reward a birdie approach rather than guiding directly into the cup.
                if(hole.Par==3){
                    for(int direction=0;direction<8;direction++){
                        double angle=direction*Math.PI/4;
                        var candidate=new CoursePoint(target.X+2*Math.Cos(angle),target.D+2*Math.Sin(angle));
                        if(candidate.DistanceTo(hole.Pin)>=2 && hole.LieAt(candidate).PenaltyStrokes()==0){target=candidate;break;}
                    }
                }
                // Severe weather never adds a lethal timing requirement, even on the optional line.
                if(kind==DreamHazardKind.LavaVent && (weather==Weather.Fog||weather==Weather.Storm))kind=DreamHazardKind.BasaltGate;
                var hazard=new DreamHazard{Id=$"v5-{hole.Number}-{kind}",Kind=kind,Centre=p,Height=hole.Ground?.Invoke(p)??0,Recovery=hole.Tee,Phase=RoundEvents.Mix(seed,hole.Number,0x504841)%12000/1000.0};
                if(Currents.TryGetValue(hole.Number,out var current)){hazard.Gain=current.gain;hazard.LiftFloor=current.lift;}hazard.Preserve=hole.Par==3?0:.2;
                // The fixed authored flight window is sized from an ordinary approach, before any player commits.
                // This is independent of weather/decorative RNG and never follows a live ball.
                var approach=hole.Tee;
                if(approach.DistanceTo(p)>215)approach=Along(hole,.15);
                if(approach.DistanceTo(p)>215)approach=Along(hole,.28);
                double aim=approach.HeadingTo(p)*Math.PI/180;
                var beyond=new CoursePoint(p.X+Math.Sin(aim)*70,p.D+Math.Cos(aim)*70);
                var plan=CourseRings.StraightShot(approach,beyond,PlayRules.Standard);
                if(plan.HasValue){
                    var flight=plan.Value.flight;double fraction=Math.Min(.96,approach.DistanceTo(p)/Math.Max(1,flight.Carry));
                    double time=flight.CarryTime*fraction;
                    // Flight speed is not uniform; locate the actual crossing of the socket's vertical plane.
                    for(double t=0;t<=flight.CarryTime;t+=.02)if(flight.PositionAt(t).DistanceYards>=approach.DistanceTo(p)){time=t;break;}
                    var point=flight.PositionAt(time);double g0=hole.Ground?.Invoke(approach)??0,g1=hole.Ground?.Invoke(beyond)??0;
                    hazard.LiftHeight=Math.Max(9,Math.Min(48,g0+(g1-g0)*time/Math.Max(.01,flight.CarryTime)+point.HeightYards-hazard.Height));
                    hazard.ActiveHeight=Math.Max(24,hazard.LiftHeight+5);
                }
                if(CorridorDistance(p,hole.Centerline)<hazard.Radius+hazard.Motion+8 || p.DistanceTo(hole.Tee)<35 || p.DistanceTo(hole.Pin)<35)
                    return new DreamCourseLayout(Array.Empty<DreamHazard>(),hole.Centerline,target,s.Name);
                return new DreamCourseLayout(new[]{hazard},hole.Centerline,target,s.Name);
            }
            return new DreamCourseLayout(Array.Empty<DreamHazard>(),hole.Centerline,hole.Pin,"Approach");
        }
        public bool IceAt(CoursePoint p)
        {
            foreach(var h in Hazards)if(h.Kind==DreamHazardKind.IceRunway && Math.Abs(p.X-h.Centre.X)<2.5 && Math.Abs(p.D-h.Centre.D)<40 && CorridorDistance(p,Conservative)>8)return true;
            return false;
        }
        public CoursePoint SafeRecovery(Hole hole,CoursePoint origin)
        {
            bool Safe(CoursePoint p){var lie=hole.LieAt(p);if(lie==CourseLie.Water||lie==CourseLie.OutOfBounds)return false;foreach(var h in Hazards)if(!h.RecoverySafe(p))return false;return true;}
            if(Safe(origin))return origin;
            for(int i=0;i<=100;i++){var p=Along(hole,i/100.0);if(Safe(p))return p;}
            return hole.Tee;
        }
        public bool Burns(double x,double y,double z,double time,out DreamHazard hit){foreach(var h in Hazards)if(h.Burns(x,y,z,time)){hit=h;return true;}hit=null;return false;}
        public Mover[] SolidMovers()
        {
            var list=new List<Mover>();foreach(var h in Hazards){
                if(h.Kind==DreamHazardKind.RockGate || h.Kind==DreamHazardKind.BasaltGate){
                    // 10-19 (Adnan: "remove floating rocks from maps"): the gate's two rocks hung in mid-air above and
                    // below the current; only the current stays.
                    list.Add(Mover.Dream(h.Centre,h.Height+h.LiftHeight,h.Period,h.Phase/h.Period,4,0,true,ShortcutTarget,h.Gain,h.LiftFloor,h.Preserve));
                } else if(h.Kind==DreamHazardKind.LavaVent)list.Add(Mover.Dream(h.Centre,h.Height+h.LiftHeight,h.Period,h.Phase/h.Period,4,0,true,ShortcutTarget,h.Gain,h.LiftFloor,h.Preserve));
                else if(h.Kind==DreamHazardKind.WindLift)list.Add(Mover.Dream(h.Centre,h.Height+h.LiftHeight,h.Period,h.Phase/h.Period,5,0,true,ShortcutTarget,h.Gain,h.LiftFloor,h.Preserve));
            }return list.ToArray();
        }
    }
}
