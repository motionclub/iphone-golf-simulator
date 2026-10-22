import numpy as np, collections
L=lambda n: np.load(f'data/{n}.npz',allow_pickle=True)
F3=L('f3_body'); FF=L('f3_face'); FIN=L('final_body')
V3=F3['V']; u=np.zeros(len(V3),bool); u[F3['corner_verts']]=True
lo=np.nonzero(~u)[0]
print('F3 Body_F loose verts:', len(lo), ' idx range', lo.min(), lo.max(), ' all >= 12421:', (lo>=12421).all())
P=V3[lo]; print('  positions: x[%.4f,%.4f] y[%.4f,%.4f] z[%.4f,%.4f]'%(P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max(),P[:,2].min(),P[:,2].max()))
print('  centroid', P.mean(0))
# vertex-group membership
W=F3['vg_weights']; names=[str(x) for x in F3['vg_names']]
inany=(W[:,lo]>0).any(0); print('  loose verts that are members of a vertex group:', int(inany.sum()))
for g,n in enumerate(names):
    k=int((W[g][lo]>0).sum())
    if k: print('    group', n, k)
# do loose verts coincide with Face_F vertices (e.g. eye shells)?
Q=FF['V']; from collections import defaultdict
kq=set(map(tuple,Q.astype(np.float32).tolist()))
print('  loose verts that coincide with a Face_F vertex:', sum(1 for p in P.astype(np.float32).tolist() if tuple(p) in kq))
# are they near the eye openings? distance to the eye boundary loops centre
for sgn in (-1,1):
    c=np.array([sgn*0.0491,-0.1099,1.5544]); d=np.linalg.norm(P-c,axis=1); print('  loose verts within 30mm of eye centre x=%+.3f:'%(sgn*0.0491), int((d<0.03).sum()), ' within 60mm:', int((d<0.06).sum()))
# clusters by z
h,e=np.histogram(P[:,2],bins=10); print('  z histogram', h.tolist(), [round(float(x),3) for x in e])
# F1/F2 sources: do they have loose verts too?
import os
for p in ('work/female-micro-f1-head/export/HeroBase_Female_MicroF1_head_STAGED.blend','work/female-micro-f2-head/export/HeroBase_Female_MicroF2_head_STAGED.blend'):
    print(p, os.path.exists('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'+p))
# in the stage the final: which final idx
print('final loose idx', len(np.nonzero(~np.isin(np.arange(len(FIN['V'])),FIN['corner_verts']))[0]))
