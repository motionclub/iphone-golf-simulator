"""hole10_look: the hole-10 wall / crust / cone / UV helpers (POSTCARD_LOOK continue, round 3). Imported by hole10_build.py and by the stage gates.

Library basalt builders only (postcard_props_lib, registered at run time; the lib files are never edited), deterministic seeds.

    register_kinds()               ROCK_WALL_BASALT_N1..N3 / F1..F3: terraced ("ragged") columnar wall segments built from the library's own hex-column primitive
    author_uv(me, rnd, ...)        Basalt_E-aware UV windows: every side face of a column shows one slice of the texture, so the glow sits IN a joint (the face
                                   edge) or the face is glow-free; tops sample glow-free slices; long vertical streaks (low v density)
    uv_variants(kinds, rnd)        4 UV-window clones of each library mesh
    near_wall / far_ring           the crater wall (near terraced wall + the 295-355 yd ring of the brief)
    crust_field(...)               round 3: the cooled crust that covers the crater floor, cut by winding lava rivers (hex-plate chunks ROCK_CRUST_nn)
    build_cone(...)                DRESS_CONE with glowing lava flows down its flanks and a molten summit (LK_BASALT + LK_LAVA faces)

Why (reviewer round 2): the wall read as a brown field of orange dashes ('rain'), a flat barcode skyline; the floor was a 45-50 % open orange lake with
floating black rectangles; the volcano was a brown hatched mass without glow.
"""
import math
import random

import numpy as np
import bpy
from mathutils import Vector
from mathutils import noise as mnoise

import postcard_lib as P
import postcard_props_lib as PL

MIN_SCALE = 0.58                            # library instances never go below this x their jitter (>= 0.55): the no-stretch gate's 0.5 limit with margin for the FBX float round trip
MAX_SCALE = 1.9                             # x a +-3 % jitter stays under the gate's 2.0
TEE_XY = (0.0, 0.0)
WINDOW = (-10.0, 40.0)            # headings from the tee (deg from +D toward +X) where the walls are kept low so the volcano and its smoke show above them
NEAR_WINDOW_H = (13.0, 18.0)      # m above the lava, near wall inside the window
FAR_WINDOW_H = (15.0, 23.0)       # far ring inside the window
NEAR_R_MIN_YD = 214.0             # the near wall never comes closer to the crater centre than this ...
NEAR_SHORE_GAP_YD = 30.0          # ... nor closer than this to the farthest shore point of its heading
NEAR_STACK_GAP_M = 16.0           # radial clearance to a stack's base (a stack is never inside the wall)
NEAR_ROW_GAP_M = 9.5              # second row, further out
N_VARIANTS = 4                    # UV-window clones per wall kind
FAR_SPIRES = 7                    # tall spire segments (scale up to 1.9, ~80 m) breaking the far skyline
YD = 0.9144

# natural wall segments (library hex-column primitive, registered at run time): kind, length, depth, height, col_r, seed, front_ratio, broken, low_mid, terraces per height
NEAR_KINDS = (("ROCK_WALL_BASALT_N1", 22.0, 7.0, 24.0, 1.7, 31, 0.50, 0.14, 0.0, 10.0),
              ("ROCK_WALL_BASALT_N2", 26.0, 8.0, 28.0, 2.0, 32, 0.45, 0.16, 0.20, 10.0),
              ("ROCK_WALL_BASALT_N3", 18.0, 6.0, 20.0, 1.5, 33, 0.55, 0.14, 0.0, 9.0),
              ("ROCK_WALL_BASALT_F1", 40.0, 12.0, 44.0, 2.6, 61, 0.55, 0.12, 0.0, 12.0),
              ("ROCK_WALL_BASALT_F2", 36.0, 11.0, 40.0, 2.4, 62, 0.60, 0.14, 0.12, 12.0),
              ("ROCK_WALL_BASALT_F3", 30.0, 10.0, 34.0, 2.2, 63, 0.50, 0.12, 0.0, 11.0))
FAR_ROWS = ((0.45, (34.0, 50.0), 1.0, 1.0), (1.0, (46.0, 62.0), 1.0, 0.95))      # (t, heights m above lava, share of segments, spacing x width)


