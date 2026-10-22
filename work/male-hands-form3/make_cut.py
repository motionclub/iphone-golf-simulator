"""Recompute the hand cut (ring, removed faces, shell vertices) on the CURRENT dump (FORM2 hands installed).
shell(side) = FORM2 reused slots (data/shellv_*.npy of FORM2) + appended vertices (id >= 30296) on that side.   py.sh make_cut.py"""
import sys, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
from hlib import *
M = Mesh.from_npz(W / 'data/mesh_cur.npz'); V = M.V.astype(np.float64); polys = M.polys
N_ORIG = 30296
print('verts', len(V), 'polys', len(polys))
F2 = W.parent / 'male-arms-hands-form2'
rem_both = np.zeros(len(polys), bool)
for side in (+1, -1):
    slots = np.load(F2 / f'data/shellv_{side}.npy')
    app = np.arange(N_ORIG, len(V)); app = app[side * V[app, 0] > 0.0]
    sh = np.zeros(len(V), bool); sh[slots] = True; sh[app] = True
    rem = np.array([sh[list(p)].any() for p in polys]); kept = ~rem
    bedges, verts, cnt, adj = boundary_info(polys, kept)
    gx = side * V[:, 0]
    near = {v for v in adj if gx[v] > 0.2}
    adj2 = {v: [u for u in adj[v] if u in near] for v in near}
    ok = all(len(x) == 2 for x in adj2.values())
    start = next(iter(adj2)); ring = [start]; prev = None; cur = start
    while True:
        nxt = [v for v in adj2[cur] if v != prev]; nxt = nxt[0] if prev is not None else adj2[cur][0]
        if nxt == start: break
        ring.append(nxt); prev, cur = cur, nxt
    ring_old = np.load(F2 / f'data/ring_{side}.npy')
    usedrem = set(v for fi in np.nonzero(rem)[0] for v in polys[fi])
    other = usedrem - set(np.nonzero(sh)[0]) - set(ring)
    print('side', side, 'slots', len(slots), 'appended', len(app), 'shell', int(sh.sum()), 'removed faces', int(rem.sum()), 'boundary simple loop', ok, 'ring', len(ring),
          'same set as FORM2 ring:', set(ring) == set(int(i) for i in ring_old), 'verts of removed faces neither shell nor ring:', len(other))
    Lr = to_local(V, side)[ring]; print('  ring local w %.4f..%.4f' % (Lr[:, 2].min(), Lr[:, 2].max()))
    np.save(W / f'data/ring_{side}.npy', np.array(ring)); np.save(W / f'data/shellv_{side}.npy', np.nonzero(sh)[0]); np.save(W / f'data/removed_{side}.npy', np.nonzero(rem)[0])
    rem_both |= rem
np.save(W / 'data/removed_both.npy', np.nonzero(rem_both)[0])
print('removed faces total', int(rem_both.sum()), 'tris removed', int(sum(len(polys[i]) - 2 for i in np.nonzero(rem_both)[0])))
