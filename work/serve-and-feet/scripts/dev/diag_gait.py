import sys, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-and-feet/scripts')
import loco, gait
clip, tag = sys.argv[1], sys.argv[2]
hero = loco.Hero(tag)
Ps, tgt, meta = dict(walk=gait.walk, runf=gait.runf, runr=gait.runr, runl=gait.runl)[clip](hero)
hs = loco.calibrate(hero, Ps, tgt)
quats, hips, infos, bases = loco.solve_frames(hero, Ps)
print('k   u     hipsZ  drop  kneeL kneeR  hL    hR   ballL(r,f)        ballR(r,f)      ankleL f  ankleR f   lean')
for k, (P, i, b, h) in enumerate(zip(Ps, infos, bases, hips)):
    Q, Pos = hero.rig.fk(b, h)
    print('%2d %5.2f  %.3f  %3.0f  %5.1f %5.1f  %4.0f %4.0f  (%.2f,%.2f)  (%.2f,%.2f)  %.2f %.2f' % (k, k/len(Ps), Pos[hero.rig.idx['Hips']][2], 1000*i.get('pelvis_auto_drop',0), i['lf_knee_flex_deg'], i['rf_knee_flex_deg'], hs[k,0]*1000, hs[k,1]*1000,
          P['lf_foot'][0], P['lf_foot'][1], P['rf_foot'][0], P['rf_foot'][1], loco.w2a(i['lf_ankle']-hero.O)[1], loco.w2a(i['rf_ankle']-hero.O)[1]))
