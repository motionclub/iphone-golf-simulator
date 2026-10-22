"""hole09_look.py - the Split look pass (POSTCARD_LOOK CONTINUE, 2026-10-04): scenery with the look libraries + the hole's own QA gates.

hole09_build.py calls this module between the scoring build and the look-lib passes. Nothing here moves a scoring vertex: the scoring
meshes (TERRAIN / FAIRWAY / GREEN / TEE_BOX / BUNKER) are built by postcard_lib exactly as before; this module only adds NEW
non-colliding objects (ROCK_ / PLANT_ / DRESS_ names) and re-materials the ridge top (a material only: the lie stays Rough).

What replaces the legacy decorative geometry of the flat build (hole09_build.py of 2026-10-03, kept at
work/postcard-look/v2/hole09/hole09_build.py.at_start):

    legacy ROCK_*/CLIFF_ROCK icosahedra (foot / face / rim boulders)   -> library rocks (PL.scatter_rocks, PL.scatter): wet foot rocks and sea
                                                                          rocks, rim rocks and ridge outcrops (crag + boulder groups)
    ROCK_STACK_nn (custom 64-80 vertex cylinder stacks)                -> PL.place_sea_stack: tapering spires with grassy crowns (+ satellites)
    ruin_wall() / fallen_arch() (rows of ROCK_MEDIUM boulders)         -> hole09_masonry (rough flat-shaded LK_MASONRY stones on wavy bed levels, a doorway with a
                                                                          lintel, a broken voussoir arch with a rubble heap) + fallen DRESS_BLOCK rubble
    surf() WATER_FOAM / WATER_FOAM_CREST strips                        -> deleted; L.build_sea draws sparse broken whitewater patches only

ROUND 2 (2026-10-04, after the skeptic review of round 1), all visual, nothing scoring-relevant:
    bunkers                  -> DRESS_SAND_nn lobes laid on the raised lip rings (build_sand_overlay): organic scalloped sand edges, <= 9 mm over the collider
    flat ridge top           -> DRESS_KNOLL_nn rock-capped hummocks (build_knolls), more crag groups, shrub thickets round cluster centres instead of dots
    scrub / rough colour step -> a shrub + rock chain every 2.2 m along every boundary edge (cover_scrub_boundary), gap-fill stones; the chain keeps the DESIGN's own
                                 4 yd route rule (hole09_design: "keep rocks >= 4 yd off [the route]"), every other scenery piece keeps the builder's 8 yd margin
    24-vertex masonry blocks -> rough, rounded, flat-shaded variants with 98 welded vertices, 4 per kind (chip_blocks, repair round 2; round 2 had one chipped cuboid per kind)

REPAIR ROUND 2 (2026-10-05, after the review "the ruin still reads as stacked bricks"): the ruin / arch are rebuilt by hole09_masonry (flat shading, brick-interior UV windows, skyline rubble on wavy
bed levels, ragged tops, the arch seated in both piers with ONE crown wedge missing: ARCH_H_RIGHT 3.9 -> 4.4 m so no wedge pokes out of the right pier) and chip_blocks gives the fallen blocks
rough rounded variants. The design file, scoring and every non-masonry piece are unchanged.

REPAIR ROUND 3 of the CONTINUE job (2026-10-05, review "the ruin still reads as stacked boxes ... diagonal triangle shading ... floating arch crown"): the ruin / arch stones are planar-faced polyhedra (hole09_stone.py:
one polygon = one plane = one UV mapping; the round-2 hull faces were split into triangles with independent UV windows, 77 % of the near-coplanar pairs mismatched), tops and ~1 stone in 4 are LK_ROCK, the arch has an
outer haunch course (no floating crown), ARCH_H 6.2 -> 5.8 and ARCH_H_RIGHT 4.4 -> 4.9; chip_blocks keeps LK_MASONRY but each block has ONE continuous projection per axis region; N_SHRUB_RIDGE 132 -> 116 / N_TUFT_OUT 64 -> 56
(triangle budget: the props library's new shrub meshes cost +3.9k, the masonry +5k). hole09_build.py: TEE_BOX UVs compensate the 10 cm plate parallax for the address camera, the blend is saved without relative_remap.

ROUND 3 (2026-10-04, after the second skeptic review): DRESS_KNOLL_nn are faceted, steeper hummocks (H/R .42-.52, jittered rings) whose LK_ROCK part is a small irregular
crest outcrop instead of a flat grey disc; hole09_build.py pushes the strata skin further out (SKIN_DISP_M / SKIN_JAG_M / SKIN_MAX_OUT_M) for a more jagged coast. Nothing else changed.

Legacy hole gates kept in spirit (rewritten for the new pieces, see qa_gates): the 8 yd clearance between scenery rocks and the dry safe
ridge route (ROUTE_CLEAR_YD), no rim rock on the ridge lip that faces the channel (RIM_STRETCHES), nothing of the ruin on the drive landing
band or in the sight lines, the ruin 7+ yd inside the cliff, the sea stack in the channel mouth out of every sight line.
"""
import json
import math
import os
import random
import sys

sys.dont_write_bytecode = True
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import postcard_lib as P  # noqa: E402
import postcard_look_lib as L  # noqa: E402
import postcard_props_lib as PL  # noqa: E402
import hole09_masonry as HM  # noqa: E402

YD = P.YD
ROUTE_CLEAR_YD = 8.0                 # legacy: no scenery rock / masonry / shrub within 8 yd of the dry safe ridge route
SCRUB_SOFT_M = 9.0                   # width of the patchy blend zone round the scrub polygon (m)
TUFT_ROUTE_CLEAR_M = 2.5             # tufts (0.25-0.45 m) may come closer to the route, but not into a ball lie on it
CHANNEL_LIP_CLEAR_M = 6.0            # legacy RIM_STRETCHES rule: no rim rock on the ridge lip that faces the channel
ARCH_FACING_DEG = 172.0              # repair round 1: the direction you look THROUGH the opening (clockwise from +Y). 172 = toward the tee along the ridge, so the opening faces the ruin landmark camera (looking north) and reads as an arch hole (the old 110 showed the arch edge-on)
RUIN_H = {1: 4.0, 2: 5.6, 3: 3.4}   # max wall heights by design wall index (the SCENERY heights 3.0 / 4.5 / 2.5 m are visual maxima; the broken profile stays below)
RUIN_SCALE = 1.1                     # plan scale of the SCENERY ruin about its centre (east edge stays >= 7 yd inside the cliff: gate H_RUIN_INSIDE_CLIFF)
RUIN_CLIFF_CLEAR_YD = 7.3            # ruin blocks / rubble centres stay this far inside the cliff (the design: 7+ yd)
RUIN_SHIFT_YD = (-1.0, 0.0)          # the scaled ruin moves 1 yd west: keeps >= 7 yd from the east cliff while the west wall stays > 6 yd off the route
RUIN_T = 1.25                        # masonry wall thickness (m) (repair round 1: was 1.5 box slabs)
RUIN_DOOR_W, RUIN_DOOR_H = 2.4, 2.4  # the doorway of the tall wall: clear width and height (m); the lintel stone bears 0.55 m on each jamb
RUIN_VERTEX_SHORE_M = 6.45           # EVERY masonry vertex stays this far inside the shore (the QA gate: 7 yd - 0.1 m = 6.3 m)
RUIN_VERTEX_ROUTE_M = 5.6            # ... and this far off the dry safe route (the QA gate: 6 yd = 5.49 m)
ARCH_R, ARCH_T, ARCH_DEPTH, ARCH_PIER_W, ARCH_SPRING, ARCH_H_RIGHT = 2.0, 0.75, 1.3, 1.7, 2.7, 4.9   # broken arch: half clear span, ring thickness, depth, pier width, spring height, right pier top (round 3: 4.4 -> 4.9, the haunch stones fill the angle to the ring)
ARCH_SHIFT_YD = (1.0, 5.5)           # the arch stands SOUTH-EAST of the SCENERY spot (repair round 1: +1.5 yd east so the west pier clears the dry safe route by >= 6 yd; the old -0.5 cut the pier)
ARCH_H = 5.8                         # the tall (left) pier top above the ridge (m) (round 3: 6.2 -> 5.8: the thin spike above the ring crown is gone)
RUIN_COURSE_H, RUIN_BLOCK_L = 0.85, (1.3, 2.1)     # chunkier courses than the lib default (0.62 / 0.9-1.5 m): reads on a phone at 40 yd
OUTCROP_GROUPS, OUTCROP_SPACING_M = 24, 11.5       # round 2: more crag groups (was 16 / 15 m: only 12 fitted), crags are what makes the flat ridge top read as a rugged crest
N_SHRUB_RIDGE, N_SHRUB_OUT, N_AGAVE, N_FLOWER_RIDGE, N_FLOWER_OUT, N_STONES = 116, 30, 6, 14, 6, 56     # round 3: 132 -> 116 ridge shrubs (the props library's new shrub meshes cost +3.9k triangles; the masonry stones cost +5k: 250k budget)
N_TUFT_CLUSTER, N_TUFT_SPRINKLE, N_TUFT_OUT = 60, 24, 56     # round 2: tufts are 117 triangles for a 0.4 m plant; the budget goes to crags, knolls and the sand lobes
SHRUB_CLUSTERS, SHRUB_CLUSTER_SIGMA_M, SHRUB_CLUSTER_SPACING_M = 30, 2.7, 12.0   # round 2: ridge shrubs grow in thickets round cluster centres, not as evenly spread dots
KNOLLS, KNOLL_R_M, KNOLL_H_RATIO = 30, (3.0, 5.4), (0.42, 0.52)      # round 2: DRESS_KNOLL_nn hummocks on the flat ridge (visual only, never on the route); round 3: steeper (H/R .31-.38 -> .42-.52): at 18-21 degrees half of every dome was 'flat' for the lawn rule = grey rock
KNOLL_ROUTE_CLEAR_YD = 5.0           # DRESS_KNOLL hummocks (low, soft, no hazard): the design's 4 yd + 1 yd, measured on the farthest vertex of the mesh
COVER_ROUTE_CLEAR_YD = 4.0           # boundary-cover shrubs / rocks keep the DESIGN's rule (hole09_design: "keep rocks >= 4 yd off [the route]"); every other scenery piece keeps 8 yd
COVER_STEP_M = 2.2                   # spacing of the boundary-cover chain along the LK_SCRUB / rough edge
SAND_Z_OFF = 0.009                   # DRESS_SAND overlay height over the collider (the gate allows 1.2 cm at the vertices)
SEEDS = dict(stones=29, ruin_s=52, ruin_w=55, ruin_e=49, reef=28, stacks=11, foot=21, sea=22, gap=23, rim=24, outcrop=25, ruin=26, arch=27, shrub_ridge=31, tuft_ridge=32, flower=33,
             shrub_out=34, tuft_out=35, cover=36, agave=37, rubble=38, knoll=41, sand=43, chip=47, cover_chain=48, cluster=49)


