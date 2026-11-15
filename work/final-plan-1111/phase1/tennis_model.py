#!/usr/bin/env python3
"""Numeric copy of the tennis ball model (TennisBall.cs, TennisRules.RallyVelocity / RallyArcVelocity /
PlanIntercept) for tuning Phase 1 of PLAN_FinalLook_Gameplay_2026-11-11.md without a Unity launch.

  python3 tennis_model.py            # today's numbers next to the candidate
Times are GAME seconds unless marked real (real = game / GameSpeed 1.1).
"""
import math, sys
from dataclasses import dataclass

G, MAGNUS, STEP = 9.81, .16, 1 / 120
BALL_R, NET_H = .10, .97
HALF_LEN, HALF_W = 11.885, 4.115
BASELINE_Z = -11.2
GAME_SPEED = 1.1
RUN_SPEED, ACCEL, REACTION, STROKE_REACH = 5.6, 16.0, .15, 1.35


@dataclass
class Model:
    name: str
    slow: float; mid: float; fast: float          # TimingPace
    clearance: float                              # RallyNetClearance (player, clean hit)
    cpu_clearance: float                          # SendFromOpponent
    restitution: float                            # bounceRestitution for rally balls
    along: float                                  # horizontal speed kept at the bounce (flat ball)
    deep: float                                   # SwingPlacement straight depth on a clean hit
    side_deep: float
    short: float                                  # SwingPlacement depth on a poor hit
    wii_pace: float; min_rally: float             # TennisOpponent
    lob_apex: float
    cpu_depth_scale: float = 1.0
    cpu_base: float = 0.0                         # >0: CPU pace = cpu_base + (old pace - 13) * cpu_k
    cpu_k: float = 0.0
    top_kick: float = .10                         # extra vertical bounce per unit of topspin
    max_flight: float = 0.0                       # >0: a CPU drive is sped up until it reaches its bounce within this
    speed_floor: float = 12.0                     # TennisBall.Solve's max(12, speed)


TODAY = Model("today", 10, 13, 17.5, 1.1, .9, .75, .94, 10.4, 8.0, 6.2, .66, 13, 4.4)


def integrate(p, v, spin, dt):
    h = math.hypot(v[0], v[2])
    a = (0.0, -G - MAGNUS * spin * h, 0.0)
    p = [p[i] + v[i] * dt + a[i] * .5 * dt * dt for i in range(3)]
    v = [v[i] + a[i] * dt for i in range(3)]
    return p, v


def bounce(v, spin, m: Model, restitution=None):
    r = m.restitution if restitution is None else restitution
    s = max(-1, min(1, spin))
    vertical = max(.3, min(.95, r + (m.top_kick if s > 0 else .14) * s))
    along = m.along + (.05 if s > 0 else .04) * s
    return [v[0] * along, -v[1] * vertical, v[2] * along], s * .45


def solve(start, target, speed, spin, m: Model):
    d = [target[i] - start[i] for i in range(3)]
    horizontal = math.hypot(d[0], d[2])
    flight = max(.25, horizontal / max(m.speed_floor, speed))
    v = [d[0] / flight, 0, d[2] / flight]
    hs = math.hypot(v[0], v[2])
    v[1] = (d[1] + .5 * G * flight * flight + MAGNUS * spin * hs * .5 * flight * flight) / flight
    return v


def net_clearance(start, v, spin):
    p, v = list(start), list(v)
    for _ in range(600):
        b = p
        p, v = integrate(p, v, spin, STEP)
        if b[2] * p[2] <= 0:
            t = 0 if abs(p[2] - b[2]) < 1e-6 else -b[2] / (p[2] - b[2])
            return b[1] + (p[1] - b[1]) * max(0, min(1, t))
        if p[1] < BALL_R and v[1] < 0: return 0
    return 0


