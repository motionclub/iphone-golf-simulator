"""Hole 10 stage gates that need no postcard_lib handle: they run on an opened staged .blend OR on a re-imported FBX.

  Blender -b --factory-startup --python stage_gates.py -- --blend STAGE/hole_10.blend [--fbx STAGE/hole_10.fbx] [--json OUT.json]
  Blender -b --factory-startup --python stage_gates.py -- --fbx STAGE/hole_10.fbx            (FBX stage only)

Prints `GATE: <ID>@<stage> PASS|FAIL - <numbers>`; exit 1 on a FAIL. Stage `blend` = the objects postcard_lib.export_fbx exports (every MESH/EMPTY
outside the hidden ASSET_LIBRARY collection), stage `fbx` = every object of the FBX re-imported into an empty scene.
Gates: H_NO_12_VERTEX_ROCK, H_NO_STRETCH_2X, H_NO_FOAM_STRIP, H_BUDGET, H_NEW_PREFIXES, H_NEAR_WALL, H_FAR_RING, H_SKYLINE_VARIED, H_CRUST, H_GLOW_JOINTS, H_STACKS, H_RUBBLE, H_LAVA_LIGHTS, H_ROCK_CHUNKING,
H_BACKDROP, H_CONE_GLOW, H_NO_COLLIDER_PROPS, H_NO_ANIMATION_ON_LAVA, H_TEE_CONTINUOUS, H_GROUND_UV_SLIVERS, H_TEE_RIM (round 3; replaces H_TEE_KERB).
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

REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
YD = 0.9144
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d=None):
    return args[args.index(n) + 1] if n in args else d


spec = importlib.util.spec_from_file_location("hole10_design", os.path.join(REPO, "blender", "scripts", "hole10_design.py"))
DES = importlib.util.module_from_spec(spec)
spec.loader.exec_module(DES)
SC = DES.SCENERY
PZ = DES.PLAY_Z
GROUND = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH")
NEWP = ("ROCK_", "PLANT_", "DRESS_", "WATER_", "LAVA_")
RES = []


def gate(name, ok, detail, stage):
    RES.append(dict(name=f"{name}@{stage}", ok=bool(ok), detail=str(detail)))
    print(f"GATE: {name}@{stage} {'PASS' if ok else 'FAIL'} - {detail}", flush=True)


def base(n):
    return re.sub(r"\.\d{3,}$", "", n)


def stage_objects(stage):
    out = []
    for ob in bpy.data.objects:
        if ob.type not in ('MESH', 'EMPTY'):
            continue
        if stage == "blend":
            cols = [c.name for c in ob.users_collection]
            if "ASSET_LIBRARY" in cols or ob.name not in bpy.context.scene.objects:
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


def _nz_world(q):
    """z component of the unit normal (Newell) of a polygon given as world-space points."""
    n = np.zeros(3)
    for k in range(len(q)):
        a, b = q[k], q[(k + 1) % len(q)]
        n[0] += (a[1] - b[1]) * (a[2] + b[2])
        n[1] += (a[2] - b[2]) * (a[0] + b[0])
        n[2] += (a[0] - b[0]) * (a[1] + b[1])
    ln = float(np.linalg.norm(n))
    return float(n[2] / ln) if ln > 1e-12 else 0.0


def welded(ob, tol=1e-4):
    me = ob.data
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    if len(co) == 0:
        return 0
    k = np.round(co / tol).astype(np.int64)
    return len(np.unique(k, axis=0))


def mats_of(ob):
    return {m.name for m in ob.data.materials if m}


_E = {}


def basalt_glow():
    if not _E:
        img = bpy.data.images.load(os.path.join(REPO, "Unity/Assets/Resources/Course/Look/Basalt_E.png"), check_existing=True)
        w, h = img.size
        px = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(px)
        E = px.reshape(h, w, 4)[:, :, :3].max(axis=2)
        _E.update(G=E > 0.2, w=w, h=h, mean=float((E > 0.2).mean()))
    return _E


_R = np.random.default_rng(1010).random((96, 2))                                      # 96 fixed, uniformly distributed samples per triangle (a thin glow line is not hit by a coarse grid)
BARY = np.stack([1.0 - np.sqrt(_R[:, 0]), np.sqrt(_R[:, 0]) * (1.0 - _R[:, 1]), np.sqrt(_R[:, 0]) * _R[:, 1]], axis=1)


def glow_gate(stage, meshes, base_s):
    """Area-weighted (every instance counts, scaled by its world scale) lit-texel share of Basalt_E on the TOP faces and on the SIDE faces of every ROCK_ mesh that uses LK_BASALT, the share of side
    triangles with any glow, and the median world length of a glow dash (0.105 tile = the median lit stretch of the strong lines of Basalt_E, over the world v tile of the authored UVs)."""
    E = basalt_glow()
    G, w, h, gmean = E["G"], E["w"], E["h"], E["mean"]
    cache = {}
    acc = dict(top_a=0.0, top_g=0.0, side_a=0.0, side_g=0.0, tri_n=0.0, tri_lit=0.0)
    dv_list, dv_w = [], []
    nobj = 0
    for o in meshes:
        if not o.name.startswith("ROCK_") or "LK_BASALT" not in mats_of(o):
            continue
        me = o.data
        if me.name not in cache:
            me.calc_loop_triangles()
            nt = len(me.loop_triangles)
            tv = np.empty(nt * 3, np.int64)
            tl = np.empty(nt * 3, np.int64)
            mi = np.empty(nt, np.int64)
            me.loop_triangles.foreach_get("vertices", tv)
            me.loop_triangles.foreach_get("loops", tl)
            me.loop_triangles.foreach_get("material_index", mi)
            co = np.empty(len(me.vertices) * 3)
            me.vertices.foreach_get("co", co)
            V = co.reshape(-1, 3)[tv.reshape(-1, 3)]
            uvl = me.uv_layers.active
            u = np.empty(len(me.loops) * 2)
            uvl.data.foreach_get("uv", u)
            UV = u.reshape(-1, 2)[tl.reshape(-1, 3)]
            nrm = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0])
            area = 0.5 * np.linalg.norm(nrm, axis=1)
            nz = np.abs(nrm[:, 2]) / np.maximum(2.0 * area, 1e-12)
            ok = area > 1e-8
            su = np.einsum("sk,tkc->tsc", BARY, UV)                                  # (T, 96, 2) sample UVs
            lit = G[(np.floor((su[..., 1] % 1.0) * h).astype(int)) % h, (np.floor((su[..., 0] % 1.0) * w).astype(int)) % w].mean(axis=1)
            # dv / dz along the steepest edge of each side triangle (object space)
            dvdz = []
            for t in np.nonzero(ok & (nz < 0.5))[0][::3]:
                dz = V[t, :, 2]
                i0, i1 = int(np.argmin(dz)), int(np.argmax(dz))
                if dz[i1] - dz[i0] > 0.3:
                    dvdz.append(abs(UV[t, i1, 1] - UV[t, i0, 1]) / (dz[i1] - dz[i0]))
            cache[me.name] = (area * ok, nz >= 0.8, lit, float(np.median(dvdz)) if dvdz else None)
        area, top, lit, dvdz = cache[me.name]
        sv = np.linalg.svd(np.array(o.matrix_world)[:3, :3], compute_uv=False) / base_s
        wgt = float(np.mean(sv[:2])) ** 2
        acc["top_a"] += wgt * float(area[top].sum())
        acc["top_g"] += wgt * float((area * lit)[top].sum())
        acc["side_a"] += wgt * float(area[~top].sum())
        acc["side_g"] += wgt * float((area * lit)[~top].sum())
        sd = ~top & (area > 0)
        acc["tri_n"] += wgt * float(area[sd].sum())
        acc["tri_lit"] += wgt * float(area[sd & (lit > 0)].sum())
        if dvdz:
            dv_list.append(dvdz / float(sv[2]))
            dv_w.append(wgt * float(area[~top].sum()))
        nobj += 1
    top_cov = acc["top_g"] / max(acc["top_a"], 1e-9)
    side_cov = acc["side_g"] / max(acc["side_a"], 1e-9)
    lit_share = acc["tri_lit"] / max(acc["tri_n"], 1e-9)
    order = np.argsort(dv_list)
    cw = np.cumsum(np.array(dv_w)[order])
    dv_med = float(np.array(dv_list)[order][int(np.searchsorted(cw, 0.5 * cw[-1]))]) if dv_list else 0.0
    streak = 0.105 / max(dv_med, 1e-9)
    gate("H_GLOW_JOINTS", nobj >= 200 and top_cov <= 0.005 and 0.25 * gmean <= side_cov <= 0.6 * gmean and 0.10 <= lit_share <= 0.50 and streak >= 2.5,
         f"Basalt_E sampled at the authored UVs of {nobj} ROCK_ objects (LK_BASALT): glow texels on TOP faces {top_cov:.2%} (<= 0.5 %), on SIDE faces {side_cov:.2%} (texture mean {gmean:.2%}, continuous box UV = 1.0 x; "
         f"allowed 0.25..0.6 x = {0.25 * gmean:.2%}..{0.6 * gmean:.2%}), {lit_share:.0%} of the side area carries any glow (10-50 %), median glow dash {streak:.1f} m long in the world (>= 2.5 m; the box-UV lattice is "
         f"{0.105 * 8:.2f} m), world v tile {1.0 / max(dv_med, 1e-9):.1f} m", stage)


def run(stage):
    objs = stage_objects(stage)
    by = {o.name: o for o in objs}
    meshes = [o for o in objs if o.type == 'MESH']
    ter = by.get("TERRAIN_CRATER")
    base_sv = np.linalg.svd(np.array(ter.matrix_world)[:3, :3], compute_uv=False) if ter is not None else np.ones(3)
    base_s = float(np.mean(base_sv))
    cx, cy = SC["crater"]["cx"] * YD, SC["crater"]["cd"] * YD
    # ---- H_NO_12_VERTEX_ROCK: every ROCK_*/CLIFF_ROCK* object (skin and wall pieces too) has >= 60 welded vertices; no 12-vertex 20-face mesh anywhere
    rocks = [o for o in meshes if o.name.startswith(("ROCK_", "CLIFF_ROCK"))]
    seen, low, vmin = {}, [], 10 ** 9
    for o in rocks:
        k = o.data.name
        if k not in seen:
            seen[k] = welded(o)
        vmin = min(vmin, seen[k])
        if seen[k] < 60:
            low.append((k, seen[k]))
    ico = [o.name for o in meshes if len(o.data.polygons) == 20 and welded(o) == 12 and o.name not in ("BALL_START",) and not o.name.startswith("PLANT_")]
    gate("H_NO_12_VERTEX_ROCK", not low and not ico and len(rocks) > 0,
         f"{len(rocks)} ROCK_ objects on {len(seen)} unique meshes: min {vmin} welded vertices (>= 60), offenders {low[:4] or 'none'}; 12-vertex 20-face meshes anywhere "
         f"(plants and BALL_START exempt): {ico[:3] or 'none'}", stage)
    # ---- H_NO_STRETCH_2X: singular values of the world matrix normalised by TERRAIN's own scale
    bad, smin, smax, rmax, n = [], 9.0, 0.0, 0.0, 0
    for o in meshes:
        if not o.name.startswith(("ROCK_", "PLANT_", "DRESS_")) or o.name.startswith(("DRESS_CONE", "DRESS_SMOKE")):
            continue
        n += 1
        sv = np.linalg.svd(np.array(o.matrix_world)[:3, :3], compute_uv=False) / base_s
        smin, smax, rmax = min(smin, float(sv.min())), max(smax, float(sv.max())), max(rmax, float(sv.max() / sv.min()))
        if sv.min() < 0.5 - 1e-6 or sv.max() > 2.0 + 1e-6 or sv.max() / sv.min() > 2.0 + 1e-6:
            bad.append((o.name, [round(float(v), 4) for v in sv]))
    gate("H_NO_STRETCH_2X", not bad and n > 0,
         f"{n} ROCK_/PLANT_/DRESS_ instances: every singular scale in [{smin:.4f}, {smax:.4f}] (limits 0.5..2.0), max/min {rmax:.3f} (<= 2.0), offenders {bad[:3] or 'none'}", stage)
    # ---- H_NO_FOAM_STRIP: no foam / surf geometry or material on a lava hole
    foam = [o.name for o in objs if re.search(r"FOAM|SURF|SPRAY|SHELF", o.name, re.I)]
    foam_m = [o.name for o in meshes if any(re.search(r"FOAM|SURF", m_, re.I) for m_ in mats_of(o))]
    white = [o.name for o in meshes if any(m_ in ("LK_SURF", "LK_FALL", "LK_WATER", "LK_WATER_SHALLOW") for m_ in mats_of(o))]
    gate("H_NO_FOAM_STRIP", not foam and not foam_m and not white,
         f"objects named FOAM/SURF/SPRAY/SHELF {foam[:3] or 'none'}; meshes with a foam / surf / sea material {(foam_m + white)[:3] or 'none'} (the crater has lava, no sea, no surf)", stage)
    # ---- H_BUDGET (triangles; the FBX size is checked by the runner)
    tris = 0
    for o in meshes:
        me = o.data
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
    gate("H_BUDGET_TRIS", tris <= 250000, f"{tris} triangles over {len(meshes)} mesh objects (<= 250000)", stage)
    # ---- H_NEW_PREFIXES: baseline names kept, everything new uses a non-collision prefix
    newbad = [o.name for o in objs if o.name.startswith(GROUND) and not re.match(r"^(TERRAIN_CRATER|FAIRWAY|FAIRWAY_FIRSTCUT|GREEN|GREEN_APRON|TEE_BOX|BUNKER_0[12](_LIP)?)(\.\d+)?$", o.name)]
    coll_props = [o.name for o in objs if o.name.startswith(("ROCK_", "PLANT_", "DRESS_", "WATER_", "LAVA_")) and o.name.startswith(GROUND)]
    gate("H_NO_COLLIDER_PROPS", not newbad and not coll_props, f"collision-prefixed objects outside the 10 baseline play meshes: {newbad[:4] or 'none'}; new props with a collision prefix: {coll_props or 'none'}", stage)
    # ---- H_NEAR_WALL / H_FAR_RING / H_SKYLINE: the crater wall = a NEAR terraced wall of tangent library wall segments + the far 295-355 yd ring of the brief
    wr = SC["wall_ring"]
    r0, r1 = wr["r_inner"] * YD, wr["r_outer"] * YD
    walls = [o for o in meshes if base(o.name).startswith("ROCK_WALL_BASALT_")]
    info = []
    for o in walls:
        w = world_arr(o)
        c = w.mean(0)
        info.append((o, w, math.hypot(c[0] - cx, c[1] - cy)))
    split_r = r0 - 2.0                                         # the far ring starts at r_inner (295 yd); the near wall (front row 214+ yd, second row +9.5 m, bays round the stacks) ends below ~290 yd
    near = [t for t in info if t[2] < split_r]
    far = [t for t in info if t[2] >= split_r]
    oldnames = [o.name for o in meshes if re.match(r"^(ROCK_WALL_(FLAT|BLUNT)|CLIFF_ROCK|ROCK_(SMALL|MEDIUM|LARGE))(\.\d+)?$", o.name)]

    def cover(group):
        ang = np.zeros(72, bool)
        for o, w, r in group:
            c = w.mean(0)
            ac = math.degrees(math.atan2(c[1] - cy, c[0] - cx))
            hw = 0.5 * float(np.hypot(*(w.max(0) - w.min(0))[:2])) / max(r, 1.0) * 180 / math.pi
            for b_ in range(72):
                mid = -180 + (b_ + 0.5) * 5
                d_ = (mid - ac + 180) % 360 - 180
                if abs(d_) <= hw:
                    ang[b_] = True
        return float(ang.mean())
    shore_m = np.array([(x * YD, d * YD) for x, d in DES.SHORE])

    def d_shore(P_):
        a_, b_ = shore_m, np.roll(shore_m, -1, axis=0)
        ab = b_ - a_
        out = np.full(len(P_), 1e9)
        for i in range(len(a_)):
            t = np.clip(((P_[:, 0] - a_[i, 0]) * ab[i, 0] + (P_[:, 1] - a_[i, 1]) * ab[i, 1]) / max(float(ab[i] @ ab[i]), 1e-9), 0.0, 1.0)
            out = np.minimum(out, np.hypot(P_[:, 0] - (a_[i, 0] + t * ab[i, 0]), P_[:, 1] - (a_[i, 1] + t * ab[i, 1])))
        return out
    near_tops = [float(w[:, 2].max()) for o, w, r in near]
    near_pts = np.vstack([w[:, :2] for o, w, r in near]) if near else np.zeros((0, 2))
    near_clear = float(d_shore(near_pts[::3]).min()) / YD if len(near_pts) else 0.0
    near_rmin = min((float(np.hypot(w[:, 0] - cx, w[:, 1] - cy).min()) for o, w, r in near), default=0.0) / YD
    gate("H_NEAR_WALL", len(near) >= 60 and cover(near) >= 0.95 and near_clear >= 14.0 and near_rmin >= 190.0 and near_tops and 12.0 <= min(near_tops) and max(near_tops) <= 60.0 and not oldnames,
         f"{len(near)} near-wall library segments (ROCK_WALL_BASALT_N*/F*, uniform scale), covering {cover(near):.0%} of the crater's 360 deg, {near_rmin:.0f} yd at the nearest to the crater centre (>= 190), nearest vertex "
         f"{near_clear:.1f} yd from the shore polygon (>= 14), tops {min(near_tops):.1f}..{max(near_tops):.1f} m above the lava (12..60); legacy ROCK_WALL_FLAT/BLUNT/CLIFF_ROCK/ROCK_SMALL..: {oldnames[:3] or 'none'}", stage)
    inband = sum(1 for o, w, r in far if r0 - 2.0 <= r <= r1 + 14.0)
    far_tops = [float(w[:, 2].max()) for o, w, r in far]
    gate("H_FAR_RING", len(far) >= 60 and inband >= 0.97 * len(far) and cover(far) >= 0.90 and far_tops and 14.0 <= min(far_tops) and max(far_tops) <= 80.0,
         f"{len(far)} far-ring library wall segments, {inband} within {r0 - 2:.0f}..{r1 + 14:.0f} m of the crater centre ({r0:.0f}..{r1:.0f} m = the brief's 295..355 yd), covering {cover(far):.0%} of the 360 deg (>= 90), "
         f"tops {min(far_tops):.1f}..{max(far_tops):.1f} m above the lava (14..80; design h_max {wr['h_max']:.0f} m + the near-wall step)", stage)
    # skyline = highest wall top per 5 deg of the crater centre (near + far): ridges and saddles, not a level fence (round 1: amplitude 30.6 m, mean step 3.2 m)
    top_bin = np.zeros(72)
    for o, w, r in info:
        a_ = (np.degrees(np.arctan2(w[:, 1] - cy, w[:, 0] - cx)) % 360 // 5).astype(int) % 72
        for b_ in np.unique(a_):
            top_bin[b_] = max(top_bin[b_], float(w[a_ == b_, 2].max()))
    step = np.abs(np.diff(np.concatenate([top_bin, top_bin[:1]])))
    amp = float(np.percentile(top_bin, 90) - np.percentile(top_bin, 10))
    gate("H_SKYLINE_VARIED", (top_bin > 0).all() and amp >= 40.0 and float(step.mean()) >= 4.0 and float(np.percentile(top_bin, 90)) <= 75.0,
         f"wall skyline over the 72 bins of 5 deg: p10 {np.percentile(top_bin, 10):.1f} / median {np.median(top_bin):.1f} / p90 {np.percentile(top_bin, 90):.1f} m, amplitude (p90 - p10) {amp:.1f} m (>= 40), mean step between neighbouring bins "
         f"{float(step.mean()):.2f} m (>= 4.0), highest {top_bin.max():.1f} m; the flat build of round 1 measured 30.6 m / 3.19 m (a level fence)", stage)
    # ---- H_CRUST: the cooled crust that covers the crater floor (ROCK_CRUST_nn hex-plate chunks): keeps off the play surfaces, the lines of play and every lava light, stays below every sight line
    crust = [o for o in meshes if re.match(r"^ROCK_CRUST_\d+$", base(o.name))]
    if crust:
        mp = np.vstack([world_arr(o) for o in crust])
        cl = [(x * YD, d * YD) for x, d in DES.CENTERLINE]

        def seg_d(P_, a_, b_):
            ab = np.array(b_) - np.array(a_)
            t = np.clip(((P_[:, 0] - a_[0]) * ab[0] + (P_[:, 1] - a_[1]) * ab[1]) / max(float(ab @ ab), 1e-9), 0.0, 1.0)
            return np.hypot(P_[:, 0] - (a_[0] + t * ab[0]), P_[:, 1] - (a_[1] + t * ab[1]))
        d_line = min(float(seg_d(mp[:, :2], cl[i], cl[i + 1]).min()) for i in range(len(cl) - 1)) / YD
        d_chord = float(seg_d(mp[:, :2], cl[0], cl[3]).min()) / YD
        d_sh = float(d_shore(mp[::2, :2]).min()) / YD
        lt_ = [np.array(o.matrix_world.translation) for o in objs if re.match(r"^LAVA_LIGHT_\d+$", o.name)]
        d_lt = min((float(np.hypot(mp[:, 0] - p[0], mp[:, 1] - p[1]).min()) for p in lt_), default=99.0) / YD
        mtop = float(mp[:, 2].max())
        mlow = float(mp[:, 2].min())
        nfaces = sum(len(o.data.polygons) for o in crust)
        rcover = sum(float(np.ptp(world_arr(o)[:, 0]) * np.ptp(world_arr(o)[:, 1])) for o in crust) / YD ** 2
        gate("H_CRUST", len(crust) >= 20 and nfaces >= 4000 and d_sh >= 24.0 and d_line >= 38.0 and d_chord >= 25.0 and d_lt >= 25.0 and mtop <= 5.0 and mlow <= -0.5,
             f"{len(crust)} crust chunks (ROCK_CRUST_nn, {nfaces} faces): nearest vertex {d_sh:.1f} yd from the shore polygon (>= 24), {d_line:.1f} yd from the line of play (>= 38), {d_chord:.1f} yd from the tee -> C chord (>= 25), "
             f"{d_lt:.1f} yd from the nearest lava light (>= 25), highest vertex {mtop:.2f} m above the lava (<= 5.0, below every sight line from z >= {PZ:.0f}), lowest {mlow:.1f} m (standing in the lava)", stage)
    else:
        gate("H_CRUST", False, "no ROCK_CRUST_nn objects", stage)
    # ---- H_GLOW_JOINTS: the Basalt_E glow, SAMPLED FROM THE TEXTURE at the authored UVs of every wall / stack / crust / skin face (round-3 reviewer: 'a brown field of short orange dashes, rain')
    glow_gate(stage, meshes, base_s)
    # ---- H_STACKS: the 11 SCENERY stacks = library basalt pieces at their design centres, <= 12 m above the lava, standing in the lava
    stacks_ok, worst_d, tall, floating = 0, 0.0, 0.0, []
    for s in SC["stacks"]:
        sx, sy = s["x"] * YD, s["d"] * YD
        near = [o for o in meshes if o.name.startswith("ROCK_BASALT_") and math.hypot(o.matrix_world.translation.x - sx, o.matrix_world.translation.y - sy) < 0.8 * s["r"] * YD + 0.6]
        if near:
            stacks_ok += 1
            worst_d = max(worst_d, min(math.hypot(o.matrix_world.translation.x - sx, o.matrix_world.translation.y - sy) for o in near))
            for o in near:
                w = world_arr(o)
                tall = max(tall, float(w[:, 2].max()))
    for o in meshes:
        if o.name.startswith("ROCK_BASALT_") and not o.name.startswith("ROCK_WALL"):
            w = world_arr(o)
            if float(w[:, 2].min()) > 0.05:
                floating.append(o.name)
    gate("H_STACKS", stacks_ok == len(SC["stacks"]) and tall <= 12.0 + 0.05 and not floating,
         f"{stacks_ok}/{len(SC['stacks'])} design stack centres carry a library ROCK_BASALT_* main piece (origin within {worst_d:.2f} m of the design point), highest top {tall:.2f} m above the lava (<= 12.0), "
         f"basalt pieces not standing in the lava (lowest vertex above z 0.05): {floating[:3] or 'none'}", stage)
    # ---- H_LAVA_LIGHTS + H_ROCK_CHUNKING (the Unity PostcardImportCheck rules, measured on the same numbers in yards)
    lights = sorted([o for o in objs if re.match(r"^LAVA_LIGHT_\d+$", o.name)], key=lambda o: o.name)
    lp = [np.array(o.matrix_world.translation) for o in lights]
    lava = by.get("WATER_LAVA")
    ztop = float(world_arr(lava)[:, 2].max()) if lava is not None else 0.0
    pair = min((float(np.hypot(*(a - b)[:2])) for i, a in enumerate(lp) for b in lp[i + 1:]), default=99.0) / YD
    above = [(p[2] - ztop) / YD for p in lp]
    rim_m = SC["crater"]["rim_radius"] * YD + 20.0
    rad = [math.hypot(p[0] - cx, p[1] - cy) for p in lp]
    ok_l = 3 <= len(lights) <= 5 and pair >= 8.0 and all(0.5 <= a <= 6.0 for a in above) and all(r <= rim_m for r in rad) and all(o.type == 'EMPTY' for o in lights)
    gate("H_LAVA_LIGHTS", ok_l,
         f"{len(lights)} LAVA_LIGHT_nn EMPTY objects (3..5), nearest pair {pair:.1f} yd (>= 8), heights over the lava {', '.join('%.2f' % a for a in above)} yd (0.5..6), "
         f"{max(rad) / YD:.0f} yd max from the crater centre (<= {rim_m / YD:.0f})", stage)
    big, near_n, worst = [], 0, 0.0
    for o in meshes:
        if not o.name.startswith("ROCK_"):
            continue
        w = world_arr(o)
        lo, hi = w.min(0), w.max(0)
        d2 = min((float(np.sum(np.maximum(np.maximum(lo - p, p - hi), 0.0) ** 2)) for p in lp), default=1e9)
        if d2 <= (25.0 * YD) ** 2:
            near_n += 1
            across = float(max(hi[0] - lo[0], hi[1] - lo[1])) / YD
            worst = max(worst, across)
            if across > 24.0:
                big.append((o.name, round(across, 1)))
    gate("H_ROCK_CHUNKING", not big and near_n > 0,
         f"{near_n} ROCK_ pieces within 25 yd of a lava light, widest {worst:.1f} yd across (<= 24: a renderer only gets the lights nearest its bounds); too wide: {big[:4] or 'none'}", stage)
    # ---- H_RUBBLE: foot rubble is library basalt, in the lava, off the lava carry corridor
    cl = DES.CENTERLINE
    c_st, p_st = (cl[-2][0] * YD, cl[-2][1] * YD), (cl[-1][0] * YD, cl[-1][1] * YD)
    carry = [(c_st[0] + (p_st[0] - c_st[0]) * k / 14.0, c_st[1] + (p_st[1] - c_st[1]) * k / 14.0) for k in range(15)]
    rub = [o for o in meshes if re.match(r"^ROCK_(BOULDER|BLOCK|SLAB|CAIRN|LEDGE|STONE)_[A-Z]_BASALT", base(o.name))]
    dmin = min((min(math.hypot(o.matrix_world.translation.x - a, o.matrix_world.translation.y - b) for a, b in carry) for o in rub), default=99.0)
    gate("H_RUBBLE", len(rub) >= 10 and dmin >= 24.0, f"{len(rub)} basalt rubble rocks at the cliff foot (library meshes), nearest to the lava carry line {dmin:.1f} m (>= 24, the legacy corridor)", stage)
    # ---- H_BACKDROP: cone behind the ring, smoke cards beyond the rim, all DRESS_ and non-colliding
    cone = by.get("DRESS_CONE")
    smoke = [o for o in meshes if o.name.startswith("DRESS_SMOKE")]
    ok_b = cone is not None and len(smoke) >= 2
    det = "DRESS_CONE missing" if cone is None else ""
    if cone is not None:
        w = world_arr(cone)
        cc = (w.min(0) + w.max(0)) / 2
        dist = math.hypot(cc[0] - cx, cc[1] - cy)
        ok_b &= dist >= r0 - 10.0
        det = f"DRESS_CONE centre {dist:.0f} m from the crater centre (>= {r0 - 10:.0f}), top {float(w[:, 2].max()):.0f} m above the lava, {len(mats_of(cone))} material(s) {sorted(mats_of(cone))}"
    sm_ok = all(mats_of(o) == {"LK_SMOKE"} and math.hypot(*(world_arr(o).mean(0)[:2] - np.array([cx, cy]))) >= SC["crater"]["rim_radius"] * YD for o in smoke)
    gate("H_BACKDROP", ok_b and sm_ok, f"{det}; {len(smoke)} DRESS_SMOKE_nn cards (LK_SMOKE only, beyond the rim: {sm_ok})", stage)
    # ---- H_CONE_GLOW: the volcano glows (round-3 reviewer: 'a hatched brown mass with no glowing joints or eruption'): LK_LAVA flow strips from the rim to the foot + a molten crater
    if cone is not None and "LK_LAVA" in mats_of(cone):
        me = cone.data
        names = [m.name if m else "" for m in me.materials]
        W = world_arr(cone)
        z0, z1 = float(W[:, 2].min()), float(W[:, 2].max())
        lava_i = names.index("LK_LAVA")
        tot_a = lav_a = 0.0
        parent = {}

        def find(a):
            while parent.setdefault(a, a) != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        comp_z = {}
        polys = []
        for p_ in me.polygons:
            vs = [W[i] for i in p_.vertices]
            a_ = 0.5 * float(np.linalg.norm(sum(np.cross(vs[k] - vs[0], vs[k + 1] - vs[0]) for k in range(1, len(vs) - 1))))
            tot_a += a_
            if p_.material_index == lava_i:
                lav_a += a_
                polys.append(p_)
                r0 = find(p_.vertices[0])
                for v_ in p_.vertices[1:]:
                    parent[find(v_)] = r0
        for p_ in polys:
            c = find(p_.vertices[0])
            zs = [float(W[i][2]) for i in p_.vertices]
            lo, hi = comp_z.get(c, (1e9, -1e9))
            comp_z[c] = (min(lo, min(zs)), max(hi, max(zs)))
        flows = [c for c, (lo, hi) in comp_z.items() if hi - lo >= 0.6 * (z1 - z0)]
        gate("H_CONE_GLOW", 0.05 <= lav_a / tot_a <= 0.35 and len(flows) >= 1 and max(hi for lo, hi in comp_z.values()) >= z1 - 0.1 * (z1 - z0) and min(lo for lo, hi in comp_z.values()) <= z0 + 0.15 * (z1 - z0),
             f"DRESS_CONE {len(me.polygons)} faces, LK_LAVA flow / crater faces = {lav_a / tot_a:.0%} of the area (5-35 %), {len(flows)} connected lava body(ies) spanning >= 60 % of the cone height "
             f"(rim to foot: lava z {min(lo for lo, hi in comp_z.values()):.0f}..{max(hi for lo, hi in comp_z.values()):.0f} m of the cone's {z0:.0f}..{z1:.0f}), a molten crater floor; static (no animation, no emission animation)", stage)
    else:
        gate("H_CONE_GLOW", False, "DRESS_CONE has no LK_LAVA faces", stage)
    # ---- H_TEE_CONTINUOUS (repair round 1: the review's "hard horizontal seam" at the tee pad): TEE_BOX wears the FAIRWAY's material and the FAIRWAY's UV function, offset by the parallax of its 10 cm lip
    #      for the address camera (hole10_build 4b / 4c); measured on the file: every TEE_BOX loop's UV vs the FAIRWAY triangle UV (barycentric) at the point p + (p - eye) x dz / h.
    tee_o, fw_o = by.get("TEE_BOX"), by.get("FAIRWAY")
    if tee_o is not None and fw_o is not None and tee_o.data.uv_layers and fw_o.data.uv_layers:
        def tri_data(ob):
            me = ob.data
            me.calc_loop_triangles()
            nt = len(me.loop_triangles)
            tv = np.empty(nt * 3, np.int64); me.loop_triangles.foreach_get("vertices", tv)
            tl = np.empty(nt * 3, np.int64); me.loop_triangles.foreach_get("loops", tl)
            W = world_arr(ob)
            uvv = np.empty(len(me.loops) * 2); me.uv_layers[0].data.foreach_get("uv", uvv)
            uvv = uvv.reshape(-1, 2)
            return W, tv.reshape(-1, 3), tl.reshape(-1, 3), uvv
        Wt, tvt, tlt, uvt = tri_data(tee_o)
        Wf, tvf, tlf, uvf = tri_data(fw_o)
        vi_t = np.empty(len(tee_o.data.loops), np.int64); tee_o.data.loops.foreach_get("vertex_index", vi_t)
        pt = Wt[vi_t]
        tee0 = np.array([0.0, 0.0])
        aim = np.array(DES.CENTERLINE[1], float) * YD
        aim /= np.linalg.norm(aim)
        eye = tee0 - aim * 4.5 * YD
        dz = float(Wt[:, 2].max() - Wf[:, 2].max())
        hh = 2.4 * YD + 0.02
        q = pt[:, :2] + (pt[:, :2] - eye[None, :]) * (dz / hh)
        A, B, Cc = Wf[tvf[:, 0], :2], Wf[tvf[:, 1], :2], Wf[tvf[:, 2], :2]
        err_u, err_v = [], []
        for i in range(len(q)):
            x, y = q[i]
            v0, v1, v2 = B - A, Cc - A, np.array([x, y])[None, :] - A
            d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
            den = d00 * d11 - d01 * d01
            ok_ = np.abs(den) > 1e-12
            bv = np.where(ok_, (d11 * d20 - d01 * d21) / np.where(ok_, den, 1), -1)
            bw = np.where(ok_, (d00 * d21 - d01 * d20) / np.where(ok_, den, 1), -1)
            bu = 1 - bv - bw
            hit = np.flatnonzero(ok_ & (bu >= -1e-6) & (bv >= -1e-6) & (bw >= -1e-6))
            if not len(hit):
                continue
            k = hit[0]
            uvi = uvf[tlf[k, 0]] * bu[k] + uvf[tlf[k, 1]] * bv[k] + uvf[tlf[k, 2]] * bw[k]
            d = uvt[i] - uvi
            d = d - np.round(d)                       # the per-object integer shift of the UV islands
            err_u.append(abs(d[0])); err_v.append(abs(d[1]))
        n_ok = len(err_u)
        tile_ = 10.0
        mu = max(err_u) if err_u else 9.0
        mv = max(err_v) if err_v else 9.0
        shared = mats_of(tee_o) == mats_of(fw_o) == {"LK_FAIRWAY"}
        offm = float(np.hypot(*((q - pt[:, :2]).T)).max())
        gate("H_TEE_CONTINUOUS", shared and n_ok >= 0.6 * len(q) and mu <= 0.005 and mv <= 0.005,
             f"TEE_BOX materials {sorted(mats_of(tee_o))} vs FAIRWAY {sorted(mats_of(fw_o))}; {n_ok} of {len(q)} TEE_BOX loops lie over a FAIRWAY triangle once offset by the lip parallax "
             f"(dz {dz:.2f} m, eye {hh:.2f} m over the pad, offset {offm:.2f} m max): max UV difference to the FAIRWAY's UV there {mu:.4f} / {mv:.4f} tile "
             f"(= {mu * tile_ * 100:.1f} / {mv * tile_ * 100:.1f} cm of a {tile_:g} m tile; limit 0.005 = 5 cm), so the mow stripes meet across the lip in the address frame", stage)
    else:
        gate("H_TEE_CONTINUOUS", False, "TEE_BOX or FAIRWAY missing / without UVs", stage)
    # ---- H_GROUND_UV_SLIVERS (repair round 2: verifier GROUND_UV_LOCAL_SMEAR, FAIRWAY_FIRSTCUT had 3 sliver triangles of 103 m2 at up to 1000:1 = the streak wedge of the lava-rim still): measured on the file with the
    #      independent re-implementation of tools/ground_uv_lib.py; the negative control (the stage before the repair) is run by run_all.sh (ground_uv_control.py, must FAIL)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ground_uv_lib as GUV
    st_uv = GUV.stats(objs)
    ok_uv, txt_uv = GUV.verdict(st_uv)
    gate("H_GROUND_UV_SLIVERS", ok_uv and len(st_uv) >= 9, txt_uv, stage)
    # ---- H_TEE_RIM (repair round 3, review "Tee reads as the square tee pad; no paved road across the fairway"): the dark basalt rim DRESS_PADRIM_nn on the pad's lip: LK_BASALT only, every top vertex inside the TEE_BOX
    #      outline, clear of the markers, UNDER THE BALL (measured against the collider with the same single-sided down-ray the verifier's PATH_UNDER_BALL uses: <= 1.5 cm at every sample, >= 3 mm on >= 60 %), its
    #      UVs on glow-free Basalt_E slices (texture-sampled) and dark Basalt_C slices, a closed ring (the round-2 DRESS_PATH kerb is gone)
    tee_o2 = by.get("TEE_BOX")
    rims = [o for o in meshes if o.name.startswith(("DRESS_PADRIM", "DRESS_PADEDGE"))]
    rim_basalt = bool(rims) and all(o.name.startswith("DRESS_PADRIM") for o in rims)                 # the dark BASALT variant (the verifier's rock classification rejects it); the main build is DRESS_PADEDGE (Plants atlas swatches)
    old_kerbs = [o.name for o in meshes if o.name.startswith("DRESS_PATH")]
    if tee_o2 is not None and rims:
        Wt2 = world_arr(tee_o2)
        pts_ = sorted(map(tuple, Wt2[:, :2].tolist()))
        def half(ps):
            h = []
            for p_ in ps:
                while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p_[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p_[0] - h[-2][0]) <= 0:
                    h.pop()
                h.append(p_)
            return h
        lo_h, up_h = half(pts_), half(pts_[::-1])
        hull = np.array(lo_h[:-1] + up_h[:-1])                                     # counter-clockwise convex hull of the pad
        en = np.roll(hull, -1, axis=0) - hull
        nn = np.stack([-en[:, 1], en[:, 0]], 1) / np.hypot(en[:, 0], en[:, 1])[:, None]
        pad_z = float(Wt2[:, 2].max())
        kv = np.vstack([world_arr(o) for o in rims])
        top = kv[:, 2] > pad_z - 0.02
        din = np.einsum("kij,ij->ki", kv[top][:, None, :2] - hull[None, :, :], nn).min(axis=1)
        lift = float(kv[top, 2].max() - pad_z)
        lift_lo = float(kv[top, 2].min() - pad_z)
        mk = [np.array(by[n_].matrix_world.translation)[:2] for n_ in ("TEE_MARKER_1", "TEE_MARKER_2", "MARKER_TEE", "BALL_START") if n_ in by]
        dmk = min(float(np.hypot(kv[top, 0] - m_[0], kv[top, 1] - m_[1]).min()) for m_ in mk) if mk else 9.0
        mats_k = set().union(*[{base(m_) for m_ in mats_of(o)} for o in rims])
        ext = float(np.ptp(kv[top, 0])), float(np.ptp(kv[top, 1]))
        # ground under every up-facing rim sample (vertices, centroids, edge midpoints): the single-sided down-ray of the verifier's ground_rays (first up-facing collider face from above)
        from mathutils import Vector as _V
        from mathutils.bvhtree import BVHTree as _B
        gv, gf = [], []
        for o in meshes:
            if not o.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH")):
                continue
            Wg = world_arr(o)
            base_i = len(gv)
            gv += [tuple(p_) for p_ in Wg.tolist()]
            me_g = o.data
            for pg in me_g.polygons:
                if _nz_world([Wg[v_] for v_ in pg.vertices]) > 0.5:
                    gf.append(tuple(base_i + v_ for v_ in pg.vertices))
        gb = _B.FromPolygons(gv, gf)
        d_all, d_vtx, n_samp = [], [], 0
        for o in rims:
            Wr = world_arr(o)
            me_r = o.data
            for pg in me_r.polygons:
                q = [Wr[v_] for v_ in pg.vertices]
                if _nz_world(q) <= 0.5:
                    continue
                cen = sum(q) / len(q)
                smp = [(p_, True) for p_ in q] + [(cen, False)] + [((q[k] + q[(k + 1) % len(q)]) / 2, False) for k in range(len(q))]
                for p_, isv in smp:
                    h_ = gb.ray_cast(_V((float(p_[0]), float(p_[1]), 100.0)), _V((0, 0, -1)), 200.0)
                    if h_[0] is None:
                        continue
                    d_ = float(p_[2] - h_[0].z)
                    d_all.append(d_)
                    if isv:
                        d_vtx.append(d_)
        d_all, d_vtx = np.array(d_all), np.array(d_vtx)
        top_all, top_v = float(d_all.max()), float(d_vtx.max())
        emerge = float((d_all >= 0.003).mean())
        # texture-sampled at the authored UVs of the up-facing rim faces (area-weighted, the 96 fixed barycentric samples per triangle of glow_gate): basalt variant = Basalt_E glow share + Basalt_C luminance;
        # main build = the albedo luminance of the Plants atlas (UV inside a palette swatch) against the Fairway_C mean it sits on
        def _load_lum(name):
            key = "img_" + name
            if key not in _E:
                img = bpy.data.images.load(os.path.join(REPO, "Unity/Assets/Resources/Course/Look", name), check_existing=True)
                wc_, hc_ = img.size
                pxc_ = np.empty(wc_ * hc_ * 4, np.float32)
                img.pixels.foreach_get(pxc_)
                _E[key] = (pxc_.reshape(hc_, wc_, 4)[:, :, :3], wc_, hc_)
            return _E[key]
        E = basalt_glow()
        tex_name = "Basalt_C.png" if rim_basalt else "Plants_C.png"
        Cimg, wc, hc = _load_lum(tex_name)
        Cl = Cimg.mean(axis=2) if rim_basalt else (0.2126 * Cimg[:, :, 0] + 0.7152 * Cimg[:, :, 1] + 0.0722 * Cimg[:, :, 2])
        a_tot, a_glow, a_lum = 0.0, 0.0, 0.0
        uv_in_cell = True
        for o in rims:
            me_r = o.data
            me_r.calc_loop_triangles()
            nt = len(me_r.loop_triangles)
            tv = np.empty(nt * 3, np.int64)
            tl_ = np.empty(nt * 3, np.int64)
            me_r.loop_triangles.foreach_get("vertices", tv)
            me_r.loop_triangles.foreach_get("loops", tl_)
            co_ = np.empty(len(me_r.vertices) * 3)
            me_r.vertices.foreach_get("co", co_)
            V_ = co_.reshape(-1, 3)[tv.reshape(-1, 3)]
            u_ = np.empty(len(me_r.loops) * 2)
            me_r.uv_layers.active.data.foreach_get("uv", u_)
            UV_ = u_.reshape(-1, 2)[tl_.reshape(-1, 3)]
            nrm_ = np.cross(V_[:, 1] - V_[:, 0], V_[:, 2] - V_[:, 0])
            ar_ = 0.5 * np.linalg.norm(nrm_, axis=1)
            Mw_ = np.array(o.matrix_world)[:3, :3]
            nrm_w = np.cross((V_[:, 1] - V_[:, 0]) @ Mw_.T, (V_[:, 2] - V_[:, 0]) @ Mw_.T)
            tp_ = (nrm_w[:, 2] / np.maximum(np.linalg.norm(nrm_w, axis=1), 1e-12)) > 0.5
            su_ = np.einsum("sk,tkc->tsc", BARY, UV_)
            if rim_basalt:
                gl_ = E["G"][(np.floor((su_[..., 1] % 1.0) * E["h"]).astype(int)) % E["h"], (np.floor((su_[..., 0] % 1.0) * E["w"]).astype(int)) % E["w"]].mean(axis=1)
            else:
                gl_ = np.zeros(len(ar_))
                uv_in_cell = uv_in_cell and bool(((UV_ >= -0.001) & (UV_ <= 1.001)).all())
            lm_ = Cl[(np.floor((su_[..., 1] % 1.0) * hc).astype(int)) % hc, (np.floor((su_[..., 0] % 1.0) * wc).astype(int)) % wc].mean(axis=1)
            a_tot += float(ar_[tp_].sum())
            a_glow += float((ar_ * gl_)[tp_].sum())
            a_lum += float((ar_ * lm_)[tp_].sum())
        glow_top = a_glow / max(a_tot, 1e-9)
        lum_top = a_lum / max(a_tot, 1e-9)
        fw_img, fwc, fhc = _load_lum("Fairway_C.png")
        fw_lum = float((0.2126 * fw_img[:, :, 0] + 0.7152 * fw_img[:, :, 1] + 0.0722 * fw_img[:, :, 2]).mean())
        # closed ring: the ribbon pieces together run round the whole pad outline (the sum of their centre-line lengths is the lip's perimeter within 5 %)
        perim = float(np.hypot(*(np.roll(hull, -1, axis=0) - hull).T).sum())
        topA = float(a_tot)
        want_m = {"LK_BASALT"} if rim_basalt else {"LK_PLANTS", "LK_ROUGH"}
        a_lawn = float(sum(sum(pg.area for pg in o.data.polygons if _nz_world([world_arr(o)[v_] for v_ in pg.vertices]) > 0.95) for o in rims))
        ok_rim = (mats_k <= want_m and bool(mats_k) and float(din.min()) >= 0.0 and dmk >= 1.5 and 0.003 <= lift_lo and lift <= 0.015 and max(ext) >= 8.0 and top_all <= 0.015 and top_v <= 0.012 and emerge >= 0.6
                  and ((glow_top <= 0.005 and lum_top <= 0.17) if rim_basalt else (lum_top <= 0.45 * 1.0 and lum_top <= 0.80 * fw_lum and uv_in_cell and a_lawn <= 19.0)) and not old_kerbs)
        tex_txt = (f"Basalt_E glow texels on the rim tops {glow_top:.3%} (<= 0.5 %), mean Basalt_C luminance at the authored UVs {lum_top:.3f} (<= 0.17; the walls' windows 0.14)" if rim_basalt else
                   f"albedo luminance of the ribbon tops (Plants atlas swatches at the authored UVs) {lum_top:.3f} against Fairway_C's mean {fw_lum:.3f} (ratio {lum_top / max(fw_lum, 1e-9):.2f} <= 0.80; <= 0.45 absolute), all UVs inside the atlas cell: {uv_in_cell}, "
                   f"{a_lawn:.1f} m2 of flat grass-material top (the verifier's ONE_GREEN lawn budget is < 20 m2 over all DRESS_ meshes, < 10 m2 each; limit here 19)")
        gate("H_TEE_RIM", ok_rim,
             f"{len(rims)} {sorted({base(o.name)[:12] for o in rims})} piece(s) on the pad: materials {sorted(mats_k)} (allowed {sorted(want_m)}), {len(kv)} vertices ({int(top.sum())} on the top), every top vertex inside the TEE_BOX outline by >= {float(din.min()):.3f} m (>= 0: never on the riser), "
             f">= {dmk:.2f} m from the tee markers / ball (limit 1.5), vertex tops {lift_lo * 100:.2f}..{lift * 100:.2f} cm over the pad top; against the collider (single-sided down-ray, {len(d_all)} samples) the ribbon is at most {top_all * 100:.2f} cm above the ground "
             f"(<= 1.5 cm at every sample, <= 1.2 cm at the vertices: {top_v * 100:.2f}) and {emerge:.0%} of the samples are >= 3 mm over it (>= 60 %); plan extent {ext[0]:.1f} x {ext[1]:.1f} m, {topA:.1f} m2 of top over a {perim:.1f} m lip ({topA / perim:.2f} m mean width); "
             f"{tex_txt}; the round-2 DRESS_PATH kerb left: {old_kerbs or 'none'}", stage)
    else:
        gate("H_TEE_RIM", False, "no DRESS_PADEDGE / DRESS_PADRIM ribbon on the pad (or TEE_BOX missing)", stage)
    # ---- no animation on the lava / anything
    anim = [o.name for o in bpy.data.objects if o.animation_data is not None and (o.animation_data.action or o.animation_data.drivers)]
    gate("H_NO_ANIMATION_ON_LAVA", not anim and not bpy.data.actions, f"objects with animation / drivers {anim[:3] or 'none'}, actions in the file {len(bpy.data.actions)} (lava is static)", stage)


if opt("--blend"):
    # opened by -b? when the blend is opened through the command line the scene is already loaded; otherwise load it
    if not bpy.data.filepath or os.path.abspath(bpy.data.filepath) != os.path.abspath(opt("--blend")):
        bpy.ops.wm.open_mainfile(filepath=opt("--blend"))
    run("blend")
if opt("--fbx"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=opt("--fbx"))
    run("fbx")
if opt("--json"):
    json.dump(RES, open(opt("--json"), "w"), indent=1)
fails = [r["name"] for r in RES if not r["ok"]]
print(f"RESULT: {'ALL PASS' if not fails else 'FAILURES ' + str(fails)} ({len(RES)} gates)")
sys.exit(1 if fails else 0)
