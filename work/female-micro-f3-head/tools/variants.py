"""evaluate analytic variants of the head surface at the staged patch directions U and write assembled-order npz meshes for rendering.
python3 variants.py"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, geo, fl, meshlib as ml
V, F, d = ml.load(fl.W / 'data/F1.npz')
vm = json.load(open(fl.W / 'data/work_assembled_vmap.json')); pmap = {int(k): int(v) for k, v in vm['pmap'].items()}
st = np.load(fl.W / 'data/b17_state.npz'); U = st['U']; Pp = st['P'][:len(U)]
res = np.load(fl.W / 'data/phi_resid_b17.npz')['res']
exact = np.linalg.norm(res, axis=1) < 1e-6
print('patch verts', len(U), 'exact-on-Phi', int(exact.sum()))
ids = np.array([pmap[i] for i in range(len(U))])
def save(name, Pn):
    Vn = V.copy(); Vn[ids] = Pn
    np.savez(fl.W / f'data/var_{name}.npz', V=Vn, F=d['F'], Foff=d['Foff'])
    print('saved', name, 'max move mm', float(np.linalg.norm(Vn - V, axis=1).max() * 1000))
H = geo.Head()
# A: as built (sanity)
PA = H.phi(U); PA = np.where(exact[:, None], PA, Pp); save('A_asbuilt', PA)
# B: no profile correction
H2 = geo.Head(); H2.prof_corr = None
PB = H2.phi(U); PB = np.where(exact[:, None], PB, Pp); save('B_noprofcorr', PB)
# C: base only (no features)
PC = H.phi(U, parts=False); PC = np.where(exact[:, None], PC, Pp); save('C_baseonly', PC)