# ----------------------------------------------------------------------------- ragged (terraced) wall segments from the library's hex-column primitive
def ragged_wall(kind, length, depth, height, col_r, seed, front_ratio, broken, low_mid, terr, bury=6.0, end_drop=0.12, max_faces=500):
    """Like postcard_props_lib.build_basalt_wall (same hex-column primitive, same lattice, same <= 500 faces) but the skyline is TERRACED: heights follow a
    low-frequency noise (+-10 %) plus a few % per column (neighbouring columns differ by 1-2 m: a stair-step slope, not a fence of equal posts), broken
    groups drop by 10 %, tops are tilted up to 0.42 rad and chipped two times in three: ragged crags, not flat-topped skyscrapers (round 2 read as a city)."""
    rng = random.Random(seed * 6151 + 29)
    cs = PL._hex_lattice(col_r, -length / 2, -depth / 2, length / 2, depth / 2, rng, rows_x=True)
    cs.sort(key=lambda p: (abs(p[0]) / length + 0.3 * rng.random()))
    mb = PL._MB(("LK_BASALT",))
    q = height / terr
    for x, y in cs:
        if len(mb.F) + 10 > max_faces:
            break
        fy = (y + depth / 2) / depth
        h = height * (front_ratio + (1 - front_ratio) * fy)
        h *= 1.0 + 0.10 * mnoise.noise(Vector((x / (length * 0.30) + seed * 3.7, fy * 0.8, 0.5)))
        ex = abs(x) / (length / 2)
        if ex > 0.7:
            h *= 1.0 - end_drop * min(1.0, (ex - 0.7) / 0.3) ** 1.5
        if low_mid > 0:
            h *= 1.0 - low_mid * math.exp(-((x / (length * 0.22)) ** 2))
        if mnoise.noise(Vector((x / (col_r * 3.0) + seed * 1.3, y / (col_r * 3.0), 2.5))) > 0.55 - broken:
            h *= 0.90
        h = max(1.5 * q, h * (1.0 + rng.uniform(-0.035, 0.035)))
        PL._hex_column(mb, rng, x, y, h, -bury, col_r, tilt_max=0.42, chip_p=0.65, a_off=math.pi / 6)
    return PL._finalize(kind, mb, "box", smooth_angle=None)


def register_kinds():
    for kind, ln, dp, ht, cr, seed, fr, br, lm, terr in NEAR_KINDS:
        PL.BUILDERS[kind] = (lambda kind=kind, ln=ln, dp=dp, ht=ht, cr=cr, seed=seed, fr=fr, br=br, lm=lm, terr=terr:
                             ragged_wall(kind, ln, dp, ht, cr, seed, fr, br, lm, terr))


# ----------------------------------------------------------------------------- UV windows (Basalt_C / Basalt_E aware)
# Basalt_E (8 m tile, u around, v = height): glow only in vertical joint lines at u = GLOW_U (each 0.014 wide, 37-59 % of the height in dashes). A column face
# is mapped to ONE slice of the tile: a "glow" slice starts (or ends) exactly on a glow line, so the glow runs along the face EDGE, i.e. in the joint between
# two columns; every other face takes a slice from a glow-free zone. Tops take glow-free slices too. The v density is low (tall streaks, 1.4-5 m dashes in
# the world, not 0.5-1.5 m rain). All numbers measured from Basalt_E.png (work/postcard-look/v2/hole10/r3/basalt_e_profile.py).
GLOW_U = (0.123, 0.446, 0.534, 0.718, 0.806, 0.930)
GLOW_EDGE = 0.016
ZONES = ((0.141, 0.211), (0.225, 0.350), (0.364, 0.435), (0.460, 0.525), (0.547, 0.705), (0.730, 0.795), (0.820, 0.920), (0.940, 1.110))
ZONE_W = np.array([b - a for a, b in ZONES])
ZONE_LUM = (0.194, 0.149, 0.151, 0.192, 0.172, 0.129, 0.122, 0.124)    # mean Basalt_C luminance of each slice (measured, texture mean 0.143): slices are drawn with weight (0.14 / lum)^3 so the walls come out darker, not lighter, than the texture average
ZONE_P = [(0.14 / l) ** 3 for l in ZONE_LUM]


def pick_zone(rnd, ok):
    w = [ZONE_P[k] for k in ok]
    r = rnd.random() * sum(w)
    for k, wk in zip(ok, w):
        r -= wk
        if r <= 0:
            return k
    return ok[-1]
TILE = 8.0                                  # LK_BASALT contract tile (m)
CONE_UV = 0.42                              # the volcano's basalt UV density x the 8 m tile (UV_DENSITY gate: >= 1/3): bigger, sparser strata and dashes


def _polys(me):
    nl = len(me.loops)
    vidx = np.empty(nl, np.int64)
    me.loops.foreach_get("vertex_index", vidx)
    ls = np.empty(len(me.polygons), np.int64)
    lt = np.empty(len(me.polygons), np.int64)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", co)
    return vidx, ls, lt, co.reshape(-1, 3)


def _newell(pts):
    n = np.zeros(3)
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        n[0] += (a[1] - b[1]) * (a[2] + b[2])
        n[1] += (a[2] - b[2]) * (a[0] + b[0])
        n[2] += (a[0] - b[0]) * (a[1] + b[1])
    ln = float(np.linalg.norm(n))
    return n / ln if ln > 1e-12 else np.array([0.0, 0.0, 1.0])


