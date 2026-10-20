#!/usr/bin/env python3
"""trace_analyze.py proof/trace.csv : find pops in the puppet (per-frame jumps of hips / head / hands / feet / strings) and summarise by state."""
import csv, sys, math, collections
rows = list(csv.DictReader(open(sys.argv[1])))
def v3(s): return tuple(float(x) for x in s.split(';'))
def dist(a, b): return math.dist(a, b)
cols = ['hips', 'head', 'rightHand', 'leftHand', 'leftFoot', 'rightFoot', 'strings']
by = collections.defaultdict(list)
for r in rows: by[(r['scenario'], r['role'])].append(r)
FPS = 60.0
worst = []
for key, rs in by.items():
    for i in range(1, len(rs)):
        a, b = rs[i-1], rs[i]
        if int(b['frame']) != int(a['frame']) + 1: continue
        # actor travel is part of the pose (the hero rides the actor): measure relative to the actor
        ra, rb = v3(a['actor']), v3(b['actor'])
        for c in cols:
            pa, pb = v3(a[c]), v3(b[c])
            da = tuple(pa[k] - ra[k] for k in range(3)); db = tuple(pb[k] - rb[k] for k in range(3))
            d = dist(da, db) * FPS
            worst.append((d, key, c, int(b['frame']), a['state'], b['state'], a['clip'], b['clip'], float(b['clipTime'])))
worst.sort(reverse=True)
print("fastest per-frame point motions (m/s, relative to the actor) - top 25")
for w in worst[:25]:
    print(f"  {w[0]:7.1f} m/s {w[1]} {w[2]:10s} frame {w[3]:5d} {w[4]!r}->{w[5]!r} clip {w[6]}->{w[7]} t={w[8]:.3f}")
# statistic: how many frames each state/clip is shown
cnt = collections.Counter((r['role'], r['clip']) for r in rows)
print("\nframes per (role, clip):")
for k, v in sorted(cnt.items()): print(" ", k, v)
# foot skate and ground lift
sk = [float(r['footSkate']) for r in rows if r['role'] == 'PLAYER']
print("\nplayer foot skate m/s: max %.3f, frames>0.15: %d of %d" % (max(sk), sum(1 for x in sk if x > .15), len(sk)))
gl = [float(r['groundLift']) for r in rows]
print("ground lift m: max %.3f, frames>0.01: %d" % (max(gl), sum(1 for x in gl if x > .01)))
ws = [float(r['weightSum']) for r in rows]
print("weight sum: min %.3f max %.3f" % (min(ws), max(ws)))
