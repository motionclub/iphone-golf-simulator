"""debug: wrist swing/twist vs racket shaft direction at the READY hand position (no bpy needed).  python3 (blender python) wrist_probe.py <tag>"""
import sys, json, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import numpy as np
import kin, pose as PS
from clips import D
tag = sys.argv[1]
base = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/data'
rig = kin.Rig(f'{base}/rig_{tag}.json')
S = PS.Solver(rig, json.load(open(f'{base}/racket_{tag}.json')), json.load(open(f'{base}/hands_{tag}.json')))
R0 = rig.Rrest[rig.idx['RightLowerArm']].T @ rig.Rrest[rig.idx['RightHand']]
print('R0 (hand rel forearm, bind):'); print(np.round(R0,3))
print('bind forearm Y', np.round(rig.Rrest[rig.idx['RightLowerArm']][:,1],3), 'hand Y', np.round(rig.Rrest[rig.idx['RightHand']][:,1],3))
base_P = dict(l_attach=0.0, rk_fit=0.0, l_hand=[-0.1,0.5,-0.7])
print('shaft(az,el) face(az,el) -> swing/twist/clamp/elbow')
for sh in ((10,72),(10,30),(10,0),(10,-30),(60,0),(60,40),(90,0),(-30,40)):
    for fc in ((-85,0),(0,0),(85,0)):
        P = dict(base_P); P.update(rk_shaft=D(*sh), rk_face=D(*fc))
        b,h,info = S.solve(P)
        print('shaft', sh, 'face', fc, '-> swing %.0f twist %.0f clamp %.0f elbow %.0f short %.1fcm' % (info['R_wrist_swing_deg'], info['R_wrist_twist_deg'], info['R_wrist_clamp_deg'], info['R_elbow_flex_deg'], info['R_arm_short']*100))
