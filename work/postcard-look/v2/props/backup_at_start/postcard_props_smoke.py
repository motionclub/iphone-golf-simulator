"""postcard_props_smoke: gates + contact sheet for postcard_props_lib (POSTCARD_LOOK role A4). Headless only:

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/postcard_props_smoke.py \
        -- [--no-render] [--no-holes] [--holes 08,09,10] [--scratch DIR]

1. Plants_C.png -> Unity/Assets/Resources/Course/Look/ (deterministic: two generations byte-identical, 256 x 256).
2. Library gates on every library mesh: face budgets, >= 6 unique rocks (no 12-vertex icosahedron), >= 4 basalt clusters made
   of vertical hex prisms, UVs (box projection at the contract tiles / inside the plant swatches / non-degenerate),
   materials (LK_PLANTS only on plants), names (section 2 prefixes, no collision prefix), no animation, determinism.
3. Contact sheet (EEVEE, the real Look/ textures, soft sun) -> ArtDir/screenshots/golf_postcards/look/props_sheet.png
4. Hole tests in a SCRATCH dir only (never writes blender/hole_NN.blend or the FBXs): P.start(design, out_dir=scratch) +
   build_terrain + build_play_surfaces + a full scatter (600 tufts + 40 shrubs + 80 flowers + 60 rocks): triangle budget,
   safety (rays against the real FAIRWAY/GREEN/TEE_BOX/BUNKER meshes over every prop footprint, pin clearance, land props
   on land), instancing (objects vs unique meshes), FBX writes each geometry once (scratch export, Geometry node count).
Prints GATE lines; exit code 1 when one fails.
"""
import sys
import os
import math
import time
import hashlib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import postcard_props_lib as PL  # noqa: E402
import postcard_lib as P  # noqa: E402

REPO = PL.REPO
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SCRATCH = os.path.abspath(ARGS[ARGS.index("--scratch") + 1]) if "--scratch" in ARGS else \
    os.path.join(REPO, "work", "postcard-look", "lib_props")
SHEET = os.path.join(REPO, "ArtDir", "screenshots", "golf_postcards", "look", "props_sheet.png")
HOLES = ARGS[ARGS.index("--holes") + 1].split(",") if "--holes" in ARGS else ["08", "09", "10"]
DO_RENDER = "--no-render" not in ARGS
DO_HOLES = "--no-holes" not in ARGS
os.makedirs(SCRATCH, exist_ok=True)

RESULTS = []
HOLE_PANELS = []


