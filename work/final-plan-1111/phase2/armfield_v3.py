"""armfield.py: the male arm as separate muscles (PLAN_FinalLook_Gameplay_2026-11-11, Phase 2 step 1), numpy only.

The arm's surface is written as a radius R(u, phi) around each bone: a bony core plus one belly per muscle, joined with a
smooth maximum so neighbouring muscles keep a groove between them instead of melting into one tube. "Transferred onto the
current mesh" means: the base body's own radius is measured into the same (u, phi) table, and the difference
  D(u, phi) = mask * (R_muscles - R_base)
is a displacement FIELD along the radial direction. The same field moves the skin and anything worn over it, so cloth keeps
its distance from the skin (the 11-11 build's lesson: identical geometric fields, never weight masks).

Coordinates (armio.coords): u along the bone (upper: 0 shoulder joint .. 1 elbow; fore: 0 elbow .. 1 wrist),
phi about it: 0 = front of the body, +90 deg = outer side, 180 = back, -90 = inner side (the armpit side). Left arm; the
right arm is the mirror image (x -> -x).
"""
import numpy as np
import armio

DEG = np.pi / 180
NU, NPHI = 96, 96
U_UP = (-0.55, 1.20)      # the upper-arm table runs over the shoulder cap and a little past the elbow
U_FO = (-0.20, 1.05)

def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def belly(u, a, p, b, full=1.0):
    """0 outside [a, b], 1 at p: a muscle belly's fullness along its length (full > 1 = blunter ends)."""
    up = sstep(a, p, u); down = 1 - sstep(p, b, u)
    return np.clip(up * down, 0, 1) ** (1 / full)

def lobe(phi, centre, width):
    d = np.angle(np.exp(1j * (phi - centre * DEG)))
    return np.exp(-(d / (width * DEG)) ** 2)

def smax(parts, p):
    return np.power(sum(np.power(np.maximum(x, 0), p) for x in parts), 1 / p)

# ---------------------------------------------------------------- the muscles (heights and radii in metres)
P = dict(
    scale=1.0,            # all bellies
    sep=5.0,              # smooth-max power: higher = deeper grooves between muscles
    up_core=0.052, elbow_w=0.052, elbow_d=0.044,     # upper-arm core; the elbow is wide across (epicondyles), shallow front to back
    fo_core0=0.046, fo_core1=0.034, fo_taper=1.35, wrist_flat=0.86,
    delt_lat=0.014, delt_ant=0.010, delt_post=0.009, # ADDED to the base shoulder (the cap is already there); see field_tables
    biceps=0.026, tri_long=0.022, tri_lat=0.024, brachialis=0.008,
    brachiorad=0.017, flexors=0.016, extensors=0.010, olecranon=0.005,
)

def upper_radius(u, phi, P=P):
    """Shoulder to elbow. u may run past both ends (table edges)."""
    k = sstep(0.62, 1.0, u)                                   # toward the elbow the core turns into the joint's oval
    core_w = P['up_core'] + (P['elbow_w'] - P['up_core']) * k # half-width across (phi = +-90)
    core_d = P['up_core'] + (P['elbow_d'] - P['up_core']) * k # half-depth front to back
    core = 1 / np.sqrt((np.cos(phi) / core_d) ** 2 + (np.sin(phi) / core_w) ** 2)
    s = P['scale']
    m = [
        # biceps: the front, peaking past mid-arm, running into the elbow's crease
        s * P['biceps'] * belly(u, 0.20, 0.60, 1.03, 1.3) * lobe(phi, -4, 44),
        # triceps: the long head on the inner back, the lateral head on the outer back (the horseshoe), ending in a flat tendon
        s * P['tri_long'] * belly(u, 0.05, 0.45, 0.88, 1.3) * lobe(phi, -158, 40),
        s * P['tri_lat'] * belly(u, 0.22, 0.50, 0.84, 1.2) * lobe(phi, 138, 32),
        # brachialis peeking out low on the outer side, and the brachioradialis starting above the elbow
        s * P['brachialis'] * belly(u, 0.50, 0.80, 1.05, 1.0) * lobe(phi, 78, 26),
        s * P['brachiorad'] * 0.75 * belly(u, 0.70, 1.08, 1.60, 1.0) * lobe(phi, 52, 34),
        s * P['olecranon'] * belly(u, 0.86, 1.02, 1.20, 1.0) * lobe(phi, 180, 24),
    ]
    return core + smax(m, P['sep'])