def lofted(start, target, speed, spin, margin, m: Model, floor=9, k=.93):
    best = solve(start, target, speed, spin, m)
    s = speed
    while s > floor:
        best = solve(start, target, s, spin, m)
        if net_clearance(start, best, spin) > NET_H + margin: return best
        s *= k
    return best


def rally_velocity(start, target, speed, spin, quality, m: Model):
    margin = .22 + (m.clearance - .22) * max(0, min(1, quality / .7))
    return lofted(start, target, speed, spin, margin, m, 9, .93)


def lob_velocity(start, target, apex):
    apex = max(apex, start[1] + .5)
    up = math.sqrt(2 * G * (apex - start[1]))
    dur = up / G + math.sqrt(2 * (apex - target[1]) / G)
    v = [(target[i] - start[i]) / dur for i in range(3)]; v[1] = up
    return v


def coverable(seconds, top):
    if seconds <= 0: return 0
    ramp = top / ACCEL
    return .5 * ACCEL * seconds * seconds if seconds <= ramp else .5 * ACCEL * ramp * ramp + (seconds - ramp) * top


def plan_intercept(p, v, spin, m: Model, player=(0, BASELINE_Z)):
    """TennisRules.PlanIntercept for a receiver on the NEGATIVE-z side. Returns (time, point, speed) or None."""
    best, best_score, bounces, time, bounce_z = None, 1e9, 0, 0.0, 0.0
    dt = STEP * 2
    p, v = list(p), list(v)
    for _ in range(360):
        n, nv = integrate(p, v, spin, dt)
        if n[1] < BALL_R and nv[1] < 0:
            n[1] = BALL_R; nv, spin = bounce(nv, spin, m)
            bounces += 1
            if bounces >= 2: break
            bounce_z = n[2]
        p, v = n, nv; time += dt
        if p[2] > -.6 or v[2] > 0: continue
        if p[2] < -15.5: break
        h = p[1]; volley = bounces == 0
        if volley and h < 1.9: continue
        if h < .3 or h > 2.3: continue
        at = (p[0], p[2] - .65)
        travel = math.hypot(at[0] - player[0], at[1] - player[1])
        if travel - coverable(time - REACTION, RUN_SPEED) > STROKE_REACH: continue
        pref = player[1] if volley else max(-12.6, min(-3, bounce_z - 2.8 - .65))
        comfort = abs(h - 1.0) * 1.2 + abs(at[1] - pref) * .18 + travel * .06
        if comfort < best_score:
            best_score, best = comfort, (time, list(p), math.hypot(v[0], v[2]))
    return best


def fly(start, v, spin, m: Model):
    """Peak, time to first bounce, landing, second-arc peak, time between bounces."""
    p, v = list(start), list(v); t = 0; peak = p[1]
    for _ in range(2000):
        p, v = integrate(p, v, spin, STEP); t += STEP; peak = max(peak, p[1])
        if p[1] < BALL_R and v[1] < 0: break
    land, t1, vin = list(p), t, math.hypot(v[0], v[2])
    p[1] = BALL_R; v, spin = bounce(v, spin, m)
    vout = math.hypot(v[0], v[2]); peak2 = 0; t = 0
    for _ in range(2000):
        p, v = integrate(p, v, spin, STEP); t += STEP; peak2 = max(peak2, p[1])
        if p[1] < BALL_R and v[1] < 0: break
    return dict(peak=peak, t1=t1, land=land, peak2=peak2, t2=t, vin=vin, vout=vout, second=list(p))


