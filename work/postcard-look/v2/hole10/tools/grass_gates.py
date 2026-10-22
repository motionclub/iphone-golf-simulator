"""Hole 10 GRASS LIVELINESS gates (repair round 4, 2026-10-05) on the staged .blend AND on the re-imported FBX (independent of the build script's own bookkeeping).

  Blender -b --factory-startup --python grass_gates.py -- --blend STAGE/hole_10.blend [--fbx STAGE/hole_10.fbx] [--json OUT.json] [--before-tris 220197]

Prints `GATE: <ID>@<stage> PASS|FAIL - <numbers>`; exit 1 on a FAIL. Gates: GRASS_FRINGE_PRESENT, GRASS_NOT_ON_PLAY_SURFACES, GRASS_NOT_ON_WATER, GRASS_BALL_CLEAR, GRASS_TRI_BUDGET, GRASS_NO_CARDS.
Every number is measured on the geometry that is IN the staged file: tuft = every PLANT_TUFT_* object (the fringe is the only tuft scatter of hole 10 since round 4); world vertices through matrix_world;
ground = the up-facing triangles (nz > 0.5) of TERRAIN / FAIRWAY / GREEN / TEE_BOX / BUNKER / CART_PATH; play surfaces = FAIRWAY* / GREEN* / TEE_BOX* / BUNKER* / CART_PATH* / DRESS_PATH* / DRESS_PADEDGE*.
Definitions (the lib's postcard_props_smoke.fringe_checks / fringe_structure, re-implemented here so they run on an FBX re-import, where there is no D handle and no custom property):
  NOT_ON_PLAY   every vertex of every tuft, ray from 30 m above the play height straight down onto the play meshes: 0 hits (the lib samples 2 of 3 vertices; this is every vertex).
  NOT_ON_WATER  every vertex over a collider top (no vertex over the lava), every origin within 5 cm of the collider top under it, lowest origin z >= 5.0, nearest origin to the cliff edge / lava (24-direction probe
                of the collider every 0.1 m up to 3 m) >= 1.0 m (hole 10's own H_NO_PLANT_ON_WATER limit; the library default is 0.8 m).
  BALL_CLEAR    nearest tuft vertex to every shot ball of the stills configs (postcard_props_lib.still_ball_zones: r 4 m, 1.5 m round the tee ball) >= r, to the pin >= 6 m, to the tee markers / ball / cup >= 1.5 m; tops of the
                tufts in the corridor (<= fw / 2 + first cut + 6 m = 19.06 m from the centerline) or within 12 m of a ball <= 0.55 yd (0.503 m + 4 mm).
  FRINGE        count >= 300, tall (D / E / F) >= 80, fillers >= 100, >= 55 % of the tufts have >= 2 neighbours within 1.0 m (clump), nearest-neighbour CV >= 0.35 and <= 45 % of the distances within 10 % of the median
                (not a grid), singles (no neighbour within 1.0 m) >= 5, lean max <= 12.25 deg and median >= 3 deg, height factor (tuft top over its own ground / library height of its kind) spread min <= 0.75 and max >= 1.2,
                coverage of the rough edge: land cells (collider top) 0.35 .. 3.0 m outside the play footprint or <= 3.0 m inside the cliff edge, thinned to one sample per 2 x 2 m block, share with a tuft origin within 2.5 m >= 20 %
                (and >= 40 % within 45 m of a still's ball).
  TRI_BUDGET    all mesh objects <= 250,000 triangles, the tufts <= 135 triangles each (tall <= 120 faces), mean <= 90, fillers >= 50 % of the tufts, FBX <= 20 MB.
  NO_CARDS      every tuft kind is a 3-D clump: its mesh bounding box is >= 8 cm in x, y AND z, and >= 36 triangles; no tuft object scales a kind by more than the library SCALE_LIMITS (0.5 .. 2.0).
"""
import sys
sys.dont_write_bytecode = True
import os
import re
import json
import math
import importlib.util

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
YD = 0.9144
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d=None):
    return args[args.index(n) + 1] if n in args else d


