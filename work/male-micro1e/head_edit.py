"""CHIN / jaw / under-chin edit. Coordinate-only wrap of the existing lower-face vertices onto an implicit V-jaw target.

Plate facts used (male_head_detail.jpg, calibrated k=0.0013044 m/px, top z=1.7047 at row 76):
  * chin bottom flat shelf at z~1.455, chin front vertical at y~-0.150 (central profile; already matched in baseline)
  * front view: jaw outline is a V-taper  hw(z) = 0.036 + 0.855 (z - 1.457)  (0.036 at chin bottom, 0.073 at z=1.50)
  * jawline rises ~30 deg from chin to gonion; neck columns hw~0.0725 continue vertically beside the chin
"""
import numpy as np
import sculpt_core as sc
from sculpt_core import BASE, sm

DEFAULT = dict(
    # jaw V-planes: |x| = hw0 + slope*(z - z0)
    hw0=0.036, slope=0.855, z0=1.457,
    # chin bottom shelf
    z_bottom=1.4485, bowl=0.0075,
    jaw_mode='v', se_a=0.074, se_b=0.053, se_zc=1.505, se_p=2.6,
    # plan-view ellipse of the face (centre y, radii)
    ell_cy=-0.070, ell_rx=0.086, ell_ry=0.080,
    # neck cylinder (ellipse in plan)
    neck_cy=-0.0188, neck_rx=0.0728, neck_ry=0.0721,
    r_round=0.014,       # smooth-intersection radius for jaw edges
    k_union=0.016,       # smooth-union radius jaw/neck (throat fillet)
    # region weights
    z_fade_lo=(1.432, 1.448), z_fade_hi=(1.494, 1.520), y_fade=(0.0, 0.035),
    iters=140, pull=0.18, tang=0.55,
)


def smax(a, b, k):
    return -sc.smin(-a, -b, k)


def make_sdf(P):
    d = DEFAULT
    def sdf(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        ax = np.abs(x)
        # face plan ellipse (infinite in z)
        qx = x / d['ell_rx']; qy = (y - d['ell_cy']) / d['ell_ry']
        k0 = np.sqrt(qx * qx + qy * qy)
        k1 = np.sqrt((qx / d['ell_rx']) ** 2 + (qy / d['ell_ry']) ** 2)
        f_plan = k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)
        if d.get('jaw_mode', 'v') == 'super':
            # plate front view: chin is a broad rounded U. Superellipse in (|x|, z), extruded along y, vertical sides above z_c.
            a_, b_, zc_, p_ = d['se_a'], d['se_b'], d['se_zc'], d['se_p']
            dz = np.minimum(z - zc_, 0.0)
            g = (np.abs(x / a_) ** p_ + np.abs(dz / b_) ** p_) ** (1.0 / p_)
            f_xz = (g - 1.0) * 0.5 * (a_ + b_)
            f_bot = d['z_bottom'] - z
            f_jaw = smax(f_plan, f_xz, d['r_round'])
            f_jaw = smax(f_jaw, f_bot, d['r_round'] * 0.6)
        else:
            # V planes: n = (cos, 0, -sin)
            ang = np.arctan(1.0 / d['slope'])             # plane tilt from vertical
            n = np.array([np.cos(ang), 0.0, -np.sin(ang)])
            # point on plane: (hw0, *, z0)
            f_v = (ax - d['hw0']) * n[0] + (z - d['z0']) * n[2]
            # chin bottom is a shallow U in the front view (plate): z_b(x) = z_bottom + bowl*(x/0.034)^2
            z_b = d['z_bottom'] + d['bowl'] * (np.minimum(ax, 0.050) / 0.034) ** 2
            f_bot = z_b - z
            f_jaw = smax(smax(f_plan, f_v, d['r_round']), f_bot, d['r_round'])
        # neck: elliptic cylinder
        nx = x / d['neck_rx']; ny = (y - d['neck_cy']) / d['neck_ry']
        n0 = np.sqrt(nx * nx + ny * ny)
        n1 = np.sqrt((nx / d['neck_rx']) ** 2 + (ny / d['neck_ry']) ** 2)
        f_neck = n0 * (n0 - 1.0) / np.maximum(n1, 1e-9)
        return sc.smin(f_jaw, f_neck, d['k_union'])
    return sdf


