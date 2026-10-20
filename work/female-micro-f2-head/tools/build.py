"""full head build (chart space): cage -> graded refinement -> Phi -> carve eye apertures / nostrils / seam chain -> outputs.
blender -b --factory-startup --python build.py -- [tag] [params.json]"""
import sys, json, time, pickle
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import numpy as np
import fl, geo, cage, mesher, zones, loftf, feat_f, carve
from fl import MM

def ring_correction(H, U, P, pinned, ring_pos, collar_u):
    """make the neck pass exactly through the (irregular) collar ring: blend the ring misfit upward over ~3 cm"""
    pk = np.array(sorted(pinned)); rp = np.array([pinned[k] for k in pk])
    dl = rp - H.phi(U[pk])
    th = np.arctan2(rp[:, 1] - fl.Y0, rp[:, 0]); o = np.argsort(th); th = th[o]; dl = dl[o]
    thv = np.arctan2(P[:, 1] - fl.Y0, P[:, 0])
    thx = np.concatenate([th - 2 * np.pi, th, th + 2 * np.pi]); dx = np.concatenate([dl, dl, dl])
    D = np.stack([np.interp(thv, thx, dx[:, k]) for k in range(3)], axis=1)
    w = 1.0 - fl.sstep(1.405, 1.440, P[:, 2])
    return P + w[:, None] * D


def build(prm=None, tag='b1', max_level=3, verbose=True):
    t0 = time.time()
    d = np.load(fl.W / 'data/ring.npz'); ring_pos = d['pos']
    H = geo.Head(prm)
    H0 = geo.Head(prm)
    cg = cage.build_cage(ring_pos, geo.C, H=H0)
    lvl = zones.make_level_fn(H)
    U, F, depth, n_orig = mesher.refine(cg, H, lvl, max_level=max_level, verbose=verbose)
    pinned = {int(k): v for k, v in cg['pinned'].items()}
    P = H.phi(U)
    for k, v in pinned.items(): P[k] = v
    P = ring_correction(H, U, P, pinned, ring_pos, None)
    for k, v in pinned.items(): P[k] = v
    info = dict(n_orig=n_orig, pinned=pinned, tag=tag, collar=[int(c) for c in cg['collar']], collar_order=[int(o) for o in cg['collar_order']])
    return H, U, F, P, info


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    tag = argv[0] if argv else 'b1'
    H, U, F, P, info = build(tag=tag)
    tris = sum(len(f) - 2 for f in F)
    print('verts', len(P), 'faces', len(F), 'tris', tris)
    loftf.save_npz(str(fl.W / f'data/{tag}.npz'), P, F)
    np.save(fl.W / f'data/{tag}_U.npy', U)
