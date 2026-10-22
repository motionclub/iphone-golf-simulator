"""Fit Gaussian bump amplitudes (dz) on the midline so the warped profile meets the reference (least squares, linearised), then print.
python3 tools/fitbumps.py <params.json>  (uses params 'bumps' as the basis; amplitudes column 6 are refit)"""
import sys, json, types; sys.modules.setdefault('bpy', types.ModuleType('bpy')); sys.path.insert(0, __file__.rsplit('/', 1)[0])
import numpy as np, off
p = json.load(open(sys.argv[1])); h = off.Head(); P = dict(off.DEFAULT); P.update(p['warp']); R = off.ref_tables()
G = h.U(h.warp(h.base, P)) * 1000; ys = np.arange(-2, -134, -1.0); _, fr = off.slices(G, h.tri, ys)
ref = np.interp(ys, R['y'][::-1], R['front'][::-1]); err = ref - fr
mid = [b for b in p['bumps'] if b[0] == 0]
B = np.array([np.exp(-.5 * ((ys - b[1]) / b[3]) ** 2) for b in mid]).T
amp, *_ = np.linalg.lstsq(B, err, rcond=None)
print('amps', np.round(amp, 2).tolist());
for b, a in zip(mid, amp): b[6] = round(float(a), 2)
if len(sys.argv) > 2: json.dump(p, open(sys.argv[2], 'w'))
print('residual rms', round(float(np.sqrt(np.mean((err - B @ amp) ** 2))), 2), 'before', round(float(np.sqrt(np.mean(err ** 2))), 2))
print(' '.join(f'{y:.0f}:{e:+.1f}' for y, e in zip(ys[::3], (err - B @ amp)[::3])))
