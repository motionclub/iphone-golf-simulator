"""Reviewer mutation harness (area V). Usage: blender -b --factory-startup --python mut.py -- <hole> <fbx0|fbx1> name1,name2|all
Loads the verifier as a module (never edits it), mutates the synthetic positive of review_V/st/h<hole>, runs the verifier, prints
MUT <hole> <name> -> FAILED[...]  (the gates that failed). Writes only under review_V/mut."""
import sys, os, importlib.util, math, traceback, shutil, re
import numpy as np
import bpy, bmesh
from mathutils import Vector

REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
RV = REPO + "/work/postcard-look/v2/review_V"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec)
sys.modules["pcv"] = m
spec.loader.exec_module(m)

argv = sys.argv[sys.argv.index("--") + 1:]
H = int(argv[0])
FBX = argv[1] == "fbx1"
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] != "all" else None
ST = f"{RV}/st2/h{H}"
BLEND = f"{ST}/hole_{H:02d}_pos.blend"
LOOK = f"{ST}/Look"
POSFBX = f"{ST}/hole_{H:02d}_pos.fbx"
if os.environ.get("PCV_BASE") == "lib":
    FX = RV + "/../gates/fixtures"
    BLEND = f"{FX}/lib_smoke_now/hole_{H:02d}.blend"
    POSFBX = f"{FX}/lib_smoke_now/hole_{H:02d}.fbx"
    LOOK = f"{FX}/look_at_run"
OUT = f"{RV}/mut2"
os.makedirs(OUT, exist_ok=True)
OPTS = m.parse_args([str(H)])

MUTS = []


def mut(name, hole=None):
    def deco(fn):
        MUTS.append((name, hole, fn))
        return fn
    return deco


def pxread(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, img.channels)
    bpy.data.images.remove(img)
    if a.shape[2] == 3:
        a = np.concatenate([a, np.ones((h, w, 1), np.float32)], 2)
    return a


def pxwrite(path, a):
    m.st_png(path, a.astype(np.float32))


# ---------------------------------------------------------------- geometry helpers
def ico(sub=2, noise=0.0, seed=0, mat="LK_ROCK"):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    rng = np.random.default_rng(seed)
    for v in bm.verts:
        v.co *= 1.0 + rng.uniform(-noise, noise)
    return m.st_bm_mesh(f"ICO{sub}_{noise}_{seed}", bm, mat)


def ico_bundle(n, jitter, seed):
    bm = bmesh.new()
    rng = np.random.default_rng(seed)
    for k in range(n):
        tmp = bmesh.new()
        bmesh.ops.create_icosphere(tmp, subdivisions=1, radius=1.0)
        # subdivisions=1 is the 12-vertex icosahedron in bmesh? (42 verts) -> use 12-vert by detail 1 radius, then check count
        me = bpy.data.meshes.new("tmp")
        tmp.to_mesh(me)
        tmp.free()
        c = rng.uniform(-1.2, 1.2, 3)
        vs = {}
        for v in me.vertices:
            vs[v.index] = bm.verts.new(np.array(v.co) * (0.5 + rng.uniform(-jitter, jitter)) * (1 + rng.uniform(-jitter, jitter, 3)) + c)
        for p in me.polygons:
            bm.faces.new([vs[i] for i in p.vertices])
        bpy.data.meshes.remove(me)
    return m.st_bm_mesh("BUNDLE", bm, "LK_ROCK")


def root():
    return m._root()


def pt_on_land(C, S=None, kind="rough"):
    S = S or m._snap(C)
    rng = np.random.default_rng(3)
    c = m.st_candidates(C, S, 3, rng, kind=kind, clear=0.0)
    return c[0]


def water_pt(C, far=30.0):
    return m._water_point(C, far)


def new_hull(name, seed=77, dims=(2.0, 1.6, 1.2), mat="LK_ROCK"):
    me = m.st_hull_rock(f"HULL_{name}", seed, mat, dims=dims)
    m.st_box_uv(me)
    return me


# ---------------------------------------------------------------- ROCK mutations
@mut("rk_ico_sub2_noise10")
def _(C):
    m._swap_all_rocks(lambda k: ico(2, 0.10, k))


@mut("rk_ico_sub2_noise25")
def _(C):
    m._swap_all_rocks(lambda k: ico(2, 0.25, k))


@mut("rk_ico_sub2_noise40")
def _(C):
    m._swap_all_rocks(lambda k: ico(2, 0.40, k))


@mut("rk_ico_sub1_42v")
def _(C):
    m._swap_all_rocks(lambda k: ico(1, 0.0, k))


@mut("rk_ico_sub1_noise20_split")
def _(C):
    def mk(k):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        rng = np.random.default_rng(k)
        for v in bm.verts:
            v.co *= 1 + rng.uniform(-.2, .2)
        bmesh.ops.split_edges(bm, edges=list(bm.edges))
        return m.st_bm_mesh(f"S{k}", bm, "LK_ROCK")
    m._swap_all_rocks(mk)


@mut("rk_bundle5_ico_jitter")
def _(C):
    m._swap_all_rocks(lambda k: ico_bundle(5, 0.12, k))


