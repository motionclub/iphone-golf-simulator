import sys, math, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet/scripts')
import loco, gait
tag = sys.argv[1]
hero = loco.Hero(tag)
Ps, tgt, meta = gait.runf(hero)
def run(el0, amp, face_az, rk_f0, rk_fa, rk_z0):
    mx = 0; tw = 0; rows = []
    for k, P in enumerate(Ps):
        c1 = math.cos(2*math.pi*k/len(Ps))
        P2 = dict(P)
        sh = hero.ready['sh_half_A']
        P2['rk_pos'] = [sh + 0.01, rk_f0 - rk_fa*c1, rk_z0 - 0.05*c1]
        P2['rk_shaft'] = gait.D(8, el0 - amp*c1)
        P2['rk_face'] = gait.D(face_az, 0)
        hero.S.reset(); b,h,i = hero.S.solve(P2)
        mx = max(mx, i['R_wrist_swing_deg']); tw = max(tw, abs(i['R_wrist_twist_deg']))
    return mx, tw
best = []
for el0 in (25, 32, 40):
    for amp in (10, 18):
        for face in (-100, -115):
            for rkf in (0.26, 0.32):
                for rkz in (-0.46, -0.40):
                    for rka in (0.10, 0.16):
                        P_ = None
                        mx = 0; tw = 0
                        for k, P in enumerate(Ps):
                            c1 = math.cos(2*math.pi*k/len(Ps)); P2 = dict(P); sh = hero.ready['sh_half_A']
                            P2['rk_pos'] = [sh + 0.01, rkf - rka*c1, rkz - 0.05*c1]; P2['rk_shaft'] = gait.D(8, el0 - amp*c1); P2['rk_face'] = gait.D(face, 0)
                            hero.S.reset(); b,h,i = hero.S.solve(P2); mx = max(mx, i['R_wrist_swing_deg']); tw = max(tw, abs(i['R_wrist_twist_deg']))
                        best.append((mx, tw, el0, amp, face, rkf, rkz, rka))
best.sort()
for b in best[:10]: print('swing %.1f twist %.1f  el0 %d amp %d face %d rk_f0 %.2f rk_z0 %.2f rk_amp %.2f' % b)
