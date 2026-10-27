using System;
using System.Collections.Generic;

namespace GolfArcade.Bowling
{
    /// The bowling sounds, synthesised (PLAN_Bowling.md §10 audio). Pure C# (System.Math only), so the
    /// renders are tested offline. Everything is 44.1 kHz stereo, interleaved L/R floats.
    ///
    /// The pin crash is rendered from the pin action's own impacts (BowlingPinDeck.Listen), so it is
    /// always in sync with what the TV shows and scales by itself: one clack for a single pin, a
    /// thunderous cascade for a strike. Each impact is a small modal model:
    ///   * pin (lacquered maple, plastic coat): a bright clack, modes ~0.8–5 kHz, 40–120 ms;
    ///   * ball on pin: a heavy low thump under the clack;
    ///   * pin on the deck: a dull wooden knock; on a kickback: a hollow panel thunk;
    ///   * the pit: a soft cushioned thud.
    /// A noise "rumble" follows the density of hits (the body of a crash), a crisp sweetener rides on a
    /// strike, and a small reverb sets the room (a club hall, an open beach, a cave).
    public static class BowlingSynth
    {
        public const int Rate = 44100;

        public enum Room { Club, Neon, Beach, Cave }

        /// Venue reverb: (wet, decay feedback, room size scale).
        static (float wet, float feedback, float size) RoomSpec(Room r) => r switch
        {
            Room.Neon => (.26f, .80f, 1.1f),
            Room.Beach => (.08f, .55f, .6f),
            Room.Cave => (.38f, .88f, 1.6f),
            _ => (.20f, .76f, 1f),
        };

        // ------------------------------------------------------------------ primitives

        /// Adds a decaying sinusoid (one mode) at `start` seconds, panned `pan` (-1..1).
        static void Mode(float[] buf, double start, double freq, double decay, double amp, double pan)
        {
            int n0 = (int)(start * Rate); int len = (int)(decay * 6 * Rate);
            double w = 2 * Math.PI * freq / Rate, k = Math.Exp(-1 / (decay * Rate));
            double c = Math.Cos(w), s = Math.Sin(w), x = 0, y = 1, e = amp;   // rotating phasor
            double gl = Math.Sqrt(.5 * (1 - pan)), gr = Math.Sqrt(.5 * (1 + pan));
            int frames = buf.Length / 2;
            for (int i = 0; i < len; i++)
            {
                int f = n0 + i; if (f >= frames) break; if (f < 0) { double nx0 = x * c - y * s; y = x * s + y * c; x = nx0; e *= k; continue; }
                double v = x * e;
                buf[2 * f] += (float)(v * gl); buf[2 * f + 1] += (float)(v * gr);
                double nx = x * c - y * s; y = x * s + y * c; x = nx; e *= k;
            }
        }

        /// A burst of filtered noise (one-pole low/high pass), exponential decay.
        static void Noise(float[] buf, double start, double dur, double amp, double lowCut, double highCut, double pan, Random rng, double attack = .001)
        {
            int n0 = (int)(start * Rate), len = (int)(dur * Rate);
            double aL = 1 - Math.Exp(-2 * Math.PI * highCut / Rate), aH = 1 - Math.Exp(-2 * Math.PI * lowCut / Rate);
            double lp = 0, hp = 0, gl = Math.Sqrt(.5 * (1 - pan)), gr = Math.Sqrt(.5 * (1 + pan));
            int frames = buf.Length / 2;
            for (int i = 0; i < len; i++)
            {
                int f = n0 + i; if (f >= frames) break;
                double white = rng.NextDouble() * 2 - 1;
                lp += aL * (white - lp); hp += aH * (lp - hp);
                double t = i / (double)Rate;
                double env = Math.Min(1, t / attack) * Math.Exp(-t / (dur * .25));
                double v = (lp - hp) * env * amp;
                if (f < 0) continue;
                buf[2 * f] += (float)(v * gl); buf[2 * f + 1] += (float)(v * gr);
            }
        }