# ----------------------------------------------------------------------------------------------- geometry helpers (metres)
def poly_m(pts_yd):
    return np.array([P.m(x, d) for x, d in pts_yd], float)


def seg_arrays(poly):
    poly = np.asarray(poly, float)
    return poly[:-1], poly[1:]


def dist_to_poly(poly, X, Y):
    A, B = seg_arrays(poly)
    pts = np.stack([np.asarray(X, float).ravel(), np.asarray(Y, float).ravel()], 1)
    return P._dist_pts_segs(pts, A, B).reshape(np.asarray(X).shape)


def route_m(D):
    return poly_m(D.SCENERY["ridge"]["route"])


def spine_m(D):
    return poly_m(D.SCENERY["ridge"]["spine"])


def center_m(D):
    return poly_m(D.CENTERLINE)


def stretch_poly_m(D, name):
    """Polyline (metres) of the SHORE points of one named SCENERY stretch."""
    for st in D.SCENERY["shore_stretches"]:
        if st["name"] == name:
            return poly_m(D.SHORE[st["first"]:st["last"] + 1])
    raise KeyError(name)


def mask_far(poly, r_m):
    return lambda X, Y: dist_to_poly(poly, X, Y) >= r_m


def mask_ridge_side(D):
    """True where the point is closer to the ridge spine than to the ribbon centerline (the verifier's ridge_side)."""
    sp, cl = spine_m(D), center_m(D)
    return lambda X, Y: dist_to_poly(sp, X, Y) < dist_to_poly(cl, X, Y)


def mask_not_ridge_side(D):
    m = mask_ridge_side(D)
    return lambda X, Y: ~m(X, Y)


def mask_in_poly_yd(poly_yd):
    pm = [P.m(x, d) for x, d in poly_yd]
    return lambda X, Y: P._inside_np(pm, X, Y)


def scrub_polygon_yd(D, ext_yd=(36.0, 36.0), seed=909):
    """Polygon (course yards) of the olive scrub on the ridge top: the design ridge spine buffered by the ridge half width + 12 yd (what the lib
    smoke does), but (a) the spine is extended `ext_yd` yd past both ends (into the tee bridge / green block, where the ridge joins the ribbon
    ends) and (b) the half width tapers to a rounded, wavy tip there, so the olive does not stop on a straight cut across the open rough
    (the old flat ends produced two ~37 yd straight seams at D 59.6 and D 461.2). The boundary then follows the 6.5 m terrain triangles."""
    R = D.SCENERY["ridge"]
    w = R.get("width_yd", 40.0)
    hw0 = float(max(w) if isinstance(w, (list, tuple)) else w) / 2 + 12.0
    S = np.array(R["spine"], float)
    t0 = S[0] - S[1]
    t0 /= np.hypot(*t0)
    t1 = S[-1] - S[-2]
    t1 /= np.hypot(*t1)
    rng = np.random.default_rng(seed)
    tips_n = [(1.0, 0.10), (0.78, 0.46), (0.52, 0.80), (0.26, 0.97)]       # (fraction of the extension from the old end... , half width fraction)
    pts, hws = [], []
    for f, hf in tips_n:                                                   # north tip -> old start
        pts.append(S[0] + t0 * ext_yd[0] * f)
        hws.append(hw0 * hf)
    for p in S:
        pts.append(p)
        hws.append(hw0)
    for f, hf in reversed(tips_n):                                         # old end -> south tip
        pts.append(S[-1] + t1 * ext_yd[1] * f)
        hws.append(hw0 * hf)
    pts = np.array(pts)
    hws = np.array(hws) * (1.0 + 0.10 * rng.uniform(-1, 1, len(pts)))     # the outline wobbles about 10 %
    tg = np.gradient(pts, axis=0)
    tg /= np.maximum(np.hypot(tg[:, 0], tg[:, 1]), 1e-9)[:, None]
    nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)
    left, right = pts + nrm * hws[:, None], pts - nrm * hws[:, None]
    return [tuple(p) for p in np.vstack([right, left[::-1]])]


def region_clusters(centers, sigma):
    cen = np.asarray(centers, float).reshape(-1, 2)

    def f(rng, n):
        k = [rng.randrange(len(cen)) for _ in range(n)]
        X = np.array([cen[i, 0] + rng.gauss(0.0, sigma) for i in k])
        Y = np.array([cen[i, 1] + rng.gauss(0.0, sigma) for i in k])
        return X, Y, None
    return f


def region_union(*regs, weights=None):
    w = weights or [1.0] * len(regs)
    cw = np.cumsum(w) / sum(w)

    def f(rng, n):
        Xs, Ys = [], []
        for _ in range(n):
            r = regs[int(np.searchsorted(cw, rng.random()))]
            x, y, _z = r(rng, 1)
            if len(x):
                Xs.append(float(x[0]))
                Ys.append(float(y[0]))
        return np.array(Xs), np.array(Ys), None
    return f


def stats_of(objs):
    return len(objs)


# ----------------------------------------------------------------------------------------------- scrub material (core + soft blend zone)
def assign_scrub_soft(D, core_poly_yd, soft_m=SCRUB_SOFT_M, seed=7, log=print):
    """LK_SCRUB on every TERRAIN top face whose centroid is inside the core polygon, plus a soft zone of `soft_m` metres outside it where a
    smooth noise picks patches (the chance falls from ~85 % at the polygon to ~15 % at the zone edge), so the olive does not end on a ruler line
    but breaks into patches of scrub in the rough. Material slots only: geometry and lies are untouched. Returns (faces_core, faces_soft)."""
    ob = D.terrain or bpy.data.objects[D.terrain_name]
    me = ob.data
    W, ls, lt, lv, mi, pn = L._mesh_arrays(ob)
    pol = L._poly_of_loop(ls, lt, len(lv))
    cen = np.zeros((len(ls), 2))
    np.add.at(cen, pol, W[lv, :2])
    cen /= lt[:, None]
    top = (pn[:, 2] > 0.5) & L._top_mask(D, W, ls, lt, lv, pn)
    poly = np.array([P.m(x, d) for x, d in core_poly_yd], float)
    inside = P._inside_np([tuple(q) for q in poly], cen[:, 0], cen[:, 1])
    A = poly
    B = np.roll(poly, -1, axis=0)
    dist = P._dist_pts_segs(cen, A, B)
    prob = np.clip(1.0 - dist / soft_m, 0.0, 1.0)
    n = L.fbm(cen[:, 0], cen[:, 1], 7.0, seed, 3)
    soft = (~inside) & (dist < soft_m) & (n < 0.15 + 0.70 * prob)
    sel = top & (inside | soft)
    mat = L.look_material("LK_SCRUB", D)
    if mat.name not in [m_.name for m_ in me.materials if m_]:
        me.materials.append(mat)
    k = [m_.name if m_ else "" for m_ in me.materials].index(mat.name)
    mi[sel] = k
    me.polygons.foreach_set("material_index", mi.astype(np.int32))
    me.update()
    log(f"[hole09] scrub material: {int((top & inside).sum())} core faces + {int((top & soft).sum())} soft-zone faces ({soft_m:g} m) -> LK_SCRUB")
    return int((top & inside).sum()), int((top & soft).sum())


# ----------------------------------------------------------------------------------------------- scrub boundary
def scrub_boundary_mid(D):
    """Midpoints (metres) of the TERRAIN top edges between an LK_SCRUB face and a non-scrub top face (the zigzag at the ridge ends)."""
    ob = D.terrain or bpy.data.objects[D.terrain_name]
    me = ob.data
    names = [m.name if m else "" for m in me.materials]
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    out = []
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        f0, f1 = e.link_faces
        if f0.normal.z < 0.5 or f1.normal.z < 0.5:
            continue
        s0 = names[f0.material_index] == "LK_SCRUB"
        s1 = names[f1.material_index] == "LK_SCRUB"
        if s0 != s1:
            a, b = e.verts[0].co, e.verts[1].co
            mw = ob.matrix_world
            a, b = mw @ a, mw @ b
            out.append(((a.x + b.x) / 2, (a.y + b.y) / 2, (a - b).length))
    bm.free()
    return np.array(out, float).reshape(-1, 3)


