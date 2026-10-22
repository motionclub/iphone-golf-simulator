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
    return info
info=pose((-0.20,0,-0.22),31,36,44,8)
sh=np.asarray(info['L_shoulder']); print('fold A Lshoulder',np.round(kin.w2a(sh-O),3))
pS=pS0+np.array([-0.0,-0.05,-0.07])      # stance hand: 5 cm forward, 7 cm lower
print('p0',np.round(kin.w2a(pS-O),3),' p1 base',np.round(kin.w2a(pR0-O),3))
for dr,df,du in ((0,0,0),(-0.1,0.0,0),(-0.2,0.0,0),(-0.1,0.1,0),(-0.2,0.1,0),(-0.2,0.2,0),(-0.3,0.2,0),(-0.15,0.15,-0.05)):
    pR=pR0+np.array([-dr,-df,du])
    dd=[]
    for u in (0.1,0.2,0.3,0.4,0.5):
        tgt=(1-sm(u))*(pS-np.array([0,0,0.09]))+sm(u)*pR
        dd.append(round(np.linalg.norm(tgt-sh)*1000))
    # also the distance to the ACTUAL (rising) shoulder isn't modelled here
    print('p1 shift (r%+.2f f%+.2f u%+.2f) -> p1 %s  dist at u=.1,.2,.3,.4,.5: %s'%(dr,df,du,np.round(kin.w2a(pR-O),2),dd))
