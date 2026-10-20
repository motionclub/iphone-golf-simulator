"""Locate open / non-manifold / inconsistent edges of a staged part.  python where_open.py <npz name>  (numpy only)"""
import sys, collections
import numpy as np
nm = sys.argv[1]
z = np.load(f'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-worn/data/{nm}.npz')
V, F, T, tn = z['V'], z['F'], z['T'], list(z['tagnames'])
E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 0)
fid = np.tile(np.arange(len(F)), 3)
Es = np.sort(E, axis=1)
u, inv, cnt = np.unique(Es, axis=0, return_inverse=True, return_counts=True)
inv = inv.reshape(-1)
for label, sel in (('boundary', cnt == 1), ('nonmanifold', cnt > 2)):
    idx = np.nonzero(sel)[0]
    print(label, len(idx))
    tags = collections.Counter()
    for e in idx[:400]:
        fs = fid[inv == e]
        for f in fs:
            tags[tn[T[f]]] += 1
    print('  tags', dict(tags))
    for e in idx[:12]:
        a, b = u[e]
        print('   edge', V[a].round(4).tolist(), V[b].round(4).tolist(), 'len mm', round(float(np.linalg.norm(V[a] - V[b])) * 1000, 2), 'faces', [tn[T[f]] for f in fid[inv == e]])
d, dc = np.unique(E, axis=0, return_counts=True)
bad = d[dc > 1]
print('same-direction edges', len(bad))
fe = collections.defaultdict(list)
for fi, f in enumerate(F.tolist()):
    for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
        fe[(a, b)].append(fi)
for a, b in bad[:12].tolist():
    print('   edge', V[a].round(4).tolist(), V[b].round(4).tolist(), [tn[T[f]] for f in fe[(a, b)]])
