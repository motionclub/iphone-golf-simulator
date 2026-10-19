using System;

namespace GolfArcade.Course
{
    /// Versioned pure rules shared by prediction, authority, replay and render adapters.
    public static class DreamConditions
    {
        public const int Version = 5;
        public const double MetresPerYard = .9144;
        public const double FogNear = 12, FogExtinction = .042;
        public static double EstHour(double utcSeconds) => ((utcSeconds / 3600 - 5) % 24 + 24) % 24;
        public static double Daylight(double utcSeconds)
        {
            double h = EstHour(utcSeconds);
            if (h < 5 || h >= 21) return 0;
            if (h < 7) return Smooth((h - 5) / 2);
            if (h <= 16.5) return 1;
            if (h < 18) return 1 - .12 * Smooth((h - 16.5) / 1.5);
            if (h < 19.5) return .88 - .65 * Smooth((h - 18) / 1.5);
            return .23 * (1 - Smooth((h - 19.5) / 1.5));
        }
        public static double Sunset(double utcSeconds)
        {
            double h = EstHour(utcSeconds);
            return h < 16.5 || h > 20.5 ? 0 : h < 18.75 ? Smooth((h-16.5)/2.25) : 1-Smooth((h-18.75)/1.75);
        }
        static double Smooth(double x) { x = Math.Max(0, Math.Min(1,x)); return x*x*(3-2*x); }
        static Weather RawWeather(int seed,int index)
        {
            double u = RoundEvents.Mix(seed,index,0x574541)/2147483648.0;
            return u < .25 ? Weather.Clear : u < .5 ? Weather.Gusty : u < .75 ? Weather.Rain : u < .9 ? Weather.Fog : Weather.Storm;
        }
        public static Weather WeatherFor(int seed,int index)
        {
            var w=RawWeather(seed,index);
            // A severe event has two holes of breathing room. No performance adaptation.
            return w==Weather.Storm && ((index>0&&RawWeather(seed,index-1)==Weather.Storm)||(index>1&&RawWeather(seed,index-2)==Weather.Storm)) ? Weather.Rain : w;
        }
        /// Broad stationary density banks, identical in the shader and the minimap.
        /// Height is relative to the observing player's terrain, never the camera.
        public static double Visibility(double x,double y,double z,double ox,double oy,double oz)
        {
            double dx=x-ox,dz=z-oz, distance=Math.Sqrt(dx*dx+dz*dz);
            double bank=1+.18*Math.Sin((x+ox)*.009)+.12*Math.Cos((z+oz)*.013);
            double height=1+.12*Math.Tanh((oy-y)/20);
            return Math.Exp(-Math.Max(0,distance-FogNear)*FogExtinction*bank*height);
        }
        public static bool ExactVisible(double x,double y,double z,double ox,double oy,double oz) => Visibility(x,y,z,ox,oy,oz) >= .24;
    }
    [Serializable]
    public sealed class EnvironmentSnapshot
    {
        public int version=DreamConditions.Version, seed, location, epoch;
        public double utcAnchor, elapsed;
        public int weather;
        public string hazards;
        public bool Compatible => version==DreamConditions.Version && double.IsFinite(utcAnchor) && utcAnchor>0 && double.IsFinite(elapsed) && elapsed>=0;
    }
    /// Monotonic progression; wall-clock changes can only be reconciled explicitly at a boundary.
    public sealed class EnvironmentClock
    {
        double anchor, start;
        public EnvironmentClock(double utc,double monotonic) { anchor=utc;start=monotonic; }
        public double At(double monotonic) => anchor+Math.Max(0,monotonic-start);
        public void Reconcile(double utc,double monotonic) { if(double.IsFinite(utc)&&double.IsFinite(monotonic)){anchor=utc;start=monotonic;} }
    }
}
