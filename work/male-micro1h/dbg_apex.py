import sys
import numpy as np, bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, loft as L, proxy as PX
V, F = PX.build_proxy(3)
lf = L.Loft()
P, rp, rl = L.remap(V, lf)
print('orig z max', V[:,2].max(), 'remap z max', P[:,2].max())
hi = V[:,2] > 1.69
print('n apex-zone verts', int(hi.sum()))
d = np.linalg.norm(P[hi]-V[hi],axis=1)*1000
print('apex-zone move mm: mean %.2f max %.2f'%(d.mean(), d.max()))
# z histogram of remapped apex-zone verts
zz = P[hi,2]
print('z percentiles of remapped apex-zone', np.percentile(zz,[0,10,50,90,100]))
# radial extent (xy) of verts with z>1.7035
m = P[:,2] > 1.7035
print('n verts z>1.7035:', int(m.sum()), 'xy radius max mm', float(np.hypot(P[m,0], P[m,1]-lf.at(P[m,2])['yw']).max()*1000) if m.any() else None)
bpy.ops.wm.read_factory_settings(use_empty=True)
H.make_mesh_object('proxy', P, [f for f in F])
H.setup_render()
H.shot(H.W/'r/proxy0/apex_top.png', (0,-0.04,1.65), 0, 89, 0.22, (800,800))
H.shot(H.W/'r/proxy0/apex_side.png', (0,-0.04,1.68), 90, 0, 0.14, (800,800))