@mut("rk_bundle8_ico_jitter")
def _(C):
    m._swap_all_rocks(lambda k: ico_bundle(8, 0.2, k))


@mut("rk_DRESS_named_ico42")
def _(C):
    # rocks hidden under DRESS_ names (not checked by the ROCK_ shape gates)
    S = m._snap(C)
    for k, o in enumerate([o for o in m._ob("ROCK_B")][:6]):
        old = o.data
        o.name = f"DRESS_BOULDER_{k:02d}"
        o.data = ico(1, 0.0, k)
        m.st_fit(o.data, old)


@mut("rk_variety_rename_only")
def _(C):
    # same hull mesh in 6 differently named datablocks with trivially different vertex jitter -> variety by data?
    names = m._rock_names()
    for k, nm in enumerate(names):
        new = new_hull(f"V{k}", seed=5, dims=(2.0, 1.6, 1.2))
        m.st_fit(new, bpy.data.meshes[nm])
        for ob in list(bpy.data.objects):
            if ob.type == "MESH" and ob.data == bpy.data.meshes[nm]:
                ob.data = new


@mut("rk_ico_sub3_noise15")
def _(C):
    m._swap_all_rocks(lambda k: ico(3, 0.15, k))


@mut("rk_ico_sub3_noise40")
def _(C):
    m._swap_all_rocks(lambda k: ico(3, 0.40, k))


@mut("rk_bundle_variety_loose_only")
def _(C):
    names = [n for n in m._rock_names()]
    for k, nm in enumerate(names):
        new = ico_bundle(5 + (k % 4), 0.12, 100 + k)
        m.st_fit(new, bpy.data.meshes[nm])
        for ob in list(bpy.data.objects):
            if ob.type == "MESH" and ob.data == bpy.data.meshes[nm] and not ob.name.startswith("ROCK_SEASTACK"):
                ob.data = new


# ---------------------------------------------------------------- stretch
def one_rock(C, name, scale=(1, 1, 1), rot=0.0, parent=None):
    S = m._snap(C)
    p = pt_on_land(C, S)
    me = new_hull(name)
    ob = m.st_obj(name, me, (p[0], p[1], p[2] + 0.4), scale, rot, root=parent or root())
    return ob


@mut("st_scale_0.5_2_0.5")
def _(C):
    one_rock(C, "ROCK_TEST_1", (0.5, 2.0, 0.5))


@mut("st_scale_1_2.0_1")
def _(C):
    one_rock(C, "ROCK_TEST_1", (1.0, 2.0, 1.0))


@mut("st_scale_1_2.15_1")
def _(C):
    one_rock(C, "ROCK_TEST_1", (1.0, 2.15, 1.0))


@mut("st_shear_parent")
def _(C):
    S = m._snap(C)
    p = pt_on_land(C, S)
    em = bpy.data.objects.new("DRESS_SHEARPARENT", None)
    bpy.context.scene.collection.objects.link(em)
    em.parent = root()
    em.location = (p[0], p[1], p[2] + 0.4)
    em.rotation_euler = (0, 0, math.radians(45))
    em.scale = (0.6, 1.9, 1.0)
    me = new_hull("shear")
    ob = m.st_obj("ROCK_TEST_SHEAR", me, (0, 0, 0), (1, 1, 1), math.radians(-45), root=em)


@mut("st_baked_stretch_wall")
def _(C):
    S = m._snap(C)
    p = pt_on_land(C, S)
    me = new_hull("bk", dims=(2.0, 1.6, 1.2))
    for v in me.vertices:
        v.co.x *= 4.0
        v.co.y *= 0.5
    m.st_box_uv(me)
    m.st_obj("ROCK_WALL_77", me, (p[0], p[1], p[2] + 0.4), (1, 1, 1), 0, root=root())


def unit_scale_all():
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith(("ROCK_LARGE", "ROCK_MEDIUM", "ROCK_SMALL", "ROCK_WALL", "CLIFF_ROCK")):
            o.scale = (1, 1, 1)


@mut("st_lib_unit_scale_control")
def _(C):
    unit_scale_all()


@mut("st_lib_unit_scale_baked_swap_stretch")
def _(C):
    unit_scale_all()
    lib = bpy.data.collections.get("ASSET_LIBRARY")
    L = set(lib.all_objects) if lib else set()
    o = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("ROCK_LARGE") and o not in L][0]
    old = o.data
    me = bpy.data.meshes.new("lbs3")
    me.from_pydata([tuple(v.co) for v in old.vertices], [], [tuple(p.vertices) for p in old.polygons])
    for v in me.vertices:
        v.co.x *= 4.0
        v.co.y *= 0.5
    me.materials.append(old.materials[0])
    me.update()
    o.data = me


