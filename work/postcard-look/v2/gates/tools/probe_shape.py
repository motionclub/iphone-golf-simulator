"""Probe rock_shape() (the v2 gate function) on every props-library ROCK_ kind and on attack meshes. Read-only use of the props lib."""
import sys, os, importlib.util, collections, math
import numpy as np, bpy, bmesh
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import postcard_props_lib as PL
[PL.library_object(k) for k in sorted(PL.BUILDERS)]   # NOT ensure_library(): it writes Plants_C.png
S = m.Snap.__new__(m.Snap); S.stage = "fbx"; S._loc = {}; S._wld = {}
def shape_of(ob): return m.rock_shape(S.loc(ob))
rows = []
lib = bpy.data.collections.get("ASSET_LIBRARY")
for o in sorted(lib.all_objects, key=lambda o: o.name):
    if o.type != "MESH" or not o.name.startswith("ROCK_") or o.name.endswith(("_WET", "_BASALT")): continue
    r = shape_of(o)
    print(f"LIB {o.name:22s} ok={r['ok']!s:5s} nv {r['nv']:4d} nf {r['nf']:4d} ncomp {r['ncomp']:3d} r2 {r['r2']:.2f} r3 {r['r3']:.2f} nfac {r['nfac']:2d} top {[round(x,2) for x in r['top']]} why {r['why'][:2]}")
# attacks
def ob_from_bm(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob
def ico_bundle(n, jitter, seed, sub=1):
    bm = bmesh.new(); rng = np.random.default_rng(seed)
    for k in range(n):
        tmp = bmesh.new(); bmesh.ops.create_icosphere(tmp, subdivisions=sub, radius=1.0)
        me = bpy.data.meshes.new("tmp"); tmp.to_mesh(me); tmp.free()
        c = rng.uniform(-1.2, 1.2, 3); vs = {}
        for v in me.vertices:
            vs[v.index] = bm.verts.new(np.array(v.co) * (0.5 + rng.uniform(-jitter, jitter)) * (1 + rng.uniform(-jitter, jitter, 3)) + c)
        for p in me.polygons: bm.faces.new([vs[i] for i in p.vertices])
        bpy.data.meshes.remove(me)
    return bm
for n in (5, 6, 7, 8):
    for j in (0.12, 0.25):
        r = shape_of(ob_from_bm(f"B{n}_{j}", ico_bundle(n, j, 3)))
        print(f"ATK bundle12 n={n} jitter={j}: ok={r['ok']} nv {r['nv']} nf {r['nf']} why {[w[:70] for w in r['why']]}")
for n in (3, 4):
    r = shape_of(ob_from_bm(f"B42_{n}", ico_bundle(n, 0.15, 5, sub=2)))
    print(f"ATK bundle42 n={n}: ok={r['ok']} nv {r['nv']} nf {r['nf']} why {[w[:70] for w in r['why']]}")