        /// A low thump: a sine whose pitch falls from f0 to f1.
        static void Thump(float[] buf, double start, double f0, double f1, double dur, double amp, double pan)
        {
            int n0 = (int)(start * Rate), len = (int)(dur * Rate); double ph = 0;
            double gl = Math.Sqrt(.5 * (1 - pan)), gr = Math.Sqrt(.5 * (1 + pan));
            int frames = buf.Length / 2;
            for (int i = 0; i < len; i++)
            {
                int f = n0 + i; if (f >= frames) break;
                double t = i / (double)Rate, u = t / dur;
                ph += 2 * Math.PI * (f1 + (f0 - f1) * Math.Exp(-u * 6)) / Rate;
                double v = Math.Sin(ph) * Math.Exp(-u * 5) * Math.Min(1, t / .002) * amp;
                if (f < 0) continue;
                buf[2 * f] += (float)(v * gl); buf[2 * f + 1] += (float)(v * gr);
            }
        }

        // ------------------------------------------------------------------ the impacts

        /// A pin's own clack. `pitch` ~1 (each pin rings a little differently), `bright` 0..1 (hard hits ring higher).
        static void Clack(float[] buf, double t, double amp, double pitch, double bright, double pan, Random rng)
        {
            double[] f = { 980, 1640, 2380, 3150, 4300, 5900, 7600 };
            double[] d = { .070, .055, .045, .035, .026, .020, .014 };
            double[] a = { 1, .9, .8, .7, .55, .4, .25 };
            for (int i = 0; i < f.Length; i++)
            {
                double ff = f[i] * pitch * (1 + (rng.NextDouble() - .5) * .03);
                double aa = a[i] * (i < 2 ? 1 : .35 + .65 * bright);
                Mode(buf, t, ff, d[i], amp * aa * .5, pan);
            }
            Noise(buf, t, .014, amp * .9, 2000, 12000, pan, rng);   // the contact click
        }

        static double Pan(float x) => Math.Max(-.7, Math.Min(.7, x / 1.4));

        /// One impact into `buf` (seconds `t`). Strength is the speed jump in m/s.
        public static void Impact(float[] buf, double t, ImpactKind kind, float strength, float x, int pin, Random rng)
        {
            double s = Math.Min(1.4, strength / 4.0);                  // ~4 m/s is a full-blooded hit
            double amp = Math.Pow(s, .75), pan = Pan(x), pitch = .94 + ((pin * 7) % 11) * .012;
            double bright = Math.Min(1, s * 1.3);
            switch (kind)
            {
                case ImpactKind.BallPin:
                    Thump(buf, t, 190, 85, .16, amp * .55, pan);
                    Clack(buf, t, amp * 1.15, pitch, 1, pan, rng);
                    Noise(buf, t, .09, amp * .35, 300, 4000, pan, rng);
                    break;
                case ImpactKind.PinPin:
                    Clack(buf, t, amp, pitch, bright, pan, rng);
                    break;
                case ImpactKind.PinDeck:
                    Mode(buf, t, 310 * pitch, .055, amp * .5, pan); Mode(buf, t, 640 * pitch, .04, amp * .35, pan); Mode(buf, t, 1120, .03, amp * .2, pan);
                    Clack(buf, t, amp * .45, pitch, bright * .6, pan, rng);
                    break;
                case ImpactKind.PinKickback:
                    Mode(buf, t, 180, .12, amp * .45, pan); Mode(buf, t, 420, .09, amp * .35, pan); Mode(buf, t, 760, .06, amp * .25, pan);
                    Clack(buf, t, amp * .6, pitch, bright * .8, pan, rng);
                    break;
                case ImpactKind.PinPit:
                    Thump(buf, t, 120, 60, .12, amp * .35, pan); Noise(buf, t, .1, amp * .2, 80, 900, pan, rng);
                    break;
                case ImpactKind.BallPit:
                    Thump(buf, t, 95, 45, .3, Math.Max(.4, amp) * .8, pan); Noise(buf, t, .25, .35, 60, 700, pan, rng, .01);
                    break;
            }
        }