spec = importlib.util.spec_from_file_location("hole10_design", os.path.join(REPO, "blender", "scripts", "hole10_design.py"))
DES = importlib.util.module_from_spec(spec)
spec.loader.exec_module(DES)
import postcard_props_lib as PL  # noqa: E402   (the lib's constants and still_ball_zones; its library meshes are not built here)

PZ = DES.PLAY_Z
CENTER = [(x * YD, d * YD) for x, d in DES.CENTERLINE]
PIN = CENTER[-1]
CORRIDOR_M = DES.FAIRWAY_WIDTH / 2 * YD + 3.0 + 6.0
TOP_CAP = 0.55 * YD
LIB_H = {"PLANT_TUFT_A": 0.39, "PLANT_TUFT_B": 0.43, "PLANT_TUFT_C": 0.37, "PLANT_TUFT_D": 0.62, "PLANT_TUFT_E": 0.57, "PLANT_TUFT_F": 0.65, "PLANT_TUFT_S": 0.37, "PLANT_TUFT_T": 0.35}
TALL = ("PLANT_TUFT_D", "PLANT_TUFT_E", "PLANT_TUFT_F")
GROUND = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH")
PLAY = ("FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH", "DRESS_PATH", "DRESS_PADEDGE", "DRESS_PADRIM")
FOOT = ("FAIRWAY", "GREEN", "TEE_BOX", "BUNKER")                      # the play footprint of the edge coverage raster (paths / the pad ribbon sit on it)
MARKERS = ("TEE_MARKER_1", "TEE_MARKER_2", "MARKER_TEE", "BALL_START", "HOLE_CUP", "MARKER_PIN")
RES = []


def gate(name, ok, detail, stage):
    RES.append(dict(name=f"{name}@{stage}", ok=bool(ok), detail=str(detail)))
    print(f"GATE: {name}@{stage} {'PASS' if ok else 'FAIL'} - {detail}", flush=True)


def base(n):
    return re.sub(r"\.\d{3,}$", "", n)


def kind_of(o):
    """library kind of a tuft instance: the mesh data name (blend) or the object name (FBX re-import), minus Blender's .001 suffixes and any numeric tail."""
    for cand in (base(o.data.name), base(o.name)):
        m = re.match(r"(PLANT_TUFT_[A-Z])", cand)
        if m:
            return m.group(1)
    return base(o.name)


def stage_objects(stage):
    out = []
    for ob in bpy.data.objects:
        if ob.type not in ('MESH', 'EMPTY'):
            continue
        if stage == "blend":
            if "ASSET_LIBRARY" in [c.name for c in ob.users_collection] or ob.name not in bpy.context.scene.objects:
                continue
        out.append(ob)
    return out


def world_arr(ob):
    me = ob.data
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    M = np.array(ob.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


def tri_soup(objs, up_only=True):
    V, F = [], []
    for o in objs:
        me = o.data
        if not len(me.polygons):
            continue
        W = world_arr(o)
        b0 = len(V)
        V.extend(map(tuple, W.tolist()))
        for p in me.polygons:
            q = [W[v] for v in p.vertices]
            if up_only:
                n = np.zeros(3)
                for k in range(len(q)):
                    a, b = q[k], q[(k + 1) % len(q)]
                    n[0] += (a[1] - b[1]) * (a[2] + b[2])
                    n[1] += (a[2] - b[2]) * (a[0] + b[0])
                    n[2] += (a[0] - b[0]) * (a[1] + b[1])
                ln = float(np.linalg.norm(n))
                if ln < 1e-12 or n[2] / ln <= 0.5:
                    continue
            F.append(tuple(b0 + v for v in p.vertices))
    return (BVHTree.FromPolygons(V, F) if F else None), V, F


def raster(V, F, x0, y0, c, shape):
    """boolean XY coverage raster of triangles (the polygons are fanned): cell centres inside any triangle."""
    g = np.zeros(shape, bool)
    Va = np.asarray(V)
    for f in F:
        for k in range(1, len(f) - 1):
            a, b, d = Va[f[0], :2], Va[f[k], :2], Va[f[k + 1], :2]
            lo = np.floor((np.minimum(np.minimum(a, b), d) - [x0, y0]) / c).astype(int)
            hi = np.ceil((np.maximum(np.maximum(a, b), d) - [x0, y0]) / c).astype(int)
            lo = np.maximum(lo, 0)
            hi = np.minimum(hi, np.array(shape) - 1)
            if hi[0] < lo[0] or hi[1] < lo[1]:
                continue
            ii, jj = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1), indexing="ij")
            px = x0 + (ii + 0.5) * c
            py = y0 + (jj + 0.5) * c
            den = (b[1] - d[1]) * (a[0] - d[0]) + (d[0] - b[0]) * (a[1] - d[1])
            if abs(den) < 1e-12:
                continue
            l1 = ((b[1] - d[1]) * (px - d[0]) + (d[0] - b[0]) * (py - d[1])) / den
            l2 = ((d[1] - a[1]) * (px - d[0]) + (a[0] - d[0]) * (py - d[1])) / den
            l3 = 1.0 - l1 - l2
            m = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
            g[ii[m], jj[m]] = True
    return g


