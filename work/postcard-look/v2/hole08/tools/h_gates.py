"""Numbers for the H_* gates that need Blender: rock vertices / stretch / plants on water / budgets / feature counts, at the BLEND stage and on the FBX re-import.
usage: Blender -b --factory-startup --python h_gates.py -- STAGED.blend STAGED.fbx OUT.json"""
import sys, os, json, math, re
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy, numpy as np
from mathutils import Vector
import postcard_check as PC
import postcard_props_lib as PL
import hole08_design as DES
HOLE = PC.Hole(DES)
YD = 0.9144
blend, fbx, out = sys.argv[sys.argv.index("--") + 1:][:3]
res = {}


def stage_numbers(stage):
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and not any(c.name == "ASSET_LIBRARY" for c in o.users_collection)]
    r = {}
    rocks = [o for o in obs if o.name.startswith(("ROCK_", "CLIFF_ROCK")) and not o.name.startswith("ROCK_SKIN")]
    wv = {}
    for o in rocks:
        k = o.data.name
        if k not in wv:
            wv[k] = (PL.welded_vertex_count(o.data), len(o.data.polygons))
    r["rocks"] = dict(objects=len(rocks), unique_meshes=len(wv), min_welded_verts=min(v[0] for v in wv.values()), min_faces=min(v[1] for v in wv.values()),
                      verts_by_mesh={k: v[0] for k, v in sorted(wv.items())}, twelve_vertex_rocks=[k for k, v in wv.items() if v[0] <= 12])
    # stretch: singular values of the 3x3 of every ROCK_/DRESS_BLOCK instance
    sc_min, sc_max, ratio, viol = 9.0, 0.0, 0.0, []
    for o in obs:
        if not o.name.startswith(("ROCK_", "DRESS_BLOCK", "CLIFF_ROCK")) or o.name.startswith("ROCK_SKIN"):
            continue
        sv = np.linalg.svd(np.array(o.matrix_world)[:3, :3], compute_uv=False)
        sc_min, sc_max, ratio = min(sc_min, sv.min()), max(sc_max, sv.max()), max(ratio, sv.max() / sv.min())
        if sv.min() < 0.5 - 1e-6 or sv.max() > 2.0 + 1e-6 or sv.max() / sv.min() > 2.0 + 1e-6:
            viol.append((o.name, [round(float(x), 3) for x in sv]))
    r["stretch"] = dict(instances=sum(1 for o in obs if o.name.startswith(("ROCK_", "DRESS_BLOCK", "CLIFF_ROCK")) and not o.name.startswith("ROCK_SKIN")),
                        min=float(sc_min), max=float(sc_max), max_ratio=float(ratio), violations=viol)
    # plants
    plants = [o for o in obs if o.name.startswith("PLANT_")]
    on_water, low, on_path = [], [], 0
    outcrop_water_lie = []          # plants whose xy is Water in the scoring mirror but which stand on the arch outcrop top (rock above the sea): kept apart, reported by name
    crown_water_lie = []            # round 8: ... or on the crown of a sea stack / spire (z >= 5 m, the stack's own surface under the base)
    vine_low = 99.0
    lowest_plant = 99.0
    for o in plants:
        if o.name.startswith("PLANT_VINE"):
            Vv = np.array([v.co[:] for v in o.data.vertices]).reshape(-1, 3) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world.translation)
            vine_low = min(vine_low, float(Vv[:, 2].min()))
            continue
        V = np.array([v.co[:] for v in o.data.vertices]).reshape(-1, 3) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world.translation)
        x, y, z = float(o.matrix_world.translation.x), float(o.matrix_world.translation.y), float(V[:, 2].min())
        if z < 5.0:                                            # round 3: this list was declared but never filled in round 2 (the gate text claimed 'lowest plant base >= 5.0 m')
            low.append((o.name, round(z, 3)))
        lowest_plant = min(lowest_plant, z)
        lie = HOLE.lie_at((x / YD, y / YD))
        if lie == PC.WATER:                                   # the arch outcrop stands in the sea: a plant over water must have an outcrop top right under its base
            sc_ = bpy.context.scene
            dg = bpy.context.evaluated_depsgraph_get()
            o_ = Vector((x, y, z + 3.0))
            sup = None
            for _ in range(40):
                okh, loc, nrm, idx, hob, mw_ = sc_.ray_cast(dg, o_, Vector((0, 0, -1)), distance=12.0)
                if not okh:
                    break
                if hob.name.startswith(("PLANT_", "DRESS_BLOCK")):
                    o_ = loc + Vector((0, 0, -1e-3))
                    continue
                sup = (hob.name, loc.z)
                break
            if sup and sup[0].startswith("ROCK_OUTCROP") and abs(sup[1] - z) < 0.25:
                outcrop_water_lie.append((o.name, round(sup[1], 3), round(z, 3)))
            elif sup and sup[0].startswith(("ROCK_SEASTACK", "ROCK_SPIRE")) and abs(sup[1] - z) < 0.25 and z >= 5.0:      # round 8: the tufts on the grass crown of a sea stack (a rock that stands in the sea)
                crown_water_lie.append((o.name, round(sup[1], 3), round(z, 3)))
            else:
                on_water.append((o.name, sup))
    r["plants"] = dict(objects=len(plants), non_vine=len([p for p in plants if not p.name.startswith("PLANT_VINE")]), vines=len([p for p in plants if p.name.startswith("PLANT_VINE")]),
                       on_water_by_lie=on_water, crown_water_lie=dict(count=len(crown_water_lie), support_top_z_min=min((a for _n, a, _b in crown_water_lie), default=None), lowest_base_z=min((b for _n, _a, b in crown_water_lie), default=None)),
                       outcrop_water_lie=dict(count=len(outcrop_water_lie), kinds={k: sum(1 for n, _a, _b in outcrop_water_lie if n.startswith(k)) for k in sorted({n.split('.')[0].rsplit('_', 1)[0] for n, _a, _b in outcrop_water_lie})}, support_top_z=sorted({a for _n, a, _b in outcrop_water_lie}), lowest_base_z=min((b for _n, _a, b in outcrop_water_lie), default=None)), lowest_base_below_5m=low, lowest_plant_base_z=lowest_plant, lowest_vine_vertex_z=vine_low, materials=sorted({m.name for o in plants for m in o.data.materials if m}),
                       unique_meshes=len({o.data.name for o in plants}), max_faces=max((len(o.data.polygons) for o in plants), default=0))
    # foam / water / ground names
    r["foam"] = dict(foam_objects=[o.name for o in obs if "FOAM" in o.name.upper()], mat_foam=sorted({m.name for o in obs for m in o.data.materials if m and m.name.startswith("MAT_FOAM")}),
                     surf_objects=len([o for o in obs if o.name.startswith("WATER_SURF")]))
    # prefixes
    allowed = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER")
    r["names"] = dict(ground=sorted(o.name for o in obs if o.name.startswith(allowed + ("CART_PATH",))),
                      collider_named_scenery=[o.name for o in obs if o.name.startswith(("ROCK_", "PLANT_", "DRESS_", "WATER_")) and o.name.startswith(allowed + ("CART_PATH",))],
                      cart_path=[o.name for o in obs if o.name.startswith("CART_PATH")])
    # clearance round the gameplay markers: nearest vertex of any plant / rock / masonry object to the pin (MARKER_PIN / HOLE_CUP / FLAG) and the tee markers (TEE_MARKER_1/2, BALL_START)
    marks = {o.name: np.array(o.matrix_world.translation) for o in bpy.data.objects if o.name in ("MARKER_PIN", "HOLE_CUP", "FLAG", "FLAG_POLE", "TEE_MARKER_1", "TEE_MARKER_2", "BALL_START", "MARKER_TEE")}
    near = {}
    for o in obs:
        if not o.name.startswith(("PLANT_", "ROCK_", "DRESS_ARCH", "DRESS_BLOCK")):
            continue
        V = np.array([v.co[:] for v in o.data.vertices]).reshape(-1, 3) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world.translation)
        for mn, mp in marks.items():
            d = float(np.hypot(V[:, 0] - mp[0], V[:, 1] - mp[1]).min())
            if mn not in near or d < near[mn][0]:
                near[mn] = (d, o.name)
    r["marker_clearance_m"] = {k: [round(v[0], 2), v[1]] for k, v in near.items()}
    tris = 0
    for o in obs:
        o.data.calc_loop_triangles(); tris += len(o.data.loop_triangles)
    mats = {}
    for o in obs:
        for m in o.data.materials:
            if m: mats[m.name] = mats.get(m.name, 0) + 1
    r["budget"] = dict(tris_every_object=tris, mesh_objects=len(obs), unique_mesh_datablocks=len({o.data.name for o in obs}), materials=sorted(mats))
    r["materials_non_lk"] = sorted(m for m in mats if not m.startswith("LK_"))
    # feature counts
    r["features"] = dict(arch_objects=[o.name for o in obs if o.name.startswith("DRESS_ARCH")], waterfall=[o.name for o in obs if o.name.startswith("WATER_FALL")],
                         paths=[o.name for o in obs if o.name.startswith("DRESS_PATH")], fallen_blocks=len([o for o in obs if o.name.startswith("DRESS_BLOCK")]),
                         stacks=len([o for o in obs if re.match(r"^ROCK_(SEASTACK|SPIRE)_[A-E]?(_WET)?\.\d+$", o.name) or re.match(r"^ROCK_(SEASTACK_[A-E]|SPIRE_A)(_WET)?\.\d+$", o.name)]),
                         skins=len([o for o in obs if o.name.startswith("ROCK_SKIN")]), shelf=[o.name for o in obs if o.name.startswith("WATER_SHELF")],
                         ocean=[o.name for o in obs if o.name.startswith("WATER_OCEAN")], sand_materials=sorted({m.name for o in obs if o.name.startswith("BUNKER") for m in o.data.materials if m}))
    return r


