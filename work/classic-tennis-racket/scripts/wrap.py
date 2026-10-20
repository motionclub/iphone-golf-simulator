"""Grip placement in hand-frame coordinates + sequential-contact finger wrap against the analytic grip cylinder.
All inputs/outputs in hand-frame coords (U along fingers, V towards thumb, Wp = palm normal)."""
import numpy as np
from handpose import apply_chain

R_GRIP = 0.017


def axis_dir(phi_deg):
    phi = np.radians(phi_deg)
    return np.array([np.sin(phi), np.cos(phi), 0.0])      # (U, V, Wp): handle axis in the palm plane


def lift_for_clearance(Qs, centre_uv, a, R=R_GRIP, margin=0.0005):
    """Height W_g of the axis (above the hand frame's Wp=0) so the cylinder clears every sample point Qs (n,3)."""
    d = Qs[:, :2] - np.asarray(centre_uv)[None, :]
    t = d @ a[:2]
    perp = np.abs(d[:, 0] * a[1] - d[:, 1] * a[0])         # in-plane distance to the axis line
    need = R + margin
    sel = perp < need
    if not sel.any():
        return Qs[:, 2].max()
    return float((Qs[sel, 2] + np.sqrt(need ** 2 - perp[sel] ** 2)).max())


def cyl_dist(P, O, a, R=R_GRIP):
    d = P - O[None, :]
    t = d @ a
    r = np.linalg.norm(d - t[:, None] * a[None, :], axis=1)
    return r - R


def wrap_digit(Q, chain, O, a, amax, steps=240, touch=0.0002, pen=0.0006, R=R_GRIP, idx=None, tip_len=0.022):
    """Wrap by link: bend joint k until the MIDDLE of link k touches the cylinder (so each link ends up tangent to it, like the
    polygon circumscribing a circle), never letting any moving vertex penetrate by more than `pen`.
    Returns angles, subset indices, final positions of the subset, per-joint contact flags."""
    if idx is None:
        idx = np.where(chain.member > 0.02)[0]
    Qi = Q[idx]
    W = chain.bone_weights(Q)[idx]
    nj = len(chain.J)
    angles = [0.0] * nj
    contacts = []
    for k in range(nj):
        t_rest = (Qi - chain.J[k]) @ chain.axis_dir
        if k + 1 < nj:
            L_k = float((chain.J[k + 1] - chain.J[k]) @ chain.axis_dir)
        else:
            L_k = tip_len
        mid = (W[:, k + 1] > 0.6) & (np.abs(t_rest - 0.5 * L_k) < 0.25 * L_k)
        moving = (W[:, k + 1:].sum(1) > 0.3) & (t_rest > 0.006)
        if not mid.any():
            contacts.append(False)
            continue
        hit = False
        last_good = 0.0
        for a_ in np.linspace(0.0, amax[k], steps):
            ang = list(angles)
            ang[k] = a_
            Pn = apply_chain(Qi, chain, ang, W=W)
            d_all = cyl_dist(Pn[moving], O, a, R).min()
            if d_all < -pen:
                break                                           # would penetrate: keep the last good angle
            if cyl_dist(Pn[mid], O, a, R).min() <= touch:
                hit = True
                last_good = a_
                break
            last_good = a_
        angles[k] = last_good
        contacts.append(hit)
    Pn = apply_chain(Qi, chain, angles, W=W)
    return angles, idx, Pn, contacts
