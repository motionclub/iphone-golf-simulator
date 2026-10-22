import sys, json, math, copy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import numpy as np
import kin, pose as PS, clipkit, clips
from kin import w2a
tag = sys.argv[1]
base = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/data'
rig = kin.Rig(f'{base}/rig_{tag}.json')
S = PS.Solver(rig, json.load(open(f'{base}/racket_{tag}.json')), json.load(open(f'{base}/hands_{tag}.json')))
d = clips.build('Forehand', S)
clip = clipkit.Clip(d, S.ready)
t = d['contact']
P0 = clip.params(t)
print('contact t', t, 'chest/pelvis rot', P0['pel_rot'], P0['chest_rot'], 'rk_pos', np.round(P0['rk_pos'],2), 'rk_abs', P0.get('rk_abs'), 'sweet', np.round(P0.get('rk_sweet'),2))
def run(label, **kw):
    P = dict(P0); P.update(kw)
    S.reset()
    b,h,i = S.solve(P)
    print('%-34s shErr %3.0f fcErr %3.0f | wrist swing %3.0f twist %4.0f | elbow %3.0f swivel %4.0f | sweet %s short %.1f | shaft_a %s face_a %s' % (
        label, i['shaft_err_deg'], i['face_err_deg'], i['R_wrist_swing_deg'], i['R_wrist_twist_deg'], i['R_elbow_flex_deg'], i.get('rk_swivel_deg',0),
        np.round(i['sweet_a'],2), i['R_arm_short']*100, np.round(i['shaft_a'],2), np.round(i['face_a'],2)))
run('as authored')
run('no abs override', rk_abs=0.0)
run('shaft weight only', rk_w=[0.0, 1.0])
run('face weight only', rk_w=[1.0, 0.0])
run('sweet farther (0.72,0.82,0.95)', rk_sweet=[0.72, 0.82, 0.95])
run('shaft D(40,20) face fwd', rk_shaft=clips.D(40,20))
run('shaft D(60,10) face fwd', rk_shaft=clips.D(60,10))
run('shaft up D(80,60)', rk_shaft=clips.D(80,60))
