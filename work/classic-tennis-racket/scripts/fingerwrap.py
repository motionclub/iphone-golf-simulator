"""Path-based finger wrap (proof-only, on a COPY): each finger is bent along a centre line that leaves the knuckle on its rest
direction, runs along the tangent to the (offset) grip cross-section and follows it round. Vertices keep their cross-section
offsets, so the finger skin stays on the cylinder (no search, no collision loop). Everything in hand-frame coordinates.
"""
import numpy as np
from handpose import smoothstep

R_GRIP = 0.017


def finger_local_frame(M, d, p_hat=np.array([0.0, 0.0, 1.0])):
    """Rest frame of a finger: x along the finger, z = palm-ward (component of +Wp orthogonal to x), y = z x x."""
    x = d / np.linalg.norm(d)
    z = p_hat - np.dot(p_hat, x) * x
    z /= np.linalg.norm(z)
    y = np.cross(z, x)
    return x, y, z


def axis_plane_centre(O, a, M, y_f):
    """Point where the grip axis crosses the finger's plane (the plane through M spanned by x_f and z_f)."""
    den = np.dot(a, y_f)
    if abs(den) < 1e-9:
        return O.copy()
    t = -np.dot(O - M, y_f) / den
    return O + a * t


def offset_curve_2d(Cc3, M, x_f, z_f, a, R, t_off, n=1440):
    """Boundary of the grip cross-section by the finger plane, offset by t_off, in plane coords (s, z) relative to M.
    Returns (B (n,2), theta (n,), Cc2 (2,))."""
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    e = np.cos(theta)[:, None] * x_f[None, :] + np.sin(theta)[:, None] * z_f[None, :]
    cr = np.cross(e, a[None, :])
    r = (R + t_off) / np.linalg.norm(cr, axis=1)
    Cc2 = np.array([np.dot(Cc3 - M, x_f), np.dot(Cc3 - M, z_f)])
    B = Cc2[None, :] + r[:, None] * np.stack([np.cos(theta), np.sin(theta)], 1)
    return B, theta, Cc2


def build_path(B, Cc2, length, step=0.0005):
    """Path in plane coords: from the origin along +s, tangent to curve B (centre on the LEFT, i.e. counter-clockwise wrap),
    then along B (increasing theta). Returns (pts (m,2), arclength (m,)) sampled every `step`; covers [-0.03, length]."""
    n = len(B)
    dB = np.roll(B, -1, axis=0) - np.roll(B, 1, axis=0)
    # tangency: cross(dB, B - O) == 0, O = origin
    cr = dB[:, 0] * B[:, 1] - dB[:, 1] * B[:, 0]
    idx = np.where(np.sign(cr) != np.sign(np.roll(cr, -1)))[0]
    best = None
    for i in idx:
        j = (i + 1) % n
        f = cr[i] / (cr[i] - cr[j]) if cr[i] != cr[j] else 0.0
        T1 = B[i] + f * (B[j] - B[i])
        dirv = T1 / np.linalg.norm(T1)
        side = dirv[0] * (Cc2[1] - 0) - dirv[1] * (Cc2[0] - 0)         # cross(dir, centre - O) > 0 -> centre on the left
        if side > 0 and np.dot(T1, [1.0, 0.0]) > -0.02:
            ang_i = i + f
            best = (T1, ang_i) if best is None or np.linalg.norm(T1) < np.linalg.norm(best[0]) else best
    if best is None:
        return None
    T1, ang_i = best
    L_seg = np.linalg.norm(T1)
    dirv = T1 / L_seg
    # straight part (extended backwards 3 cm so proximal vertices map rigidly)
    s_line = np.arange(-0.03, L_seg, step)
    line = s_line[:, None] * dirv[None, :]
    # arc part: start at index ang_i, go to increasing theta (CCW about Cc2)
    k0 = int(np.ceil(ang_i))
    Bc = np.concatenate([B[k0:], B[:k0], B[k0:], B[:k0]], axis=0)
    seg = np.linalg.norm(np.diff(Bc, axis=0), axis=1)
    sarc = np.concatenate([[0], np.cumsum(seg)])
    first_gap = np.linalg.norm(Bc[0] - T1)
    s_arc_total = max(length - L_seg, 0.0) + 0.02
    ns = int(s_arc_total / step) + 1
    su = np.linspace(first_gap, first_gap + s_arc_total, ns)
    arc = np.stack([np.interp(su - first_gap, sarc, Bc[:, 0]), np.interp(su - first_gap, sarc, Bc[:, 1])], 1)
    # prepend a short connector T1 -> first arc point is negligible (first_gap ~ sub-step); concatenate
    pts = np.concatenate([line, T1[None, :], arc], axis=0)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)]) - 0.03          # arclength measured from the origin
    return pts, s


