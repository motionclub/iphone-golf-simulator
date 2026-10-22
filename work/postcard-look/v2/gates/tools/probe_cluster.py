"""Probe rock_shape() on WELDED clusters of regular solids (the round-3 review attack) and on the real props library.
usage: blender -b --factory-startup --python probe_cluster.py
Cluster kinds: icosahedra (12 v) / icospheres (42 v) / octahedra / cubes that share a VERTEX or an EDGE with an earlier one, sizes varied, jitter before / after the weld.
Every cluster must FAIL rock_shape (ok False); every library ROCK_ kind must PASS."""
import sys, os, importlib.util, math
import numpy as np, bpy, bmesh
from mathutils import Vector
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import postcard_props_lib as PL
[PL.library_object(k) for k in sorted(PL.BUILDERS)]            # NOT ensure_library(): it writes Plants_C.png
S = m.Snap.__new__(m.Snap); S.stage = "fbx"; S._loc = {}; S._wld = {}


def template(kind):
    bm = bmesh.new()
    if kind == "ico12":
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    elif kind == "ico42":
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    elif kind == "octa":
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        bm.clear()
        vs = [bm.verts.new(p) for p in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
        for a, b, c in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)):
            bm.faces.new((vs[a], vs[b], vs[c]))
    elif kind == "cube":
        bmesh.ops.create_cube(bm, size=2.0)
    me = bpy.data.meshes.new("t"); bm.to_mesh(me); bm.free()
    P = np.array([v.co[:] for v in me.vertices]); F = [tuple(p.vertices) for p in me.polygons]
    bpy.data.meshes.remove(me)
    return P, F


def cluster(kind, n, seed, share="vertex", jitter_after=0.0, jitter_before=0.0, sizes=(0.7, 1.1)):
    rng = np.random.default_rng(seed)
    P0, F0 = template(kind)
    placed = []
    for k in range(n):
        s = rng.uniform(*sizes)
        Pn = P0 * s * (1 + rng.uniform(-jitter_before, jitter_before, P0.shape))
        if k == 0:
            off = np.zeros(3)
        else:
            Pj = placed[int(rng.integers(0, k))]
            if share == "vertex":
                b = int(rng.integers(0, len(Pj))); a = int(rng.integers(0, len(P0)))
                off = Pj[b] - Pn[a]
            else:                                           # an EDGE: align the first edge of the new cell with an edge of an earlier one
                e0 = [(i, j) for i in range(len(P0)) for j in range(i + 1, len(P0))
                      if abs(np.linalg.norm(P0[i] - P0[j]) - min(np.linalg.norm(P0[0] - P0[q]) for q in range(1, len(P0)))) < 1e-6]
                ia, ja = e0[int(rng.integers(0, len(e0)))]
                ej = [(i, j) for i in range(len(Pj)) for j in range(i + 1, len(Pj))
                      if abs(np.linalg.norm(Pj[i] - Pj[j]) - min(np.linalg.norm(Pj[0] - Pj[q]) for q in range(1, len(Pj)))) < 1e-6 * 100]
                ib, jb = ej[int(rng.integers(0, len(ej)))]
                # scale the new cell so its edge equals the earlier edge, then translate / rotate (rotation about the edge is ignored: only the first point matches exactly)
                Pn = Pn * (np.linalg.norm(Pj[ib] - Pj[jb]) / max(np.linalg.norm(Pn[ia] - Pn[ja]), 1e-9))
                off = Pj[ib] - Pn[ia]
        placed.append(Pn + off)
    bm = bmesh.new()
    verts = {}
    for k, Pn in enumerate(placed):
        loc = []
        for p in Pn:
            hit = None
            for q, v in verts.items():
                if np.linalg.norm(np.array(q) - p) < 1e-3:
                    hit = v
                    break
            if hit is None:
                hit = bm.verts.new(tuple(p)); verts[tuple(p)] = hit
            loc.append(hit)
        for f in F0:
            try:
                bm.faces.new([loc[i] for i in f])
            except ValueError:
                pass
    if jitter_after:
        for v in bm.verts:
            v.co = v.co + Vector(rng.uniform(-jitter_after, jitter_after, 3) * 0.5)
    me = bpy.data.meshes.new(f"CL_{kind}_{n}_{seed}")
    bm.to_mesh(me); bm.free()
    return me


def judge(me):
    ob = bpy.data.objects.new(me.name, me)
    bpy.context.scene.collection.objects.link(ob)
    r = m.rock_shape(S.loc(ob))
    return r


bad = 0
for kind in ("ico12", "ico42", "octa", "cube"):
    for share in ("vertex", "edge"):
        for n in (4, 6, 9, 14):
            for ja, jb in ((0.0, 0.0), (0.12, 0.0), (0.0, 0.12)):
                for seed in (1, 2):
                    me = cluster(kind, n, seed, share, jitter_after=ja, jitter_before=jb)
                    r = judge(me)
                    ok_bad = not r["ok"]
                    # a cluster that welds into a clean 'natural' blob is not what this probe tests: report only the verdict
                    tag = "FAILS(good)" if ok_bad else "PASSES(BAD)"
                    if not ok_bad:
                        bad += 1
                    print(f"CL {kind:5s} {share:6s} n={n:2d} jit_after={ja} jit_before={jb} seed={seed}: nv {r['nv']:3d} nf {r['nf']:3d} ncomp {r['ncomp']:2d} {tag} {[w[:60] for w in r['why'][:2]]}")
print("CLUSTERS PASSING THE ROCK TEST (should be 0):", bad)
lib = bpy.data.collections.get("ASSET_LIBRARY")
nl = 0
for o in sorted(lib.all_objects, key=lambda o: o.name):
    if o.type != "MESH" or not o.name.startswith("ROCK_") or o.name.endswith(("_WET", "_BASALT")):
        continue
    r = m.rock_shape(S.loc(o))
    nl += 0 if r["ok"] else 1
    print(f"LIB {o.name:22s} ok={r['ok']!s:5s} nv {r['nv']:4d} nf {r['nf']:4d} ncomp {r['ncomp']:3d} r2 {r['r2']:.2f} r3 {r['r3']:.2f} why {r['why'][:2]}")
print("LIBRARY KINDS FAILING THE ROCK TEST (should be 0):", nl)
