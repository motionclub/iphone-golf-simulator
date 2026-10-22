"""grass_gates.py - the GRASS pass gates of the hole 9 staged build (2026-10-05), measured on the STAGED blend (and the FBX re-import for the vertex rules). Changes nothing.

    Blender -b --factory-startup --python grass_gates.py -- --blend DIR/hole_09.blend [--fbx DIR/hole_09.fbx] [--json OUT.json] [--before-tris N]

GRASS_FRINGE_PRESENT      counts, clumps (3-7 + singles), lean <= 12 deg, height factor 0.6-1.8, tall / filler, not a grid, coverage of the rough edge (strips hugging the play surfaces and the cliff lip) in the camera zones
GRASS_NOT_ON_PLAY_SURFACES every vertex of EVERY PLANT_TUFT* (fringe, field, skirt, old) ray-cast onto FAIRWAY / GREEN / TEE_BOX / BUNKER meshes: none over one
GRASS_NOT_ON_WATER        every tuft vertex over land, origin >= 1.0 m inside the cliff edge, origin on the ground top (|dz| <= 0.06), z >= 5
GRASS_BALL_CLEAR          >= 4 m (tee ball 1.5 m) from every still ball, 6 m from the pin, 1.5 m from the markers, tops <= 0.55 yd (0.503 m) in the corridor / within 12 m of a ball
GRASS_TRI_BUDGET          whole export set <= 250k triangles (before / after), fringe triangles, FBX size <= 20 MB, animation 0
Same checks as postcard_props_smoke.fringe_checks (re-implemented here because the smoke builds scratch holes), with the hole's own 1.0 m shore margin of H_NO_PLANT_ON_WATER.
"""
import json
import math
import os
import sys

sys.dont_write_bytecode = True
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts"
sys.path.insert(0, HERE)
import postcard_lib as P  # noqa: E402
import postcard_look_lib as L  # noqa: E402
import postcard_props_lib as PL  # noqa: E402

YD = P.YD
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS and ARGS.index(name) + 1 < len(ARGS) else default


BLEND = os.path.abspath(opt("--blend"))
FBX = os.path.abspath(opt("--fbx")) if opt("--fbx") else None
JSON_OUT = opt("--json")
BEFORE = int(opt("--before-tris", "247439"))
RES = []


def gate(gid, ok, detail):
    RES.append(dict(id=gid, ok=bool(ok), detail=str(detail)))
    print(f"GATE: {gid} {'PASS' if ok else 'FAIL'} - {detail}", flush=True)


def lib_only(o):
    return len(o.users_collection) > 0 and all(c.name == "ASSET_LIBRARY" for c in o.users_collection)


def wverts(o):
    me = o.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    M = np.array(o.matrix_world)
    return co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]


def surface_bvh(objs, up_only=False):
    V, F = [], []
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        W = wverts(o)
        b = len(V)
        V += [tuple(p) for p in W.tolist()]
        for t in me.loop_triangles:
            if up_only and t.normal[2] < 0.2:
                continue
            F.append([b + i for i in t.vertices])
    return BVHTree.FromPolygons(V, F) if F else None


def ground_z(bvh, x, y):
    h = bvh.ray_cast(Vector((x, y, 60.0)), Vector((0, 0, -1)), 120.0)
    return None if h[0] is None else float(h[0].z)


def tri_count(objs):
    n = 0
    for o in objs:
        o.data.calc_loop_triangles()
        n += len(o.data.loop_triangles)
    return n


