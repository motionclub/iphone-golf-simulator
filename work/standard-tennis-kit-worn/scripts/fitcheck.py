"""Fit checks: garment vs body clearance + triangle overlap (BVH), garment vs garment overlap.  Run inside Blender."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from fitbody import *


def clearance(Vg, tree_body, sample_tris=None):
    """per-vertex signed distance (sign from the nearest face normal): positive = outside the body."""
    d = np.empty(len(Vg))
    for i, p in enumerate(Vg.tolist()):
        loc, n, idx, dist = tree_body.find_nearest(p)
        s = (p[0] - loc[0]) * n[0] + (p[1] - loc[1]) * n[1] + (p[2] - loc[2]) * n[2]
        d[i] = dist if s >= 0 else -dist
    return d


def tri_centroid_clearance(Vg, Fg, tree_body):
    C = Vg[Fg].mean(1)
    return clearance(C, tree_body)


def overlap_pairs(Vg, Fg, Vb, Fb):
    tg = bvh_from(Vg, Fg)
    tb = bvh_from(Vb, Fb)
    return tg.overlap(tb)


def check_garment(name, Vg, Fg, bodies, min_ok=0.0010, verbose=True, keep_pairs=False, nohand=False):
    """returns dict per body: min vertex clearance, min centroid clearance, #verts below 0 / min_ok, #overlapping triangle pairs."""
    out = {}
    for b in bodies:
        tr = b['tree_nohand'] if nohand and 'tree_nohand' in b else b['tree']
        d = clearance(Vg, tr)
        dc = tri_centroid_clearance(Vg, Fg, tr)
        if nohand and 'mesh_nohand' in b:
            pairs = overlap_pairs(Vg, Fg, *b['mesh_nohand'])
        else:
            pairs = overlap_pairs(Vg, Fg, b['V'], b['F'])
        res = dict(min_vertex=float(d.min()), min_centroid=float(dc.min()), neg_verts=int((d < 0).sum()), below_min=int((d < min_ok).sum()),
                   overlap_pairs=len(pairs), verts=len(Vg), p05=float(np.percentile(d, 5)))
        if keep_pairs:
            res['_pairs'] = pairs
            res['_d'] = d
        out[b['name']] = res
        if verbose:
            print(f"   [{name} vs {b['name']}{' (hands excluded)' if nohand and b['name'] != 'female_authority' else ''}] min {res['min_vertex']*1000:+.2f} mm  (centroid {res['min_centroid']*1000:+.2f})  neg {res['neg_verts']}  <{min_ok*1000:.1f}mm {res['below_min']}  overlap tri pairs {res['overlap_pairs']}")
    return out


if __name__ == '__main__':
    gender, names = sys.argv[sys.argv.index('--') + 1], sys.argv[sys.argv.index('--') + 2]
    bodies = load_set(gender)
    add_nohand_trees(bodies, gender)
    nh = (len(sys.argv) > sys.argv.index('--') + 3 and sys.argv[sys.argv.index('--') + 3] == 'nohand')
    for nm in names.split(','):
        d = np.load(f'{WORK}/data/{nm}_{gender}.npz')
        check_garment(nm, d['V'], d['F'], bodies, nohand=nh)
