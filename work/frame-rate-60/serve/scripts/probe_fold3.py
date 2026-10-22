import sys, math, itertools
sys.path.insert(0,'.')
import numpy as np, loco, kin
tag=sys.argv[1] if len(sys.argv)>1 else 'male'
h=loco.Hero(tag); S=h.S; R=h.rig; IX=R.idx
z=np.load('../data/gen_serve_%s.npz'%tag, allow_pickle=True)
pS0,pR,pT=z['ritual']; O=h.O
f0=S.ready['rf_foot'][1]; xr,xl=0.26,-0.18
sm=lambda u:u*u*(3-2*u)
def pose(pel, pyaw, ppitch, cyaw, cpitch):
    P=dict(S.ready)
    P.update(lf_foot=[xl,f0+0.14], rf_foot=[xr,f0-0.08], lf_yaw=h.toe_dir_to_yaw('L',38.0), rf_yaw=h.toe_dir_to_yaw('R',75.0))
    P['pel']=[pel[1],pel[0],pel[2]]; P['pel_rot']=[pyaw,ppitch,0]; P['chest_rot']=[cyaw-pyaw,cpitch,0]
    S.reset(); b,hl,info=S.solve(P)
    return info
fold=dict(A=((-0.20,0,-0.22),36,8), B=((-0.16,0,-0.20),30,6), C=((-0.24,0,-0.24),40,6), D=((-0.12,0,-0.185),42,16))
for name,(pel,pp,cp) in fold.items():
    info=pose(pel,31,pp,44,cp)
    sh=np.asarray(info['L_shoulder'])
    print('fold',name,pel,pp,cp,'Lshoulder (authoring r,f,u)',np.round(kin.w2a(sh-O),3),'knee',round(max(info['lf_knee_flex_deg'],info['rf_knee_flex_deg']),1))
    for (dr,df,du) in ((0,0,0),(0,0.05,-0.05),(0,0.08,-0.08),(0,0.10,-0.12),(-0.05,0.10,-0.12),(-0.1,0.1,-0.12),(-0.1,0.12,-0.15),(-0.15,0.15,-0.15)):
        pS=pS0+np.array([-dr,-df,du])   # world = (-r,-f,u)
        dm=9; dd=[]
        for u in (0.0,0.1,0.2,0.3,0.4):
            tgt=(1-sm(u))*(pS-np.array([0,0,0.09]))+sm(u)*pR
            d=np.linalg.norm(tgt-sh); dd.append(round(d*1000)); dm=min(dm,d)
        print('   p0 shift (r%+.2f f%+.2f u%+.2f) -> palm_S %s  dist at u=0,.1,.2,.3,.4: %s'%(dr,df,du,np.round(kin.w2a(pS-O),2),dd))
