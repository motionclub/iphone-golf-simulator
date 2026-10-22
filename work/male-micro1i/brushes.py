"""Sculpt brushes on the dense head mesh: normal-direction displacement fields (mm), mirrored through |x|.  Pure numpy."""
import sys; sys.path.insert(0, '.')
from edlib import *
import sculpt as S


def export_normals(V, F, M, smooth=3):
    n = vertex_normals(V, F)
    for _ in range(smooth):
        m = M.nbr_mean(n); t = 0.5 * n + 0.5 * m; n = t / np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)
    return n


def front_w(V, y0=-0.050, y1=-0.080):
    return sstep(y0, y1, V[:, 1])


def blob(V, cx, cz, rx, rz, amp, q=2.0):
    """smooth bump in the (|x|, z) plane: value 'amp' (mm) at the centre, 0.5*amp at r=1 (half-value radii rx, rz in mm)"""
    x = np.abs(V[:, 0]) * 1000; z = V[:, 2] * 1000
    return amp * np.exp(-LN2 * (np.abs((x - cx) / rx) ** q + np.abs((z - cz * 1000) / rz) ** q))


LN2 = math.log(2.0)


def seg_dist(px, pz, pts):
    d = np.full(px.shape, np.inf)
    for (ax_, az_), (bx_, bz_) in zip(pts[:-1], pts[1:]):
        ex, ez = bx_ - ax_, bz_ - az_
        t = np.clip(((px - ax_) * ex + (pz - az_) * ez) / (ex * ex + ez * ez + 1e-18), 0, 1)
        d = np.minimum(d, np.hypot(px - (ax_ + t * ex), pz - (az_ + t * ez)))
    return d


def groove(V, pts_mm_z, depth, sigma, taper=None):
    """groove (positive depth = into the surface) along a polyline given as [(|x| mm, z m)], gaussian cross-section sigma (mm)"""
    x = np.abs(V[:, 0]) * 1000; z = V[:, 2] * 1000
    pts = [(a, b * 1000) for a, b in pts_mm_z]
    d = seg_dist(x, z, pts)
    g = depth * np.exp(-0.5 * (d / sigma) ** 2)
    if taper is not None:                                   # taper(x_mm) in [0,1] along the line
        g = g * taper(x)
    return -g                                               # displacement along the outward normal (negative = inward)


def apply_field(V, N, disp_mm, w=None):
    """displace along N; exactly zero (bit-identical) for z < 1.444 so the weld ring and everything below stays untouched"""
    P = V.copy(); dd = disp_mm * 1e-3 * (1.0 if w is None else w)
    dd = np.where(V[:, 2] < 1.444, 0.0, dd * sstep(1.444, 1.456, V[:, 2]))
    P += N * dd[:, None]
    return P