def fore_radius(u, phi, P=P):
    """Elbow to wrist."""
    k = np.clip(u, 0, 1) ** P['fo_taper']
    r = P['fo_core0'] + (P['fo_core1'] - P['fo_core0']) * k
    # the elbow end is the joint's oval (wide across); the wrist end is flat the other way (wide front to back as the arm hangs)
    e = 1 - sstep(-0.05, 0.30, u); w = sstep(0.55, 1.0, u)
    core_w = r * (1 - e) + P['elbow_w'] * e; core_d = r * (1 - e) + P['elbow_d'] * e
    core_w = core_w * (1 - w * (1 - P['wrist_flat']))
    core = 1 / np.sqrt((np.cos(phi) / core_d) ** 2 + (np.sin(phi) / core_w) ** 2)
    s = P['scale']
    m = [
        # brachioradialis and the wrist extensors beside it: the outer front, crossing the elbow from the upper arm
        s * P['brachiorad'] * belly(u, -0.30, 0.16, 0.62, 1.2) * lobe(phi, 58, 40),
        # the flexor mass on the inner front
        s * P['flexors'] * belly(u, -0.08, 0.20, 0.64, 1.2) * lobe(phi, -72, 50),
        # the extensor mass on the outer back
        s * P['extensors'] * belly(u, -0.02, 0.24, 0.66, 1.1) * lobe(phi, 150, 44),
        s * P['olecranon'] * belly(u, -0.18, -0.02, 0.10, 1.0) * lobe(phi, 180, 24),
    ]
    return core + smax(m, P['sep'])

def deltoid_add(u, phi, P=P):
    """The three heads of the deltoid as height ADDED to the base shoulder: the outer head, the front and the back, coming to a
    point on the outer side just above mid-arm, with a furrow between each pair."""
    s = P['scale']
    heads = [
        s * P['delt_lat'] * belly(u, -0.40, 0.06, 0.52, 1.5) * lobe(phi, 92, 36),
        s * P['delt_ant'] * belly(u, -0.34, 0.08, 0.46, 1.4) * lobe(phi, 22, 30),
        s * P['delt_post'] * belly(u, -0.34, 0.08, 0.46, 1.4) * lobe(phi, 162, 30),
    ]
    return smax(heads, P['sep'])

def grids():
    uu = np.linspace(*U_UP, NU); uf = np.linspace(*U_FO, NU)
    ph = np.linspace(-np.pi, np.pi, NPHI, endpoint=False)
    return uu, uf, ph

