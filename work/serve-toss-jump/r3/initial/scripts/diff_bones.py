"""diff_bones.py <male|female> [before.npz after.npz] : per-bone max / frames-changed of the Serve between the job-start clip and the new one (degrees); hips location too."""
import json, sys
import numpy as np
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump'
tag = sys.argv[1]
A = np.load(sys.argv[2] if len(sys.argv) > 2 else f'{W}/before/gen_serve_{tag}.npz', allow_pickle=True)
B = np.load(sys.argv[3] if len(sys.argv) > 3 else f'{W}/data/gen_serve_{tag}.npz', allow_pickle=True)
names = [b['name'] for b in json.load(open(f'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/data/rig_{tag}.json'))['bones']]
qa, qb = A['quats'], B['quats']
ang = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(qa * qb, axis=2)), 0, 1)))   # (frames, bones)
print('frames', len(qa), len(qb), 'hips loc max diff mm', float(np.abs(A['hips'] - B['hips']).max() * 1000))
rows = []
for i, n in enumerate(names):
    if n == 'Root': continue
    rows.append((float(ang[:, i].max()), n, int((ang[:, i] > 0.05).sum()), int(np.argmax(ang[:, i]))))
rows.sort(reverse=True)
arm = ('Left', 'Right')
for m, n, c, f in rows:
    if m > 0.05: print('%-24s max %7.2f deg  frames>0.05: %2d  worst frame %d' % (n, m, c, f))
print('bones unchanged (<=0.05 deg):', sum(1 for r in rows if r[0] <= 0.05), 'of', len(rows))
