import sys, numpy as np
sys.path.insert(0,'../male-micro1e')
import hand_sdf as H, run, quality
V0=run.V0.astype(np.float32); C=np.load('data/final_cur.npy')
d=np.linalg.norm(C.astype(float)-V0.astype(float),axis=1)
sh=run.SHC
mv=np.nonzero((d>0)&~sh)[0]
order=mv[np.argsort(-d[mv])][:15]
for i in order:
    side=+1 if V0[i,0]>0 else -1
    l=H.to_local(V0[i:i+1].astype(float),side)[0]
    print(i,'disp %.2f mm'%(1000*d[i]),'pos',np.round(V0[i],3),'hand-local (a n w)',np.round(l,3),'t=%.3f'%quality.arm_t(V0[i:i+1].astype(float),side)[0])
print('non-shell moved by t bins (R):')
t=quality.arm_t(V0.astype(float),+1)
for a in np.arange(-0.04,0.14,0.02):
    m=(d>0)&~sh&(V0[:,0]>0)&(t>=a)&(t<a+0.02)
    if m.sum(): print(f' t {a:+.2f}..{a+0.02:+.2f} n={m.sum():3d} mean {1000*d[m].mean():.2f} max {1000*d[m].max():.2f} mm')
# flipped polys
Fn0=quality.face_normals(V0.astype(float),run.polys); Fn1=quality.face_normals(C.astype(float),run.polys)
zone=run.ZR|run.ZL
for i,p in enumerate(run.polys):
    if zone[list(p)].all() and (Fn0[i]*Fn1[i]).sum()<0.5:
        c=V0[list(p)].mean(0); l=H.to_local(c[None].astype(float),+1 if c[0]>0 else -1)[0]
        print('poly',i,'dot %.2f'%(Fn0[i]*Fn1[i]).sum(),'centroid local',np.round(l,3),'shell',bool(sh[list(p)].all()))
