"""Female skort (worn): mid-thigh A-line skirt + hidden liner shorts + lofted contrasting waistband + wrap flap, all closed double-walled shells.

Layering (skin -> out): liner (inner shorts; hem ABOVE the skirt hem so it never shows) -> skirt (hangs from the band bottom, hem at mid-thigh) ->
wrap flap (front-left overlap panel with a piped diagonal edge).  The band (slot 2, contrast colour) is a separate closed ring island lofted from
the body slice; the polo hem overlaps its top.  Materials: 0 fabric, 1 piping, 2 band.
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

P = dict(set='female', h=0.0160, lo=(-0.30, -0.22, 0.52), hi=(0.30, 0.20, 1.12),
         z_wb=0.955, z_wt=0.995, hem=0.630, hem_rise=0.025, liner_hem=0.730, liner_rise=0.010,     # band 40 mm; skirt hem = mid-thigh (crotch ~0.79, knee ~0.49)
         cone=dict(z=[0.995, 0.955, 0.920, 0.880, 0.850, 0.800, 0.750, 0.700, 0.630],      # A-line: hugs the band at the top (<= 3 mm step so no sight line passes
                   a=[0.126, 0.134, 0.148, 0.162, 0.170, 0.180, 0.190, 0.200, 0.212],      #  between the skirt rim and the band), then flares just below it
                   b=[0.108, 0.110, 0.122, 0.138, 0.147, 0.154, 0.158, 0.160, 0.163], cy=0.0),
         center=(0.0, 0.0),
         diag=dict(x_top=0.095, x_bot=-0.035, curve=1.15, left=-0.185),
         wrap=True, tv_liner=0.0020, tv_skirt=0.0025, tv_flap=0.0020, flap_gap=0.0004,
         band_in=0.0065, band_out=0.0110, liner_ease=0.0090, liner_min=0.0088, skirt_gap=0.0020, lap=0.0055, band_gap=0.0010, flap_lip=0.0016)


def hem_panel(x, y):
    """skirt hem height: lowest front/back centre, scooped up at the sides."""
    return P['hem'] + P['hem_rise'] * smoothstep(0.07, 0.19, np.abs(x))


def hem_base(x, y):
    """under-layer hem: raised on the front-right (the wrap opening)."""
    d = P['diag']
    raise_ = 0.030 * smoothstep(d['x_bot'], d['x_bot'] + 0.12, x) * smoothstep(P['center'][1] + 0.05, P['center'][1] - 0.04, y)
    return hem_panel(x, y) + raise_


def x_diag(z):
    d = P['diag']
    u = np.clip((P['z_wb'] - z) / (P['z_wb'] - P['hem']), 0, 1)
    return d['x_top'] + (d['x_bot'] - d['x_top']) * u ** d['curve']


def build_skort(verbose=True):
    t0 = time.time()
    bodies = load_set(P['set'])
    add_nohand_trees(bodies, 'female')
    nh_trees = [b['tree_nohand'] for b in bodies]
    nh_meshes = [b['mesh_nohand'] for b in bodies]
    zwt, zwb = P['z_wt'], P['z_wb']
    lo, hi, h = P['lo'], P['hi'], P['h']
    tvl, tvs, tvf = P['tv_liner'], P['tv_skirt'], P['tv_flap']
    z_cut = zwb - 0.006                           # liner top edge: 6 mm under the band's bottom plane, fully behind the skirt wall (structure only; never visible)
    z_cut_skirt = zwb + P['lap']                  # skirt top edge LAPS over the band's lower edge, standing off it: no line of sight can thread the seam

    # ---------------- liner (inner shorts: structure only, shorter than the skirt)
    def ease_liner(X, Y, Z):
        return np.float32(P['liner_ease']) + 0.0 * Z

    def cut_liner(Pv):
        x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
        z_h = P['liner_hem'] + P['liner_rise'] * smoothstep(0.06, 0.20, np.abs(x))
        return np.maximum(z - z_cut, z_h - z)

    liner = build_shell(bodies, 'female', 'skort', lo, hi, h, ease_liner, blur_mm=7.0, min_clear=P['liner_min'], cut_fn=cut_liner, verbose=verbose,
                        fit=True, enforce=(nh_trees, P['liner_min'], nh_meshes))

    # ---------------- skirt
    cn = P['cone']

    def ease_skirt(X, Y, Z):
        zz = np.array([1.00, 0.95, 0.90, 0.84, 0.80, 0.76, 0.70, 0.63])
        ee = np.array([0.013, 0.013, 0.0135, 0.014, 0.014, 0.0145, 0.015, 0.016])
        return np.interp(Z, zz[::-1], ee[::-1]).astype(np.float32)

    def extra_skirt(g, S, X, Y, Z):
        zz = np.array(cn['z'])[::-1]
        a = np.interp(Z, zz, np.array(cn['a'])[::-1])
        b = np.interp(Z, zz, np.array(cn['b'])[::-1])
        r = np.sqrt((X / a) ** 2 + ((Y - cn['cy']) / b) ** 2)
        cone = ((r - 1.0) * np.minimum(a, b)).astype(np.float32)
        cone = np.broadcast_to(cone, tuple(g.n)).copy()
        return np.minimum(cone, liner.Sg - (tvs + P['skirt_gap']))         # the skirt wall always clears the liner (outer face of the liner + gap + wall)

    def cut_skirt(Pv):
        x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
        return np.maximum(z - z_cut_skirt, hem_base(x, y) - z)

    # ---- waistband first (depends only on the body); the skirt is built against the band surface so the two can never intersect
    b0 = bodies[0]
    cen_band = slice_center(b0['V'], b0['F'], 0.5 * (zwb + zwt))
    band = build_band([b['tree_nohand'] for b in bodies], cen_band, zwb, zwt, P['band_in'], P['band_out'], n_theta=96)
    save_part(f'{WORK}/data/band_female.npz', dict(V=band['V'], F=band['F'], LN=band['N'][band['F']].reshape(-1, 3), M=np.full(len(band['F']), 2), T=np.zeros(len(band['F']), int), tagnames=np.array(['band'])))
    tree_band = bvh_from(band['V'], band['F'])
    skirt = build_shell(bodies, 'female', 'skort', lo, hi, h, ease_skirt, blur_mm=10.0, min_clear=0.0125, cut_fn=cut_skirt, extra_field=extra_skirt,
                        verbose=verbose, fit=True, enforce=(nh_trees, 0.0125, nh_meshes), obstacles=[(tree_band, tvs + P['band_gap'], zwb - 0.03, zwt + 0.01, cen_band)])

    acc = Acc()
    # liner closed shell
    Vl, Fl = liner.V, liner.F
    Nl = vertex_field_normals(liner.g, liner.Sg, Vl)
    add_closed_shell(acc, Vl, Fl, Nl, tvl, 0, tag='liner')
    # skirt closed shell
    Vs, Fs = skirt.V, skirt.F
    Ns = vertex_field_normals(skirt.g, skirt.Sg, Vs)
    loops_s = boundary_loops(Fs)
    add_closed_shell(acc, Vs, Fs, Ns, tvs, 0, tag='skirt')
    surf_s = Surface(Vs, Fs, skirt.g, skirt.Sg)
    cen = P['center']
    # ---- waistband: closed lofted ring (slot 2)
    acc.add(band['V'], band['F'], band['N'], 2, 'band')
    surf_vis = surf_s
    info_flap = {}
    # ---- wrap overlap flap (front-left): a second closed layer on the skirt with a piped diagonal edge
    if P['wrap']:
        def c_flap(Pv):
            x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
            return np.maximum(x - x_diag(z), y - 0.012)
        Vf_, Ff_, (Nf_,), _ = clip_mesh(Vs, Fs, c_flap(Vs), vattrs=(Ns,))
        Vf_, Ff_ = keep_largest(Vf_, Ff_)
        Vf_, Ff_ = clean_sheet(Vf_, Ff_)
        Nf_ = vertex_field_normals(skirt.g, skirt.Sg, Vf_)
        w = smoothstep(0.012, -0.030, Vf_[:, 1])                       # 1 on the visible front panel .. 0 where the flap meets the side seam (thin lip)
        tvf_v = P['flap_lip'] + (tvf - P['flap_lip']) * w                # wall thickness of the flap: full on the panel, a 1.6 mm lip at the seam (never a hairline)
        Vf_o = Vf_ + Nf_ * (P['flap_gap'] + tvf_v)[:, None]              # inner face = skirt outer face + 0.4 mm gap
        add_closed_shell(acc, Vf_o, Ff_, Nf_, tvf_v, 0, tag='flap')
        xd = x_diag(Vf_[:, 2])
        near_diag = np.abs(Vf_[:, 0] - xd) < 0.004
        diag_pts = Vf_o[near_diag]
        if len(diag_pts) > 6:
            diag_pts = diag_pts[np.argsort(-diag_pts[:, 2])]
            surf_f = Surface(Vf_o, Ff_)
            ctrl = diag_pts[::max(1, len(diag_pts) // 12)] - np.array([0.0030, 0, 0])
            ribbon(acc, surf_f, ctrl, 0.0034, 0.0010, 1, spacing=0.004, taper_end=0.004, tag='diagpipe')
        surf_vis = Surface(np.concatenate([Vs, Vf_o]), np.concatenate([Fs, Ff_ + len(Vs)]))
        info_flap = dict(flap_tris=int(len(Ff_)), flap_verts=int(len(Vf_)))
    # ---- hem piping lines on the visible outer surface (flap where it exists, base elsewhere)
    for li, l in enumerate(loops_s):
        pts = Vs[l][::max(1, len(l) // 60)] + np.array([0, 0, 0.009])
        nr = surf_s.normals_at(pts)
        pts = pts + nr * 0.0032
        ribbon(acc, surf_vis, pts, 0.0030, 0.0009, 1, spacing=0.004, closed=True, tag=f'skirt_hem{li}')
    res = finalize_acc(acc)
    info = dict(tris=int(len(res['F'])), liner_tris=int(len(Fl)), skirt_tris=int(len(Fs)), skirt_loops=len(loops_s), z_wb=zwb, z_wt=zwt,
                skirt_hem_min=float(Vs[:, 2].min()), liner_hem_min=float(Vl[:, 2].min()), liner_hem_loops=[round(float(Vl[l][:, 2].min()), 4) for l in boundary_loops(Fl)],
                band_center=list(cen_band), band_in=P['band_in'], band_out=P['band_out'], tv_liner=tvl, tv_skirt=tvs, topo=res['topo'], **info_flap)
    if verbose:
        print(f'  skort total tris {len(res["F"])} (liner {len(Fl)}, skirt {len(Fs)}) in {time.time()-t0:.1f}s {info}')
    res.update(info=info, parts=dict(liner=(Vl, Fl), skirt=(Vs, Fs)), bodies=bodies, band=band)
    return res


if __name__ == '__main__':
    res = build_skort()
    save_part(f'{WORK}/data/skort_female.npz', res)
    json.dump(res['info'], open(f'{WORK}/data/skort_female_info.json', 'w'), indent=1)