bpy.ops.wm.open_mainfile(filepath=blend)
bpy.context.view_layer.update()
res["blend"] = stage_numbers("blend")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
bpy.context.view_layer.update()
res["fbx"] = stage_numbers("fbx")
res["fbx_bytes"] = os.path.getsize(fbx)
# the tee path in the tee camera (CameraRig.FrameAddress, 900x1600, 60 degrees vertical): share of the path's length that is inside the frame and not hidden
def tee_path_visibility():
    import postcard_lib as P
    bpy.ops.wm.open_mainfile(filepath=blend)
    bpy.context.view_layer.update()
    import hole08_look as K
    paths = [o for o in bpy.data.objects if o.name.startswith("DRESS_PATH")]
    ground = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER"))]
    occ = K.bvh_of_objects([o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(("ROCK_", "PLANT_", "DRESS_ARCH", "DRESS_BLOCK")) and not any(c.name == "ASSET_LIBRARY" for c in o.users_collection)])
    gb = K.bvh_of_objects(ground)
    ball = Vector((0.0, 0.0, 6.24)); aim = Vector((19 * YD, 178 * YD, 0.0)); dv = Vector((aim.x, aim.y, 0)).normalized()
    cam = ball - dv * 4.5 * YD + Vector((0, 0, 2.4 * YD)); look = ball + dv * 1.5 * YD
    f = (look - cam).normalized(); r = f.cross(Vector((0, 0, 1))).normalized(); u = r.cross(f).normalized()
    tv = math.tan(math.radians(30.0)); th = tv * 900 / 1600
    tot = vis = inframe = 0
    for p in K.PATHS[:1]:
        pts = [Vector((x * YD, y * YD, 0.0)) for x, y in p["pts"]]
        # dense polyline (linear is enough for a visibility share)
        for a, b in zip(pts[:-1], pts[1:]):
            for t in np.linspace(0, 1, 40, endpoint=False):
                q = a + (b - a) * t
                h = gb.ray_cast(Vector((q.x, q.y, 20.0)), Vector((0, 0, -1)), 40.0)
                if h[0] is None:
                    continue
                q = Vector((q.x, q.y, h[0].z + 0.02))
                v = q - cam; z = v.dot(f)
                tot += 1
                if z <= 0.3 or abs(v.dot(r) / (z * th)) > 1 or abs(v.dot(u) / (z * tv)) > 1:
                    continue
                inframe += 1
                d = q - cam
                hit = occ.ray_cast(cam, d.normalized(), d.length - 0.05)
                hg = gb.ray_cast(cam, d.normalized(), d.length - 0.1)
                if hit[0] is None and hg[0] is None:
                    vis += 1
    return dict(samples=tot, in_frame=inframe, visible=vis)


