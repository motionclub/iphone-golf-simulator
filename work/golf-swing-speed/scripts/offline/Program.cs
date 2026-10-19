using System; using System.Collections.Generic; using System.Numerics; using GolfArcade.Shot; using GolfArcade.Swing;
static class P {
  static void Main() {
    foreach (var (club, top, down) in new[]{(GolfClub.Driver,2.75,.20),(GolfClub.Driver,2.75,.32),(GolfClub.Iron,1.6,.28),(GolfClub.Putter,.45,.35),(GolfClub.Wedge,2.75,.25)}) {
      var d = new MotionSwingDetector(); d.SetReadyPose(Quaternion.Identity); d.Configure(club);
      var coming = new List<double>(); double struck = double.NaN, t = 0; double tDown=-1, tStruck=-1;
      void Feed(double a, double r) { t += .01; var e = d.Ingest(t, Quaternion.CreateFromAxisAngle(Vector3.UnitX,(float)a), new Vector3((float)r,0,0), Vector3.Zero);
        if (d.Phase == SwingPhase.Downswing) { if (tDown<0) tDown=t; coming.Add(d.DownswingProgress); }
        if (e?.Kind == SwingEventKind.Impact) { struck = d.DownswingProgress; tStruck=t; } }
      for (int i=0;i<40;i++) Feed(0,0);
      for (int i=1;i<=80;i++){double u=i/80.0; Feed(top*(.5-.5*Math.Cos(Math.PI*u)), top*.5*Math.PI/.8*Math.Sin(Math.PI*u));}
      for (int i=0;i<6;i++) Feed(top,0); double t0=t;
      double k=top/(down*down); for(double s=.01;s<down*1.3;s+=.01) Feed(top-k*s*s,-2*k*s);
      bool mono=true; for(int i=1;i<coming.Count;i++) if(coming[i]<coming[i-1]-1e-9) mono=false;
      Console.WriteLine($"{club} top {top} down {down}: first {(coming.Count>0?coming[0]:-1):F3} mono {mono} struck {struck:F3}  detect +{tDown-t0:F2}s  struck +{tStruck-t0:F2}s n={coming.Count}");
    } } }