def base_tables(body, B, side='Left'):
    """The base body's own radius over the same grids: binned from the arm's vertices, holes filled, lightly smoothed."""
    S, E, W = B[side + "UpperArm"], B[side + "LowerArm"], B[side + "Hand"]
    uu, uf, ph = grids()
    w = body['w']; o = 0 if side == 'Left' else 4
    arm = w[:, o + 0] + w[:, o + 1] + w[:, o + 2] + w[:, o + 3]
    out = []
    for (a, b, ug, mine) in ((S, E, uu, w[:, o + 0] + w[:, o + 1]), (E, W, uf, w[:, o + 2] + w[:, o + 3] * .5 + w[:, o + 1] * .3)):
        u, rho, phi, L = armio.coords(body['pos'], a, b)
        sel = (arm > .35) & (mine > .15) & (rho < .13)
        if a is S:   # (the deltoid's skin is partly the shoulder's and the chest's: take the outer half geometrically)
            outer = np.abs(np.angle(np.exp(1j * (phi - np.pi / 2)))) < 105 * DEG
            sel = sel | (outer & (u > -0.5) & (u < 0.38) & (rho < .115) & (body['pos'][:, 0] * (1 if side == 'Right' else -1) > 0.12))
        acc = np.zeros((NU, NPHI)); cnt = np.zeros((NU, NPHI))
        iu = (u[sel] - ug[0]) / (ug[-1] - ug[0]) * (NU - 1); ip = (phi[sel] + np.pi) / (2 * np.pi) * NPHI
        ok = (iu >= 0) & (iu <= NU - 1)
        for du in (0, 1):
            for dp in (0, 1):
                i = np.clip(np.floor(iu[ok]).astype(int) + du, 0, NU - 1); j = (np.floor(ip[ok]).astype(int) + dp) % NPHI
                wt = (1 - np.abs(iu[ok] - (np.floor(iu[ok]) + du))) * (1 - np.abs(ip[ok] - (np.floor(ip[ok]) + dp)))
                np.add.at(acc, (i, j), wt * rho[sel][ok]); np.add.at(cnt, (i, j), wt)
        have = cnt > 1e-3; t = np.where(have, acc / np.maximum(cnt, 1e-9), 0)
        for _ in range(200):                                   # diffuse into the holes (rows with no vertices, the far side of the shoulder)
            if have.all(): break
            n = sum(np.roll(np.pad(t, ((1, 1), (0, 0)), mode='edge'), s, a)[1:-1] * np.roll(np.pad(have.astype(float), ((1, 1), (0, 0)), mode='edge'), s, a)[1:-1] for a, s in ((0, 1), (0, -1), (1, 1), (1, -1)))
            d = sum(np.roll(np.pad(have.astype(float), ((1, 1), (0, 0)), mode='edge'), s, a)[1:-1] for a, s in ((0, 1), (0, -1), (1, 1), (1, -1)))
            fill = (~have) & (d > 0); t[fill] = n[fill] / d[fill]; have = have | fill
        for _ in range(2):                                     # a light blur: the field must be smooth, the base's lumps are not wanted
            t = (t + np.roll(t, 1, 1) + np.roll(t, -1, 1)) / 3
            t[1:-1] = (t[:-2] + t[1:-1] + t[2:]) / 3
        out.append(t)
    return out

def masks():
    """Where the field acts (0..1): all of the arm, fading out at the wrist (the hand keeps its join) and on the body's side of
    the shoulder (armpit, chest and shoulder blade are Phase 2 step 5, not the arm)."""
    uu, uf, ph = grids(); U, PH = np.meshgrid(uu, ph, indexing='ij')
    inner = lobe(PH, -90, 70)                                  # the armpit side
    mu = sstep(-0.42, -0.12, U) * (1 - inner * (1 - sstep(0.10, 0.34, U)))
    U2, PH2 = np.meshgrid(uf, ph, indexing='ij')
    mf = 1 - sstep(0.80, 0.97, U2)
    return mu, mf

def centre_line(t, ug, lo, hi):
    """Where the limb's middle runs relative to the bone, per station (front, up) in metres: the base ring's area centroid,
    smoothed along the limb and held constant outside [lo, hi] (where the base is not a closed ring)."""
    ph = np.linspace(-np.pi, np.pi, NPHI, endpoint=False)
    x, y = t * np.cos(ph), t * np.sin(ph)
    cross = x * np.roll(y, -1, 1) - np.roll(x, -1, 1) * y
    area = cross.sum(1) / 2
    cx = ((x + np.roll(x, -1, 1)) * cross).sum(1) / (6 * area); cy = ((y + np.roll(y, -1, 1)) * cross).sum(1) / (6 * area)
    ok = (ug >= lo) & (ug <= hi)
    i0, i1 = np.argmax(ok), len(ok) - 1 - np.argmax(ok[::-1])
    cx[:i0], cy[:i0], cx[i1 + 1:], cy[i1 + 1:] = cx[i0], cy[i0], cx[i1], cy[i1]
    for _ in range(6):
        cx[1:-1] = (cx[:-2] + cx[1:-1] + cx[2:]) / 3; cy[1:-1] = (cy[:-2] + cy[1:-1] + cy[2:]) / 3
    return cx, cy