# ----------------------------------------------------------------------------------------------- bunker sand overlay (DRESS_SAND_nn)
def bunker_lip_geometry(D):
    """The ring construction of BUNKER_nn_LIP exactly as postcard_lib.build_play_surfaces makes it (same functions, same candidate scales): per bunker the
    inner (scale 1.0, z play+0.32), mid (crest, z play+0.57) and outer (z play+0.22) ring points, the `good` mask (angles that have lip faces) and s_out.
    The play meshes are NOT touched; the overlay only reads this to lay sand on the lip surface."""
    pz = D.play_z
    out, bi = [], 0
    for hz in D.hole.hazards:
        if hz[0] != "bunker":
            continue
        bi += 1
        cx, cy = P.m(hz[1], hz[2])
        a, b = hz[3] / 2 * YD, hz[4] / 2 * YD
        ring = P._bunker_ring_pts(hz, 1.0)
        n = len(ring)
        cand = [1.22, 1.17, 1.12, 1.07, 1.03]
        ok = np.zeros((len(cand), n), bool)
        for k, sc_ in enumerate(cand):
            Pk = P._bunker_ring_pts(hz, sc_, n)
            dirv = (Pk - np.array([cx, cy])) / np.maximum(np.hypot(Pk[:, 0] - cx, Pk[:, 1] - cy), 1e-6)[:, None]
            far = Pk + dirv * 0.9
            ok[k] = (P.lie_codes_m(D, Pk[:, 0], Pk[:, 1]) != P.LIE_WATER) & (P.lie_codes_m(D, far[:, 0], far[:, 1]) != P.LIE_WATER)
        has = ok.any(axis=0)
        s_out = np.where(has, np.array(cand)[np.where(has, ok.argmax(axis=0), 0)], 1.0)
        inner_ok = P.lie_codes_m(D, ring[:, 0], ring[:, 1]) != P.LIE_WATER
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)

        def rpts(sv, a=a, b=b, cx=cx, cy=cy, t=t):
            return np.stack([cx + a * sv * np.cos(t), cy + b * sv * np.sin(t)], 1)
        out.append(dict(index=bi, n=n, c=(cx, cy), a=a, b=b, inner=rpts(1.0), mid=rpts(1.0 + (s_out - 1.0) * 0.45), outer=rpts(s_out), good=has & inner_ok,
                        s_out=s_out, z=(pz + P.Z_SAND + 0.02, pz + 0.57, pz + 0.22)))
    return out


def sand_levels(bun, seed, rows=6):
    """Coverage level (0..rows) of the sand overlay on every column of one bunker's lip: smooth lobes (two sines of different wavelength, periodic in the angle),
    slope-limited to one row per column so a lobe edge is a ramp, never a radial cut. Columns: 2*i = the lip angle i, 2*i+1 = the midpoint to i+1."""
    n = bun["n"]
    C = 2 * n
    good = bun["good"]
    exist = np.zeros(C, bool)
    for i in range(n):
        exist[2 * i] = good[i]
        exist[2 * i + 1] = good[i] and good[(i + 1) % n]
    rg = np.random.default_rng(seed)
    pa, pb = rg.uniform(0, math.tau, 2)
    ka, kb = (3, 8) if bun["index"] % 2 else (4, 9)
    t = np.arange(C) * math.tau / C
    noise = 0.5 + 0.5 * (0.64 * np.sin(ka * t + pa) + 0.36 * np.sin(kb * t + pb))
    cov = np.clip((noise - 0.30) / 0.50, 0.0, 1.0)
    lvl = np.rint(cov * rows).astype(int)
    lvl[lvl == 1] = 0                                           # no 0.2 m slivers
    lvl[~exist] = 0
    for _ in range(2 * rows + 2):                               # slope limit between existing neighbours
        ch = False
        for u in range(C):
            for v in ((u - 1) % C, (u + 1) % C):
                if exist[u] and exist[v] and lvl[u] > lvl[v] + 1:
                    lvl[u] = lvl[v] + 1
                    ch = True
        if not ch:
            break
    return lvl, exist


