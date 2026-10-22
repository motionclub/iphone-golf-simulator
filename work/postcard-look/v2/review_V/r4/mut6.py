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
ST = f"{RV}/r4/st/h{H}"
BLEND = f"{ST}/hole_{H:02d}_pos.blend"
LOOK = f"{ST}/Look"
POSFBX = f"{ST}/hole_{H:02d}_pos.fbx"
if os.environ.get("PCV_BASE") == "lib":
    FX = RV + "/../gates/fixtures"
    BLEND = f"{FX}/lib_smoke_now/hole_{H:02d}.blend"
    POSFBX = f"{FX}/lib_smoke_now/hole_{H:02d}.fbx"
    LOOK = f"{FX}/look_at_run"
OUT = f"{RV}/r4/out_mut6"
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


def existing_plant_mesh():
    ps = m._ob("PLANT_")
    return ps[0].data if ps else plant_mesh()



sys.path.insert(0, REPO + "/blender/scripts")
import postcard_props_lib as PL


def libmesh(kind, bake=None):
    lo = PL.library_object(kind)
    me = bpy.data.meshes.new("L_" + kind)
    me.from_pydata([tuple(v.co) for v in lo.data.vertices], [], [tuple(p.vertices) for p in lo.data.polygons])
    if bake:
        for v in me.vertices:
            v.co.x *= bake[0]; v.co.y *= bake[1]; v.co.z *= bake[2]
    me.materials.append(bpy.data.materials["LK_ROCK"])
    me.update()
    m.st_box_uv(me)
    return me


def land_pt(C, k=0):
    S = m._snap(C)
    rng = np.random.default_rng(3 + k)
    c = m.st_candidates(C, S, 3, rng, kind="rough", clear=0.0)
    return c[0]


@mut("LB_libkind_baked_4x0.5_unit_scale")
def _(C):
    p = land_pt(C)
    for kind in ("ROCK_BOULDER_A", "ROCK_CRAG_A", "ROCK_SLAB_A"):
        pass
    m.st_obj("ROCK_BOULDER_A.900", libmesh("ROCK_BOULDER_A", (4.0, 0.5, 1.0)), (p[0], p[1], p[2] + 0.2), root=root())


@mut("LB_libkind_baked_3x1_renamed_CAIRN")
def _(C):
    p = land_pt(C)
    m.st_obj("ROCK_CAIRN_77", libmesh("ROCK_SLAB_A", (3.0, 1.0, 1.0)), (p[0], p[1], p[2] + 0.2), root=root())


@mut("LB_libkind_baked_1.8x_control_pass")
def _(C):
    p = land_pt(C)
    m.st_obj("ROCK_BOULDER_A.901", libmesh("ROCK_BOULDER_A", (1.8, 1.0, 1.0)), (p[0], p[1], p[2] + 0.2), root=root())


@mut("LB_libkind_baked_stretch_plus_chip_removed")
def _(C):
    # stretched library mesh with ONE vertex nudged and a face dropped -> topology hash differs from the library
    p = land_pt(C)
    me = libmesh("ROCK_SLAB_A", (4.0, 0.6, 1.0))
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[0]], context="FACES_ONLY")
    bm.to_mesh(me); bm.free()
    m.st_obj("ROCK_SLAB_77", me, (p[0], p[1], p[2] + 0.2), root=root())


@mut("LB_lib_scale_2_2_0.5")
def _(C):
    p = land_pt(C)
    m.st_obj("ROCK_BOULDER_A.902", libmesh("ROCK_BOULDER_A"), (p[0], p[1], p[2] + 0.2), (2.0, 2.0, 0.5), root=root())


@mut("LB_lib_scale_1.9_1.9_1.0_control")
def _(C):
    p = land_pt(C)
    m.st_obj("ROCK_BOULDER_A.903", libmesh("ROCK_BOULDER_A"), (p[0], p[1], p[2] + 0.2), (1.9, 1.9, 1.0), root=root())