def about_bone(radius, U, PH, cx, cy, P):
    """Radius about the bone of the closed curve `radius(u, angle about the centre line)`: where the ray from the bone meets it."""
    lo = np.zeros_like(U); hi = np.full_like(U, 0.25)
    C, S_ = np.cos(PH), np.sin(PH)
    for _ in range(44):
        mid = (lo + hi) / 2
        qx, qy = mid * C - cx[:, None], mid * S_ - cy[:, None]
        outside = np.hypot(qx, qy) > radius(U, np.arctan2(qy, qx), P)
        hi = np.where(outside, mid, hi); lo = np.where(outside, lo, mid)
    return (lo + hi) / 2

def field_tables(body, B, side='Left', P=P):
    uu, uf, ph = grids(); bu, bf = base_tables(body, B, side); mu, mf = masks()
    U, PH = np.meshgrid(uu, ph, indexing='ij'); U2, PH2 = np.meshgrid(uf, ph, indexing='ij')
    cux, cuy = centre_line(bu, uu, 0.40, 0.95); cfx, cfy = centre_line(bf, uf, 0.05, 0.80)
    # the two centre lines must agree at the elbow, or the two bones' targets would not meet
    ex, ey = (cux[np.argmin(np.abs(uu - 1))] + cfx[np.argmin(np.abs(uf))]) / 2, (cuy[np.argmin(np.abs(uu - 1))] + cfy[np.argmin(np.abs(uf))]) / 2
    ku = sstep(0.6, 1.0, uu); cux, cuy = cux * (1 - ku) + ex * ku, cuy * (1 - ku) + ey * ku
    kf = 1 - sstep(0.0, 0.4, uf); cfx, cfy = cfx * (1 - kf) + ex * kf, cfy * (1 - kf) + ey * kf
    tu, tf = about_bone(upper_radius, U, PH, cux, cuy, P), about_bone(fore_radius, U2, PH2, cfx, cfy, P)
    # the shoulder: the base cap with the deltoid's heads added, handing over to the muscle model below it
    hand = sstep(0.16, 0.42, U)
    tu = (bu + deltoid_add(U, PH, P)) * (1 - hand) + (tu + deltoid_add(U, PH, P)) * hand
    return dict(du=mu * (tu - bu), df=mf * (tf - bf), bu=bu, bf=bf, tu=tu, tf=tf, centre=(cux, cuy, cfx, cfy))

def lookup(t, ug, u, phi):
    iu = np.clip((u - ug[0]) / (ug[-1] - ug[0]) * (NU - 1), 0, NU - 1); ip = (phi + np.pi) / (2 * np.pi) * NPHI
    i0 = np.floor(iu).astype(int); i1 = np.minimum(i0 + 1, NU - 1); j0 = np.floor(ip).astype(int) % NPHI; j1 = (j0 + 1) % NPHI
    fu = iu - i0; fp = ip - np.floor(ip)
    return (t[i0, j0] * (1 - fu) + t[i1, j0] * fu) * (1 - fp) + (t[i0, j1] * (1 - fu) + t[i1, j1] * fu) * fp

