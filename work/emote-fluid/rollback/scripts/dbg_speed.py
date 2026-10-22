import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts'))
import emo_hero as EH
import emo_clips2 as EC
a_ = sys.argv[sys.argv.index('--') + 1:]
tag, clip = a_[0], a_[1]
H = EH.EmoHero(tag); C = EC.build(clip, H); ix = H.rig.idx
nF = int(round(C.length * 30)) + 1
xs = C.clearance_track()
cl = {nm: np.array([C.solve(k / 30.0)['info']['Pos'][ix[nm]] for k in range(nF)]) for nm in ('LeftHand', 'RightHand')}
sv = C._track; C._track = np.zeros_like(sv)
nm_ = {nm: np.array([C.solve(k / 30.0)['info']['Pos'][ix[nm]] for k in range(nF)]) for nm in ('LeftHand', 'RightHand')}
C._track = sv
for nm in cl:
    vc = np.linalg.norm(np.diff(cl[nm], axis=0), axis=1) * 30
    vn = np.linalg.norm(np.diff(nm_[nm], axis=0), axis=1) * 30
    d = vc - vn
    top = np.argsort(-d)[:5]
    print(nm, 'top speed-added frames:', [(int(k), round(float(d[k]), 2), round(float(vc[k]), 2), round(float(vn[k]), 2)) for k in top])
print('track steps L', np.round(np.linalg.norm(np.diff(xs[:, 0, :3], axis=0), axis=1).max(), 3), 'R', np.round(np.linalg.norm(np.diff(xs[:, 1, :3], axis=0), axis=1).max(), 3))
i = int(np.argmax(np.linalg.norm(np.diff(xs[:, 0, :3], axis=0), axis=1)))
print('largest L step at frame', i, np.round(xs[i-2:i+4, 0, :3], 3).tolist())
