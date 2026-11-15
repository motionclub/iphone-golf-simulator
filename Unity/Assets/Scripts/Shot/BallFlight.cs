using System;
using System.Collections.Generic;

namespace GolfArcade.Shot
{
    /// A point on the ball's path. x = lateral (right), y = height, z = downrange, in yards,
    /// relative to where the ball was struck and the line it was aimed on.
    public struct FlightPoint
    {
        public double LateralYards;
        public double HeightYards;
        public double DistanceYards;

        public FlightPoint(double lateral, double height, double distance)
        {
            LateralYards = lateral; HeightYards = height; DistanceYards = distance;
        }

        public static FlightPoint Lerp(FlightPoint a, FlightPoint b, double t) => new(
            a.LateralYards + (b.LateralYards - a.LateralYards) * t,
            a.HeightYards + (b.HeightYards - a.HeightYards) * t,
            a.DistanceYards + (b.DistanceYards - a.DistanceYards) * t);
    }

    /// How a patch of ground takes a ball coming down on it (BallFlight.BounceOff): the fairway is the reference, a green
    /// is softer and bites on backspin, rough smothers, sand swallows, ice gives the spin nothing to hold.
    public readonly struct Turf
    {
        /// Share of its downward speed a slow, square bounce gets back (0 dead .. about 0.5 lively), and how much of that
        /// each m/s of impact takes away: the harder the ball comes down the more goes into the pitch mark.
        public readonly double Firm, Give;
        /// Friction between ball and ground during the bounce.
        public readonly double Friction;
        /// 0-1: the share of its pace along the ground the turf simply absorbs at each bounce, and the share of the hop.
        public readonly double Take, Dead;
        /// How hard backspin grips: 1 is a solid ball on a hard floor, more on a receptive green, less out of the rough.
        public readonly double Bite;

        public Turf(double firm, double give, double friction, double take, double dead, double bite)
        { Firm = firm; Give = give; Friction = friction; Take = take; Dead = dead; Bite = bite; }

        public static readonly Turf Fairway = new(0.44, 0.016, 0.42, 0.22, 0, 1.0);
        /// The same ground holding or deadening more: `dead` and `take` are floors (a rule that makes greens sticky).
        public Turf Holding(double dead, double take) => new(Firm, Give, Friction, Math.Max(Take, take), Math.Max(Dead, dead), Bite);
    }

    /// Physical ball flight: gravity, aerodynamic drag, Magnus lift from backspin (tilted for a
    /// draw or fade), then bounce and roll on a fairway. Integrated once per shot and sampled
    /// for playback. Units are SI inside, yards outside. Same fit as the iOS app.
    public sealed class BallFlight
    {
        public struct Launch
        {
            public double BallSpeedMPH;
            public double LaunchAngleDegrees;
            public double SpinRPM;
            /// Initial direction, degrees right of the target line.
            public double DirectionDegrees;
            /// Tilt of the spin axis, degrees. Positive curves right (fade/slice).
            public double CurveDegrees;
            /// Wind the ball flies through: speed in mph and the direction it blows toward,
            /// degrees right of the target line (0 helps, 180 is into the face).
            public double WindMPH;
            public double WindDegrees;
            /// The ground the ball comes down on (a fairway when not given). The flight itself is the same whatever is
            /// under it; the course flies each hop onto the ground it actually lands on (CourseShot), and this flat model
            /// is what the club tables, the rings and a shot over nothing but fairway use.
            public Turf? Ground;
            /// -1..1: how this particular landing differs from the average one (a harder or softer spot of turf). Zero for
            /// a planned shot; a struck one takes it from the strike, so every phone sees the same bounce.
            public double LandingLuck;
            /// The round's rules (Course.PlayRules): × gravity, and × how high it hops off the
            /// turf. 0 is plain golf's, the same as 1.
            public double Gravity;
            public double Bounce;
        }

        public const double SampleInterval = 1.0 / 60;
        public const double MaxDuration = 16.0;
        public const double MetersPerYard = 0.9144;

        readonly List<FlightPoint> samples;
        public double Carry { get; }
        /// Where the ball first touched down (the end of the carry), aim frame.
        public FlightPoint CarryPoint { get; }
        /// Seconds from the strike to that first touchdown.
        public double CarryTime { get; }
        public double Roll { get; }
        public double Apex { get; }
        /// Seconds into the flight at which the ball stopped bouncing and began to roll (0 for a
        /// putt), and its horizontal velocity then, yards/s. The course re-rolls from here on
        /// whatever grass the ball is actually on.
        public double RollStartTime { get; }
        public double RollStartVelocityX { get; }
        public double RollStartVelocityZ { get; }
        /// The ball as it first touches down, before the bounce: velocity in yards/s (lateral, up, downrange; up is
        /// negative) and the backspin it still has, rad/s. Zero for a putt.
        public double TouchdownVelocityX { get; private set; }
        public double TouchdownVelocityY { get; private set; }
        public double TouchdownVelocityZ { get; private set; }
        public double TouchdownSpin { get; private set; }
        public double Duration => (samples.Count - 1) * SampleInterval;
        public double Total => Carry + Roll;
        public FlightPoint Landing => samples[samples.Count - 1];
        public IReadOnlyList<FlightPoint> Samples => samples;