def apply(pos, B, T, side='Left', reach=0.035, fade=0.05):
    """Move points by the field. `pos` in the hero's frame; the right arm is done as the mirror of the left with the same tables
    (pass T built from the left side, or from the right side mirrored). Returns the new positions.
    A point takes the field of the bone it is nearer, blended across the elbow; beyond `reach` outside the base skin the field
    fades out over `fade` (the far side of the torso's cloth is not the sleeve)."""
    mirror = side == 'Right'
    p = pos.copy()
    Bm = {k: v.copy() for k, v in B.items()}
    if mirror:
        p[:, 0] *= -1
        S, E, W = (Bm["RightUpperArm"] * [-1, 1, 1], Bm["RightLowerArm"] * [-1, 1, 1], Bm["RightHand"] * [-1, 1, 1])
    else:
        S, E, W = Bm["LeftUpperArm"], Bm["LeftLowerArm"], Bm["LeftHand"]
    uu, uf, ph = grids()
    out = np.zeros_like(p)
    wsum = np.zeros(len(p))
    # blend weight across the elbow: signed distance to the plane through E square to the bisector of the two bones
    a1 = (E - S) / np.linalg.norm(E - S); a2 = (W - E) / np.linalg.norm(W - E); bis = (a1 + a2) / np.linalg.norm(a1 + a2)
    sd = (p - E) @ bis
    wf = sstep(-0.02, 0.02, sd); wu = 1 - wf
    for (a, b, ug, dt, bt, wgt) in ((S, E, uu, T['du'], T['bu'], wu), (E, W, uf, T['df'], T['bf'], wf)):
        ax, f, up = armio.frame(a, b); L = np.linalg.norm(b - a)
        d = p - a; t = d @ ax; r = d - np.outer(t, ax); rho = np.linalg.norm(r, axis=1); phi = np.arctan2(r @ up, r @ f); u = t / L
        delta = lookup(dt, ug, u, phi); base = lookup(bt, ug, u, phi)
        inside = (u >= ug[0]) & (u <= ug[-1])
        near = 1 - sstep(base + reach, base + reach + fade, rho)
        amt = delta * near * inside * wgt
        out += (r / np.maximum(rho, 1e-6)[:, None]) * amt[:, None]
    q = p + out
    if mirror: q[:, 0] *= -1
    return q

def girths(pos, body_w, B, side='Left'):
    """Girth (m) and front-back / across ratio at stations along the arm, from the arm's own vertices."""
    S, E, W = B[side + "UpperArm"], B[side + "LowerArm"], B[side + "Hand"]
    o = 0 if side == 'Left' else 4
    rows = []
    for name, a, b in (("upper", S, E), ("fore", E, W)):
        u, rho, phi, L = armio.coords(pos, a, b)
        sel = (body_w[:, o + 1] + body_w[:, o + 2] + body_w[:, o + 3] > .5) & (rho < .13)
        for k in range(10):
            s = sel & (u >= k / 10) & (u < (k + 1) / 10)
            if s.sum() < 12: continue
            r, pp = rho[s], phi[s]
            def half(c):
                q = np.abs(np.cos(pp - c)) > .9
                return r[q].mean() if q.sum() else np.nan
            fb = (half(0) + half(np.pi)) / 2; ac = (half(np.pi / 2) + half(-np.pi / 2)) / 2
            # girth of the ring: order by angle and sum the chord lengths
            order = np.argsort(pp); x, y = (r * np.cos(pp))[order], (r * np.sin(pp))[order]
            nb = 36; bins = np.floor((pp[order] + np.pi) / (2 * np.pi) * nb).astype(int) % nb
            rx = np.array([x[bins == i].mean() if (bins == i).any() else np.nan for i in range(nb)]); ry = np.array([y[bins == i].mean() if (bins == i).any() else np.nan for i in range(nb)])
            ok = ~np.isnan(rx); rx, ry = rx[ok], ry[ok]
            g = np.hypot(np.roll(rx, -1) - rx, np.roll(ry, -1) - ry).sum()
            rows.append((name, k / 10 + .05, g, fb, ac))
    return rows
