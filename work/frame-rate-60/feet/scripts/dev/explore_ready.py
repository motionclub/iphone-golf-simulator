import sys, json, math, numpy as np
REPO='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
MA=REPO+'/work/match-anim-set'
sys.path.insert(0, MA+'/scripts')
import kin, pose as PS
from kin import a2w, w2a
for tag in ('male','female'):
    rig=kin.Rig(f'{MA}/data/rig_{tag}.json')
    S=PS.Solver(rig, json.load(open(f'{MA}/data/racket_{tag}.json')), json.load(open(f'{MA}/data/hands_{tag}.json')))
    print('=====',tag,'root origin',S.O,'A_arm',S.A_arm,'a_u',S.a_u,'a_f',S.a_f,'thigh',S.t_len,'shank',S.s_len,'shoulder_w',S.shoulder_w)
    R=S.ready
    print({k:(np.round(v,3).tolist() if isinstance(v,(list,np.ndarray)) else v) for k,v in R.items()})
    S.reset(); b,h,info=S.solve(dict(S.ready))
    Q,P=rig.fk(b,h)
    for nm in ('Hips','LeftUpperLeg','LeftFoot','LeftToes','RightFoot','Spine','Chest','Head','LeftUpperArm','RightUpperArm','RightHand','LeftHand'):
        print('  %-14s'%nm, np.round(w2a(P[rig.idx[nm]]-S.O),3))
    print('  ankle L (authoring r,f,u rel root)', np.round(w2a(info['lf_ankle']-S.O),3), ' ball', np.round(w2a(info['lf_ball']-S.O),3))
    print('  keys', [k for k in info.keys() if np.isscalar(info[k])][:50])
    print('  knee flex', info['lf_knee_flex_deg'], 'pelvis z', P[rig.idx['Hips']][2], 'hip joint z', rig.J['hip_L'][2])
    print('  ankle_rest-ball_rest', S.ankle_rest['L']-S.ball_rest['L'])