        BallFlight(List<FlightPoint> samples, double carry, FlightPoint carryPoint, double carryTime, double roll, double apex, double rollStartTime, double rollVx, double rollVz)
        {
            this.samples = samples; Carry = carry; CarryPoint = carryPoint; CarryTime = carryTime; Roll = roll; Apex = apex;
            RollStartTime = rollStartTime; RollStartVelocityX = rollVx; RollStartVelocityZ = rollVz;
        }

        public FlightPoint PositionAt(double time)
        {
            if (time <= 0) return samples[0];
            double last = Duration;
            if (time >= last) return samples[samples.Count - 1];
            double index = time / SampleInterval;
            int lower = Math.Min((int)index, samples.Count - 2);
            return FlightPoint.Lerp(samples[lower], samples[lower + 1], index - lower);
        }

        /// The 10-28 turf, kept for the record and for TurfRestitutionClassic's test: every full shot, wedges included,
        /// got 30-46% of its fall back, so everything hopped head-high and skipped two or three times whatever the club.
        public static double TurfRestitutionClassic(double downwardSpeed) =>
            Math.Max(0.30, Math.Min(0.46, 0.46 - 0.006 * Math.Max(0, downwardSpeed)));

        public const double BallRadiusMetres = 0.02135;
        /// The pitch mark: a ball coming down hard and steep digs in, and the ground's reaction leans back against it by
        /// this many radians per m/s of impact speed at a vertical landing (none for a ball skimming in), up to `MaxLean`.
        /// It is what makes a steep landing check and a shallow one skip (Penner, "The run of a golf ball", 2002).
        public const double LeanPerSpeed = 0.010, MaxLean = 0.32;
        /// The least any turf gives back of the speed into it, and the upward speed (m/s) under which a ball stays down.
        public const double MinRestitution = 0.10, HopSpeed = 1.2;
        /// How far one landing's luck moves the bounce (share of the rebound) and what the turf takes of the pace along it
        /// (share of `Turf.Take`: a softer or a firmer spot, never a push).
        public const double LuckInBounce = 0.10, LuckInTake = 0.35;

        /// One bounce, in SI units, y up. `spin` is backspin about the axis across the ball's travel (rad/s; negative once
        /// it is rolling forward). `slopeX`, `slopeZ` are the ground's rise per unit run along x and z where it lands.
        ///
        ///  * Into the ground: the turf gives back less the harder it is hit (`Turf.Firm`, `Turf.Give`), so a drive comes
        ///    off low and a chip nearly as it arrived.
        ///  * Along the ground: a spinning solid ball. Friction acts on the slip at the contact patch (travel plus
        ///    backspin); when it can stop the slip the ball leaves rolling at (5 v - 2 r w) / 7, which is zero or backwards
        ///    for a steep wedge with enough spin and most of v for a driver. `Turf.Bite` scales how hard the spin grips,
        ///    `Turf.Take` is what the grass absorbs on top.
        ///  * The slope: all of it happens in the ground's own frame, so an upslope takes the ball square on and kills
        ///    it, and a side slope kicks it downhill.
        public static void BounceOff(ref double vx, ref double vy, ref double vz, ref double spin, Turf turf,
            double slopeX = 0, double slopeZ = 0, double lively = 1, double luck = 0)
        {
            double nl = Math.Sqrt(slopeX * slopeX + 1 + slopeZ * slopeZ);
            double nx = -slopeX / nl, ny = 1 / nl, nz = -slopeZ / nl;
            double into = -(vx * nx + vy * ny + vz * nz);
            if (into <= 0) return;   // already leaving the face
            double tx = vx + into * nx, ty = vy + into * ny, tz = vz + into * nz;
            double along = Math.Sqrt(tx * tx + ty * ty + tz * tz);
            if (along > 1e-9) { tx /= along; ty /= along; tz /= along; }
            else
            {
                // straight down onto it: any direction along the ground serves
                tx = 1 - nx * nx; ty = -nx * ny; tz = -nx * nz;
                double l = Math.Sqrt(tx * tx + ty * ty + tz * tz);
                tx /= l; ty /= l; tz /= l; along = 0;
            }
            double steep = Math.Atan2(into, along), speed = Math.Sqrt(into * into + along * along);
            double lean = Math.Min(MaxLean, LeanPerSpeed * speed * steep / (Math.PI / 2));
            double c = Math.Cos(lean), sn = Math.Sin(lean);
            double vt = along * c - into * sn, vn = into * c + along * sn;
            luck = double.IsFinite(luck) ? Math.Max(-1, Math.Min(1, luck)) : 0;
            double e = Math.Max(MinRestitution, turf.Firm - turf.Give * vn) * (1 - turf.Dead);
            e = Math.Min(0.85, e * (double.IsFinite(lively) && lively > 0 ? lively : 1) * (1 + LuckInBounce * luck));
            double up = e * vn;
            double rs = BallRadiusMetres * spin * (spin > 0 ? turf.Bite : 1);
            double slip = vt + rs, most = turf.Friction * (1 + e) * vn;
            double outT, outSpin;
            double keep = 1 - Math.Min(1, turf.Take * (1 + LuckInTake * luck));
            if (Math.Abs(slip) <= 3.5 * most) { outT = (5 * vt - 2 * rs) / 7 * keep; outSpin = -outT / BallRadiusMetres; }
            else { double d = Math.Sign(slip) * most; outT = (vt - d) * keep; outSpin = spin - 2.5 * d / BallRadiusMetres; }
            double gT = outT * c - up * sn, gN = Math.Max(0, up * c + outT * sn);
            vx = gT * tx + gN * nx; vy = gT * ty + gN * ny; vz = gT * tz + gN * nz;
            // (kept against the way it now travels: a ball that has spun back is rolling, not still spinning back)
            spin = gT >= 0 ? outSpin : -outSpin;
        }

