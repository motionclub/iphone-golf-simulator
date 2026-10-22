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
# bind: forearm frame columns, hand palm normal in world
print('bind LowerArm axes X,Y,Z (world):'); print(np.round(rig.Rrest[ix['RightLowerArm']],3))
print('bind Hand axes (world):'); print(np.round(rig.Rrest[ix['RightHand']],3))
# ready, one frame: reproduce internals
P = dict(S.ready); P.update(l_attach=0.0, rk_fit=0.0)
b,h,info = S.solve(P)
Q,Pos = rig.fk(b,h)
ia, ib = ix['RightLowerArm'], ix['RightHand']
Ql, Qh = Q[ia], Q[ib]
sg, tw = S._wrist_dev(Ql, Qh, R0)
print('ready: forearm Y(world)', np.round(Ql[:,1],3), ' hinge N', np.round(Ql[:,0],3), ' hand Y', np.round(Qh[:,1],3), ' hand Z(palm)', np.round(Qh[:,2],3))
print('       post-limit swing %.1f twist %.1f   clamp %.1f' % (math.degrees(sg), math.degrees(tw), info['R_wrist_clamp_deg']))
# pre-limit: recompute with limiter disabled
S.WRIST_SWING = math.radians(179); S.WRIST_TWIST = math.radians(179)
b,h,info = S.solve(P)
Q,Pos = rig.fk(b,h)
sg, tw = S._wrist_dev(Q[ia], Q[ib], R0)
print('no limit: swing %.1f twist %.1f ' % (math.degrees(sg), math.degrees(tw)))
print('  commanded racket: shaft(world)', np.round(info['rk_R'][:,1],3), 'face(world)', np.round(info['rk_R'][:,2],3))
print('  elbow flex', info['R_elbow_flex_deg'], 'shoulder', np.round(info['R_shoulder'],3), 'elbow', np.round(info['R_elbow'],3), 'wrist', np.round(Pos[ib],3))