@mut("LB_lib_rock_normal_control")
def _(C):
    p = land_pt(C)
    for k, kind in enumerate(("ROCK_BOULDER_A", "ROCK_BLOCK_A", "ROCK_CRAG_B", "ROCK_STONE_A", "ROCK_LEDGE_A")):
        q = land_pt(C, k + 1)
        m.st_obj(f"{kind}.91{k}", libmesh(kind), (q[0], q[1], q[2] + 0.1), root=root())


def welded_cluster(n, seed, jitter):
    # icosahedra that SHARE vertices with each other (weld) -> valence set {5,10,15,...}
    rng = np.random.default_rng(seed)
    bm = bmesh.new()
    tmpl = bmesh.new(); bmesh.ops.create_icosphere(tmpl, subdivisions=1, radius=1.0)
    me0 = bpy.data.meshes.new("t"); tmpl.to_mesh(me0)
    P0 = np.array([v.co[:] for v in me0.vertices]); F0 = [tuple(p.vertices) for p in me0.polygons]
    # sphere subdivisions=1 gives 12 verts? check
    placed = []
    for k in range(n):
        s = rng.uniform(0.7, 1.1)
        R = np.eye(3)
        if k == 0:
            off = np.zeros(3)
        else:
            j = rng.integers(0, k)
            # attach so that vertex a of new coincides with vertex b of a previous one
            Pj, = [placed[j]]
            a = rng.integers(0, len(P0)); b = rng.integers(0, len(Pj))
            off = Pj[b] - P0[a] * s
        Pn = P0 * s * (1 + rng.uniform(-jitter, jitter, P0.shape)) + off
        placed.append(Pn)
    vs = {}
    allv = []
    for Pn in placed:
        ids = []
        for p in Pn:
            key = tuple(np.round(p, 4))
            ids.append(key)
        allv.append(ids)
    # weld exact-coincident pairs: re-anchor coincident vertices exactly
    verts = {}
    for k, Pn in enumerate(placed):
        for i, p in enumerate(Pn):
            pass
    bmv = {}
    for k, Pn in enumerate(placed):
        loc = []
        for i, p in enumerate(Pn):
            hit = None
            for q, v in bmv.items():
                if np.linalg.norm(np.array(q) - p) < 1e-3:
                    hit = v; break
            if hit is None:
                hit = bm.verts.new(tuple(p)); bmv[tuple(p)] = hit
            loc.append(hit)
        for f in F0:
            try:
                bm.faces.new([loc[i] for i in f])
            except ValueError:
                pass
    return m.st_bm_mesh("WELDCL", bm, "LK_ROCK")



def pale_mat(name, v):
    mt = bpy.data.materials.new(name)
    mt.use_nodes = True
    for nd in mt.node_tree.nodes:
        if nd.type == "BSDF_PRINCIPLED":
            nd.inputs["Base Color"].default_value = (v, v, v, 1.0)
    mt.diffuse_color = (v, v, v, 1.0)
    return mt


def ring_strip(C, name, o0, o1, z, matname, uvw=8.0):
    P, N, LID = m._shore(C, 2.0)
    k = 0
    for lid in sorted(set(LID.tolist())):
        idx = np.flatnonzero(LID == lid)
        me = m.st_strip(f"{name}_{k}", P[idx], N[idx], o0, o1, z, mat=matname, vcol=False, uv_world=uvw)
        m._env(f"{name}_{k}", me)
        k += 1


@mut("FM_pale_lin0.70_band_1.5to4")
def _(C):
    pale_mat("MAT_PALE70", 0.70)
    ring_strip(C, "WATER_WASH", 1.5, 4.0, 0.12, "MAT_PALE70")


@mut("FM_pale_lin0.55_band_1.5to4")
def _(C):
    pale_mat("MAT_PALE55", 0.55)
    ring_strip(C, "WATER_WASH", 1.5, 4.0, 0.12, "MAT_PALE55")