def smooth(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


def timing_pace(t, m: Model, power=.6, stamina=1):
    t = max(0, min(1, t))
    pace = m.slow + (m.mid - m.slow) * t / .55 if t < .55 else m.mid + (m.fast - m.mid) * ((t - .55) / .45) ** 1.3
    return pace * (.95 + .10 * power) * (.92 + .08 * stamina)


def swing_placement(side, quality, m: Model):
    c = smooth(quality / .85)
    width = 2.4 + (3.95 - 2.4) * c
    z = m.short + ((m.side_deep if side else m.deep) - m.short) * c
    return [side * width, BALL_R, max(2.8, min(HALF_LEN - .3, z))]


def mirror(p):  # the player's shot seen by a receiver on the negative side
    return [-p[0], p[1], -p[2]]


def player_shot(q, side, m: Model, spin=.35, contact_y=1.0):
    start = [0, contact_y, BASELINE_Z + .3]
    target = swing_placement(side, q, m)
    v = rally_velocity(start, target, timing_pace(q, m), spin, q, m)
    f = fly(start, v, spin, m)
    hit = plan_intercept(mirror(start), mirror(v), spin, m)
    return f, hit, math.hypot(v[0], v[2])


def cpu_shot(depth, speed, spin, m: Model, kind="drive", from_y=1.15):
    start = [0, from_y, 10.6]
    target = [1.5, BALL_R, -max(2.4, min(11.3, depth * m.cpu_depth_scale))]
    if m.max_flight > 0: speed = max(speed, math.hypot(target[0] - start[0], target[2] - start[2]) / m.max_flight)
    if kind == "lob": v = lob_velocity(start, target, m.lob_apex); spin = 0
    else: v = lofted(start, target, speed, spin, m.cpu_clearance, m, 8, .94)
    f = fly(start, v, spin, m)
    hit = plan_intercept(start, v, spin, m)
    return f, hit, math.hypot(v[0], v[2])


def row(label, f, hit, v0):
    if hit: h = f"{hit[0]:5.2f} ({hit[0] / GAME_SPEED:4.2f} real)  y={hit[1][1]:4.2f} z={abs(hit[1][2]):5.2f} v={hit[2]:4.1f}"
    else: h = "  -- no reachable contact --"
    return (f"  {label:<26} v0={v0:5.1f}  peak={f['peak']:4.2f}  bounce@{abs(f['land'][2]):5.2f} t={f['t1']:4.2f}"
            f"  kept {f['vout']:4.1f}/{f['vin']:4.1f}  2nd peak={f['peak2']:4.2f}  2nd@{abs(f['second'][2]):5.2f}  contact {h}")


def report(m: Model):
    print(f"== {m.name}: pace {m.slow}/{m.mid}/{m.fast}  clear {m.clearance}/{m.cpu_clearance}  rest {m.restitution}  along {m.along}"
          f"  depth {m.short}-{m.deep} (side {m.side_deep})  cpu x{m.wii_pace} min {m.min_rally} lob {m.lob_apex}")
    for label, q in (("PERFECT straight", 1.0), ("GREAT straight", .8), ("middle straight", .55), ("poor straight", .3), ("edge straight", .08)):
        print(row(label, *player_shot(q, 0, m)))
    for label, q in (("PERFECT side", 1.0), ("middle side", .55)):
        print(row(label, *player_shot(q, 1, m)))
    print(row("PERFECT topspin", *player_shot(1.0, 0, m, spin=.9)))
    print(row("middle slice", *player_shot(.55, 0, m, spin=-.8)))
    for label, pace, depth, spin in (("CPU rookie deep", 22, 9.5, .3), ("CPU rookie short", 18.5, 6.5, .1), ("CPU mid deep", 25, 10.2, .5),
                                     ("CPU pro deep", 28, 10.8, .9), ("CPU pro mid", 24, 8.5, .4), ("CPU ace deep", 30, 11.0, .9)):
        speed = max(m.min_rally, max(18.5, pace) * m.wii_pace)
        if m.cpu_base > 0: speed = m.cpu_base + (max(13, max(18.5, pace) * .66) - 13) * m.cpu_k
        print(row(label, *cpu_shot(depth, speed, spin, m)))
    print(row("CPU lob", *cpu_shot(10.6, 16, 0, m, "lob")))
    print()


if __name__ == "__main__":
    report(TODAY)
    for arg in sys.argv[1:]:
        vals = [float(x) for x in arg.split(",")]
        report(Model("candidate", *vals))
