import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from onhand import *
from collections import deque
reset_scene()
body = load_body_copy('female')
co = mesh_co(body); tris = mesh_tris(body)
parts = FH.hand_parts(co, tris)
seeds = set(parts['forearm'].tolist())
adj = {}
for a, b, c in tris:
    for u, v in ((a, b), (b, c), (c, a)):
        adj.setdefault(int(u), set()).add(int(v)); adj.setdefault(int(v), set()).add(int(u))
for zmax in (1.15, 1.25, 1.35):
    seen = set(seeds); q = deque(seeds)
    while q:
        u = q.popleft()
        for v in adj.get(u, ()):
            if v not in seen and co[v, 2] < zmax:
                seen.add(v); q.append(v)
    P = co[list(seen)]
    print('zmax', zmax, 'arm set', len(seen), 'bbox x', P[:, 0].min().round(3), P[:, 0].max().round(3), 'y', P[:, 1].min().round(3), P[:, 1].max().round(3), 'z', P[:, 2].min().round(3), P[:, 2].max().round(3))
