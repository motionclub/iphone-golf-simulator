import numpy as np, sys, pickle, itertools
from collections import defaultdict
sys.path.insert(0,'.')
import hand_build as HB, hand_assemble as HA
d=np.load('baseline/mesh.npz'); co=d['co']; F=np.load('faces.npy')
base=dict(h_valley=0.0065, n_f0=-0.0182, r_n=0.0172)
def folds(verts,faces,limit=0.2):
    def fnorm(f):
        p=verts[list(f)]; n=np.zeros(3)
        for k in range(1,len(f)-1): n+=np.cross(p[k]-p[0],p[k+1]-p[0])
        return n
    FN=np.array([fnorm(f) for f in faces]); FNu=FN/np.maximum(np.linalg.norm(FN,axis=1),1e-18)[:,None]
    ef=defaultdict(list)
    for i,f in enumerate(faces):
        for k in range(len(f)):
            a,b=f[k],f[(k+1)%len(f)]; ef[(min(a,b),max(a,b))].append(i)
    return sorted(float(FNu[fs[0]]@FNu[fs[1]]) for e,fs in ef.items() if len(fs)==2 and FNu[fs[0]]@FNu[fs[1]]<limit)
cands={
 'A_prev':   dict(thumb_pts=[(0.043,-0.002,0.040),(0.058,0.012,0.068),(0.065,0.022,0.098)], thumb_r=(0.0200,0.0172,0.0148), thumb_first=0.014),
 'B_curved': dict(thumb_pts=[(0.040,-0.004,0.036),(0.051,0.008,0.042),(0.059,0.013,0.066),(0.065,0.021,0.098)], thumb_r=(0.0185,0.0185,0.0165,0.0148), thumb_first=0.012),
 'C_curved2':dict(thumb_pts=[(0.040,-0.004,0.036),(0.050,0.006,0.044),(0.058,0.012,0.068),(0.065,0.021,0.098)], thumb_r=(0.0175,0.0185,0.0170,0.0148), thumb_first=0.016),
 'D_curved3':dict(thumb_pts=[(0.041,-0.005,0.036),(0.052,0.009,0.046),(0.059,0.014,0.070),(0.065,0.022,0.098)], thumb_r=(0.0170,0.0185,0.0170,0.0148), thumb_first=0.020),
}
for name,over in cands.items():
    HB.P.update(base); HB.P.update(over)
    verts,faces,info=HA.assemble(co,F,smooth_iters=10)
    f=folds(verts,faces)
    print(name,'folded edges (<0.2):',len(f),'worst',np.round(f[:5],2))
