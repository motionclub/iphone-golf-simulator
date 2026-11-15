"""torsofield.py: the male chest as muscle shapes (PLAN_FinalLook_Gameplay_2026-11-11, Phase 2), numpy only. Same idea as
armfield.py, about the trunk's upright axis: height y (metres, hero frame) and angle theta about the axis (0 = front, +-90 = the
sides, 180 = back; the body is mirror-symmetric so everything is written in |theta|). The muscles are heights ADDED to the
body as it stands (the 11-11 build's torso), as a displacement FIELD along the horizontal ray from the axis, so the skin and
what is worn over it are moved by the same function; cloth uses the slack rule of armfield.CLOTH.

Adnan, 2026-11-12: "work on the chest, it's not proportional to the shoulders and arms"."""
import numpy as np
import armfield as af
from armfield import sstep, DEG

ZC = 0.040                 # the axis: x = 0, z = ZC (midway between the breastbone and the spine at chest height)
NY, NT = 132, 144
Y0, Y1 = 0.84, 1.50

# WHOLE BODY, on the plain base body (HERO_BUILD=0), 2026-11-12. Adnan: "he just looks extremely weirdly built ... make
# everything proportional, back, abdomen, etc". Measured cause: muscles had been added part by part (arms, then chest) on top
# of the 11-11 build, whose waist term had pulled the waist to 80 cm between a 121 cm chest and 109 cm hips, and whose
# pectoral lobes came to a point. This set replaces all of it with one build: a straight strong trunk (chest : waist about
# 1.3, hips trimmed toward the waist), a flat stomach, a filled back, a neck to match, and arms sized to that.
P = dict(
    # THE CHEST (rebuilt 2026-11-12 after "almost look like female breasts from side angle, and there's some disfiguration"):
    # the version before this built each pectoral as its own 3.3 cm mound, fullest low, with the breastbone left at zero
    # between them: two mounds and a deep cleft, torn where the cleft's walls were steeper than the mesh could carry.
    # Now the forward volume is ONE broad dome over the whole upper chest, breastbone included, fullest high (below the
    # collarbone); the pectorals are thin plates on it with a shallow line between them and a small step at their lower border.
    dome=0.022, dome_w=58.0,                      # the upper chest as one mass: thickness at its fullest height; where it fades toward the sides (deg)
    pec=0.006, pec_low=1.185, pec_edge=0.055,     # the plate: thickness; the height of its lower border at its lowest; how gently it rises from that border
    pec_groove=0.45,                              # how much of the plate's thickness is lost on the breastbone line (0 = none)
    pec_top=1.345, pec_in=0.0, pec_out=66.0,      # collarbone; breastbone line; the armpit fold (deg)
    pec_tie=0.008,                                # the outer upper corner running into the front of the shoulder
    lat=0.013, lat_lo=1.02, lat_peak=1.19, lat_hi=1.275, lat_at=104.0, lat_w=34.0,   # width under the armpits, fading into the waist
    resurface=1.0,                                # 1 = lay the front of the chest onto the smoothed surface (see tables)
    flatten=0.5,                                  # how much of the body's own low chest point is levelled into the plate
    waist=0.003,                                  # all round at the waist (+ fuller): the trunk runs straight from ribs to hips
    abs=-0.010, belly=0.006,                      # the base body's stomach stands as far forward as its chest: the front wall is held in, and the soft pouch below it too
    hip=0.0,                                      # (the hips are no wider than the waist allows; the width low down is the thighs, which this set does not touch)
    upback=0.011, lowback=0.006,                  # the upper back filled between the shoulder blades and the neck; the hollow of the lower back filled
    neck=0.007,                                   # the neck, sides and back
)
# the chest and lats alone, as first built on top of the 11-11 build's torso (proof_chest_v1.jpg)
CHEST_ON_BUILD = dict(pec=0.024, pec_low=1.176, pec_edge=0.036, pec_peak=1.270, pec_lowfrac=0.55, pec_top=1.345, pec_in=3.0, pec_out=66.0, pec_tie=0.012,
                      lat=0.016, lat_lo=1.02, lat_peak=1.19, lat_hi=1.275, lat_at=104.0, lat_w=34.0, flatten=0.85)

DOME_Y = np.array([1.07, 1.10, 1.13, 1.16, 1.19, 1.22, 1.25, 1.28, 1.31, 1.34, 1.365, 1.39])
DOME_V = np.array([0.0, 0.06, 0.14, 0.24, 0.35, 0.48, 0.64, 0.86, 1.00, 0.92, 0.45, 0.0])   # (it runs on down over the ribs: no shelf under the pectorals)