def author_uv(me, rnd, uf=0.62, vf=0.42, p_glow=0.30, top_vf=0.60, slot=None):
    """Rewrite UV0 of a mesh (object space metres): see the section comment. uf / vf = u / v density x the 8 m tile (the UV_DENSITY gate wants the
    geometric mean in 1/3..3 and the anisotropy <= 4:1), p_glow = share of side faces whose window carries a glow line at its edge. slot = only polygons of
    that material slot (None = all). Returns dict(side, glow, top, top_glow_free) counters. The tangent frame stays right-handed (u = z x n for sides,
    u = +x / v = +y for tops), so the normal map is not mirrored."""
    vidx, ls, lt, co = _polys(me)
    lay = me.uv_layers.active or me.uv_layers.new(name="UVMap")
    nl = len(me.loops)
    try:
        uv = np.empty(nl * 2, np.float64)
        lay.uv.foreach_get("vector", uv)
        uv = uv.reshape(-1, 2)
    except Exception:
        uv = np.zeros((nl, 2))
    mi = np.zeros(len(me.polygons), np.int32)
    me.polygons.foreach_get("material_index", mi)
    st = dict(side=0, glow=0, top=0, top_glow_free=0)
    for pi in range(len(me.polygons)):
        if slot is not None and mi[pi] != slot:
            continue
        l0, n = int(ls[pi]), int(lt[pi])
        pts = co[vidx[l0:l0 + n]]
        nrm = _newell(pts)
        if abs(nrm[2]) >= 0.80:                                             # a TOP (chamfers and chips are steep enough to count as sides): a glow-free slice, v long, u compressed to the zone
            c = pts.mean(0)
            d = pts - c
            rx = max(float(np.abs(d[:, 0]).max()), 0.05)
            ok = [k for k in range(len(ZONES)) if ZONE_W[k] >= (0.150 if rx > 2.2 else 0.060)]        # big tops take the widest glow-free zones
            k = pick_zone(rnd, ok)
            lo, hi = ZONES[k]
            zw = hi - lo
            du = min(uf / TILE, 0.9 * zw / (2.0 * rx))
            zc = 0.5 * (lo + hi)
            uv[l0:l0 + n, 0] = zc + d[:, 0] * du
            uv[l0:l0 + n, 1] = rnd.random() + d[:, 1] * min(top_vf / TILE, 3.0 * du)         # anisotropy <= 3:1
            st["top"] += 1
            st["top_glow_free"] += 1
            continue
        h = np.array([nrm[0], nrm[1], 0.0])
        hl = float(np.linalg.norm(h))
        h = h / hl if hl > 1e-9 else np.array([1.0, 0.0, 0.0])
        t = np.array([-h[1], h[0], 0.0])                                    # z x h
        s = pts @ t
        w = max(float(s.max() - s.min()), 0.05)
        su = w * uf / TILE
        glow = rnd.random() < p_glow
        if glow:
            g = GLOW_U[int(rnd.random() * len(GLOW_U)) % len(GLOW_U)]
            u0 = g - GLOW_EDGE if rnd.random() < 0.5 else g + GLOW_EDGE - su
            su_eff = su
        else:
            ok = [k for k in range(len(ZONES)) if ZONE_W[k] >= su * 1.03]
            if ok:
                k = pick_zone(rnd, ok)
                su_eff = su
            else:
                k = int(np.argmax(ZONE_W))
                su_eff = 0.96 * float(ZONE_W[k])
            lo, hi = ZONES[k]
            u0 = lo + rnd.random() * max(hi - lo - su_eff, 0.0)
        uv[l0:l0 + n, 0] = u0 + (s - s.min()) / w * su_eff
        uv[l0:l0 + n, 1] = pts[:, 2] * (vf / TILE) + rnd.random()
        st["side"] += 1
        st["glow"] += 1 if glow else 0
    try:
        lay.uv.foreach_set("vector", uv.ravel())
    except Exception:
        lay.data.foreach_set("uv", uv.ravel())
    me.update()
    return st


UV_STATS = {}                                # variant kind -> counters written by author_uv (read by the build's gate)
UV_PARAMS = ((0.62, 0.36), (0.70, 0.32), (0.58, 0.38), (0.66, 0.34), (0.60, 0.36))


def uv_variants(kinds, rnd, p_glow=0.30):
    """{kind: [variant kinds]}: clones of the library meshes with their UVs authored by author_uv (own random windows, own density factors inside the
    UV_DENSITY gate's 1/3..3 x). Same shape, same materials, no mirroring."""
    out = {}
    for kind in kinds:
        src = PL.library_object(kind)
        vs = []
        for k in range(N_VARIANTS):
            vk = f"{kind}_V{k + 1}"
            me = src.data.copy()
            me.name = vk
            me["lk_kind"] = vk
            uf, vf = UV_PARAMS[(k + len(vs) + len(out)) % len(UV_PARAMS)]
            UV_STATS[vk] = dict(author_uv(me, rnd, uf=uf, vf=vf, p_glow=p_glow), uf=uf, vf=vf)
            ob = bpy.data.objects.new(vk, me)
            PL._lib_collection().objects.link(ob)
            ob.hide_viewport = ob.hide_render = True
            vs.append(vk)
        out[kind] = vs
    return out


_BAGS = {}


def pick_variant(kinds_var, kind, rnd):
    """Next UV variant of `kind` from a shuffled bag (every variant is used once before any is used twice: a balanced, deterministic spread)."""
    bag = _BAGS.get(kind)
    if not bag:
        bag = list(kinds_var[kind])
        rnd.shuffle(bag)
        _BAGS[kind] = bag
    return bag.pop()


