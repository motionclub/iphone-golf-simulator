"""Micro1g: plate-driven FACE sculpt on Body_M (positions only; z < 1.43 untouched; hands/body never touched).

All landmarks come from ArtDir/hero/base_lock/male_head_detail.jpg with the head calibration
k = 1.3043874 mm/px, top row 76 -> z 1.70466 (same calibration the chin lock used):
  brow shelf z 1.613, eye centre z 1.598 (x ±0.052, inner corner ±0.029, outer ±0.075), nose root z 1.608 (y -0.149),
  nose tip z 1.545 (y -0.171), nose base z 1.535 (y -0.162), upper lip z 1.510 (y -0.154), mouth line z 1.497 (y -0.149),
  lower lip z 1.4855, chin bottom z 1.449, ear z 1.525..1.592 / y -0.059..+0.004 / x 0.102, cranium hw 0.085 at z 1.62.
"""
import numpy as np
import bmesh

YC = -0.045                      # head centre line in y

LM = dict(
    brow_z=1.6125, eye_z=1.5975, eye_x=0.052, nose_root_z=1.608, nose_tip_z=1.5450, nose_base_z=1.535,
    lip_up_z=1.5105, mouth_z=1.4973, lip_lo_z=1.4855, chin_z=1.449,
    ear_cy=-0.0295, ear_cz=1.5585, ear_ry=0.0295, ear_rz=0.0335, ear_xmax=0.1025,
)

P = dict(
    brow=0.0032, brow_sx=0.090, brow_sz=0.0090,
    glabella=0.0010,
    socket=-0.0030, socket_sx=0.027, socket_sz=0.0135,
    infra=0.0010,                                 # infraorbital soft cushion under the socket
    cheekbone=0.0022, cheek_hollow=0.0, cheek_full=0.0022, temple=-0.0006, tip_ball=0.0012,
    lip_up=0.0034, lip_lo=0.0038, philtrum=-0.0012, chin_cleft=-0.0010, mentolabial=-0.0012,
    ear_scale=0.70, helix=0.0020, concha=-0.0050, antihelix=0.0010, lobe=0.0012,
    # nose profile (z -> ridge y) and half-width (z -> w)
    nose_z=np.array([1.503, 1.513, 1.522, 1.530, 1.5355, 1.540, 1.545, 1.5525, 1.565, 1.580, 1.595, 1.608, 1.618]),
    nose_y=np.array([-0.1500, -0.1540, -0.1545, -0.1575, -0.1625, -0.1690, -0.1715, -0.1700, -0.1640, -0.1580, -0.1530, -0.1490, -0.1470]),
    nose_w=np.array([0.0050, 0.0080, 0.0120, 0.0175, 0.0235, 0.0255, 0.0245, 0.0205, 0.0160, 0.0130, 0.0112, 0.0100, 0.0095]),
    nose_prof_pow=1.10, ala=0.0022, nose_wgt_x=(0.028, 0.060), nose_blend=1.0,
)


def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def g2(a, ca, sa, b, cb, sb):
    return np.exp(-((a - ca) / sa) ** 2 - ((b - cb) / sb) ** 2)


def vnormals(me):
    bm = bmesh.new(); bm.from_mesh(me); bm.normal_update()
    n = np.array([v.normal[:] for v in bm.verts]); bm.free(); return n


EYES = {}
EYE_R = 0.0130
EYE_A, EYE_B, EYE_C = 0.0300, 0.0180, 0.0120     # stylized eyeball ellipsoid semi-axes (x, z, depth)
EYE_RX, EYE_UP, EYE_DN = 0.0235, 0.0108, 0.0092


def eye_centres(V0):
    """eyeball centres from the LOCK surface: front-most skin y at (±eye_x, eye_z) -> sphere front 1 mm proud of it"""
    out = {}
    for s in (-1, 1):
        cx = s * LM['eye_x']
        m = (np.abs(V0[:, 0] - cx) < 0.012) & (np.abs(V0[:, 2] - LM['eye_z']) < 0.010) & (V0[:, 1] < YC)
        ys = V0[m, 1].min()
        out[s] = np.array([cx, ys - 0.0010 + EYE_C, LM['eye_z']])
    return out