def dilate(g, n):
    out = g.copy()
    for _ in range(n):
        s = out.copy()
        s[1:, :] |= out[:-1, :]
        s[:-1, :] |= out[1:, :]
        s[:, 1:] |= out[:, :-1]
        s[:, :-1] |= out[:, 1:]
        out = s
    return out


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / max(dx * dx + dy * dy, 1e-12), 0.0, 1.0)
    return np.hypot(px - (ax + t * dx), py - (ay + t * dy))


MUTANT = opt("--mutant")                  # negative controls: one injected bad tuft (blend only); the named gate MUST fail


def inject(name, tufts):
    """Copy a real fringe tuft (same mesh) to a bad place: 'play' = on the fairway (course yd 14.3, 66.2 = station A), 'water' = over the lava (171, 161), 'ball' = 2 m from the approach ball (107.1, 159.3),
    'tall' = a 1.6 m tuft (z scale x 3) in the ball corridor on the first cut near station A, 'pin' = 3 m from the pin (261, 164.7), 'carpet' = nothing (the carpet control is a different stage file)."""
    src = next(o for o in tufts if kind_of(o) == "PLANT_TUFT_D")
    spots = dict(play=(14.3 * YD, 66.2 * YD, 1.0), water=(171.0 * YD, 161.0 * YD, 1.0), ball=(107.1 * YD + 2.0, 159.3 * YD, 1.0), tall=(14.3 * YD + 12.5, 66.2 * YD, 3.0), pin=(261.0 * YD - 3.0, 164.7 * YD, 1.0))
    x, y, k = spots[name]
    ob = src.copy()
    for c in src.users_collection:
        c.objects.link(ob)
    ob.location = (x, y, PZ)
    ob.scale = (1.0, 1.0, k)
    ob.rotation_euler = (0.0, 0.0, 0.0)
    ob.name = "PLANT_TUFT_D_MUTANT"
    bpy.context.view_layer.update()


