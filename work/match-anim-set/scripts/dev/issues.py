"""dev/issues.py <hero> [Clip...]  : run the tracker + solver (numpy only) and list the problem frames of each clip."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trk
tag = sys.argv[1]
names = sys.argv[2:] or list(trk.CL.BUILDERS.keys())
rig, solver = trk.load(tag)
FPS = 30.0
tot = {}
for n in names:
    r = trk.run(tag, n, rig, solver, quiet=True)
    infos = r['infos']; N = r['N']; dq = r['dq']
    flags = []
    for i, inf in enumerate(infos):
        m = []
        for k, thr in (('R_arm_short', 0.012), ('L_arm_short', 0.012), ('lf_short', 0.012), ('rf_short', 0.012), ('racket_shift', 0.02)):
            if inf.get(k, 0) > thr: m.append('%s %.1fcm' % (k, inf[k] * 100))
        for k in ('lf_knee_flex_deg', 'rf_knee_flex_deg'):
            if inf.get(k, 0) > 105: m.append('%s %.0f' % (k, inf[k]))
        if abs(inf.get('R_wrist_twist_deg', 0)) > 110: m.append('Rtw %.0f' % inf['R_wrist_twist_deg'])
        if inf.get('R_wrist_clamp_deg', 0) > 1: m.append('Rclamp %.0f' % inf['R_wrist_clamp_deg'])
        if inf.get('pelvis_auto_drop', 0) > 0.03: m.append('pelvis_drop %.0fcm' % (inf['pelvis_auto_drop'] * 100))
        if m: flags.append('t=%.2f %s' % (i / FPS, '; '.join(m)))
    arm = dq[:, r['arm_b']]
    big = [(int(i) + 1, int(j)) for i, j in zip(*np.where(arm > 90))]
    ci = r['ci']
    ce = '' if ci is None else ' contact f%d err sh/fc %.0f/%.0f' % (ci, r['shE'][ci], r['fcE'][ci])
    print('%-15s N=%2d track %.1fs  flags %2d  arm>90deg steps %d (frames %s)%s' % (n, N, r['track_s'], len(flags), len(big), sorted(set(f / FPS for f, _ in big)), ce))
    for f in flags[:6]:
        print('      ', f)
