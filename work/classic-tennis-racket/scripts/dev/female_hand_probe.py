import numpy as np
from collections import deque
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/'
d = np.load(W + 'data/female_body.npz')
co, tris = d['co'], d['tris']
sel = np.where((co[:, 0] < -0.20) & (co[:, 2] < 1.0))[0]
# components restricted to the selection
s = set(sel.tolist())
adj = {}
for a, b, c in tris:
    for u, v in ((a, b), (b, c), (c, a)):
        if u in s and v in s:
            adj.setdefault(u, set()).add(v); adj.setdefault(v, set()).add(u)
seen, comps = set(), []
for st in sel:
    if st in seen: continue
    q = deque([st]); seen.add(st); comp = [st]
    while q:
        u = q.popleft()
        for v in adj.get(u, ()):
            if v not in seen:
                seen.add(v); q.append(v); comp.append(v)
    comps.append(np.array(comp))
comps.sort(key=lambda c: -co[c, 2].max())
for i, c in enumerate(comps):
    P = co[c]
    cen = P.mean(0)
    print(i, 'n=%4d' % len(c), 'bbox', P.min(0).round(4), P.max(0).round(4), 'centroid', cen.round(4), 'size', (P.max(0) - P.min(0)).round(4))
# forearm end: arm vertices at z in 0.82..0.95 with x<-0.2
arm = co[(co[:, 0] < -0.2) & (co[:, 2] > 0.80) & (co[:, 2] < 1.0)]
print('arm band z[0.8,1.0] x range', arm[:, 0].min().round(4), arm[:, 0].max().round(4), 'y range', arm[:, 1].min().round(4), arm[:, 1].max().round(4))
# thigh outer surface x at several z (legs: |x| < 0.2 region): for the right leg take x<0 verts with z in band & y in [-0.12,0.12]
for z0 in (0.70, 0.75, 0.80, 0.85, 0.90, 0.95):
    m = (co[:, 2] >= z0) & (co[:, 2] < z0 + 0.02) & (co[:, 0] < 0)
    # separate arm from leg by x: leg verts are those with x > -0.235 at this height OR connected... print x extremes of two clusters
    xs = np.sort(co[m, 0])
    # cluster gap
    gaps = np.diff(xs)
    k = np.argsort(gaps)[-3:]
    print('z', z0, 'x min', xs.min().round(4), 'x max', xs.max().round(4), 'big gaps at x:', [(xs[i].round(4), xs[i + 1].round(4)) for i in sorted(k)])