@mut("FM_pale_lin0.79_band_1.5to4")
def _(C):
    pale_mat("MAT_PALE79", 0.79)
    ring_strip(C, "WATER_WASH", 1.5, 4.0, 0.12, "MAT_PALE79")


@mut("FM_thin_3cm_line_LK_SURF")
def _(C):
    ring_strip(C, "WATER_SURF_7", 1.0, 1.03, 0.12, "LK_SURF")


@mut("FM_fall_sheets_8m_ring")
def _(C):
    P, N, LID = m._shore(C, 2.0)
    k = 0
    for lid in sorted(set(LID.tolist())):
        idx = np.flatnonzero(LID == lid)
        i = int(idx[0]) + 1
        while i + 4 < idx[-1]:
            ii = np.arange(i, i + 4)    # 6 m
            me = m.st_strip(f"WATER_FALL_{k}", P[ii], N[ii], 2.0, None, -1.0, z1=3.0, mat="LK_FALL", uv_world=8.0)
            m._env(f"WATER_FALL_{k}", me)
            k += 1
            i += 4 + 5
    print("sheets", k)


@mut("FM_fall_two_sheets_control_pass")
def _(C):
    P, N, LID = m._shore(C, 2.0)
    for k in range(2):
        ii = np.arange(10 + 20 * k, 13 + 20 * k)
        me = m.st_strip(f"WATER_FALL_{k}", P[ii], N[ii], 2.0, None, -1.0, z1=3.0, mat="LK_FALL", uv_world=8.0)
        m._env(f"WATER_FALL_{k}", me)


def mk_hull_named(name, dims, seed=5):
    p = land_pt(C_GLOBAL[0])
    me = new_hull(name, seed=seed, dims=dims)
    return p, me


C_GLOBAL = [None]


@mut("RK_ico42_named_DRESS_BOULDER")
def _(C):
    p = land_pt(C)
    m.st_obj("DRESS_BOULDER_1", ico(1, 0.0, 1), (p[0], p[1], p[2] + 0.5), root=root())
    p = land_pt(C, 2)
    m.st_obj("DRESS_BOULDER_2", ico(2, 0.15, 2), (p[0], p[1], p[2] + 0.5), root=root())


@mut("RK_ico42_named_WATER_STONE")
def _(C):
    p = land_pt(C)
    m.st_obj("WATER_STONE_1", ico(2, 0.0, 1), (p[0], p[1], p[2] + 0.5), root=root())


@mut("RK_ico12_named_WATER_STONE")
def _(C):
    p = land_pt(C)
    me = m._ico("WS12", sub=1)
    m.st_obj("WATER_STONE_1", me, (p[0], p[1], p[2] + 0.5), root=root())


@mut("RK_ico12_named_LAVA_ROCK")
def _(C):
    p = land_pt(C)
    me = m._ico("LR12", sub=1)
    m.st_obj("LAVA_ROCK_1", me, (p[0], p[1], p[2] + 0.5), root=root())


@mut("RK_ico12_named_PLANT_ROCK")
def _(C):
    p = land_pt(C)
    me = m._ico("PR12", sub=1)
    m.st_obj("PLANT_ROCK_1", me, (p[0], p[1], p[2] + 0.5), root=root())


def cluster_template(n_sub_edges=1):
    tmpl = bmesh.new(); bmesh.ops.create_icosphere(tmpl, subdivisions=1, radius=1.0)
    tmpl.edges.ensure_lookup_table()
    if n_sub_edges:
        bmesh.ops.subdivide_edges(tmpl, edges=[tmpl.edges[0]], cuts=1, use_grid_fill=False)
        # triangulate the n-gon fans
        bmesh.ops.triangulate(tmpl, faces=list(tmpl.faces))
    me0 = bpy.data.meshes.new("t"); tmpl.to_mesh(me0)
    P0 = np.array([v.co[:] for v in me0.vertices]); F0 = [tuple(p.vertices) for p in me0.polygons]
    return P0, F0