def build_sand_overlay(D, log=print):
    """DRESS_SAND_01..03: sand (LK_SAND) laid on the raised lip ring of each scoring bunker in lobes, so the sand reads as an irregular organic patch with a
    ragged edge instead of a perfect ellipse inside a uniform green ring (split.jpg's bunkers are peanut-shaped). VISUAL ONLY: the play meshes
    (BUNKER_nn sand, BUNKER_nn_LIP, TERRAIN, FAIRWAY ...) are untouched and the lie is still decided by Hole.LieAt (the ellipse); the overlay never leaves the
    lip footprint, so it stays on one ground surface (no step to straddle) and sits SAND_Z_OFF (9 mm) over it (gate PATH_UNDER_BALL: <= 1.5 cm, >= 3 mm,
    no ball hidden). Vertices are exact points of the lip faces (ring rows at 0, 1/3, 2/3 of the way inner -> crest and crest -> outer edge, plus the midpoint
    columns in between), so the overlay follows the lip's creases: no chord can dip under the crest. Returns (objects, info)."""
    mat = L.look_material("LK_SAND", D)
    tile = L.LOOK["LK_SAND"][2]
    objs, info = [], []
    for bun in bunker_lip_geometry(D):
        n, good = bun["n"], bun["good"]
        z_in, z_mid, z_out = bun["z"]
        lip = bpy.data.objects.get(f"BUNKER_{bun['index']:02d}_LIP")
        if lip is None or not good.any():
            info.append(dict(index=bun["index"], faces=0, note="no lip"))
            continue
        # check the replica against the real lip mesh: every inner / mid / outer point of a good angle is a vertex of BUNKER_nn_LIP
        lv_ = np.array([tuple(v.co) for v in lip.data.vertices])
        for key, zz in (("inner", z_in), ("mid", z_mid), ("outer", z_out)):
            for i in np.nonzero(good)[0]:
                d = np.abs(lv_ - np.array([bun[key][i, 0], bun[key][i, 1], zz])).max(axis=1).min()
                if d > 1e-4:                                   # the mesh stores float32 coordinates
                    raise RuntimeError(f"bunker {bun['index']} lip replica mismatch ({key} point {i}, {d:.2e} m): postcard_lib changed, the sand overlay cannot follow the lip")
        # rows 0..6 of every lip angle (exact points of the lip faces)
        R = np.zeros((n, 7, 3))
        for i in range(n):
            p0 = np.array([*bun["inner"][i], z_in])
            p3 = np.array([*bun["mid"][i], z_mid])
            p6 = np.array([*bun["outer"][i], z_out])
            for k in range(7):                          # the end rows sit 1.5 % inside the lip edges: a vertex exactly on a mesh boundary edge is ray-ambiguous (it may hit the sand / fairway below)
                if k <= 3:
                    R[i, k] = p0 + (p3 - p0) * max(k / 3.0, 0.015)
                else:
                    R[i, k] = p3 + (p6 - p3) * min((k - 3) / 3.0, 0.985)
        C = 2 * n
        lvl, exist = sand_levels(bun, SEEDS["sand"] + bun["index"])
        col = np.zeros((C, 7, 3))
        for u in range(C):
            if not exist[u]:
                continue
            col[u] = R[u // 2] if u % 2 == 0 else 0.5 * (R[u // 2] + R[(u // 2 + 1) % n])
        verts, vid = [], {}

        def vtx(u, r):
            if (u, r) not in vid:
                p = col[u, r]
                vid[(u, r)] = len(verts)
                verts.append((float(p[0]), float(p[1]), float(p[2]) + SAND_Z_OFF))
            return vid[(u, r)]
        faces = []
        for u in range(C):
            v = (u + 1) % C
            if not (exist[u] and exist[v]):
                continue
            lu, lw = int(lvl[u]), int(lvl[v])
            lo, hi = min(lu, lw), max(lu, lw)
            for r in range(6):
                if r < lo:
                    faces.append((vtx(u, r), vtx(u, r + 1), vtx(v, r + 1), vtx(v, r)))
                elif r == lo and hi > lo:
                    if lu > lw:
                        faces.append((vtx(u, r), vtx(u, r + 1), vtx(v, r)))
                    else:
                        faces.append((vtx(u, r), vtx(v, r + 1), vtx(v, r)))
        faces = [f for f in faces if _poly_area(verts, f) > 1e-5]
        if not faces:
            info.append(dict(index=bun["index"], faces=0, note="no faces"))
            continue
        uvs = [[(verts[i][0] / tile, verts[i][1] / tile) for i in f] for f in faces]
        ob = L._new_piece(D, L._next_name(D, "DRESS_SAND"), verts, faces, uvs, [0] * len(faces), [mat], col="STRUCTURES", sharp_deg=50.0)
        ob["h9_class"] = "sand"
        objs.append(ob)
        ext = np.maximum(lvl[exist], 0)
        info.append(dict(index=bun["index"], faces=len(faces), name=ob.name, columns=int(exist.sum()), covered=float((lvl[exist] >= 2).mean()), max_level=int(ext.max()),
                         s_out=float(bun["s_out"][good].mean())))
        log(f"[hole09] sand overlay {ob.name}: {len(faces)} faces, {int(exist.sum())} columns, {float((lvl[exist] >= 2).mean()):.0%} of the lip columns carry sand, "
            f"max level {int(ext.max())}/6, mean lip scale {float(bun['s_out'][good].mean()):.3f}")
    return objs, info


def _poly_area(verts, f):
    p = np.array([verts[i] for i in f])
    a = 0.0
    for i in range(1, len(f) - 1):
        a += 0.5 * np.linalg.norm(np.cross(p[i] - p[0], p[i + 1] - p[0]))
    return a


# ----------------------------------------------------------------------------------------------- chipped masonry blocks
def chipped_mesh(src, name, seed, min_verts=64):
    """A worn copy of a library DRESS_BLOCK mesh with at least `min_verts` welded vertices (the library blocks have 24: bevelled cuboids): the longest edges
    are split first, then random ones, the new vertices are pushed in 1-3.5 cm (chipped edges), the old ones jitter 0.8 cm, everything is triangulated."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    bm.from_mesh(src)
    bm.edges.ensure_lookup_table()
    edges = sorted(bm.edges, key=lambda e: (-round(e.calc_length(), 4), e.index))
    k = 0
    while len(bm.verts) + k < min_verts + 6 and k < len(edges):
        k += 1
    pick = edges[:k // 2] + rnd.sample(edges[k // 2:], k - k // 2) if k > 1 else edges
    old = {v.index for v in bm.verts}
    res = bmesh.ops.subdivide_edges(bm, edges=list(pick), cuts=1, use_grid_fill=False)
    bm.verts.ensure_lookup_table()
    bm.normal_update()
    for v in bm.verts:
        if v.index in old:
            v.co += Vector((rnd.uniform(-0.008, 0.008), rnd.uniform(-0.008, 0.008), rnd.uniform(-0.008, 0.008)))
        else:
            v.co -= v.normal * rnd.uniform(0.010, 0.035)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    sm = bool(src.polygons[0].use_smooth) if len(src.polygons) else False
    for f in bm.faces:
        f.smooth = sm
    new = src.copy()
    new.name = name
    bm.to_mesh(new)
    bm.free()
    new.update()
    return new


def chip_blocks(D, log=print):
    """Replace the mesh of every placed DRESS_BLOCK_A / _B instance (fallen ruin blocks, rubble) by a rough, rounded, flat-shaded variant (hole09_masonry.make_block_variant: >= 64 welded vertices,
    brick-interior UV windows). Repair round 2 (2026-10-05): four variants per kind (the instances no longer all share one shape), sized like the library block they replace; the old
    chipped_mesh (a bevelled cuboid with smooth shading and the library's tiled UVs) showed the 'paving brick' top and the box silhouette of the review."""
    protos, variants, n, counter = {}, {}, 0, {}
    for ob in list(bpy.data.objects):
        if ob.type != 'MESH' or ob.data is None:
            continue
        base = ob.data.name.split(".")[0]
        if base not in ("DRESS_BLOCK_A", "DRESS_BLOCK_B"):
            continue
        if base not in variants:
            src = ob.data
            co = np.array([tuple(v.co) for v in src.vertices], float)
            dims = tuple(float(x) for x in (co.max(0) - co.min(0)))
            protos[base] = (src, dims, [m_ for m_ in src.materials])
            variants[base] = []
            for k in range(4):
                rr = random.Random(SEEDS["chip"] * 10 + k + (0 if base.endswith("A") else 50))
                dv = (dims[0] * rr.uniform(0.9, 1.15), dims[1] * rr.uniform(0.85, 1.15), dims[2] * rr.uniform(0.85, 1.1))
                me = HM.make_block_variant(f"{base}_CHIP{k}", SEEDS["chip"] * 10 + k + (0 if base.endswith("A") else 50), dims=dv)
                for m_ in protos[base][2]:
                    me.materials.append(m_)
                if not me.materials:
                    me.materials.append(L.look_material("LK_MASONRY", D))
                variants[base].append(me)
        lib_proto = bool(ob.users_collection) and all(c.name == "ASSET_LIBRARY" for c in ob.users_collection)
        old = ob.data
        if lib_proto:
            ob.data = variants[base][0]               # the hidden library prototypes too: no 24-vertex DRESS_BLOCK mesh is left in the blend (they are not exported anyway)
        else:
            k = counter.get(base, 0)
            counter[base] = k + 1
            ob.data = variants[base][k % 4]
            n += 1
        if old.users == 0:
            bpy.data.meshes.remove(old)
    log("[hole09] rough masonry blocks: " + ", ".join(f"{k}: {len(v)} variants of {sorted(PL.welded_vertex_count(m_) for m_ in v)} welded vertices / {len(v[0].polygons)} triangles" for k, v in variants.items()) + f"; {n} instances")
    return n, {m_.name: PL.welded_vertex_count(m_) for v in variants.values() for m_ in v}


# ----------------------------------------------------------------------------------------------- ridge knolls (DRESS_KNOLL_nn)
def _knoll_mesh(D, name, cx, cy, R, H, seed, ground):
    """One conformal hummock (round 3: a faceted, craggy dome): an apex + 6 rings (u = .22 .42 .62 .80 .92 1.0 of a wobbly radius R, 16 segments), height
    H*(1 - u**1.2) - 0.10 (so the last ring is 10 cm under the flat ridge and the contour is clean) plus a seeded vertical + radial jitter on the inner rings, so the
    top is a pile of tilted facets instead of a clean disc. Faces with a (triangle) normal z > 0.953 (the lawn rule's 0.95 + a margin) are LK_ROCK (the ONE_GREEN lawn rule), a few more tilted faces of the
    upper rings are LK_ROCK too (an irregular outcrop edge); the flanks are LK_SCRUB (warped planar UV like the terrain, so the olive matches)."""
    rg = np.random.default_rng(seed)
    nseg = 16
    us = [0.22, 0.42, 0.62, 0.80, 0.92, 1.0]
    ph = rg.uniform(0, math.tau, 4)
    t = np.arange(nseg) * math.tau / nseg + rg.uniform(0, 0.45)
    rf = 1 + 0.15 * np.sin(2 * t + ph[0]) + 0.09 * np.sin(3 * t + ph[1])
    hm = 1 + 0.20 * np.sin(3 * t + ph[2]) + 0.10 * np.sin(5 * t + ph[3])
    P2 = [(cx, cy)]
    Z = []
    ring_idx = []
    for k, u in enumerate(us):
        idx = []
        jit_r = 0.06 if k < 3 else 0.0
        for j in range(nseg):
            rr = R * u * rf[j] * (1.0 + rg.uniform(-jit_r, jit_r))
            x, y = cx + rr * math.cos(t[j]), cy + rr * math.sin(t[j])
            zr = H * hm[j] * (1.0 - u ** 1.1) - 0.10 + (rg.uniform(-0.07, 0.07) * H if k < 4 else 0.0)
            idx.append(len(P2))
            P2.append((x, y))
            Z.append(zr)
        ring_idx.append(idx)
    g = ground(np.array([p[0] for p in P2]), np.array([p[1] for p in P2]))
    if not np.isfinite(g).all():
        return None
    zr_apex = H * float(hm.mean()) - 0.10 + rg.uniform(-0.05, 0.05) * H
    verts = [(P2[0][0], P2[0][1], float(g[0]) + zr_apex)] + [(P2[i + 1][0], P2[i + 1][1], float(g[i + 1]) + Z[i]) for i in range(len(Z))]
    faces, face_ring = [], []
    for j in range(nseg):
        j2 = (j + 1) % nseg
        faces.append((0, ring_idx[0][j], ring_idx[0][j2]))
        face_ring.append(0)
    for k in range(len(us) - 1):
        for j in range(nseg):
            j2 = (j + 1) % nseg
            faces.append((ring_idx[k][j], ring_idx[k + 1][j], ring_idx[k + 1][j2], ring_idx[k][j2]))
            face_ring.append(k + 1)
    mscrub, mrock = L.look_material("LK_SCRUB", D), L.look_material("LK_ROCK", D)
    t_s, t_r = L.LOOK["LK_SCRUB"][2], L.LOOK["LK_ROCK"][2]
    midx, uvs = [], []
    for f, fr in zip(faces, face_ring):
        p = np.array([verts[i] for i in f])
        nz = []                                                  # the face normal as the polygon (Newell) and as BOTH triangulations of a quad see it: the verifier judges triangles
        for tri in ([(0, 1, 2)] if len(f) == 3 else [(0, 1, 2), (0, 2, 3), (1, 2, 3), (0, 1, 3)]):
            q = np.cross(p[tri[1]] - p[tri[0]], p[tri[2]] - p[tri[0]])
            nz.append(float(q[2] / max(np.linalg.norm(q), 1e-12)))
        rock = max(nz) > 0.953                                   # summit cap and any gentle patch: rock, so no flat grass-coloured area is left (gate ONE_GREEN lawn rule)
        if not rock and fr <= 2 and max(nz) > 0.80 and rg.random() < (0.12, 0.06, 0.0)[fr]:
            rock = True                                          # a few more tilted facets near the top: an irregular outcrop edge, not a clean circle
        midx.append(1 if rock else 0)
        xw, yw = L._warp(p[:, 0], p[:, 1], *L.UV_WARP["LK_SCRUB"]) if not rock else (p[:, 0], p[:, 1])
        tl = t_r if rock else t_s
        uvs.append([(float(a / tl), float(b / tl)) for a, b in zip(xw, yw)])
    ob = L._new_piece(D, name, verts, faces, uvs, midx, [mscrub, mrock], col="ENVIRONMENT", sharp_deg=45.0)
    return ob


def build_knolls(D, avoid, log=print):
    """KNOLLS low hummocks (DRESS_KNOLL_nn: R 3.4-5.2 m, H 1.2-2.3 m) on the flat ridge top, only where the whole footprint stays on the scrub, >= 8 yd from the
    dry safe route (like every scenery rock), >= 6 m + off the channel lip, inside the cliff, clear of the ruin / crags / each other. They register their
    footprint so no plant or rock is scattered through them."""
    route = route_m(D)
    chan_lip = stretch_poly_m(D, "channel_wall_ridge")
    spine = spine_m(D)
    in_scrub = mask_in_poly_yd(scrub_polygon_yd(D))
    ridge_side = mask_ridge_side(D)
    ground = PL.ground_sampler(D)
    reg = PL.region_polyline(spine, 24.0)
    rng = random.Random(SEEDS["knoll"])
    X, Y, _ = reg(rng, 24000)
    ok = in_scrub(X, Y) & ridge_side(X, Y)
    X, Y = X[ok], Y[ok]
    sd = P.signed_dist_m(D, X, Y)
    dr = dist_to_poly(route, X, Y)
    dl = dist_to_poly(chan_lip, X, Y)
    lie = P.lie_codes_m(D, X, Y)
    chosen, objs = [], []
    r_opts = [KNOLL_R_M[1], 0.5 * (KNOLL_R_M[1] + KNOLL_R_M[0]) + 0.6, 0.5 * (KNOLL_R_M[1] + KNOLL_R_M[0]), KNOLL_R_M[0] + 0.5, KNOLL_R_M[0]]
    for i in range(len(X)):
        if len(chosen) >= KNOLLS:
            break
        if lie[i] == P.LIE_WATER:
            continue
        x, y = float(X[i]), float(Y[i])
        for R0 in r_opts:                                        # the largest hummock that fits here
            R = R0 * rng.uniform(0.94, 1.06)
            Rv = 1.26 * R                                         # the plan wobble reaches 1.24 R: every vertex of the mesh keeps the clearances
            if sd[i] > -(Rv + 0.8) or dr[i] < KNOLL_ROUTE_CLEAR_YD * YD + Rv or dl[i] < 5.0 + 0.7 * R:
                continue
            if any(math.hypot(x - ax, y - ay) < ar + Rv + 1.5 for ax, ay, ar in avoid):
                continue
            if any(math.hypot(x - cx, y - cy) < 1.25 * (Rv + 1.26 * cr) for cx, cy, cr, _h in chosen):
                continue
            break
        else:
            continue
        H = R * rng.uniform(*KNOLL_H_RATIO)                        # H/R >= 0.42 keeps the flanks at 22-28 degrees (no flat grass-coloured skirt: the ONE_GREEN lawn rule), so only the crest is rock
        ob = _knoll_mesh(D, L._next_name(D, "DRESS_KNOLL"), x, y, R, H, SEEDS["knoll"] * 100 + len(chosen), ground)
        if ob is None:
            continue
        ob["h9_class"] = "knoll"
        ob["knoll_R"], ob["knoll_H"] = float(R), float(H)
        chosen.append((x, y, R, H))
        objs.append(ob)
        _register(D, x, y, 0.95 * R)
    log(f"[hole09] ridge knolls: {len(objs)} of {KNOLLS} requested, R {min([c[2] for c in chosen] or [0]):.1f}..{max([c[2] for c in chosen] or [0]):.1f} m, H {min([c[3] for c in chosen] or [0]):.1f}..{max([c[3] for c in chosen] or [0]):.1f} m")
    return objs, chosen


# ----------------------------------------------------------------------------------------------- scenery
def _register(D, x, y, r):
    """Reserve a footprint so later scatter calls keep clear of a prop that was placed by hand (place() does not register)."""
    PL._occ(D).append((float(x), float(y), float(r)))


def build_scenery(D, log=print):
    """Rocks, sea stacks, ruin + arch, plants. Returns a dict of the object lists (for the QA gates)."""
    S = D.SCENERY
    pz = D.play_z
    route = route_m(D)
    spine = spine_m(D)
    scrub_poly = scrub_polygon_yd(D)
    in_scrub = mask_in_poly_yd(scrub_poly)
    ridge_side = mask_ridge_side(D)
    off_ridge = mask_not_ridge_side(D)
    route_tuft = mask_far(route, TUFT_ROUTE_CLEAR_M)
    chan_lip = stretch_poly_m(D, "channel_wall_ridge")
    far_route = lambda r: mask_far(route, ROUTE_CLEAR_YD * YD + r + 0.1)         # noqa: E731  (the scatter masks test the centre, so add the prop's radius)
    far_lip = lambda r: mask_far(chan_lip, CHANNEL_LIP_CLEAR_M + r + 0.1)         # noqa: E731
    route_rock, chan_lip_far = far_route(2.6), far_lip(2.6)                       # loose rocks: footprint radius <= 2.6 m
    route_shrub = far_route(2.0)
    out = {}

    def band(lo, hi, side="land"):
        return PL.region_band(D, lo, hi, side)

    def at(x, y):
        return np.array([x]), np.array([y])

    # ---- 1. sea stacks (design positions; the legacy ROCK_STACK_nn columns are gone)
    stacks, stack_avoid = [], []
    for i, s in enumerate(S["sea_stacks"]):
        x, y = P.m(s["x"], s["d"])
        stacks += PL.place_sea_stack(D, x, y, float(s["height_m"]), s["radius_yd"] * YD, seed=SEEDS["stacks"] + i)
        stack_avoid.append((x, y, s["radius_yd"] * YD + 7.0))
    out["stacks"] = stacks
    log(f"[hole09] sea stacks: {len(S['sea_stacks'])} clusters, {len(stacks)} objects")

    # ---- 2. ruin (repair round 1, 2026-10-04): irregular rubble masonry (hole09_masonry: hulls of chipped stones, buried first course, support-checked courses, a lintel bearing on
    #         both jambs, a broken voussoir arch with its crown stones on the ground and a rubble heap in the gap). The old PL.build_ruin / PL.build_masonry_arch boxes are gone.
    R = S["ruin"]
    walls = R["walls"]
    on_land = lambda x, y: (P._on_land_margin(D, x, y, 1.0)          # noqa: E731
                            and float(P.signed_dist_m(D, np.array([x]), np.array([y]))[0]) <= -RUIN_CLIFF_CLEAR_YD * YD)   # centre test for the DRESS_BLOCK instances (fallen blocks / rubble)
    ruin_clip = lambda X, Y: (P.signed_dist_m(D, X, Y) <= -RUIN_VERTEX_SHORE_M) & (dist_to_poly(route, X, Y) >= RUIN_VERTEX_ROUTE_M)    # noqa: E731  every VERTEX of every masonry stone
    ground_fn = PL.ground_sampler(D)
    ruin_objs, fallen = [], []
    rc = np.array([P.m(sum(w[k][0] for w in walls for k in ("p0", "p1")) / 8.0, sum(w[k][1] for w in walls for k in ("p0", "p1")) / 8.0)])[0]
    shift = np.array(P.m(*RUIN_SHIFT_YD))
    big = lambda p: tuple(rc + (np.array(P.m(*p)) - rc) * RUIN_SCALE + shift)       # noqa: E731  the ruin is scaled up about its centre: bigger masonry reads on a phone
    path_w = [big(walls[0]["p1"]), big(walls[0]["p0"]), big(walls[1]["p1"]), big(walls[2]["p1"])]    # one polyline: south stub -> west wall -> the tall wall with the doorway (design walls 0, 1, 2)
    path_e = [big(walls[3]["p0"]), big(walls[3]["p1"])]                                              # the east stub (design wall 3)
    G0 = float(ground_fn(np.array([rc[0]]), np.array([rc[1]]))[0])
    ss = HM.StoneSet(D, "DRESS_RUIN", SEEDS["ruin_s"], clip=ruin_clip)
    door_len = float(np.hypot(*(np.array(path_w[3]) - np.array(path_w[2]))))
    wst = HM.build_wall_path(ss, path_w, [RUIN_H[1], RUIN_H[1], RUIN_H[2]], RUIN_T, (2, 0.5 * door_len, RUIN_DOOR_W, RUIN_DOOR_H), SEEDS["ruin_w"], ground_fn, G0)
    est = HM.build_wall_path(ss, path_e, [RUIN_H[3]], RUIN_T, None, SEEDS["ruin_e"], ground_fn, G0)
    dpt = np.array(wst["door_world"])
    dd = np.array(path_w[3]) - np.array(path_w[2])
    dd /= np.hypot(*dd)
    dn = np.array([-dd[1], dd[0]])

    def door_keep_out(x, y):                                    # no rubble inside the doorway corridor (the QA rays run through the wall at the doorway)
        v = np.array([x, y]) - dpt
        return abs(float(v @ dd)) < RUIN_DOOR_W / 2 + 1.2 and abs(float(v @ dn)) < 3.6
    n_rub_m = 0
    for k_, pts_ in enumerate((path_w, path_e)):
        n_rub_m += HM.scatter_rubble(ss, pts_, RUIN_T, ground_fn, door_keep_out, SEEDS["rubble"] + k_)
    ss.flush()
    ruin_objs += ss.objs
    A = R["fallen_arch"]
    ax, ay = P.m(A["x"] + ARCH_SHIFT_YD[0] + RUIN_SHIFT_YD[0], A["d"] + ARCH_SHIFT_YD[1] + RUIN_SHIFT_YD[1])
    sa = HM.StoneSet(D, "DRESS_ARCH", SEEDS["arch"], clip=ruin_clip)
    arch_info = HM.build_arch(sa, (ax, ay), ARCH_FACING_DEG, ground_fn, G0, r=ARCH_R, t=ARCH_T, depth=ARCH_DEPTH, pier_w=ARCH_PIER_W, spring=ARCH_SPRING,
                              left_top=ARCH_H, right_top=ARCH_H_RIGHT, seed=SEEDS["arch"])
    sa.flush()
    ruin_objs += sa.objs
    rng = random.Random(SEEDS["rubble"])
    rub = []
    for pile in R["rubble"]:
        px, py = P.m(pile["x"] + RUIN_SHIFT_YD[0], pile["d"] + RUIN_SHIFT_YD[1])
        rr = pile["radius_yd"] * YD
        for _ in range(int(2 + rr * 1.0)):
            a, d = rng.uniform(0, math.tau), rr * math.sqrt(rng.random())
            x, y = px + math.cos(a) * d, py + math.sin(a) * d
            if not on_land(x, y) or door_keep_out(x, y):
                continue
            k = rng.choice(("DRESS_BLOCK_A", "DRESS_BLOCK_B"))              # rubble = fallen cut blocks (masonry class: 6 yd off the route, not loose rocks)
            z = pz - 0.1
            rub.append(PL.place(D, k, (x, y, z), rng.uniform(0, math.tau), rng.uniform(0.7, 1.25),
                                (rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25))))
    for i_ in range(4):                                                     # fallen DRESS_BLOCK stones at the foot of the arch piers
        a_ = rng.uniform(0, math.tau)
        x, y = ax + math.cos(a_) * rng.uniform(4.2, 5.6), ay + math.sin(a_) * rng.uniform(4.2, 5.6)
        if on_land(x, y) and ruin_clip(np.array([x]), np.array([y]))[0]:
            rub.append(PL.place(D, rng.choice(("DRESS_BLOCK_A", "DRESS_BLOCK_B")), (x, y, pz - 0.1), rng.uniform(0, math.tau), rng.uniform(0.8, 1.1),
                                (rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25))))
    out["ruin"] = ruin_objs
    out["ruin_fallen"] = fallen + rub
    out["ruin_stats"] = dict(walls=wst, east=est, arch=arch_info, blocks=ss.n_blocks + sa.n_blocks, refused=ss.n_refused + sa.n_refused, rubble_stones=n_rub_m,
                             records=ss.records + sa.records)
    for o in fallen + rub:                                   # fallen blocks / rubble reserve their footprint: no plant grows through them
        _register(D, o.location.x, o.location.y, 1.3)
    # footprints of the ruin (3 m round every 2 m of wall, 7 m round the arch): later scatter keeps off the masonry
    ruin_avoid = []
    for w in walls:
        a, b = np.array(big(w["p0"])), np.array(big(w["p1"]))
        n = max(2, int(np.hypot(*(b - a)) / 2.0))
        for u in np.linspace(0, 1, n + 1):
            p = a + (b - a) * u
            ruin_avoid.append((float(p[0]), float(p[1]), 3.0))
    ruin_avoid.append((ax, ay, 7.5))
    out["ruin_avoid"] = ruin_avoid
    log(f"[hole09] ruin walls: {wst['blocks']} stones, lintel stones {wst['lintels']}, {wst['joints']} joints of which {wst['tight']} within 12 cm of a joint of the course below; east stub {est['blocks']} stones; door jambs {wst.get('jamb')}; blocks per course per segment {wst.get('per_course')}")
    if ss.refused or sa.refused:
        log(f"[hole09] ruin clip refused: walls {[(round(x / YD, 1), round(y / YD, 1)) for x, y in ss.refused]} arch {[(round(x / YD, 1), round(y / YD, 1)) for x, y in sa.refused]} (course yards)")
    log(f"[hole09] ruin: {len(ruin_objs)} masonry meshes, {ss.n_blocks + sa.n_blocks} irregular stones ({ss.n_refused + sa.n_refused} refused by the clip), arch {arch_info['height']:.1f} m with "
        f"{arch_info['missing']} crown wedges on the ground, {n_rub_m} wall-foot rubble stones, {len(rub)} DRESS_BLOCK rubble")

    # ---- 3. wet rocks: foot rocks, reef rocks (tall enough to break the swell: build_sea puffs the whitewater at them), the gap faces, sea rocks
    foot = PL.scatter(D, ["ROCK_BOULDER_B", "ROCK_BLOCK_A", "ROCK_SLAB_A", "ROCK_CAIRN_A", "ROCK_BOULDER_A"], 44, region=band(2.9, 7.0, "sea"),
                      seed=SEEDS["foot"], min_gap=4.0, scale_range=(0.8, 1.6), z=(-0.45, -0.05), wet=True, surface="sea", avoid=stack_avoid)
    reef = PL.scatter(D, ["ROCK_BOULDER_A", "ROCK_BLOCK_A", "ROCK_BOULDER_B"], 10, region=band(3.6, 11.0, "sea"), seed=SEEDS["reef"],
                      min_gap=14.0, scale_range=(1.25, 1.9), z=(-0.15, 0.25), sink=0.0, wet=True, surface="sea", avoid=stack_avoid)
    gap_c = P.m(S["gap"]["x"], S["gap"]["d"])
    gap = PL.scatter(D, ["ROCK_BOULDER_A", "ROCK_BLOCK_A", "ROCK_SLAB_A", "ROCK_BOULDER_B"], 12, region=PL.region_disc(gap_c[0], gap_c[1], 60.0),
                     seed=SEEDS["gap"], min_gap=5.0, scale_range=(1.1, 1.9), z=(-0.5, -0.1), wet=True, surface="sea",
                     masks=[PL.mask_sea(D, 2.9, 14.0)], avoid=stack_avoid)
    sea = PL.scatter(D, ["ROCK_BOULDER_A", "ROCK_SLAB_A", "ROCK_LEDGE_A", "ROCK_BLOCK_A", "ROCK_BOULDER_B"], 14, region=band(12.0, 26.0, "sea"),
                     seed=SEEDS["sea"], min_gap=9.0, scale_range=(1.0, 2.0), z=(-0.6, -0.1), wet=True, surface="sea", avoid=stack_avoid)
    out["foot"], out["reef"], out["gap"], out["sea"] = foot, reef, gap, sea
    log(f"[hole09] wet rocks: foot {len(foot)}, reef {len(reef)}, gap {len(gap)}, sea {len(sea)}")

    # ---- 4. ridge outcrops (big crag + boulders: the relief the flat top cannot have) and rim rocks, 8 yd off the safe route, never on the channel lip
    outcrop = []
    rrng = random.Random(SEEDS["outcrop"])
    cand = []
    for _ in range(9000):
        t = rrng.uniform(0.04, 0.98)
        k = min(int(t * (len(spine) - 1)), len(spine) - 2)
        u = t * (len(spine) - 1) - k
        c = spine[k] * (1 - u) + spine[k + 1] * u
        cand.append((c[0] + rrng.uniform(-24.0, 8.0), c[1] + rrng.uniform(-4.0, 4.0)))
    cand = np.array(cand)
    ok = in_scrub(cand[:, 0], cand[:, 1]) & ridge_side(cand[:, 0], cand[:, 1]) & (P.signed_dist_m(D, cand[:, 0], cand[:, 1]) <= -3.8)
    ok &= P.lie_codes_m(D, cand[:, 0], cand[:, 1]) != P.LIE_WATER
    cand = cand[ok]
    dr_all = dist_to_poly(route, cand[:, 0], cand[:, 1])
    dl_all = dist_to_poly(chan_lip, cand[:, 0], cand[:, 1])
    chosen = []                                             # (x, y, kind, scale, footprint radius)
    for (x, y), dr, dl in zip(cand, dr_all, dl_all):
        kind = ("ROCK_CRAG_B", "ROCK_CRAG_A")[len(chosen) % 2]
        mn, mx = PL.lib_bbox(kind)
        for sc in (1.25, 1.05, 0.88, 0.72, 0.6):            # the largest crag that fits between the route, the lip and the cliff
            rad = 0.5 * math.hypot(mx.x - mn.x, mx.y - mn.y) * sc + 0.3          # half diagonal: no vertex can be farther from the origin in plan
            if dr >= ROUTE_CLEAR_YD * YD + rad and dl >= CHANNEL_LIP_CLEAR_M + rad:
                break
        else:
            continue
        if any(math.hypot(x - rx, y - ry) < rr_ + rad + 5.0 for rx, ry, rr_ in ruin_avoid):
            continue
        if all(math.hypot(x - c[0], y - c[1]) >= OUTCROP_SPACING_M + 0.5 * (rad + c[4]) for c in chosen):
            chosen.append((x, y, kind, sc, rad))
        if len(chosen) >= OUTCROP_GROUPS:
            break
    ground = PL.ground_sampler(D)
    for gi, (cx, cy, kind, sc, rad) in enumerate(chosen):
        z0 = float(ground(*at(cx, cy))[0])
        outcrop.append(PL.place(D, kind, (cx, cy, z0 - 0.35), rrng.uniform(0, math.tau), sc, (rrng.uniform(-0.04, 0.04), rrng.uniform(-0.04, 0.04))))
        _register(D, cx, cy, 0.8 * rad)
        for j in range(rrng.randint(2, 4)):
            a = rrng.uniform(0, math.tau)
            dd = rad + rrng.uniform(1.2, 3.0)
            x, y = cx + math.cos(a) * dd, cy + math.sin(a) * dd
            if not (in_scrub(*at(x, y))[0] and route_rock(*at(x, y))[0] and chan_lip_far(*at(x, y))[0]
                    and P.lie_codes_m(D, *at(x, y))[0] != P.LIE_WATER and P.signed_dist_m(D, *at(x, y))[0] <= -2.0):
                continue
            z1 = float(ground(*at(x, y))[0])
            k2 = rrng.choice(("ROCK_BOULDER_A", "ROCK_BOULDER_B", "ROCK_BLOCK_A", "ROCK_SLAB_A", "ROCK_CAIRN_A", "ROCK_LEDGE_A"))
            s2 = rrng.uniform(0.8, 1.3)
            outcrop.append(PL.place(D, k2, (x, y, z1 - 0.12), rrng.uniform(0, math.tau), s2, (rrng.uniform(-0.1, 0.1), rrng.uniform(-0.1, 0.1))))
            _register(D, x, y, 1.6 * s2)
    # ---- 4b. round 2: low hummocks (DRESS_KNOLL) on the flat ridge, then the shrub / rock chain over the scrub boundary BEFORE the loose rocks and the plants take the room
    crag_discs = [(cx, cy, rad) for (cx, cy, kind_, sc_, rad) in chosen]
    knoll_objs, knoll_specs = build_knolls(D, ruin_avoid + crag_discs, log=log)
    out["knolls"], out["knoll_specs"] = knoll_objs, knoll_specs
    out["cover"] = cover_scrub_boundary(D, avoid=ruin_avoid, log=log)
    rim = PL.scatter(D, ["ROCK_BOULDER_B", "ROCK_STONE_A", "ROCK_STONE_B", "ROCK_BLOCK_A", "ROCK_CAIRN_A", "ROCK_BOULDER_A"], 56, region=band(0.9, 9.5),
                     seed=SEEDS["rim"], min_gap=3.4, scale_range=(0.7, 1.5), masks=[route_rock, chan_lip_far], avoid=ruin_avoid)
    stones = PL.scatter(D, {"ROCK_STONE_A": 3, "ROCK_STONE_B": 3, "ROCK_BOULDER_B": 1}, N_STONES, region=PL.region_polyline(spine, 26.0),
                        masks=[in_scrub, ridge_side, far_route(1.3), far_lip(1.3)], seed=SEEDS["stones"], min_gap=2.4, scale_range=(0.8, 1.5), avoid=ruin_avoid)
    out["outcrop"], out["rim"], out["stones"] = outcrop, rim, stones
    log(f"[hole09] ridge outcrops: {len(chosen)} groups, {len(outcrop)} objects; rim rocks {len(rim)}; ridge stones {len(stones)}")
    out["outcrop_groups"] = chosen

    # ---- 5. plants. big things first (registered footprints), tufts last
    ag = PL.scatter(D, {"PLANT_AGAVE_A": 1}, N_AGAVE, region=PL.region_polyline(spine, 20.0), masks=[in_scrub, ridge_side, route_shrub],
                    seed=SEEDS["agave"], min_gap=6.0, scale_range=(0.9, 1.3), shore_margin_m=1.5, avoid=ruin_avoid)
    # thickets: shrubs grow round ~SHRUB_CLUSTERS centres (beside the crag groups, then free scrub), not as evenly spread dots (split.jpg: dark green patches on the olive)
    crng = random.Random(SEEDS["cluster"])
    cl_cen = []

    def cl_ok(x, y):
        X, Y = at(x, y)
        return (in_scrub(X, Y)[0] and ridge_side(X, Y)[0] and route_shrub(X, Y)[0] and P.signed_dist_m(D, X, Y)[0] <= -3.5 and P.lie_codes_m(D, X, Y)[0] != P.LIE_WATER
                and all(math.hypot(x - ax, y - ay) >= ar + 1.5 for ax, ay, ar in ruin_avoid)
                and all(math.hypot(x - kx, y - ky) >= kr + 1.5 for kx, ky, kr, _kh in knoll_specs)
                and all(math.hypot(x - cx2, y - cy2) >= SHRUB_CLUSTER_SPACING_M for cx2, cy2 in cl_cen))
    for gi, (cx, cy, kind_, sc_, rad) in enumerate(chosen):                 # beside every second crag group (a thicket in its lee)
        if gi % 2:
            continue
        for _ in range(12):
            a = crng.uniform(0, math.tau)
            x, y = cx + math.cos(a) * (rad + 2.4), cy + math.sin(a) * (rad + 2.4)
            if cl_ok(x, y):
                cl_cen.append((x, y))
                break
    for _ in range(4000):
        if len(cl_cen) >= SHRUB_CLUSTERS:
            break
        X_, Y_, _z = PL.region_polyline(spine, 24.0)(crng, 1)
        if cl_ok(float(X_[0]), float(Y_[0])):
            cl_cen.append((float(X_[0]), float(Y_[0])))
    out["shrub_clusters"] = cl_cen
    shr = PL.scatter(D, {"PLANT_SHRUB_C": 5, "PLANT_SHRUB_A": 1}, N_SHRUB_RIDGE, region=region_clusters(np.array(cl_cen), SHRUB_CLUSTER_SIGMA_M), masks=[in_scrub, ridge_side, route_shrub],
                     seed=SEEDS["shrub_ridge"], min_gap=2.8, scale_range=(1.0, 1.75), shore_margin_m=1.5, avoid=ruin_avoid)
    shr2 = PL.scatter(D, {"PLANT_SHRUB_A": 2, "PLANT_SHRUB_B": 1}, N_SHRUB_OUT, region=band(1.2, 9.0), masks=[off_ridge], seed=SEEDS["shrub_out"],
                      min_gap=4.0, scale_range=(0.8, 1.35), shore_margin_m=1.5)
    fl = PL.scatter(D, {"PLANT_FLOWER_WHITE": 2, "PLANT_FLOWER_YELLOW": 2}, N_FLOWER_RIDGE, region=PL.region_polyline(spine, 18.0),
                    masks=[in_scrub, ridge_side, route_tuft], seed=SEEDS["flower"], min_gap=3.0, shore_margin_m=1.5, avoid=ruin_avoid)
    fl += PL.scatter(D, {"PLANT_FLOWER_PURPLE": 1, "PLANT_FLOWER_WHITE": 1}, N_FLOWER_OUT, region=band(1.5, 8.0), masks=[off_ridge], seed=SEEDS["flower"] + 1,
                     min_gap=4.0, shore_margin_m=1.5)
    sc = np.array([[o.location.x, o.location.y] for o in shr + ag]) if (shr or ag) else np.zeros((1, 2))
    tuft_a = PL.scatter(D, {"PLANT_TUFT_C": 5, "PLANT_TUFT_A": 1}, N_TUFT_CLUSTER, region=region_clusters(sc, 2.4), masks=[in_scrub, ridge_side, route_tuft],
                        seed=SEEDS["tuft_ridge"], min_gap=0.6, shore_margin_m=1.2, avoid=ruin_avoid)
    tuft_b = PL.scatter(D, {"PLANT_TUFT_C": 4, "PLANT_TUFT_A": 1}, N_TUFT_SPRINKLE, region=PL.region_polyline(spine, 24.0), masks=[in_scrub, ridge_side, route_tuft],
                        seed=SEEDS["tuft_ridge"] + 1, min_gap=1.4, shore_margin_m=1.2, avoid=ruin_avoid)
    tuft_o = PL.scatter(D, {"PLANT_TUFT_A": 3, "PLANT_TUFT_B": 2}, N_TUFT_OUT, region=band(0.5, 11.0), masks=[off_ridge], seed=SEEDS["tuft_out"],
                        min_gap=1.0, shore_margin_m=1.2)
    out["shrubs"], out["shrubs_out"], out["agave"], out["flowers"] = shr, shr2, ag, fl
    out["tufts"] = tuft_a + tuft_b + tuft_o
    log(f"[hole09] plants: shrubs {len(shr)} + {len(shr2)}, agave {len(ag)}, flowers {len(fl)}, tufts {len(out['tufts'])}")
    return out


