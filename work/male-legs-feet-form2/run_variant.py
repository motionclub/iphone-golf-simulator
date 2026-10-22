"""Run a parameter variant: assemble, write blend, render a standard view set.  python run_variant.py <name> ['{json overrides}']  (uses Blender's python + `blender -b` for the blend/render)"""
import sys, json, subprocess, pickle, os
sys.path.insert(0, '.')
import numpy as np
from ff_common import *
from ff_build import DEFAULT
import ff_assemble as A
from ff_slopes import slopes_fn
BL = '/Applications/Blender.app/Contents/MacOS/Blender'
name = sys.argv[1]
ov = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
P = dict(DEFAULT); P.update(ov)
y_cut = P.pop('y_cut', -0.095)
from ff_build import ToeRow
_tr = ToeRow(P)
set_origin(P['L'][0], lc_big=float(_tr.lc[0]))
f_cut = float(to_local(np.array([[0.2207, y_cut, 0.0]]), +1)[0, 0])
V, F = load_base()
Vf, Ff, meta, cuts, builds = A.assemble(V, F, P=P, f_cut=f_cut, slopes_fn=slopes_fn)
ne, nb, nm, bad = check_manifold(Ff)
print(f'{name}: verts {len(Vf)} faces {len(Ff)} boundary {nb} nonmanifold {nm} samedir {bad} unvisited {meta["unvisited"]}')
d = W + '/tmp'
np.save(f'{d}/V_{name}.npy', Vf)
pickle.dump(dict(faces=Ff, kept_idx=meta['kept_idx'], n_orig=meta['n_orig']), open(f'{d}/F_{name}.pkl', 'wb'))
json.dump(P, open(f'{d}/P_{name}.json', 'w'))
subprocess.run([BL, '-b', '--factory-startup', '--python', W + '/ff_blend.py', '--', BASE_BLEND, f'{d}/V_{name}.npy', f'{d}/F_{name}.pkl', f'{d}/{name}.blend'], capture_output=True)
out = f'{W}/proof/{name}'
os.makedirs(out, exist_ok=True)
views = ["front:0:12:0.22:-0.18:0.04:0.24", "q3lat:38:22:0.22:-0.16:0.04:0.30", "q3med:-38:22:0.22:-0.16:0.04:0.30:clip0.5",
         "side:90:6:0.22:-0.10:0.05:0.34", "top:0:89:0.22:-0.10:0.0:0.34:clip0.13", "frontw:0:12:0.22:-0.18:0.04:0.24:wire"]
r = subprocess.run([BL, '-b', '--factory-startup', '--python', W + '/closeup.py', '--', f'{d}/{name}.blend', out] + views, capture_output=True, text=True)
from PIL import Image
names = [v.split(':')[0] for v in views]
ims = [Image.open(f'{out}/{n}.png').convert('RGB').resize((500, 500), Image.LANCZOS) for n in names]
S = Image.new('RGB', (1500, 1000))
for i, im in enumerate(ims): S.paste(im, ((i % 3) * 500, (i // 3) * 500))
S.save(f'{out}/sheet.png'); print('sheet', f'{out}/sheet.png')
