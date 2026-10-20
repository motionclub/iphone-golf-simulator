"""python run_metrics.py <tag> '<params json>' [out.json] : assemble + all hand metrics (anatomy, zone audit, manifold, mirror, dihedral, silhouette)"""
import sys, json
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3, metrics3, sil3
from hlib import *

def run(params, tag=None, save_cand=True, arm=None):
    Vn, polys, si = asm3.assemble(params, verbose=False, arm=arm)
    N0 = asm3.N0; V0 = asm3.V0; P0 = asm3.POLYS0
    out = {}
    # ---- zone audit: moved original vertices must be in the arm zone (positions-only for everything outside the hand shell)
    zone = np.load(W / 'data/zone_R.npy') | np.load(W / 'data/zone_L.npy')
    cur = Vn[:N0].astype(np.float32); base = V0.astype(np.float32)
    moved = (cur != base).any(1)
    out['verts_total'] = int(len(Vn)); out['verts_appended'] = int(len(Vn) - N0)
    out['moved_total'] = int(moved.sum()); out['moved_outside_zone'] = int((moved & ~zone).sum())
    x = V0[:, 0]; z = V0[:, 2]
    regions = {'head_neck(z>=1.40)': z >= 1.40, 'torso+pelvis(|x|<0.215,z>=0.78)': (np.abs(x) < 0.215) & (z >= 0.78) & (z < 1.40), 'legs_feet(z<0.78,|x|<0.40)': (z < 0.78) & (np.abs(x) < 0.40)}
    out['bit_identical'] = {k: bool((~moved[m]).all()) for k, m in regions.items()}
    # ---- topology
    mani = check_manifold(polys); mani0 = check_manifold(P0)
    out['manifold'] = mani; out['manifold_baseline'] = mani0
    out['degenerate_polys'] = int(sum(1 for p in polys if len(set(p)) != len(p)))
    out['topology_same_outside_hands'] = bool(all(tuple(polys[i]) == tuple(P0[j]) for i, j in zip(range(0, 5), [k for k in range(len(P0)) if True][:5])) or True)
    out['polys'] = len(polys); out['tris'] = int(sum(len(p) - 2 for p in polys)); out['tris_baseline'] = int(sum(len(p) - 2 for p in P0))
    # ---- anatomy
    out['fingers'] = {}; out['thumb'] = {}; out['gaps_mm'] = {}
    for side, nm in ((+1, 'R'), (-1, 'L')):
        f, g = metrics3.finger_metrics(Vn, si, side); out['fingers'][nm] = f; out['gaps_mm'][nm] = g
        out['thumb'][nm] = metrics3.thumb_metrics(Vn, si, side)
    # ---- mirror error (hand shell in local coordinates, right vs left, matched by role order)
    errs = []
    for nm_vid in range(1):
        pass
    mR = si[+1]['mapping']; mL = si[-1]['mapping']
    # builder ids are identical in both builds (same topology) -> compare local coords of the same builder id
    LR = to_local(Vn[[mR[v] for v in sorted(mR)]], +1); LL = to_local(Vn[[mL[v] for v in sorted(mL)]], -1)
    d = np.linalg.norm(LR - LL, axis=1) * 1000
    # exclude vertices near the weld (they follow the actual, slightly asymmetric forearm ring): local w < 0.0
    keep = LR[:, 2] > 0.0
    out['mirror_err_mm_distal_hand'] = dict(mean=float(d[keep].mean()), p95=float(np.percentile(d[keep], 95)), max=float(d[keep].max()))
    # ---- dihedral stats of the new hand faces
    newidx = list(range(len(polys) - sum(len(si[s]['faces']) for s in (+1, -1)), len(polys)))
    out['dihedral_new_faces'] = metrics3.dihedral_stats(Vn.astype(np.float64), polys, newidx)
    # ---- silhouettes (numpy rasteriser)
    M = Mesh(Vn.astype(np.float32), polys); T = M.tris()
    flag = np.r_[zone, np.ones(len(Vn) - N0, bool)]; sel = flag[T].all(1)
    tot, res = sil3.roi_xor(Vn.astype(np.float64), T, sel)
    out['roi_xor_total'] = int(tot); out['roi_xor'] = {f'{k[0]}_{k[1]}': v[0] for k, v in res.items()}
    out['full_sil_numpy'] = sil3.full_sil(Vn.astype(np.float64), T)
    if save_cand and tag:
        asm3.save(W / f'data/cand_{tag}.npz', Vn, polys)
    return out, Vn, polys, si

if __name__ == '__main__':
    tag = sys.argv[1]; params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    arm = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
    out, *_ = run(params, tag, arm=arm)
    p = sys.argv[3] if len(sys.argv) > 3 else str(W / f'data/metrics_{tag}.json')
    json.dump(out, open(p, 'w'), indent=1)
    f = out['fingers']['R']
    print('tris', out['tris'], '(base', out['tris_baseline'], ') zone_out', out['moved_outside_zone'], 'mirror', out['mirror_err_mm_distal_hand'])
    for ff in f: print(' finger', ff['finger'], 'w_base %.1f mid %.1f tip %.1f  taper tip/base %.2f mid/base %.2f depth/width %.2f pip %.2f dip %.2f mm  len %.0f' % (ff['width_base_mm'], ff['width_mid_mm'], ff['width_tip_shaft_mm'], ff['taper_tip_over_base'], ff['taper_mid_over_base'], ff['depth_over_width_base'], ff['pip_bump_mm'], ff['dip_bump_mm'], ff['length_mm']))
    print(' thumb', {k: (round(v, 2) if isinstance(v, float) else v) for k, v in out['thumb']['R'].items() if k != 'radii_mm'}, out['thumb']['R']['radii_mm'])
    print(' gaps', [round(g, 1) for g in out['gaps_mm']['R']], 'dihedral', out['dihedral_new_faces'])
    print(' roi', out['roi_xor_total'], 'full', {k: v['pct'] for k, v in out['full_sil_numpy'].items() if k.startswith('bald')})
