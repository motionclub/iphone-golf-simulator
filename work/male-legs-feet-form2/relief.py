"""Soft-plastic form relief for the legs/feet zone (positions only, old topology).  Gaussian bumps placed on the surface, displaced along the
vertex normals; left leg defined, right leg = mirror (x -> -x) of the same field.  The top 3 cm of the zone (z >= 0.735) is untouched.
Features are (name, facing, dx_from_centre, z, y_hint, sigma(3), amp_mm).  Everything in metres."""
import numpy as np
from ff_common import *

TOPFADE = (0.725, 0.752)         # weight 1 below 0.725, 0 above 0.752 (zone top 0.765, last ~1.3 cm untouched)

# (name, facing, dx (m, + = lateral), z, y_hint or None, sigma (sx, sy, sz) m, amp mm).  CARVING ONLY on the silhouette-critical faces: crests stay on the
# plate silhouette (calf back edge, shin front edge, x-edges), form comes from grooves/hollows.  Weighted by the facing of the vertex normal.
FEATURES = [
    # --- back of the lower leg: two gastrocnemius heads read through the median groove, flank hollows, and the creases that end the belly
    ('gastroc_groove', 'back', 0.000, 0.335, None, (0.007, 0.040, 0.058), -2.6),
    ('gastroc_flank_med', 'back', -0.042, 0.335, None, (0.012, 0.040, 0.050), -1.5),
    ('gastroc_flank_lat', 'back', +0.038, 0.335, None, (0.012, 0.040, 0.050), -1.5),
    ('belly_end', 'back', 0.000, 0.250, None, (0.036, 0.040, 0.013), -2.0),
    ('popliteal', 'back', 0.000, 0.428, None, (0.030, 0.040, 0.016), -2.0),
    ('achilles_hollow_med', 'back', -0.030, 0.150, None, (0.011, 0.040, 0.030), -2.2),
    ('achilles_hollow_lat', 'back', +0.030, 0.150, None, (0.011, 0.040, 0.030), -2.2),
    ('achilles_low_med', 'back', -0.028, 0.105, None, (0.012, 0.040, 0.020), -1.5),
    ('achilles_low_lat', 'back', +0.028, 0.105, None, (0.012, 0.040, 0.020), -1.5),
    # --- front of the lower leg (crest stays on the plate contour; sides hollow)
    ('shin_flat_med', 'front', -0.030, 0.300, None, (0.010, 0.040, 0.085), -1.5),
    ('shin_flat_lat', 'front', +0.030, 0.300, None, (0.010, 0.040, 0.085), -1.5),
    ('shin_low_med', 'front', -0.025, 0.200, None, (0.009, 0.040, 0.045), -1.0),
    ('shin_low_lat', 'front', +0.025, 0.200, None, (0.009, 0.040, 0.045), -1.0),
    ('shin_crest_keep', 'front', 0.000, 0.230, None, (0.014, 0.040, 0.110), +0.5),
    # --- ankle
    ('mal_lat', 'lat', 0.0, 0.082, +0.012, (0.012, 0.012, 0.012), +2.6),
    ('mal_med', 'med', 0.0, 0.094, -0.004, (0.012, 0.012, 0.012), +2.6),
    ('mal_hollow_lat', 'lat', 0.0, 0.126, +0.010, (0.020, 0.016, 0.018), -1.2),
    ('mal_hollow_med', 'med', 0.0, 0.132, -0.002, (0.020, 0.016, 0.018), -1.2),
    # --- foot behind the forefoot cut
    ('heel_pad', 'back', 0.000, 0.030, None, (0.026, 0.020, 0.018), +2.0),
    ('arch_med', 'med', 0.0, 0.026, -0.030, (0.030, 0.030, 0.014), -5.0),
    ('lat_edge', 'lat', 0.0, 0.012, -0.040, (0.060, 0.060, 0.008), +2.0),
    # --- thigh / knee (carving only)
    ('quad_groove', 'front', +0.012, 0.640, None, (0.007, 0.040, 0.060), -2.0),
    ('vastus_med_edge', 'front', -0.026, 0.640, None, (0.008, 0.040, 0.040), -1.6),
    # knee: keep the cap proud, define it with soft peri-patellar planes
    ('patella', 'front', 0.000, 0.520, None, (0.020, 0.030, 0.020), +1.2),
    ('knee_above', 'front', 0.000, 0.585, None, (0.030, 0.030, 0.016), -1.3),
    ('knee_below', 'front', 0.000, 0.462, None, (0.030, 0.030, 0.016), -1.3),
    ('ham_groove', 'back', 0.000, 0.620, None, (0.007, 0.040, 0.070), -2.0),
    ('ham_flank_lat', 'back', +0.040, 0.640, None, (0.010, 0.040, 0.060), -1.2),
    ('ham_flank_med', 'back', -0.040, 0.640, None, (0.010, 0.040, 0.060), -1.2),
]