@mut("st_lib_unit_scale_baked_swap_stretch_wallname")
def _(C):
    unit_scale_all()
    lib = bpy.data.collections.get("ASSET_LIBRARY")
    L = set(lib.all_objects) if lib else set()
    o = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("ROCK_LARGE") and o not in L][0]
    old = o.data
    me = bpy.data.meshes.new("lbs4")
    me.from_pydata([tuple(v.co) for v in old.vertices], [], [tuple(p.vertices) for p in old.polygons])
    for v in me.vertices:
        v.co.x *= 4.0
        v.co.y *= 0.5
    me.materials.append(old.materials[0])
    me.update()
    o.data = me
    o.name = "ROCK_CAIRN_01"


@mut("st_lib_baked_swap_stretch")
def _(C):
    lib = bpy.data.collections.get("ASSET_LIBRARY")
    o = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("ROCK_LARGE") and o not in (set(lib.all_objects) if lib else set())][0]
    old = o.data
    me = new_hull("lbs", dims=(2.0, 1.6, 1.2))
    m.st_fit(me, old)
    for v in me.vertices:
        v.co.x *= 4.0
        v.co.y *= 0.5
    o.data = me


@mut("st_lib_baked_swap_fit")
def _(C):
    lib = bpy.data.collections.get("ASSET_LIBRARY")
    o = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("ROCK_LARGE") and o not in (set(lib.all_objects) if lib else set())][0]
    old = o.data
    me = new_hull("lbs2", dims=(2.0, 1.6, 1.2))
    m.st_fit(me, old)
    o.data = me


@mut("st_baked_stretch_loose")
def _(C):
    S = m._snap(C)
    p = pt_on_land(C, S)
    me = new_hull("bk2", dims=(2.0, 1.6, 1.2))
    for v in me.vertices:
        v.co.x *= 5.0
        v.co.y *= 0.4
    m.st_box_uv(me)
    m.st_obj("ROCK_LARGE.099", me, (p[0], p[1], p[2] + 0.4), (1, 1, 1), 0, root=root())


# ---------------------------------------------------------------- foam / shelf
def piece_starts(C, run_samples, gap_samples):
    P, N, LID = m._shore(C, 2.0)
    out = []
    for lid in sorted(set(LID.tolist())):
        idx = np.flatnonzero(LID == lid)
        i = int(idx[0]) + 2
        while i + run_samples < idx[-1]:
            out.append(i)
            i += run_samples + gap_samples
    return out


@mut("foam_dash_9m_gap27")        # runs 9 m (<=10), gaps 27 m, cover 25 %: boundary of the stated rules
def _(C):
    m._patches(C, piece_starts(C, 5, 14), length=5)           # 5 samples * 2 m = 8..10 m


@mut("foam_dash_9m_gap7")
def _(C):
    m._patches(C, piece_starts(C, 5, 4), length=5)


@mut("foam_dash_9m_gap9_fail_cov")
def _(C):
    m._patches(C, piece_starts(C, 5, 5), length=5)


@mut("foam_two_rows_union50")
def _(C):
    s = piece_starts(C, 5, 14)
    m._patches(C, s, length=5, prefix="WATER_SURF", base=50)
    m._patches(C, [i + 9 for i in s], length=5, prefix="WATER_SURF", base=70)


@mut("foam_dash_offshore_ring_20m")
def _(C):
    P, N, LID = m._shore(C, 2.0)
    k = 0
    for lid in sorted(set(LID.tolist())):
        idx = np.flatnonzero(LID == lid)
        i = int(idx[0]) + 2
        while i + 5 < idx[-1]:
            ii = np.arange(i, i + 5)
            me = m.st_strip(f"WATER_SURF_{80 + k}", P[ii], N[ii], 20.0, 23.0, 0.12, mat="LK_SURF", vcol=True, uv_world=8.0)
            m._env(f"WATER_SURF_{80 + k}", me)
            k += 1
            i += 5 + 3
    print("offshore pieces", k)


@mut("foam_ribbon_far_30m")
def _(C):
    P, N, LID = m._shore(C, 2.0)
    best = max(m.split_by_loop(np.arange(len(P)), LID), key=len)
    me = m.st_strip("WATER_SURF_97", P[best], N[best], 30.0, 33.0, 0.12, mat="LK_SURF", vcol=True, uv_world=8.0)
    m._env("WATER_SURF_97", me)


