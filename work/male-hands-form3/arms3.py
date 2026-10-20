"""Light soft-plastic mass for the arms: smooth Gaussian displacement fields along the vertex normals (mirrored L/R by construction).
All amplitudes in metres; positions only; fades to zero at the shoulder cut and before the wrist weld ring."""
import numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent
from hlib import *
AX = np.array([0.678, -0.178, -0.713]); AX /= np.linalg.norm(AX); C0 = np.array([0.437, -0.061, 1.064])
FRONT = np.array([0.0, -1.0, 0.0]); FRONT = FRONT - FRONT.dot(AX) * AX; FRONT /= np.linalg.norm(FRONT)
TOP = np.array([0.0, 0.0, 1.0]); TOP = TOP - TOP.dot(AX) * AX; TOP /= np.linalg.norm(TOP)

ARM0 = dict(
    comps=[   # name, amp(m), t0, sigma, phi0(deg), exponent (angular sharpness)
        ('biceps',   0.0022, -0.170, 0.050,   0.0, 2.0),
        ('triceps',  0.0016, -0.180, 0.055, 180.0, 2.0),
        ('elbow',   -0.0012, -0.105, 0.025,   0.0, 0.0),
        ('fore_top', 0.0018, -0.050, 0.040,  55.0, 1.5),
        ('fore_flex',0.0012, -0.045, 0.040, -50.0, 1.5),
        ('delt',     0.0025, -0.275, 0.040,  90.0, 2.0),
    ],
    t_fade_shoulder=(-0.345, 0.040), t_fade_wrist=(0.095, 0.030), scale=1.0,
    smooth_iters=14, smooth_t=(-0.315, 0.035, 0.085, 0.030), seam_fade=0.05,
)

def vertex_normals(V, polys):
    N = np.zeros_like(V)
    for f in polys:
        p = V[list(f)]; n = np.zeros(3)
        for k in range(1, len(f) - 1): n += np.cross(p[k] - p[0], p[k + 1] - p[0])
        for i in f: N[i] += n
    l = np.linalg.norm(N, axis=1, keepdims=True); return N / np.maximum(l, 1e-12)

def arm_edit(V0, polys, params=None):
    P = dict(ARM0); P.update(params or {})
    V = V0.astype(np.float64).copy()
    Nrm = vertex_normals(V, polys)
    sh = np.zeros(len(V), bool)
    for side in (+1, -1): sh[np.load(W / f'data/shellv_{side}.npy')] = True
    moved = {}
    E_all = edges_of(polys)
    zone_all = np.load(W / 'data/zone_R.npy') | np.load(W / 'data/zone_L.npy')
    # zone boundary = zone vertices with an edge to a non-zone vertex that is not part of the hand shell (the torso / shoulder seam)
    seam = np.zeros(len(V), bool)
    a_, b_ = E_all[:, 0], E_all[:, 1]
    m1 = zone_all[a_] & ~zone_all[b_]; m2 = zone_all[b_] & ~zone_all[a_]
    seam[a_[m1]] = True; seam[b_[m2]] = True
    seam &= ~sh
    seam_pts = V0[seam]
    for side, zn in ((+1, 'zone_R'), (-1, 'zone_L')):
        zone = np.load(W / f'data/{zn}.npy') & ~sh
        idx = np.nonzero(zone)[0]
        Q = V[idx].copy(); Q[:, 0] *= side
        t = (Q - C0) @ AX
        # centreline per t (cubic fit of the slab centroids)
        bins = np.arange(-0.37, 0.13, 0.02); cs = []; tc = []
        for lo in bins:
            m = (t >= lo) & (t < lo + 0.02)
            if m.sum() > 8: cs.append(Q[m].mean(0)); tc.append(t[m].mean())
        cs = np.array(cs); tc = np.array(tc)
        cf = [np.polyfit(tc, cs[:, k], 3) for k in range(3)]
        cen = np.stack([np.polyval(cf[k], t) for k in range(3)], 1)
        r = Q - cen
        phi = np.arctan2(r @ TOP, r @ FRONT)                      # 0 = front, +90deg = outer-top, 180 = back
        d = np.zeros(len(idx))
        for name, amp, t0, sg, ph0, ex in P['comps']:
            g = np.exp(-((t - t0) / sg) ** 2)
            if ex > 0:
                h = np.maximum(0, np.cos(phi - np.radians(ph0))) ** ex
            else:
                h = np.ones_like(g)
            d += amp * g * h
        fs0, fsw = P['t_fade_shoulder']; fw0, fww = P['t_fade_wrist']
        fade = smooth01((t - fs0) / fsw) * smooth01((fw0 - t) / fww)
        dseam = np.sqrt(((V0[idx][:, None, :] - seam_pts[None, :, :]) ** 2).sum(2)).min(1)
        sfade = smooth01(dseam / P['seam_fade']) if P['seam_fade'] > 0 else np.ones(len(idx))
        d *= fade * sfade * P['scale']
        V[idx] = V[idx] + Nrm[idx] * d[:, None]
        moved[side] = (idx, d)
    if P['smooth_iters'] > 0:
        E = edges_of(polys)
        w = np.zeros(len(V))
        a0, af, b0, bf = P['smooth_t']
        for side, zn in ((+1, 'zone_R'), (-1, 'zone_L')):
            zone = np.load(W / f'data/{zn}.npy') & ~sh
            idx = np.nonzero(zone)[0]
            Q = V[idx].copy(); Q[:, 0] *= side
            t = (Q - C0) @ AX
            dseam = np.sqrt(((V[idx][:, None, :] - seam_pts[None, :, :]) ** 2).sum(2)).min(1)
            w[idx] = smooth01((t - a0) / af) * smooth01((b0 - t) / bf) * (smooth01(dseam / P['seam_fade']) if P['seam_fade'] > 0 else 1.0)
        V = taubin(V, E, w, P['smooth_iters'])
    return V, moved
