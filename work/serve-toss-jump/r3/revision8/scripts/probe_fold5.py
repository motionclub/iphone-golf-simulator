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
def evalf(label,pel,pp,cp,pshift=(0,0,0)):
    info,b,hl=pose(pel,31,pp,44,cp)
    sh=np.asarray(info['L_shoulder'])
    pS=pS0+np.array([-pshift[0],-pshift[1],pshift[2]])
    dd=[]
    for u in (0.0,0.1,0.2,0.3,0.4):
        tgt=(1-sm(u))*(pS-np.array([0,0,0.09]))+sm(u)*pR0
        dd.append(round(np.linalg.norm(tgt-sh)*1000))
    Q,Pos=R.fk(b,hl)
    # trunk pitch actual: angle between hips->neck and vertical
    v=Pos[IX['Neck']]-Pos[IX['Hips']]; ang=math.degrees(math.atan2(math.hypot(v[0],v[1]),v[2]))
    print('%-40s Lsh (r %.2f f %.2f u %.2f) trunkAngle %4.1f knee %4.1f/%4.1f  dist u=0,.1,.2,.3,.4: %s'%(label,*kin.w2a(sh-O),ang,info['lf_knee_flex_deg'],info['rf_knee_flex_deg'],dd))
evalf('stance',(0,0,0),9,8)
for lab,pel,pp,cp in (('E f-.20 z-.15 30+10',(-0.20,0,-0.15),30,10),('F f-.26 z-.14 34+6',(-0.26,0,-0.14),34,6),('G f-.22 z-.12 32+10',(-0.22,0,-0.12),32,10),
                      ('H f-.24 z-.16 28+12',(-0.24,0,-0.16),28,12),('I f-.28 z-.16 30+10',(-0.28,0,-0.16),30,10),('J f-.20 z-.14 36+8',(-0.20,0,-0.14),36,8)):
    evalf(lab,pel,pp,cp)
    evalf(lab+' +p0(f+.05,u-.07)',pel,pp,cp,(0,0.05,-0.07))
