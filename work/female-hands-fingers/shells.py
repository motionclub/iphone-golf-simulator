import numpy as np
from collections import defaultdict
D = np.load('data/mesh_start.npz')
V = D['V'].astype(np.float64); cv = D['corner_verts']; ls = D['loop_start']; lt = D['loop_total']
polys = [tuple(int(x) for x in cv[s:s+t]) for s, t in zip(ls, lt)]
M = np.load('../female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz')
f2b = M['final_to_base']
newv = f2b < 0
print('new verts', newv.sum(), 'z>0.5:', (newv & (V[:,2]>0.5)).sum())
# connectivity: edges
vadj = defaultdict(set)
for p in polys:
    for k in range(len(p)):
        a, b = p[k], p[(k+1) % len(p)]
        vadj[a].add(b); vadj[b].add(a)
for side in (+1, -1):
    hv = np.nonzero(newv & (V[:,2] > 0.5) & (side*V[:,0] > 0.0))[0]
    print('side', side, 'hand new verts', len(hv), 'z range', V[hv,2].min(), V[hv,2].max(), 'x', V[hv,0].min(), V[hv,0].max(), 'y', V[hv,1].min(), V[hv,1].max())
    hs = set(hv.tolist())
    # ring = old verts adjacent to new hand verts
    ring = sorted(set(u for v in hv for u in vadj[v] if u not in hs))
    print('  ring verts', len(ring), [ (int(r), tuple(np.round(V[r],4))) for r in ring][:20])
    # faces of the hand: faces with all verts in hs or ring and at least one in hs
    hf = [i for i, p in enumerate(polys) if any(v in hs for v in p)]
    nt = sum(len(polys[i]) - 2 for i in hf)
    print('  hand faces', len(hf), 'tris', nt, 'sizes', {k: sum(1 for i in hf if len(polys[i])==k) for k in (3,4)})
    np.save(f'data/start_hand_verts_{side}.npy', hv); np.save(f'data/start_hand_ring_{side}.npy', np.array(ring)); np.save(f'data/start_hand_faces_{side}.npy', np.array(hf))
