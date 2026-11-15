#!/usr/bin/env python3
"""Numeric copy of the golf flight (Shot/BallFlight.cs) with the 2026-11-11 landing model, for tuning Phase 1 of
PLAN_FinalLook_Gameplay_2026-11-11.md without a Unity launch.

  python3 golf_model.py            # every club's full shot onto each surface, old landing next to new
Units: SI inside, yards in the tables.
"""
import math, sys
from dataclasses import dataclass

YD = 0.9144
R = 0.02135
CLUBS = {  # name: (reference yards, smash, launch deg, spin rpm, rated by total)
    "Driver": (240, 1.46, 12.5, 2600, False), "Hybrid": (190, 1.42, 16, 4600, False), "5 Iron": (175, 1.37, 15.5, 5300, False),
    "7 Iron": (150, 1.33, 18.5, 6800, False), "9 Iron": (125, 1.28, 23, 8200, False), "PW": (100, 1.23, 27, 9000, False),
    "SW": (80, 1.18, 32, 9800, False), "LW": (50, 1.12, 42, 10200, False), "Chipper": (25, 1.08, 8, 1200, True),
}


@dataclass
class Surface:
    name: str
    firm: float      # restitution of a slow, square bounce (0 dead .. ~.5 lively)
    give: float      # how fast the bounce dies with impact speed (per m/s): the pitch mark
    mu: float        # friction between ball and ground during the bounce
    take: float      # 0..1 share of the pace along the ground the turf simply absorbs at each bounce
    dead: float      # 0..1 share of the hop it swallows (sand, deep rough)
    bite: float      # how hard backspin grips: 1 = a solid ball on a hard floor, more on a receptive green
    roll: float      # rolling deceleration, m/s^2 (the course re-rolls on its own numbers; this is BallFlight's flat one)


NEW = {   # the game's table: Course/Hole.cs CourseLies.Ground and Shot/BallFlight.cs Turf.Fairway
    "tee":     Surface("tee",     .46, .016, .42, .20, 0,   1.0, 3.2),
    "fairway": Surface("fairway", .44, .016, .42, .22, 0,   1.0, 3.2),
    "fringe":  Surface("fringe",  .40, .016, .46, .26, 0,   1.1, 2.4),
    "green":   Surface("green",   .36, .016, .50, .30, 0,   1.25, 1.5),
    "rough":   Surface("rough",   .26, .012, .60, .50, .35, .5,  6.4),
    "bunker":  Surface("bunker",  .05, .0,   .90, .92, .9,  0,   19),
    "oob":     Surface("oob",     .30, .014, .55, .40, .2,  .6,  6.4),
}


def air(speed_mph, launch_deg, spin_rpm, dt=1 / 240):
    """Fly to the first touchdown on flat ground. Returns carry m, time, (vt, vn) at impact, spin rad/s, apex."""
    mass, area, rho = 0.04593, math.pi * R * R, 1.225
    v0 = speed_mph * 0.44704; el = math.radians(launch_deg)
    pz = py = 0.0; vz = math.cos(el) * v0; vy = math.sin(el) * v0
    spin = spin_rpm * 2 * math.pi / 60; t = 0; apex = 0
    while t < 16:
        v = math.hypot(vz, vy)
        ay, az = -9.81, 0.0
        if v > 0.01:
            sr = R * spin / v
            drag = 0.20 + 0.35 * sr; lift = min(0.32, 0.45 * sr ** 0.4)
            k = 0.5 * rho * area * v * v / mass
            dz, dy = vz / v, vy / v
            # backspin axis flat and perpendicular to travel: lift = axis x direction -> (ly, lz) = (dz, -dy)
            az += (-dz * drag + (-dy) * lift) * k
            ay += (-dy * drag + dz * lift) * k
            spin *= math.exp(-dt / 45)
        vz += az * dt; vy += ay * dt; pz += vz * dt; py += vy * dt; t += dt; apex = max(apex, py)
        if py <= 0 and vy < 0: return pz, t, vz, -vy, spin, apex
    return pz, t, vz, 0, spin, apex


