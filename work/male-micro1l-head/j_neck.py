"""Micro1j neck edits: (A) Adam's apple rounded + throat hollow, (C) nape lump.  Position-only, zone z >= 1.40.
All numbers in mm inside the profile tables; y negative = front of the body."""
from j_edit import *

# ---- A: front neck centre-line target (z mm -> dy mm; +dy = move BACK, i.e. toward +y).  nodes are the cage rows (x ~ +-5.5 columns)
APPLE_NODES_Z = [1396.2, 1404.1, 1412.8, 1422.9, 1433.1, 1443.1, 1450.5, 1453.3]
APPLE_DY      = [0.0,    0.0,    0.1,    -0.7,   1.4,    1.6,    11.5,   0.0]


def lateral_plateau(ax, flat, zero):
    """1 for |x| <= flat, smooth to 0 at |x| >= zero"""
    return 1.0 - sstep(flat, zero, np.abs(ax))


def edit_apple(ctx, V, scale=1.0, flat=0.014, zero=0.040):
    V = V.copy(); x, y, z = V[:, 0], V[:, 1], V[:, 2]
    m = (y < -0.02) & (y > -0.1005) & (z >= 1.3995) & (z <= 1.4545) & (np.abs(x) < 0.050)
    dy = np.interp(z[m] * 1000, APPLE_NODES_Z, APPLE_DY)          # linear is fine: PCHIP below smooths per row via profile
    dy = interp_profile(APPLE_NODES_Z, APPLE_DY, z[m] * 1000)
    V[m, 1] += scale * dy * mm * lateral_plateau(x[m], flat, zero)
    return V, m


# ---- C: nape target (back, z mm -> dy mm; negative = move FORWARD toward the neck)
NAPE_NODES_Z = [1394.0, 1401.6, 1409.0, 1417.3, 1424.2, 1430.0, 1436.9, 1445.3, 1455.2, 1466.4]
NAPE_DY      = [0.0,    -0.6,   -1.8,   -2.8,   -3.0,   -2.4,   -1.4,   -0.5,   0.0,    0.0]


def edit_nape(ctx, V, scale=1.0, flat=0.025, zero=0.062):
    V = V.copy(); x, y, z = V[:, 0], V[:, 1], V[:, 2]
    m = (y > 0.0) & (z >= 1.3995) & (z <= 1.4665) & (np.abs(x) < 0.070)
    dy = interp_profile(NAPE_NODES_Z, NAPE_DY, z[m] * 1000)
    V[m, 1] += scale * dy * mm * lateral_plateau(x[m], flat, zero)
    return V, m


def fair_region(ctx, V, mask, iters=6, lam=0.5, mu=-0.53, hold=None):
    """Taubin fairing restricted to `mask` (weights 0/1, feathered by 2 ring neighbours); hold = bool array of vertices never smoothed"""
    w = mask.astype(float)
    for _ in range(2):                       # feather
        w = np.maximum(w, 0.5 * ctx.M.nbr_mean(w[:, None])[:, 0] * (w == 0))
    if hold is not None: w[hold] = 0.0
    w[~ctx.zone] = 0.0
    return ctx.M.taubin(V, w, iters=iters, lam=lam, mu=mu)


# ---- C2: nape v2 -- the plate's skin edge sits 1.1-2.2 mm in front of the mesh over the whole nape (silhouette incl. shirt) and the shirt hides 4-6 mm more below z 1.45:
#      pull the whole back of the neck forward (mm, negative = toward the front), feathering to 0 at the zone line and at the skull
NAPE2_NODES_Z = [1394.0, 1401.6, 1409.0, 1417.3, 1424.2, 1430.0, 1436.9, 1445.3, 1455.2, 1466.4, 1478.6, 1490.8, 1505.0, 1520.0]
NAPE2_DY      = [0.0,    -0.8,   -2.2,   -3.4,   -3.8,   -3.4,   -2.8,   -2.3,   -2.2,   -2.1,   -1.8,   -1.4,   -0.9,   0.0]


def edit_nape2(ctx, V, scale=1.0, flat=0.025, zero=0.062, zmax=1.5205, dys=None):
    V = V.copy(); x, y, z = V[:, 0], V[:, 1], V[:, 2]
    m = (y > 0.0) & (z >= 1.3995) & (z <= zmax) & (np.abs(x) < 0.070)
    dy = interp_profile(NAPE2_NODES_Z, NAPE2_DY if dys is None else dys, z[m] * 1000)
    V[m, 1] += scale * dy * mm * lateral_plateau(x[m], flat, zero)
    return V, m


def fair_disp(ctx, V, mask, iters=4, feather=2):
    """smooth the DISPLACEMENT field D = V - V0 inside `mask` (+feather rings): untouched geometry keeps D = 0 exactly; zone enforced"""
    D = V - ctx.V0
    w = mask.astype(float)
    for _ in range(feather):
        w = np.maximum(w, 0.5 * ctx.M.nbr_mean(w[:, None])[:, 0] * (w == 0))
    w[~ctx.zone] = 0.0
    for _ in range(iters):
        D = D + 0.5 * w[:, None] * (ctx.M.nbr_mean(D) - D)
    return ctx.V0 + D