def grids():
    return np.linspace(Y0, Y1, NY), np.linspace(-np.pi, np.pi, NT, endpoint=False)

def add(y, th, P=P, parts=False):
    """Added height (m) at height y and angle th. parts=True: (pectoral, where the pectoral is 0..1, tie to the shoulder, lat)."""
    a = np.abs(np.angle(np.exp(1j * th))) / DEG                       # 0 front .. 180 back
    # --- pectoral: a slab from the breastbone to the armpit fold. Its lower border is lowest under the middle of the slab and
    # rises toward the breastbone and toward the armpit; it is fullest low and thins toward the collarbone.
    mid = (P['pec_in'] + P['pec_out']) / 2; half = (P['pec_out'] - P['pec_in']) / 2
    t = np.clip((a - mid) / half, -1.4, 1.4)
    low = P['pec_low'] + 0.012 * np.clip(-t, 0, 1) ** 2 + 0.045 * np.clip(t, 0, 1) ** 2       # the border climbs toward the armpit, a little toward the breastbone
    up = sstep(low - P['pec_edge'] / 2, low + P['pec_edge'] / 2, y)                            # a soft lower edge
    across = (1 - P.get('pec_groove', 1.0) * (1 - sstep(0.0, 17.0, a))) * (1 - sstep(P['pec_out'] - 18, P['pec_out'] + 6, a))
    where = up * across * (1 - sstep(P['pec_top'] - 0.035, P['pec_top'] + 0.02, y)); pec = P['pec'] * where
    if 'pec_peak' in P:                                                                        # (the first, mound-shaped chest: CHEST_ON_BUILD)
        low = P['pec_low'] + 0.030 * np.clip(t, -1, 1) ** 2 + 0.020 * np.clip(t, 0, 1) ** 2
        up = sstep(low, low + P['pec_edge'], y)
        top = (P['pec_lowfrac'] + (1 - P['pec_lowfrac']) * sstep(low + 0.02, P['pec_peak'], y)) * (1 - 0.70 * sstep(P['pec_peak'] + 0.015, P['pec_top'], y))
        across = sstep(P['pec_in'] - 2.5, P['pec_in'] + 9, a) * (1 - sstep(P['pec_out'] - 15, P['pec_out'] + 5, a))
        where = up * across * (1 - sstep(P['pec_top'] - 0.02, P['pec_top'] + 0.02, y)); pec = P['pec'] * top * where
    # the dome: by height (fullest just under the collarbone, gone by the bottom of the ribs), fading round toward the sides
    dome = P.get('dome', 0.0) * np.interp(y, DOME_Y, DOME_V) * (1 - sstep(P.get('dome_w', 58.0) - 22, P.get('dome_w', 58.0) + 22, a))
    pec = pec + dome
    # the outer upper corner: the muscle's tail toward the arm, so the chest meets the front of the shoulder instead of leaving a notch
    tie = P['pec_tie'] * np.exp(-((a - (P['pec_out'] + 2)) / 15.0) ** 2) * np.exp(-((y - 1.285) / 0.038) ** 2)
    # --- latissimus: width under the armpit, widest a hand below it, gone by the waist
    lat = P['lat'] * np.exp(-((a - P['lat_at']) / P['lat_w']) ** 2) * sstep(P['lat_lo'], P['lat_peak'], y) * (1 - sstep(P['lat_peak'] + 0.03, P['lat_hi'], y))
    # --- the rest of the trunk (zero in the chest-only set)
    g = lambda k: P.get(k, 0.0); bump = lambda c, w: np.exp(-((y - c) / w) ** 2)
    front = 1 - sstep(30, 55, a); back = sstep(115, 150, a); side = np.exp(-((a - 90) / 38.0) ** 2)
    rest = (g('waist') * bump(1.03, 0.075)
            + g('abs') * front * sstep(0.95, 1.01, y) * (1 - sstep(1.06, 1.15, y))
            - g('belly') * (1 - sstep(40, 70, a)) * bump(0.945, 0.045)
            - g('hip') * side * bump(0.905, 0.05)
            + g('upback') * back * sstep(1.16, 1.24, y) * (1 - sstep(1.33, 1.39, y))
            + g('lowback') * back * bump(1.03, 0.06)
            + g('neck') * sstep(55, 85, a) * sstep(1.395, 1.425, y) * (1 - sstep(1.462, 1.485, y)))   # sides and back only: the throat and the jaw are the face's
    lat = lat + rest
    return (pec, where, tie, lat) if parts else (pec ** 4 + tie ** 4) ** 0.25 + lat

