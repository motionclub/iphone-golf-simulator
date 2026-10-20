"""Red-team mutations for postcard_look_verify.py (reviewer scratch; writes ONLY under work/postcard-look/review_gates/).

Blender -b --factory-startup --python rt_mutate.py -- <hole> <outdir>
Starts from the A5 synthetic positive st/hole_0N_pos.blend (passes every gate at blend + FBX), applies ONE change per
variant, saves <outdir>/hole_0N_<name>.blend + .fbx (+ baseline .meta copy) and writes <outdir>/hole_0N_manifest.json
(name, expected-fail gates, kind = required | redteam, look dir to use).
"""
import sys
sys.dont_write_bytecode = True
import os, json, math, shutil, importlib.util
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix

REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
RG = os.path.join(REPO, "work/postcard-look/review_gates")
ST = os.path.join(RG, "st")
spec = importlib.util.spec_from_file_location("plv", os.path.join(REPO, "blender/scripts/postcard_look_verify.py"))
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)

argv = sys.argv[sys.argv.index("--") + 1:]
HOLE = int(argv[0])
OUT = argv[1]
os.makedirs(OUT, exist_ok=True)
TAG = f"{HOLE:02d}"
POS = os.path.join(ST, f"hole_{TAG}_pos.blend")
LOOK = os.path.join(ST, "Look")
SIG = json.load(open(os.path.join(REPO, f"work/postcard-look/baseline_signature/hole_{TAG}.json")))
MAN = []


def ctx():
    return V.st_ctx(HOLE, dict(look_dir=LOOK))


def root():
    return bpy.data.objects.get(f"HOLE_{TAG}_ROOT")


def add(name, me, loc=(0, 0, 0), scale=(1, 1, 1), coll="ENVIRONMENT"):
    return V.st_obj(name, me, loc, scale, root=root(), coll=coll)


def pin_xy():
    p = bpy.data.objects["MARKER_PIN"].matrix_world.translation
    return float(p.x), float(p.y)


def ico_mesh(name, split=False, extra_vertex=False, mat="LK_ROCK", scale=1.0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=scale)   # Blender 5: subdivisions=1 -> 12 verts / 20 faces
    if split:
        bmesh.ops.split_edges(bm, edges=list(bm.edges))
    if extra_vertex:
        bm.verts.new((0.0, 0.0, 0.0))
    return V.st_bm_mesh(name, bm, mat)


def swap_geometry(me_name, new_me):
    """Replace mesh datablock me_name's geometry users with new_me fitted to the old bbox (keeps instancing)."""
    old = bpy.data.meshes[me_name]
    V.st_fit(new_me, old)
    for ob in list(bpy.data.objects):
        if ob.type == "MESH" and ob.data == old:
            ob.data = new_me


def water_point(C, far=30.0):
    """A point in open water near the shore (outside dry land), metres."""
    P, N = V.st_shore_frame(C, 4.0)
    i = len(P) // 3
    return float(P[i][0] + N[i][0] * far), float(P[i][1] + N[i][1] * far)


def rough_point(C, S):
    rng = np.random.default_rng(5)
    sp = V.st_candidates(C, S, 1, rng)
    return sp[0]