def macro(theta, phases, amps=(0.26, 0.20, 0.15, 0.10, 0.06), ks=(2, 3, 5, 8, 13)):
    """Low-frequency height multiplier along the ring (1 +- ~0.55): ridges and saddles instead of one level fence. Clipped to [0.55, 1.45]."""
    m = 1.0 + sum(a * math.sin(k * theta + p) for a, k, p in zip(amps, ks, phases))
    return min(1.45, max(0.55, m))


def heading_from_tee(x, y):
    return math.degrees(math.atan2(x - TEE_XY[0], y - TEE_XY[1]))


def near_radius_profile(D, W, n=720):
    """R(theta) (m from the crater centre) of the near wall's front row: max(R_MIN, farthest shore point of the heading + gap, a pushed-out bay round each
    stack), made an upper envelope (max-filter) and then box-smoothed with a window not larger than the max-filter's, so the smoothed value never drops
    below a constraint."""
    cx, cy = P.m(W["cx"], W["cd"])
    th = np.linspace(0.0, 2 * math.pi, n, endpoint=False)
    con = np.full(n, NEAR_R_MIN_YD * P.YD)
    for x, d in D.SHORE:
        px, py = P.m(x, d)
        a = math.atan2(py - cy, px - cx) % (2 * math.pi)
        r = math.hypot(px - cx, py - cy) + NEAR_SHORE_GAP_YD * P.YD
        i0 = int(round(a / (2 * math.pi) * n))
        for k in range(-24, 25):
            j = (i0 + k) % n
            con[j] = max(con[j], r)
    for s in D.scenery["stacks"]:
        px, py = P.m(s["x"], s["d"])
        a = math.atan2(py - cy, px - cx) % (2 * math.pi)
        dist = math.hypot(px - cx, py - cy)
        rad = s["r"] * P.YD + 8.0                                          # base radius + the satellites standing beside the main piece
        for j in range(n):
            lat = abs((th[j] - a + math.pi) % (2 * math.pi) - math.pi) * dist
            if lat < rad + 60.0:
                con[j] = max(con[j], dist + rad + NEAR_STACK_GAP_M - 0.55 * max(0.0, lat - rad - 6.0))
    w_max, w_box = 30, 24
    pad = np.concatenate([con[-w_max:], con, con[:w_max]])
    mx = np.array([pad[i:i + 2 * w_max + 1].max() for i in range(n)])
    pad2 = np.concatenate([mx[-w_box:], mx, mx[:w_box]])
    ker = np.ones(2 * w_box + 1) / (2 * w_box + 1)
    sm = np.convolve(pad2, ker, mode="valid")[:n]
    sm = np.maximum(sm, con)                                              # numerical safety (never below a constraint)
    return th, sm


NEAR_ROWS = ((0.0, (26.0, 40.0), 0.06), (NEAR_ROW_GAP_M, (36.0, 52.0), 0.0))     # (radial offset m, heights m above the lava, gap share)


def near_wall(D, W, kinds_var):
    """Two terraced rows of tangent library wall segments (ROCK_WALL_BASALT_N* / F2 / F3) round the crater, continuous (the second row behind the first, 6 % gaps in the
    front row only), heights = macro(theta) x (row range), low inside the tee shot's window. Returns the instances."""
    rnd = random.Random(1020)
    cx, cy = P.m(W["cx"], W["cd"])
    th_p, R_p = near_radius_profile(D, W)
    phases = [rnd.uniform(0, math.tau) for _ in range(5)]
    kinds = ["ROCK_WALL_BASALT_N1", "ROCK_WALL_BASALT_N2", "ROCK_WALL_BASALT_N3", "ROCK_WALL_BASALT_F2", "ROCK_WALL_BASALT_F3"]
    dims = {}
    for k in kinds:
        lo, hi = PL.lib_bbox(k)
        dims[k] = (float(hi.x - lo.x), float(hi.y - lo.y), float(hi.z))
    out = []
    for ri, (dr, (hlo, hhi), gap) in enumerate(NEAR_ROWS):
        th = rnd.uniform(0.0, 0.3) + ri * 0.11
        th_end = th + 2 * math.pi
        while th < th_end:
            Rm = float(np.interp(th % (2 * math.pi), th_p, R_p, period=2 * math.pi)) + dr + rnd.uniform(-1.2, 1.2)
            h = min(58.0, 0.5 * (hlo + hhi) * rnd.uniform(0.93, 1.07) * macro(th, phases))
            kind = kinds[rnd.randrange(len(kinds))]
            xl, yl, zt = dims[kind]
            tc = th + 0.5 * (xl * 0.7) / Rm
            hd = heading_from_tee(cx + Rm * math.cos(tc), cy + Rm * math.sin(tc))
            if WINDOW[0] <= hd <= WINDOW[1]:
                h = min(h, rnd.uniform(*NEAR_WINDOW_H))
            s = min(1.7, max(MIN_SCALE, h / zt))
            width = xl * s
            dth = width * 0.93 / Rm
            if rnd.random() < gap:
                th += dth
                continue
            tc = th + 0.5 * dth
            Rm2 = float(np.interp(tc % (2 * math.pi), th_p, R_p)) + dr
            vk = pick_variant(kinds_var, kind, rnd)
            yaw = tc - math.pi / 2 + rnd.uniform(-0.05, 0.05)
            sc3 = (s * rnd.uniform(0.97, 1.03), s * rnd.uniform(0.97, 1.03), s)
            out.append(PL.place(D, vk, (cx + Rm2 * math.cos(tc), cy + Rm2 * math.sin(tc), 0.0), yaw=yaw, scale=sc3))
            th += dth
    return out, th_p, R_p