def run(stage, tris_before):
    objs = stage_objects(stage)
    meshes = [o for o in objs if o.type == 'MESH']
    tufts = [o for o in meshes if base(o.name).startswith("PLANT_TUFT") or base(o.data.name).startswith("PLANT_TUFT")]
    if MUTANT and stage == "blend":
        inject(MUTANT, tufts)
        objs = stage_objects(stage)
        meshes = [o for o in objs if o.type == 'MESH']
        tufts = [o for o in meshes if base(o.name).startswith("PLANT_TUFT") or base(o.data.name).startswith("PLANT_TUFT")]
    ground_objs = [o for o in meshes if base(o.name).startswith(GROUND)]
    play_objs = [o for o in meshes if base(o.name).startswith(PLAY)]
    foot_objs = [o for o in meshes if base(o.name).startswith(FOOT)]
    gb, GV, GF = tri_soup(ground_objs)
    pb, PV, PF = tri_soup(play_objs)
    down = Vector((0, 0, -1))
    kinds = [kind_of(o) for o in tufts]
    W = [world_arr(o) for o in tufts]
    origin = np.array([[o.matrix_world.translation.x, o.matrix_world.translation.y, o.matrix_world.translation.z] for o in tufts]) if tufts else np.zeros((0, 3))

    def ground_z(x, y):
        h = gb.ray_cast(Vector((float(x), float(y), PZ + 30.0)), down, 80.0)
        return None if h[0] is None else float(h[0].z)

    gz = np.array([ground_z(p[0], p[1]) if ground_z(p[0], p[1]) is not None else np.nan for p in origin]) if len(origin) else np.zeros(0)

    # ---- NOT_ON_PLAY
    viol = []
    for o, w in zip(tufts, W):
        for x, y, _z in w:
            if pb is not None and pb.ray_cast(Vector((float(x), float(y), PZ + 30.0)), down, 80.0)[0] is not None:
                viol.append((o.name, round(float(x), 2), round(float(y), 2)))
                break
    nv = int(sum(len(w) for w in W))
    gate("GRASS_NOT_ON_PLAY_SURFACES", len(tufts) > 0 and not viol,
         f"{len(tufts)} tufts / {nv} vertices (every vertex) ray-cast down onto {len(play_objs)} play meshes ({', '.join(sorted({re.sub(r'[_.0-9]+$', '', base(o.name)) for o in play_objs}))}): {len(viol)} tufts over a play surface {viol[:3]}", stage)

    # ---- NOT_ON_WATER
    over_water = 0
    for w in W:
        for x, y, _z in w:
            if gb.ray_cast(Vector((float(x), float(y), PZ + 30.0)), down, 80.0)[0] is None:
                over_water += 1
    dz = np.abs(origin[:, 2] - gz) if len(origin) else np.zeros(0)
    ang = np.linspace(0.0, 2 * math.pi, 24, endpoint=False)
    edge = []
    for p in origin:
        e = 3.0
        for r in np.arange(0.3, 3.01, 0.1):
            if any(gb.ray_cast(Vector((float(p[0] + r * math.cos(a)), float(p[1] + r * math.sin(a)), PZ + 30.0)), down, 80.0)[0] is None for a in ang):
                e = float(r)
                break
        edge.append(e)
    edge = np.array(edge) if edge else np.zeros(0)
    zmin = float(origin[:, 2].min()) if len(origin) else 0.0
    gate("GRASS_NOT_ON_WATER", len(tufts) > 0 and over_water == 0 and not np.isnan(gz).any() and float(np.nanmax(dz)) <= 0.05 and zmin >= 5.0 and float(edge.min()) >= 1.0,
         f"{len(tufts)} tufts / {nv} vertices: vertices over the lava 0 expected, found {over_water}; origins on a collider top max |dz| {float(np.nanmax(dz)) if len(dz) else 0:.3f} m (<= 0.05), lowest origin z {zmin:.2f} (>= 5.0), "
         f"nearest origin to the cliff edge / lava {float(edge.min()) if len(edge) else 0:.2f} m (>= 1.0; the probe stops at 3 m)", stage)

    # ---- BALL_CLEAR
    balls = PL.still_ball_zones(None, number=10)
    mk = [np.array(o.matrix_world.translation)[:2] for o in objs if base(o.name) in MARKERS]
    worst_ball, worst_pin, worst_mk = 99.0, 99.0, 99.0
    short = []
    for o, w in zip(tufts, W):
        xy = w[:, :2]
        for bx, by, br in balls:
            d = float(np.hypot(xy[:, 0] - bx, xy[:, 1] - by).min()) - br
            worst_ball = min(worst_ball, d)
            if d < -1e-6:
                short.append((o.name, round(d, 2)))
        worst_pin = min(worst_pin, float(np.hypot(xy[:, 0] - PIN[0], xy[:, 1] - PIN[1]).min()) - 6.0)
        for m_ in mk:
            worst_mk = min(worst_mk, float(np.hypot(xy[:, 0] - m_[0], xy[:, 1] - m_[1]).min()) - 1.5)
    tops = np.array([float(w[:, 2].max()) - (g if not np.isnan(g) else PZ) for w, g in zip(W, gz)]) if W else np.zeros(0)
    d_line = np.array([min(float(seg_dist(p[0], p[1], *CENTER[i], *CENTER[i + 1])) for i in range(len(CENTER) - 1)) for p in origin]) if len(origin) else np.zeros(0)
    near_ball = np.array([any(math.hypot(p[0] - bx, p[1] - by) <= 12.0 for bx, by, _r in balls) for p in origin]) if len(origin) else np.zeros(0, bool)
    # the corridor (the chain of fairway stations up to C): the last segment C -> pin crosses the lava, so only the segments tee -> C count
    d_corr = np.array([min(float(seg_dist(p[0], p[1], *CENTER[i], *CENTER[i + 1])) for i in range(len(CENTER) - 2)) for p in origin]) if len(origin) else np.zeros(0)
    in_c = (d_corr <= CORRIDOR_M) | near_ball
    top_c = float(tops[in_c].max()) if in_c.any() else 0.0
    bad_top = [(tufts[i].name, round(float(tops[i]), 3)) for i in np.nonzero(in_c & (tops > TOP_CAP + 0.004))[0]]
    gate("GRASS_BALL_CLEAR", worst_ball >= -1e-6 and worst_pin >= -1e-6 and worst_mk >= -1e-6 and not bad_top,
         f"{len(balls)} shot-ball zones {[(round(b[0] / YD, 1), round(b[1] / YD, 1), b[2]) for b in balls]} (course yd, r m): nearest tuft vertex vs the balls worst margin {worst_ball:+.2f} m, margin to the 6 m pin disc {worst_pin:+.2f} m, "
         f"to the 1.5 m tee markers / ball / cup ({len(mk)} markers) {worst_mk:+.2f} m; {int(in_c.sum())} tufts in the ball corridor (<= {CORRIDOR_M:.1f} m off the centerline tee -> C or <= 12 m from a ball): tallest top {top_c:.3f} m "
         f"(<= {TOP_CAP:.3f} + 4 mm = 0.55 yd), over {bad_top[:3] or 'none'}; whole hole tallest {float(tops.max()) if len(tops) else 0:.2f} m", stage)

    # ---- FRINGE_PRESENT
    n = len(tufts)
    P2 = origin[:, :2]
    nn = np.zeros(n)
    nb1 = np.zeros(n, int)
    if n:
        for i in range(0, n, 300):
            d = np.hypot(P2[i:i + 300, None, 0] - P2[None, :, 0], P2[i:i + 300, None, 1] - P2[None, :, 1])
            d[np.arange(d.shape[0]), np.arange(i, i + d.shape[0])] = 1e9
            nn[i:i + 300] = d.min(1)
            nb1[i:i + 300] = (d <= 1.0).sum(1)
    cv = float(nn.std() / max(nn.mean(), 1e-9)) if n else 0.0
    grid = float((np.abs(nn - np.median(nn)) <= 0.1 * np.median(nn)).mean()) if n else 1.0
    clump_share = float((nb1 >= 2).mean()) if n else 0.0
    singles = int((nb1 == 0).sum())
    lean = []
    for o in tufts:
        z = np.array(o.matrix_world)[:3, :3] @ np.array([0.0, 0.0, 1.0])
        lean.append(math.degrees(math.acos(min(1.0, float(z[2] / max(np.linalg.norm(z), 1e-9))))))
    lean = np.array(lean)
    f = np.array([t / LIB_H.get(k, 0.5) for t, k in zip(tops, kinds)])
    tall_n = sum(1 for k in kinds if k in TALL)
    fill_n = n - tall_n
    by_kind = {k: kinds.count(k) for k in sorted(set(kinds))}
    # rough-edge coverage raster (0.5 m cells over the shore bbox)
    allv = np.asarray(GV)
    x0, y0 = float(allv[:, 0].min()) - 2.0, float(allv[:, 1].min()) - 2.0
    c = 0.5
    shape = (int((allv[:, 0].max() + 2.0 - x0) / c) + 1, int((allv[:, 1].max() + 2.0 - y0) / c) + 1)
    land = raster(GV, GF, x0, y0, c, shape)
    _fb, FV, FF = tri_soup(foot_objs)
    foot = raster(FV, FF, x0, y0, c, shape)
    # distance of every land cell to the play footprint (<= 3 m: dilation rings) and to the cliff edge (<= 3 m: erosion rings)
    d_play = np.full(shape, 99.0)
    cur = foot.copy()
    d_play[cur] = 0.0
    for k in range(1, 7):
        nxt = dilate(cur, 1)
        d_play[nxt & ~cur] = k * c
        cur = nxt
    d_edge = np.full(shape, 99.0)
    cur = ~land
    for k in range(1, 7):
        nxt = dilate(cur, 1)
        d_edge[nxt & ~cur] = k * c
        cur = nxt
    strip = land & ~foot & (((d_play >= 0.35) & (d_play <= 3.0)) | (d_edge <= 3.0))
    ii, jj = np.nonzero(strip)
    blk = {}
    for a, b in zip(ii.tolist(), jj.tolist()):
        blk.setdefault((a // 4, b // 4), (a, b))                                           # one sample per 2 x 2 m block
    smp = np.array([(x0 + (a + 0.5) * c, y0 + (b + 0.5) * c) for a, b in blk.values()]) if blk else np.zeros((0, 2))
    kd = KDTree(max(n, 1))
    for i in range(n):
        kd.insert((float(P2[i, 0]), float(P2[i, 1]), 0.0), i)
    kd.balance()
    cov = np.array([kd.find((float(p[0]), float(p[1]), 0.0))[2] <= 2.5 for p in smp]) if len(smp) and n else np.zeros(0, bool)
    near_b = np.array([any(math.hypot(p[0] - bx, p[1] - by) <= 45.0 for bx, by, _r in balls) for p in smp]) if len(smp) else np.zeros(0, bool)
    cov_all = float(cov.mean()) if len(cov) else 0.0
    cov_foc = float(cov[near_b].mean()) if near_b.any() else 1.0
    zs = np.array([float(np.linalg.norm(np.array(o.matrix_world)[:3, :3][:, 2])) for o in tufts]) if n else np.zeros(0)          # the instance's z scale = the fringe height factor (0.6 .. 1.8 of the library tuft)
    ok = (n >= 300 and tall_n >= 80 and fill_n >= 100 and clump_share >= 0.55 and cv >= 0.35 and grid <= 0.45 and singles >= 5 and float(lean.max()) <= 12.25 and float(np.median(lean)) >= 3.0
          and float(f.min()) <= 0.75 and float(f.max()) >= 1.2 and float(zs.min()) >= 0.595 and float(zs.max()) <= 1.805 and float(zs.max()) >= 1.5 and float(zs.min()) <= 0.7 and cov_all >= 0.20 and (cov_foc >= 0.40 or int(near_b.sum()) < 30))
    gate("GRASS_FRINGE_PRESENT", ok,
         f"{n} tufts ({tall_n} tall D/E/F + {fill_n} fillers S/T; by kind {by_kind}), {100 * clump_share:.0f}% have >= 2 neighbours within 1 m (a clump; >= 55 %), {singles} singles (>= 5); nearest-neighbour distance mean {float(nn.mean()) if n else 0:.2f} m, CV {cv:.2f} "
         f"(>= 0.35), {100 * grid:.0f}% within 10 % of the median (<= 45 %): not a grid; lean max {float(lean.max()) if n else 0:.1f} deg (<= 12), median {float(np.median(lean)) if n else 0:.1f} (>= 3); height over its ground / library height of its kind "
         f"{float(f.min()) if n else 0:.2f}..{float(f.max()) if n else 0:.2f} (median {float(np.median(f)) if n else 0:.2f}; the corridor cap scales some down), tallest {float(tops.max()) if n else 0:.2f} m; instance z scale (the height factor) {float(zs.min()) if n else 0:.2f}..{float(zs.max()) if n else 0:.2f} (asked 0.6-1.8); rough-edge coverage {100 * cov_all:.0f}% of {len(smp)} samples "
         f"(2 x 2 m blocks of {int(strip.sum())} land cells 0.35-3 m outside the play footprint / <= 3 m inside the cliff edge; a tuft within 2.5 m; >= 20 %), {100 * cov_foc:.0f}% of the {int(near_b.sum())} within 45 m of a still ball (>= 40 %)", stage)

    # ---- TRI_BUDGET + NO_CARDS
    tri_all = 0
    tri_t = []
    for o in meshes:
        o.data.calc_loop_triangles()
        t = len(o.data.loop_triangles)
        tri_all += t
    for o in tufts:
        tri_t.append(len(o.data.loop_triangles))
    fbx = opt("--fbx")
    size_mb = os.path.getsize(fbx) / 1048576.0 if (stage == "fbx" and fbx) else os.path.getsize(opt("--blend")) / 1048576.0
    tri_sum = int(sum(tri_t))
    gate("GRASS_TRI_BUDGET", tri_all <= 250000 and (max(tri_t) <= 135 if tri_t else True) and (tri_sum / max(n, 1)) <= 90.0 and fill_n >= 0.5 * n and (stage != "fbx" or size_mb <= 20.0),
         f"{tri_all} triangles over {len(meshes)} mesh objects (<= 250,000; round 3 stage: {tris_before}, {tri_all - tris_before:+d}), the {n} tufts {tri_sum} triangles ({tri_sum / max(n, 1):.0f} per tuft <= 90, largest {max(tri_t) if tri_t else 0} <= 135, "
         f"{fill_n} of {n} are 36-triangle fillers >= 50 %); the 170 old A / B tufts of round 3 (19,890 triangles) are gone; {'FBX' if stage == 'fbx' else '.blend'} {size_mb:.2f} MB (<= 20 for the FBX)", stage)
    sm = {}
    for o, k in zip(tufts, kinds):
        me = o.data
        if k in sm:
            continue
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        sm[k] = (co.max(0) - co.min(0), len(me.loop_triangles), len(me.polygons))
    bad = [(k, [round(float(v), 3) for v in e], t, pg) for k, (e, t, pg) in sm.items() if min(e) < 0.08 or t < 36 or (k in TALL and pg > 120)]
    scl = [float(np.abs(np.linalg.norm(np.array(o.matrix_world)[:3, :3], axis=0)).max()) for o in tufts]
    ext_txt = str({k: [round(float(v), 2) for v in e] for k, (e, _t, _p) in sm.items()})
    gate("GRASS_NO_CARDS", not bad and (max(scl) <= 2.0 + 1e-6 if scl else True),
         f"{len(sm)} tuft kinds, every one a 3-D clump: bounding box >= 8 cm on every axis, >= 36 triangles, tall <= 120 faces (bad {bad or 'none'}; extents m {ext_txt}); largest instance scale {max(scl) if scl else 0:.2f} (<= 2.0)", stage)
    return dict(n=n, tall=tall_n, fill=fill_n, by_kind=by_kind, tris_all=tri_all, tris_tufts=tri_sum, cov=cov_all, cov_focus=cov_foc, lean_max=float(lean.max()) if n else 0.0, tallest=float(tops.max()) if n else 0.0, top_corridor=top_c,
                clump_share=clump_share, singles=singles, nn_cv=cv, grid=grid, balls=[list(b) for b in balls])


STATS = {}
before = int(opt("--before-tris", "220197"))
if opt("--blend"):
    if not bpy.data.filepath or os.path.abspath(bpy.data.filepath) != os.path.abspath(opt("--blend")):
        bpy.ops.wm.open_mainfile(filepath=opt("--blend"))
    STATS["blend"] = run("blend", before)
if opt("--fbx"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=opt("--fbx"))
    STATS["fbx"] = run("fbx", before)
if opt("--json"):
    json.dump(dict(gates=RES, stats=STATS), open(opt("--json"), "w"), indent=1)
fails = [r["name"] for r in RES if not r["ok"]]
print(f"RESULT: {'ALL PASS' if not fails else 'FAILURES ' + str(fails)} ({len(RES)} gates)")
sys.exit(1 if fails else 0)