@mut("foam_in_ocean_material_white")
def _(C):
    # foam painted into the WATER_SHELF object itself: a white LK_SURF face band on the shelf mesh
    sh = bpy.data.objects.get("WATER_SHELF")
    if sh is None:
        raise RuntimeError("no shelf")
    me = sh.data
    me.materials.append(m._mat("LK_SURF", C))
    for p in me.polygons[: len(me.polygons) // 2]:
        p.material_index = len(me.materials) - 1


@mut("shelf_halo_as_DRESS_obj")
def _(C):
    P, N, LID = m._shore(C, 2.0)
    best = max(m.split_by_loop(np.arange(len(P)), LID), key=len)
    me = m.st_strip("DRESS_SHELF2", P[best], N[best], 0.0, 16.0, -0.05, mat="LK_WATER_SHALLOW", uv_world=8.0)
    m._env("DRESS_SHELF2", me)


@mut("shelf_ring_3.9m_uniform")
def _(C):
    m._set_shelf(C, lambda i: np.full(len(i), 3.9), gaps_every=10 ** 6, gap_len=0)


@mut("shelf_ring_2.4_uniform")
def _(C):
    m._set_shelf(C, lambda i: np.full(len(i), 2.4), gaps_every=10 ** 6, gap_len=0)


def ragged_band(C, name, o_in, wmin, wmax, seed=1, loops=None, vcol_alpha=1.0):
    P, N, LID = m._shore(C, 2.0)
    rng = np.random.default_rng(seed)
    V, F, vcols = [], [], []
    prev = None
    k = 0
    for i in range(len(P)):
        if prev is not None and LID[i] != LID[i - 1]:
            prev = None
        w = rng.uniform(wmin, wmax)
        a = (P[i][0] + N[i][0] * o_in, P[i][1] + N[i][1] * o_in, 0.12)
        b = (P[i][0] + N[i][0] * (o_in + w), P[i][1] + N[i][1] * (o_in + w), 0.12)
        base = len(V)
        V += [a, b]
        if prev is not None:
            F.append((prev, prev + 1, base + 1, base))
        prev = base
    me = m.st_mesh(name, V, F, "LK_SURF", uv=None)
    me.update()
    if len(me.polygons) and me.polygons[0].normal.z < 0:
        me.flip_normals()
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    cols = np.ones(len(ca.data) * 4)
    ca.data.foreach_set("color", cols)
    # uv world
    me.uv_layers.new(name="UVMap")
    uv = np.empty(len(me.loops) * 2)
    lv = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    co = np.array([v.co[:] for v in me.vertices])
    uv = np.stack([co[lv][:, 0] / 8.0, co[lv][:, 1] / 8.0], 1)
    me.uv_layers[0].data.foreach_set("uv", uv.ravel())
    m._env(name, me)


@mut("foam_ragged_continuous_band_off1.6")
def _(C):
    ragged_band(C, "WATER_SURF_95", 1.6, 1.0, 4.5)


@mut("foam_ragged_continuous_band_off1.2")
def _(C):
    ragged_band(C, "WATER_SURF_95", 1.2, 1.0, 4.5)


@mut("foam_ragged_continuous_band_off0.3")
def _(C):
    ragged_band(C, "WATER_SURF_95", 0.3, 1.0, 4.5)


@mut("foam_ragged_hicv_band_off1.6")
def _(C):
    ragged_band(C, "WATER_SURF_95", 1.6, 0.3, 5.5, seed=4)


@mut("foam_ragged_hicv_band_off2.5")
def _(C):
    ragged_band(C, "WATER_SURF_95", 2.5, 0.3, 5.5, seed=4)
    # give it an alpha ramp so SURF_SHORE is happy
    ob = bpy.data.objects["WATER_SURF_95"]
    ca = ob.data.color_attributes[0]
    cols = np.ones(len(ca.data) * 4)
    cols[3::8] = 0.0
    ca.data.foreach_set("color", cols)


@mut("foam_squares_touching_off2")
def _(C):
    P, N, LID = m._shore(C, 2.0)
    k = 0
    for lid in sorted(set(LID.tolist())):
        idx = np.flatnonzero(LID == lid)
        i = int(idx[0]) + 1
        while i + 3 < idx[-1]:
            ii = np.arange(i, i + 3)
            me = m.st_strip(f"WATER_SURF_{120 + k}", P[ii], N[ii], 2.0, 6.0, 0.12, mat="LK_SURF", vcol=True, uv_world=8.0)
            m._env(f"WATER_SURF_{120 + k}", me)
            k += 1
            i += 3
    print("squares", k)


# ---------------------------------------------------------------- path
def path_raise(dz):
    def f(C):
        S = m._snap(C)
        for o in m._ob("DRESS_PATH"):
            for v in o.data.vertices:
                v.co.z += dz / max(o.matrix_world.to_scale().z, 1e-9)
    return f


for nm, dz in (("path_plus_1.0cm", 0.010), ("path_plus_1.6cm", 0.016), ("path_plus_3cm", 0.03)):
    MUTS.append((nm, 8, path_raise(dz)))


@mut("path_renamed_CART_PATH_3cm", 8)
def _(C):
    for o in m._ob("DRESS_PATH"):
        o.name = "CART_PATH_01"
        for v in o.data.vertices:
            v.co.z += 0.03


@mut("path_renamed_DRESS_WALKWAY_11cm", 8)
def _(C):
    for o in m._ob("DRESS_PATH"):
        o.name = "DRESS_WALKWAY_01"
        for v in o.data.vertices:
            v.co.z += 0.11


@mut("path_one_spike_5cm", 8)
def _(C):
    o = m._ob("DRESS_PATH")[0]
    v = max(o.data.vertices, key=lambda v: v.co.z)
    v.co.z += 0.05


# ---------------------------------------------------------------- plants
def plant_mesh(name="PLANT_TUFT_X"):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((-0.2, -0.2, 0), (0.2, -0.2, 0), (0, 0.25, 0), (0, 0, 0.5))]
    bm.faces.new([vs[0], vs[1], vs[3]])
    bm.faces.new([vs[1], vs[2], vs[3]])
    bm.faces.new([vs[2], vs[0], vs[3]])
    return m.st_bm_mesh(name, bm, "LK_PLANTS", uv="tuft" if "tuft" in m.ST_SWATCH else "box")


