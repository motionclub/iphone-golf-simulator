"""quick numbers for a clip on a hero: python3.13 emo_diag.py <male|female> <clip>"""
import sys, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/emotes/scripts')
from emo_hero import *
import emo_clips as EC
tag, clip = sys.argv[1], sys.argv[2]
H = EmoHero(tag); C = EC.build(clip, H)
n = int(round(C.length * 30)) + 1
rows = []
prevq = None
step = []
for f in range(n):
    d = C.solve(f / 30.0); info = d['info']
    q = quats_of(H.rig, d['basis'], prevq)
    if prevq is not None:
        dd = rot_diff_deg(q, prevq)
        step.append(dd.max())
        if dd.max() > 45 and '--steps' in sys.argv:
            print('  step f%d: ' % f + ', '.join('%s %.0f' % (H.rig.names[i], dd[i]) for i in np.argsort(-dd)[:4]))
    prevq = q
    m = H.mesh(d['basis'], d['hips'])
    rows.append((f, info['R_wrist_clamp_deg'], info['L_wrist_clamp_deg'], info['R_arm_short'], info['L_arm_short'], info['R_arm_near'], info['L_arm_near'], info['lf_short'], info['rf_short'], m[:, 2].min(),
                 info['R_elbow_flex_deg'], info['L_elbow_flex_deg']))
a = np.array(rows)
print(f'{tag} {clip}: frames {n}  clamp max R {a[:,1].max():.1f} L {a[:,2].max():.1f}  arm short max R {a[:,3].max()*1000:.1f} L {a[:,4].max()*1000:.1f} mm  near R {a[:,5].max()*1000:.1f} L {a[:,6].max()*1000:.1f}  leg short {max(a[:,7].max(),a[:,8].max())*1000:.1f} mm  mesh min z {a[:,9].min()*1000:.1f} mm  elbow flex R {a[:,10].min():.0f}-{a[:,10].max():.0f} L {a[:,11].min():.0f}-{a[:,11].max():.0f}  max bone step {max(step):.1f} deg at f{int(np.argmax(step))+1}')
if '--table' in sys.argv:
    for r in rows: print('%3d clampR %5.1f clampL %5.1f shortR %5.1f shortL %5.1f minz %6.1f' % (r[0], r[1], r[2], r[3]*1000, r[4]*1000, r[9]*1000))