        // ------------------------------------------------------------------ the crash

        /// The whole pin action as sound: impacts, the rumble of the cascade, a strike sweetener, the room.
        public static float[] Crash(IList<PinImpact> impacts, float length, bool strike, Room room, int seed)
        {
            var rng = new Random(seed);
            var buf = new float[(int)((length + 1.2f) * Rate) * 2];
            foreach (var i in impacts) Impact(buf, i.Time, i.Kind, i.Strength, i.X, i.Pin, rng);

            // The rumble: hit energy per 20 ms, smoothed, drives low-mid noise (the crash's body).
            int bins = (int)(length / .02f) + 2; var energy = new double[bins];
            foreach (var i in impacts) { int b = Math.Min(bins - 1, (int)(i.Time / .02f)); energy[b] += Math.Min(1.4, i.Strength / 4.0); }
            double smooth = 0, lp = 0, a = 1 - Math.Exp(-2 * Math.PI * 2200.0 / Rate), hp = 0, ah = 1 - Math.Exp(-2 * Math.PI * 220.0 / Rate);
            int frames = buf.Length / 2;
            for (int f = 0; f < frames; f++)
            {
                int b = Math.Min(bins - 1, f / (int)(.02f * Rate));
                smooth += ((f % (int)(.02f * Rate) == 0 ? energy[b] : 0) - smooth * .00035);
                double white = rng.NextDouble() * 2 - 1; lp += a * (white - lp); hp += ah * (lp - hp);
                double v = (lp - hp) * Math.Min(1.2, smooth) * .12;
                buf[2 * f] += (float)v; buf[2 * f + 1] += (float)v;
            }

            if (strike)
            {
                // the sweetener: a crisp spray of extra clacks on the main burst and a bright splash
                double t0 = impacts.Count > 0 ? impacts[0].Time : 0;
                for (int k = 0; k < 14; k++)
                    Clack(buf, t0 + .02 + rng.NextDouble() * .22, .25 + rng.NextDouble() * .35, .9 + rng.NextDouble() * .25, 1, (rng.NextDouble() - .5) * 1.2, rng);
                Noise(buf, t0 + .01, .45, .32, 1500, 9000, -.3, rng, .004); Noise(buf, t0 + .015, .45, .32, 1500, 9000, .3, rng, .004);
            }
            Reverb(buf, room);
            Normalise(buf, .9f, strike ? 1f : Math.Min(1f, .55f + .45f * (float)Math.Sqrt(Count(impacts) / 25.0)));
            return buf;
        }

        static int Count(IList<PinImpact> impacts) { int n = 0; foreach (var i in impacts) if (i.Strength > .6f) n++; return n; }

        /// A synthetic crash for the neighbouring lanes (no pin action to read): a ball hit and a cascade.
        public static float[] NeighbourCrash(int seed, Room room)
        {
            var rng = new Random(seed);
            var list = new List<PinImpact>();
            int pins = 4 + rng.Next(7);
            list.Add(new PinImpact { Time = .05f, Kind = ImpactKind.BallPin, Strength = 5f, X = 0, Pin = 1 });
            for (int i = 0; i < pins * 3; i++)
                list.Add(new PinImpact { Time = .06f + (float)(rng.NextDouble() * rng.NextDouble()) * 1.1f, Kind = rng.NextDouble() < .5 ? ImpactKind.PinPin : rng.NextDouble() < .6 ? ImpactKind.PinDeck : ImpactKind.PinKickback, Strength = 1 + (float)rng.NextDouble() * 4, X = (float)(rng.NextDouble() - .5f) * .9f, Pin = 1 + rng.Next(10) });
            list.Sort((p, q) => p.Time.CompareTo(q.Time));
            var buf = Crash(list, 2f, pins >= 10, room, seed + 1);
            LowPass(buf, 2400);   // a lane or two away: duller
            return buf;
        }