def welded_cluster_t(n, seed, jitter, P0, F0):
    rng = np.random.default_rng(seed)
    bm = bmesh.new()
    placed = []
    for k in range(n):
        s = rng.uniform(0.7, 1.1)
        if k == 0:
            off = np.zeros(3)
        else:
            j = rng.integers(0, k)
            Pj = placed[j]
            a = rng.integers(0, len(P0)); b = rng.integers(0, len(Pj))
            off = Pj[b] - P0[a] * s
        placed.append(P0 * s * (1 + rng.uniform(-jitter, jitter, P0.shape)) + off)
    bmv = {}
    for k, Pn in enumerate(placed):
        loc = []
        for i, p in enumerate(Pn):
            hit = None
            for q, v in bmv.items():
                if np.linalg.norm(np.array(q) - p) < 1e-3:
                    hit = v; break
            if hit is None:
                hit = bm.verts.new(tuple(p)); bmv[tuple(p)] = hit
            loc.append(hit)
        for f in F0:
            try:
                bm.faces.new([loc[i] for i in f])
            except ValueError:
                pass
    return m.st_bm_mesh("WELDCL2", bm, "LK_ROCK")


@mut("RK_welded_cluster_one_edge_subdivided")
def _(C):
    P0, F0 = cluster_template(1)
    print("template verts", len(P0), "faces", len(F0))
    m._swap_all_rocks(lambda k: welded_cluster_t(6 + (k * 3) % 9, 100 + k * 7, 0.08, P0, F0))


@mut("RK_welded_cluster_plain_ico_jitter08")
def _(C):
    P0, F0 = cluster_template(0)
    m._swap_all_rocks(lambda k: welded_cluster_t(6 + (k * 3) % 9, 100 + k * 7, 0.08, P0, F0))


def rot_bake(kind, rz, bake):
    lo = PL.library_object(kind)
    c, s = math.cos(rz), math.sin(rz)
    me = bpy.data.meshes.new("L_" + kind)
    vs = []
    for v in lo.data.vertices:
        x, y, z = v.co
        x, y = c * x - s * y, s * x + c * y
        vs.append((x * bake[0], y * bake[1], z * bake[2]))
    me.from_pydata(vs, [], [tuple(p.vertices) for p in lo.data.polygons])
    me.materials.append(bpy.data.materials["LK_ROCK"])
    me.update(); m.st_box_uv(me)
    return me


@mut("SW_lib_rot30_then_baked_3x_ROCK")
def _(C):
    p = land_pt(C)
    m.st_obj("ROCK_BOULDER_A.920", rot_bake("ROCK_BOULDER_A", 0.5, (3.0, 1.0, 1.0)), (p[0], p[1], p[2] + 0.3), root=root())


@mut("SW_lib_rot30_then_baked_4x_0.5_ROCK")
def _(C):
    p = land_pt(C)
    m.st_obj("ROCK_BOULDER_A.921", rot_bake("ROCK_BOULDER_A", 0.5, (4.0, 0.6, 1.0)), (p[0], p[1], p[2] + 0.3), root=root())


@mut("SW_handmade_hull_5x0.4_named_DRESS_STONE")
def _(C):
    p = land_pt(C)
    me = new_hull("hh", seed=9, dims=(2.0, 1.6, 1.2))
    for v in me.vertices:
        v.co.x *= 5.0; v.co.z *= 0.4
    me.update()
    m.st_obj("DRESS_STONE_9", me, (p[0], p[1], p[2] + 0.3), root=root())


@mut("SW_handmade_hull_5x0.4_named_ROCK_control_fail")
def _(C):
    p = land_pt(C)
    me = new_hull("hh2", seed=9, dims=(2.0, 1.6, 1.2))
    for v in me.vertices:
        v.co.x *= 5.0; v.co.z *= 0.4
    me.update()
    m.st_obj("ROCK_STONE_9", me, (p[0], p[1], p[2] + 0.3), root=root())


