"""probe_sum.py <male|female> <clip> : solve every frame of an overhaul clip and print the worst arm shortfall / wrist clamp / knee flex / racket-below-floor numbers (python3.13 of Blender)."""
import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
from kin import w2a
a_ = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
tag, clip = a_[0], a_[1]
H = EH.EmoHero(tag)
C = EC.build(clip, H)
nF = int(round(C.length * 30)) + 1
rows = []
for f in range(nF):
    d = C.solve(f / 30.0)
    i = d['info']
    rk_o, rk_R = i['rk_origin'], i['rk_R']
    rows.append((f, i['R_arm_short'], i['R_wrist_clamp_deg'], i['L_arm_short'], i['L_wrist_clamp_deg'], i['lf_knee_flex_deg'], i['rf_knee_flex_deg'], EC.racket_min_z(rk_o, rk_R) if d.get('racket') is None else np.nan))
a = np.array(rows, float)
def worst(col, name, fmt='%.3f'):
    k = int(np.nanargmax(a[:, col])); return f'{name} max ' + fmt % a[k, col] + f' @f{int(a[k, 0])}'
print(f'{clip} {tag} frames={nF}:', worst(1, 'Rshort'), '|', worst(2, 'Rclamp', '%.1f'), '|', worst(3, 'Lshort'), '|', worst(4, 'Lclamp', '%.1f'), '|', worst(5, 'kneeL', '%.0f'), '|', worst(6, 'kneeR', '%.0f'))
bad = [int(r[0]) for r in a if r[1] > 0.005 or r[3] > 0.005]
print('  frames with arm shortfall > 5 mm:', len(bad), bad[:40])
cl = [int(r[0]) for r in a if r[2] > 5 or r[4] > 5]
print('  frames with wrist clamp > 5 deg :', len(cl), cl[:40])