def existing_plant_mesh():
    ps = m._ob("PLANT_")
    return ps[0].data if ps else plant_mesh()


@mut("pl_on_sea_z0")
def _(C):
    x, y = water_pt(C)
    m.st_obj("PLANT_TUFT_SEA", existing_plant_mesh(), (x, y, 0.0), root=root())


@mut("pl_on_sea_z5.2")
def _(C):
    x, y = water_pt(C, 14.0)
    m.st_obj("PLANT_TUFT_SEA52", existing_plant_mesh(), (x, y, 5.2), root=root())


@mut("pl_on_floating_rock_z5.2")
def _(C):
    x, y = water_pt(C, 20.0)
    me = new_hull("float", dims=(3.0, 3.0, 0.5))
    co = np.array([v.co[:] for v in me.vertices])
    # lift so top = 5.2
    for v in me.vertices:
        v.co.z += 5.2 - co[:, 2].max()
    m.st_obj("ROCK_MEDIUM.088", me, (x, y, 0), root=root())
    m.st_obj("PLANT_TUFT_ONROCK", existing_plant_mesh(), (x, y, 5.2), root=root())


@mut("pl_merged_far_copy_over_sea")
def _(C):
    S = m._snap(C)
    p = pt_on_land(C, S)
    x, y = water_pt(C, 40.0)
    base = existing_plant_mesh()
    bm = bmesh.new()
    bm.from_mesh(base)
    for i, v in enumerate(list(bm.verts)):
        pass
    # shrink the source plant to 1 face-triple to stay inside the face budget
    for f in list(bm.faces)[3:]:
        bmesh.ops.delete(bm, geom=[f], context="FACES")
    for sgn in (1, -1):
        bm2 = bm.copy()
        bmesh.ops.translate(bm2, vec=(sgn * (x - p[0]), sgn * (y - p[1]), 0.0), verts=list(bm2.verts))
        tmp = bpy.data.meshes.new("t2")
        bm2.to_mesh(tmp)
        bm.from_mesh(tmp)
    me = bpy.data.meshes.new("PLANT_MERGED")
    bm.to_mesh(me)
    me.materials.append(bpy.data.materials["LK_PLANTS"])
    if len(base.uv_layers):
        pass
    m.st_box_uv(me)
    m.st_obj("PLANT_TUFT_MERGED", me, (p[0], p[1], p[2]), root=root())


@mut("pl_on_play_edge_fairway")
def _(C):
    pin = m._pin()
    m.st_obj("PLANT_SHRUB_PIN", existing_plant_mesh(), (pin[0] + 2.5, pin[1], C.pz), root=root())


# ---------------------------------------------------------------- props near pin / play
@mut("pr_boulder_3.2m_from_pin")
def _(C):
    pin = m._pin()
    m.st_obj("ROCK_MEDIUM.077", new_hull("pb"), (pin[0] + 3.2, pin[1], C.pz), root=root())


@mut("pr_boulder_on_apron_edge")
def _(C):
    pin = m._pin()
    rad = C.gr * m.YD + 1.0
    m.st_obj("ROCK_MEDIUM.078", new_hull("pb2"), (pin[0] + rad + 0.2, pin[1], C.pz), root=root())


@mut("pr_floating_boulder_over_pin_9m")
def _(C):
    pin = m._pin()
    m.st_obj("ROCK_MEDIUM.079", new_hull("pb3"), (pin[0], pin[1], C.pz + 9.5), root=root())


@mut("pr_TERRAIN_named_boulder")
def _(C):
    S = m._snap(C)
    p = pt_on_land(C, S)
    m.st_obj("TERRAIN_BOULDER", new_hull("tb"), (p[0], p[1], p[2]), root=root(), coll="ENVIRONMENT")


@mut("pr_small_DRESS_boulder_between_grid_pts")
def _(C):
    S = m._snap(C)
    pts = m.play_samples(S, C)
    pin = np.array(m._pin())
    # grid points over FAIRWAY far from the pin; place at a cell centre
    best = None
    for (x, y, z) in pts:
        if math.hypot(x - pin[0], y - pin[1]) < 25:
            continue
        cx, cy = x + 0.75, y + 0.75
        hit, hz = m.on_land(S, C, cx, cy)
        if hit and hit.startswith("FAIRWAY"):
            if all(m.on_land(S, C, cx + dx, cy + dy)[0] == hit for dx, dy in ((.4, 0), (-.4, 0), (0, .4), (0, -.4))):
                best = (cx, cy, hz)
                break
    print("placing at", best)
    me = new_hull("small", dims=(0.7, 0.7, 0.6))
    m.st_obj("DRESS_BOULDER_FW", me, (best[0], best[1], best[2]), root=root())