def gate(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(f"GATE: {name} {'PASS' if ok else 'FAIL'} {detail}", flush=True)


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    PL._COUNTERS.clear()
    PL.reset_scatter(None)


def mesh_hash(me):
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    return hashlib.sha256(np.round(co, 6).tobytes() + str([tuple(p.vertices) for p in me.polygons]).encode()).hexdigest()


def uv_array(me):
    lay = me.uv_layers.active
    uv = np.empty(len(me.loops) * 2)
    try:
        lay.uv.foreach_get("vector", uv)
    except Exception:
        lay.data.foreach_get("uv", uv)
    return uv.reshape(-1, 2)


# ----------------------------------------------------------------------------- 1 + 2: atlas and library gates
def library_gates():
    fresh()
    p1, h1 = PL.write_plants_atlas(os.path.join(SCRATCH, "Plants_C_a.png"))
    p2, h2 = PL.write_plants_atlas(os.path.join(SCRATCH, "Plants_C_b.png"))
    pr, hr = PL.write_plants_atlas()
    with open(pr, "rb") as f:
        head = f.read(24)
    w, h = int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
    gate("PLANTS_ATLAS", h1 == h2 == hr and (w, h) == (256, 256) and os.path.isfile(pr),
         f"{os.path.relpath(pr, REPO)} {w}x{h} sha {hr[:12]} (two generations identical: {h1 == h2})")

    lib = PL.ensure_library()
    for k in ("ROCK_BOULDER_A_WET", "ROCK_SLAB_A_WET", "ROCK_BLOCK_A_BASALT", "ROCK_BOULDER_B_BASALT"):
        lib[k] = PL.library_object(k)
    rep = PL.library_report()
    hashes = {k: mesh_hash(PL.library_object(k).data) for k in PL.BUILDERS}

    over = {k: v["faces"] for k, v in rep.items() if v["faces"] > 500}
    tufts = {k: rep[k]["faces"] for k in PL.TUFT_KINDS}
    gate("LIB_FACES", not over and max(tufts.values()) <= 120,
         f"{len(rep)} library meshes, max faces {max(v['faces'] for v in rep.values())} "
         f"(max tris {max(v['tris'] for v in rep.values())}), tufts {tufts}, over 500: {over or 'none'}")

    rocks = {k: rep[k] for k in PL.ROCK_KINDS}
    vmin = min(v["verts"] for v in rocks.values())
    frange = (min(v["faces"] for v in rocks.values()), max(v["faces"] for v in rocks.values()))
    ok_range = all(60 <= v["faces"] <= 500 for v in rocks.values())
    gate("ROCK_UNIQUE", len(set(hashes[k] for k in PL.ROCK_KINDS)) >= 6 and vmin > 12 and ok_range,
         f"{len(rocks)} unique rock meshes, min verts {vmin}, faces {frange[0]}..{frange[1]}")
    low = {k: rep[k]["verts"] for k in PL.ROCK_KINDS + PL.BASALT_KINDS + PL.WALL_KINDS if rep[k]["verts"] < 60}
    gate("ROCK_VERTS_60", not low, f"contract target >= 60 vertices per rock mesh: min "
         f"{min(rep[k]['verts'] for k in PL.ROCK_KINDS + PL.BASALT_KINDS + PL.WALL_KINDS)}; under 60: {low or 'none'}")
    ico = [k for k, v in rep.items() if k.startswith("ROCK_") and (v["verts"] <= 12 or (v["verts"], v["faces"]) == (12, 20))]
    gate("NO_ICOSAHEDRON", not ico, f"rock meshes with <= 12 verts: {ico or 'none'}")

    det = []
    for kind in list(PL.BASALT_KINDS) + list(PL.WALL_KINDS):
        me = PL.library_object(kind).data
        vert = sum(1 for pl in me.polygons if abs(pl.normal.z) < 0.02)
        tops = sum(1 for pl in me.polygons if pl.normal.z > 0.9)
        det.append((kind, vert, tops, vert / len(me.polygons)))
    cl_ok = sum(1 for k, v, t, s in det if k in PL.BASALT_KINDS and t >= 8 and s >= 0.6) >= 4
    wl_ok = all(v >= 60 and s >= 0.6 for k, v, t, s in det if k in PL.WALL_KINDS)
    gate("BASALT_COLUMNS", cl_ok and wl_ok and len(set(hashes[k] for k in PL.BASALT_KINDS)) >= 4,
         "; ".join(f"{k} {t} column tops, {v} vertical faces ({s:.0%})" for k, v, t, s in det))

    # UVs
    bad_tile, bad_deg, bad_sw = [], [], []
    for k, ob in sorted(lib.items()):
        me = ob.data
        uv = uv_array(me)
        mats = [m.name for m in me.materials]
        vidx, co, pol, nrm, mi = PL._loop_arrays(me)
        if k.startswith(("ROCK_", "DRESS_BLOCK")):
            tiles = [PL.TILE[m] for m in mats]
            exp = PL.box_uv_expected(me, tiles)
            err = float(np.abs(exp - uv).max())
            if err > 1e-4 or any(PL.TILE[m] != {"LK_ROCK": 4.0, "LK_ROCK_WET": 4.0, "LK_BASALT": 8.0, "LK_MASONRY": 4.0,
                                                "LK_ROUGH": 12.0}[m] for m in mats):
                bad_tile.append((k, err))
        # degenerate UV faces (fan triangulation area in UV)
        ls = np.zeros(len(me.polygons), np.int64)
        lt = np.zeros(len(me.polygons), np.int64)
        me.polygons.foreach_get("loop_start", ls)
        me.polygons.foreach_get("loop_total", lt)
        ndeg = 0
        for p in range(len(me.polygons)):
            a = uv[ls[p]]
            area = 0.0
            for j in range(1, lt[p] - 1):
                b, c = uv[ls[p] + j], uv[ls[p] + j + 1]
                area += abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2
            if area < 1e-9:
                ndeg += 1
        if ndeg:
            bad_deg.append((k, ndeg))
        if k.startswith("PLANT_"):
            for p in range(len(me.polygons)):
                pts = uv[ls[p]:ls[p] + lt[p]]
                cell = np.floor(pts * 4).astype(int)
                if (cell != cell[0]).any():
                    bad_sw.append((k, p))
                    break
                inner = (pts * 4 - cell)
                if (inner < PL.SW_MARGIN - 1e-6).any() or (inner > 1 - PL.SW_MARGIN + 1e-6).any():
                    bad_sw.append((k, p))
                    break
    gate("UV_TILE_UNITS", not bad_tile, f"box UV = object space / contract tile (rock 4, basalt 8, masonry 4, rough cap 12) on "
         f"{sum(1 for k in lib if k.startswith(('ROCK_', 'DRESS_BLOCK')))} meshes; bad: {bad_tile or 'none'}")
    gate("UV_NONDEGENERATE", not bad_deg, f"faces with zero UV area: {bad_deg or 'none'}")
    gate("UV_IN_SWATCH", not bad_sw, f"{sum(1 for k in lib if k.startswith('PLANT_'))} plant meshes, every face inside one "
         f"swatch {int(PL.SW_MARGIN * 64)} px inside its border; bad: {bad_sw or 'none'}")

    wrong = []
    for k, ob in lib.items():
        mats = [m.name for m in ob.data.materials]
        if k.startswith("PLANT_"):
            if mats != ["LK_PLANTS"]:
                wrong.append((k, mats))
        elif "LK_PLANTS" in mats:
            wrong.append((k, mats))
        elif k.startswith(("ROCK_BASALT", "ROCK_WALL")) and mats != ["LK_BASALT"]:
            wrong.append((k, mats))
        elif k.startswith("DRESS_BLOCK") and mats != ["LK_MASONRY"]:
            wrong.append((k, mats))
    gate("PLANTS_ONE_MATERIAL", not wrong, f"all {sum(1 for k in lib if k.startswith('PLANT_'))} plant meshes = [LK_PLANTS], no "
         f"other prop uses it; wrong: {wrong or 'none'}")
    return hashes, rep


# ----------------------------------------------------------------------------- 3: contact sheet
REF_MATS = {}


def ref_mat(name, rgb, emission=0.0, rough=0.8, image=None, alpha=None):
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    col = P.rgb(*rgb)
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = rough
    if image is not None:
        path = PL._look_path(image)
        if os.path.isfile(path):
            t = nt.nodes.new("ShaderNodeTexImage")
            t.image = bpy.data.images.load(path, check_existing=True)
            nt.links.new(t.outputs[0], b.inputs["Base Color"])
            if emission:
                nt.links.new(t.outputs[0], b.inputs["Emission Color"])
    if emission:
        if image is None:
            b.inputs["Emission Color"].default_value = col
        b.inputs["Emission Strength"].default_value = emission
    return m


def ref_box(name, x0, y0, z0, x1, y1, z1, mat, tile=4.0, top_mat=None):
    mb = PL._MB([mat] + ([top_mat] if top_mat else []))
    v = [mb.v(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        mb.f([v[i] for i in f], 0)
    mb.f([v[i] for i in (4, 5, 6, 7)], 1 if top_mat else 0)
    me = bpy.data.meshes.new(name)
    me.from_pydata(mb.V, [], mb.F)
    for mn in mb.mats:
        me.materials.append(bpy.data.materials[mn] if mn in bpy.data.materials else PL.lk_material(mn))
    me.polygons.foreach_set("material_index", np.array(mb.M, np.int32))
    me.update()
    lay = me.uv_layers.new(name="UVMap")
    uv = PL.box_uv_expected(me, [tile] * len(mb.mats))
    lay.uv.foreach_set("vector", uv.ravel())
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def ref_plane(name, cx, cy, z, sx, sy, mat, tile=12.0):
    return ref_box(name, cx - sx / 2, cy - sy / 2, z - 0.05, cx + sx / 2, cy + sy / 2, z, mat, tile)


def ref_figure(x, y, z=0.0, yaw=0.0):
    """1.7 m scale figure (capsule body + head)."""
    import bmesh
    me = bpy.data.meshes.new("REF_FIGURE")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.2, radius2=0.17, depth=1.3,
                          matrix=__import__("mathutils").Matrix.Translation((0, 0, 0.65)))
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.14,
                              matrix=__import__("mathutils").Matrix.Translation((0, 0, 1.56)))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(ref_mat("REF_FIGURE", (232, 70, 60), rough=0.5))
    ob = bpy.data.objects.new("REF_FIGURE", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (x, y, z)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def ref_cube(x, y, z=0.0):
    ob = ref_box("REF_CUBE_1M", x - 0.5, y - 0.5, z, x + 0.5, y + 0.5, z + 1.0, ref_mat("REF_CUBE", (225, 225, 230)).name)
    return ob


def label(text, loc, size, cam, color=(10, 12, 18)):
    cu = bpy.data.curves.new("REF_TXT", 'FONT')
    cu.body = text
    cu.size = size
    cu.align_x = 'CENTER'
    ob = bpy.data.objects.new("REF_TXT", cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = cam.rotation_euler.copy()
    ob.visible_shadow = False
    cu.materials.append(ref_mat("REF_TXT_%d_%d_%d" % color, color, emission=1.0))
    return ob


def title(cam, text, size=0.045):
    """Text pinned to the camera's top-left corner."""
    sc = bpy.context.scene
    fr = cam.data.view_frame(scene=sc)
    tl = min(fr, key=lambda v: (v.x - v.y))
    d = 3.0
    if cam.data.type == 'PERSP':
        tl = tl * (d / -tl.z)
    cu = bpy.data.curves.new("REF_TITLE", 'FONT')
    cu.body = text
    cu.size = size * d
    cu.align_x = 'LEFT'
    cu.align_y = 'TOP'
    ob = bpy.data.objects.new("REF_TITLE", cu)
    sc.collection.objects.link(ob)
    ob.parent = cam
    span = (max(v.x for v in fr) - min(v.x for v in fr)) * (d / -fr[0].z if cam.data.type == 'PERSP' else 1.0)
    ob.location = (tl.x + 0.015 * span, tl.y - 0.015 * span, -d)
    cu.size = size * span * 0.5
    ob.visible_shadow = False
    if cam.data.type == 'ORTHO':
        cu.size = size * cam.data.ortho_scale
    cu.materials.append(ref_mat("REF_TITLE", (255, 255, 255), emission=2.0))
    bg = bpy.data.curves.new("REF_TITLE_BG", 'FONT')
    return ob


def camera(name, loc, target, lens=35.0, ortho=None, clip=1500.0):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.clip_start = 0.1
    cam.data.clip_end = clip
    if ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho
    return cam


def setup_scene(res):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    try:
        sc.view_settings.view_transform = 'Standard'
    except Exception:
        pass
    for attr, val in (("taa_render_samples", 48), ("use_shadows", True), ("shadow_ray_count", 2), ("shadow_step_count", 6),
                      ("use_fast_gi", True), ("use_raytracing", False)):
        if hasattr(sc.eevee, attr):
            try:
                setattr(sc.eevee, attr, val)
            except Exception:
                pass
    w = bpy.data.worlds.new("REF_WORLD")
    sc.world = w
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = P.rgb(150, 190, 236)
    bg.inputs[1].default_value = 0.85
    for nm, en, rot, ang, col, sh in (("REF_SUN", 3.3, (48, 0, -32), 5.0, (1.0, 0.94, 0.84), True),
                                      ("REF_FILL", 0.6, (60, 0, 150), 30.0, (0.8, 0.88, 1.0), False)):
        L = bpy.data.lights.new(nm, 'SUN')
        L.energy = en
        L.angle = math.radians(ang)
        L.color = col
        try:
            L.use_shadow = sh
        except Exception:
            pass
        o = bpy.data.objects.new(nm, L)
        sc.collection.objects.link(o)
        o.rotation_euler = [math.radians(a) for a in rot]


def row(kinds, x0, y, gap, z=0.0, yaw=0.4, scale=1.0, cam=None, lab=0.0, labsize=0.25, labdy=0.0):
    """Place kinds left to right (by bbox width) starting at x0; returns (objs, x_end)."""
    objs = []
    x = x0
    for k in kinds:
        mn, mx = PL.lib_bbox(k)
        wdt = (mx.x - mn.x) * scale
        cx = x + wdt / 2 - (mn.x + mx.x) / 2 * scale
        ob = PL.place(None, k, (cx, y, z), yaw, scale)
        objs.append(ob)
        if cam is not None and lab:
            label(k.replace("PLANT_", "").replace("ROCK_", "").replace("DRESS_", ""), (x + wdt / 2, y + mn.y * scale - 0.2 - labdy, z + lab),
                  labsize, cam)
        x += wdt + gap
    return objs, x


def build_panels():
    """Every panel lives 3000 m from the next one; cameras clip at 1500 m. Returns [(camera, filename)]."""
    fresh()
    PL.write_plants_atlas()
    setup_scene((800, 500))
    rough = PL.lk_material("LK_ROUGH").name
    panels = []

    # ---- A rocks
    O = Vector((0, 0, 0))
    cam = camera("CAM_A", O + Vector((6.3, -16.0, 6.2)), O + Vector((6.3, 3.2, 0.5)), lens=27)
    ref_plane("REF_GROUND_A", 7, 4, 0.0, 80, 60, rough)
    row(["ROCK_STONE_A", "ROCK_STONE_B", "ROCK_CAIRN_A", "ROCK_BLOCK_A", "ROCK_BOULDER_B", "ROCK_BOULDER_A"], -4.0, 0.0, 1.2,
        cam=cam, lab=-0.05, labsize=0.42)
    ref_cube(13.6, 0.0)
    ref_figure(15.2, 0.2)
    label("1 m", (13.6, -0.8, -0.05), 0.42, cam)
    label("1.7 m", (15.2, -0.8, -0.05), 0.42, cam)
    row(["ROCK_SLAB_A", "ROCK_LEDGE_A", "ROCK_BOULDER_A_WET", "ROCK_BLOCK_A_BASALT"], -6.0, 6.5, 1.8, cam=cam, lab=-0.05,
        labsize=0.42, labdy=0.2)
    title(cam, "ROCKS  LK_ROCK / _WET / _BASALT twins  (1 m cube, 1.7 m figure)")
    panels.append((cam, "panel_a_rocks.png"))

    # ---- B sea stacks + waterfall
    O = Vector((3000, 0, 0))
    water = ref_mat("REF_WATER", (36, 104, 168), rough=0.15)
    ref_plane("REF_WATER_B", O.x + 10, O.y + 30, 0.0, 300, 300, water.name)
    cliff = ref_mat("REF_CLIFF", (90, 90, 92), image="Cliff_C")
    ref_box("REF_CLIFFBOX", O.x + 14, O.y + 12, -2.0, O.x + 32, O.y + 24, 6.0, cliff.name, 12.0, top_mat=rough)
    PL.place(None, "ROCK_SEASTACK_A", O + Vector((-2, 46, 0)), 0.3)
    PL.place(None, "ROCK_SEASTACK_B", O + Vector((8, 32, 0)), 1.9)
    PL.place_outcrop(None, O.x - 19, O.y + 36, 5.0, 6.4, seed=1)
    PL.build_masonry_arch(None, (O.x - 19, O.y + 36, 5.0), 10.0, span_m=6.5, height_m=10.0, seed=4, base_rock=False)
    top = (O.x + 25.0, O.y + 11.95, 5.65)
    PL.build_waterfall_sheet(None, top, (0, -1), width_m=3.0, foot_z=0.0, seed=1)
    foot = PL.waterfall_foot(top, (0, -1), 3.0)
    for i, (dx, k) in enumerate(((-5.0, "ROCK_BOULDER_A_WET"), (4.5, "ROCK_SLAB_A_WET"), (8.0, "ROCK_BOULDER_B_WET"))):
        PL.place(None, k, (top[0] + dx, top[1] - 2.5 - i, -0.4), i * 1.3, 1.1)
    ref_figure(O.x + 28, O.y + 16, 6.0)
    PL.hang_vines(None, [((O.x + 15 + 1.6 * i, O.y + 11.97, 5.98), (0, -1)) for i in range(5)] +
                  [((O.x + 27 + 1.3 * i, O.y + 11.97, 5.98), (0, -1)) for i in range(4)], seed=3)
    cam = camera("CAM_B", O + Vector((2.0, -30.0, 9.0)), O + Vector((6.0, 25.0, 7.0)), lens=30)
    label("SEASTACK_A 17 m", O + Vector((-2, 40, -1.5)), 1.1, cam, (255, 255, 255))
    label("SEASTACK_B 12 m", O + Vector((8, 28, -1.5)), 1.0, cam, (255, 255, 255))
    label("place_outcrop + arch", O + Vector((-19, 28, -1.5)), 1.0, cam, (255, 255, 255))
    label(f"WATER_FALL_00 (foot w {foot['width']:.1f} m)", O + Vector((25, 9.0, -1.2)), 0.8, cam, (255, 255, 255))
    title(cam, "SEA STACKS, OUTCROP + ARCH, WATERFALL SHEET (LK_FALL), CLIFF VINES")
    panels.append((cam, "panel_b_stacks_fall.png"))

    # ---- C basalt
    O = Vector((6000, 0, 0))
    lava = ref_mat("REF_LAVA", (255, 110, 30), emission=3.0, image="Lava_E")
    ref_plane("REF_LAVA_C", O.x, O.y + 20, -0.3, 300, 300, lava.name)
    PL.place(None, "ROCK_WALL_BASALT_A", O + Vector((-14, 52, 0)), 0.0)
    PL.place(None, "ROCK_WALL_BASALT_B", O + Vector((24, 58, 0)), 0.15)
    xs = [(-17, "ROCK_BASALT_A"), (-7.5, "ROCK_BASALT_B"), (1.5, "ROCK_BASALT_C"), (11.5, "ROCK_BASALT_D")]
    for x, k in xs:
        PL.place(None, k, O + Vector((x, 8, 0)), 0.2)
    ref_figure(O.x + 11.5, O.y + 7, 1.6)
    # pillar with a column skin (build_basalt_skin): grass disc top at 6 m
    import bmesh  # noqa
    n = 40
    loop = [(O.x + 24 + 7 * math.cos(math.tau * i / n), O.y + 14 + 6 * math.sin(math.tau * i / n)) for i in range(n)]
    mb = PL._MB([rough])
    ring_top = [mb.v((x, y, 6.0)) for x, y in loop]
    mb.f(ring_top, 0)
    me = bpy.data.meshes.new("REF_PILLAR_TOP")
    me.from_pydata(mb.V, [], mb.F)
    me.materials.append(bpy.data.materials[rough])
    lay = me.uv_layers.new(name="UVMap")
    lay.uv.foreach_set("vector", PL.box_uv_expected(me, [12.0]).ravel())
    obp = bpy.data.objects.new("REF_PILLAR_TOP", me)
    bpy.context.scene.collection.objects.link(obp)
    PL.build_basalt_skin(None, loop, 5.98, -1.5, col_r=1.0, seed=2, rows=2)
    ref_figure(O.x + 24, O.y + 14, 6.0)
    cam = camera("CAM_C", O + Vector((3.0, -30.0, 12.0)), O + Vector((4.0, 20.0, 7.0)), lens=24)
    for x, k in xs:
        label(k.replace("ROCK_", ""), O + Vector((x, 2.0, -0.3)), 0.9, cam, (255, 255, 255))
    label("build_basalt_skin (pillar)", O + Vector((24, 6.5, -0.3)), 0.9, cam, (255, 255, 255))
    label("WALL_BASALT_A / B (40 m, 36 m)", O + Vector((2, 40, 8)), 1.6, cam, (255, 255, 255))
    title(cam, "BASALT  hex-column clusters, wall segments, pillar skin (LK_BASALT + crack glow)")
    panels.append((cam, "panel_c_basalt.png"))

    # ---- D masonry
    O = Vector((9000, 0, 0))
    ref_plane("REF_GROUND_D", O.x, O.y + 10, 0.0, 120, 120, rough)
    a1 = PL.build_masonry_arch(None, (O.x - 8.5, O.y + 8.0, 0.9), 0.0, span_m=7.0, height_m=10.5, seed=1)
    a2 = PL.build_masonry_arch(None, (O.x + 4.5, O.y + 12.0, 0.0), 25.0, span_m=6.0, height_m=9.0, seed=2, broken=True)
    ru = PL.build_ruin(None, [(O.x + 11, O.y + 4), (O.x + 23, O.y + 4.5), (O.x + 25.5, O.y + 14)], seed=3, base_z=0.0,
                       doorway_at=0.3)
    ref_figure(O.x - 8.5, O.y + 4.5)
    ref_figure(O.x + 12.5, O.y + 2.0)
    cam = camera("CAM_D", O + Vector((4.0, -22.0, 6.5)), O + Vector((5.0, 9.0, 4.0)), lens=28)
    label("DRESS_ARCH_00 + vines + rock base", O + Vector((-8.5, 3.0, -0.2)), 0.7, cam)
    label("DRESS_ARCH_01 broken", O + Vector((4.5, 7.5, -0.2)), 0.7, cam)
    label("DRESS_RUIN_00 (door, fallen blocks)", O + Vector((18.5, 1.5, -0.2)), 0.7, cam)
    title(cam, f"MASONRY  arch {len(a1['arch'].data.polygons)} faces, broken arch, ruin ({sum(len(o.data.polygons) for o in ru['walls'])} faces)")
    panels.append((cam, "panel_d_masonry.png"))

    # ---- E plants
    O = Vector((12000, 0, 0))
    ref_plane("REF_GROUND_E", O.x + 4, O.y + 3, 0.0, 60, 40, rough)
    cam = camera("CAM_E", O + Vector((5.4, -9.4, 3.3)), O + Vector((5.4, 2.6, 0.8)), lens=26)
    row(["PLANT_TUFT_A", "PLANT_TUFT_B", "PLANT_TUFT_C", "PLANT_FLOWER_PURPLE", "PLANT_FLOWER_WHITE", "PLANT_FLOWER_YELLOW",
         "PLANT_AGAVE_A", "PLANT_AGAVE_B"], O.x - 0.6, O.y + 0.0, 0.45, cam=cam, lab=-0.02, labsize=0.15)
    row(["PLANT_SHRUB_A", "PLANT_SHRUB_B", "PLANT_SHRUB_C", "PLANT_PINE_A", "PLANT_TREE_A"], O.x - 0.6, O.y + 3.0, 0.7, cam=cam,
        lab=-0.02, labsize=0.16)
    ref_cube(O.x + 8.6, O.y + 0.2)
    ref_figure(O.x + 10.0, O.y + 0.3)
    wall = ref_box("REF_WALL_E", O.x - 1.5, O.y + 7.0, 0.0, O.x + 8.5, O.y + 8.0, 4.2, PL.lk_material("LK_MASONRY").name, 4.0)
    PL.hang_vines(None, [((O.x - 0.5 + i * 0.9, O.y + 6.98, 4.2), (0, -1)) for i in range(10)], seed=5)
    label("VINE S / M / L on a wall", (O.x + 3.5, O.y + 6.8, 4.35), 0.18, cam)
    title(cam, "PLANTS  one LK_PLANTS palette atlas: tufts, flowers, agave, shrubs, pine, tree, vines")
    panels.append((cam, "panel_e_plants.png"))

    # ---- F scatter patch (phone camera) + G same patch from above
    O = Vector((15000, 0, 0))
    ref_plane("REF_ROUGH_F", O.x, O.y + 40, 0.0, 70, 100, rough)
    fw = ref_mat("REF_FAIRWAY", (110, 196, 60), image="Fairway_C")
    ref_box("REF_FAIRWAY_F", O.x - 7.0, O.y - 10, 0.0, O.x + 7.0, O.y + 90, 0.14, fw.name, 10.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0427 * 1.6, location=(O.x + 1.5, O.y + 0.0, 0.2))
    ball = bpy.context.active_object
    ball.name = "REF_BALL"
    ball.data.name = "REF_BALL"
    ball.data.materials.append(ref_mat("REF_BALL", (250, 250, 250), rough=0.3))

    def off_fw(X, Y):
        return np.abs(np.asarray(X) - O.x) > 7.0 + 0.6

    def off_fw_big(X, Y):
        return np.abs(np.asarray(X) - O.x) > 7.0 + 2.0
    reg = PL.region_rect(O.x - 34, O.y - 8, O.x + 34, O.y + 88)
    rk = PL.scatter(None, ["ROCK_BOULDER_A", "ROCK_BOULDER_B", "ROCK_STONE_A", "ROCK_STONE_B", "ROCK_BLOCK_A", "ROCK_CAIRN_A"], 60,
                    region=reg, masks=[off_fw_big], seed=4, z=0.0)
    sh = PL.scatter(None, ["PLANT_SHRUB_A", "PLANT_SHRUB_B", "PLANT_SHRUB_C"], 40, region=reg, masks=[off_fw_big], seed=2, z=0.0)
    fl = PL.scatter(None, {"PLANT_FLOWER_PURPLE": 2, "PLANT_FLOWER_WHITE": 1, "PLANT_FLOWER_YELLOW": 1}, 80, region=reg,
                    masks=[off_fw], seed=3, z=0.0)
    tu = PL.scatter(None, {"PLANT_TUFT_A": 3, "PLANT_TUFT_B": 2, "PLANT_TUFT_C": 1}, 600, region=reg, masks=[off_fw], seed=1,
                    z=0.0)
    tris = 0
    for ob in rk + sh + fl + tu:
        ob.data.calc_loop_triangles()
        tris += len(ob.data.loop_triangles)
    YDm = P.YD
    cam = camera("CAM_F", O + Vector((1.5, -4.5 * YDm, 2.4 * YDm)), O + Vector((1.5, 1.5 * YDm + 6.0, 0.0)), lens=24)
    title(cam, f"SCATTER at the phone camera: {len(tu)} tufts, {len(sh)} shrubs, {len(fl)} flowers, {len(rk)} rocks = {tris} tris")
    panels.append((cam, "panel_f_scatter_phone.png"))
    cam = camera("CAM_G", O + Vector((-38.0, -30.0, 34.0)), O + Vector((0.0, 30.0, 0.0)), lens=30)
    title(cam, "SCATTER patch from above (fairway strip + 2 m margin kept clear by masks)")
    panels.append((cam, "panel_g_scatter_top.png"))

    # ---- H backdrop: cone + smoke + wall
    O = Vector((18000, 0, 0))
    ref_plane("REF_LAVA_H", O.x, O.y + 500, -0.3, 2400, 2400, lava.name)
    cone = PL.build_background_cone(None, (O.x + 40, O.y + 520, -8.0), seed=1, notch_deg=250)
    PL.build_smoke_cards(None, [((O.x + 10, O.y + 520, 70.0), 70.0, 90.0), ((O.x + 90, O.y + 540, 60.0), 50.0, 70.0),
                                ((O.x - 60, O.y + 480, 30.0), 40.0, 50.0)], face=(O.x, O.y - 60))
    PL.place(None, "ROCK_WALL_BASALT_C", O + Vector((-70, 220, 0)), 0.1)
    PL.place(None, "ROCK_WALL_BASALT_A", O + Vector((120, 260, 0)), -0.2)
    cam = camera("CAM_H", O + Vector((0.0, -60.0, 14.0)), O + Vector((20.0, 500.0, 55.0)), lens=32, clip=3000)
    title(cam, f"BACKDROP  DRESS_CONE ({len(cone.data.polygons)} faces, no undercut, rim notch), DRESS_SMOKE cards, basalt walls")
    panels.append((cam, "panel_h_backdrop.png"))

    # ---- I Plants_C atlas (emission plane, swatch names)
    O = Vector((21000, 0, 0))
    am = bpy.data.materials.new("REF_ATLAS")
    nt = am.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    outn = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(PL.PLANTS_PNG, check_existing=True)
    tx.interpolation = 'Closest'
    nt.links.new(tx.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], outn.inputs[0])
    mb = PL._MB(["REF_ATLAS"])
    q = [mb.v((O.x - 2, O.y - 2, 0), (0, 0)), mb.v((O.x + 2, O.y - 2, 0), (1, 0)), mb.v((O.x + 2, O.y + 2, 0), (1, 1)),
         mb.v((O.x - 2, O.y + 2, 0), (0, 1))]
    mb.f(q)
    me = bpy.data.meshes.new("REF_ATLAS")
    me.from_pydata(mb.V, [], mb.F)
    me.materials.append(am)
    lay = me.uv_layers.new(name="UVMap")
    lay.uv.foreach_set("vector", np.array([mb.UV[i] for i in (0, 1, 2, 3)], float).ravel())
    oa = bpy.data.objects.new("REF_ATLAS", me)
    bpy.context.scene.collection.objects.link(oa)
    cam = camera("CAM_I", O + Vector((1.3, 0.35, 10.0)), O + Vector((1.3, 0.35, 0.0)), ortho=7.6)
    cam.rotation_euler = (0.0, 0.0, 0.0)
    for i, (nm, col) in enumerate(PL.SWATCHES):
        c, r = i % 4, i // 4
        cx, cy = O.x - 2 + c + 0.5, O.y + 2 - r - 0.5
        lum = 0.3 * col[0] + 0.59 * col[1] + 0.11 * col[2]
        label(nm, (cx, cy - 0.38, 0.02), 0.13, cam, (20, 20, 20) if lum > 140 else (250, 250, 250))
    notes = ["Plants_C.png 256 x 256", "4 x 4 swatches of 64 px", "UV islands 6 px inside", "dark bottom -> light top",
             "PLANT_* = LK_PLANTS only", "written by write_plants_atlas()"]
    for k, t in enumerate(notes):
        lb = label(t, (O.x + 3.3, O.y + 1.4 - k * 0.5, 0.0), 0.17, cam, (250, 250, 250))
        lb.data.align_x = 'LEFT'
        lb.location.x = O.x + 2.2
    title(cam, "LK_PLANTS palette atlas (Plants_C.png)")
    panels.append((cam, "panel_i_atlas.png"))
    return panels


def render_panels(panels):
    sc = bpy.context.scene
    paths = []
    for cam, fn in panels:
        sc.camera = cam
        path = os.path.join(SCRATCH, fn)
        sc.render.filepath = path
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"rendered {fn} {time.time() - t:.1f}s", flush=True)
        paths.append(path)
    return paths


def compose_sheet(paths, out, cols=2):
    imgs = []
    for p in paths:
        im = bpy.data.images.load(p, check_existing=False)
        w, h = im.size
        px = np.array(im.pixels[:], np.float32).reshape(h, w, 4)[::-1, :, :3]
        imgs.append(px)
        bpy.data.images.remove(im)
    h, w = imgs[0].shape[:2]
    rows = (len(imgs) + cols - 1) // cols
    pad = 6
    sheet = np.full((rows * (h + pad) + pad, cols * (w + pad) + pad, 3), 0.12, np.float32)
    for i, im in enumerate(imgs):
        r, c = i // cols, i % cols
        sheet[pad + r * (h + pad):pad + r * (h + pad) + h, pad + c * (w + pad):pad + c * (w + pad) + w] = im
    data = PL._png_bytes(np.clip(np.round(sheet * 255), 0, 255).astype(np.uint8))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)
    return out, sheet.shape