def save(name, expect, kind, note, look=LOOK):
    for ob in bpy.data.objects:
        if ob.parent is None and root() is not None and ob is not root() and ob.type in ("MESH", "EMPTY") and \
                any(c.name in V.EXPORT_COLLECTIONS for c in ob.users_collection):
            ob.parent = root()
    blend = os.path.join(OUT, f"hole_{TAG}_{name}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend, copy=True)
    fbx = os.path.join(OUT, f"hole_{TAG}_{name}.fbx")
    V.st_export(HOLE, fbx)
    MAN.append(dict(name=name, expect=expect, kind=kind, note=note, blend=blend, fbx=fbx, look=look))
    print(f"MUTANT {name} saved", flush=True)


def fresh():
    bpy.ops.wm.open_mainfile(filepath=POS, load_ui=False)
    V.IMG_CACHE.clear()
    if "_ground_rays" in V.Snap.__dict__:
        pass
    return ctx()


def look_copy(name, edit):
    """A copy of the synthetic Look folder with one file edited; returns its path."""
    d = os.path.join(OUT, f"look_{TAG}_{name}", "Look")
    if os.path.isdir(d):
        shutil.rmtree(d)
    shutil.copytree(LOOK, d)
    edit(d)
    return d


def repoint_images(look):
    for img in bpy.data.images:
        if img.filepath:
            img.filepath = os.path.join(look, os.path.basename(bpy.path.abspath(img.filepath)))


def write_png(path, rgba):
    V.st_png(path, rgba)


# ------------------------------------------------------------------ REQUIRED mutations (task list)
def run():
    C = fresh()
    S = V.Snap("blend", C)
    # 1. a 12-vertex icosahedron rock (new ROCK_ object in the water)
    C = fresh()
    wx, wy = water_point(C)
    add("ROCK_ICO_T.000", ico_mesh("ICO12_T", mat="LK_BASALT" if HOLE == 10 else "LK_ROCK"), (wx, wy, 0.5))
    save("req_rock_ico12", ["ROCK_NOT_ICOSAHEDRON"], "required", "new ROCK_ICO_T = 12-vertex 20-face icosahedron in the water")
    if HOLE == 10:
        C = fresh()
        ico = ico_mesh("ICO12_WALL", mat="LK_BASALT")
        for me in sorted({o.data.name for o in bpy.data.objects if o.name.startswith("ROCK_WALL_") and o.type == "MESH"}):
            swap_geometry(me, ico.copy())
        save("req_wall_ico12", ["ROCK_NOT_ICOSAHEDRON", "CRATER_COLUMNS"], "required",
             "every ROCK_WALL_* mesh -> 12-vertex icosahedron (the brief's crater FAIL line)")
    # 2. MAT_FOAM strip (name without FOAM)
    if HOLE in (8, 9):
        C = fresh()
        P, N = V.st_shore_frame(C, 4.0)
        idx = np.arange(0, len(P) // 4)
        me = V.st_strip("WATER_EDGE_01", P[idx], N[idx], 0.3, 3.0, 0.1, mat="LK_SURF", uv_world=8.0)
        me.materials[0] = bpy.data.materials.get("MAT_FOAM") or bpy.data.materials.new("MAT_FOAM")
        add("WATER_EDGE_01", me)
        save("req_mat_foam_strip", ["NO_MAT_FOAM"], "required",
             "WATER_EDGE_01 white strip along a quarter of the shore, material MAT_FOAM (object name has no FOAM)")
    # 3. BUNKER_-prefixed sand patch on the rough (and the legal DRESS_SAND_ control)
    C = fresh()
    S = V.Snap("blend", C)
    x, y, z = rough_point(C, S)
    for nm, exp, kind in (("BUNKER_09", ["SAND_NAMES", "PLAY_SURFACE_NAMES"], "required"), ("DRESS_SAND_01", [], "control")):
        C = fresh()
        me = V.st_mesh(nm, [(x - 2, y - 2, z + 0.02), (x + 2, y - 2, z + 0.02), (x + 2, y + 2, z + 0.02), (x - 2, y + 2, z + 0.02)],
                       [(0, 1, 2, 3)], "LK_SAND")
        add(nm, me)
        save(f"{'req' if kind == 'required' else 'ctl'}_sand_patch_{nm}", exp, kind, f"4x4 m LK_SAND patch named {nm} on the rough at play height + 2 cm")
    # 4. collision-prefix props
    C = fresh()
    add("TERRAIN_ROCK.000", bpy.data.meshes["RK_A"], (x, y, z + 0.6), (1.0, 1.0, 1.0))
    save("req_collision_prefix_TERRAIN_rock", ["PLAY_SURFACE_NAMES", "NEW_OBJECT_PREFIXES"], "required",
         "a rock instance named TERRAIN_ROCK.000 on the rough")
    C = fresh()
    add("GREENERY_BUSH.000", bpy.data.meshes["PLANT_SHRUB_A"], (x, y, z))
    save("req_collision_prefix_GREENERY_plant", ["PLAY_SURFACE_NAMES", "NEW_OBJECT_PREFIXES"], "required",
         "a shrub instance named GREENERY_BUSH.000 (starts with GREEN -> HoleView MeshCollider)")
    # 5. moved terrain vertex (top, 5 cm up) / (top, 3 cm sideways)
    for nm, dv in (("req_terrain_top_vertex_up5cm", (0, 0, 0.05)), ("req_terrain_top_vertex_side3cm", (0.03, 0, 0))):
        C = fresh()
        ob = [o for o in bpy.data.objects if o.name.startswith("TERRAIN") and o.type == "MESH"][0]
        me = ob.data
        mw = ob.matrix_world
        up = [p for p in me.polygons if (mw.to_3x3() @ p.normal).z > 0.5]
        vid = up[len(up) // 2].vertices[0]
        me.vertices[vid].co += mw.to_3x3().inverted() @ Vector(dv)
        me.update()
        save(nm, ["PLAY_SURFACE_TOPS"], "required", f"{ob.name} vertex {vid} on an up-facing face moved {dv} m")
    # 6. WATER_LAVA one polygon (hole 10), with proper UVs
    if HOLE == 10:
        C = fresh()
        S = V.Snap("blend", C)
        lava = bpy.data.objects["WATER_LAVA"]
        W = S.wld(lava)["W"]
        lo, hi = W.min(0), W.max(0)
        me = V.st_mesh("LAVA_ONE", [(lo[0], lo[1], 0), (hi[0], lo[1], 0), (hi[0], hi[1], 0), (lo[0], hi[1], 0)], [(0, 1, 2, 3)], "LK_LAVA", uv=None)
        me.uv_layers.new(name="UVMap")
        lv = np.empty(len(me.loops), np.int64)
        me.loops.foreach_get("vertex_index", lv)
        co = np.array([(lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1])])[lv]
        me.uv_layers[0].data.foreach_set("uv", (co / 24.0).ravel())
        lava.data = me
        save("req_lava_one_polygon", ["CRATER_LAVA"], "required", "WATER_LAVA = one LK_LAVA quad with UVs at the contract tile")
    # 7. missing normal map (cliff on 8/9, basalt on 10)
    C = fresh()
    mname = "LK_BASALT" if HOLE == 10 else "LK_CLIFF"
    nt = bpy.data.materials[mname].node_tree
    for l in list(nt.links):
        if l.to_socket.name == "Normal":
            nt.links.remove(l)
    save("req_normal_map_unlinked", ["LK_TEXTURED"], "required", f"{mname}: Normal Map link removed")
    nfile = "Basalt_N" if HOLE == 10 else "Cliff_N"
    lk = look_copy("no_normal_file", lambda d: os.remove(os.path.join(d, nfile + ".png")))
    C = fresh()
    repoint_images(lk)
    save("req_normal_file_deleted", ["LK_TEXTURED", "LOOK_FILES"], "required", f"{nfile}.png deleted from the Look folder", look=lk)
    # 8. second GREEN (collision copy) and a DRESS_ copy with LK_GREEN
    C = fresh()
    S = V.Snap("blend", C)
    g = bpy.data.objects["GREEN"]
    gp = g.matrix_world.translation
    o = add("GREEN.001", g.data.copy())
    o.matrix_world = g.matrix_world.copy()
    o.location = (x - (S.centre(g)[0] - gp.x), y - (S.centre(g)[1] - gp.y), gp.z)
    save("req_second_GREEN", ["ONE_GREEN", "PLAY_SURFACE_NAMES", "NEW_OBJECT_PREFIXES"], "required",
         "GREEN.001 = copy of the green moved onto the rough")
    # 9. LK_SCRUB on the ribbon (Split): a DRESS_ overlay patch on the fairway in the ribbon core
    if HOLE == 9:
        C = fresh()
        P = V.split_samples(C)
        _rc, bc, _s, _dc, _ds = V.split_regions(C, P)
        q = P[bc][len(P[bc]) // 2] * V.YD
        me = V.st_mesh("DRESS_SCRUBPATCH", [(q[0] - 3, q[1] - 3, C.pz + 0.03), (q[0] + 3, q[1] - 3, C.pz + 0.03), (q[0] + 3, q[1] + 3, C.pz + 0.03),
                                            (q[0] - 3, q[1] + 3, C.pz + 0.03)], [(0, 1, 2, 3)], "LK_SCRUB")
        add("DRESS_SCRUBPATCH", me)
        save("req_scrub_on_ribbon", ["SPLIT_NO_SCRUB_RIBBON"], "required", "6x6 m DRESS_ patch with LK_SCRUB on the ribbon fairway")
    # 10. props renamed FLAG_...
    C = fresh()
    t = [o for o in bpy.data.objects if o.name.startswith("PLANT_TUFT")][0]
    t.name = "FLAG_TUFT"
    save("req_prop_renamed_FLAG", ["RESERVED_NAMES", "NEW_OBJECT_PREFIXES"], "required", "one tuft renamed FLAG_TUFT")

    # ------------------------------------------------------------------ RED TEAM (bad data that should FAIL a brief line)
    # R1 every rock mesh -> a 20-face icosahedron with split vertices (60 v): the same faceted grey blob the brief forbids
    C = fresh()
    rock_meshes = sorted({o.data.name for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(("ROCK_", "CLIFF_ROCK"))
                          and not o.name.startswith(("ROCK_SKIN_", "ROCK_WALL_"))})
    for k, me in enumerate(rock_meshes):
        swap_geometry(me, ico_mesh(f"ICO_SPLIT_{k}", split=True, mat="LK_BASALT" if HOLE == 10 else "LK_ROCK"))
    save("rt_all_rocks_split_icosahedron", ["ROCK_NOT_ICOSAHEDRON"], "redteam",
         f"every loose rock / stack mesh {rock_meshes} -> 20-face icosahedron with split vertices (60 verts)")
    # R2 every rock -> icosahedron + 1 loose vertex (13 v)
    C = fresh()
    for k, me in enumerate(rock_meshes):
        swap_geometry(me, ico_mesh(f"ICO_13_{k}", extra_vertex=True, mat="LK_BASALT" if HOLE == 10 else "LK_ROCK"))
    save("rt_all_rocks_ico_plus_loose_vertex", ["ROCK_NOT_ICOSAHEDRON"], "redteam",
         "every loose rock / stack mesh -> 12-vertex icosahedron + 1 loose vertex (13 verts, 20 faces)")
    # R3 a DRESS_ boulder sitting on the green over the pin / a ROCK_WALL_ pile on the fairway (8/9)
    C = fresh()
    px, py = pin_xy()
    add("DRESS_BOULDER", bpy.data.meshes["RK_A"], (px + 0.5, py, C.pz + 1.0), (3.0, 3.0, 3.0))
    save("rt_dress_boulder_on_pin", ["PROPS_OFF_PLAY"], "redteam", "DRESS_BOULDER (RK_A x3) standing on the green 0.5 m from the pin")
    if HOLE in (8, 9):
        C = fresh()
        add("ROCK_WALL_PILE", bpy.data.meshes["RK_A"], (px, py, C.pz + 1.0), (3.0, 3.0, 3.0))
        save("rt_rock_wall_on_pin", ["PROPS_OFF_PLAY"], "redteam", "ROCK_WALL_PILE (rock) standing on the pin (ROCK_WALL_ is exempt)")
    # R4 a continuous white foam band around the whole shore, LK_SURF, DRESS_ name, no vertex colour
    if HOLE in (8, 9):
        C = fresh()
        P, N = V.st_shore_frame(C, 4.0)
        me = V.st_strip("DRESS_SHOREBAND", P, N, 0.3, 3.0, 0.15, mat="LK_SURF", uv_world=8.0)
        add("DRESS_SHOREBAND", me)
        save("rt_white_band_dress_lk_surf", ["NO_MAT_FOAM"], "redteam",
             "DRESS_SHOREBAND = one continuous 2.7 m LK_SURF strip round the whole shore, no vertex colour (renders as a solid white band)")
        C = fresh()
        me = V.st_strip("WATER_SURF_99", P, N, 0.3, 3.0, 0.16, mat="LK_SURF", vcol=True, uv_world=8.0)
        ca = me.color_attributes[0]
        cols = np.ones(len(ca.data) * 4)
        cols[3] = 0.0
        ca.data.foreach_set("color", cols)
        add("WATER_SURF_99", me)
        save("rt_white_band_surf_alpha1", ["SURF_SHORE"], "redteam",
             "WATER_SURF_99 = continuous strip round the shore, vertex alpha 1 everywhere except one vertex (alpha range 1.0)")
    # R5 a collider hole: delete ONE up-facing TERRAIN face (vertices kept) that contains no signature grid point
    #     and is not covered by another collision mesh, + the same face flipped (single-sided collider)
    for mode in ("delete", "flip"):
        C = fresh()
        S = V.Snap("blend", C)
        g = SIG["grid"]
        ob = [o for o in bpy.data.objects if o.name.startswith("TERRAIN") and o.type == "MESH"][0]
        others = [o for o in V.coll_objects(S) if o.name != ob.name]
        rays_o = V.Rays(S, others)
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        mw = np.array(ob.matrix_world)
        upf = [f for f in bm.faces if (mw[:3, :3] @ np.array(f.normal))[2] > 0.5]
        vcount = {}
        for f in upf:
            for v in f.verts:
                vcount[v.index] = vcount.get(v.index, 0) + 1
        best = None
        for f in upf:
            if any(vcount[v.index] < 2 for v in f.verts):
                continue
            W = np.array([(mw[:3, :3] @ np.array(v.co)) + mw[:3, 3] for v in f.verts])
            lo, hi = W[:, :2].min(0), W[:, :2].max(0)
            i0, i1 = int(math.ceil((lo[0] - g["x0"]) / g["step"])), int(math.floor((hi[0] - g["x0"]) / g["step"]))
            j0, j1 = int(math.ceil((lo[1] - g["y0"]) / g["step"])), int(math.floor((hi[1] - g["y0"]) / g["step"]))
            inside = False
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    gx, gy = g["x0"] + i * g["step"], g["y0"] + j * g["step"]
                    if V.pip(W[:, :2], np.array([gx]), np.array([gy]))[0]:
                        inside = True
            if inside:
                continue
            c = W.mean(0)
            if rays_o.cast(float(c[0]), float(c[1])) is not None:
                continue
            area = f.calc_area()
            if best is None or area > best[1]:
                best = (f.index, area, c)
        if best is None:
            print(f"R5 {mode}: no uncovered up-facing TERRAIN face without a grid point", flush=True)
            bm.free()
            continue
        f = bm.faces[best[0]]
        if mode == "delete":
            bmesh.ops.delete(bm, geom=[f], context="FACES_ONLY")
        else:
            f.normal_flip()
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
        save(f"rt_terrain_top_face_{mode}", ["PLAY_SURFACE_TOPS", "PLAY_SURFACE_GRID"], "redteam",
             f"{ob.name}: one up-facing rough face ({best[1]:.2f} m2, centre {best[2][0]:.1f},{best[2][1]:.1f}) "
             f"{'deleted' if mode == 'delete' else 'flipped'} -> GroundHeight misses (falls to water) there; vertices kept")
    # R6 texture thresholds: flat RGB + noisy alpha; near-flat RGB (lum sd ~0.009)
    def flat_alpha(d):
        rng = np.random.default_rng(1)
        a = np.ones((128, 128, 4))
        a[..., :3] = (0.20, 0.55, 0.18)
        a[..., 3] = rng.uniform(0.0, 1.0, (128, 128))
        write_png(os.path.join(d, "Fairway_C.png"), a)

    def near_flat(d):
        rng = np.random.default_rng(2)
        a = np.ones((128, 128, 4))
        a[..., :3] = np.array((0.20, 0.55, 0.18)) + 0.0095 * rng.normal(0, 1, (128, 128))[..., None]
        write_png(os.path.join(d, "Fairway_C.png"), a)

    def flat_normal(d):
        rng = np.random.default_rng(3)
        a = np.ones((128, 128, 4))
        a[..., 0] = 0.5 + 0.0055 * rng.normal(0, 1, (128, 128))
        a[..., 1] = 0.5 + 0.0055 * rng.normal(0, 1, (128, 128))
        a[..., 2] = 1.0
        write_png(os.path.join(d, "Fairway_N.png"), a)
    for nm, fn, what in (("rt_fairway_C_flat_rgb_noisy_alpha", flat_alpha, "Fairway_C.png = one flat green RGB, random alpha"),
                         ("rt_fairway_C_near_flat", near_flat, "Fairway_C.png = one flat green + luminance noise sd 0.0095 (2.4/255)"),
                         ("rt_fairway_N_flat_dither", flat_normal, "Fairway_N.png = flat (128,128,255) + xy noise sd 0.0055")):
        lk = look_copy(nm, fn)
        C = fresh()
        repoint_images(lk)
        save(nm, ["LOOK_FILES"], "redteam", what, look=lk)
    if HOLE == 9:
        lk = look_copy("scrub_is_fairway", lambda d: shutil.copyfile(os.path.join(d, "Fairway_C.png"), os.path.join(d, "Scrub_C.png")))
        C = fresh()
        repoint_images(lk)
        save("rt_scrub_C_is_fairway_green", ["SPLIT_SCRUB_RIDGE"], "redteam",
             "Scrub_C.png = a copy of Fairway_C.png (the ridge renders the same green as the fairway)", look=lk)
    if HOLE == 10:
        def lava_flat(d):
            rng = np.random.default_rng(4)
            a = np.ones((128, 128, 4))
            a[..., :3] = np.array((1.0, 0.43, 0.10)) + 0.0095 * rng.normal(0, 1, (128, 128))[..., None]
            write_png(os.path.join(d, "Lava_C.png"), a)
            e = np.zeros((128, 128, 4))
            e[..., 3] = 1.0
            e[60:63, 60:63, :3] = 1.0
            write_png(os.path.join(d, "Lava_E.png"), e)
        lk = look_copy("lava_flat_orange", lava_flat)
        C = fresh()
        repoint_images(lk)
        save("rt_lava_flat_orange_textures", ["LOOK_FILES"], "redteam",
             "Lava_C.png = flat orange (+ sd 0.0095 noise), Lava_E.png = black with one 3x3 hot spot", look=lk)
    # R7 cliff / basalt UVs stretched 16:1 (u x4, v x0.25): same area density
    C = fresh()
    mname = "LK_BASALT" if HOLE == 10 else "LK_CLIFF"
    ob = [o for o in bpy.data.objects if o.name.startswith("TERRAIN") and o.type == "MESH"][0]
    me = ob.data
    k = [m.name for m in me.materials].index(mname)
    uv = me.uv_layers[0].data
    for p in me.polygons:
        if p.material_index == k:
            for li in p.loop_indices:
                u, v = uv[li].uv
                uv[li].uv = (u * 4.0, v * 0.25)
    save("rt_wall_uv_stretched_16to1", ["UV_DENSITY"], "redteam", f"{mname} wall UVs u x4, v x0.25 (16:1 anisotropic smear)")
    # R8 arch = one solid pillar of 14 stacked cubes (no opening)
    if HOLE == 8:
        C = fresh()
        a = C.sc["arch"]
        ax, ay, z0 = a["x"] * V.YD, a["d"] * V.YD, a["base_top_m"]
        bm = bmesh.new()
        for lvl in range(7):
            for col in range(6):
                bmesh.ops.create_cube(bm, size=0.98, matrix=Matrix.Translation((ax - 2.5 + col, ay, z0 + 0.5 + 1.0 * lvl)))
        bpy.data.objects["DRESS_ARCH_01"].data = V.st_bm_mesh("ARCH_WALL", bm, "LK_MASONRY")
        save("rt_arch_is_a_solid_wall", ["NEEDLE_ARCH"], "redteam", "DRESS_ARCH_01 = a solid 6 x 7 block wall, no opening (no arch)")
    # R9 a second 'green' as dressing: DRESS_LAWN disc in plant-green + a DRESS_FLAGSTICK
    C = fresh()
    S = V.Snap("blend", C)
    x, y, z = rough_point(C, S)
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=32, radius=8.0)
    me = V.st_bm_mesh("DRESS_LAWN", bm, "LK_PLANTS", uv="green")
    add("DRESS_LAWN", me, (x, y, z + 0.03))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.05, radius2=0.05, depth=2.4, matrix=Matrix.Translation((0, 0, 1.2)))
    add("DRESS_FLAGSTICK", V.st_bm_mesh("DRESS_FLAGSTICK", bm, "LK_PLANTS", uv="brown"), (x, y, z))
    save("rt_second_green_as_dressing", ["ONE_GREEN"], "redteam", "DRESS_LAWN 8 m plant-green disc + DRESS_FLAGSTICK pole on the rough")

    with open(os.path.join(OUT, f"hole_{TAG}_manifest.json"), "w") as f:
        json.dump(MAN, f, indent=1)
    print(f"MANIFEST {len(MAN)} variants", flush=True)


run()
