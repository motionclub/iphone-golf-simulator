import sys, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-and-feet/scripts')
import loco, gait
clip, tag = sys.argv[1], sys.argv[2]
hero = loco.Hero(tag)
hero.S.reset(); b,h,info = hero.S.solve(dict(hero.ready))
print('READY wrist swing/twist', round(info['R_wrist_swing_deg'],1), round(info['R_wrist_twist_deg'],1), 'elbow R', round(info['R_elbow_flex_deg'],1))
Ps, tgt, meta = dict(walk=gait.walk, runf=gait.runf, runr=gait.runr, runl=gait.runl)[clip](hero)
print('k   Rwr_swing  Rwr_twist  Relbow  Lelbow  Lwr_sw  rk_shaft_el')
for k, P in enumerate(Ps):
    hero.S.reset(); b,h,i = hero.S.solve(P)
    print('%2d  %7.1f  %7.1f  %6.1f  %6.1f %6.1f   %.1f' % (k, i['R_wrist_swing_deg'], i['R_wrist_twist_deg'], i['R_elbow_flex_deg'], i['L_elbow_flex_deg'], i['L_wrist_swing_deg'], np.degrees(np.arcsin(P['rk_shaft'][2]))))