def leg_centre(V, z, side=+1):
    s = (side * V[:, 0] > 0.02) & (side * V[:, 0] < 0.30) & (np.abs(V[:, 2] - z) < 0.004) & (V[:, 1] > -0.17)
    X = side * V[s, 0]
    return 0.5 * (X.min() + X.max())


def place(V, N, zone, feat, side=+1):
    """find the surface anchor of a feature on the leg of `side`; returns centre (3,) world coords"""
    name, facing, dx, z, yh, sig, amp = feat
    Vs = V.copy(); Vs[:, 0] *= side                           # left-leg frame (x > 0)
    cx = leg_centre(V, z, side)
    win = zone & (Vs[:, 0] > 0.02) & (np.abs(Vs[:, 2] - z) < 0.006)
    if facing in ('back', 'front'):
        sel = win & (np.abs(Vs[:, 0] - (cx + dx)) < 0.006)
        if not sel.any():
            sel = win & (np.abs(Vs[:, 0] - (cx + dx)) < 0.012)
        idx = np.where(sel)[0]
        k = idx[np.argmax(Vs[idx, 1])] if facing == 'back' else idx[np.argmin(Vs[idx, 1])]
    else:
        sel = win & (np.abs(Vs[:, 1] - yh) < 0.008)
        idx = np.where(sel)[0]
        k = idx[np.argmax(Vs[idx, 0])] if facing == 'lat' else idx[np.argmin(Vs[idx, 0])]
    c = Vs[k].copy()
    c[0] *= side
    return c


def fair_tube(V, F, zone_mask, iters=12, z0=0.14, z1=0.72, ramp=0.03):
    """light volume-preserving fairing of the lower-leg / thigh tube (cm-scale lumps); weight 1 inside [z0, z1], smooth ramps outside"""
    M = Mesh(V, F)
    w = zone_mask * smooth01((V[:, 2] - z0) / ramp) * (1 - smooth01((V[:, 2] - z1) / ramp))
    w = w * (V[:, 2] > 0.0)
    return M.taubin(V, w, iters=iters)


def apply_relief(V, F, zone_mask, features=FEATURES, scale=1.0, verbose=False, scale_by=None):
    N = vertex_normals(V, F)
    dV = np.zeros_like(V)
    wtop = 1.0 - smooth01((V[:, 2] - TOPFADE[0]) / (TOPFADE[1] - TOPFADE[0]))
    info = {}
    for side in (+1, -1):
        for feat in features:
            name, facing, dx, z, yh, sig, amp = feat
            c = place(V, N, zone_mask, feat, side)
            Vs = V.copy()
            d = (V - c)
            # gaussian in a frame where x-sigma is measured along world x (mirror-invariant)
            g = np.exp(-0.5 * ((d[:, 0] / sig[0]) ** 2 + (d[:, 1] / sig[1]) ** 2 + (d[:, 2] / sig[2]) ** 2))
            mine = zone_mask & (side * V[:, 0] > 0.0)
            Ns = N * np.array([side, 1.0, 1.0])
            fw = {'back': np.clip(Ns[:, 1], 0, 1), 'front': np.clip(-Ns[:, 1], 0, 1), 'lat': np.clip(Ns[:, 0], 0, 1), 'med': np.clip(-Ns[:, 0], 0, 1)}[facing] ** 2
            w = g * mine * wtop * fw
            sc = scale if scale_by is None else scale_by(name)
            dV += (amp * 1e-3 * sc) * w[:, None] * N
            info[(name, side)] = c
            if verbose and side == +1:
                print(f'{name:22s} anchor {np.round(c * 1000, 1)} amp {amp:+.1f}')
    return V + dV, dV, info


if __name__ == '__main__':
    V, F = load_base()
    zone = zone_mask_eff(len(V))
    Vf = fair_tube(V, F, zone)
    print('fair_tube max move mm', np.linalg.norm(Vf - V, axis=1).max() * 1000)
    V1, dV, info = apply_relief(Vf, F, zone, verbose=False, scale_by=lambda n: 1.5 if n.startswith(('vastus', 'ham')) else 1.8)
    mag = np.linalg.norm(dV, axis=1)
    print('moved verts', int((mag > 1e-6).sum()), 'max displacement mm', mag.max() * 1000, 'top band z>=0.735 max mm', mag[V[:, 2] >= 0.735].max() * 1000)
    np.save(W + '/data/V_relief1.npy', V1)
