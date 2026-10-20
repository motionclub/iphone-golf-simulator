"""Full pipeline: base (shared ArtDir arrays) -> fair + relief (positions only, old topology) -> forefoot rebuild -> blend + arrays.
python build_all.py <name> [design.json] ['{"overrides"}']  (run with Blender's python 3.13; blend/render steps spawn `blender -b`)"""
import sys, json, subprocess, pickle, os
sys.path.insert(0, '.')
import numpy as np
from ff_common import *
from ff_build import DEFAULT, ToeRow
import ff_assemble as A
from ff_slopes import slopes_fn
import relief as R
BL = '/Applications/Blender.app/Contents/MacOS/Blender'

name = sys.argv[1]
design = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and sys.argv[2].endswith('.json') else {}
ov = json.loads(sys.argv[-1]) if len(sys.argv) > 2 and sys.argv[-1].startswith('{') else {}
P = dict(DEFAULT); P.update(design); P.update(ov)
relief_cfg = P.pop('relief', {})
y_cut = P.pop('y_cut', -0.095)
set_origin(P['L'][0], lc_big=float(ToeRow(P).lc[0]))
f_cut = float(to_local(np.array([[FRAME_ORIGIN[0], y_cut, 0.0]]), +1)[0, 0])

V0, F = load_base()
zone = zone_mask_eff(len(V0))
if relief_cfg.get('on', True):
    Vf = R.fair_tube(V0, F, zone, iters=relief_cfg.get('fair_iters', 12))
    sc = relief_cfg.get('scale', {})
    def scale_by(n):
        for k, v in sc.items():
            if n.startswith(k): return v
        return sc.get('default', 1.8)
    V1, dV, info = R.apply_relief(Vf, F, zone, scale_by=scale_by)
    # keep the soles on the ground plane: nothing below Z0 (float32-exact value of the PASS minimum)
    V1[:, 2] = np.where(zone, np.maximum(V1[:, 2], Z0), V1[:, 2])
else:
    V1 = V0.copy()
np.save(W + f'/tmp/V1_{name}.npy', V1)
Vn, Fn, meta, cuts, builds = A.assemble(V1, F, P=P, f_cut=f_cut, slopes_fn=slopes_fn)
# ground plane: nothing in the rebuilt / reshaped foot may sit below the PASS sole plane
foot_sel = (Vn[:, 2] < 0.06) & (np.abs(Vn[:, 0]) > 0.10)
Vn[foot_sel, 2] = np.maximum(Vn[foot_sel, 2], Z0)
ne, nb, nm, bad = check_manifold(Fn)
print(f'{name}: verts {len(Vn)} faces {len(Fn)} boundary {nb} nonmanifold {nm} samedir {bad} unvisited {meta["unvisited"]}')
d = W + '/tmp'
np.save(f'{d}/V_{name}.npy', Vn)
pickle.dump(dict(faces=Fn, kept_idx=meta['kept_idx'], n_orig=meta['n_orig'], tags=meta['tags']), open(f'{d}/F_{name}.pkl', 'wb'))
json.dump(dict(P=P, relief=relief_cfg, y_cut=y_cut, f_cut=f_cut), open(f'{d}/P_{name}.json', 'w'), indent=1, default=float)
r = subprocess.run([BL, '-b', '--factory-startup', '--python', W + '/ff_blend.py', '--', BASE_BLEND, f'{d}/V_{name}.npy', f'{d}/F_{name}.pkl', f'{d}/{name}.blend'], capture_output=True, text=True)
print([l for l in r.stdout.splitlines() if 'has_custom' in l or 'tris' in l or 'SAVED' in l])
