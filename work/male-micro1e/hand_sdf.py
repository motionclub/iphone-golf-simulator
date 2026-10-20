"""Target hand (right hand) as an implicit surface in hand-local coordinates (a', n, w).

local axes: w = along the hand (wrist -> fingertips), n = palm normal (+n = palm side, toward the body),
            a' = across the hand, +a' = front / thumb side.   origin: wrist reference O shifted so fingers centre on a'=0.
"""
import numpy as np

O = np.array([0.554, -0.0775, 0.925])
D = np.array([0.63709983, -0.11248794, -0.76252886]); D /= np.linalg.norm(D)
A = np.array([0.0, -1.0, 0.0]); A = A - A.dot(D) * D; A /= np.linalg.norm(A)
N = np.cross(D, A); N /= np.linalg.norm(N)
A_SHIFT = 0.0175
O2 = O + A_SHIFT * A


def to_local(P, side=+1):
    """global (M,3) -> (a', n, w). side=-1 mirrors the left hand into right-hand space."""
    Q = P.copy()
    if side < 0:
        Q[:, 0] = -Q[:, 0]
    R = Q - O2
    return np.stack([R @ A, R @ N, R @ D], 1)


def to_global(L, side=+1):
    P = O2 + L[:, 0:1] * A + L[:, 1:2] * N + L[:, 2:3] * D
    if side < 0:
        P = P.copy(); P[:, 0] = -P[:, 0]
    return P


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def sd_roundcone(p, a, b, r1, r2):
    """exact SDF of a round cone (iq). p:(M,3), a,b:(3,), radii r1 at a, r2 at b."""
    ba = b - a
    l2 = ba.dot(ba)
    rr = r1 - r2
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = p - a
    y = pa @ ba
    z = y - l2
    xv = pa * l2 - ba[None, :] * y[:, None]
    x2 = (xv * xv).sum(1)
    y2 = y * y * l2
    z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    out = np.empty(len(p))
    c1 = np.sign(z) * a2 * z2 > k
    c2 = np.sign(y) * a2 * y2 < k
    out[:] = (np.sqrt(x2 * a2 * il2) + y * rr) * il2 - r1
    out[c1] = (np.sqrt(x2[c1] + z2[c1]) * il2 - r2)
    m2 = c2 & ~c1
    out[m2] = (np.sqrt(x2[m2] + y2[m2]) * il2 - r1)
    return out


def sd_rbox(p, c, b, r):
    q = np.abs(p - c) - b
    return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(np.max(q, axis=1), 0) - r


def chain(p, pts, radii):
    d = None
    for i in range(len(pts) - 1):
        f = sd_roundcone(p, np.array(pts[i]), np.array(pts[i + 1]), radii[i], radii[i + 1])
        d = f if d is None else np.minimum(d, f)
    return d


# ---------------- default parameters ----------------
PARAMS = dict(
    # finger spacing / radii
    f_x=[0.0353, 0.0118, -0.0118, -0.0353],         # index, middle, ring, pinky (a')
    f_base_w=[0.060, 0.064, 0.060, 0.052],
    f_len_tip_w=[0.150, 0.165, 0.152, 0.130],
    f_r_base=0.0118, f_r_tip=0.0100,
    f_n0=-0.0205, f_curl=0.014,                       # finger axis height and curl toward +n at tip
    # palm
    palm_c=(0.0, -0.016, 0.026), palm_b=(0.030, 0.007, 0.034), palm_r=0.018, palm_taper=(0.0, 0.07, 0.72),
    knuck_c=(0.0, -0.017, 0.062), knuck_b=(0.030, 0.006, 0.008), knuck_r=0.013,
    # thumb chain (a', n, w) and radii
    thumb_pts=[(0.036, 0.002, 0.008), (0.050, 0.012, 0.050), (0.058, 0.022, 0.098)],
    thumb_r=[0.0175, 0.0128, 0.0104],
    k_web=0.010, k_valley=0.0015, k_thumb=0.012,
)


