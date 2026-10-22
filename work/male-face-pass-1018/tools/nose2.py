"""Anatomical male nose (2026-10-18 round 3), applied as a post-step on the 10-17 warp result, face frame in mm.
nose_op(x, y, z, Q) -> x', z'. Components: dorsum/tip ridge on the sheet-17 profile Zp(y), tip lobule cross-section, two alar lobes,
smooth-max union (the alar creases are the valleys of the union), unioned with the cheek, blended by w inside the nose zone."""
import numpy as np
def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def smax(a, b, k):
    h = np.clip(.5 + .5 * (a - b) / k, 0, 1); return b + (a - b) * h + k * h * (1 - h)
# sheet-17 midline profile in the game face frame (aligned at the nasion against the 10-17 head), y step -2 from +10
PY = np.arange(10, -64, -2.0)
PZ = np.array([38.7,38.1,37.3,37.3,37.3,38.2,39.3,40.6,42.0,43.6,45.3,46.6,47.7,48.8,49.8,50.8,51.9,53.1,54.4,55.6,57.0,58.9,60.9,62.3,63.6,64.8,65.7,65.8,65.7,65.3,64.9,63.8,62.2,56.0,49.7,47.6,45.7])
DEF = dict(flare=6.5, flare_x0=12., flare_x1=40., flare_y=-49., flare_h=9., flare_z=(22., 34.),
           w_top=8.5, w_mid=10., w_tip=10.5, ridge_drop=5.0, tip_lobe_y=-47., tip_lobe_drop=7.0,
           ala_x=16.0, ala_y=-49.5, ala_rx=7.5, ala_ry=6.5, ala_rz=6.0, ala_back=12.0, k_ala=1.6, k_cheek=2.5,
           y_top=8., y_bot=-56.5, blend=.88, zone_x=(26., 32.), zone_z=(18., 28.))
def nose_op(x, y, z, Q=DEF, nz=None):
    Q = {**DEF, **Q}
    ax = np.abs(x)
    # 1. flare the wings sideways (vertex distribution), tip/bridge stay
    prof = np.where(ax < Q['flare_x0'], ax / Q['flare_x0'], np.clip(1 - (ax - Q['flare_x0']) / (Q['flare_x1'] - Q['flare_x0']), 0, 1)); prof = prof * prof * (3 - 2 * prof)
    reg = np.exp(-((y - Q['flare_y']) / Q['flare_h']) ** 4) * ss(Q['flare_z'][0], Q['flare_z'][1], z) * ss(Q['y_bot'] + Q.get('flare_stop', (-1.5, 1.5))[0], Q['y_bot'] + Q.get('flare_stop', (-1.5, 1.5))[1], y)
    x = x + np.sign(x) * Q['flare'] * prof * reg; ax = np.abs(x)
    # 2. ridge on the reference profile, width growing toward the tip
    zp = np.interp(y, PY[::-1], PZ[::-1])
    w = np.interp(y, [-56, -47, -38, -25, -10, 8], [Q['w_tip'], Q['w_tip'], Q['w_mid'], Q['w_mid'] * .95, Q['w_top'], Q['w_top']])
    drop = np.where(y < -36, Q['tip_lobe_drop'], Q['ridge_drop'])
    drop = np.interp(y, [-56, -44, -36, 8], [Q['tip_lobe_drop'], Q['tip_lobe_drop'], Q['ridge_drop'], Q['ridge_drop']])
    if Q.get('ridge_depth'):   # soft side walls: same curvature on top, flattening toward the cheek (a parabola keeps steepening)
        D = Q['ridge_depth']; ridge = zp - D * (1 - np.exp(-drop * (ax / w) ** 2 / D))
    else:
        ridge = zp - drop * (ax / w) ** 2
    # 3. alar lobes (ellipsoids) set back from the tip
    zt = np.interp(Q['ala_y'], PY[::-1], PZ[::-1]); zc = zt - Q['ala_back'] - Q['ala_rz']
    q = 1 - ((ax - Q['ala_x']) / Q['ala_rx']) ** 2 - ((y - Q['ala_y']) / Q['ala_ry']) ** 2
    if Q.get('ala_smooth'):   # smooth rim: (1-r^2)^p inside, the same power continued below the rim (zero slope at the rim, no hard crease)
        pw = Q['ala_smooth']; ala = zc + Q['ala_rz'] * np.sign(q) * np.abs(q) ** pw
    else:
        ala = np.where(q > 0, zc + Q['ala_rz'] * np.sqrt(np.clip(q, 0, 1)), zc + Q['ala_rz'] * q * 3)   # continues below the rim as a steep falloff
    kb = Q.get('k_ala_bottom')   # crease only along the top of the wing; toward the base the wings flow into the tip (one rounded base)
    k = Q['k_ala'] if kb is None else Q['k_ala'] + (kb - Q['k_ala']) * ss(Q.get('k_ala_y', (-44., -50.))[0], Q.get('k_ala_y', (-44., -50.))[1], y)
    N = smax(ridge, ala, k)
    # 4. vertical limits: nothing above the nasion zone or below the nose base
    N = np.where((y > Q['y_top']) | (y < Q['y_bot']), -1e3, N)
    N = N - 25 * ss(Q['y_bot'] + Q.get('base_soft', 3.5), Q['y_bot'], y) - 60 * ss(Q['y_top'] - 3, Q['y_top'], y)
    # 5. union with the existing surface (cheeks stay), the old narrow nose is carved to N where it stands higher
    old = (ax < 13) & (y < -28) & (y > Q['y_bot'] + Q.get('carve_stop', 0.))
    zc_ = np.where(old, np.minimum(z, N), z)
    T = smax(zc_, N, Q['k_cheek'])
    m = (1 - ss(Q['zone_x'][0], Q['zone_x'][1], ax)) * ss(Q['zone_z'][0], Q['zone_z'][1], z) * ss(Q['y_bot'] - 4, Q['y_bot'] - 1, y) * (1 - ss(Q['y_top'], Q['y_top'] + 4, y))
    if Q.get('nostril_keep'): nk = Q['nostril_keep']; m = m * (1 - nk[4] * np.exp(-((ax - nk[0]) / nk[1]) ** 2 - ((y - nk[2]) / nk[3]) ** 2))
    if nz is not None and Q.get('front_gate'): m = m * ss(Q['front_gate'][0], Q['front_gate'][1], nz)
    z = z + Q['blend'] * m * (T - z)
    return x, z