@mut("SW_handmade_hull_5x0.4_named_WATER_STONE")
def _(C):
    p = land_pt(C)
    me = new_hull("hh3", seed=9, dims=(2.0, 1.6, 1.2))
    for v in me.vertices:
        v.co.x *= 5.0; v.co.z *= 0.4
    me.update()
    m.st_obj("WATER_STONE_9", me, (p[0], p[1], p[2] + 0.3), root=root())


@mut("WL_extra_vertical_wall_added_to_TERRAIN")
def _(C):
    ob = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("TERRAIN")][0]
    pin = m._pin()
    bm = bmesh.new(); bm.from_mesh(ob.data)
    inv = np.linalg.inv(np.array(ob.matrix_world))
    def loc(p):
        return tuple((inv @ np.array([p[0], p[1], p[2], 1.0]))[:3])
    x, y = float(pin[0]) + 4.0, float(pin[1])
    z0 = float(pin[2]) if len(pin) > 2 else 0.0
    vs = [bm.verts.new(loc(q)) for q in ((x, y - 3, z0 - 1), (x, y + 3, z0 - 1), (x, y + 3, z0 + 3), (x, y - 3, z0 + 3))]
    bm.faces.new(vs)
    bm.to_mesh(ob.data); bm.free()


@mut("WL_extra_vertical_wall_added_to_FAIRWAY")
def _(C):
    ob = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("FAIRWAY")][0]
    pin = m._pin()
    bm = bmesh.new(); bm.from_mesh(ob.data)
    inv = np.linalg.inv(np.array(ob.matrix_world))
    def loc(p):
        return tuple((inv @ np.array([p[0], p[1], p[2], 1.0]))[:3])
    x, y = float(pin[0]) - 12.0, float(pin[1])
    z0 = float(pin[2]) if len(pin) > 2 else 0.0
    vs = [bm.verts.new(loc(q)) for q in ((x, y - 3, z0 - 1), (x, y + 3, z0 - 1), (x, y + 3, z0 + 3), (x, y - 3, z0 + 3))]
    bm.faces.new(vs)
    bm.to_mesh(ob.data); bm.free()


@mut("WL_nonup_poly_nudge_1mm_control")
def _(C):
    # a 0.3 mm move of one wall vertex: below tolerance? (control: should it pass? 1e-4 rounding)
    ob = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("TERRAIN")][0]
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    mw = np.array(ob.matrix_world)
    ws = [f for f in bm.faces if abs((mw[:3, :3] @ np.array(f.normal))[2]) < 0.3]
    f = max(ws, key=lambda q: q.calc_area())
    f.verts[0].co.x += 0.0003
    bm.to_mesh(ob.data); bm.free()


@mut("WL_nonup_poly_lower_vertex_2mm")
def _(C):
    ob = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("TERRAIN")][0]
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    mw = np.array(ob.matrix_world)
    ws = [f for f in bm.faces if abs((mw[:3, :3] @ np.array(f.normal))[2]) < 0.3]
    f = max(ws, key=lambda q: q.calc_area())
    f.verts[0].co.y += 0.002
    bm.to_mesh(ob.data); bm.free()

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



@mut("SS_ziggurat_named_DRESS_STACK")
def _(C):
    x, y = water_pt(C, 45.0)
    me = ziggurat("ZIGD"); m.st_box_uv(me)
    m.st_obj("DRESS_STACK_99", me, (x, y, 0), root=root())


@mut("SS_ziggurat_named_ROCK_WALL")
def _(C):
    x, y = water_pt(C, 45.0)
    me = ziggurat("ZIGW"); m.st_box_uv(me)
    m.st_obj("ROCK_WALL_99", me, (x, y, 0), root=root())

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
