"""Score the mesh under the plate's own fitted SH lighting. python3.13 shlit.py <tag>"""
import sys, subprocess
sys.path.insert(0, '.')
from plateview import *
tag = sys.argv[1]; V = np.load(f'data/V_{tag}.npy'); Nn = vertex_normals(V)
base = np.load('data/V_base.npy'); Nb = vertex_normals(base)
Lm = {}
for name in ('front', 'back'):
    vw = View(name); body = (base[:, 2] < 1.40) & (np.abs(base[:, 0]) < 0.40)
    vis = visible(vw, base, Nb, sel=base[:, 2] < 1.40) & body
    col, row = vw.project(base); I = bilinear(gblur(PLATE, 4.0), col, row)
    c, *_ = np.linalg.lstsq(sh2(Nb[vis]), I[vis], rcond=None)         # lighting fitted ONCE on the baseline mesh, reused for every candidate
    Lm[name] = sh2(Nn) @ c
np.savez(f'r/lum_{tag}.npz', front=Lm['front'], back=Lm['back'])
subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '--python', 'vcrender.py', '--', f'data/V_{tag}.npy', f'r/lum_{tag}.npz', f'r/{tag}sh'], capture_output=True)
from relcorr2 import corr_reg, REG
out = {f'{v[0]}-{rn[:3]}': round(corr_reg(v, f'{tag}sh', z0, z1, 0.12, 1.2, 5.0), 3) for v in ('front', 'back') for rn, (z0, z1) in REG.items()}
print(tag, 'under plate-fitted SH lighting:', out, 'mean %.3f' % np.mean(list(out.values())))