res["tee_path"] = tee_path_visibility()
# hole 8 course lies of the shot positions
import hole08_look as K0
_pb = (float(K0.PATHBALL_YD[0]), float(K0.PATHBALL_YD[1]))
res["pathball_yd"] = _pb
res["lies"] = {k: HOLE.lie_at(v) for k, v in dict(tee=(0.0, 0.0), M=(19.0, 178.0), pathball=_pb, pin=(-6.0, 340.0)).items()}
# tuft heights (world bbox height of every PLANT_TUFT_* instance) and the distance from the two address balls to the nearest path vertex
bpy.ops.wm.open_mainfile(filepath=blend)
bpy.context.view_layer.update()
th = []
groups = {"carpet": [], "fringe": [], "outcrop_fringe": [], "crown": []}
from mathutils.bvhtree import BVHTree
_gv, _gf = [], []
for _o in bpy.data.objects:
    if _o.type == 'MESH' and _o.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER")):
        _M = np.array(_o.matrix_world); _co = np.array([v.co[:] for v in _o.data.vertices]).reshape(-1, 3) @ _M[:3, :3].T + _M[:3, 3]
        _o.data.calc_loop_triangles(); _b = len(_gv); _gv += [tuple(q) for q in _co.tolist()]; _gf += [tuple(_b + i for i in t.vertices) for t in _o.data.loop_triangles]