# ----------------------------------------------------------------------------- 4: hole tests
def play_bvh():
    objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(("FAIRWAY", "GREEN", "TEE_BOX", "BUNKER"))]
    V, F = [], []
    for o in objs:
        mw = o.matrix_world
        base = len(V)
        V.extend([mw @ v.co for v in o.data.vertices])
        F.extend([[base + i for i in p.vertices] for p in o.data.polygons])
    return BVHTree.FromPolygons(V, F), [o.name for o in objs]


def hole_test(tag, lib_hashes):
    fresh()
    D = P.start(f"hole{tag}_design", out_dir=os.path.join(SCRATCH, f"hole{tag}"))
    t0 = time.time()
    P.build_terrain(D)
    P.build_play_surfaces(D)
    if tag == "10":
        P.build_water(D, 'WATER_LAVA', 'MAT_LAVA', shallow_material=None, foam_material=None, crest=False)
    else:
        P.build_water(D)
    t_build = time.time() - t0
    t0 = time.time()
    var = "BASALT" if tag == "10" else None          # crater: basalt twins in/at the lava
    rocks = PL.scatter_rocks(D, 30, zone="rim", seed=4, variant=var) + PL.scatter_rocks(D, 30, zone="sea", seed=5, variant=var)
    shrubs = PL.scatter(D, ["PLANT_SHRUB_A", "PLANT_SHRUB_B", "PLANT_SHRUB_C"], 40, region=PL.region_band(D, 0.6, 6.0), seed=2)
    flowers = PL.scatter(D, {"PLANT_FLOWER_PURPLE": 2, "PLANT_FLOWER_WHITE": 1, "PLANT_FLOWER_YELLOW": 1}, 80,
                         region=PL.region_band(D, 0.4, 10.0), seed=3)
    tufts = PL.scatter(D, {"PLANT_TUFT_A": 3, "PLANT_TUFT_B": 2, "PLANT_TUFT_C": 1}, 600, region=PL.region_band(D, 0.3, 14.0),
                       seed=1)
    t_sc = time.time() - t0
    props = rocks + shrubs + flowers + tufts
    tris = 0
    for ob in props:
        ob.data.calc_loop_triangles()
        tris += len(ob.data.loop_triangles)
    print(f"hole {tag}: terrain+play {t_build:.1f}s, scatter {t_sc:.1f}s: rocks {len(rocks)}, shrubs {len(shrubs)}, "
          f"flowers {len(flowers)}, tufts {len(tufts)}, tris {tris}", flush=True)
    # safety: rays against the real play meshes over every land prop footprint
    bvh, names = play_bvh()
    viol, in_water, pin_min = [], [], 1e9
    px, py = D.hole.pin[0] * P.YD, D.hole.pin[1] * P.YD
    for ob in props:
        x, y, z = ob.location
        pin_min = min(pin_min, math.hypot(x - px, y - py))
        if z < D.play_z - 1.0:
            continue
        mn, mx = PL.lib_bbox(ob.data.name)
        r = 0.45 * max((mx.x - mn.x) * ob.scale.x, (mx.y - mn.y) * ob.scale.y)
        pts = [(x, y)] + [(x + r * math.cos(a), y + r * math.sin(a)) for a in np.linspace(0, math.tau, 8, endpoint=False)]
        for qx, qy in pts:
            hit = bvh.ray_cast(Vector((qx, qy, D.play_z + 5.0)), Vector((0, 0, -1)), 20.0)
            if hit[0] is not None:
                viol.append((ob.name, round(qx, 1), round(qy, 1)))
                break
        if P.lie_codes_m(D, np.array([x]), np.array([y]))[0] == P.LIE_WATER:
            in_water.append(ob.name)
    gate(f"SCATTER_SAFE_{tag}", not viol and not in_water and pin_min >= 6.0,
         f"{len(props)} props; footprint rays hitting {len(names)} play meshes (fairway/first cut/green/apron/tee/bunker+lip): "
         f"{len(viol)} {viol[:3]}; land props standing in water: {len(in_water)}; nearest prop to the pin {pin_min:.1f} m (>= 6)")
    # instancing
    meshes = {ob.data.name for ob in props}
    libok = all(ob.data.get("lk_kind") == ob.data.name and bpy.data.objects.get(ob.data.name) is not None for ob in props)
    gate(f"INSTANCED_{tag}", libok and len(meshes) <= 30 and len(props) >= 10 * len(meshes),
         f"{len(props)} prop objects share {len(meshes)} library meshes (linked duplicates, every mesh is a hidden library mesh)")
    gate(f"HOLE_BUDGET_{tag}", tris <= 150000,
         f"placed {len(tufts)}/600 tufts + {len(shrubs)}/40 shrubs + {len(flowers)}/80 flowers + {len(rocks)}/60 rocks = {tris} tris (<= 150k)")
    # names + no animation
    bad = [ob.name for ob in props if not ob.name.startswith(PL.NAME_PREFIXES) or ob.name.startswith(PL.GROUND_PREFIXES)]
    gate(f"PROP_NAMES_{tag}", not bad, f"collision-prefix / non-section-2 names: {bad[:5] or 'none'}")
    # determinism: the rebuilt library equals the first build
    diff = [k for k in meshes if k in lib_hashes and mesh_hash(bpy.data.meshes[k]) != lib_hashes[k]]
    gate(f"DETERMINISTIC_{tag}", not diff, f"{len(meshes)} library meshes rebuilt in a fresh file are identical: {diff or 'yes'}")
    if DO_RENDER:
        P.build_cameras_and_light(D)
        cl = D.hole.center
        tgt = Vector((*P.m(*cl[len(cl) // 2]), D.play_z))
        if tag == "10":
            tgt = Vector((*P.m(*cl[-1]), D.play_z))
        cam = camera(f"CAM_HOLE{tag}", tgt + Vector((-34.0, -44.0, 30.0)), tgt + Vector((0.0, 4.0, 0.0)), lens=30, clip=3000)
        title(cam, f"hole {tag} (scratch, flat terrain): {len(tufts)} tufts, {len(shrubs)} shrubs, {len(flowers)} flowers, "
                   f"{len(rocks)} rocks = {tris} tris")
        sc = bpy.context.scene
        sc.render.resolution_x, sc.render.resolution_y = 800, 500
        sc.camera = cam
        sc.render.filepath = os.path.join(SCRATCH, f"panel_hole{tag}.png")
        try:
            sc.eevee.taa_render_samples = 32
        except Exception:
            pass
        bpy.ops.render.render(write_still=True)
        HOLE_PANELS.append(sc.render.filepath)
    # legacy swap: old hole-7 icosahedron instances -> library meshes filling the same local box
    P.import_rocks(D)
    legacy = P.scatter_rocks(D, count=10, zone="sea", seed=9) + P.scatter_rocks(D, count=6, zone="foot", seed=10)
    legacy.append(P.place_rock(D, "CLIFF", (P.m(-60, 150)[0], P.m(-60, 150)[1], -2.0), scale=(0.4, 0.4, 1.2)))
    bpy.context.view_layer.update()

    def box_world(o):
        co = np.array([v.co[:] for v in o.data.vertices])
        mn, mx = co.min(0), co.max(0)
        cs = [Vector((x, y, z)) for x in (mn[0], mx[0]) for y in (mn[1], mx[1]) for z in (mn[2], mx[2])]
        return np.array([(o.matrix_world @ c)[:] for c in cs])
    before = {o.name: box_world(o) for o in legacy}
    names_before = [o.name for o in legacy]
    objs_before = list(legacy)
    swapped = PL.swap_legacy_rocks(D, objs=objs_before, basalt=(tag == "10"))
    bpy.context.view_layer.update()
    err = max(float(np.abs(box_world(o) - before[nb]).max()) for o, nb in zip(objs_before, names_before))
    left = [o.name for o in bpy.data.objects if o.type == 'MESH' and o.data is not None and len(o.data.vertices) == 12
            and o.name.startswith(("ROCK", "CLIFF")) and not any(c.name == PL.LIB_COLLECTION for c in o.users_collection)]
    kinds = sorted({o.data.name for o in swapped})
    gate(f"LEGACY_SWAP_{tag}", len(swapped) == len(objs_before) and err < 0.02 and not left
         and all(o.name.startswith("ROCK_") for o in swapped),
         f"{len(swapped)}/{len(objs_before)} icosahedron instances -> {kinds}; local box kept (max corner error {err * 1000:.1f} mm); "
         f"12-vertex rocks left: {len(left)}")
    for o in swapped:
        bpy.data.objects.remove(o, do_unlink=True)
    # FBX: each shared geometry written once
    if tag == HOLES[0]:
        vl = bpy.context.view_layer
        for o in vl.objects:
            o.select_set(False)
        for o in props:
            o.select_set(True)
        path = os.path.join(SCRATCH, f"props_test_{tag}.fbx")
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'}, axis_forward='-Z', axis_up='Y',
                                 apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_anim=False,
                                 use_mesh_modifiers=True, add_leaf_bones=False, path_mode='STRIP', embed_textures=False)
        with open(path, "rb") as f:
            blob = f.read()
        ngeo = blob.count(b"\x00\x01Geometry")
        nmodel = blob.count(b"\x00\x01Model")
        gate("FBX_GEOMETRY_ONCE", ngeo == len(meshes),
             f"{os.path.basename(path)}: {ngeo} Geometry nodes for {len(meshes)} unique meshes, {nmodel} Model nodes, "
             f"{len(blob) // 1024} KB")
    return dict(tris=tris, props=len(props), meshes=len(meshes))


def main():
    t = time.time()
    hashes, rep = library_gates()
    # budget worst case (library maxima, independent of placement)
    tri = {k: v["tris"] for k, v in rep.items()}
    worst = (600 * max(tri[k] for k in PL.TUFT_KINDS) + 40 * max(tri[k] for k in ("PLANT_SHRUB_A", "PLANT_SHRUB_B", "PLANT_SHRUB_C")) +
             80 * max(tri[k] for k in ("PLANT_FLOWER_PURPLE", "PLANT_FLOWER_WHITE", "PLANT_FLOWER_YELLOW")) +
             60 * max(tri[k] for k in PL.ROCK_KINDS if not k.startswith("ROCK_SEASTACK")))
    gate("SCATTER_BUDGET_WORST", worst <= 150000, f"600 x max tuft + 40 x max shrub + 80 x max flower + 60 x max rock = {worst} tris")
    if DO_RENDER:
        panels = build_panels()
        # gates on the panel scene props
        cone = bpy.data.objects.get("DRESS_CONE")
        me = cone.data
        co = np.array([v.co[:] for v in me.vertices])
        sides = 28
        rings = (len(co) - sides) // sides
        R = np.hypot(co[:rings * sides, 0] - (18040), co[:rings * sides, 1] - 520).reshape(rings, sides)
        Z = co[:rings * sides, 2].reshape(rings, sides)
        under = int((np.diff(R, axis=0) > 1e-6).sum())
        fold = int((np.diff(Z, axis=0) <= 0).sum())
        gate("CONE_NO_UNDERCUT", under == 0 and fold == 0 and len(me.polygons) <= 500,
             f"DRESS_CONE {len(me.polygons)} faces, {rings} rings x {sides}: radius growing upward {under}, z folds {fold}")
        fall = next(o for o in bpy.data.objects if o.name.startswith("WATER_FALL_"))
        uv = uv_array(fall.data)
        vidx = PL._loop_arrays(fall.data)[0]
        zc = np.array([fall.data.vertices[i].co.z for i in vidx])
        order = np.argsort(-zc)
        mono = np.all(np.diff(uv[order, 1][np.argsort(-zc[order], kind="stable")]) >= -1e-6)
        dn = np.mean([pl.normal.dot(Vector((0, -1, 0))) for pl in fall.data.polygons])
        gate("WATERFALL_SHEET", fall.data.materials[0].name == "LK_FALL" and abs(uv[:, 1].min()) < 1e-6 and
             abs(uv[:, 1].max() - 1) < 1e-6 and mono and dn > 0.5 and not fall.name.startswith(PL.GROUND_PREFIXES),
             f"{fall.name}: LK_FALL, v 0 (top) .. 1 (foot) monotone {mono}, mean normal . out_dir {dn:.2f}, "
             f"{len(fall.data.polygons)} faces, foot = {PL.waterfall_foot((3025.0, 11.95, 5.65), (0, -1), 3.0)}")
        skins = [o for o in bpy.data.objects if o.name.startswith("ROCK_SKIN_BASALT")]
        vs = np.array([(o.matrix_world @ v.co)[:] for o in skins for v in o.data.vertices])
        ell = ((vs[:, 0] - 6024.0) / 7.0) ** 2 + ((vs[:, 1] - 14.0) / 6.0) ** 2
        gate("BASALT_SKIN_INSIDE", skins and float(ell.max()) <= 1.0 and float(vs[:, 2].max()) <= 5.98 + 1e-6
             and max(len(o.data.polygons) for o in skins) <= 500,
             f"{len(skins)} skin meshes ({sum(len(o.data.polygons) for o in skins)} faces, max {max(len(o.data.polygons) for o in skins)}"
             f" per object) stay inside the pillar outline (max ellipse value {float(ell.max()):.3f} <= 1) and under its top "
             f"(max z {float(vs[:, 2].max()):.3f} <= 5.98)")
        arch = bpy.data.objects.get("DRESS_ARCH_00")
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(arch.data)
        comps, seen = 0, set()
        for v in bm.verts:
            if v.index in seen:
                continue
            comps += 1
            stack = [v]
            while stack:
                q = stack.pop()
                if q.index in seen:
                    continue
                seen.add(q.index)
                stack.extend(e.other_vert(q) for e in q.link_edges)
        bm.free()
        vines = [o for o in bpy.data.objects if o.name.startswith("PLANT_VINE") and o.location.x < 9000 - 3 and o.location.x > 9000 - 20]
        gate("MASONRY_ARCH", comps >= 25 and len(arch.data.polygons) <= 500 and len(vines) >= 6,
             f"DRESS_ARCH_00: {comps} separate cut blocks (piers, voussoirs, keystone, haunches, mortar core), "
             f"{len(arch.data.polygons)} faces, {len(vines)} hanging vines, rock base + fallen blocks")
        ruins = [o for o in bpy.data.objects if o.name.startswith("DRESS_RUIN_")]
        rfaces = [len(o.data.polygons) for o in ruins]
        gate("MASONRY_RUIN", ruins and max(rfaces) <= 500 and sum(rfaces) / 5 >= 20,
             f"{len(ruins)} ruin wall meshes, {sum(rfaces)} faces (~{sum(rfaces) // 5} blocks), max {max(rfaces)} per object")
        names = [o.name for o in bpy.data.objects if not o.name.startswith(("REF_", "CAM_")) and o.type == 'MESH']
        names += [m.name for m in bpy.data.meshes if not m.name.startswith("REF_")]
        bad = [n for n in names if not n.startswith(PL.NAME_PREFIXES) or n.startswith(PL.GROUND_PREFIXES + ("FLAG", "HOLE_CUP",
                                                                                                             "BALL_START", "MARKER_"))]
        gate("NAMES_SECTION2", not bad, f"{len(names)} prop objects + meshes, bad: {bad[:6] or 'none'}")
        anim = [o.name for o in bpy.data.objects if o.animation_data is not None] + [a.name for a in bpy.data.actions]
        gate("NO_ANIMATION", not anim, f"objects with animation data / actions: {anim or 'none'}")
        paths = render_panels(panels)
    if DO_HOLES:
        for tag in HOLES:
            hole_test(tag, hashes)
    if DO_RENDER:
        out, shape = compose_sheet(paths + HOLE_PANELS, SHEET, cols=3)
        gate("PROPS_SHEET", os.path.isfile(out), f"{os.path.relpath(out, REPO)} {shape[1]}x{shape[0]} ({len(paths) + len(HOLE_PANELS)} panels)")
    fails = [r for r in RESULTS if not r[1]]
    print(f"SUMMARY: {len(RESULTS) - len(fails)}/{len(RESULTS)} gates PASS in {time.time() - t:.1f}s", flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    if "--no-exit" not in ARGS:
        os._exit(code)
