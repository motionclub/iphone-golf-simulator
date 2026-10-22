import sys, math, itertools
sys.path.insert(0,'.')
import numpy as np, loco, kin
tag=sys.argv[1] if len(sys.argv)>1 else 'male'
h=loco.Hero(tag); S=h.S; R=h.rig; IX=R.idx
z=np.load('../data/gen_serve_%s.npz'%tag, allow_pickle=True)
pS,pR,pT=z['ritual']; O=h.O
f0=S.ready['rf_foot'][1]; xr,xl=0.26,-0.18
sm=lambda u:u*u*(3-2*u)
def pose(pel, pyaw, ppitch, cyaw, cpitch):
    P=dict(S.ready)
    P.update(lf_foot=[xl,f0+0.14], rf_foot=[xr,f0-0.08], lf_yaw=h.toe_dir_to_yaw('L',38.0), rf_yaw=h.toe_dir_to_yaw('R',75.0))
    P['pel']=[pel[1],pel[0],pel[2]]; P['pel_rot']=[pyaw,ppitch,0]; P['chest_rot']=[cyaw-pyaw,cpitch,0]
    S.reset(); b,hl,info=S.solve(P)
    return info
res=[]
for fb,dz,pp,cp in itertools.product((-0.14,-0.20,-0.26,-0.32),(-0.20,-0.25,-0.29),(24,32,40),(0,8)):
    info=pose((fb,0,dz),31,pp,44,cp)
    sh=np.asarray(info['L_shoulder'])
    dmin=9
    for u in (0.1,0.2,0.3,0.4):
        tgt=(1-sm(u))*(pS-np.array([0,0,0.09]))+sm(u)*pR
        dmin=min(dmin,np.linalg.norm(tgt-sh))
    kn=max(info['lf_knee_flex_deg'],info['rf_knee_flex_deg'])
    res.append((dmin,fb,dz,pp,cp,kn,info['lf_short'],info['rf_short'],info.get('pelvis_auto_drop',0)))
res.sort(reverse=True)
print('dmin(mm)  f   dz  pelpitch chestpitch  kneeMax shortL shortR autodrop')
for r in res[:30]:
    print('%6.0f  %5.2f %5.2f  %3d  %3d   %5.1f  %.3f %.3f %.3f'%(r[0]*1000,*r[1:]))