def far_ring(D, W, kinds_var):
    """The 295-355 yd ring (brief), two rows: a middle row (34-50 m) and a tall outer row (46-62 m), uniform scales (a few % jitter), a macro skyline (ridges and
    saddles), a handful of spire segments, a low window in the tee shot's headings. Segments are the terraced F1 / F2 / F3 kinds."""
    rnd = random.Random(1010)
    cx, cy = P.m(W["cx"], W["cd"])
    r0, r1 = W["r_inner"] * P.YD, W["r_outer"] * P.YD
    phases = [rnd.uniform(0, math.tau) for _ in range(5)]
    seg_kinds = ("ROCK_WALL_BASALT_F1", "ROCK_WALL_BASALT_F2", "ROCK_WALL_BASALT_F3")
    dims = {}
    for k in seg_kinds:
        lo, hi = PL.lib_bbox(k)
        dims[k] = (float(hi.x - lo.x), float(hi.y - lo.y), float(hi.z))
    out = []
    spire_at = sorted(rnd.uniform(0.0, 2 * math.pi) for _ in range(FAR_SPIRES))
    for k_row, (t, (hlo, hhi), seg_share, spacing) in enumerate(FAR_ROWS):
        r = r0 + (r1 - r0) * t
        th = rnd.uniform(0.0, 0.2) + k_row * 0.07
        th_end = th + 2 * math.pi
        while th < th_end:
            rr = r + rnd.uniform(-6.0, 6.0)
            h = 0.5 * (hlo + hhi) * rnd.uniform(0.93, 1.07) * macro(th * 1.0 + 0.9 * k_row, phases)
            hd = heading_from_tee(cx + rr * math.cos(th + 0.5 * 34.0 / rr), cy + rr * math.sin(th + 0.5 * 34.0 / rr))
            in_window = WINDOW[0] <= hd <= WINDOW[1]
            if in_window:
                h = min(h, rnd.uniform(*FAR_WINDOW_H))
            spire = (k_row == 1 and not in_window and any(0.0 <= (a - th) % (2 * math.pi) < 0.05 for a in spire_at))
            if spire:
                kind, h = "ROCK_WALL_BASALT_F1", rnd.uniform(68.0, 74.0)
                s = min(1.9, h / dims[kind][2])
                yaw = rnd.uniform(0, math.tau)
                sc3 = (s * rnd.uniform(0.97, 1.03), s * rnd.uniform(0.97, 1.03), s)
                width = dims[kind][0] * s
            else:
                kind = "ROCK_WALL_BASALT_F3" if in_window else seg_kinds[rnd.randrange(3)]
                xl, yl, zt = dims[kind]
                s = min(1.9, max(MIN_SCALE, h / zt))
                yaw = th - math.pi / 2 + rnd.uniform(-0.08, 0.08)
                sc3 = (s * rnd.uniform(0.96, 1.04), s * rnd.uniform(0.96, 1.04), s)
                width = xl * s * 0.92
            dth = width * 0.95 * spacing / rr
            if rnd.random() < 0.05 and not spire:
                th += dth
                continue
            tc = th + 0.5 * dth
            vk = pick_variant(kinds_var, kind, rnd)
            out.append(PL.place(D, vk, (cx + rr * math.cos(tc), cy + rr * math.sin(tc), 0.0), yaw=yaw, scale=sc3))
            th += dth
    return out


def seg_dist(px, py, ax, ay, bx, by):
    abx, aby = bx - ax, by - ay
    t = np.clip(((px - ax) * abx + (py - ay) * aby) / max(abx * abx + aby * aby, 1e-9), 0.0, 1.0)
    return np.hypot(px - (ax + t * abx), py - (ay + t * aby))


# ----------------------------------------------------------------------------- the crust that covers the crater floor
CRUST_COL_R = 4.3                 # hex plate circumradius (m): plates ~6 m across
CRUST_SHORE_GAP_M = 24.0 * YD     # the keep-outs of round 2's H_MESAS, unchanged: 24 yd off every play surface,
CRUST_LINE_GAP_M = 38.0 * YD      # 38 yd off the line of play (the centerline polyline incl. the carry), 
CRUST_CHORD_GAP_M = 25.0 * YD     # 25 yd off the tee -> C chord (the corner-cutting line)
CRUST_STACK_GAP_M = 6.0           # a lava ring round every basalt stack
CRUST_TOP = (1.4, 3.6)            # plate tops, m above the lava (every sight line is above the 6 m play height: nothing here can cut one)
CRUST_TOP_MAX = 5.0               # highest vertex of any crust chunk incl. tilt and stumps (the sight lines are all above 6.5 m)
CRUST_BOTTOM = -4.0
CRUST_CELL_M = 44.0               # chunk grid (meshes of >= 14 plates, >= 100 faces)
CRUST_MIN_PLATES = 14
CRUST_MAX_FACES = 480             # props <= 500 faces each (PROP_FACE_BUDGET)
LIGHT_RULE_M = 25.0 * YD + 0.4    # a ROCK_ piece within 25 yd of a lava light may not be wider than 24 yd: crust chunks never come that close


