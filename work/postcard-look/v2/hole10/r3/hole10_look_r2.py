"""hole10_look: the hole-10 wall / mesa / UV-variant helpers (POSTCARD_LOOK continue, round 2). Imported by hole10_build.py and by the stage gates.

Library basalt only (postcard_props_lib builders, registered at run time; the lib files are never edited), uniform instance scales, deterministic seeds.

    register_near_kinds()          register ROCK_WALL_BASALT_N1..N3 (near-wall segments) and ROCK_BASALT_M1..M3 (crust mesas) with PL.BUILDERS
    uv_variants(kinds, rnd)        UV-phase clones of library meshes: per-variant density factor + shift and a random shift per hex column
    near_wall(D, W, kinds_var)     two terraced rows of tangent wall segments round the crater, 30 yd beyond the farthest shore point -> (instances, theta, R)
    far_ring(D, W, kinds_var)      the 295-355 yd ring: two rows of A / B / C segments with a macro skyline and spires
    crust_mesas(...)               low flat-topped column plateaus: a shelf along the wall foot (free half of the crater) and islands in the open lava

Why (reviewer round 1): the wall ring read as a flat brown skyline of boxy slabs with dotted ladders, and the aerial was 63-72 % open orange.
"""
import math
import random

import numpy as np
import bpy

import postcard_lib as P
import postcard_props_lib as PL

MIN_SCALE = 0.58                            # library instances never go below this x their jitter (>= 0.55): the no-stretch gate's 0.5 limit with margin for the FBX float round trip
MAX_SCALE = 1.9                             # x a +-3 % jitter stays under the gate's 2.0


# ----------------------------------------------------------------------------- crater wall: NEAR terraced wall + FAR ring (library basalt, uniform scales)
# Round 2 (reviewer: "flat-topped brown skyline of boxy slabs, dotted ladders, open lava 63-72 %"): the bowl is bounded by a NEAR wall of tangent
# basalt wall segments (continuous cliff, 2 terraced rows, 30 yd beyond the farthest shore point, pushed out round the stacks), the 295-355 yd
# ring is thinned to two rows and given a macro skyline (ridges, saddles, spires), and every wall kind is cloned into UV-shift variants so the glow
# lattice of the Basalt_E map is not the same on every piece (identical lattices read as a city of windows).
TEE_XY = (0.0, 0.0)
WINDOW = (-10.0, 40.0)            # headings from the tee (deg from +D toward +X) where the walls are kept low so the volcano and its smoke show above them
NEAR_WINDOW_H = (13.0, 18.0)      # m above the lava, near wall inside the window
FAR_WINDOW_H = (15.0, 23.0)       # far ring inside the window
NEAR_R_MIN_YD = 214.0             # the near wall never comes closer to the crater centre than this ...
NEAR_SHORE_GAP_YD = 30.0          # ... nor closer than this to the farthest shore point of its heading
NEAR_STACK_GAP_M = 16.0           # radial clearance to a stack's base (a stack is never inside the wall)
NEAR_ROW_GAP_M = 9.5              # second row, further out
N_VARIANTS = 4                    # UV-shift clones per wall kind
# natural wall segments of the near wall (library builder, registered at run time: kind, length, depth, height, col_r, seed, front_ratio, broken, low_mid)
NEAR_KINDS = (("ROCK_WALL_BASALT_N1", 22.0, 7.0, 24.0, 1.7, 31, 0.50, 0.08, 0.0),
              ("ROCK_WALL_BASALT_N2", 26.0, 8.0, 28.0, 2.0, 32, 0.45, 0.10, 0.20),
              ("ROCK_WALL_BASALT_N3", 18.0, 6.0, 20.0, 1.5, 33, 0.55, 0.08, 0.0),
              # far-ring segments: flat-topped terraces (almost no broken columns), the skyline steps BETWEEN segments (terraces tens of metres wide), not between columns
              ("ROCK_WALL_BASALT_F1", 40.0, 12.0, 44.0, 2.6, 61, 0.55, 0.03, 0.0),
              ("ROCK_WALL_BASALT_F2", 36.0, 11.0, 40.0, 2.4, 62, 0.60, 0.05, 0.12),
              ("ROCK_WALL_BASALT_F3", 30.0, 10.0, 34.0, 2.2, 63, 0.50, 0.04, 0.0))