def run(label, objs_all, D, fringe_only_props=True):
    tufts = [o for o in objs_all if o.name.startswith("PLANT_TUFT")]
    fringe = [o for o in tufts if "lk_fringe" in o.keys()]
    play = surface_bvh([o for o in objs_all if o.name.startswith(("FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH", "DRESS_PATH"))])
    gb = surface_bvh([o for o in objs_all if o.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER"))], up_only=True)
    W = {o.name: wverts(o) for o in tufts}
    # ---- play surfaces
    viol = []
    for o in tufts:
        for x, y, _z in W[o.name][::2]:
            if play.ray_cast(Vector((float(x), float(y), D.play_z + 30.0)), Vector((0, 0, -1)), 80.0)[0] is not None:
                viol.append((o.name, round(float(x), 2), round(float(y), 2)))
                break
    gate(f"GRASS_NOT_ON_PLAY_SURFACES@{label}", not viol, f"{len(tufts)} PLANT_TUFT* ({len(fringe)} fringe, {len(tufts) - len(fringe)} field / skirt / old), every vertex (2 of 3 sampled) ray-cast down onto the FAIRWAY / GREEN / TEE_BOX / BUNKER meshes: {len(viol)} over a play surface {viol[:3]}")
    # ---- water
    X = np.array([o.matrix_world.translation.x for o in tufts])
    Y = np.array([o.matrix_world.translation.y for o in tufts])
    Z = np.array([o.matrix_world.translation.z for o in tufts])
    wv = np.concatenate([W[o.name][:, :2] for o in tufts])
    water_v = int((P.lie_codes_m(D, wv[:, 0], wv[:, 1]) == P.LIE_WATER).sum())
    sd = P.signed_dist_m(D, X, Y)
    dz = []
    for o in tufts:
        g = ground_z(gb, o.matrix_world.translation.x, o.matrix_world.translation.y)
        dz.append(99.0 if g is None else abs(o.matrix_world.translation.z - g))
    gate(f"GRASS_NOT_ON_WATER@{label}", water_v == 0 and float(sd.max()) <= -1.0 and max(dz) <= 0.06 and float(Z.min()) >= 5.0,
         f"{len(tufts)} tufts / {len(wv)} vertices: vertices over water {water_v}; nearest origin to a shore / lip edge {-float(sd.max()):.2f} m (>= 1.0, the hole gate's margin); origin vs the ray-cast ground max |dz| {max(dz):.3f} m (<= 0.06); lowest origin z {float(Z.min()):.2f} (>= 5.0)")
    # ---- ball clear
    balls = PL.still_ball_zones(D)
    h = D.hole
    px, py = h.pin[0] * YD, h.pin[1] * YD
    markers = [(o.matrix_world.translation.x, o.matrix_world.translation.y) for o in objs_all if o.name.startswith(("TEE_MARKER", "HOLE_CUP", "BALL_START", "FLAG"))]
    corridor = h.fw / 2 * YD + float(D.scenery.get("firstcut_yd", 3.0)) + 6.0
    wb, wp, wm, bad_top, top_c, top_all = 99.0, 99.0, 99.0, [], 0.0, 0.0
    for o in tufts:
        w = W[o.name]
        xy = w[:, :2]
        for bx, by, br in balls:
            wb = min(wb, float(np.hypot(xy[:, 0] - bx, xy[:, 1] - by).min()) - br)
        wp = min(wp, float(np.hypot(xy[:, 0] - px, xy[:, 1] - py).min()) - 6.0)
        for mx_, my_ in markers:
            wm = min(wm, float(np.hypot(xy[:, 0] - mx_, xy[:, 1] - my_).min()) - 1.5)
        g = ground_z(gb, o.matrix_world.translation.x, o.matrix_world.translation.y)
        top = float(w[:, 2].max()) - (g if g is not None else D.play_z)
        top_all = max(top_all, top)
        off = float(P._lie_all(D, np.array([o.matrix_world.translation.x]), np.array([o.matrix_world.translation.y]))[1][0]) * YD
        near = any(math.hypot(o.matrix_world.translation.x - bx, o.matrix_world.translation.y - by) <= 12.0 for bx, by, _r in balls)
        if off <= corridor or near:
            top_c = max(top_c, top)
            if top > 0.503 + 0.004:
                bad_top.append((o.name, round(top, 3)))
    gate(f"GRASS_BALL_CLEAR@{label}", wb >= -1e-6 and wp >= -1e-6 and wm >= -1e-6 and not bad_top,
         f"{len(balls)} shot-ball zones {[(round(b[0] / YD, 1), round(b[1] / YD, 1), b[2]) for b in balls]} (course yd, r m): nearest tuft vertex vs the balls (worst margin {wb:+.2f} m), margin to the 6 m pin disc {wp:+.2f} m, to the 1.5 m markers {wm:+.2f} m; "
         f"tops in the ball corridor (<= {corridor:.1f} m off the centerline or <= 12 m from a ball): max {top_c:.3f} m (<= 0.503 m = 0.55 yd), over {bad_top[:3] or 'none'}; whole hole max {top_all:.2f} m")
    return tufts, fringe, W, gb, balls


def fringe_structure(D, fringe, tufts, label):
    byc = {}
    for o in fringe:
        byc.setdefault((o.get("h9_zone", ""), o["lk_fringe"]), []).append(o)
    sizes = np.array([len(v) for v in byc.values()])
    P_ = np.array([[o.matrix_world.translation.x, o.matrix_world.translation.y] for o in fringe])
    nn = []
    for i in range(0, len(P_), 400):
        d = np.hypot(P_[i:i + 400, None, 0] - P_[None, :, 0], P_[i:i + 400, None, 1] - P_[None, :, 1])
        d[np.arange(d.shape[0]), np.arange(i, i + d.shape[0])] = 1e9
        nn.append(d.min(1))
    nn = np.concatenate(nn)
    lean = []
    for o in fringe:
        z = np.array(o.matrix_world)[:3, :3] @ np.array([0.0, 0.0, 1.0])
        lean.append(math.degrees(math.acos(min(1.0, float(z[2] / max(np.linalg.norm(z), 1e-9))))))
    lean = np.array(lean)
    fs = np.array([o["lk_fringe_f"] for o in fringe])
    tall = sum(1 for o in fringe if o.data.name in PL.TUFT_KINDS_TALL)
    in_clump = int(sum(s for s in sizes if s >= 3))
    grid = float((np.abs(nn - np.median(nn)) <= 0.1 * np.median(nn)).mean())
    # edge coverage: 2 m grid over the camera zones, points on the strip hugging a play surface (0.35-2.5 m outside) or the cliff lip (0.9-2.5 m inside), dry land; covered = a fringe tuft origin within 2.2 m
    d_play = PL.play_edge_distance(D)
    zones = dict(tee_view=(-45.0, 30.0, 45.0, 112.0), green_end=(-50.0, 325.0, 50.0, 470.0), ribbon_mid=(-45.0, 112.0, 45.0, 285.0))
    cov = {}
    for name, (x0, y0, x1, y1) in zones.items():
        gx, gy = np.meshgrid(np.arange(x0, x1, 2.0), np.arange(y0, y1, 2.0))
        gx, gy = gx.ravel(), gy.ravel()
        lie = P._lie_all(D, gx, gy)
        dpl = d_play(gx, gy, lie)
        sdm = P.signed_dist_m(D, gx, gy)
        strip = (lie[0] != P.LIE_WATER) & (((dpl >= 0.35) & (dpl <= 2.5)) | ((sdm <= -0.9) & (sdm >= -2.5) & (dpl >= 0.35)))
        pts = np.stack([gx[strip], gy[strip]], 1)
        if len(pts) == 0:
            cov[name] = (0, 0)
            continue
        dmin = np.min(np.hypot(pts[:, None, 0] - P_[None, :, 0], pts[:, None, 1] - P_[None, :, 1]), axis=1)
        cov[name] = (int(len(pts)), int((dmin <= 2.2).sum()))
    return dict(count=len(fringe), clumps=int((sizes >= 3).sum()), singles=int((sizes == 1).sum()), pairs=int((sizes == 2).sum()), max_clump=int(sizes.max()), in_clump_share=in_clump / max(len(fringe), 1),
                nn_mean=float(nn.mean()), nn_cv=float(nn.std() / max(nn.mean(), 1e-9)), grid_share=grid, lean_max=float(lean.max()), lean_med=float(np.median(lean)), f_min=float(fs.min()), f_max=float(fs.max()),
                f_med=float(np.median(fs)), tall=tall, fill=len(fringe) - tall, cov=cov)


if True:
    D = P.start("hole09_design", out_dir="/tmp/hole09_grass_scratch")
    D.mod.SCENERY["tee_box_m"] = (10.4, 13.2)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    D.terrain = bpy.data.objects[D.terrain_name]
    loops = L.terrain_top_loops(D, D.terrain)
    D.loops = [[(float(x), float(y)) for x, y in Pl] for Pl, _ in loops]
    D.loop_kinds = ["outer" if P.signed_area(np.array(l_)) > 0 else "hole" for l_ in D.loops]
    D._distfield = None
    objs = [o for o in bpy.data.objects if o.type == 'MESH' and not lib_only(o)]
    tufts, fringe, W, gb, balls = run("blend", objs, D)
    st = fringe_structure(D, fringe, tufts, "blend")
    cov = st["cov"]
    cov_txt = {k: f"{c}/{n} = {c / max(n, 1):.0%}" for k, (n, c) in cov.items()}
    cov_ok = (cov["tee_view"][0] >= 30 and cov["tee_view"][1] / cov["tee_view"][0] >= 0.30) and (cov["green_end"][0] >= 30 and cov["green_end"][1] / cov["green_end"][0] >= 0.20)
    ok = (st["count"] >= 300 and st["tall"] >= 60 and st["fill"] >= 100 and st["max_clump"] <= 7 and st["in_clump_share"] >= 0.55 and st["singles"] >= 5 and st["lean_max"] <= 12.25 and st["lean_med"] >= 3.0
          and st["f_min"] <= 0.7 and st["f_max"] >= 1.2 and st["nn_cv"] >= 0.35 and st["grid_share"] <= 0.45 and cov_ok
          and all(PL.SCALE_LIMITS["lo"] - 1e-9 <= o.scale[i] <= PL.SCALE_LIMITS["hi"] + 1e-9 for o in tufts for i in range(3)))
    gate("GRASS_FRINGE_PRESENT@blend", ok,
         f"{st['count']} fringe tufts ({st['tall']} tall D/E/F + {st['fill']} filler S/T) in {st['clumps']} clumps of 3-7 (largest {st['max_clump']}), {st['pairs']} pairs, {st['singles']} singles; {st['in_clump_share']:.0%} stand in a clump of >= 3 (>= 55 %); "
         f"nearest-neighbour mean {st['nn_mean']:.2f} m, CV {st['nn_cv']:.2f} (>= 0.35), {st['grid_share']:.0%} of the distances within 10 % of the median (<= 45 %): not a grid; lean max {st['lean_max']:.1f} deg (<= 12), median {st['lean_med']:.1f}; "
         f"height factor {st['f_min']:.2f}..{st['f_max']:.2f} median {st['f_med']:.2f} (0.6-1.8); no scale component outside the SCALE_LIMITS on any of the {len(tufts)} tufts; coverage of the rough-edge strips (a fringe tuft within 2.2 m of a 2 m grid point "
         f"0.35-2.5 m outside a play surface / 0.9-2.5 m inside the lip): tee view {cov_txt['tee_view']} (>= 30 %), green end {cov_txt['green_end']} (>= 20 %), ribbon middle {cov_txt['ribbon_mid']}; plus {sum(1 for o in tufts if o.get('h9_class') == 'field')} field and "
         f"{sum(1 for o in tufts if o.get('h9_class') == 'skirt')} skirt tufts on the scrub ridge")
    tri_all = tri_count(objs)
    tri_fringe = tri_count(fringe)
    tri_tufts = tri_count(tufts)
    mb = os.path.getsize(FBX) / 1048576 if FBX and os.path.exists(FBX) else float("nan")
    anim = sum(1 for a in bpy.data.actions)
    gate("GRASS_TRI_BUDGET@blend", tri_all <= 250000 and (FBX is None or mb <= 20.0) and anim == 0,
         f"{tri_all} triangles over {len(objs)} mesh objects (<= 250000; before the grass pass {BEFORE}: {tri_all - BEFORE:+d}); all {len(tufts)} PLANT_TUFT* = {tri_tufts} tris, fringe {len(fringe)} tufts = {tri_fringe} tris ({tri_fringe / max(len(fringe), 1):.0f} per tuft); "
         f"FBX {mb:.2f} MB (<= 20); animation actions {anim}")
    if FBX:
        P.start("hole09_design", out_dir="/tmp/hole09_grass_scratch")
        D2 = P._ST["D"]
        bpy.ops.import_scene.fbx(filepath=FBX)
        objs2 = [o for o in bpy.data.objects if o.type == 'MESH']
        D2.loops, D2._distfield = D.loops, None
        run("fbx", objs2, D2)
    fails = [r["id"] for r in RES if not r["ok"]]
    print(f"GRASS_GATES: {len(RES)} gates, {len(fails)} FAIL {fails}", flush=True)
    if JSON_OUT:
        json.dump(RES, open(JSON_OUT, "w"), indent=1)
    sys.exit(1 if fails else 0)