def base_table(body):
    """The trunk's own radius about the axis over the grid, from the vertices that are not arm (body['armLeft'/'armRight'])."""
    yg, tg = grids(); pos = body['pos']
    arms = body['armLeft'] + body['armRight']
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2] - ZC
    sel = (arms < .35) & (y > Y0 - .02) & (y < Y1 + .02)
    rho = np.hypot(x, z)[sel]; th = np.arctan2(x, z)[sel]; yy = y[sel]
    acc = np.zeros((NY, NT)); cnt = np.zeros((NY, NT))
    iy = (yy - Y0) / (Y1 - Y0) * (NY - 1); it = (th + np.pi) / (2 * np.pi) * NT
    ok = (iy >= 0) & (iy <= NY - 1)
    for dy in (0, 1):
        for dt in (0, 1):
            i = np.clip(np.floor(iy[ok]).astype(int) + dy, 0, NY - 1); j = (np.floor(it[ok]).astype(int) + dt) % NT
            w = (1 - np.abs(iy[ok] - (np.floor(iy[ok]) + dy))) * (1 - np.abs(it[ok] - (np.floor(it[ok]) + dt)))
            np.add.at(acc, (i, j), w * rho[ok]); np.add.at(cnt, (i, j), w)
    have = cnt > 1e-3; t = np.where(have, acc / np.maximum(cnt, 1e-9), 0)
    for _ in range(300):
        if have.all(): break
        pad = lambda a: np.pad(a, ((1, 1), (0, 0)), mode='edge')
        n = sum(np.roll(pad(t * have), s, a)[1:-1] for a, s in ((0, 1), (0, -1), (1, 1), (1, -1)))
        d = sum(np.roll(pad(have.astype(float)), s, a)[1:-1] for a, s in ((0, 1), (0, -1), (1, 1), (1, -1)))
        fill = (~have) & (d > 0); t[fill] = n[fill] / d[fill]; have = have | fill
    for _ in range(6):
        t = (t + np.roll(t, 1, 1) + np.roll(t, -1, 1)) / 3; t[1:-1] = (t[:-2] + t[1:-1] + t[2:]) / 3
    return t

def tables(body, P=P):
    yg, tg = grids(); Y, TH = np.meshgrid(yg, tg, indexing='ij')
    base = base_table(body)
    # The body's own chest comes to a point low on each side (a cone). The slab is built over the chest with that point
    # smoothed away: where the body already stands proud of its own smoothed self the slab adds less, around it more.
    smooth = base.copy()
    for _ in range(40):
        pad = np.vstack([smooth[:1], smooth, smooth[-1:]]); smooth = (pad[:-2] + pad[1:-1] + pad[2:]) / 3
    for _ in range(20): smooth = (np.roll(smooth, 1, 1) + smooth + np.roll(smooth, -1, 1)) / 3
    pec, where, tie, lat = add(Y, TH, P, parts=True)
    mid = base.copy()
    for _ in range(10):                                   # (the detail to level is the 5 cm point, not the table's cell-to-cell noise)
        pad = np.vstack([mid[:1], mid, mid[-1:]]); mid = (pad[:-2] + pad[1:-1] + pad[2:]) / 3; mid = (np.roll(mid, 1, 1) + mid + np.roll(mid, -1, 1)) / 3
    want = pec + P['flatten'] * where * (smooth - mid)
    pec2 = np.maximum((want + np.sqrt(want ** 2 + 0.002 ** 2)) / 2 - 0.001, 0)   # smooth max(want, 0): the slab never cuts into the body
    d = (pec2 ** 4 + tie ** 4) ** 0.25 + lat
    for _ in range(2):                                    # no edge in the field sharper than the mesh can carry
        pad = np.vstack([d[:1], d, d[-1:]]); d = (pad[:-2] + pad[1:-1] + pad[2:]) / 3; d = (np.roll(d, 1, 1) + d + np.roll(d, -1, 1)) / 3
    # RESURFACE: the base body carries small sculpt dents along the pectorals' edges; over the front of the chest the skin
    # is laid onto the smoothed surface itself (apply), so the chest that comes out is clean, not those dents with muscle on top
    a = np.abs(np.angle(np.exp(1j * TH))) / DEG
    zone = (1 - sstep(P['pec_out'] - 12, P['pec_out'] + 10, a)) * sstep(1.12, 1.17, Y) * (1 - sstep(1.32, 1.37, Y)) if P.get('resurface', 0) else np.zeros_like(base)
    return dict(base=base, d=d, zone=zone * P.get('resurface', 0), mid=mid)

