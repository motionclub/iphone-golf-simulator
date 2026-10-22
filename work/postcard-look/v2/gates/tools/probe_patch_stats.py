"""Per-patch statistics (valence mix, edge / area variation) of every props-library rock patch versus 'perturbed icosahedra' (one edge subdivided, jitter 0..40 %),
and the synthetic hull stones. usage: blender -b --factory-startup --python probe_patch_stats.py"""
import sys, importlib.util, collections
import numpy as np, bpy, bmesh
from mathutils import Vector
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import postcard_props_lib as PL
[PL.library_object(k) for k in sorted(PL.BUILDERS)]
S = m.Snap.__new__(m.Snap); S.stage = "fbx"; S._loc = {}; S._wld = {}


def patches(L):
    wid = m.weld_ids(L["V"]); nw = int(wid.max()) + 1
    P = np.zeros((nw, 3)); np.add.at(P, wid, L["V"]); P /= np.maximum(np.bincount(wid, minlength=nw), 1)[:, None]
    Tw = wid[L["T"]]; A = L["A"]
    ok = (Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2]) & (A > 1e-12)
    Tk, Ak, Nk, tpk = Tw[ok], A[ok], L["N"][ok], L["tp"][ok]
    P2, T2, npatch = m.manifold_patches(P, Tk, tpk)
    lab = m.tri_components(T2)
    val, bnd = m.poly_valences(T2, tpk)
    out = []
    for c in np.unique(lab):
        sel = lab == c
        verts = np.unique(T2[sel])
        interior = [v for v in verts.tolist() if v not in bnd]
        if len(interior) < 6: continue
        vals = [val[v] for v in interior]
        cnt = collections.Counter(vals)
        rcv, ecv, acv, _ = m.tess_numbers(P2, T2[sel], Ak[sel])
        out.append(dict(n=len(interior), f5=cnt.get(5, 0) / len(vals), f56=(cnt.get(5, 0) + cnt.get(6, 0)) / len(vals), distinct=len(cnt), hist=dict(sorted(cnt.items())), rcv=rcv, ecv=ecv, acv=acv))
    return out


def report(tag, pl):
    for p in pl:
        print(f"PATCH {tag:34s} n {p['n']:3d} f5 {p['f5']:.2f} f56 {p['f56']:.2f} distinct {p['distinct']} hist {p['hist']} rcv {p['rcv']:.2f} ecv {p['ecv']:.2f} acv {p['acv']:.2f}")


lib = bpy.data.collections.get("ASSET_LIBRARY")
allp = []
for o in sorted(lib.all_objects, key=lambda o: o.name):
    if o.type != "MESH" or not o.name.startswith("ROCK_") or "BASALT" in o.name: continue
    pl = patches(S.loc(o))
    allp += pl
    report(o.name, pl)
print("LIB patches", len(allp), "max f5 %.2f" % max(p["f5"] for p in allp), "max f56 %.2f" % max(p["f56"] for p in allp), "min ecv %.2f" % min(p["ecv"] for p in allp), "min acv %.2f" % min(p["acv"] for p in allp), "min rcv %.2f" % min(p["rcv"] for p in allp))


def ob_from(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob


def perturbed(jit, seed, splits=1):
    rng = np.random.default_rng(seed)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    for _ in range(splits):
        bm.edges.ensure_lookup_table()
        bmesh.ops.subdivide_edges(bm, edges=[bm.edges[int(rng.integers(0, len(bm.edges)))]], cuts=1, use_grid_fill=False)
    for v in bm.verts:
        v.co = v.co * (1 + rng.uniform(-jit, jit)) + Vector(rng.uniform(-jit, jit, 3) * 0.3)
    return ob_from(f"PI_{jit}_{seed}", bm)


for splits in (0, 1, 2):
    for jit in (0.0, 0.12, 0.25, 0.4):
        pl = []
        for seed in range(6):
            pl += patches(S.loc(perturbed(jit, seed, splits)))
        if pl:
            print(f"ATK splits={splits} jit={jit}: n {sorted(set(p['n'] for p in pl))} f5 {min(p['f5'] for p in pl):.2f}..{max(p['f5'] for p in pl):.2f} f56 min {min(p['f56'] for p in pl):.2f} distinct {sorted(set(p['distinct'] for p in pl))} ecv {min(p['ecv'] for p in pl):.2f}..{max(p['ecv'] for p in pl):.2f} acv {min(p['acv'] for p in pl):.2f}..{max(p['acv'] for p in pl):.2f} rcv {min(p['rcv'] for p in pl):.2f}..{max(p['rcv'] for p in pl):.2f}")
        else:
            print(f"ATK splits={splits} jit={jit}: no patch with >= 6 interior vertices")
# synthetic hull stones
hs = []
for seed in range(1, 25):
    me = m.st_hull_rock("H%d" % seed, seed, "LK_ROCK", dims=(2.0, 1.6, 1.2))
    ob = bpy.data.objects.new("H%d" % seed, me); bpy.context.scene.collection.objects.link(ob)
    hs += patches(S.loc(ob))
print("SYN hull stones: patches", len(hs), "n", min(p['n'] for p in hs), "..", max(p['n'] for p in hs), "f5 max %.2f" % max(p['f5'] for p in hs), "f56 max %.2f" % max(p['f56'] for p in hs), "ecv min %.2f" % min(p['ecv'] for p in hs), "acv min %.2f" % min(p['acv'] for p in hs))
