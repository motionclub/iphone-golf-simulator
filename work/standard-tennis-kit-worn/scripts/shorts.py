"""Male tennis shorts (worn): closed double-walled SDF fabric shell + lofted contrasting waistband (material slot 2) + pocket slash / side seam / hem piping.

The band is its own closed ring island (rounded top and bottom edge) lofted from the body slice; the fabric shell is cut just below it so the
band stands as a separate belt-like element with the polo hem overlapping its top.  Materials: 0 fabric, 1 piping, 2 band (contrast colour).
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from sdf import *
from fitbody import *
from shell import build_shell
from kit_common import *
from band import build_band, slice_center

P = dict(set='male', h=0.0145, lo=(-0.34, -0.28, 0.46), hi=(0.34, 0.20, 1.10),
         z_wb=0.925, z_wt=0.965, hem=0.575, hem_rise=0.024,                 # band 40 mm tall; polo hem (0.950 front / 0.945 back) overlaps its top by 15-20 mm
         ease_leg=0.034, blur=22.0, min_clear=0.0150, flare=0.016, ease_inner=0.0150, lap=0.0055,
         tv=0.0030, band_in=0.0065, band_out=0.0110, band_gap=0.0010)                        # fabric wall 3 mm; band wall 4.5 mm, 6 mm .. 10.5 mm off the skin


def build_shorts(verbose=True):
    t0 = time.time()
    bodies = load_set(P['set'])
    zwt, zwb = P['z_wt'], P['z_wb']
    z_cut = zwb + P['lap']                        # fabric top edge LAPS over the band's lower edge (4 mm), standing off it ~1 mm: no line of sight can thread the seam

    def ease_fn(X, Y, Z):
        zz = np.array([1.00, 0.95, 0.90, 0.82, 0.74, 0.66, 0.58])
        ee = np.array([0.0150, 0.0150, 0.0155, 0.022, 0.029, 0.032, 0.034])
        flare = P['flare'] * smoothstep(0.84, 0.62, Z) * smoothstep(0.115, 0.185, np.abs(X))      # boxy leg: extra ease on the OUTER side only
        base = np.interp(Z, zz[::-1], ee[::-1])
        inner = smoothstep(0.11, 0.07, np.abs(X)) * smoothstep(0.80, 0.74, Z)                       # inner thigh below the crotch: hug it so the legs stay two tubes
        return (base * (1 - inner) + P['ease_inner'] * inner + flare).astype(np.float32)

    def cut_fn(Pv):
        x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
        z_hem = P['hem'] + P['hem_rise'] * smoothstep(0.10, 0.215, np.abs(x))
        return np.maximum(z - z_cut, z_hem - z)

    # ---- waistband first (it depends only on the body); the fabric is then built against the band surface so the two can never intersect
    b0 = bodies[0]
    cen_band = slice_center(b0['V'], b0['F'], 0.5 * (zwb + zwt))
    band = build_band([b['tree'] for b in bodies], cen_band, zwb, zwt, P['band_in'], P['band_out'], n_theta=96)
    save_part(f'{WORK}/data/band_male.npz', dict(V=band['V'], F=band['F'], LN=band['N'][band['F']].reshape(-1, 3), M=np.full(len(band['F']), 2), T=np.zeros(len(band['F']), int), tagnames=np.array(['band'])))
    tree_band = bvh_from(band['V'], band['F'])
    sh = build_shell(bodies, P['set'], 'shorts', P['lo'], P['hi'], P['h'], ease_fn, blur_mm=P['blur'], min_clear=P['min_clear'],
                     cut_fn=cut_fn, verbose=verbose, obstacles=[(tree_band, P['tv'] + P['band_gap'], zwb - 0.03, zwt + 0.01, cen_band)])
    V, F = sh.V, sh.F
    N = vertex_field_normals(sh.g, sh.Sg, V)
    loops = boundary_loops(F)
    cz = [V[l][:, 2].mean() for l in loops]
    top_i = int(np.argmax(cz))
    acc = Acc()
    add_closed_shell(acc, V, F, N, P['tv'], 0, tag='shorts')
    surf = Surface(V, F, sh.g, sh.Sg)
    # ---- waistband: closed lofted ring (slot 2)
    acc.add(band['V'], band['F'], band['N'], 2, 'band')
    # ---- pocket slash + side seam (both sides)
    cen = (0.0, cen_band[1])
    for sgn in (+1, -1):
        th = [np.radians(a) * sgn for a in (52, 66, 80, 90)]
        zz = [zwb - 0.006, zwb - 0.032, zwb - 0.064, zwb - 0.094]
        ribbon(acc, surf, list(zip(th, zz)), 0.0030, 0.0008, 1, spacing=0.004, taper_end=0.010, tag='pocket', polar=cen)
    # side seam piping from the pocket down to the hem (outer side of each leg)
    for sgn in (+1, -1):
        pts = []
        for z in np.linspace(zwb - 0.100, P['hem'] + P['hem_rise'] + 0.012, 8):
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
    res = finalize_acc(acc)
    info = dict(tris=int(len(res['F'])), sheet_tris=int(len(F)), loops=len(loops), top=top_i, z_wb=zwb, z_wt=zwt, band_center=list(cen_band),
                band_in=P['band_in'], band_out=P['band_out'], tv=P['tv'], topo=res['topo'])
    if verbose:
        print(f'  shorts total tris {len(res["F"])} (sheet {len(F)}) in {time.time()-t0:.1f}s {info}')
    res.update(info=info, sheet=(V, F), bodies=bodies, band=band)
    return res


if __name__ == '__main__':
    res = build_shorts()
    save_part(f'{WORK}/data/shorts_male.npz', res)
    json.dump(res['info'], open(f'{WORK}/data/shorts_male_info.json', 'w'), indent=1)