        public static BallFlight Simulate(Launch launch)
        {
            const double mass = 0.04593;
            const double radius = 0.02135;
            double area = Math.PI * radius * radius;
            const double airDensity = 1.225;
            double heavy = double.IsFinite(launch.Gravity) && launch.Gravity > 0 ? Math.Min(3, launch.Gravity) : 1;
            double gravity = 9.81 * heavy;
            double springy = double.IsFinite(launch.Bounce) && launch.Bounce > 0 ? Math.Min(4, launch.Bounce) : 1;
            // (a hop is one that leaves the turf for a moment; under a lighter pull a slower one still does)
            double hopSpeed = HopSpeed * Math.Sqrt(heavy);
            var turf = launch.Ground ?? Turf.Fairway;
            const double dt = 1.0 / 240;
            const double rollingDeceleration = 3.2;

            double speed = Math.Max(0, launch.BallSpeedMPH) * 0.44704;
            double elevation = launch.LaunchAngleDegrees * Math.PI / 180;
            double azimuth = launch.DirectionDegrees * Math.PI / 180;
            // x = right, y = up, z = downrange
            double px = 0, py = 0, pz = 0;
            double vx = Math.Sin(azimuth) * Math.Cos(elevation) * speed;
            double vy = Math.Sin(elevation) * speed;
            double vz = Math.Cos(azimuth) * Math.Cos(elevation) * speed;
            double spin = Math.Max(0, launch.SpinRPM) * 2 * Math.PI / 60;
            double tilt = launch.CurveDegrees * Math.PI / 180;
            // The air moves too: aerodynamic forces act on the ball's speed through the air,
            // not over the ground, which is all a head, tail or cross wind is.
            double windSpeed = (double.IsFinite(launch.WindMPH) ? Math.Max(0, launch.WindMPH) : 0) * 0.44704;
            double windAzimuth = (double.IsFinite(launch.WindDegrees) ? launch.WindDegrees : 0) * Math.PI / 180;
            double windX = Math.Sin(windAzimuth) * windSpeed, windZ = Math.Cos(windAzimuth) * windSpeed;

            var samples = new List<FlightPoint> { new(0, 0, 0) };
            double time = 0;
            double nextSample = SampleInterval;
            bool airborne = speed > 0.5 && elevation > 0.002; // a putt rolls from the first inch
            bool rolling = !airborne;
            double rollStartTime = 0, rollVx = vx, rollVz = vz;
            double? carryMeters = null;
            double carryX = 0, carryZ = 0, carryTime = 0;
            double downVx = 0, downVy = 0, downVz = 0, downSpin = 0;
            // (the spin the air acts on: gone after the first bounce, as it always was here; the ground still has the ball's)
            double groundSpin = 0; bool landed = false;
            double apexMeters = 0;

            while (time < MaxDuration)
            {
                if (airborne)
                {
                    double rx = vx - windX, ry = vy, rz = vz - windZ; // velocity through the air
                    double v = Math.Sqrt(rx * rx + ry * ry + rz * rz);
                    double ax = 0, ay = -gravity, az = 0;
                    if (v > 0.01)
                    {
                        // Fits to launch-monitor flights: drag grows with spin ratio, lift rises
                        // quickly then saturates, and spin fades slowly.
                        double spinRatio = radius * spin / v;
                        double drag = 0.20 + 0.35 * spinRatio;
                        double lift = Math.Min(0.32, 0.45 * Math.Pow(spinRatio, 0.4));
                        double dynamicPressure = 0.5 * airDensity * area * v * v;
                        double dx = rx / v, dy = ry / v, dz = rz / v;
                        // Backspin axis lies flat and perpendicular to travel; tilting it adds sideways lift.
                        double fx = -dz, fz = dx;
                        double fl = Math.Sqrt(fx * fx + fz * fz);
                        if (fl < 1e-9) { fx = 1; fz = 0; fl = 1; }
                        fx /= fl; fz /= fl;
                        double axX = fx * Math.Cos(tilt), axY = Math.Sin(tilt), axZ = fz * Math.Cos(tilt);
                        double al = Math.Sqrt(axX * axX + axY * axY + axZ * axZ);
                        axX /= al; axY /= al; axZ /= al;
                        // lift direction = axis × direction
                        double lx = axY * dz - axZ * dy;
                        double ly = axZ * dx - axX * dz;
                        double lz = axX * dy - axY * dx;
                        double k = dynamicPressure / mass;
                        ax += (-dx * drag + lx * lift) * k;
                        ay += (-dy * drag + ly * lift) * k;
                        az += (-dz * drag + lz * lift) * k;
                        spin *= Math.Exp(-dt / 45);
                    }
                    vx += ax * dt; vy += ay * dt; vz += az * dt;
                    px += vx * dt; py += vy * dt; pz += vz * dt;
                    apexMeters = Math.Max(apexMeters, py);
                    if (py <= 0 && vy < 0)
                    {
                        py = 0;
                        if (carryMeters is null)
                        {
                            carryMeters = Math.Sqrt(px * px + pz * pz); carryX = px; carryZ = pz; carryTime = time + dt;
                            downVx = vx; downVy = vy; downVz = vz; downSpin = spin;
                        }
                        if (!landed) { groundSpin = spin; landed = true; }
                        BounceOff(ref vx, ref vy, ref vz, ref groundSpin, turf, 0, 0, springy, launch.LandingLuck);
                        spin = 0;
                        if (vy < hopSpeed) { vy = 0; airborne = false; rolling = true; rollStartTime = time; rollVx = vx; rollVz = vz; }
                    }
                }
                else if (rolling)
                {
                    double ground = Math.Sqrt(vx * vx + vz * vz);
                    if (ground <= 0) break;
                    double slowed = Math.Max(0, ground - rollingDeceleration * dt);
                    double dx = vx / ground, dz = vz / ground;
                    double movingTime = Math.Min(dt, ground / rollingDeceleration);
                    double travel = ground * movingTime - 0.5 * rollingDeceleration * movingTime * movingTime;
                    vx = dx * slowed; vy = 0; vz = dz * slowed;
                    px += dx * travel; pz += dz * travel; py = 0;
                }
                time += dt;
                if (time + 1e-9 >= nextSample)
                {
                    samples.Add(new FlightPoint(px / MetersPerYard, Math.Max(0, py) / MetersPerYard, pz / MetersPerYard));
                    nextSample += SampleInterval;
                }
            }
            // still hopping when the clock ran out (a light-gravity round floats every hop): it rolls from here
            if (airborne && carryMeters is not null) { rollStartTime = time; rollVx = vx; rollVz = vz; }
            double finalDistance = Math.Sqrt(px * px + pz * pz);
            samples.Add(new FlightPoint(px / MetersPerYard, 0, pz / MetersPerYard));
            double carry = (carryMeters ?? 0) / MetersPerYard; // a shot that never flew is all roll
            var carryPoint = new FlightPoint(carryX / MetersPerYard, 0, carryZ / MetersPerYard);
            return new BallFlight(samples, carry, carryPoint, carryTime, Math.Max(0, finalDistance / MetersPerYard - carry), apexMeters / MetersPerYard,
                rollStartTime, rollVx / MetersPerYard, rollVz / MetersPerYard)
            {
                TouchdownVelocityX = downVx / MetersPerYard, TouchdownVelocityY = downVy / MetersPerYard, TouchdownVelocityZ = downVz / MetersPerYard,
                TouchdownSpin = downSpin,
            };
        }
    }
}