def zone_w(x, y, z):
    """nose zone for the relax step (as the game's MaleNoseZone)"""
    ax = np.abs(x)
    return (1 - ss(24, 30, ax)) * ss(20, 30, z) * ss(-56.5 - 5, -56.5 - 2, y) * (1 - ss(8 - 2, 8 + 2, y))

LIPS = dict(seam=-78.5, corner_drop=1.2, W=29., up_h=2.6, up_top=8., up_peak=3.2, lo_h=2.4, lo_bot=10., lo_peak=4.5, groove=1.0, groove_w=.9, bow=.8, power=1.3)
def lips_op(x, y, z, L=None):
    """clean lip volume (mm, face frame) added on a smoothed mouth: upper-lip bulge with a slight bow, lower-lip roll, soft seam groove"""
    L = {**LIPS, **(L or {})}
    ax = np.abs(x); u = np.clip(ax / L['W'], 0, 1)
    f = np.clip(1 - u ** 2, 0, 1) ** L['power']
    ys = L['seam'] - L['corner_drop'] * u ** 2
    # upper lip: from the seam up to ys + up_top (higher at the bow peaks, x ~ 7 mm)
    top = ys + L['up_top'] + L['bow'] * np.exp(-((ax - 7) / 4.5) ** 2) - L['bow'] * np.exp(-(ax / 2.2) ** 2)
    t = np.clip((y - ys) / np.maximum(top - ys, 1e-3), 0, 1)
    upper = L['up_h'] * np.sin(np.pi * t) ** 1.2 * np.where((y > ys) & (y < top), 1, 0)
    upper = upper * (1 - np.clip((t - L['up_peak'] / L['up_top']) * 0, 0, 1))
    tl = np.clip((ys - y) / L['lo_bot'], 0, 1)
    lower = L['lo_h'] * np.sin(np.pi * tl) ** 1.0 * np.where((y < ys) & (y > ys - L['lo_bot']), 1, 0)
    groove = -L['groove'] * np.exp(-((y - ys) / L['groove_w']) ** 2) * np.sqrt(f)
    return z + (upper + lower) * f + groove
