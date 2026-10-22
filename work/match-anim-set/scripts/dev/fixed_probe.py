import sys, json, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import numpy as np
import kin, pose as PS, clipkit, clips
tag = sys.argv[1]
base = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/data'
rig = kin.Rig(f'{base}/rig_{tag}.json')
S = PS.Solver(rig, json.load(open(f'{base}/racket_{tag}.json')), json.load(open(f'{base}/hands_{tag}.json')))
d = clips.build('Forehand', S)
clip = clipkit.Clip(d, S.ready)
t = d['contact']
P0 = clip.params(t)
S.reset(); b,h,i = S.solve(dict(P0, rk_mode='fit'))
print('FIT   : swivel %.1f wrist %s shErr %.0f fcErr %.0f short %.1f sweet %s' % (i['rk_swivel_deg'], np.round(i['rk_fit_flex_dev_twist'],1), i['shaft_err_deg'], i['face_err_deg'], i['R_arm_short']*100, np.round(i['sweet_a'],2)))
Pf = dict(P0, rk_mode='fixed', rk_swivel=i['rk_swivel_deg'], rk_wrist=i['rk_fit_flex_dev_twist'])
S.reset(); b,h,j = S.solve(Pf)
print('FIXED : swivel %.1f wrist %s shErr %.0f fcErr %.0f short %.1f sweet %s' % (j['rk_swivel_deg'], np.round(j['rk_fit_flex_dev_twist'],1), j['shaft_err_deg'], j['face_err_deg'], j['R_arm_short']*100, np.round(j['sweet_a'],2)))
clip.resolve(S)
print('resolved times', np.round(clip.resolved['times'],3))
print('swivel', np.round(clip.resolved['swivel'],1))
for tt, w in zip(clip.resolved['times'], clip.resolved['wrist']): print(round(tt,3), np.round(w,1))
P1 = clip.params(t); print('params at contact: mode', P1.get('rk_mode'), 'swivel', P1['rk_swivel'], 'wrist', P1['rk_wrist'])
S.reset(); b,h,k = S.solve(P1)
print('CLIPPED: swivel %.1f wrist %s shErr %.0f fcErr %.0f short %.1f sweet %s' % (k['rk_swivel_deg'], np.round(k['rk_fit_flex_dev_twist'],1), k['shaft_err_deg'], k['face_err_deg'], k['R_arm_short']*100, np.round(k['sweet_a'],2)))