def _wrap_once(Q, member, M, x_f, y_f, z_f, loc, O, a, R, length, t_off, ramp):
    Cc3 = axis_plane_centre(O, a, M, y_f)
    B, th, Cc2 = offset_curve_2d(Cc3, M, x_f, z_f, a, R, t_off)
    res = build_path(B, Cc2, length)
    if res is None:
        return None
    pts, s = res
    T = np.gradient(pts, s, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
    N = np.stack([-T[:, 1], T[:, 0]], 1)                                          # left normal (towards the grip)
    sv = np.clip(loc[:, 0], s[0] + 1e-6, s[-1] - 1e-6)
    cx = np.interp(sv, s, pts[:, 0]); cz = np.interp(sv, s, pts[:, 1])
    nx = np.interp(sv, s, N[:, 0]); nz = np.interp(sv, s, N[:, 1])
    over = np.maximum(loc[:, 0] - s[-1], 0.0)
    tx = np.interp(sv, s, T[:, 0]); tz = np.interp(sv, s, T[:, 1])
    cx = cx + over * tx; cz = cz + over * tz
    newx = cx + loc[:, 2] * nx
    newz = cz + loc[:, 2] * nz
    mapped = M[None, :] + newx[:, None] * x_f[None, :] + loc[:, 1:2] * y_f[None, :] + newz[:, None] * z_f[None, :]
    w = member * smoothstep((loc[:, 0] - ramp[0]) / (ramp[1] - ramp[0]))
    # only skin that really belongs to this finger (excludes the thumb / web skin standing far off the finger axis)
    w = w * smoothstep((0.020 - np.abs(loc[:, 1])) / 0.006) * smoothstep((0.024 - np.abs(loc[:, 2])) / 0.006)
    return Q + w[:, None] * (mapped - Q), w, Cc3


def wrap_finger(Q, member, M, d, joints_hint, O, a, R=R_GRIP, length=0.10, t_off=None, ramp=(-0.004, 0.016), touch_iters=4):
    """Return new hand-frame positions for ALL vertices Q (n,3): finger vertices (weighted by `member`) follow the wrap path.
    The offset t_off (finger half thickness on the palm side) is refined so the closest finger skin just touches the grip."""
    x_f, y_f, z_f = finger_local_frame(M, d)
    loc = np.stack([(Q - M) @ x_f, (Q - M) @ y_f, (Q - M) @ z_f], 1)           # (s, y, z)
    core = member > 0.5
    if t_off is None:
        strip = core & (np.abs(loc[:, 1]) < 0.004) & (loc[:, 0] > 0.012) & (loc[:, 0] < length - 0.012) & (loc[:, 2] < 0.03)
        zin = loc[strip, 2]
        t_off = float(np.percentile(zin, 95)) + 0.0004 if len(zin) else 0.012
    t0 = t_off
    best = None
    for it in range(touch_iters + 1):
        res = _wrap_once(Q, member, M, x_f, y_f, z_f, loc, O, a, R, length, t_off, ramp)
        if res is None:
            return Q.copy(), dict(ok=False)
        out, w, Cc3 = res
        mv = core & (loc[:, 0] > 0.01)
        gap = float(cyl_dist_local(out[mv], O, a, R).min())
        best = (out, t_off, gap)
        if abs(gap) < 0.0003 or it == touch_iters:
            break
        t_off = max(t_off - 0.9 * gap, 0.5 * t0)
    out, t_off, gap = best
    return out, dict(ok=True, t_off=t_off, t_off0=t0, gap_mm=gap * 1000, centre=Cc3.tolist())


def cyl_dist_local(P, O, a, R):
    d = P - O[None, :]
    t = d @ a
    r = np.linalg.norm(d - t[:, None] * a[None, :], axis=1)
    return r - R