# far ring rows
FAR_ROWS = ((0.45, (34.0, 50.0), 1.0, 1.0), (1.0, (46.0, 62.0), 1.0, 0.95))      # (t, heights m above lava, share of segments, spacing x width: > 1 = gaps between peaks)
# crust MESAS: low flat-topped hex-column plateaus (kind, rx, ry, height above the lava, col_r, seed, dome) = cooled basalt shelves along the wall foot and
# islands in the open lava: they replace open orange by dark rock (crater.jpg: lava pools between big black column plateaus). Tops stay <= ~6 m so no
# sight line (all >= the play height) can touch them, and they keep 28 yd off every play surface and 45 yd off the line of play.
MESA_KINDS = (("ROCK_BASALT_M1", 13.0, 11.0, 3.0, 2.9, 51, 0.10, 0.12),      # kind, rx, ry, height, col_r, seed, dome, var (per-column height spread): flat plateaus of big hex tops (>= 100 faces each: ROCK_NOT_ICOSAHEDRON)
              ("ROCK_BASALT_M2", 15.0, 11.0, 3.8, 3.3, 52, 0.15, 0.14),
              ("ROCK_BASALT_M3", 9.0, 8.0, 4.6, 2.2, 53, 0.30, 0.16))
MESA_SHORE_GAP_M = 28.0 * 0.9144
MESA_LINE_GAP_M = 45.0 * 0.9144
MESA_CHORD_GAP_M = 30.0 * 0.9144
FAR_SPIRES = 7                    # tall spire segments (scale up to 1.9, ~80 m) breaking the far skyline


def register_near_kinds():
    for kind, rx, ry, ht, cr, seed, dome, var in MESA_KINDS:
        PL.BUILDERS[kind] = (lambda kind=kind, rx=rx, ry=ry, ht=ht, cr=cr, seed=seed, dome=dome, var=var:
                             PL.build_basalt_cluster(kind, rx, ry, ht, cr, seed=seed, dome=dome, var=var, bury=3.0, tilt_max=0.12, chip_p=0.3, edge_noise=0.18))
    for kind, ln, dp, ht, cr, seed, fr, br, lm in NEAR_KINDS:
        PL.BUILDERS[kind] = (lambda kind=kind, ln=ln, dp=dp, ht=ht, cr=cr, seed=seed, fr=fr, br=br, lm=lm:
                             PL.build_basalt_wall(kind, ln, dp, ht, cr, seed=seed, front_ratio=fr, broken=br, low_mid=lm))


UV_VARIANT_SCALES = ((1.0, 1.0), (1.2, 0.85), (0.85, 1.15), (1.1, 1.0), (0.9, 0.9))


def mesh_components(me):
    """Polygon -> connected component id (shared vertices). Each hex column of a library basalt mesh is its own component (the builders never weld columns)."""
    n = len(me.vertices)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for p in me.polygons:
        v = p.vertices
        r0 = find(v[0])
        for k in range(1, len(v)):
            r1 = find(v[k])
            if r1 != r0:
                parent[r1] = r0
    return np.array([find(p.vertices[0]) for p in me.polygons])


UV_STATS = {}                                # variant kind -> dict(components, distinct, scale): what uv_variants wrote (read by the build's H_UV_PHASE gate)


def uv_variants(kinds, rnd):
    """{kind: [variant kinds]}: clones of the library meshes whose UV0 is re-phased: each variant has its own (u, v) density factor (within 0.85..1.2, the
    UV_DENSITY gate allows 0.45..2.2) and a global shift, and EVERY HEX COLUMN gets its own random shift (a column is a connected component and its
    outline is a hard edge anyway), so the Basalt_E glow lattice (regular dashes, the same on every column of every piece = 'windows and ladders') never
    repeats across neighbouring columns. Same shape, same materials, no mirroring (a mirrored UV would flip the normal map's tangent frame)."""
    out = {}
    for kind in kinds:
        src = PL.library_object(kind)
        comp = mesh_components(src.data)
        vs = []
        for k in range(N_VARIANTS):
            vk = f"{kind}_V{k + 1}"
            me = src.data.copy()
            me.name = vk
            me["lk_kind"] = vk
            lay = me.uv_layers.active
            uv = np.empty(len(me.loops) * 2, np.float64)
            try:
                lay.uv.foreach_get("vector", uv)
            except Exception:
                lay.data.foreach_get("uv", uv)
            uv = uv.reshape(-1, 2)
            su, sv = UV_VARIANT_SCALES[(k + len(vs)) % len(UV_VARIANT_SCALES)]
            uv = uv * np.array([su, sv]) + np.array([rnd.random(), rnd.random()])
            lt = np.empty(len(me.polygons), np.int32)
            ls = np.empty(len(me.polygons), np.int32)
            me.polygons.foreach_get("loop_total", lt)
            me.polygons.foreach_get("loop_start", ls)
            off = {}
            su_, sv_ = su, sv
            for pi in range(len(me.polygons)):
                c = int(comp[pi])
                if c not in off:
                    off[c] = (rnd.random(), rnd.random())
                uv[ls[pi]:ls[pi] + lt[pi]] += off[c]
            try:
                lay.uv.foreach_set("vector", uv.ravel())
            except Exception:
                lay.data.foreach_set("uv", uv.ravel())
            me.update()
            UV_STATS[vk] = dict(components=len(off), distinct=len({(round(a * 50) % 50, round(b * 50) % 50) for a, b in off.values()}), scale=(su_, sv_))
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


