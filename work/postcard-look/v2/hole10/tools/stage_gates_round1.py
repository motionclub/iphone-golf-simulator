"""Hole 10 stage gates that need no postcard_lib handle: they run on an opened staged .blend OR on a re-imported FBX.

  Blender -b --factory-startup --python stage_gates.py -- --blend STAGE/hole_10.blend [--fbx STAGE/hole_10.fbx] [--json OUT.json]
  Blender -b --factory-startup --python stage_gates.py -- --fbx STAGE/hole_10.fbx            (FBX stage only)

Prints `GATE: <ID>@<stage> PASS|FAIL - <numbers>`; exit 1 on a FAIL. Stage `blend` = the objects postcard_lib.export_fbx exports (every MESH/EMPTY
outside the hidden ASSET_LIBRARY collection), stage `fbx` = every object of the FBX re-imported into an empty scene.
Gates: H_NO_12_VERTEX_ROCK, H_NO_STRETCH_2X, H_NO_FOAM_STRIP, H_BUDGET, H_NEW_PREFIXES, H_WALL_RING, H_STACKS, H_RUBBLE, H_LAVA_LIGHTS, H_ROCK_CHUNKING,
H_BACKDROP, H_NO_COLLIDER_PROPS, H_NO_ANIMATION_ON_LAVA.
"""
import sys
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
    # ---- H_WALL_RING: library towers / segments between r_inner and r_outer, none an icosahedron, terraced heights
    wr = SC["wall_ring"]
    r0, r1 = wr["r_inner"] * YD, wr["r_outer"] * YD
    towers = [o for o in meshes if base(o.name).startswith("ROCK_WALL_BASALT_")]
    rr, tops = [], []
    for o in towers:
        w = world_arr(o)
        c = w.mean(0)
        rr.append(math.hypot(c[0] - cx, c[1] - cy))
        tops.append(float(w[:, 2].max()))
    inband = sum(1 for r in rr if r0 - 14.0 <= r <= r1 + 14.0)
    oldnames = [o.name for o in meshes if re.match(r"^(ROCK_WALL_(FLAT|BLUNT)|CLIFF_ROCK|ROCK_(SMALL|MEDIUM|LARGE))(\.\d+)?$", o.name)]
    ang = np.zeros(72, bool)
    for o, r in zip(towers, rr):
        w = world_arr(o)
        a0, a1 = np.degrees(np.arctan2(w[:, 1] - cy, w[:, 0] - cx)).min(), np.degrees(np.arctan2(w[:, 1] - cy, w[:, 0] - cx)).max()
        c = w.mean(0)
        ac = math.degrees(math.atan2(c[1] - cy, c[0] - cx))
        hw = 0.5 * float(np.hypot(*(w.max(0) - w.min(0))[:2])) / max(r, 1.0) * 180 / math.pi
        for b in range(72):
            mid = -180 + (b + 0.5) * 5
            d = (mid - ac + 180) % 360 - 180
            if abs(d) <= hw:
                ang[b] = True
    gate("H_WALL_RING", len(towers) >= 120 and inband >= 0.97 * len(towers) and not oldnames and tops and 14.0 <= min(tops) and max(tops) <= 60.0 and ang.mean() >= 0.95,
         f"{len(towers)} library basalt towers/segments (ROCK_WALL_BASALT_*), {inband} within {r0 - 14:.0f}..{r1 + 14:.0f} m of the crater centre ({r0:.0f}..{r1:.0f} m = 295..355 yd), "
         f"tops {min(tops):.1f}..{max(tops):.1f} m above the lava, covering {ang.mean():.0%} of the ring's 360 deg; legacy ROCK_WALL_FLAT/BLUNT/CLIFF_ROCK/ROCK_SMALL.. objects: {oldnames[:3] or 'none'}", stage)
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