@mut("pr_small_ROCK_boulder_on_fairway")
def _(C):
    S = m._snap(C)
    pts = m.play_samples(S, C)
    pin = np.array(m._pin())
    for (x, y, z) in pts:
        if math.hypot(x - pin[0], y - pin[1]) < 25:
            continue
        cx, cy = x + 0.75, y + 0.75
        hit, hz = m.on_land(S, C, cx, cy)
        if hit and hit.startswith("FAIRWAY"):
            me = new_hull("small2", dims=(0.7, 0.7, 0.6))
            m.st_obj("ROCK_SMALL.099", me, (cx, cy, hz), root=root())
            return


# ---------------------------------------------------------------- sea stacks
def ziggurat(name, layers=5, yaw=22.0, w0=7.0, shrink=0.7, h=3.9):
    bm = bmesh.new()
    z = -3.0
    w = w0
    for k in range(layers):
        r = bmesh.ops.create_cube(bm, size=1.0)
        vs = r["verts"]
        for v in vs:
            v.co.x *= w
            v.co.y *= w * 0.8
            v.co.z = (v.co.z + 0.5) * h + z
        bmesh.ops.rotate(bm, cent=(0, 0, z), matrix=__import__("mathutils").Matrix.Rotation(math.radians(yaw * k), 3, "Z"), verts=vs)
        z += h * (1.0 if k else 1.75)
        w *= shrink
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=2, use_grid_fill=True)
    return m.st_bm_mesh(name, bm, "LK_ROCK")


@mut("stack_ziggurat_named_SEASTACK", 8)
def _(C):
    ss = m._stacks()
    for k, o in enumerate(ss):
        me = ziggurat(f"ZIG{k}")
        m.st_box_uv(me)
        o.data = me


@mut("stack_ziggurat_named_PEDESTAL_extra", 8)
def _(C):
    x, y = water_pt(C, 45.0)
    me = ziggurat("ZIGP")
    m.st_box_uv(me)
    m.st_obj("ROCK_PEDESTAL_99", me, (x, y, 0), root=root())


@mut("stack_boxes_named_WALL_extra", 8)
def _(C):
    x, y = water_pt(C, 45.0)
    me = m.st_box_stack("BX")
    m.st_box_uv(me)
    m.st_obj("ROCK_WALL_88", me, (x, y, 0), root=root())


# ---------------------------------------------------------------- crater wall
@mut("wall_one_sector_open_5m", 10)
def _(C):
    S = m._snap(C)
    for o in m._ob("ROCK_SKIN"):
        pass
    cl = [o for o in bpy.data.objects if o.type == "MESH" and ("CLAD" in o.name or "SKIN" in o.name)]
    print("cladding objs", [o.name for o in cl])
    for o in cl:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        mw = o.matrix_world
        cen = lambda f: mw @ f.calc_center_median()
        c0 = cen(bm.faces[0])
        dead = [f for f in bm.faces if (cen(f) - c0).length < float(os.environ.get("PCV_R", "12"))]
        print("deleted cladding faces", len(dead), "of", len(bm.faces))
        bmesh.ops.delete(bm, geom=dead, context="FACES")
        bm.to_mesh(o.data)
        bm.free()
        break


@mut("wall_top_band_open", 10)
def _(C):
    band = float(os.environ.get("PCV_BAND", "1.5"))
    for o in [o for o in bpy.data.objects if o.type == "MESH" and "SKIN" in o.name]:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        mw = o.matrix_world
        dead = [f for f in bm.faces if (mw @ f.calc_center_median()).z > C.pz - band]
        print("deleted top-band faces", len(dead), "of", len(bm.faces))
        bmesh.ops.delete(bm, geom=dead, context="FACES")
        bm.to_mesh(o.data)
        bm.free()


@mut("wall_quarter_open", 10)
def _(C):
    cl = [o for o in bpy.data.objects if o.type == "MESH" and ("CLAD" in o.name or "SKIN" in o.name)]
    for o in cl:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        mw = o.matrix_world
        dead = [f for f in bm.faces if (mw @ f.calc_center_median()).x > 0 and (mw @ f.calc_center_median()).y > 0]
        bmesh.ops.delete(bm, geom=dead, context="FACES")
        bm.to_mesh(o.data)
        bm.free()


# ---------------------------------------------------------------- play surface
def top_vert_shift(dz, name_prefix="TERRAIN"):
    def f(C):
        ob = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(name_prefix)][0]
        # a top vertex shared by several up faces, away from the shore
        best = max((v for v in ob.data.vertices if abs(v.co.z - C.pz) < 0.5), key=lambda v: -abs(v.co.x) - abs(v.co.y))
        best.co.z += dz / max(ob.matrix_world.to_scale().z, 1e-9)
    return f


for nm, dz in (("top_shift_0.3mm", 3e-4), ("top_shift_0.9mm", 9e-4), ("top_shift_2mm", 2e-3), ("top_shift_1cm", 1e-2)):
    MUTS.append((nm, None, top_vert_shift(dz)))