def macro(theta, phases, amps=(0.20, 0.17, 0.13, 0.09), ks=(2, 3, 5, 8)):
    """Low-frequency height multiplier along the ring (1 +- ~0.45), clipped to [0.70, 1.30]: ridges and saddles instead of one level fence."""
    m = 1.0 + sum(a * math.sin(k * theta + p) for a, k, p in zip(amps, ks, phases))
    return min(1.30, max(0.70, m))


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


def near_wall(D, W, kinds_var):
    """Two terraced rows of tangent library wall segments (ROCK_WALL_BASALT_N1..N3 + A / B / C at small scales) round the crater, continuous (the second row
    behind the first, 6 % gaps in the front row only), heights = macro(theta) x (row range), low inside the tee shot's window. Returns the instances."""
    rnd = random.Random(1020)
    cx, cy = P.m(W["cx"], W["cd"])
    th_p, R_p = near_radius_profile(D, W)
    phases = [rnd.uniform(0, math.tau) for _ in range(4)]
    kinds = ["ROCK_WALL_BASALT_N1", "ROCK_WALL_BASALT_N2", "ROCK_WALL_BASALT_N3", "ROCK_WALL_BASALT_F2", "ROCK_WALL_BASALT_F3"]
    dims = {}
    for k in kinds:
        lo, hi = PL.lib_bbox(k)
        dims[k] = (float(hi.x - lo.x), float(hi.y - lo.y), float(hi.z))
    rows = ((0.0, (20.0, 34.0), 0.06), (NEAR_ROW_GAP_M, (30.0, 46.0), 0.0))
    out = []
    for ri, (dr, (hlo, hhi), gap) in enumerate(rows):
        th = rnd.uniform(0.0, 0.3) + ri * 0.11
        th_end = th + 2 * math.pi
        while th < th_end:
            Rm = float(np.interp(th % (2 * math.pi), th_p, R_p, period=2 * math.pi)) + dr + rnd.uniform(-1.2, 1.2)
            h = rnd.uniform(hlo, hhi) * macro(th, phases)
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
    """The 295-355 yd ring (brief), two rows: a middle row (30-46 m: wall segments A / B / C and column PEAKS) and a tall outer row (44-66 m: peaks only),
    uniform scales (a few % jitter), a macro skyline (ridges and saddles), a handful of spire peaks, a low window in the tee shot's headings.
    Peaks (domed hex-column clusters: tall in the middle, falling off to the sides) replace the flat-topped S / M / L towers of round 1, which read as
    skyscrapers against the sky."""
    rnd = random.Random(1010)
    cx, cy = P.m(W["cx"], W["cd"])
    r0, r1 = W["r_inner"] * P.YD, W["r_outer"] * P.YD
    phases = [rnd.uniform(0, math.tau) for _ in range(4)]
    seg_kinds = ("ROCK_WALL_BASALT_F1", "ROCK_WALL_BASALT_F2", "ROCK_WALL_BASALT_F3")
    pk_kinds = ()
    dims = {}
    for k in seg_kinds + pk_kinds:
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
            h = rnd.uniform(hlo, hhi) * macro(th * 1.0 + 0.9 * k_row, phases)
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
            elif rnd.random() < seg_share:
                kind = "ROCK_WALL_BASALT_F3" if in_window else seg_kinds[rnd.randrange(3)]
                xl, yl, zt = dims[kind]
                s = min(1.9, max(MIN_SCALE, h / zt))
                yaw = th - math.pi / 2 + rnd.uniform(-0.08, 0.08)
                sc3 = (s * rnd.uniform(0.96, 1.04), s * rnd.uniform(0.96, 1.04), s)
                width = xl * s * 0.92
            else:
                kind = pk_kinds[rnd.randrange(3)]
                xl, yl, zt = dims[kind]
                s = min(1.5, max(MIN_SCALE, h / zt))
                yaw = rnd.uniform(0, math.tau)
                sc3 = (s * rnd.uniform(0.96, 1.04), s * rnd.uniform(0.96, 1.04), s)
                width = xl * s * 0.78
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


