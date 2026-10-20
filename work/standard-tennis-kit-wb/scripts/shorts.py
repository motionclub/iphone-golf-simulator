"""Male tennis shorts: SDF shell -> clips -> rims/inner bands -> waistband stitching, pocket slash, side seam, hem piping."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from sdf import *
from fitbody import *
from shell import build_shell
from kit_common import *

P = dict(set='male', h=0.0145, lo=(-0.34, -0.28, 0.46), hi=(0.34, 0.20, 1.10),
         z_wt=0.965, z_wb=0.922, hem=0.575, hem_rise=0.024,
         ease_waist=0.008, ease_leg=0.034, blur=26.0, min_clear=0.0035, center=(0.0, -0.04), flare=0.016)


def build_shorts(verbose=True):
    t0 = time.time()
    bodies = load_set(P['set'])
    zwt, zwb = P['z_wt'], P['z_wb']

    def ease_fn(X, Y, Z):
        zz = np.array([1.00, 0.95, 0.90, 0.82, 0.74, 0.66, 0.58])
        ee = np.array([0.008, 0.009, 0.014, 0.022, 0.029, 0.032, 0.034])
        band = 0.0030 * smoothstep(zwb - 0.010, zwb + 0.004, Z)                 # the elastic band stands slightly proud
        flare = P['flare'] * smoothstep(0.84, 0.62, Z) * smoothstep(0.115, 0.185, np.abs(X))      # boxy leg: extra ease on the OUTER side only
        return (np.interp(Z, zz[::-1], ee[::-1]) + band + flare).astype(np.float32)

    def cut_fn(Pv):
        x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
        z_hem = P['hem'] + P['hem_rise'] * smoothstep(0.10, 0.215, np.abs(x))
        return np.maximum(z - zwt, z_hem - z)

    sh = build_shell(bodies, P['set'], 'shorts', P['lo'], P['hi'], P['h'], ease_fn, blur_mm=P['blur'], min_clear=P['min_clear'],
                     cut_fn=cut_fn, verbose=verbose)
    V, F = sh.V, sh.F
    N = vertex_field_normals(sh.g, sh.Sg, V)
    loops = boundary_loops(F)
    cz = [V[l][:, 2].mean() for l in loops]
    top_i = int(np.argmax(cz))
    acc = Acc()
    add_sheet(acc, V, F, N, 0)
    add_rims_and_inner(acc, V, F, N, t=0.002, depth=0.014, piped={})
    surf = Surface(V, F, sh.g, sh.Sg)
    cen = P['center']
    # ---- waistband stitching rings
    for dz, w, lift in ((0.0, 0.0030, 0.0009), (0.0245, 0.0020, 0.0006)):
        ring = ring_at_z(V, F, zwb + dz, 64)
        if ring is not None:
            ribbon(acc, surf, ring, w, lift, 0, spacing=0.0075, closed=True, tag='waistring')
    # ---- pocket slash + side seam (both sides)
    for sgn in (+1, -1):
        th = [np.radians(a) * sgn for a in (52, 66, 80, 90)]
        zz = [zwb - 0.004, zwb - 0.030, zwb - 0.062, zwb - 0.092]
        ribbon(acc, surf, list(zip(th, zz)), 0.0030, 0.0008, 1, spacing=0.004, taper_end=0.010, tag='pocket', polar=cen)
    # side seam piping from the waistband to the hem (outer side of each leg)
    for sgn in (+1, -1):
        pts = []
        for z in np.linspace(zwb - 0.098, P['hem'] + P['hem_rise'] + 0.012, 8):
            cxy = (0.0, cen[1]) if z > 0.80 else (sgn * 0.13, cen[1])
            loc, _ = surf.cast_polar(cxy, [sgn * np.pi / 2], [z])
            pts.append(loc[0])
        ribbon(acc, surf, pts, 0.0032, 0.0008, 1, spacing=0.004, taper_end=0.012, tag='sidepipe')
    # ---- hem piping lines (10 mm above each leg opening)
    for li, l in enumerate(loops):
        if li == top_i:
            continue
        pts = V[l][::max(1, len(l) // 36)] + np.array([0, 0, 0.011])
        ribbon(acc, surf, pts, 0.0030, 0.0009, 1, spacing=0.004, closed=True, tag=f'hempipe{li}')
    Vf, Ff, Nf, Mf = acc.merged()
    info = dict(tris=int(len(Ff)), sheet_tris=int(len(F)), loops=len(loops), top=top_i)
    if verbose:
        print(f'  shorts total tris {len(Ff)} (sheet {len(F)}) in {time.time()-t0:.1f}s {info}')
    tg, tn = acc.tags()
    return dict(V=Vf, F=Ff, N=Nf, M=Mf, T=tg, tagnames=tn, info=info, sheet=(V, F), bodies=bodies)


if __name__ == '__main__':
    import scene_utils as su
    cw = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'white'
    res = build_shorts()
    np.savez(f'{WORK}/data/shorts_male.npz', V=res['V'], F=res['F'], N=res['N'], M=res['M'], T=res['T'], tagnames=np.array(res['tagnames']))