@mut("terrain_wall_poly_deleted")
def _(C):
    ob = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("TERRAIN")][0]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    mw = np.array(ob.matrix_world)
    walls = [f for f in bm.faces if (mw[:3, :3] @ np.array(f.normal))[2] < -0.2 or abs((mw[:3, :3] @ np.array(f.normal))[2]) < 0.3]
    f = max(walls, key=lambda f: f.calc_area())
    bmesh.ops.delete(bm, geom=[f], context="FACES_ONLY")
    bm.to_mesh(ob.data)
    bm.free()


@mut("coincident_dup_up_tri_raised_1cm")
def _(C):
    ob = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("FAIRWAY")][0]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    f = [f for f in bm.faces if f.normal.z > 0.5][10]
    vs = [bm.verts.new(v.co + Vector((0, 0, 0.01))) for v in f.verts]
    bm.faces.new(vs)
    bm.to_mesh(ob.data)
    bm.free()


# ---------------------------------------------------------------- Look folder mutations (texture files)
def tex_mut(name, holes, edit, expect=None):
    MUTS.append((name, holes, ("TEX", edit)))


def tex_edit_scrub_hueshift(d):
    a = pxread(f"{d}/Fairway_C.png")
    import colorsys
    rgb = a[:, :, :3]
    mx, mn = rgb.max(2), rgb.min(2)
    # crude rotate by 25 deg in hue + darken, via numpy HSV
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.zeros_like(mx)
    dlt = mx - mn + 1e-9
    h = np.where(mx == r, ((g - b) / dlt) % 6, np.where(mx == g, (b - r) / dlt + 2, (r - g) / dlt + 4)) * 60
    s = np.where(mx > 0, dlt / (mx + 1e-9), 0)
    v = mx * 0.85
    h = (h - 28) % 360
    c = v * s
    x = c * (1 - np.abs((h / 60) % 2 - 1))
    mm = v - c
    z = np.zeros_like(c)
    sec = (h // 60).astype(int)
    R = np.choose(sec, [c, x, z, z, x, c]) + mm
    G = np.choose(sec, [x, c, c, x, z, z]) + mm
    B = np.choose(sec, [z, z, x, c, c, x]) + mm
    out = np.stack([R, G, B, np.ones_like(R)], 2)
    pxwrite(f"{d}/Scrub_C.png", out)


tex_mut("tex_scrub_is_hueshifted_fairway", (9,), tex_edit_scrub_hueshift)


def tex_edit_scrub_copy(d):
    shutil.copyfile(f"{d}/Fairway_C.png", f"{d}/Scrub_C.png")


def tex_edit_scrub_roll(d):
    a = pxread(f"{d}/Fairway_C.png")
    pxwrite(f"{d}/Scrub_C.png", np.roll(a, (37, 91), (0, 1)))


def tex_edit_scrub_tint_hue(d):
    a = pxread(f"{d}/Fairway_C.png")
    b = a.copy()
    b[..., 0] = np.clip(a[..., 0] * 1.18, 0, 1)       # redder -> hue lower (about -10..-13 deg)
    b[..., 2] = np.clip(a[..., 2] * 1.0, 0, 1)
    b[..., 1] = a[..., 1] * 0.88
    pxwrite(f"{d}/Scrub_C.png", b)


tex_mut("tex_scrub_exact_copy_fairway", (9,), tex_edit_scrub_copy)
tex_mut("tex_scrub_rolled_copy_fairway", (9,), tex_edit_scrub_roll)
tex_mut("tex_scrub_tint_copy_fairway", (9,), tex_edit_scrub_tint_hue)


def tex_edit_scrub_rough(d):
    shutil.copyfile(f"{d}/Rough_C.png", f"{d}/Scrub_C.png")


tex_mut("tex_scrub_is_rough_copy", (9,), tex_edit_scrub_rough)


def tex_edit_lowfreq_only(d):
    # Fairway/Green with ONLY a smooth big-blotch pattern at 0.03 sd (what the real Look looks like), at 256px
    rng = np.random.default_rng(5)
    n = 256
    for nm, hue in (("Fairway_C", (0.50, 0.62, 0.20)), ("Green_C", (0.56, 0.68, 0.24)), ("Rough_C", (0.30, 0.42, 0.12))):
        f = np.fft.fft2(rng.normal(0, 1, (n, n)))
        fx = np.fft.fftfreq(n)[:, None]
        fy = np.fft.fftfreq(n)[None, :]
        r = np.sqrt(fx ** 2 + fy ** 2) + 1e-6
        g = np.real(np.fft.ifft2(f / r ** 2.0))
        g = (g - g.mean()) / (g.std() + 1e-9)
        a = np.zeros((n, n, 4), np.float32)
        a[..., :3] = np.array(hue)[None, None, :] * (1 + 0.05 * g[..., None])
        a[..., 3] = 1
        pxwrite(f"{d}/{nm}.png", np.clip(a, 0, 1))


tex_mut("tex_grass_smooth_lowfreq_sd5pct_256px", (8,), tex_edit_lowfreq_only)


def tex_edit_fw_checker(d):
    n = 256
    yy, xx = np.mgrid[0:n, 0:n]
    chk = (((xx // 8) + (yy // 8)) % 2).astype(np.float32)
    base = np.array([0.50, 0.62, 0.20])
    for nm, hshift in (("Fairway_C", 0.0), ("Green_C", 0.06)):
        a = np.zeros((n, n, 4), np.float32)
        a[..., :3] = (base + hshift)[None, None, :] * (0.93 + 0.14 * chk)[..., None]
        if nm == "Green_C":
            a[..., :3] = a[..., :3][:, ::-1][::-1] * 1.0
        a[..., 3] = 1.0
        pxwrite(f"{d}/{nm}.png", a)


tex_mut("tex_grass_checker_pattern", (8,), tex_edit_fw_checker)


def tex_edit_fw_lowres(d):
    for nm in ("Fairway_C", "Green_C"):
        a = pxread(f"{d}/{nm}.png")
        n = a.shape[0]
        f = max(1, n // 128)
        sm = a.reshape(n // f, f, n // f, f, 4).mean((1, 3))
        pxwrite(f"{d}/{nm}.png", sm)


# real Look PNGs downsampled 8x (1024 -> 128): same content, less resolution
def tex_real_lowres(holes):
    MUTS.append(("tex_REAL_look_downsampled_to_128", holes, ("TEXREAL", tex_edit_fw_lowres)))


tex_real_lowres((8,))


def tex_edit_bimodal_hue(d):
    for nm in ("Fairway_C", "Green_C", "Rough_C"):
        a = pxread(f"{d}/{nm}.png")
        n = a.shape[0]
        a[:, : n // 2, :3] = np.array([0.25, 0.80, 0.25])     # hue ~120 (the old blue-green)
        a[:, n // 2:, :3] = np.array([0.80, 0.45, 0.10])      # hue ~33 (orange)
        # keep original luminance structure
        pxwrite(f"{d}/{nm}.png", a)


tex_mut("tex_grass_bimodal_hue_avg_ok", (8,), tex_edit_bimodal_hue)


def tex_edit_rough_flat_ok_others_fine(d):
    pass


# ---------------------------------------------------------------- driver
def stage_fails(res):
    return sorted({r["name"] for r in res if not r["ok"]})


def run_check(blend, fbx, look):
    o = dict(OPTS, hole=H, blend=blend, fbx=fbx, no_fbx=(fbx is None), look_dir=look, json=None)
    fails, res, _out = m.quiet_check(H, o)
    return fails, res


def main():
    # baseline positive
    f0, r0 = run_check(BLEND, POSFBX if FBX else None, LOOK)
    F0 = set(f0)
    print(f"POSITIVE hole {H}: failed {f0}", flush=True)
    for name, holes, fn in MUTS:
        if holes is not None and H not in (holes if isinstance(holes, (tuple, list)) else (holes,)):
            continue
        if ONLY and not any(k in name for k in ONLY):
            continue
        try:
            bpy.ops.wm.open_mainfile(filepath=BLEND, load_ui=False)
            C = m.st_ctx(H, dict(OPTS, look_dir=LOOK))
            look = LOOK
            if isinstance(fn, tuple):
                kind, edit = fn
                if kind == "TEX":
                    bak = f"{OUT}/Look_bak_{H}"
                    if os.path.isdir(bak):
                        shutil.rmtree(bak)
                    shutil.copytree(LOOK, bak)
                    look = LOOK
                else:
                    look = f"{OUT}/Look_{H}_{name}"
                    if os.path.isdir(look):
                        shutil.rmtree(look)
                    shutil.copytree(m.LOOK_DIR, look)
                m.IMG_CACHE.clear()
                edit(look)
                m.IMG_CACHE.clear()
            else:
                fn(C)
            mb = f"{OUT}/h{H}_{name}.blend"
            bpy.ops.wm.save_as_mainfile(filepath=mb, copy=True)
            mf = None
            if FBX and not isinstance(fn, tuple):
                mf = f"{OUT}/h{H}_{name}.fbx"
                m.st_export(H, mf)
            elif FBX:
                mf = POSFBX
            fails, res = run_check(mb, mf, look)
            if isinstance(fn, tuple) and fn[0] == "TEX":
                shutil.rmtree(LOOK)
                shutil.copytree(f"{OUT}/Look_bak_{H}", LOOK)
                m.IMG_CACHE.clear()
            print(f"MUT {H} {name} -> FAILED {[f for f in fails]}  NEW {[f for f in fails if f not in F0]}", flush=True)
            det = [r for r in res if not r["ok"] and r["name"] not in F0]
            for r in res:
                if os.environ.get("PCV_SHOW") and r["name"].split("@")[0] in os.environ["PCV_SHOW"].split(","):
                    print(f"  SHOW {r['name']} {'PASS' if r['ok'] else 'FAIL'}: {r['detail'][:300]}", flush=True)
            for r in det[:4]:
                print(f"     {r['name']}: {r['detail'][:230]}", flush=True)
            for p in (mb, mf):
                if p and p != POSFBX and os.path.exists(p):
                    os.remove(p)
        except Exception as e:  # noqa
            traceback.print_exc()
            print(f"MUT {H} {name} -> HARNESS-ERROR {type(e).__name__}: {e}", flush=True)


main()
