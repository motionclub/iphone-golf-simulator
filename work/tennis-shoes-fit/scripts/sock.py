"""Crew socks rebuilt on THESE feet (right sock from the right foot, left sock from the left foot via the mirrored-body pipeline).
Same design as the start kit (2 mm knit wall, ribbed cuff stands 1.4 mm proud, cuff ring), fit to the SHA-verified bodies:
male  = work/male-pelvis-form3/export/merged_fd04bc28.blend (d6c4dcfb...), female = work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend (a1d73a33...)."""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from sdf import *
from fitbody import *
from shell import build_shell
from kit_common import *


def drop_small_islands(res, min_verts=40):
    V, F = res['V'], res['F']
    par = np.arange(len(V))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for a, b, c in F.tolist():
        for u, v in ((a, b), (b, c)):
            ru, rv = find(u), find(v)
            if ru != rv:
                par[ru] = rv
    lab = np.array([find(i) for i in range(len(V))])
    ids, cnt = np.unique(lab[np.unique(F)], return_counts=True)
    small = set(ids[cnt < min_verts].tolist())
    if not small:
        return res, 0
    keep = np.array([lab[f[0]] not in small for f in F.tolist()])
    out = dict(res)
    F2 = F[keep]
    used = np.unique(F2)
    remap = -np.ones(len(V), int)
    remap[used] = np.arange(len(used))
    out['V'] = V[used]
    out['F'] = remap[F2]
    out['LN'] = res['LN'].reshape(-1, 3, 3)[keep].reshape(-1, 3)
    out['M'] = res['M'][keep]
    out['T'] = res['T'][keep]
    return out, int((~keep).sum())

PS = {      # outer face >= min_clear off the skin; knit wall tv inward -> inner face >= 2.5 mm off the skin (a sock is snug by nature)
    'male': dict(set='male', which=['male_form3'], h=0.0150, z_top=0.300, min_clear=0.0066, enforce=0.0064, cuff=0.034, tv=0.0020),
    'female': dict(set='female', which=['female_full'], h=0.0130, z_top=0.285, min_clear=0.0064, enforce=0.0062, cuff=0.030, tv=0.0020),
}


def build_sock(gender, side=+1, verbose=True):
    P = PS[gender]
    t0 = time.time()
    bodies = load_set(P['set'], which=P['which'])
    if side < 0:                                   # left sock = right-foot pipeline on the mirrored body
        for b in bodies:
            b['V'] = b['V'] * np.array([-1, 1, 1])
            b['F'] = b['F'][:, [0, 2, 1]]
            b['tree'] = bvh_from(b['V'], b['F'])
    Vb = bodies[0]['V']
    m = (Vb[:, 0] > 0.02) & (Vb[:, 2] < P['z_top'] + 0.06)
    lo = (Vb[m, 0].min() - 0.05, Vb[m, 1].min() - 0.07, -0.045)
    hi = (Vb[m, 0].max() + 0.05, Vb[m, 1].max() + 0.07, P['z_top'] + 0.045)
    P = dict(P, lo=lo, hi=hi)

    def ease_fn(X, Y, Z):
        return np.float32(0.0064) + 0.0 * Z

    def cut_fn(Pv):
        return Pv[:, 2] - P['z_top']

    sh = build_shell(bodies, P['set'], 'sock', P['lo'], P['hi'], P['h'], ease_fn, blur_mm=P['h'] * 1000 * 0.9, min_clear=P['min_clear'], cut_fn=cut_fn,
                     verbose=verbose, taubin_iters=6, enforce=([b['tree'] for b in bodies], P['enforce'], [(b['V'], b['F']) for b in bodies]))
    V, F = sh.V, sh.F
    N = vertex_field_normals(sh.g, sh.Sg, V)
    acc = Acc()
    # ribbed cuff: the top 26 mm stands 1.4 mm proud (soft step at its lower edge) -- a wall-thickness change of the one closed shell
    zb0, zb1 = P['z_top'] - 0.026, P['z_top']
    stepw = smoothstep(zb0 - 0.002, zb0 + 0.004, V[:, 2])
    V = ensure_inner_clearance(V, N, P['tv'], [b['tree'] for b in bodies], 0.0025)         # inner knit wall >= 2.5 mm off the foot (toe tips, heel)
    V = fix_inner_overlaps(V, F, N, P['tv'], [b['tree'] for b in bodies])                  # and no inner triangle cuts a toe tip
    Vo = V + N * (0.0014 * stepw)[:, None]
    tvv = P['tv'] + 0.0014 * stepw
    add_closed_shell(acc, Vo, F, N, tvv, 0, tag='sock')
    surf = Surface(Vo, F, sh.g, sh.Sg)
    ring = ring_at_z(Vo, F, P['z_top'] - 0.013, 48)
    if ring is not None:
        ribbon(acc, surf, ring, 0.0024, 0.0007, 0, spacing=0.0075, closed=True, tag='cuffring', base=0.0005)
    res = finalize_acc(acc)
    res, ndrop = drop_small_islands(res, 40)          # stray iso-surface slivers (a 12-vertex fleck at the female toe tips)
    res['topo'] = mesh_topology(res['V'], res['F'])
    info = dict(dropped_sliver_faces=ndrop, tris=int(len(res['F'])), sheet_tris=int(len(F)), top_z=P['z_top'], tv=P['tv'], topo=res['topo'], body_set=P['which'][0])
    if verbose:
        print(f'  sock[{gender}] right: tris {len(res["F"])} (sheet {len(F)}) in {time.time()-t0:.1f}s topo {res["topo"]}')
    if side < 0:                                   # back to world space (mirror: reflect x, swap the winding, keep per-corner normals in step)
        res = mirror_part(res)
    res.update(info=info)
    return res


if __name__ == '__main__':
    gender = sys.argv[sys.argv.index('--') + 1]
    for side, tag in ((+1, 'R'), (-1, 'L')):
        res = build_sock(gender, side=side)
        save_part(f"{WORK}/data/sock{tag}_{gender}.npz", res)
        json.dump(res['info'], open(f"{WORK}/data/sock{tag}_{gender}_info.json", 'w'), indent=1)