def finger_pts(i, P=PARAMS):
    x = P['f_x'][i]; w0 = P['f_base_w'][i]; w1 = P['f_len_tip_w'][i]
    wm = w0 + 0.55 * (w1 - w0)
    n0 = P['f_n0']; c = P['f_curl']
    # axis: straight to mid then curling toward +n
    return [(x, n0, w0), (x, n0 + 0.15 * c, wm), (x, n0 + c, w1)]


def sdf_hand(L, P=PARAMS):
    """L: (M,3) local (a', n, w). Returns signed distance (neg inside)."""
    fingers = None
    for i in range(4):
        pts = finger_pts(i, P)
        r0 = P['f_r_base']; r2 = P['f_r_tip']
        f = chain(L, pts, [r0, 0.5 * (r0 + r2), r2])
        fingers = f if fingers is None else smin(fingers, f, P['k_valley'])
    # palm: tapered (narrow at wrist, wide at knuckles). Non-uniform scale of a' by s(w) around the centre line.
    t = np.clip((L[:, 2] - P['palm_taper'][0]) / (P['palm_taper'][1] - P['palm_taper'][0]), 0, 1); t = t * t * (3 - 2 * t)
    s_a = P['palm_taper'][2] + (1.0 - P['palm_taper'][2]) * t          # <1 at wrist
    Lp = L.copy(); Lp[:, 0] = L[:, 0] / s_a
    palm = sd_rbox(Lp, np.array(P['palm_c']), np.array(P['palm_b']), P['palm_r']) * 0.9
    knuck = sd_rbox(L, np.array(P['knuck_c']), np.array(P['knuck_b']), P['knuck_r'])
    palm = smin(palm, knuck, 0.012)
    thumb = chain(L, P['thumb_pts'], P['thumb_r'])
    body = smin(palm, fingers, P['k_web'])
    return smin(body, thumb, P['k_thumb'])


def raymarch(view_dir, up, size=(360, 360), center=(0.0, -0.016, 0.08), extent=0.22, P=PARAMS, light=(0.4, 0.5, 0.8)):
    """orthographic raymarch in LOCAL coords. returns RGB uint8 image."""
    v = np.array(view_dir, float); v /= np.linalg.norm(v)        # direction rays travel
    up = np.array(up, float); right = np.cross(v, up); right /= np.linalg.norm(right); up = np.cross(right, v)
    W, H = size
    xs = (np.arange(W) - W / 2 + 0.5) / W * extent
    ys = (H / 2 - np.arange(H) - 0.5) / H * extent
    X, Y = np.meshgrid(xs, ys)
    c = np.array(center)
    origin = c[None, None, :] - v[None, None, :] * 0.4 + X[..., None] * right + Y[..., None] * up
    o = origin.reshape(-1, 3).copy()
    t = np.zeros(len(o))
    hit = np.zeros(len(o), bool)
    alive = np.ones(len(o), bool)
    for it in range(90):
        idx = np.where(alive)[0]
        if not len(idx):
            break
        p = o[idx] + v * t[idx, None]
        d = sdf_hand(p, P)
        t[idx] += np.maximum(d, 0.0006) * 0.9
        h = d < 0.0004
        hit[idx[h]] = True
        alive[idx[h]] = False
        alive[idx[t[idx] > 0.9]] = False
    p = o + v * t[:, None]
    e = 0.0008
    g = np.stack([sdf_hand(p + [e, 0, 0], P) - sdf_hand(p - [e, 0, 0], P),
                  sdf_hand(p + [0, e, 0], P) - sdf_hand(p - [0, e, 0], P),
                  sdf_hand(p + [0, 0, e], P) - sdf_hand(p - [0, 0, e], P)], 1)
    g /= np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)
    Lt = np.array(light); Lt = Lt[0] * right + Lt[1] * up - Lt[2] * v
    Lt /= np.linalg.norm(Lt)
    sh = np.clip(g @ Lt, 0, 1) * 0.75 + 0.25
    img = np.full((H * W, 3), 38, np.uint8)
    col = (sh[:, None] * np.array([205, 205, 205])).astype(np.uint8)
    img[hit] = col[hit]
    return img.reshape(H, W, 3)
