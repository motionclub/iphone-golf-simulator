import sys, json, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import numpy as np
import kin, pose as PS
from kin import a2w, w2a, unit
from clips import D
tag = sys.argv[1]
base = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/data'
rig = kin.Rig(f'{base}/rig_{tag}.json')
S = PS.Solver(rig, json.load(open(f'{base}/racket_{tag}.json')), json.load(open(f'{base}/hands_{tag}.json')))
ix = rig.idx
R0 = rig.Rrest[ix['RightLowerArm']].T @ rig.Rrest[ix['RightHand']]
P = dict(S.ready); P.update(l_attach=0.0, rk_fit=0.0)
b,h,info = S.solve(P)
Q,Pos = rig.fk(b,h)
Ql = Q[ix['RightLowerArm']]
print('forearm Y (r,f,u):', np.round(w2a(Ql[:,1]),2), ' hinge N (r,f,u):', np.round(w2a(Ql[:,0]),2), ' Zf:', np.round(w2a(Ql[:,2]),2))
def az_el(v):
    v = w2a(v); return math.degrees(math.atan2(v[0], v[1])), math.degrees(math.asin(max(-1,min(1,v[2]))))
print('flex dev twist -> shaft az/el | face az/el')
for tw in (-60, 0, 60):
    for fl in (-30, 0, 30, 50, 70):
        for dv in (0,):
            Dm = S._wrist_D(fl, dv, tw)
            Rk = (Ql @ Dm @ R0) @ S.R_rh
            sa, se = az_el(Rk[:,1]); fa, fe = az_el(Rk[:,2])
            print('%4d %4d %4d -> shaft az %4.0f el %4.0f | face az %4.0f el %4.0f' % (fl, dv, tw, sa, se, fa, fe))