def weights(p):
    d = DEFAULT
    z = p[:, 2]; y = p[:, 1]
    w = sm(*d['z_fade_lo'], z) * (1 - sm(*d['z_fade_hi'], z)) * (1 - sm(*d['y_fade'], y))
    return w


def build(overrides=None):
    if overrides:
        DEFAULT.update(overrides)
    d = DEFAULT
    p0 = BASE.copy()
    sdf = make_sdf(p0)
    w = weights(p0)
    act = w > 1e-4
    p = p0.copy()
    for it in range(d['iters']):
        pr = sc.project(sdf, p, iters=3)
        p += (w * d['pull'])[:, None] * (pr - p)
        # tangential smoothing (remove normal component using SDF gradient)
        h = 1e-4
        g = np.stack([(sdf(p + [h, 0, 0]) - sdf(p - [h, 0, 0])),
                      (sdf(p + [0, h, 0]) - sdf(p - [0, h, 0])),
                      (sdf(p + [0, 0, h]) - sdf(p - [0, 0, h]))], 1)
        g /= np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)
        L = sc.neighbor_mean(p) - p
        Lt = L - np.einsum('ij,ij->i', L, g)[:, None] * g
        p += (w * d['tang'])[:, None] * Lt
    # final snap + light taubin in the active region
    pr = sc.project(sdf, p, iters=4)
    p = p + (w)[:, None] * (pr - p)
    p = sc.smooth(p, w, iters=6, lam=0.4, mu=-0.42)
    nf, mn = sc.flips(p)
    disp = np.linalg.norm(p - p0, axis=1)
    info = dict(active=int(act.sum()), flips=nf, min_dot=mn, max_disp_mm=float(disp.max() * 1000),
                mean_disp_mm=float(disp[act].mean() * 1000), edge_min_mean_max_mm=[1000 * v for v in sc.edge_stats(p, act)])
    return p, info


def cheek_smooth(co, iters=24):
    x, y, z = co.T
    wz = sm(1.452, 1.470, z) * (1 - sm(1.552, 1.575, z))
    wx = sm(0.012, 0.030, np.abs(x)) * (1 - sm(0.078, 0.092, np.abs(x)))
    wy = 1 - sm(-0.045, -0.010, y)
    return sc.smooth(co, wz * wx * wy, iters=iters, lam=0.5, mu=-0.53)


def run(tag, overrides=None, render=True):
    """Full head pipeline inside live Blender: build -> cheek smooth -> apply -> save npy -> render plate panels."""
    import bpy, lib
    sc.load_faces(bpy.data.objects['Body_M'].data)
    co, info = build(overrides)
    co = cheek_smooth(co)
    nf, mn = sc.flips(co)
    sc.apply_to_blender(co)
    np.save(str(sc.W / f'r/head_{tag}.npy'), co)
    if render:
        lib.clay_setup(); bpy.context.scene.render.film_transparent = False
        lib.head_panels(str(sc.W / f'r/{tag}'))
    info.update(flips_final=nf, min_dot_final=mn, tag=tag)
    return info


def trial(tag, overrides, cheek=True):
    """Head-only experiment on the CURRENT live mesh (hand topology may differ; head indices are identical to baseline)."""
    import bpy, lib
    sc.FACES = np.load(str(sc.W / 'faces.npy'))
    me = bpy.data.objects['Body_M'].data
    cur = np.array([v.co[:] for v in me.vertices], float)
    base = sc.BASE
    co, info = build(overrides)
    if cheek:
        co = cheek_smooth(co)
    reset = (base[:, 2] > 1.40) & (np.abs(base[:, 0]) < 0.13)       # whole head/neck zone returns to the locked baseline first
    cur[:len(base)][reset] = base[reset]
    cur[:len(base)] = np.where(np.any(co != base, axis=1)[:, None], co, cur[:len(base)])
    me.vertices.foreach_set('co', cur.astype(np.float32).ravel()); me.update()
    np.save(str(sc.W / f'r/head_{tag}.npy'), co)
    lib.clay_setup(); bpy.context.scene.render.film_transparent = False
    lib.head_panels(str(sc.W / f'r/{tag}'))
    info['tag'] = tag
    return info