        // ------------------------------------------------------------------ the crash from real recordings

        /// The recorded sound kit (Resources/Audio/v2/sfx/bowling, cut from CC0/CC-BY recordings by
        /// work/bowling/audio/kit.py), as interleaved stereo at 44.1 kHz.
        public sealed class Kit
        {
            public float[][] PinHits, BallHits, Crashes, Wobbles, Landings;
            public bool Ready => PinHits != null && PinHits.Length > 0;
        }

        /// Adds `grain` at `t` seconds: gain, pan, playback rate (pitch) and an optional low-pass.
        static void Grain(float[] buf, float[] grain, double t, double gain, double pan, double rate, double lowpass = 0)
        {
            if (grain == null || grain.Length < 4 || gain <= 0) return;
            int frames = buf.Length / 2, gf = grain.Length / 2, n0 = (int)(t * Rate);
            double gl = Math.Sqrt(.5 * (1 - pan)) * Math.Sqrt(2), gr = Math.Sqrt(.5 * (1 + pan)) * Math.Sqrt(2);
            double a = lowpass > 0 ? 1 - Math.Exp(-2 * Math.PI * lowpass / Rate) : 1, l = 0, r = 0;
            for (int i = 0; ; i++)
            {
                double p = i * rate; int k = (int)p; if (k + 1 >= gf) break;
                int f = n0 + i; if (f >= frames) break;
                double u = p - k;
                double sl = grain[2 * k] * (1 - u) + grain[2 * k + 2] * u, sr = grain[2 * k + 1] * (1 - u) + grain[2 * k + 3] * u;
                l += a * (sl - l); r += a * (sr - r);
                if (f < 0) continue;
                buf[2 * f] += (float)(l * gain * gl); buf[2 * f + 1] += (float)(r * gain * gr);
            }
        }

        /// The pin action as sound, from real recordings: every impact the physics found triggers a real
        /// grain (a pin knock, the ball meeting a pin, a pin dropping into the pit), and a real crash
        /// recording sits under the first hit, as loud as the number of pins going down calls for.
        /// `knocked` and `strike` come from the pin action; standing pins that were hit wobble.
        public static float[] Mix(IList<PinImpact> impacts, float length, int knocked, bool strike, int standingHitPins, Room room, Kit kit, int seed)
        {
            var rng = new Random(seed);
            var buf = new float[(int)((length + 1.8f) * Rate) * 2];
            float[] Pick(float[][] set) => set == null || set.Length == 0 ? null : set[rng.Next(set.Length)];
            double first = -1;
            foreach (var i in impacts)
            {
                double s = Math.Min(1.3, i.Strength / 4.0), amp = Math.Pow(s, .8), pan = Pan(i.X);
                double rate = .93 + rng.NextDouble() * .16;                 // no two knocks the same
                switch (i.Kind)
                {
                    case ImpactKind.BallPin:
                        if (first < 0) first = i.Time;
                        Grain(buf, Pick(kit.BallHits), i.Time, .9 * Math.Max(.5, amp), pan, 1);
                        Grain(buf, Pick(kit.PinHits), i.Time + .002, .55 * amp, pan, rate, 6500);
                        break;
                    case ImpactKind.PinPin: Grain(buf, Pick(kit.PinHits), i.Time, .6 * amp, pan, rate, 6500); break;
                    case ImpactKind.PinKickback: Grain(buf, Pick(kit.PinHits), i.Time, .6 * amp, pan, rate * .88, 3500); break;
                    case ImpactKind.PinDeck: Grain(buf, Pick(kit.PinHits), i.Time, .55 * amp, pan, rate * .82, 2600); break;
                    case ImpactKind.PinPit: Grain(buf, Pick(kit.PinHits), i.Time, .3 * amp, pan, rate * .72, 1300); break;
                    case ImpactKind.BallPit: Grain(buf, Pick(kit.Landings), i.Time, .55, pan, .78, 900); break;
                }
            }
            // the roar: a real crash under the first hit, scaled (and darkened) by how many pins go
            if (first >= 0 && knocked >= 2 && kit.Crashes != null && kit.Crashes.Length > 0)
            {
                double k = Math.Min(1, knocked / 10.0);
                double gain = strike ? 1.0 : .2 + .65 * k * k;
                int c0 = rng.Next(kit.Crashes.Length);
                Grain(buf, kit.Crashes[c0], first - .004, gain, (rng.NextDouble() - .5) * .2, .96 + rng.NextDouble() * .08, strike ? 0 : 2500 + 6000 * k);
                // a strike is two crashes deep: a second real crash a beat later, darker, for the body
                if (strike && kit.Crashes.Length > 1)
                    Grain(buf, kit.Crashes[(c0 + 1 + rng.Next(kit.Crashes.Length - 1)) % kit.Crashes.Length], first + .025, .65, (rng.NextDouble() - .5) * .3, .9, 3000);
            }
            // a pin that took a knock but stayed up rocks on its base
            for (int p = 0; p < standingHitPins && p < 2; p++)
                Grain(buf, Pick(kit.Wobbles), (first < 0 ? 0 : first) + .35 + p * .25 + rng.NextDouble() * .2, .35, (rng.NextDouble() - .5) * .6, 1);
            if (room == Room.Cave) Reverb(buf, room);
            Normalise(buf, .92f, strike ? 1f : (float)Math.Min(1, .5 + .5 * Math.Sqrt(knocked / 9.0)));
            return buf;
        }

