import sys, math, itertools
sys.path.insert(0,'.')
import numpy as np, loco, kin
tag=sys.argv[1] if len(sys.argv)>1 else 'male'
h=loco.Hero(tag); S=h.S; R=h.rig; IX=R.idx
z=np.load('../data/gen_serve_%s.npz'%tag, allow_pickle=True)
pS0,pR0,pT=z['ritual']; O=h.O
f0=S.ready['rf_foot'][1]; xr,xl=0.26,-0.18
sm=lambda u:u*u*(3-2*u)
def pose(pel, pyaw, ppitch, cyaw, cpitch):
    P=dict(S.ready)
    P.update(lf_foot=[xl,f0+0.14], rf_foot=[xr,f0-0.08], lf_yaw=h.toe_dir_to_yaw('L',38.0), rf_yaw=h.toe_dir_to_yaw('R',75.0))
    P['pel']=[pel[1],pel[0],pel[2]]; P['pel_rot']=[pyaw,ppitch,0]; P['chest_rot']=[cyaw-pyaw,cpitch,0]
    S.reset(); b,hl,info=S.solve(P)
    return info,b,hl
pS=pS0+np.array([0.0,-0.04,-0.05])
rows=[]
for fb,dz,pp,cp in itertools.product((-0.24,-0.28,-0.32),(-0.14,-0.17,-0.20),(28,32,36,40),(4,10)):
    info,b,hl=pose((fb,0,dz),31,pp,44,cp)
    sh=np.asarray(info['L_shoulder'])
    dd=[]
    for u in (0.1,0.2,0.3):
        tgt=(1-sm(u))*(pS-np.array([0,0,0.09]))+sm(u)*pR0
        dd.append(np.linalg.norm(tgt-sh)*1000)
    Q,Pos=R.fk(b,hl)
    v=Pos[IX['Neck']]-Pos[IX['Hips']]; ang=math.degrees(math.atan2(math.hypot(v[0],v[1]),v[2]))
    kn=max(info['lf_knee_flex_deg'],info['rf_knee_flex_deg'])
    rows.append((ang,min(dd),fb,dz,pp,cp,kn,[round(x) for x in dd]))
rows=[r for r in rows if r[1]>=280]
rows.sort(reverse=True)
print('trunk  mind  f   dz   pp  cp  knee  dists(u=.1,.2,.3)')
for r in rows[:25]: print('%5.1f %5.0f %5.2f %5.2f %3d %3d %5.1f %s'%r)