def lookup(t, y, th):
    iy = np.clip((y - Y0) / (Y1 - Y0) * (NY - 1), 0, NY - 1); it = (th + np.pi) / (2 * np.pi) * NT
    i0 = np.floor(iy).astype(int); i1 = np.minimum(i0 + 1, NY - 1); j0 = np.floor(it).astype(int) % NT; j1 = (j0 + 1) % NT
    fy = iy - i0; ft = it - np.floor(it)
    return (t[i0, j0] * (1 - fy) + t[i1, j0] * fy) * (1 - ft) + (t[i0, j1] * (1 - fy) + t[i1, j1] * fy) * ft

def cloth_table(T, garment_pos, radius=0.04, keep=None, drape=0.07):
    """How far a garment has to move, over the grid, so the grown chest stays `cmin` under it: nothing where the garment had the
    slack, and where it had not, a smooth TENT over the need (cloth bridges the groove between the pectorals and the fold under
    them; it does not print them). The tent is the need spread by `radius` and then blurred within that radius, so it is never
    less than the need."""
    yg, tg = grids(); x, y, z = garment_pos[:, 0], garment_pos[:, 1], garment_pos[:, 2] - ZC
    rho = np.hypot(x, z); th = np.arctan2(x, z); c = rho - lookup(T['base'], y, th)
    ok = (y > Y0) & (y < Y1) & (c > -0.01) & (c < 0.09)
    if keep is not None: ok = ok & keep                         # (the sleeves are the arm's cloth, not the trunk's)
    iy = np.rint((y[ok] - Y0) / (Y1 - Y0) * (NY - 1)).astype(int); it = np.rint((th[ok] + np.pi) / (2 * np.pi) * NT).astype(int) % NT
    cm = np.full((NY, NT), np.inf); np.minimum.at(cm, (iy, it), c[ok])
    for _ in range(3):                                           # close the gaps between vertices with the nearest clearance
        nb = np.minimum.reduce([np.roll(cm, 1, 1), np.roll(cm, -1, 1), np.vstack([cm[:1], cm[:-1]]), np.vstack([cm[1:], cm[-1:]])])
        cm = np.where(np.isinf(cm), nb, cm)
    need = np.clip(af.CLOTH['cmin'] + T['d'] - cm, 0, np.maximum(T['d'], 0)); need[np.isinf(cm)] = 0
    ny = max(1, int(round(radius / ((Y1 - Y0) / (NY - 1))))); nt = max(1, int(round(radius / 0.18 / (2 * np.pi / NT))))
    tent = need.copy()
    for k in range(1, ny + 1): tent = np.maximum(tent, np.maximum(np.vstack([need[k:], np.zeros((k, NT))]), np.vstack([np.zeros((k, NT)), need[:-k]])))
    t2 = tent.copy()
    for k in range(1, nt + 1): t2 = np.maximum(t2, np.maximum(np.roll(tent, k, 1), np.roll(tent, -k, 1)))
    for _ in range(ny // 2):
        pad = np.vstack([t2[:1], t2, t2[-1:]]); t2 = (pad[:-2] + pad[1:-1] + pad[2:]) / 3
    for _ in range(nt // 2): t2 = (np.roll(t2, 1, 1) + t2 + np.roll(t2, -1, 1)) / 3
    t2 = np.maximum(t2, need)
    # cloth hangs from the chest: below the fullest point it falls nearly straight instead of tucking back under the pectorals
    keep = 0.5 ** (((Y1 - Y0) / (NY - 1)) / drape)
    for i in range(NY - 2, -1, -1): t2[i] = np.maximum(t2[i], t2[i + 1] * keep)
    return t2

def apply(pos, T, reach=0.035, fade=0.05, cloth=False, arms=None):
    """Move points by the chest field (rest pose, hero frame). arms = (B, TL, TR): the arm field's tables, so that points that
    are the upper arm's are left alone."""
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2] - ZC
    rho = np.hypot(x, z); th = np.arctan2(x, z)
    delta = lookup(T['d'], y, th); base = lookup(T['base'], y, th)
    inside = (y > Y0) & (y < Y1)
    near = 1 - sstep(base + reach, base + reach + fade, rho)
    free = np.ones(len(pos))
    if arms is not None:
        B, TL, TR = arms; free = (1 - af.armness(pos, B, TL, 'Left')) * (1 - af.armness(pos, B, TR, 'Right'))
    if cloth: delta = lookup(cloth_table(T, pos, keep=free > .5), y, th)           # (one garment per call)
    amt = delta * near * inside * free
    if not cloth and 'zone' in T:
        onskin = 1 - sstep(0.010, 0.020, np.abs(rho - base))
        amt = amt + lookup(T['zone'], y, th) * (lookup(T['mid'], y, th) - rho) * onskin * inside * free
    out = pos.copy(); r = np.maximum(rho, 1e-6)
    out[:, 0] += x / r * amt; out[:, 2] += z / r * amt
    return out
