import sys, math
sys.path.insert(0,'.')
import numpy as np, loco, kin
tag=sys.argv[1] if len(sys.argv)>1 else 'male'
h=loco.Hero(tag); S=h.S; R=h.rig; IX=R.idx
z=np.load('../data/gen_serve_%s.npz'%tag, allow_pickle=True)
pS,pR,pT=z['ritual']
O=h.O
print('palm S (authoring r,f,u):',np.round(kin.w2a(pS-O),3),' R:',np.round(kin.w2a(pR-O),3),' T:',np.round(kin.w2a(pT-O),3))
f0=S.ready['rf_foot'][1]
xr,xl=0.26,-0.18
sm=lambda u:u*u*(3-2*u)
def pose(t_u, pel, pyaw, ppitch, cyaw, cpitch):
    P=dict(S.ready)
    P.update(lf_foot=[xl,f0+0.14], rf_foot=[xr,f0-0.08], lf_yaw=h.toe_dir_to_yaw('L',38.0), rf_yaw=h.toe_dir_to_yaw('R',75.0))
    P['pel']=[pel[1],pel[0],pel[2]]; P['pel_rot']=[pyaw,ppitch,0]; P['chest_rot']=[cyaw-pyaw,cpitch,0]
    S.reset(); b,hl,info=S.solve(P)
    return info
def evalfold(label, pel, ppitch, cpitch, u=0.27, pyaw=31, cyaw=44):
    info=pose(u, pel, pyaw, ppitch, cyaw, cpitch)
    tgt=(1-sm(u))*(pS-np.array([0,0,0.09]))+sm(u)*pR
    sh=np.asarray(info['L_shoulder'])
    d=np.linalg.norm(tgt-sh)
    chest=np.asarray(info['chest_center'])
    print('%-44s u %.2f  palm-to-Lshoulder %4.0f mm  chest ctr (f %.2f u %.2f)  Lsh (r %.2f f %.2f u %.2f) ball (r %.2f f %.2f u %.2f)'%(label,u,d*1000,*kin.w2a(chest-O)[1:],*kin.w2a(sh-O),*kin.w2a(tgt-O)))
for u in (0.15,0.27,0.4):
    print('--- u',u)
    evalfold('stance (no fold)',(0,0,0),9,8,u)
    evalfold('draft: f-.12 z-.185 pitch 42+16',(-0.12,0,-0.185),42,16,u)
    evalfold('f-.16 z-.185 pitch 30+8',(-0.16,0,-0.185),30,8,u)
    evalfold('f-.18 z-.19 pitch 30+4',(-0.18,0,-0.19),30,4,u)
    evalfold('f-.20 z-.20 pitch 34+0',(-0.20,0,-0.20),34,0,u)
    evalfold('f-.22 z-.20 pitch 38+0',(-0.22,0,-0.20),38,0,u)
    evalfold('f-.22 z-.17 pitch 36+0',(-0.22,0,-0.17),36,0,u)