        // ------------------------------------------------------------------ the other sounds

        /// The ball rolling: a seamless loop of low rumble with the faint thump of the finger holes.
        public static float[] RollLoop(float seconds = 4)
        {
            var rng = new Random(3); int n = (int)(seconds * Rate); var buf = new float[n * 2];
            // two cascaded low-passes (12 dB/oct) for the rumble, a little lane "hiss" band on top
            double lp1 = 0, lp1b = 0, lp2 = 0, lp2b = 0, a1 = 1 - Math.Exp(-2 * Math.PI * 170.0 / Rate), a2 = 1 - Math.Exp(-2 * Math.PI * 700.0 / Rate);
            for (int f = 0; f < n; f++)
            {
                double w = rng.NextDouble() * 2 - 1; lp1 += a1 * (w - lp1); lp1b += a1 * (lp1 - lp1b); lp2 += a2 * (w - lp2); lp2b += a2 * (lp2 - lp2b);
                double t = f / (double)Rate;
                double holes = 1 + .18 * Math.Sin(2 * Math.PI * 5 * t);            // ~5 revs a second
                double v = (lp1b * 5 + (lp2b - lp1b) * .35) * holes;
                buf[2 * f] = (float)v; buf[2 * f + 1] = (float)v;
            }
            buf = Loop(buf, .3f); Normalise(buf, .7f, 1);
            return buf;
        }

        /// In the gutter: a hollow rattle (the ball knocking the channel's sides).
        public static float[] GutterLoop(float seconds = 3)
        {
            var rng = new Random(5); int n = (int)(seconds * Rate); var buf = new float[n * 2];
            double lp = 0, hp = 0, a = 1 - Math.Exp(-2 * Math.PI * 900.0 / Rate), ah = 1 - Math.Exp(-2 * Math.PI * 180.0 / Rate);
            for (int f = 0; f < n; f++)
            {
                double w = rng.NextDouble() * 2 - 1; lp += a * (w - lp); hp += ah * (lp - hp);
                buf[2 * f] = buf[2 * f + 1] = (float)((lp - hp) * 1.4);
            }
            for (double t = .03; t < seconds - .2; t += .05 + rng.NextDouble() * .16)
            {
                double pan = (rng.NextDouble() - .5) * .3;
                Mode(buf, t, 260 + rng.NextDouble() * 60, .05, .35, pan); Mode(buf, t, 610 + rng.NextDouble() * 90, .035, .2, pan);
            }
            buf = Loop(buf, .25f); Normalise(buf, .7f, 1);
            return buf;
        }

