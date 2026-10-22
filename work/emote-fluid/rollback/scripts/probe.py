"""probe.py <male|female> <clip> [t1,t2,...|every:N]  : solve some frames of an overhaul clip and print the solver diagnostics (python3.13 of Blender)."""
import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
import kin
from kin import w2a
a_ = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
tag, clip = a_[0], a_[1]
spec = a_[2] if len(a_) > 2 else 'every:5'
H = EH.EmoHero(tag)
C = EC.build(clip, H)
nF = int(round(C.length * 30)) + 1
frames = list(range(0, nF, int(spec[6:]))) if spec.startswith('every:') else [int(round(float(x) * 30)) for x in spec.split(',')]
print(f'{clip} {tag} length={C.length} frames={nF}')
print(' f    t   Rshort Rclamp Lshort Lclamp  rkMinZ  kneeL kneeR  pelDrop   gripAuth(r,f,u)         shaft')
for f in frames:
    t = f / 30.0
    d = C.solve(t)
    info = d['info']
    P = d['P']
    rk_o, rk_R = info['rk_origin'], info['rk_R']
    mz = EC.racket_min_z(rk_o, rk_R)
    g = w2a(rk_o - H.O)
    sh = w2a(rk_R[:, 1])
    print(f'{f:3d} {t:5.2f}  {info["R_arm_short"]:6.3f} {info["R_wrist_clamp_deg"]:6.1f} {info["L_arm_short"]:6.3f} {info["L_wrist_clamp_deg"]:6.1f}  {mz:6.3f}  {info["lf_knee_flex_deg"]:5.1f} {info["rf_knee_flex_deg"]:5.1f}  {info.get("pelvis_auto_drop", 0):6.3f}   ({g[0]:5.2f},{g[1]:5.2f},{g[2]:5.2f})  ({sh[0]:5.2f},{sh[1]:5.2f},{sh[2]:5.2f})')
