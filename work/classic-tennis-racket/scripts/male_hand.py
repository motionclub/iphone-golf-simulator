"""Digit model of the male right hand (hand-frame coordinates measured from the rasterised silhouette, see
male_digits_probe.py): four fingers + thumb as skinning chains for proof-only posing on a copy."""
import numpy as np
from handpose import Chain, smoothstep, apply_chain

# measured: finger centre-line V at U=0.010 and slope dV/dU, tip U (hand frame, metres)
FINGERS = {
    'pinky':  dict(V10=-0.0615, slope=-0.0875, tip=0.058, half=0.0100),
    'ring':   dict(V10=-0.0315, slope=-0.025, tip=0.079, half=0.0112),
    'middle': dict(V10=-0.0010, slope=0.025, tip=0.091, half=0.0115),
    'index':  dict(V10=+0.0290, slope=0.075, tip=0.075, half=0.0112),
}
U_MCP = -0.012
FRACS = (0.46, 0.76)        # PIP, DIP positions as fractions of the MCP->tip length


def frame_from_body(co, refine_palm=True):
    """Hand frame (c, u, v, p). PCA gives the coarse frame; the palm normal is then re-fitted to the palm-side SURFACE
    (the relaxed hand is cupped: ulnar side higher), so grip/finger axes follow the palm rather than the hand's mean plane."""
    sel = np.where((co[:, 0] < -0.50) & (co[:, 2] < 1.0))[0]
    P = co[sel]
    c = P.mean(0)
    U_, S_, Vt = np.linalg.svd(P - c, full_matrices=False)
    u, v = Vt[0], Vt[1]
    if u[2] > 0:
        u = -u
    if v[1] > 0:
        v = -v
    p = np.cross(v, u)
    assert p[0] > 0
    if refine_palm:
        Q = np.stack([(P - c) @ u, (P - c) @ v, (P - c) @ p], 1)
        # top (palm-side) surface heights on a 5 mm grid inside the palm proper
        reg = (Q[:, 0] > -0.095) & (Q[:, 0] < -0.015) & (Q[:, 1] > -0.055) & (Q[:, 1] < 0.020)
        cells = {}
        for q in Q[reg]:
            key = (int(np.floor(q[0] / 0.005)), int(np.floor(q[1] / 0.005)))
            if key not in cells or q[2] > cells[key][2]:
                cells[key] = q
        pts = np.array(list(cells.values()))
        A = np.stack([np.ones(len(pts)), pts[:, 0], pts[:, 1]], 1)
        for _ in range(3):
            coef, *_ = np.linalg.lstsq(A, pts[:, 2], rcond=None)
            res = pts[:, 2] - A @ coef
            keep = np.abs(res) < 2.0 * res.std() + 1e-9
            A, pts = A[keep], pts[keep]
        alpha, beta, gamma = coef
        # plane W = alpha + beta*U + gamma*V -> normal (-beta, -gamma, 1) in (U,V,W)
        p2 = p - beta * u - gamma * v
        p2 /= np.linalg.norm(p2)
        u2 = u - np.dot(u, p2) * p2
        u2 /= np.linalg.norm(u2)
        v2 = np.cross(u2, p2)
        # keep the origin where the plane crosses the PCA centroid axis -> shift c along p2 so the palm plane is Wp = 0.017
        c2 = c + p * alpha
        u, v, p, c = u2, v2, p2, c2
        print('palm plane refit: beta %.3f gamma %.3f alpha %.4f -> tilt %.1f deg' % (beta, gamma, alpha, np.degrees(np.arccos(np.clip(np.dot(p, p2), -1, 1)))))
    return sel, c, u, v, p


def to_hand(P, c, u, v, p):
    d = P - c
    return np.stack([d @ u, d @ v, d @ p], axis=1)


def from_hand(Q, c, u, v, p):
    return c + Q[:, 0:1] * u + Q[:, 1:2] * v + Q[:, 2:3] * p


def build_chains(Q):
    """Q: (n,3) hand-frame coords of the hand vertex subset. Returns dict name -> Chain (index, middle, ring, pinky)."""
    chains = {}
    names = list(FINGERS)
    for name in names:
        f = FINGERS[name]
        Vf = lambda U: f['V10'] + f['slope'] * (U - 0.010)
        dist = np.abs(Q[:, 1] - Vf(Q[:, 0]))
        m = np.clip(1 - (dist - 0.7 * f['half']) / (0.5 * f['half'] + 0.003), 0, 1)
        m = np.where(Q[:, 0] > U_MCP - 0.02, m, 0.0)
        # centre line height of the finger along U (mean Wp of the finger skin per 1 cm slab) -> straight-line fit -> rest direction
        core = (dist < 0.8 * f['half']) & (Q[:, 0] > U_MCP) & (Q[:, 0] < f['tip'] - 0.008)
        Uc, Wc = Q[core, 0], Q[core, 2]
        w1, w0 = np.polyfit(Uc, Wc, 1)
        wp = w0 + w1 * U_MCP
        d = np.array([1.0, f['slope'], w1])
        d /= np.linalg.norm(d)
        L = f['tip'] - U_MCP
        U_pip, U_dip = U_MCP + FRACS[0] * L, U_MCP + FRACS[1] * L
        joints = [(U_MCP, Vf(U_MCP), w0 + w1 * U_MCP), (U_pip, Vf(U_pip), w0 + w1 * U_pip), (U_dip, Vf(U_dip), w0 + w1 * U_dip)]
        h = np.cross(d, [0, 0, 1.0])                    # hinge d x p : +angle moves d towards +Wp (the palm side)
        chains[name] = Chain(name, joints, [h, h, h], [0.012, 0.009, 0.007], d, m)
        chains[name].tilt = float(w1)
    tot = sum(c.member for c in chains.values())
    scale = np.where(tot > 1.0, 1.0 / np.maximum(tot, 1e-9), 1.0)
    for c in chains.values():
        c.member = c.member * scale
    return chains


def build_thumb(Q):
    """Thumb: V > ~0.044 at U > -0.05, fading into the thenar; two flexion joints about axes along the palm."""
    dth = np.array([0.96, 0.28, 0.0])
    dth /= np.linalg.norm(dth)
    # membership: lateral (thumb side) region
    m_v = smoothstep((Q[:, 1] - 0.040) / 0.012)
    m_u = smoothstep((Q[:, 0] + 0.075) / 0.030)
    m = m_v * m_u
    sel = (m > 0.9)
    wp = float(Q[sel, 2].mean()) if sel.any() else -0.02
    J1 = np.array([-0.050, 0.050, wp])
    J2 = np.array([-0.018, 0.057, wp])
    h = np.cross(dth, [0, 0, 1.0])
    return Chain('thumb', [J1, J2], [h, h], [0.020, 0.012], dth, m)
