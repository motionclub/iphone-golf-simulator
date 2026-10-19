import sys, math, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet/scripts')
import loco, gait
tag = sys.argv[1]
hero = loco.Hero(tag)
Ps, tgt, meta = gait.walk(hero)
sh = hero.ready['sh_half_A']
best = []
for el in (-60, -45, -30, -15):
    for face in (-85, -105, -65):
        for rkx in (0.07, 0.11):
            for rkf in (0.02, 0.10):
                for rkz in (-0.86, -0.80):
                    mx = 0; tw = 0
                    for k, P in enumerate(Ps):
                        c1 = math.cos(2*math.pi*k/len(Ps)); P2 = dict(P)
                        P2['rk_pos'] = [sh + rkx, rkf - 0.07*c1, rkz]; P2['rk_shaft'] = gait.D(8, el); P2['rk_face'] = gait.D(face, 0)
                        hero.S.reset(); b,h,i = hero.S.solve(P2); mx = max(mx, i['R_wrist_swing_deg']); tw = max(tw, abs(i['R_wrist_twist_deg']))
                    best.append((mx, tw, el, face, rkx, rkf, rkz))
best.sort()
for b in best[:8]: print('swing %.1f twist %.1f el %d face %d rkx %.2f rkf %.2f rkz %.2f' % b)
