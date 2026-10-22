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
OUT = f"{RV}/mut3"
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


@mut("RK_welded_ico_cluster_6")
def _(C):
    m._swap_all_rocks(lambda k: welded_cluster(7, k, 0.0))


@mut("RK_welded_ico_cluster_varied")
def _(C):
    m._swap_all_rocks(lambda k: welded_cluster(6 + (k * 3) % 9, 100 + k * 7, 0.0))


@mut("RK_welded_ico_cluster_jitter12")
def _(C):
    m._swap_all_rocks(lambda k: welded_cluster(7, k, 0.12))


@mut("FM_sloped_white_skirt_nz0.45")
def _(C):
    P, N, LID = m._shore(C, 2.0)
    V, F, k = [], [], 0
    for lid in sorted(set(LID.tolist())):
        idx = np.flatnonzero(LID == lid)
        prev = None
        for i in idx:
            a = (P[i][0], P[i][1], 3.0)
            # slope: 2.0 m horizontal drop 3.0 m? choose nz ~0.45 -> horizontal run = tan(acos .45)^-1 ; rise/run = sqrt(1-.2025)/.45 = 1.98
            b = (P[i][0] + N[i][0] * 1.5, P[i][1] + N[i][1] * 1.5, 3.0 - 1.5 * 1.98)
            base = len(V); V += [a, b]
            if prev is not None:
                F.append((prev, prev + 1, base + 1, base))
            prev = base
    me = m.st_mesh("WATER_SURF_90", V, F, "LK_SURF", uv=None)
    me.update()
    n = np.array([p.normal for p in me.polygons])
    print("skirt nz mean", float(np.abs(n[:, 2]).mean()))
    if len(me.polygons) and me.polygons[0].normal.z < 0:
        me.flip_normals()
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    lvv = np.empty(len(me.loops), np.int64); me.loops.foreach_get("vertex_index", lvv)
    zs = np.array([v.co.z for v in me.vertices])[lvv]
    cols = np.ones((len(lvv), 4)); cols[:, 3] = np.where(zs > zs.max() - 0.01, 1.0, 0.0)
    ca.data.foreach_set("color", cols.ravel())
    me.uv_layers.new(name="UVMap")
    lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get("vertex_index", lv)
    co = np.array([v.co[:] for v in me.vertices])
    me.uv_layers[0].data.foreach_set("uv", np.stack([co[lv][:, 0] / 8.0, co[lv][:, 1] / 8.0], 1).ravel())
    m._env("WATER_SURF_90", me)


@mut("FM_offshore_dashes_9m_gap9_at_12m")
def _(C):
    P, N, LID = m._shore(C, 2.0)
    k = 0
    for lid in sorted(set(LID.tolist())):
        idx = np.flatnonzero(LID == lid)
        i = int(idx[0]) + 2
        while i + 5 < idx[-1]:
            ii = np.arange(i, i + 5)
            me = m.st_strip(f"WATER_SURF_{80 + k}", P[ii], N[ii], 12.0, 16.0, 0.12, mat="LK_SURF", vcol=True, uv_world=8.0)
            m._env(f"WATER_SURF_{80 + k}", me)
            k += 1
            i += 5 + 5
    print("pieces", k)


@mut("FM_tiny_gaps_ring_at_12m_wide")
def _(C):
    P, N, LID = m._shore(C, 2.0)
    k = 0
    for lid in sorted(set(LID.tolist())):
        idx = np.flatnonzero(LID == lid)
        i = int(idx[0]) + 2
        while i + 7 < idx[-1]:
            ii = np.arange(i, i + 7)   # 12 m pieces
            me = m.st_strip(f"WATER_SURF_{80 + k}", P[ii], N[ii], 11.0, 14.0, 0.12, mat="LK_SURF", vcol=True, uv_world=8.0)
            m._env(f"WATER_SURF_{80 + k}", me)
            k += 1
            i += 7 + 5   # 10 m gaps
    print("pieces", k)


@mut("PL_on_floating_rock_lo2.9")
def _(C):
    x, y = water_pt(C, 20.0)
    me = new_hull("float2", dims=(3.0, 3.0, 3.0))
    co = np.array([v.co[:] for v in me.vertices])
    for v in me.vertices:
        v.co.z += 5.2 - co[:, 2].max()   # top 5.2, bottom ~2.2
    print("rock bottom", 5.2 - (co[:, 2].max() - co[:, 2].min()))
    m.st_obj("ROCK_MEDIUM.089", me, (x, y, 0), root=root())
    m.st_obj("PLANT_TUFT_ONROCK2", existing_plant_mesh(), (x, y, 5.2), root=root())


@mut("PL_on_floating_DRESS_BLOCK_z5.2")
def _(C):
    x, y = water_pt(C, 20.0)
    me = new_hull("float3", dims=(3.0, 3.0, 0.5), mat="LK_MASONRY")
    co = np.array([v.co[:] for v in me.vertices])
    for v in me.vertices:
        v.co.z += 5.2 - co[:, 2].max()
    m.st_obj("DRESS_BLOCK_77", me, (x, y, 0), root=root())
    m.st_obj("PLANT_TUFT_ONBLK", existing_plant_mesh(), (x, y, 5.2), root=root())


def face_edit(prefix, mode, idx=7, minnz=0.5):
    ob = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(prefix)][0]
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    mw = np.array(ob.matrix_world)
    ups = [f for f in bm.faces if (mw[:3, :3] @ np.array(f.normal))[2] > minnz]
    f = ups[min(idx, len(ups) - 1)]
    if mode == "del":
        bmesh.ops.delete(bm, geom=[f], context="FACES_ONLY")
    elif mode == "flip":
        bmesh.ops.reverse_faces(bm, faces=[f])
    elif mode == "lower":
        for v in f.verts:
            v.co.z -= 0.004
    elif mode == "swapdiag":
        pass
    bm.to_mesh(ob.data); bm.free()


for pre in ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER"):
    for mode in ("del", "flip"):
        def mk(pre=pre, mode=mode):
            def f(C):
                face_edit(pre, mode)
            return f
        MUTS.append((f"UP_{mode}_{pre}", None, mk()))


@mut("UP_del_TERRAIN_rim_tri")
def _(C):
    face_edit("TERRAIN", "del", idx=3)


@mut("UP_flip_TERRAIN_idx200")
def _(C):
    face_edit("TERRAIN", "flip", idx=200)


@mut("UP_del_TERRAIN_idx200")
def _(C):
    face_edit("TERRAIN", "del", idx=200)


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
