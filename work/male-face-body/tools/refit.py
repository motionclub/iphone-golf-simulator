"""python3 tools/refit.py <params in> <result tag> <params out>: add least-squares bump amplitude increments from the residual of <tag>."""
import sys, json, types; sys.modules.setdefault('bpy', types.ModuleType('bpy')); sys.path.insert(0, __file__.rsplit('/', 1)[0])
import numpy as np, off
p = json.load(open(sys.argv[1])); h = off.Head(); R = off.ref_tables()
G = np.load(f'eval/{sys.argv[2]}_G.npy'); ys = np.arange(-2, -134, -1.0); _, fr = off.slices(G, h.tri, ys)
err = np.interp(ys, R['y'][::-1], R['front'][::-1]) - fr
prof = [b for b in p['bumps'] if b[0] == 0]
B = np.array([np.exp(-.5 * ((ys - b[1]) / b[3]) ** 2) for b in prof]).T
amp, *_ = np.linalg.lstsq(B, err, rcond=None)
for b, a in zip(prof, amp): b[6] = round(b[6] + float(a), 2)
json.dump(p, open(sys.argv[3], 'w')); print('increments', np.round(amp, 2).tolist())
