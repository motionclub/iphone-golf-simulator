"""Female skort: liner shorts + A-line skirt (+ wrap overlap flap) + waistband.  Built on the arm-less fit field; verified later against the full body."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from sdf import *
from fitbody import *
from shell import build_shell
from kit_common import *

P = dict(set='female', h=0.0125, lo=(-0.30, -0.22, 0.52), hi=(0.30, 0.20, 1.12),
         z_wt=0.995, z_wb=0.953, hem=0.700, hem_rise=0.030, liner_hem=0.640,
         cone=dict(zt=0.995, zh=0.700, a_top=0.126, b_top=0.108, a_hem=0.192, b_hem=0.150, cy=0.0),
         center=(0.0, 0.0),
         diag=dict(x_top=0.095, x_bot=-0.035, curve=1.15, left=-0.185),
         wrap=True)


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
    mask_fn = None
    add_nohand_trees(bodies, 'female')
    nh_trees = [b['tree_nohand'] for b in bodies]
    nh_meshes = [b['mesh_nohand'] for b in bodies]
    zwt, zwb = P['z_wt'], P['z_wb']
    lo, hi, h = P['lo'], P['hi'], P['h']

    # ---------------- liner (inner shorts, incl. the waistband zone)
    def ease_liner(X, Y, Z):
        wx = smoothstep(0.140, 0.115, np.abs(X))                      # band / waist ease only over the torso (not beside the hanging arms)
        band = 0.0055 * smoothstep(zwb - 0.012, zwb + 0.004, Z) * wx
        return (0.0055 + 0.0035 * smoothstep(0.86, 0.95, Z) * wx + band).astype(np.float32)

    def cut_liner(Pv):
        x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
        z_h = P['liner_hem'] + 0.012 * smoothstep(0.06, 0.20, np.abs(x))
        return np.maximum(z - zwt, z_h - z)

    liner = build_shell(bodies, 'female', 'skort', lo, hi, h, ease_liner, blur_mm=7.0, min_clear=0.0035, cut_fn=cut_liner, verbose=verbose, fit=True, enforce=(nh_trees, 0.0030, nh_meshes))

    # ---------------- skirt
    cn = P['cone']

    def ease_skirt(X, Y, Z):
        zz = np.array([1.00, 0.95, 0.90, 0.84, 0.80, 0.76, 0.70])
        ee = np.array([0.010, 0.010, 0.0115, 0.012, 0.011, 0.012, 0.014])
        return np.interp(Z, zz[::-1], ee[::-1]).astype(np.float32)

    def extra_skirt(g, S, X, Y, Z):
        t = np.clip((cn['zt'] - Z) / (cn['zt'] - cn['zh']), 0, 1)
        a = cn['a_top'] + (cn['a_hem'] - cn['a_top']) * t
        b = cn['b_top'] + (cn['b_hem'] - cn['b_top']) * t
        r = np.sqrt((X / a) ** 2 + ((Y - cn['cy']) / b) ** 2)
        cone = ((r - 1.0) * np.minimum(a, b)).astype(np.float32)
        cone = np.broadcast_to(cone, tuple(g.n)).copy()
        return np.minimum(cone, liner.Sg - 0.0045)

    def cut_skirt(Pv):
        x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
        return np.maximum(z - zwb, hem_base(x, y) - z)

    skirt = build_shell(bodies, 'female', 'skort', lo, hi, h, ease_skirt, blur_mm=10.0, min_clear=0.007, cut_fn=cut_skirt, extra_field=extra_skirt,
                        verbose=verbose, fit=True, enforce=(nh_trees, 0.0035, nh_meshes))

    acc = Acc()
    # liner sheet + rims/inner band
    Vl, Fl = liner.V, liner.F
    Nl = vertex_field_normals(liner.g, liner.Sg, Vl)
    add_sheet(acc, Vl, Fl, Nl, 0)
    add_rims_and_inner(acc, Vl, Fl, Nl, t=0.002, depth=0.014, piped={})
    surf_l = Surface(Vl, Fl, liner.g, liner.Sg)
    # skirt sheet
    Vs, Fs = skirt.V, skirt.F
    Ns = vertex_field_normals(skirt.g, skirt.Sg, Vs)
    add_sheet(acc, Vs, Fs, Ns, 0)
    loops_s = boundary_loops(Fs)
    add_rims_and_inner(acc, Vs, Fs, Ns, t=0.002, depth=0.014, piped={})
    surf_s = Surface(Vs, Fs, skirt.g, skirt.Sg)
    cen = P['center']
    # ---- waistband stitching rings on the liner (waist zone)
    for dz, w, lift in ((0.0, 0.0030, 0.0009), (0.0245, 0.0020, 0.0006)):
        ring = ring_at_z(Vl, Fl, zwb + dz + 0.003, 64)
        if ring is not None:
            ribbon(acc, surf_l, ring, w, lift, 0, spacing=0.0075, closed=True, tag='waistring')
    # ---- wrap overlap flap (front-left) with a piped diagonal edge
    surf_vis = surf_s
    if P['wrap']:
        d = P['diag']
        Tsk = Fs
        def c_flap(Pv):
            x, y, z = Pv[:, 0], Pv[:, 1], Pv[:, 2]
            return np.maximum(x - x_diag(z), y - 0.012)
        Vf_, Ff_, _, _ = clip_mesh(Vs, Tsk, c_flap(Vs))
        Vf_, Ff_ = keep_largest(Vf_, Ff_)
        Nf_ = vertex_field_normals(skirt.g, skirt.Sg, Vf_)
        w = smoothstep(0.012, -0.030, Vf_[:, 1])
        Vf_d = Vf_ + Nf_ * (0.0024 * w)[:, None]
        # rim only along the diagonal and the hem
        xd = x_diag(Vf_[:, 2])
        near_diag = np.abs(Vf_[:, 0] - xd) < 0.0016
        near_hem = np.abs(Vf_[:, 2] - hem_base(Vf_[:, 0], Vf_[:, 1])) < 0.0016
        add_sheet(acc, Vf_d, Ff_, Nf_, 0, 'flap')
        add_rim_segments(acc, Vf_d, Ff_, Nf_, t=0.0024, vmask=(near_diag | near_hem), piped=False, tag='flaprim')
        # piped diagonal edge: ribbon on the flap surface, just inside the edge
        bl = boundary_loops(Ff_)
        diag_pts = []
        for l in bl:
            for i in l:
                if near_diag[i]:
                    diag_pts.append(Vf_d[i])
        if diag_pts:
            diag_pts = np.array(diag_pts)
            diag_pts = diag_pts[np.argsort(-diag_pts[:, 2])]
            surf_f = Surface(Vf_d, Ff_)
            ctrl = diag_pts[::max(1, len(diag_pts) // 12)] - np.array([0.0022, 0, 0])
            ribbon(acc, surf_f, ctrl, 0.0034, 0.0010, 1, spacing=0.004, taper_end=0.004, tag='diagpipe')
        surf_vis = Surface(np.concatenate([Vs, Vf_d]), np.concatenate([Fs, Ff_ + len(Vs)]))
    # ---- hem piping lines on the visible outer surface (flap where it exists, base elsewhere)
    for li, l in enumerate(loops_s):
        pts = Vs[l][::max(1, len(l) // 60)] + np.array([0, 0, 0.009])
        nr = surf_s.normals_at(pts) if hasattr(surf_s, 'normals_at') else 0
        pts = pts + nr * 0.0032
        ribbon(acc, surf_vis, pts, 0.0030, 0.0009, 1, spacing=0.004, closed=True, tag=f'skirt_hem{li}')
    Vf, Ff, Nf, Mf = acc.merged()
    info = dict(tris=int(len(Ff)), liner_tris=int(len(Fl)), skirt_tris=int(len(Fs)), skirt_loops=len(loops_s))
    if verbose:
        print(f'  skort total tris {len(Ff)} (liner {len(Fl)}, skirt {len(Fs)}) in {time.time()-t0:.1f}s {info}')
    tg, tn = acc.tags()
    return dict(V=Vf, F=Ff, N=Nf, M=Mf, T=tg, tagnames=tn, info=info, parts=dict(liner=(Vl, Fl), skirt=(Vs, Fs)), bodies=bodies)


if __name__ == '__main__':
    res = build_skort()
    np.savez(f'{WORK}/data/skort_female.npz', V=res['V'], F=res['F'], N=res['N'], M=res['M'], T=res['T'], tagnames=np.array(res['tagnames']))
