from pathlib import Path
p=Path('Unity/Assets/Scripts/Course/CourseShot.cs');s=p.read_text();sig='        public CourseShot(GolfClub club, SwingImpact impact, double heading, CoursePoint origin, Hole hole, double lieFactor = 1, Wind wind = default)'
assert sig in s
s=s.replace(sig,'''        public readonly bool Burned;
        public readonly double BurnTime, BurnHeight;
        public readonly string BurnHazard;
        public CourseShot(GolfClub club, SwingImpact impact, double heading, CoursePoint origin, Hole hole, double lieFactor = 1, Wind wind = default)
            : this(club,impact,heading,origin,hole,lieFactor,wind,true)
        {
            if(hole.Dream==null || Duration<=0 || Power<=0)return;
            var ground=hole.Ground ?? (_=>0.0);
            // Substeps bounded at 1/600 s: the narrowest plume is 8 yd wide and shots are <150 yd/s.
            // This includes rebounds and rolling, and only runs for a committed moving shot.
            for(double t=1.0/600;t<=Duration;t+=1.0/600){
                var w=WorldAt(t,ground);
                if(!hole.Dream.Burns(w.x,w.y,w.d,(hole.Movers?.PhaseAtLaunch??0)+t,out var hazard))continue;
                var samples=new List<(double x,double y,double d)>();
                for(double q=0;q<t;q+=SampleInterval)samples.Add(WorldAt(q,ground));
                samples.Add(w);
                Burned=true;BurnTime=t;BurnHeight=w.y;BurnHazard=hazard.Id;
                Rest=Landing=Touchdown=new CoursePoint(w.x,w.d);NextPosition=hole.Dream.SafeRecovery(hole,origin);
                Duration=CarryTime=LandingTime=t;Roll=0;HoledAt=null;Lie=CourseLie.Water;
                path.Clear();double g0=ground(origin),g1=ground(Rest);
                for(int i=0;i<samples.Count;i++){double q=Math.Min(t,i*SampleInterval);var v=samples[i];path.Add((v.x,v.y-(g0+(g1-g0)*q/Math.Max(t,.001)),v.d));}
                knocks.RemoveAll(k=>k.Time>t);return;
            }
        }
        CourseShot(GolfClub club, SwingImpact impact, double heading, CoursePoint origin, Hole hole, double lieFactor, Wind wind, bool core)''')
p.write_text(s)
p=Path('Unity/Assets/Scripts/Game/MoverView.cs');s=p.read_text().replace('                    case MoverKind.Balloon: view.BuildBalloon', '''                    case MoverKind.RockGate: case MoverKind.WindLift:
                        var body=m.Body(0,0);
                        var stone=HoleView.Primitive(PrimitiveType.Sphere,m.Kind==MoverKind.RockGate?"Solid floating rock":"Visible wind lift",m.Kind==MoverKind.RockGate?new Color(.38f,.46f,.49f):new Color(.35f,.85f,.9f),root);
                        stone.transform.localScale=Vector3.one*(float)(body.r*2);
                        stone.GetComponent<Renderer>().sharedMaterial.SetFloat("_Smoothness",.18f);
                        if(m.Kind==MoverKind.WindLift){stone.GetComponent<Renderer>().enabled=false;view.BuildTwister(root,i);}
                        break;
                    case MoverKind.Balloon: view.BuildBalloon''');s=s.replace('                    case MoverKind.Balloon:\n                    {','''                    case MoverKind.RockGate: case MoverKind.WindLift:
                        root.SetPositionAndRotation(new Vector3((float)x,(float)y,(float)d),Quaternion.Euler(0,(float)t*2,0));break;
                    case MoverKind.Balloon:
                    {''',1);p.write_text(s)
p=Path('Unity/Assets/Scripts/Game/GolfGame.cs');s=p.read_text().replace('bool InLava(CourseShot shot) => hole.HazardAt(shot.Rest) == HazardKind.Lava;', 'bool InLava(CourseShot shot) => shot.Burned || hole.HazardAt(shot.Rest) == HazardKind.Lava;')
s=s.replace('            if (flightTime < end || !caughtUp) return;', '''            if(LastShot.Burned && flightTime>=LastShot.BurnTime && splashedAt<0){
                splashedAt=flightTime;var impactAt=new Vector3((float)LastShot.Rest.X,(float)LastShot.BurnHeight,(float)LastShot.Rest.D);
                effects.LavaBurst(impactAt);sounds.PlayLavaHiss();Haptics.Failure();ball.gameObject.SetActive(false);
                hud.ShowCallout("Incinerated · shot + 1 penalty",new Color(1,.4f,.15f));
            }
            if(LastShot.Burned){if(flightTime>=LastShot.BurnTime+.6)FinishShot();return;}
            if (flightTime < end || !caughtUp) return;''')
s=s.replace('BallFlight.Launch PreviewLaunch(double power, CourseLie lie) => lie.LaunchFrom(club, Math.Clamp(power, 0, 1), 0, 0);','''BallFlight.Launch PreviewLaunch(double power, CourseLie lie)
        {
            var launch=lie.LaunchFrom(club,Math.Clamp(power,0,1),0,0);hole.Rules.Apply(ref launch);
            launch.WindMPH=Wind.SpeedMPH;launch.WindDegrees=Wind.RelativeTo(heading);return launch;
        }''')
s=s.replace('BallFlight.Simulate(lie.LaunchFrom(club, 1, 0, 0))','BallFlight.Simulate(PreviewLaunch(1,lie))')
s=s.replace('BallFlight.Launch L(double power, double start, double curve) => lie.LaunchFrom(club, power, start, curve);','BallFlight.Launch L(double power, double start, double curve) { var l=lie.LaunchFrom(club,power,start,curve);hole.Rules.Apply(ref l);l.WindMPH=Wind.SpeedMPH;l.WindDegrees=Wind.RelativeTo(heading);return l; }')
s=s.replace('                aimPath.Add(new Vector3','                if(!GolfArcade.EnvironmentArt.DreamVisibility.Visible(HoleView.ToWorld(at)))break;\n                aimPath.Add(new Vector3')
p.write_text(s)
p=Path('Unity/Assets/Scripts/Game/LandingZone.cs');s=p.read_text().replace('        void Update() => Build(0.5f + 0.5f * Mathf.Sin(Time.time * 2.2f));','        void Update() { GetComponent<Renderer>().enabled=GolfArcade.EnvironmentArt.DreamVisibility.Visible(transform.position); Build(0.5f + 0.5f * Mathf.Sin(Time.time * 2.2f)); }');p.write_text(s)