def scrub_boundary_edges(D):
    """End points (metres) of the TERRAIN top edges between an LK_SCRUB face and a non-scrub top face: [(ax, ay, bx, by)]."""
    ob = D.terrain or bpy.data.objects[D.terrain_name]
    me = ob.data
    names = [m.name if m else "" for m in me.materials]
    bm = bmesh.new()
    bm.from_mesh(me)
    out = []
    mw = ob.matrix_world
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        f0, f1 = e.link_faces
        if f0.normal.z < 0.5 or f1.normal.z < 0.5:
            continue
        if (names[f0.material_index] == "LK_SCRUB") != (names[f1.material_index] == "LK_SCRUB"):
            a, b = mw @ e.verts[0].co, mw @ e.verts[1].co
            out.append((a.x, a.y, b.x, b.y))
    bm.free()
    return out


def cover_scrub_boundary(D, avoid=(), log=print):
    """A chain of shrubs and rocks over the colour step where the olive LK_SCRUB meets the green rough (the tapered tips of the scrub polygon at the two ridge
    ends, where it follows the 6.5 m terrain triangles). One piece every COVER_STEP_M metres along every boundary edge, alternating shrub / rock, each tried
    at the sample and then at up to 14 jittered spots (+-2.2 m across, +-0.8 m along) until it passes: land with 1.5 m to the shore, off the play surfaces, 6 m off
    the pin, 1.5 m off the markers, clear of every registered footprint, the footprint off the channel lip (rocks) and COVER_ROUTE_CLEAR_YD (4.5 yd, the design's
    '>= 4 yd off the route' rule; the other scenery keeps 8 yd) off the dry safe route. Tufts are added over the same chain. Returns a dict for the gates."""
    edges = scrub_boundary_edges(D)
    mid = scrub_boundary_mid(D)
    if not edges:
        log("[hole09] scrub boundary: none")
        return dict(edges=0, length=0.0, shrubs=[], rocks=[], tufts=[], mid=mid, samples=0, unplaced=0)
    rnd = random.Random(SEEDS["cover_chain"])
    route = route_m(D)
    chan_lip = stretch_poly_m(D, "channel_wall_ridge")
    land = PL.mask_real_land(D, 1.5)
    off_play = PL.mask_off_play(D, 0.5)
    pin_clear = PL.mask_pin_clear(D, 6.0)
    markers = PL.mask_off_markers(1.5)
    ground = PL.ground_sampler(D)
    occ = PL._occ(D)
    shrubs, rocks, unplaced = [], [], 0
    k_shr = (("PLANT_SHRUB_C", 3), ("PLANT_SHRUB_A", 2), ("PLANT_SHRUB_B", 1))
    k_rock = ("ROCK_BOULDER_B", "ROCK_BLOCK_A", "ROCK_STONE_A", "ROCK_BOULDER_A", "ROCK_CAIRN_A", "ROCK_STONE_B")
    wl = [k for k, w in k_shr for _ in range(w)]
    samples = []
    for (ax, ay, bx, by) in edges:
        ln = math.hypot(bx - ax, by - ay)
        n = max(1, int(round(ln / COVER_STEP_M)))
        tx, ty = (bx - ax) / max(ln, 1e-9), (by - ay) / max(ln, 1e-9)
        for k in range(n):
            u = (k + 0.5) / n
            samples.append((ax + (bx - ax) * u, ay + (by - ay) * u, tx, ty, k))
    for si, (sx, sy, tx, ty, k) in enumerate(samples):
        shrub_first = (k + si) % 2 == 0
        placed = False
        for att in range(24):
            # the planned piece first (alternating shrub / rock), then, where the route buffer or a crowded spot refuses it, a small stone: it needs the least room
            small = att >= 8
            shrub = shrub_first and not small
            kind = rnd.choice(("ROCK_STONE_A", "ROCK_STONE_B")) if small else (rnd.choice(wl) if shrub else rnd.choice(k_rock))
            s = rnd.uniform(1.3, 1.7) if small else (rnd.uniform(1.1, 1.7) if shrub else rnd.uniform(1.0, 1.7))
            mn, mx = PL.lib_bbox(kind)
            foot = max(mx.x - mn.x, mx.y - mn.y) * 0.5 * s
            rad = max(0.8 if small else 1.0, foot * 0.55)
            rv = 0.5 * math.hypot(mx.x - mn.x, mx.y - mn.y) * s * 1.12 + 0.1        # farthest vertex from the origin in plan (scale jitter 1.1 included)
            if att % 8 == 0:
                x, y = sx, sy
            else:
                lat, al = rnd.uniform(-2.2, 2.2), rnd.uniform(-0.8, 0.8)
                x, y = sx + tx * al - ty * lat, sy + ty * al + tx * lat
            X, Y = np.array([x]), np.array([y])
            aa = np.linspace(0.0, math.tau, 8, endpoint=False)
            RX, RY = x + 0.75 * foot * np.cos(aa), y + 0.75 * foot * np.sin(aa)
            if not (land(X, Y)[0] and off_play(X, Y)[0] and pin_clear(X, Y)[0] and markers(X, Y)[0] and land(RX, RY).all() and off_play(RX, RY).all()):
                continue
            if (P.lie_codes_m(D, RX, RY) == P.LIE_WATER).any():
                continue
            if float(dist_to_poly(route, X, Y)[0]) < COVER_ROUTE_CLEAR_YD * YD + rv + 0.1:
                continue
            if not shrub and float(dist_to_poly(chan_lip, X, Y)[0]) < CHANNEL_LIP_CLEAR_M + rv:
                continue
            if any(math.hypot(x - ax_, y - ay_) < ar_ + rad + 0.3 for ax_, ay_, ar_ in avoid):
                continue
            if any(math.hypot(x - ox, y - oy) < max(orr + rad, 1.6 if small else 2.0) for ox, oy, orr in occ):
                continue
            z = float(ground(X, Y)[0])
            if not math.isfinite(z):
                continue
            if shrub:
                ob = PL.place(D, kind, (x, y, z - 0.03), rnd.uniform(0, math.tau), (s, s, s * rnd.uniform(0.92, 1.08)), (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05)))
                shrubs.append(ob)
            else:
                hh = (mx.z - max(mn.z, 0.0)) * s
                ob = PL.place(D, kind, (x, y, z - 0.12 * hh), rnd.uniform(0, math.tau), (s * rnd.uniform(0.9, 1.1), s * rnd.uniform(0.9, 1.1), s * rnd.uniform(0.85, 1.1)),
                              (rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06)))
                rocks.append(ob)
            ob["h9_class"] = "cover"
            occ.append((x, y, rad))
            placed = True
            break
        unplaced += 0 if placed else 1
    # ---- gap fill: any 1 m boundary sample still without a shrub / rock within 3 m (and farther than 1.7 m from the route axis, where nothing may stand) gets the small stone
    #      that covers the most of them
    smp1, big_xy = [], [(o.location.x, o.location.y) for o in shrubs + rocks]
    for (ax, ay, bx, by) in edges:
        ln = math.hypot(bx - ax, by - ay)
        n = max(1, int(math.ceil(ln)))
        for k in range(n):
            u = (k + 0.5) / n
            smp1.append((ax + (bx - ax) * u, ay + (by - ay) * u))
    smp1 = np.array(smp1)
    other = [o for o in bpy.data.objects if o.type == 'MESH' and (o.name.startswith(("PLANT_SHRUB", "PLANT_AGAVE")) or (o.name.startswith("ROCK_") and not o.name.startswith(("ROCK_SKIN", "ROCK_SEASTACK", "ROCK_SPIRE")) and "_WET" not in o.name))
             and not o.hide_viewport and o.location.z > 4.0 and o.get("h9_class") != "cover"]
    big_xy += [(o.location.x, o.location.y) for o in other]
    bxy = np.array(big_xy) if big_xy else np.zeros((0, 2))
    n_fill = 0
    skip = np.zeros(len(smp1), bool)
    for _ in range(80):
        cnt = np.array([int((np.hypot(bxy[:, 0] - x, bxy[:, 1] - y) <= 3.0).sum()) if len(bxy) else 0 for x, y in smp1])
        dax = dist_to_poly(route, smp1[:, 0], smp1[:, 1])
        bad = np.nonzero((cnt == 0) & (dax >= 1.7) & ~skip)[0]
        if len(bad) == 0:
            break
        tx_, ty_ = smp1[bad[0]]
        best = None
        why = dict(land=0, route=0, lip=0, avoid=0, occ=0, z=0)
        for ox in np.arange(-2.95, 2.96, 0.25):
            for oy in np.arange(-2.95, 2.96, 0.25):
                x, y = float(tx_ + ox), float(ty_ + oy)
                if math.hypot(ox, oy) > 2.95:
                    continue
                kind = "ROCK_STONE_A" if (n_fill % 2 == 0) else "ROCK_STONE_B"
                s_ = 1.4
                mn, mx = PL.lib_bbox(kind)
                rv = 0.5 * math.hypot(mx.x - mn.x, mx.y - mn.y) * s_ * 1.12 + 0.1
                X, Y = np.array([x]), np.array([y])
                aa = np.linspace(0.0, math.tau, 8, endpoint=False)
                RX, RY = x + 0.6 * rv * np.cos(aa), y + 0.6 * rv * np.sin(aa)
                if not (land(X, Y)[0] and off_play(X, Y)[0] and pin_clear(X, Y)[0] and markers(X, Y)[0] and land(RX, RY).all() and off_play(RX, RY).all()):
                    why["land"] += 1
                    continue
                if (P.lie_codes_m(D, RX, RY) == P.LIE_WATER).any():
                    why["land"] += 1
                    continue
                if float(dist_to_poly(route, X, Y)[0]) < COVER_ROUTE_CLEAR_YD * YD + rv + 0.1:
                    why["route"] += 1
                    continue
                if float(dist_to_poly(chan_lip, X, Y)[0]) < CHANNEL_LIP_CLEAR_M + rv:
                    why["lip"] += 1
                    continue
                if any(math.hypot(x - ax_, y - ay_) < ar_ + 0.9 + 0.3 for ax_, ay_, ar_ in avoid):
                    why["avoid"] += 1
                    continue
                if any(math.hypot(x - ox_, y - oy_) < max(orr + 0.9, 1.6) for ox_, oy_, orr in occ):
                    why["occ"] += 1
                    continue
                z = float(ground(X, Y)[0])
                if not math.isfinite(z):
                    why["z"] += 1
                    continue
                gain = int(((np.hypot(smp1[bad, 0] - x, smp1[bad, 1] - y) <= 3.0)).sum())
                if best is None or gain > best[0]:
                    best = (gain, x, y, z, kind, s_, mx, mn)
        if best is None:
            log(f"[hole09] gap fill: nothing can stand within 3 m of the boundary point ({tx_:.1f}, {ty_:.1f}) (rejections {why})")
            skip[bad[0]] = True                                         # nothing can stand within reach: leave it (counted by the gate)
            continue
        gain, x, y, z, kind, s_, mx, mn = best
        hh = (mx.z - max(mn.z, 0.0)) * s_
        ob = PL.place(D, kind, (x, y, z - 0.12 * hh), rnd.uniform(0, math.tau), (s_ * rnd.uniform(0.9, 1.1), s_ * rnd.uniform(0.9, 1.1), s_ * rnd.uniform(0.85, 1.1)),
                      (rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06)))
        ob["h9_class"] = "cover"
        occ.append((x, y, 0.9))
        rocks.append(ob)
        bxy = np.vstack([bxy, [x, y]]) if len(bxy) else np.array([[x, y]])
        n_fill += 1
    cen = mid[:, :2]
    sc = np.array([[o.location.x, o.location.y] for o in shrubs]) if shrubs else cen
    tufts = PL.scatter(D, {"PLANT_TUFT_C": 2, "PLANT_TUFT_A": 2, "PLANT_TUFT_B": 1}, 40, region=region_clusters(np.vstack([cen, sc]), 1.7),
                       masks=[mask_far(route, TUFT_ROUTE_CLEAR_M)], seed=SEEDS["cover"] + 2, min_gap=0.8, shore_margin_m=1.2)
    for o in tufts:
        o["h9_class"] = "cover"
    log(f"[hole09] scrub boundary: {len(edges)} edges ({mid[:, 2].sum():.0f} m), {len(samples)} chain samples every {COVER_STEP_M} m -> {len(shrubs)} shrubs + {len(rocks)} rocks "
        f"(unplaced samples {unplaced}, {n_fill} gap-fill stones) + {len(tufts)} tufts; route clearance for the chain {COVER_ROUTE_CLEAR_YD} yd")
    return dict(edges=len(edges), length=float(mid[:, 2].sum()), shrubs=shrubs, rocks=rocks, tufts=tufts, mid=mid, samples=len(samples), unplaced=unplaced)