def calibrate(club):
    ref, smash, ang, spin, total = CLUBS[club]
    lo, hi = 1.0, 145.0
    for _ in range(24):
        s = (lo + hi) / 2
        carry, t, vt, vn, sp, apex = air(s * smash, ang, spin)
        dist = carry + (land(vt, vn, sp, NEW["fairway"], model=MODEL)[0] if total else 0)
        if dist / YD < ref: lo = s
        else: hi = s
    return (lo + hi) / 2


def old_bounce(vt, vn, spin, soft=0, grab=0):
    rest = max(0.30, min(0.46, 0.46 - 0.006 * max(0, vn)))
    vy = vn * min(0.85, rest) * (1 - soft)
    grip = max(0.08, 0.6 - 0.5 * (spin * 60 / (2 * math.pi)) / 10000) * (1 - grab)
    return vt * grip, vy, 0.0


def new_bounce(vt, vn, spin, s: Surface, slope=0.0, p=None):
    """One bounce. vt along the ground in the travel direction (may be negative), vn into the ground (>0), spin = backspin rad/s.
    `slope` = rise per metre in the travel direction (uphill > 0). Returns (vt, vn_out, spin) in the level frame."""
    p = p or P
    # the slope: work in the ground's own frame
    a = math.atan(slope)
    vt_g = vt * math.cos(a) - vn * math.sin(a)            # into an upslope: less along it
    vn_g = vn * math.cos(a) + vt * math.sin(a)            # ... and more into it
    if vn_g <= 0: return vt, 0.0, spin
    # the pitch mark: a steep, hard landing digs in and the turf's reaction leans back against the ball
    steep = math.atan2(vn_g, abs(vt_g) + 1e-9)            # 0 skimming .. pi/2 straight down
    speed = math.hypot(vt_g, vn_g)
    dig = min(p.dig_max, p.dig * speed * (steep / (math.pi / 2)))   # radians the reaction tilts back
    c, sn = math.cos(dig), math.sin(dig)
    sign = 1 if vt_g >= 0 else -1
    vt_c = vt_g * c - sign * vn_g * sn                    # frame tilted back toward the incoming ball
    vn_c = vn_g * c + sign * vt_g * sn
    if vn_c <= 0: vt_c, vn_c = vt_g, vn_g
    e = max(p.e_min, s.firm - s.give * vn_c) * (1 - s.dead)
    vn_out = e * vn_c
    # friction with backspin (solid sphere): slip at the contact patch = vt + r*spin
    rs = R * spin * (s.bite if spin > 0 else 1)
    slip = vt_c + rs
    jmax = s.mu * (1 + e) * vn_c                          # the most friction can take out of the slip's linear part
    if abs(slip) <= 3.5 * jmax:                           # grips: leaves rolling
        vt_out = (5 * vt_c - 2 * rs) / 7
        spin_out = -vt_out / R
    else:                                                 # slides throughout
        d = math.copysign(jmax, slip)
        vt_out = vt_c - d
        spin_out = spin - 2.5 * d / R
    vt_out *= (1 - s.take)
    # back to the ground frame, then level
    vt_g2 = vt_out * c - sign * vn_out * sn              # the leaning reaction pushes back along the ground ...
    vn_g2 = vn_out * c + sign * vt_out * sn              # ... and the ball rides up the front of its own pitch mark
    if vn_g2 < 0: vn_g2 = 0
    vt_l = vt_g2 * math.cos(a) - vn_g2 * math.sin(a)
    vn_l = vn_g2 * math.cos(a) + vt_g2 * math.sin(a)
    return vt_l, max(0, vn_l), spin_out


