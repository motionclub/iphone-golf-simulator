"""Waistband: a closed, rounded-edge ring lofted from the body slice (NOT from the blurred garment SDF, whose blur is wider than the band).

The band outer wall sits `c_out` off the skin and the inner wall `c_in` off the skin (thickness c_out-c_in), straight vertical walls with
semicircular (rolled) top and bottom edges.  It is a closed torus, one island, one material (slot 2 = the contrasting colour).
"""
import numpy as np
from kitlib import *


def _periodic_smooth(a, w):
    """moving average over the last axis (periodic), window w (odd)."""
    if w <= 1:
        return a
    k = w // 2
    acc = np.zeros_like(a)
    for s in range(-k, k + 1):
        acc += np.roll(a, s, axis=-1)
    return acc / (2 * k + 1)


def body_envelope(trees, center, zs, thetas, rmax=0.6):
    """radius of the body envelope along rays from the vertical axis through `center` at heights zs and polar angles thetas
    (theta 0 = front -y, +pi/2 = +x).  First exit hit per body, the outermost body wins."""
    cx, cy = center
    R = np.zeros((len(zs), len(thetas)))
    for i, z in enumerate(zs):
        for j, th in enumerate(thetas):
            d = (float(np.sin(th)), float(-np.cos(th)), 0.0)
            best = 0.0
            for tr in trees:
                loc, n, idx, dist = tr.ray_cast((cx, cy, float(z)), d, rmax)
                if idx is not None:
                    best = max(best, dist)
            R[i, j] = best
    return R


def slice_center(V, F, z):
    """centre of the largest closed slice loop of a body mesh at height z (the torso/pelvis loop, not the arms)."""
    loops = [P for P in slice_plane(V, F, 2, float(z)) if len(P) >= 12]
    P = max(loops, key=lambda p: abs(poly_area_xy(p)))
    return (float(0.5 * (P[:, 0].min() + P[:, 0].max())), float(0.5 * (P[:, 1].min() + P[:, 1].max())))