        /// The ball landing on the lane (a loft is a louder, deeper drop).
        public static float[] Landing(float loft)
        {
            var rng = new Random(7); var buf = new float[(int)(.6 * Rate) * 2];
            double s = Math.Min(1, .35 + loft * 1.6);
            Thump(buf, 0, 150, 60, .22, .9 * s, 0); Mode(buf, 0, 420, .06, .25 * s, 0); Noise(buf, 0, .05, .3 * s, 200, 3000, 0, rng);
            Normalise(buf, .85f, (float)s);
            return buf;
        }

        /// The foul buzzer: two detuned square-ish tones, a short stab.
        public static float[] Buzzer()
        {
            int n = (int)(.9 * Rate); var buf = new float[n * 2]; double p1 = 0, p2 = 0, lp = 0, a = 1 - Math.Exp(-2 * Math.PI * 2500.0 / Rate);
            for (int f = 0; f < n; f++)
            {
                double t = f / (double)Rate; p1 += 2 * Math.PI * 220 / Rate; p2 += 2 * Math.PI * 233 / Rate;
                double sq = Math.Tanh(4 * Math.Sin(p1)) + Math.Tanh(4 * Math.Sin(p2));
                lp += a * (sq - lp);
                double env = Math.Min(1, t / .01) * (t > .8 ? (0.9 - t) / .1 : 1);
                buf[2 * f] = buf[2 * f + 1] = (float)(lp * .35 * env);
            }
            return buf;
        }

        /// The pinsetter: a clank as the sweep bar drops, the motor's whir, a clank as it lifts.
        public static float[] Sweep(Room room)
        {
            var rng = new Random(9); double dur = 2.2; var buf = new float[(int)((dur + .8) * Rate) * 2];
            void Clank(double t, double amp) { double[] f = { 520, 1340, 2780, 4100 }; for (int i = 0; i < f.Length; i++) Mode(buf, t, f[i] * (1 + (rng.NextDouble() - .5) * .02), .28 / (1 + i * .6), amp / (1 + i), 0); Noise(buf, t, .03, amp * .5, 1200, 7000, 0, rng); }
            Clank(0, .5); Clank(dur - .25, .4);
            double ph = 0, lp = 0, a = 1 - Math.Exp(-2 * Math.PI * 500.0 / Rate);
            int n = (int)(dur * Rate);
            for (int f = 0; f < n; f++)
            {
                double t = f / (double)Rate; ph += 2 * Math.PI * (62 + 8 * Math.Sin(t * 2.1)) / Rate;
                double saw = (ph / Math.PI % 2) - 1 + (rng.NextDouble() - .5) * .3;
                lp += a * (saw - lp);
                double env = Math.Min(1, t / .25) * Math.Min(1, (dur - t) / .3);
                buf[2 * f] += (float)(lp * .22 * env); buf[2 * f + 1] += (float)(lp * .22 * env);
            }
            Reverb(buf, room); Normalise(buf, .6f, 1);
            return buf;
        }

        /// The ball return: the air blower's whoosh, then the ball knocking into the rack.
        public static float[] BallReturn()
        {
            var rng = new Random(11); var buf = new float[(int)(1.6 * Rate) * 2];
            Noise(buf, 0, .9, .45, 60, 900, -.2, rng, .25);
            Thump(buf, .85, 140, 70, .2, .8, -.2); Mode(buf, .85, 380, .07, .3, -.2); Mode(buf, .85, 1150, .03, .15, -.2);
            Thump(buf, 1.05, 120, 70, .12, .3, -.2);
            Normalise(buf, .75f, 1);
            return buf;
        }

        /// The release whoosh: the ball's swing through the air, brighter and louder with speed.
        public static float[] Whoosh(float speed01)
        {
            var rng = new Random(13); var buf = new float[(int)(.5 * Rate) * 2];
            Noise(buf, 0, .45, .5, 300 + 400 * speed01, 1800 + 3000 * speed01, .15, rng, .14);
            Normalise(buf, .6f, .4f + .6f * speed01);
            return buf;
        }