@dataclass
class Params:
    dig: float = .010       # radians of lean per m/s of impact speed at a vertical landing
    dig_max: float = .32
    e_min: float = .10
    hop: float = 1.2        # m/s: below this the ball stays down and rolls
    spin_keep: float = 1.0  # share of spin that survives the flight model's decay into the first bounce


P = Params()
MODEL = "new"


def land(vt, vn, spin, s: Surface, slope=0.0, model="new", trace=None):
    """From first touchdown to rest on a uniform surface. Returns run m (signed), hops, first-hop height m, list of hop heights.
    `trace`: a list that receives (x m, height m) points of the path after touchdown (level ground only)."""
    x = 0.0; hops = []; t = 0
    for i in range(12):
        if model == "old":
            vt, vy, spin = old_bounce(vt, vn, spin)
        else:
            vt, vy, spin = new_bounce(vt, vn, spin, s, slope)
        if vy < P.hop: break
        # the hop (on a slope the ground rises under it: approximate with the level flight time)
        g = 9.81
        T = 2 * vy / g
        if slope != 0:
            # land where the parabola meets the inclined ground: y = vy t - g t^2/2 = slope * vt * t
            T = max(0, 2 * (vy - slope * vt) / g)
        hops.append(vy * vy / (2 * g))
        if trace is not None:
            for k in range(25): tt = T * k / 24; trace.append((x + vt * tt, vy * tt - .5 * g * tt * tt))
        x += vt * T
        vn = max(0, g * T - vy) if slope != 0 else vy
        if T <= 0: break
    # roll (on a slope gravity helps or hinders)
    decel = 3.2 if model == "old" else s.roll + 9.81 * slope * (1 if vt >= 0 else -1)
    if trace is not None: trace.append((x, 0))
    if decel > 0.05: x += math.copysign(vt * vt / (2 * decel), vt)
    else: x += math.copysign(60, vt)
    if trace is not None: trace.append((x, 0))
    return x, len(hops), (hops[0] if hops else 0), hops


def table(surfaces=("fairway", "green", "rough", "bunker"), power=1.0):
    print(f"{'club':8} {'carry':>5} {'land':>11} {'spin':>5} | {'OLD fairway':>22} | " + " | ".join(f"{n:>24}" for n in surfaces))
    for club, (ref, smash, ang, spin, total) in CLUBS.items():
        cs = calibrate(club) * power
        carry, t, vt, vn, sp, apex = air(cs * smash, ang, spin * power)
        o = land(vt, vn, sp, None, model="old")
        cells = []
        for n in surfaces:
            x, h, first, hops = land(vt, vn, sp, NEW[n])
            cells.append(f"{x / YD:+6.1f}yd {h}hop {first:4.2f}m")
        print(f"{club:8} {carry / YD:5.0f} {math.degrees(math.atan2(vn, vt)):4.0f}d{math.hypot(vt, vn):5.1f} {sp * 60 / (2 * math.pi):5.0f} | "
              f"{o[0] / YD:+6.1f}yd {o[1]}hop {o[2]:4.2f}m | " + " | ".join(f"{c:>24}" for c in cells))


if __name__ == "__main__":
    for kv in sys.argv[1:]:
        k, v = kv.split("=")
        if "." in k:
            sname, field = k.split("."); setattr(NEW[sname], field, float(v))
        else: setattr(P, k, float(v))
    table()
    print("\nslopes, new model (run yd): 7 Iron onto fairway / PW onto green, 6% up, level, 6% down")
    for club, surf in (("7 Iron", "fairway"), ("PW", "green"), ("Driver", "fairway")):
        ref, smash, ang, spin, total = CLUBS[club]; cs = calibrate(club)
        carry, t, vt, vn, sp, apex = air(cs * smash, ang, spin)
        print(f"  {club:7} {surf:8}", "  ".join(f"{sl:+.2f}: {land(vt, vn, sp, NEW[surf], sl)[0] / YD:+6.1f}yd" for sl in (.06, 0, -.06)))