def build_band(trees, center, z0, z1, c_in, c_out, n_theta=96, n_rows=9, wall_pts=3, cap_pts=3, smooth_w=7, r_bottom=0.0010, corner_pts=2):
    """returns dict(V, F, N, ring=outer-wall centre ring info, c_mid, rho)."""
    cx, cy = center
    nth = n_theta
    th = 2 * np.pi * np.arange(nth) / nth
    zs = np.linspace(z0, z1, n_rows)
    R = body_envelope(trees, center, zs, th)
    # fill dimples only (never shrink into the skin): smooth, take the max with the raw envelope, smooth lightly again, max again
    R1 = _periodic_smooth(R, smooth_w)
    R2 = np.maximum(R1, R)
    R3 = _periodic_smooth(R2, 3)
    Rf = np.maximum(R3, R)
    # light smoothing along z too (the band walls stay straight)
    Rz = Rf.copy()
    for i in range(1, n_rows - 1):
        Rz[i] = 0.25 * Rf[i - 1] + 0.5 * Rf[i] + 0.25 * Rf[i + 1]
    Rf = np.maximum(Rz, R)
    dirs = np.stack([np.sin(th), -np.cos(th), np.zeros(nth)], 1)           # (nth, 3) horizontal outward direction
    S = np.zeros((n_rows, nth, 3))
    S[..., 0] = cx + Rf * dirs[None, :, 0]
    S[..., 1] = cy + Rf * dirs[None, :, 1]
    S[..., 2] = zs[:, None]
    # outward normals of the envelope surface: d/dtheta x d/dz
    dth = np.roll(S, -1, 1) - np.roll(S, 1, 1)
    dz = np.gradient(S, axis=0)
    Nn = np.cross(dth, dz)
    Nn /= np.linalg.norm(Nn, axis=2, keepdims=True)
    flip = (Nn * dirs[None]).sum(2) < 0
    Nn[flip] *= -1
    rho = 0.5 * (c_out - c_in)
    c_mid = 0.5 * (c_out + c_in)
    rb = min(r_bottom, rho)                                               # the bottom corners are nearly square: the straight outer wall runs down to z0 + rb,
    ztop, zbot = z1 - rho, z0 + rb                                        # so a camera ray cannot pass under a rounded bottom roll next to the fabric seam
    # profile: (reference height, absolute z, offset along the normal)
    prof = []
    for m in range(wall_pts):                                              # outer wall, bottom -> top
        z = zbot + (ztop - zbot) * m / (wall_pts - 1)
        prof.append((z, z, c_out))
    for a_ in np.linspace(0, np.pi, cap_pts + 2)[1:-1]:                    # top cap (outer -> inner over the top): full roll, the polo hem laps over it
        prof.append((ztop, ztop + rho * np.sin(a_), c_mid + rho * np.cos(a_)))
    for m in range(wall_pts):                                              # inner wall, top -> bottom
        z = ztop - (ztop - zbot) * m / (wall_pts - 1)
        prof.append((z, z, c_in))
    for k in range(1, corner_pts + 1):                                     # inner-bottom corner arc (inner wall -> flat bottom)
        phi = 0.5 * np.pi * k / (corner_pts + 1)
        prof.append((zbot, zbot - rb * np.sin(phi), c_in + rb - rb * np.cos(phi)))
    prof.append((zbot, z0, c_in + rb))                                     # flat bottom, inner end
    prof.append((zbot, z0, c_out - rb))                                    # flat bottom, outer end
    for k in range(1, corner_pts + 1):                                     # outer-bottom corner arc (flat bottom -> outer wall)
        phi = 0.5 * np.pi * k / (corner_pts + 1)
        prof.append((zbot, z0 + rb - rb * np.cos(phi), c_out - rb + rb * np.sin(phi)))
    npf = len(prof)

    def interp_rows(A, zref):
        f = (zref - z0) / (z1 - z0) * (n_rows - 1)
        i0 = int(np.clip(np.floor(f), 0, n_rows - 2))
        t = f - i0
        return A[i0] * (1 - t) + A[i0 + 1] * t
    V = np.zeros((npf, nth, 3))
    for p, (zref, zabs, off) in enumerate(prof):
        Sp = interp_rows(S, zref)
        Np = interp_rows(Nn, zref)
        Np = Np / np.linalg.norm(Np, axis=1, keepdims=True)
        # offset HORIZONTALLY by off / cos(tilt) so the normal distance to the body envelope is `off` while the walls stay vertical and both edges planar
        nh = Np.copy()
        nh[:, 2] = 0.0
        cosa = np.maximum(np.linalg.norm(nh, axis=1), 0.6)
        nh /= np.maximum(np.linalg.norm(nh, axis=1, keepdims=True), 1e-9)
        V[p] = Sp + nh * (off / cosa)[:, None]
        V[p, :, 2] = zabs
    V = V.reshape(-1, 3)                                                   # index p*nth + j
    quads = []
    for p in range(npf):
        p2 = (p + 1) % npf
        for j in range(nth):
            j2 = (j + 1) % nth
            quads.append((p * nth + j, p * nth + j2, p2 * nth + j2, p2 * nth + j))
    quads = np.array(quads)
    F = np.concatenate([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]], 0)
    # the grid winding is uniform by construction: one global outward test (section centroid) decides the flip for every face
    sec = V.reshape(npf, nth, 3).mean(0)
    fc = V[F].mean(1)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    jj = F[:, 0] % nth
    if np.einsum('ij,ij->i', fn, fc - sec[jj]).sum() < 0:
        F = F[:, [0, 2, 1]]
    N = vertex_normals(V, F)
    return dict(V=V, F=F, N=N, c_mid=c_mid, rho=rho, center=center, z0=z0, z1=z1, R=Rf, thetas=th)