_gbvh = BVHTree.FromPolygons(_gv, _gf)
fringe_top = []                                  # round 8: the EXACT top of a pad-fringe tuft above the ground under its origin (what GRASS_BALL_CLEAR caps at 0.503 m); the bbox height below also counts the sunk base and the lean
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith("PLANT_TUFT") and not any(c.name == "ASSET_LIBRARY" for c in o.users_collection):
        M = np.array(o.matrix_world); V = np.array([v.co[:] for v in o.data.vertices]).reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        h_ = float(V[:, 2].max() - V[:, 2].min())
        th.append(h_)
        grp = "fringe" if "lk_fringe" in o.keys() else ("outcrop_fringe" if "lk_outcrop_fringe" in o.keys() else ("crown" if "lk_shrub_tuft" in o.keys() else "carpet"))
        groups[grp].append(h_)
        if grp == "fringe":
            _h = _gbvh.ray_cast(Vector((o.location.x, o.location.y, 60.0)), Vector((0, 0, -1)), 200.0)
            fringe_top.append(float(V[:, 2].max()) - float(_h[0].z))
th = np.array(th)
res["tufts"] = dict(count=int(len(th)), median_m=float(np.median(th)), p95_m=float(np.percentile(th, 95)), max_m=float(th.max()))
# round 8: the tufts by group (the old carpet keeps the round-2 height gate; the pad fringe is held by GRASS_BALL_CLEAR; the island and crown tufts stand where no ball lies)
res["fringe_top_above_ground"] = dict(count=len(fringe_top), max_m=float(max(fringe_top)), p95_m=float(np.percentile(fringe_top, 95)), median_m=float(np.median(fringe_top)))
res["tuft_groups"] = {k: (dict(count=len(v), median_m=float(np.median(v)), p95_m=float(np.percentile(v, 95)), max_m=float(max(v))) if v else dict(count=0)) for k, v in groups.items()}
pv = np.vstack([np.array([v.co[:] for v in o.data.vertices]).reshape(-1, 3) @ np.array(o.matrix_world)[:3, :3].T + np.array(o.matrix_world.translation)
                for o in bpy.data.objects if o.name.startswith("DRESS_PATH") and o.type == 'MESH'])
res["ball_to_path_m"] = {k: float(np.hypot(pv[:, 0] - x * YD, pv[:, 1] - y * YD).min()) for k, (x, y) in dict(tee=(0.0, 0.0), M=(19.0, 178.0)).items()}
json.dump(res, open(out, "w"), indent=1, default=str)
print("H_JSON", out)
