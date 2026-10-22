"""quickgate.py <coords.npy> : fast binary-ish checks used while iterating (full gates run in gates3.py)"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
import numpy as np
import seam
from torso2 import *
import torso2 as t2

def quick(co, verbose=True):
    out = {}
    out['border_moved'] = int((np.abs(co[BORDER] - CO0[BORDER]).max(1) > 0).sum())
    out['outside_zone_moved'] = int((np.abs(co[~T] - CO0[~T]).max(1) > 0).sum())
    bs, bm = seam.border_steps(co)
    out['step_legs_mm'] = round(bs['legs']['max_mm'], 2); out['step_arm_mm'] = round(bs['arm']['max_mm'], 2); out['step_top_mm'] = round(bs['top']['max_mm'], 2)
    a1 = seam.dihedral(co); a0 = seam.dihedral(CO0); z = seam.ZPAIR
    out['dih_gt40'] = int((z & (a1 > 40)).sum()); out['dih_gt40_orig'] = int((z & (a0 > 40)).sum())
    out['dih_max'] = round(float(a1[z].max()), 1)
    # flipped triangles vs original in zone
    tri = TRI
    def fn(c):
        v0, v1, v2 = c[tri[:, 0]], c[tri[:, 1]], c[tri[:, 2]]; n = np.cross(v1 - v0, v2 - v0); return n / np.maximum(np.linalg.norm(n, axis=1), 1e-18)[:, None]
    zt = T[tri].any(1); dot = (fn(CO0) * fn(co)).sum(1)
    out['flipped_zone_tris'] = int(((dot < 0) & zt).sum()); out['turned_gt60'] = int(((dot < 0.5) & zt).sum())
    # contour error front/back
    fe, be = section_extents(co); fe, be = fillnan(fe), fillnan(be)
    m = (ZG >= 0.84) & (ZG <= 1.30)
    ef = np.array([plate_front(z_) for z_ in ZG]) - fe; eb = np.array([plate_back(z_) for z_ in ZG]) - be
    out['contour_front_mean_mm'] = round(1000 * float(np.abs(ef[m]).mean()), 2); out['contour_back_mean_mm'] = round(1000 * float(np.abs(eb[m]).mean()), 2)
    out['contour_front_max_mm'] = round(1000 * float(np.abs(ef[m]).max()), 1); out['contour_back_max_mm'] = round(1000 * float(np.abs(eb[m]).max()), 1)
    out['max_move_mm'] = round(1000 * float(np.linalg.norm(co - CO0, axis=1).max()), 1)
    lim = {'step_legs_mm': 8, 'step_arm_mm': 10, 'step_top_mm': 1, 'border_moved': 0, 'outside_zone_moved': 0, 'flipped_zone_tris': 0}
    ok = all(out[k] <= v for k, v in lim.items()) and out['dih_gt40'] <= out['dih_gt40_orig'] and out['turned_gt60'] <= 2
    out['QUICK_PASS'] = bool(ok)
    if verbose:
        print(json.dumps(out))
    return out

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p); quick(np.load(p))