def crust_mesas(D, W, kinds_var, near_th, near_R, lights):
    """Low basalt column plateaus: a shelf along the foot of the near wall (rows 15 and 38 m in front of its first row, wherever the clearances allow it:
    only on the free half of the crater, the strip side keeps its lava) and islands in the open lava. Every candidate keeps >= 28 yd off every shore point
    (play surface), >= 45 yd off the centerline polyline, >= 30 yd off the tee -> C chord (the corner-cutting line), a stack's base + 10 m, 30 m off a lava light.
    Returns pseudo-stacks (dict(obs=[ob])) so the sight-line clearing treats them like the stacks (they are too low to cut any line anyway)."""
    rnd = random.Random(1040)
    cx, cy = P.m(W["cx"], W["cd"])
    cl = [P.m(*p) for p in D.CENTERLINE]
    chord = (cl[0], cl[3])
    stk = [(*P.m(s_["x"], s_["d"]), s_["r"] * P.YD + 10.0) for s_ in D.scenery["stacks"]]
    dims = {}
    for k in [m[0] for m in MESA_KINDS]:
        lo, hi = PL.lib_bbox(k)
        dims[k] = (float(hi.x - lo.x) / 2, float(hi.y - lo.y) / 2, float(hi.z))
    placed = []

    def ok(x, y, r, spacing=0.8):
        rho = math.hypot(x - cx, y - cy)
        th = math.atan2(y - cy, x - cx) % (2 * math.pi)
        if rho + r > float(np.interp(th, near_th, near_R, period=2 * math.pi)) - 5.0:
            return False
        if float(P.signed_dist_m(D, np.array([x]), np.array([y]))[0]) < MESA_SHORE_GAP_M + r:
            return False
        if min(float(seg_dist(x, y, *cl[i], *cl[i + 1])) for i in range(len(cl) - 1)) < MESA_LINE_GAP_M + 0.5 * r:
            return False
        if float(seg_dist(x, y, *chord[0], *chord[1])) < MESA_CHORD_GAP_M + r:
            return False
        if any(math.hypot(x - sx, y - sy) < sr + r + 2.0 for sx, sy, sr in stk):
            return False
        if any(math.hypot(x - lx, y - ly) < 30.0 + r for lx, ly in lights):
            return False
        if any(math.hypot(x - qx, y - qy) < spacing * (r + qr) for qx, qy, qr in placed):
            return False
        return True

    def put(x, y, r_scale_rng, h_rng, spacing=0.8):
        kind = MESA_KINDS[rnd.randrange(len(MESA_KINDS))][0]
        rx, ry, zt = dims[kind]
        sc = rnd.uniform(*r_scale_rng)
        top = rnd.uniform(*h_rng)
        sc_h = max(MIN_SCALE, min(1.9, top / zt))
        sc = min(1.9, max(MIN_SCALE, sc))
        s_u = min(sc, sc_h * 1.6, 1.9)
        r = 1.2 * max(rx, ry) * s_u                                        # the cluster's noisy edge reaches ~1.2 x its nominal radius
        if not ok(x, y, r, spacing):
            return None
        vk = pick_variant(kinds_var, kind, rnd)
        ob = PL.place(D, vk, (x, y, 0.0), yaw=rnd.uniform(0, math.tau), scale=(s_u * rnd.uniform(0.97, 1.03), s_u * rnd.uniform(0.97, 1.03), s_u))
        placed.append((x, y, r))
        return dict(obs=[ob], kind="mesa")

    out = []
    for row, off in enumerate((15.0, 38.0)):                              # shelf rows at the foot of the near wall
        th = rnd.uniform(0.0, 0.2) + 0.13 * row
        while th < 2 * math.pi + 0.2:
            R = float(np.interp(th % (2 * math.pi), near_th, near_R)) - off
            x, y = cx + R * math.cos(th), cy + R * math.sin(th)
            st = put(x + rnd.uniform(-2, 2), y + rnd.uniform(-2, 2), (1.0, 1.7), (2.8, 6.0))
            th += (2 * (dims[MESA_KINDS[1][0]][0]) * 1.1) / R * (1.0 if st is None else 1.0)
            if st:
                out.append(st)
    n_isl = 0
    for _clump in range(14):                                                # islands in the open lava: CLUMPS of 3-6 overlapping plateaus (big irregular rock masses, not polka dots)
        if n_isl >= 40:
            break
        for _ in range(200):
            rho = rnd.uniform(25.0, 145.0)
            th = rnd.uniform(0, math.tau)
            c0 = (cx + rho * math.cos(th), cy + rho * math.sin(th))
            st0 = put(c0[0], c0[1], (0.9, 1.45), (3.0, 5.4), spacing=0.9)
            if st0:
                out.append(st0)
                n_isl += 1
                for _j in range(rnd.randint(2, 5)):
                    for _k in range(30):
                        a_ = rnd.uniform(0, math.tau)
                        d_ = rnd.uniform(9.0, 20.0)
                        st = put(c0[0] + d_ * math.cos(a_), c0[1] + d_ * math.sin(a_), (0.6, 1.2), (2.4, 5.0), spacing=0.62)
                        if st:
                            out.append(st)
                            n_isl += 1
                            break
                break
    return out


