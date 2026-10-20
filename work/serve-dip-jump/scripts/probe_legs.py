import sys, math
sys.path.insert(0,'.')
import numpy as np, loco, kin
tag=sys.argv[1] if len(sys.argv)>1 else 'male'
h=loco.Hero(tag); S=h.S; R=h.rig
f0=S.ready['rf_foot'][1]
xr,xl=0.26,-0.18
def base(**kw):
    P=dict(S.ready)
    P.update(lf_foot=[xl,f0+0.14], rf_foot=[xr,f0-0.08], lf_yaw=h.toe_dir_to_yaw('L',38.0), rf_yaw=h.toe_dir_to_yaw('R',75.0), pel_rot=[30,9,0], chest_rot=[12,8,0])
    P.update(kw); return P
def run(label, **kw):
    S.reset(); b,hl,info=S.solve(base(**kw))
    Q,Pos=R.fk(b,hl)
    hh=h.foot_h(b,hl)
    print('%-34s kneeL %5.1f kneeR %5.1f shortL %.3f shortR %.3f  autodrop %.3f  footLow(L,R) mm %5.0f %5.0f  hipsZ %.3f' % (label, info['lf_knee_flex_deg'], info['rf_knee_flex_deg'], info['lf_short'], info['rf_short'], info.get('pelvis_auto_drop',0.0), hh['L']*1000, hh['R']*1000, Pos[R.idx['Hips']][2]))
run('ready-ish')
for dz in (-0.05,-0.10,-0.15,-0.20,-0.25):
    run('dip dz %.2f f-0.08 pitch 9'%dz, pel=[0,-0.08,dz])
for dz,fb,pp in ((-0.15,-0.10,35),(-0.17,-0.12,42),(-0.20,-0.14,45),(-0.22,-0.15,48)):
    run('fold dz %.2f f%.2f pitch %d'%(dz,fb,pp), pel=[0,fb,dz], pel_rot=[30,pp,0], chest_rot=[12,14,0])
for dz in (0.0,0.03,0.06,0.10):
    run('planted extend dz %.2f'%dz, pel=[0,0,dz])
for dz,lift,heel in ((0.20,0.17,60),(0.20,0.20,60),(0.22,0.19,65),(0.22,0.14,65),(0.22,0.10,65)):
    run('air dz %.2f lift %.2f heel %d'%(dz,lift,heel), pel=[0,0,dz], lf_lift=lift, rf_lift=lift, lf_heel=heel, rf_heel=heel)
