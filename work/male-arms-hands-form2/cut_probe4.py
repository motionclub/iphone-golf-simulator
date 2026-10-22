import numpy as np, sys, collections
sys.path.insert(0,'.')
from hlib import *
M = Mesh.from_npz('data/mesh_start.npz'); V = M.V.astype(np.float64); polys = M.polys
SH = np.load('../male-parallel-arms/data/shell_cur.npy'); print('shell mask', SH.sum(), len(SH))
zR = np.load('../male-parallel-arms/data/zone_R.npy'); zL = np.load('../male-parallel-arms/data/zone_L.npy')
print('zone R', zR.sum(), 'zone L', zL.sum())
for side,zone in ((+1,zR),(-1,zL)):
    sh = SH & zone
    print('side',side,'shell verts',int(sh.sum()))
    rem = np.array([sh[list(p)].any() for p in polys]); kept = ~rem
    bedges, verts, cnt, adj = boundary_info(polys, kept)
    gx = side*V[:,0]
    near = {v for v in adj if gx[v] > 0.2}
    adj2 = {v: [u for u in adj[v] if u in near] for v in near}
    print('  boundary verts near', len(near), 'all deg2', all(len(x)==2 for x in adj2.values()), 'removed faces', int(rem.sum()), collections.Counter(len(polys[i]) for i in np.nonzero(rem)[0]))
    start = next(iter(adj2)); ring=[start]; prev=None; cur=start
    while True:
        nxt=[v for v in adj2[cur] if v!=prev]; nxt = nxt[0] if prev is not None else adj2[cur][0]
        if nxt==start: break
        ring.append(nxt); prev,cur=cur,nxt
    L = to_local(V, side); Lr=L[ring]
    print('  ring',len(ring),'local w %.4f..%.4f'%(Lr[:,2].min(),Lr[:,2].max()))
    # vertices used by removed faces but not shell and not ring -> should be none
    usedrem = set(v for fi in np.nonzero(rem)[0] for v in polys[fi])
    other = usedrem - set(np.nonzero(sh)[0]) - set(ring)
    print('  verts of removed faces that are neither shell nor ring:', len(other))
    np.save(f'data/ring_{side}.npy', np.array(ring)); np.save(f'data/shellv_{side}.npy', np.nonzero(sh)[0]); np.save(f'data/removed_{side}.npy', np.nonzero(rem)[0])