def sculpt(obj, base_verts, params=None):
    """base_verts: (N,3) lock coordinates (so repeated runs are deterministic). Returns moved count."""
    Pz = dict(P); Pz.update(params or {})
    L = LM
    me = obj.data
    V0 = np.asarray(base_verts, float)
    me.vertices.foreach_set('co', V0.astype(np.float32).ravel()); me.update()
    N = vnormals(me)
    V = V0.copy()
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    ax = np.abs(x)
    head = (z > 1.43) & (ax < 0.14)
    fr = sm(YC + 0.015, YC - 0.055, y)                     # 1 on the face half
    d = np.zeros(len(V))
    # ---------------- forehead / brow / sockets
    for s_ in (-1, 1):
        d += Pz['brow'] * g2(x, s_ * 0.048, 0.030, z, L['brow_z'], Pz['brow_sz']) * fr
    d += Pz['glabella'] * g2(ax, 0.0, 0.012, z, L['nose_root_z'] + 0.004, 0.008) * fr
    for s in (-1, 1):
        d += Pz['socket'] * g2(x, s * L['eye_x'], Pz['socket_sx'], z, L['eye_z'] - 0.001, Pz['socket_sz']) * fr
        d += Pz['infra'] * g2(x, s * (L['eye_x'] + 0.004), 0.022, z, L['eye_z'] - 0.023, 0.007) * fr
        d += Pz['cheekbone'] * g2(x, s * 0.074, 0.018, z, 1.576, 0.013) * fr
        d += Pz['cheek_hollow'] * g2(x, s * 0.080, 0.016, z, 1.536, 0.016) * fr
        d += Pz['cheek_full'] * g2(x, s * 0.062, 0.022, z, 1.552, 0.017) * fr
        d += Pz['temple'] * g2(x, s * 0.086, 0.014, z, 1.632, 0.016) * fr
    # ---------------- mouth / chin
    d += Pz['lip_up'] * g2(ax, 0.0, 0.030, z, L['lip_up_z'] - 0.002, 0.0065) * fr
    d += Pz['lip_lo'] * g2(ax, 0.0, 0.026, z, L['lip_lo_z'] + 0.001, 0.0065) * fr
    d += Pz['philtrum'] * g2(ax, 0.0, 0.0045, z, (L['nose_base_z'] + L['lip_up_z']) / 2, 0.009) * fr
    d += Pz['mentolabial'] * g2(ax, 0.0, 0.020, z, 1.4745, 0.0055) * fr
    d += Pz['chin_cleft'] * g2(ax, 0.0, 0.0040, z, 1.4585, 0.009) * fr
    d *= head
    V = V + N * d[:, None]
    # ---------------- eye sockets follow the eyeball sphere: skin inside the opening sits >= 1.5 mm behind the sphere
    EYES.clear(); EYES.update(eye_centres(V0))
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    for s_ in (-1, 1):
        C = EYES[s_]
        dx = x - C[0]; dz = z - C[2]
        u = np.clip(dx / (EYE_RX + 0.0080), -0.999, 0.999)
        f = (1 - u * u) ** .6
        inside = head & (y < YC) & (np.abs(dx) < EYE_RX + 0.0080) & (dz < (EYE_UP + 0.0055) * f) & (dz > -(EYE_DN + 0.0055) * f)
        q = np.maximum(1.0 - (dx / EYE_A) ** 2 - (dz / EYE_B) ** 2, 0.0)
        behind = C[1] - (EYE_C - 0.0030) * np.sqrt(q)
        V[inside, 1] = np.maximum(y[inside], behind[inside])
    # ---------------- nose: flatten the old mound to the cheek plane inside |x|<0.036, then raise the wedge
    x, y, z = V[:, 0], V[:, 1], V[:, 2]; ax = np.abs(x)
    zb = np.arange(1.49, 1.64, 0.005); ch = []
    for zz in zb:
        m = (np.abs(z - zz) < 0.006) & (ax > 0.050) & (ax < 0.070) & (y < YC)
        ch.append(y[m].min() if m.any() else np.nan)
    ch = np.array(ch); ok = ~np.isnan(ch); cheek = np.interp(z, zb[ok], ch[ok])
    ridge = np.interp(z, Pz['nose_z'], Pz['nose_y']); w = np.interp(z, Pz['nose_z'], Pz['nose_w'])
    region = head & (y < YC) & (ax < 0.046) & (z > 1.500) & (z < 1.616)
    wz = sm(1.500, 1.510, z) * (1 - sm(1.606, 1.616, z))
    flat = cheek - 0.0015 * np.clip(1 - ax / 0.040, 0, 1)
    wflat = (1 - sm(0.024, 0.040, ax)) * wz
    y_f = y + (flat - y) * wflat                                                     # smooth flatten of the old mound
    prof = np.clip(1 - (ax / np.maximum(w, 1e-4)) ** 2, 0, 1) ** Pz['nose_prof_pow']
    bump = (ridge - flat) * prof * wz
    y_new = np.minimum(y_f, y_f + bump)                                              # bump only ever moves forward
    V[region, 1] = y_new[region]
    tb = Pz['tip_ball'] * g2(np.abs(V[:, 0]), 0.0, 0.011, V[:, 2], L['nose_tip_z'] + 0.001, 0.0065) * fr * head
    V[:, 1] -= tb
    # alae bulbs
    N2 = N
    for s in (-1, 1):
        ab = Pz['ala'] * g2(x, s * 0.0235, 0.0085, z, L['nose_tip_z'] - 0.004, 0.0065) * fr
        V -= N2 * 0.0 * ab[:, None]
        V[:, 1] -= ab * head                      # push forward (−y)
        V[:, 0] += s * 0.8 * ab * head            # and outward
    # ---------------- ears: shrink the lump to the plate extent, add helix / concha / antihelix / lobe
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    for s in (-1, 1):
        side = 0.0885
        ear = (s * x > side) & (z > 1.505) & (z < 1.610) & (y > -0.095) & (y < 0.025)
        u = (y - L['ear_cy']) / L['ear_ry']; v = (z - L['ear_cz']) / L['ear_rz']
        r = np.sqrt(u * u + v * v)
        # 1) scale the lump
        V[ear, 0] = s * (side + (s * x[ear] - side) * Pz['ear_scale'])
        # 2) ear relief, outward along +s x, confined to the ear disc (r<1.15)
        inear = ear & (r < 1.18)
        helix = Pz['helix'] * np.exp(-((r - 0.92) / 0.14) ** 2)
        concha = Pz['concha'] * np.exp(-(r / 0.48) ** 2) * (1 - sm(-0.55, -0.25, u))       # front/tragus side less recessed
        anti = Pz['antihelix'] * np.exp(-((r - 0.58) / 0.12) ** 2) * sm(-0.6, 0.0, u)       # rear half
        lobe = Pz['lobe'] * np.exp(-((v + 0.95) / 0.25) ** 2) * np.exp(-((u - 0.1) / 0.5) ** 2)
        rel = (helix + concha + anti + lobe)
        V[inear, 0] += s * rel[inear]
        idx = np.where(inear)[0]
        for _ in range(2):
            for i in idx:
                nb = idx[np.linalg.norm(V[idx] - V[i], axis=1) < 0.013]
                if len(nb) > 2: V[i, 0] = 0.6 * V[i, 0] + 0.4 * V[nb, 0].mean()
    # keep everything outside the head exactly
    V[~head] = V0[~head]
    me.vertices.foreach_set('co', V.astype(np.float32).ravel()); me.update()
    moved = int((np.linalg.norm(V - V0, axis=1) > 1e-7).sum())
    return moved, V
