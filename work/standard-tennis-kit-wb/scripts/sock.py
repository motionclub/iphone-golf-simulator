"""Crew socks (right foot built from the body SDF, left = mirror).  Female footwear is fit to the arms-candidate feet/legs."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from sdf import *
from fitbody import *
from shell import build_shell
from kit_common import *

PS = {
    'male': dict(set='male', which=['male_authority'], h=0.0150, z_top=0.300, min_clear=0.0048, enforce=0.0038, cuff=0.034),
    'female': dict(set='female', which=['female_arms_cand'], h=0.0130, z_top=0.285, min_clear=0.0046, enforce=0.0036, cuff=0.030),
    'female_auth': dict(set='female', which=['female_authority'], h=0.0120, z_top=0.285, min_clear=0.0046, enforce=0.0036, cuff=0.030),
}
SUFFIX = {'male': 'male', 'female': 'female', 'female_auth': 'female_auth'}


def mirror_mesh(V, F, N=None):
    V2 = V * np.array([-1, 1, 1])
    F2 = F[:, [0, 2, 1]]
    N2 = None if N is None else N * np.array([-1, 1, 1])
    return V2, F2, N2


def build_sock(gender, side=+1, verbose=True):
    P = PS[gender]
    t0 = time.time()
    bodies = load_set(P['set'], which=P['which'])
    if side < 0:                                   # build the left sock with the right-foot pipeline on the mirrored body
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
        return np.float32(0.0050) + 0.0 * Z

    def cut_fn(Pv):
        return Pv[:, 2] - P['z_top']

    sh = build_shell(bodies, P['set'], 'sock', P['lo'], P['hi'], P['h'], ease_fn, blur_mm=P['h'] * 1000 * 0.9, min_clear=P['min_clear'], cut_fn=cut_fn,
                     verbose=verbose, taubin_iters=6, enforce=([b['tree'] for b in bodies], P['enforce'], [(b['V'], b['F']) for b in bodies]))
    V, F = sh.V, sh.F
    N = vertex_field_normals(sh.g, sh.Sg, V)
    acc = Acc()
    add_sheet(acc, V, F, N, 0, 'sock')
    add_rims_and_inner(acc, V, F, N, t=0.0010, depth=0.02, piped={})
    surf = Surface(V, F, sh.g, sh.Sg)
    # ribbed-cuff band: the top 26 mm of the sock stands 1.4 mm proud with a soft step at its lower edge, plus one ring line in the band
    zb0, zb1 = P['z_top'] - 0.026, P['z_top']
    fm = (V[F][:, :, 2] > zb0 - 0.004).any(1)
    used = np.unique(F[fm])
    remap = -np.ones(len(V), int)
    remap[used] = np.arange(len(used))
    Vb = V[used].copy()
    Nb = N[used]
    stepw = smoothstep(zb0 - 0.002, zb0 + 0.004, Vb[:, 2])
    Vb = Vb + Nb * (0.0014 * stepw)[:, None]
    acc.add(Vb, remap[F[fm]], Nb, 0, 'cuffband')
    ring = ring_at_z(V, F, P['z_top'] - 0.013, 48)
    if ring is not None:
        surf_b = Surface(Vb, remap[F[fm]])
        ribbon(acc, surf_b, ring, 0.0024, 0.0007, 0, spacing=0.0075, closed=True, tag='cuffring')
    Vr, Fr, Nr, Mr = acc.merged()
    tg, tn = acc.tags()
    info = dict(tris=int(len(Fr)), sheet_tris=int(len(F)), top_z=P['z_top'])
    if verbose:
        print(f'  sock[{gender}] right: tris {len(Fr)} (sheet {len(F)}) in {time.time()-t0:.1f}s')
    if side < 0:                                   # back to world space
        Vr, Fr, Nr = Vr * np.array([-1, 1, 1]), Fr[:, [0, 2, 1]], Nr * np.array([-1, 1, 1])
    return dict(V=Vr, F=Fr, N=Nr, M=Mr, T=tg, tagnames=tn, info=info, sheet=(V, F), bodies=bodies)


if __name__ == '__main__':
    gender = sys.argv[sys.argv.index('--') + 1]
    parts = {}
    for side, tag in ((+1, 'R'), (-1, 'L')):
        res = build_sock(gender, side=side)
        parts[tag] = res
        np.savez(f"{WORK}/data/sock{tag}_{SUFFIX[gender]}.npz", V=res['V'], F=res['F'], N=res['N'], M=res['M'], T=res['T'], tagnames=np.array(res['tagnames']))
    a, b = parts['R'], parts['L']
    V = np.concatenate([a['V'], b['V']]); F = np.concatenate([a['F'], b['F'] + len(a['V'])]); N = np.concatenate([a['N'], b['N']]); M = np.concatenate([a['M'], b['M']])
    np.savez(f"{WORK}/data/sock_{SUFFIX[gender]}.npz", V=V, F=F, N=N, M=M)