        // ------------------------------------------------------------------ post

        /// A small Schroeder reverb (4 combs, 2 all-passes), mixed in place.
        static void Reverb(float[] buf, Room room)
        {
            var (wet, fb, size) = RoomSpec(room);
            int[] combs = { 1557, 1617, 1491, 1422 }; int[] aps = { 225, 556 };
            int frames = buf.Length / 2;
            for (int ch = 0; ch < 2; ch++)
            {
                var outp = new float[frames];
                foreach (int c0 in combs)
                {
                    int d = (int)(c0 * size) + ch * 23; var line = new float[d]; int idx = 0; float damp = 0;
                    for (int f = 0; f < frames; f++)
                    {
                        float y = line[idx]; damp = y * .7f + damp * .3f;
                        line[idx] = buf[2 * f + ch] + damp * fb; idx = (idx + 1) % d;
                        outp[f] += y * .25f;
                    }
                }
                foreach (int a0 in aps)
                {
                    int d = (int)(a0 * size); var line = new float[d]; int idx = 0;
                    for (int f = 0; f < frames; f++) { float b = line[idx], x = outp[f]; float y = -x + b; line[idx] = x + b * .5f; idx = (idx + 1) % d; outp[f] = y; }
                }
                for (int f = 0; f < frames; f++) buf[2 * f + ch] = buf[2 * f + ch] * (1 - wet * .5f) + outp[f] * wet;
            }
        }

        static void LowPass(float[] buf, double cut)
        {
            double a = 1 - Math.Exp(-2 * Math.PI * cut / Rate), l = 0, r = 0;
            for (int f = 0; f < buf.Length / 2; f++) { l += a * (buf[2 * f] - l); r += a * (buf[2 * f + 1] - r); buf[2 * f] = (float)l; buf[2 * f + 1] = (float)r; }
        }

        /// A seamless loop: the last `seconds` are faded into the start and cut off.
        static float[] Loop(float[] buf, float seconds)
        {
            int frames = buf.Length / 2, n = (int)(seconds * Rate);
            var o = new float[(frames - n) * 2];
            for (int i = 0; i < frames - n; i++)
                for (int ch = 0; ch < 2; ch++)
                {
                    float v = buf[2 * i + ch];
                    if (i < n) { float u = i / (float)n; v = v * u + buf[2 * (frames - n + i) + ch] * (1 - u); }
                    o[2 * i + ch] = v;
                }
            return o;
        }

        /// Scales to `peak` × `loudness`, with a soft knee above 0.8 so a monster strike never hard-clips.
        static void Normalise(float[] buf, float peak, float loudness)
        {
            float max = 1e-6f; foreach (var v in buf) max = Math.Max(max, Math.Abs(v));
            float g = peak * loudness / max;
            for (int i = 0; i < buf.Length; i++)
            {
                float x = buf[i] * g, ax = Math.Abs(x);
                buf[i] = ax < .8f ? x : Math.Sign(x) * (.8f + .2f * (float)Math.Tanh((ax - .8f) / .2f));
            }
        }

        /// 16-bit PCM WAV bytes (offline proof renders).
        public static byte[] Wav(float[] stereo)
        {
            int frames = stereo.Length / 2; var ms = new System.IO.MemoryStream(); var w = new System.IO.BinaryWriter(ms);
            w.Write(System.Text.Encoding.ASCII.GetBytes("RIFF")); w.Write(36 + frames * 4); w.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt "));
            w.Write(16); w.Write((short)1); w.Write((short)2); w.Write(Rate); w.Write(Rate * 4); w.Write((short)4); w.Write((short)16);
            w.Write(System.Text.Encoding.ASCII.GetBytes("data")); w.Write(frames * 4);
            foreach (var v in stereo) w.Write((short)Math.Max(-32767, Math.Min(32767, v * 32767)));
            return ms.ToArray();
        }
    }
}