def crust_plan(D, W, near_th, near_R, stacks_xy, lights, seed=1060):
    """Candidate plates [(x, y, h)] (world metres): a jittered hex lattice kept where the clearances hold, cut by winding rivers (zero crossings of a Perlin field)
    and lakes, heights = smooth noise quantised to 0.5 m terraces + a rising shelf along the wall foot."""
    rnd = random.Random(seed)
    cx, cy = P.m(W["cx"], W["cd"])
    cl = [P.m(*p) for p in D.CENTERLINE]
    R = 215.0 * YD
    cs = PL._hex_lattice(CRUST_COL_R, -R, -R, R, R, rnd, jitter=0.04, rows_x=True)
    xs = np.array([c[0] + cx for c in cs])
    ys = np.array([c[1] + cy for c in cs])
    rho = np.hypot(xs - cx, ys - cy)
    th = np.arctan2(ys - cy, xs - cx) % (2 * math.pi)
    rwall = np.interp(th, near_th, near_R, period=2 * math.pi)
    keep = rho + CRUST_COL_R + 5.0 < rwall
    sd = P.signed_dist_m(D, xs, ys)
    keep &= sd >= CRUST_SHORE_GAP_M + CRUST_COL_R
    dl = np.min([seg_dist(xs, ys, *cl[i], *cl[i + 1]) for i in range(len(cl) - 1)], axis=0)
    keep &= dl >= CRUST_LINE_GAP_M + CRUST_COL_R
    keep &= seg_dist(xs, ys, *cl[0], *cl[3]) >= CRUST_CHORD_GAP_M + CRUST_COL_R
    for sx, sy, sr in stacks_xy:
        keep &= np.hypot(xs - sx, ys - sy) >= sr + CRUST_STACK_GAP_M + CRUST_COL_R
    for lx, ly in lights:
        keep &= np.hypot(xs - lx, ys - ly) >= LIGHT_RULE_M + 8.0 + CRUST_COL_R
    riv = np.array([abs(mnoise.noise(Vector((x / 52.0 + 11.3, y / 52.0 + 7.1, 0.3)))) for x, y in zip(xs, ys)])
    riv2 = np.array([abs(mnoise.noise(Vector((x / 29.0 + 3.7, y / 29.0 + 19.2, 1.1)))) for x, y in zip(xs, ys)])
    lake = np.array([mnoise.noise(Vector((x / 41.0 - 5.5, y / 41.0 + 2.2, 2.7))) for x, y in zip(xs, ys)])
    keep &= (riv > 0.026) & (riv2 > 0.016) & (lake < 0.95)
    hn = np.array([0.5 + 0.5 * mnoise.noise(Vector((x / 47.0 + 1.9, y / 47.0 - 8.4, 0.9))) for x, y in zip(xs, ys)])
    h = CRUST_TOP[0] + (CRUST_TOP[1] - CRUST_TOP[0]) * 0.75 * hn
    h = np.round(h / 0.5) * 0.5
    shelf = np.clip((rho - (rwall - 46.0)) / 46.0, 0.0, 1.0)                  # the last 46 m before the wall rise to the wall foot
    h = np.minimum(CRUST_TOP[1], h + 1.6 * shelf)
    rr = np.array([rnd.uniform(-0.06, 0.06) for _ in xs])
    idx = np.nonzero(keep)[0]
    return [(float(xs[i]), float(ys[i]), float(h[i] + rr[i])) for i in idx], (cx, cy)


def crust_field(D, W, kinds_var_unused, near_th, near_R, stacks_xy, lights, rnd_uv):
    """The crust: hex plates (the library hex-column primitive, tops tilted <= 0.12 rad, most chipped) plus small basalt stumps standing on some of them, grouped into
    ROCK_CRUST_nn meshes of 100..480 faces (the props' 500-face budget) inside 44 m cells (six passes on shifted grids so fragments of one grid join the next, a group that
    comes out over 480 faces is split at its median); chunks closer than 25 yd to a lava light are dropped (H_ROCK_CHUNKING), chunks of < 100 faces too (ROCK_NOT_ICOSAHEDRON).
    UVs authored with author_uv (glow in the joints, glow-free tops). Returns (objects, plates kept, plates planned)."""
    plan, (cx, cy) = crust_plan(D, W, near_th, near_R, stacks_xy, lights)
    rng = random.Random(1061)
    left = list(plan)
    out, kept = [], 0
    drop = dict(light=0, faces=0)

    def build(cols):
        mb = PL._MB(("LK_BASALT",))
        for x, y, h in cols:
            PL._hex_column(mb, rng, x, y, h, CRUST_BOTTOM, CRUST_COL_R, gap=0.06, tilt_max=0.12, chip_p=0.7, a_off=math.pi / 6)
        for x, y, h in rng.sample(cols, max(3, len(cols) // 5)):                       # stumps: small broken columns standing on a plate
            a_ = rng.uniform(0, math.tau)
            r_ = rng.uniform(0.0, 0.35) * CRUST_COL_R
            hh = rng.uniform(0.6, 1.4)
            PL._hex_column(mb, rng, x + r_ * math.cos(a_), y + r_ * math.sin(a_), min(h + hh, 4.3), h - 0.4, rng.uniform(0.9, 1.5), gap=0.08, tilt_max=0.25, chip_p=0.6, a_off=rng.uniform(0, 1.0))
        return mb

    def emit(cols):
        """-> list of (mb, cols) chunks of <= 480 faces (split at the median of the longer axis while over)."""
        mb = build(cols)
        if len(mb.F) <= CRUST_MAX_FACES:
            return [(mb, cols)]
        xs = [c[0] for c in cols]
        ys = [c[1] for c in cols]
        k = 0 if (max(xs) - min(xs)) >= (max(ys) - min(ys)) else 1
        srt = sorted(cols, key=lambda c: c[k])
        half = len(srt) // 2
        return emit(srt[:half]) + emit(srt[half:])

    for off in ((0.0, 0.0), (0.5, 0.0), (0.0, 0.5), (0.5, 0.5), (0.25, 0.25), (0.75, 0.75)):
        cells = {}
        for x, y, h in left:
            cells.setdefault((int(math.floor(x / CRUST_CELL_M + off[0])), int(math.floor(y / CRUST_CELL_M + off[1]))), []).append((x, y, h))
        used = set()
        for key in sorted(cells):
            if len(cells[key]) < CRUST_MIN_PLATES:
                continue
            for mb, cols in emit(cells[key]):
                xs = [v[0] for v in mb.V]
                ys = [v[1] for v in mb.V]
                lo, hi = (min(xs), min(ys)), (max(xs), max(ys))
                near_light = False
                for lx, ly in lights:
                    dx = max(lo[0] - lx, 0.0, lx - hi[0])
                    dy = max(lo[1] - ly, 0.0, ly - hi[1])
                    if dx * dx + dy * dy <= LIGHT_RULE_M ** 2:
                        near_light = True
                if near_light or len(mb.F) < 100:
                    drop["light" if near_light else "faces"] += len(cols)
                    continue
                name = f"ROCK_CRUST_{len(out):02d}"
                me = PL._finalize(name, mb, "box", smooth_angle=None, library=False)
                UV_STATS[name] = dict(author_uv(me, rnd_uv, uf=0.72, vf=0.48, p_glow=0.42), uf=0.72, vf=0.48)
                ob = bpy.data.objects.new(name, me)
                PL._collection_for(name).objects.link(ob)
                PL._parent(D, ob)
                out.append(ob)
                kept += len(cols)
                used.update((round(x, 3), round(y, 3)) for x, y, h in cols)
        left = [c for c in left if (round(c[0], 3), round(c[1], 3)) not in used]
    print(f"[hole10_look] crust: {len(plan)} plates planned, kept {kept} in {len(out)} chunks, dropped plates {drop}, left over {len(left)}", flush=True)
    return out, kept, len(plan)


# ----------------------------------------------------------------------------- the volcano: basalt strata with glowing lava flows and a molten crater
def build_cone(D, center, base_r=125.0, height=135.0, seed=1, name="DRESS_CONE", notch_deg=250.0, sides=72, bands=7, crater_frac=0.2,
               notch_depth=0.2, crater_depth=0.1, flows=5):
    """DRESS_CONE like the library's background cone (chunky strata: a steep step + a gentler slope per band, never undercut, a V-notch in the crater rim, a crater dish),
    but with `sides` = 72 and `flows` winding strips of LK_LAVA faces from the crater rim to the foot (crater.jpg's volcano glows along its flanks) + a molten
    crater floor. Slot 0 = LK_BASALT (box UV at CONE_UV x the 8 m tile), slot 1 = LK_LAVA (planar UV at the 24 m tile). Visual only, no collider."""
    rng = random.Random(PL._seed_int("cone", seed, name))
    cx, cy, cz = center
    mb = PL._MB(("LK_BASALT",))                  # slot 1 (LK_LAVA, the look lib's material) is appended after _finalize: the props lib has no LK_LAVA spec
    notch = math.radians(notch_deg)
    angs = [math.tau * i / sides + rng.uniform(-0.25, 0.25) * math.tau / sides for i in range(sides)]
    rim_r = base_r * crater_frac
    rings = []
    prev = [float("inf")] * sides
    levels = []
    for b in range(bands):
        z0 = height * (b / bands)
        z1 = height * ((b + 1) / bands)
        levels.append((z0, 0, z0))
        levels.append((z0 + (z1 - z0) * rng.uniform(0.38, 0.5), 1, z0))
    levels.append((height, 2, height))
    jit = [[1.0 + rng.uniform(-0.11, 0.11) for _ in range(sides)] for _ in range(bands + 1)]
    prev_z = [-1e9] * sides
    for li, (z, kind, zband) in enumerate(levels):
        tz = z / height
        r_prof = rim_r + (base_r - rim_r) * (1.0 - tz) ** 1.6
        if kind == 1:
            r_prof = (rim_r + (base_r - rim_r) * (1.0 - zband / height) ** 1.6) * 0.95
        bidx = min(li // 2, bands)
        ring = []
        for i, a in enumerate(angs):
            r = r_prof * jit[bidx][i]
            r = min(r, prev[i])
            prev[i] = r
            zz = z
            da = math.atan2(math.sin(a - notch), math.cos(a - notch))
            if tz > 0.55:
                zz -= notch_depth * height * max(0.0, math.cos(da)) ** 6 * ((tz - 0.55) / 0.45) ** 1.2
            if kind == 2:
                zz += rng.uniform(-0.015, 0.015) * height
            zz = max(zz, prev_z[i] + 0.006 * height)
            prev_z[i] = zz
            ring.append(mb.v((cx + math.cos(a) * r, cy + math.sin(a) * r, cz + zz)))
        rings.append(ring)
    nlev = len(rings)
    # flows: each starts at a random angular index of the top ring and walks down (+-1 index per level with p 0.4), a strip of single lava quads; neighbouring flows never touch
    lava_cells = set()
    starts = sorted(rng.sample(range(sides), flows))
    for s0 in starts:
        i = s0
        for k in range(nlev - 2, -1, -1):                                  # from the top (last ring pair) to the foot
            lava_cells.add((k, i))
            if k > 0 and rng.random() < 0.4:
                i = (i + rng.choice((-1, 1))) % sides
                lava_cells.add((k, i))
    faces = []
    for k in range(nlev - 1):
        for i in range(sides):
            j = (i + 1) % sides
            lava = (k, i) in lava_cells
            faces.append(((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]), 1 if lava else 0))
    rim = rings[-1]
    inner = []
    floor_z = min(min(prev_z) - 0.03 * height, height * (1.0 - crater_depth))
    for i, a in enumerate(angs):
        inner.append(mb.v((cx + math.cos(a) * rim_r * 0.62, cy + math.sin(a) * rim_r * 0.62, cz + floor_z)))
    for i in range(sides):
        j = (i + 1) % sides
        faces.append(((rim[i], rim[j], inner[j], inner[i]), 1))            # the molten inner wall
    faces.append((tuple(inner), 1))
    for idx, slot in faces:
        mb.f(idx, 0)
    me = PL._finalize(name, mb, "box", smooth_angle=None, library=False)
    me.materials.append(bpy.data.materials["LK_LAVA"])
    me.polygons.foreach_set("material_index", np.array([slot for _, slot in faces], np.int32))
    me.update()
    # UV: basalt faces keep the world box UV at 0.45 x (a 40 m tile: the strata stay readable), lava faces a planar map (u along the slope's horizontal tangent, v up the slope) at the 24 m tile
    vidx, ls, lt, co = _polys(me)
    lay = me.uv_layers.active
    mi = np.zeros(len(me.polygons), np.int32)
    me.polygons.foreach_get("material_index", mi)
    uv = np.zeros((len(me.loops), 2))
    for pi in range(len(me.polygons)):
        l0, n = int(ls[pi]), int(lt[pi])
        pts = co[vidx[l0:l0 + n]]
        nrm = _newell(pts)
        if mi[pi] == 1:
            c = pts.mean(0)
            hh = np.array([nrm[0], nrm[1], 0.0])
            hl = float(np.linalg.norm(hh))
            if hl < 1e-6:
                t_, s_ = np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])
            else:
                hh /= hl
                t_ = np.array([-hh[1], hh[0], 0.0])
                s_ = np.cross(nrm, t_)
            uv[l0:l0 + n, 0] = (pts @ t_) / 24.0
            uv[l0:l0 + n, 1] = (pts @ s_) / 24.0
        else:
            if abs(nrm[2]) >= 0.5:
                uv[l0:l0 + n, 0] = pts[:, 0] * CONE_UV / TILE
                uv[l0:l0 + n, 1] = pts[:, 1] * CONE_UV / TILE
            else:
                hh = np.array([nrm[0], nrm[1], 0.0])
                hh /= max(float(np.linalg.norm(hh)), 1e-9)
                t_ = np.array([-hh[1], hh[0], 0.0])
                uv[l0:l0 + n, 0] = (pts @ t_) * CONE_UV / TILE
                uv[l0:l0 + n, 1] = pts[:, 2] * CONE_UV / TILE
    lay.uv.foreach_set("vector", uv.ravel())
    me.update()
    if bpy.data.objects.get(name) is not None:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    ob = bpy.data.objects.new(name, me)
    PL._collection_for("DRESS_CONE").objects.link(ob)
    PL._parent(D, ob)
    return ob
