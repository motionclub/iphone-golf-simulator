"""Reviewer's independent checks of postcard_look_lib (A3) on the smoke outputs in review_ground/smoke_holeNN.
Does NOT use postcard_look_lib's own gate code. Blender headless:
  Blender -b --factory-startup --python review_check.py -- --hole 08
"""
import sys, os, json, math, time, runpy
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
SCRIPTS = os.path.join(REPO, "blender", "scripts")
sys.path.insert(0, SCRIPTS)
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import postcard_lib as P

args = sys.argv[sys.argv.index("--") + 1:]
H = args[args.index("--hole") + 1].zfill(2)
RG = os.path.join(REPO, "work", "postcard-look", "review_ground")
SM = os.path.join(RG, f"smoke_hole{H}")
OUT = os.path.join(RG, f"check_hole{H}")
os.makedirs(OUT, exist_ok=True)
FROZEN = os.path.join(REPO, "work", "postcard-look", "baseline", "blender", f"hole_{H}.blend")
BASE = os.path.join(SM, "base", f"hole_{H}.blend")
LOOK = os.path.join(SM, f"smoke_hole{H}.blend")
FBX = os.path.join(SM, "look", f"hole_{H}.fbx")
GP = P.GROUND_PREFIXES
RES = []


def gate(name, ok, detail):
    RES.append(dict(name=name, ok=bool(ok), detail=detail))
    print(f"GATE: R_{name} {'PASS' if ok else 'FAIL'} - {detail}", flush=True)


def info(msg):
    print(f"INFO: {msg}", flush=True)


# ---------------------------------------------------------------- design handle D (frozen baseline build into scratch)
_orig = P.start
P.start = lambda name, out_dir=None: _orig(name, out_dir=os.path.join(OUT, "D_build"))
sys.argv = [os.path.join(REPO, "work/postcard-look/baseline/scripts", f"hole{H}_build.py")]
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit:
    pass
P.start = _orig
D = P._ST["D"]
PZ = D.play_z
info(f"D built: play_z {PZ}, {len(D.loops)} loops")


def export_objs():
    out, seen = [], set()

    def walk(c):
        for o in c.objects:
            if o.name not in seen and o.type in ("MESH", "EMPTY"):
                seen.add(o.name)
                out.append(o)
        for ch in c.children:
            walk(ch)
    for cn in ("COURSE", "ENVIRONMENT", "STRUCTURES", "GAMEPLAY"):
        c = bpy.data.collections.get(cn)
        if c:
            walk(c)
    return out


def mesh_data(o):
    me = o.data
    nv, npl, nl = len(me.vertices), len(me.polygons), len(me.loops)
    co = np.empty(nv * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    mw = np.array(o.matrix_world)
    W = co @ mw[:3, :3].T + mw[:3, 3]
    ls = np.empty(npl, np.int64); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(npl, np.int64); me.polygons.foreach_get("loop_total", lt)
    lv = np.empty(nl, np.int64); me.loops.foreach_get("vertex_index", lv)
    mi = np.empty(npl, np.int64); me.polygons.foreach_get("material_index", mi)
    mats = [m.name if m else "" for m in me.materials]
    uv = None
    if len(me.uv_layers):
        uv = np.empty(nl * 2); me.uv_layers[0].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    polys = [lv[a:a + n].tolist() for a, n in zip(ls.tolist(), lt.tolist())]
    # world normals from geometry (Newell)
    pn = np.zeros((npl, 3))
    for p, vs in enumerate(polys):
        Q = W[vs]
        Q2 = np.roll(Q, -1, 0)
        pn[p] = [((Q[:, 1] - Q2[:, 1]) * (Q[:, 2] + Q2[:, 2])).sum(), ((Q[:, 2] - Q2[:, 2]) * (Q[:, 0] + Q2[:, 0])).sum(),
                 ((Q[:, 0] - Q2[:, 0]) * (Q[:, 1] + Q2[:, 1])).sum()]
    area = 0.5 * np.linalg.norm(pn, axis=1)
    pn = pn / np.maximum(np.linalg.norm(pn, axis=1), 1e-12)[:, None]
    cols = {a.name: a for a in me.color_attributes}
    return dict(W=W, ls=ls, lt=lt, lv=lv, mi=mi, mats=mats, uv=uv, polys=polys, pn=pn, area=area,
                nuv=len(me.uv_layers), cols=list(cols), data_name=me.name)


def load(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    out = {}
    for o in export_objs():
        if o.type == "MESH":
            out[o.name] = mesh_data(o)
        else:
            out[o.name] = dict(empty=True, loc=tuple(o.matrix_world.translation))
    allmats = {m.name: m.users for m in bpy.data.materials}
    return out, allmats


def bvh(data, names, up_only=False):
    V, F = [], []
    for n in names:
        d = data[n]
        b = len(V)
        V += [tuple(p) for p in d["W"].tolist()]
        for p, vs in enumerate(d["polys"]):
            if up_only and d["pn"][p, 2] <= 0.0:
                continue
            F.append([b + v for v in vs])
    return BVHTree.FromPolygons(V, F) if F else None


t0 = time.time()
frozen, fm = load(FROZEN)
look, lm = load(LOOK)
info(f"loaded frozen {len(frozen)} objs, look {len(look)} objs ({time.time() - t0:.1f}s)")

# ================================================================ (1) top surfaces unchanged vs the FROZEN repo baseline
gf = sorted(n for n in frozen if n.startswith(GP))
gl = sorted(n for n in look if n.startswith(GP))
bad, worst, nv = [], 0.0, 0
for n in gf:
    if n not in look:
        bad.append(f"{n} missing"); continue
    a, b = frozen[n], look[n]
    if a["W"].shape != b["W"].shape:
        bad.append(f"{n} verts {len(a['W'])}->{len(b['W'])}"); continue
    d = float(np.abs(a["W"] - b["W"]).max()) if len(a["W"]) else 0.0
    worst = max(worst, d); nv += len(a["W"])
    if d > 1e-6:
        bad.append(f"{n} moved {d:.2e}")
    if not np.array_equal(a["lv"], b["lv"]) or not np.array_equal(a["lt"], b["lt"]):
        bad.append(f"{n} topology changed")
gate("TOP_VERTS_VS_FROZEN_BASELINE", gf == gl and not bad,
     f"frozen {FROZEN.split('work/')[-1]}: ground meshes frozen {len(gf)} / look {len(gl)} (same set {gf == gl}), {nv} vertices, "
     f"max |delta| {worst:.2e} m, topology equal; problems {bad[:5]}")

# ---- height-from-above grid
bx0, by0, bx1, by1 = P._shore_bbox_m(D)
step = 0.75
xs = np.arange(bx0 - 30, bx1 + 30, step)
ys = np.arange(by0 - 30, by1 + 30, step)
GX, GY = np.meshgrid(xs, ys, indexing="ij")
X, Y = GX.ravel(), GY.ravel()
lie = P.lie_codes_m(D, X, Y)
sd = P.signed_dist_m(D, X, Y)


def heights(tree, X, Y, z0=60.0):
    out = np.full(len(X), np.nan)
    if tree is None:
        return out
    d = Vector((0, 0, -1))
    for i, (x, y) in enumerate(zip(X.tolist(), Y.tolist())):
        h = tree.ray_cast(Vector((x, y, z0)), d, 200.0)
        if h[0] is not None:
            out[i] = h[0].z
    return out


t0 = time.time()
hf = heights(bvh(frozen, gf), X, Y)
hl = heights(bvh(look, gl), X, Y)
same_mask = np.array_equal(np.isnan(hf), np.isnan(hl))
dh = np.nanmax(np.abs(hf - hl)) if (~np.isnan(hf)).any() else 0.0
gate("GROUND_HEIGHT_GRID_IDENTICAL", same_mask and dh < 1e-6,
     f"{len(X)} points at {step} m over the shore box +30 m, ground-only ray casts from z 60: hit masks equal {same_mask}, "
     f"max |dz| {dh:.2e} m, land hits {int((~np.isnan(hl)).sum())} ({time.time() - t0:.1f}s)")

new_names = [n for n in look if n not in frozen and "empty" not in look[n]]
changed_water = [n for n in look if n.startswith("WATER_") and n in frozen]
lib_names = sorted(set(new_names + changed_water))
info(f"new / rebuilt look objects: {len(lib_names)}: {sorted(set(n.rstrip('0123456789').rstrip('_') for n in lib_names))}")
by_prefix = {}
for n in lib_names:
    k = "ROCK_SKIN" if n.startswith("ROCK_SKIN") else ("WATER_SURF" if n.startswith("WATER_SURF") else
                                                       ("DRESS_PATH" if n.startswith("DRESS_PATH") else n))
    by_prefix.setdefault(k, []).append(n)
land = ~np.isnan(hl)
hazard_water = np.zeros(len(X), bool)
for kind, hx, hd, w, l, tag in D.hole.hazards:
    if kind == "water":
        cx, cy = P.m(hx, hd)
        hazard_water |= ((X - cx) / (w / 2 * P.YD)) ** 2 + ((Y - cy) / (l / 2 * P.YD)) ** 2 <= 1
above = {}
for k, ns in sorted(by_prefix.items()):
    hk = heights(bvh(look, ns), X, Y)
    over_land = land & ~np.isnan(hk) & (hk > hl + 1e-4)
    in_haz = hazard_water & (lie == P.LIE_WATER) & ~np.isnan(hk) & (hk > 0.2)
    out_shore = ~hazard_water & (lie == P.LIE_WATER) & ~np.isnan(hk) & (hk > 0.2)
    above[k] = dict(over_land=int(over_land.sum()), over_land_max_dz=float(np.nanmax((hk - hl)[over_land])) if over_land.any() else 0.0,
                    in_hazard_ellipse=int(in_haz.sum()), in_hazard_max_z=float(np.nanmax(hk[in_haz])) if in_haz.any() else 0.0,
                    in_hazard_max_dist_from_shore=float(sd[in_haz].max()) if in_haz.any() else 0.0,
                    water_outside_shore=int(out_shore.sum()), water_max_z=float(np.nanmax(hk[out_shore])) if out_shore.any() else 0.0,
                    water_max_dist_from_shore=float(sd[out_shore].max()) if out_shore.any() else 0.0)
    info(f"from above, {k}: {above[k]}")
lib_over_land = {k: v["over_land"] for k, v in above.items() if v["over_land"] and k != "DRESS_PATH"}
gate("NO_LIB_GEOMETRY_ABOVE_PLAY_SURFACE", not lib_over_land,
     f"grid points where a lib mesh is the top hit above the ground collider (DRESS_PATH excluded, it is meant to sit 3.5 cm "
     f"on top): {lib_over_land}; DRESS_PATH {above.get('DRESS_PATH', {}).get('over_land', 0)} pts, max +{above.get('DRESS_PATH', {}).get('over_land_max_dz', 0):.3f} m")
sk = above.get("ROCK_SKIN", {})
gate("SKIN_UPFACE_IN_WATER_ELLIPSES", sk.get("in_hazard_ellipse", 0) == 0,
     f"grid points ({step} m cells = {step * step:.2f} m2 each) inside a scoring water ellipse where ROCK_SKIN is hit from above "
     f"above z 0.2: {sk.get('in_hazard_ellipse', 0)} (= {sk.get('in_hazard_ellipse', 0) * step * step:.0f} m2), highest {sk.get('in_hazard_max_z', 0):.2f} m, "
     f"reaching {sk.get('in_hazard_max_dist_from_shore', 0):.2f} m past the scoring shore; outside the shore: {sk.get('water_outside_shore', 0)} pts "
     f"(= {sk.get('water_outside_shore', 0) * step * step:.0f} m2) up to z {sk.get('water_max_z', 0):.2f} m, {sk.get('water_max_dist_from_shore', 0):.2f} m out")

# ================================================================ (3) objects / foam / ocean / shelf / surf / lava
odd = [n for n in new_names if n.startswith(GP)]
gate("NO_NEW_COLLISION_PREFIX", not odd, f"{len(new_names)} objects new vs frozen; with a ground prefix: {odd}")
foam_users = {k: v for k, v in lm.items() if k.startswith("MAT_FOAM") and v > 0}
foam_on = [n for n, d in look.items() if "mats" in d and any(m.startswith("MAT_FOAM") for m in d["mats"])]
foam_obj = [n for n in look if n.startswith("WATER_FOAM")]
gate("NO_MAT_FOAM", not foam_users and not foam_on and not foam_obj,
     f"MAT_FOAM users {foam_users}, meshes using it {foam_on}, WATER_FOAM* objects {foam_obj} (frozen had "
     f"{[n for n in frozen if n.startswith('WATER_FOAM')]})")
if H != "10":
    oc = [n for n in look if n.startswith("WATER_OCEAN")]
    d = look.get("WATER_OCEAN")
    if d:
        z = d["W"][:, 2]
        gate("OCEAN_ONE_FLAT_PLANE_LK_WATER", len(oc) == 1 and float(np.abs(z).max()) < 1e-6 and d["mats"] == ["LK_WATER"]
             and float(d["pn"][:, 2].min()) > 0.999,
             f"objects {oc}; {len(d['W'])} verts {len(d['polys'])} faces, z range {z.min():.4f}..{z.max():.4f}, all normals up "
             f"{float(d['pn'][:, 2].min()) > 0.999}, materials {d['mats']} (frozen: {len(frozen['WATER_OCEAN']['W'])} verts)")
    sh = look.get("WATER_SHELF")
    sf = [n for n in look if n.startswith("WATER_SURF")]
    gate("SHELF_AND_SURF_EXIST", sh is not None and sh["mats"] == ["LK_WATER_SHALLOW"] and len(sf) > 0,
         f"WATER_SHELF {'present' if sh else 'MISSING'} mats {sh['mats'] if sh else None} z {sh['W'][:, 2].min() if sh else 0:.3f}; "
         f"WATER_SURF objects {len(sf)}; WATER_SHALLOW still present: {'WATER_SHALLOW' in look}")
    # connected components + areas
    comps = []
    for n in sf:
        d = look[n]
        par = list(range(len(d["W"])))

        def f_(a):
            while par[a] != a:
                par[a] = par[par[a]]
                a = par[a]
            return a
        for vs in d["polys"]:
            r0 = f_(vs[0])
            for v in vs[1:]:
                r = f_(v)
                if r != r0:
                    par[r] = r0
        roots = np.array([f_(v) for v in range(len(d["W"]))])
        proot = np.array([roots[vs[0]] for vs in d["polys"]])
        for r in np.unique(proot):
            pm = proot == r
            vv = np.unique(np.concatenate([np.array(d["polys"][i]) for i in np.nonzero(pm)[0]]))
            ext = d["W"][vv, :2].max(0) - d["W"][vv, :2].min(0)
            comps.append((float(d["area"][pm].sum()), float(np.hypot(*ext)), n))
    ar = np.array([c[0] for c in comps])
    ln = np.array([c[1] for c in comps])
    shore_len = sum(float(np.hypot(*(np.roll(np.array(L_), -1, 0) - np.array(L_)).T).sum()) for L_ in D.loops)
    gate("SURF_MANY_RAGGED_PIECES", len(comps) >= 12 and ar.max() < 0.35 * ar.sum(),
         f"{len(comps)} connected pieces in {len(sf)} objects; area m2 min {ar.min():.1f} / median {np.median(ar):.1f} / max {ar.max():.1f} / "
         f"total {ar.sum():.0f} (largest = {100 * ar.max() / ar.sum():.0f}% of total); extent m median {np.median(ln):.1f} max {ln.max():.1f}; "
         f"design shore length {shore_len:.0f} m")
    # overlap of transparent surf objects (same z): cells covered by >= 2 different WATER_SURF objects
    cover = np.zeros(len(X), np.int32)
    for n in sf:
        hk = heights(bvh(look, [n]), X, Y)
        cover += (~np.isnan(hk)).astype(np.int32)
    ov = int((cover >= 2).sum())
    gate("SURF_NO_OVERLAP", ov == 0, f"{ov} grid cells ({ov * step * step:.0f} m2) covered by >= 2 WATER_SURF objects at the same z 0.12 "
         f"(alpha-blended: double foam / sort popping); covered total {int((cover >= 1).sum()) * step * step:.0f} m2")
else:
    d = look.get("WATER_LAVA")
    tri = sum(len(vs) - 2 for vs in d["polys"])
    gate("LAVA_SUBDIVIDED_LK", tri >= 3000 and d["mats"] == ["LK_LAVA"] and float(np.abs(d["W"][:, 2]).max()) < 1e-6,
         f"WATER_LAVA {len(d['W'])} verts, {tri} tris, mats {d['mats']}, z max |{float(np.abs(d['W'][:, 2]).max()):.4f}|; "
         f"frozen WATER_LAVA {len(frozen['WATER_LAVA']['polys'])} polys mats {frozen['WATER_LAVA']['mats']}")
    lights = sorted(n for n in look if n.startswith("LAVA_LIGHT"))
    info(f"lava lights {[(n, tuple(round(c, 1) for c in look[n]['loc'])) for n in lights]}")

# ================================================================ (4) UVs
LK_TILE = {"LK_FAIRWAY": 10, "LK_GREEN": 6, "LK_ROUGH": 12, "LK_SCRUB": 12, "LK_SAND": 6, "LK_CLIFF": 12, "LK_CLIFF_DARK": 12,
           "LK_ROCK": 4, "LK_ROCK_WET": 4, "LK_PATH": 5, "LK_MASONRY": 4, "LK_BASALT": 8, "LK_LAVA": 24, "LK_WATER": 8,
           "LK_WATER_SHALLOW": 8, "LK_SURF": 8}
nouv, nan, degen, ratio = [], [], {}, {}
for n, d in look.items():
    if "mats" not in d:
        continue
    lkm = [m for m in d["mats"] if m.startswith("LK_")]
    if not lkm:
        continue
    if d["uv"] is None:
        nouv.append(n); continue
    if d["nuv"] != 1:
        nouv.append(f"{n}:{d['nuv']} layers")
    if not np.isfinite(d["uv"]).all():
        nan.append(n); continue
    uv, W = d["uv"], d["W"]
    for p in range(len(d["polys"])):
        m = d["mats"][min(d["mi"][p], len(d["mats"]) - 1)] if d["mats"] else ""
        if m not in LK_TILE:
            continue
        a, k = int(d["ls"][p]), int(d["lt"][p])
        vs = d["lv"][a:a + k]
        if d["area"][p] < 1e-3:
            continue
        U = uv[a:a + k]
        ua = 0.5 * abs(((U[:, 0] * np.roll(U[:, 1], -1)) - (np.roll(U[:, 0], -1) * U[:, 1])).sum())
        if ua < 1e-9:
            degen[m] = degen.get(m, 0) + 1
        r = math.sqrt(ua * LK_TILE[m] ** 2 / d["area"][p])
        if n.startswith("TERRAIN") and abs(d["pn"][p, 2]) < 0.5:
            m = m + "(wall)"
        ratio.setdefault(m, []).append(r)
rs = {m: (round(float(np.percentile(v, 1)), 2), round(float(np.median(v)), 2), round(float(np.percentile(v, 99)), 2), len(v))
      for m, v in sorted(ratio.items())}
gate("LK_FACES_HAVE_TILE_UVS", not nouv and not nan and not degen and all(0.4 <= v[1] <= 2.5 for v in rs.values()),
     f"meshes with LK_ but no / extra UV layer {nouv[:6]}; NaN {nan}; zero-area UV faces {degen}; sqrt(UV area * tile^2 / world area) "
     f"p1/median/p99/n per material {rs}")

# ---- fairway centreline sample (hand-computed lateral / arc on the RAW design centreline)
rng = np.random.default_rng(int(H) + 7)
fw = look["FAIRWAY"]
tris = []
for p, vs in enumerate(fw["polys"]):
    if fw["pn"][p, 2] > 0.9:
        a = int(fw["ls"][p])
        for k in range(1, len(vs) - 1):
            tris.append((p, (a, a + k, a + k + 1)))
areas = np.array([0.5 * np.linalg.norm(np.cross(fw["W"][fw["lv"][t[1]]] - fw["W"][fw["lv"][t[0]]], fw["W"][fw["lv"][t[2]]] - fw["W"][fw["lv"][t[0]]]))
                  for _, t in tris])
pick = rng.choice(len(tris), size=20, replace=False, p=areas / areas.sum())
C = np.array([P.m(x, d_) for x, d_ in D.hole.center])
d0 = (C[1] - C[0]) / np.linalg.norm(C[1] - C[0])
d1 = (C[-1] - C[-2]) / np.linalg.norm(C[-1] - C[-2])
C = np.vstack([C[0] - d0 * 120, C, C[-1] + d1 * 120])
segL = np.linalg.norm(np.diff(C, axis=0), axis=1)
cum = np.concatenate([[0], np.cumsum(segL)]) - 120.0          # arc 0 at the tee


def raw_uv(px, py):
    best = (1e9, 0, 0, None)
    for i in range(len(C) - 1):
        A, B = C[i], C[i + 1]
        ab = B - A
        t = np.clip(((px - A[0]) * ab[0] + (py - A[1]) * ab[1]) / (ab @ ab), 0, 1)
        q = A + ab * t
        dd = math.hypot(px - q[0], py - q[1])
        if dd < best[0]:
            tx, ty = ab / np.linalg.norm(ab)
            lat = (px - q[0]) * ty - (py - q[1]) * tx
            best = (dd, lat, cum[i] + t * segL[i], (tx, ty))
    return best


rows = []
for k in pick:
    p, (i0, i1, i2) = tris[k]
    r1, r2 = rng.random(), rng.random()
    if r1 + r2 > 1:
        r1, r2 = 1 - r1, 1 - r2
    w = np.array([1 - r1 - r2, r1, r2])
    Pw = w @ fw["W"][fw["lv"][[i0, i1, i2]]]
    Uw = w @ fw["uv"][[i0, i1, i2]]
    dd, lat, arc, tg = raw_uv(Pw[0], Pw[1])
    # gradient of v in world (per triangle) -> direction of the stripes
    Q = fw["W"][fw["lv"][[i0, i1, i2]]][:, :2]
    Uv = fw["uv"][[i0, i1, i2]] * 10.0
    M = np.array([Q[1] - Q[0], Q[2] - Q[0]])
    g = np.linalg.solve(M, np.array([Uv[1] - Uv[0], Uv[2] - Uv[0]]))   # rows: d(u,v)/dx, d(u,v)/dy -> columns
    gv = g[:, 1]
    ang = math.degrees(math.acos(min(1, abs(gv @ np.array(tg)) / max(np.linalg.norm(gv), 1e-9))))
    rows.append(dict(x=round(Pw[0], 2), y=round(Pw[1], 2), u_m=round(Uw[0] * 10, 2), lat_raw=round(lat, 2),
                     v_m=round(Uw[1] * 10, 2), arc_raw=round(arc, 2), stripe_angle_deg=round(ang, 1)))
# same check against a Chaikin(5)-smoothed copy of the raw line (what the lib says it uses), my own implementation


def chaikin_open(Pts, it):
    Q = np.array(Pts, float)
    for _ in range(it):
        R_ = [Q[0]]
        for i in range(len(Q) - 1):
            R_ += [0.75 * Q[i] + 0.25 * Q[i + 1], 0.25 * Q[i] + 0.75 * Q[i + 1]]
        R_.append(Q[-1])
        Q = np.array(R_)
    return Q


C0 = np.array([P.m(x, d_) for x, d_ in D.hole.center])
CS = chaikin_open(C0, 5)
e0 = (CS[1] - CS[0]) / np.linalg.norm(CS[1] - CS[0])
e1 = (CS[-1] - CS[-2]) / np.linalg.norm(CS[-1] - CS[-2])
CS = np.vstack([CS[0] - e0 * 120, CS, CS[-1] + e1 * 120])
sm_err = []
for r in rows:
    best = (1e9, 0)
    for i in range(len(CS) - 1):
        A, B = CS[i], CS[i + 1]
        ab = B - A
        t = np.clip(((r["x"] - A[0]) * ab[0] + (r["y"] - A[1]) * ab[1]) / (ab @ ab), 0, 1)
        q = A + ab * t
        dd = math.hypot(r["x"] - q[0], r["y"] - q[1])
        if dd < best[0]:
            tx, ty = ab / np.linalg.norm(ab)
            best = (dd, (r["x"] - q[0]) * ty - (r["y"] - q[1]) * tx)
    r["lat_smooth"] = round(best[1], 2)
    sm_err.append(r["u_m"] - best[1])
sm_err = np.array(sm_err)
info(f"fairway u*10 vs lateral from my own Chaikin(5)-smoothed centreline: max |err| {np.abs(sm_err).max():.3f} m (u is quantised by the "
     f"x/y rounding of the sample to 1 cm)")
lat_err = np.array([r["u_m"] - r["lat_raw"] for r in rows])
arc_off = np.array([r["v_m"] - r["arc_raw"] for r in rows])
arc_off_c = arc_off - np.median(arc_off)
ang = np.array([r["stripe_angle_deg"] for r in rows])
json.dump(rows, open(os.path.join(OUT, "fairway_uv_samples.json"), "w"), indent=1)
gate("FAIRWAY_UV_FOLLOWS_CENTRELINE", np.abs(lat_err).max() < 3.0 and np.abs(arc_off_c).max() < 5.0 and ang.max() < 15,
     f"20 random FAIRWAY points: u*10 - lateral(raw centreline) median {np.median(lat_err):+.2f} m, max |err| {np.abs(lat_err).max():.2f} m; "
     f"v*10 - arc(raw) median offset {np.median(arc_off):+.2f} m (integer-tile shift), spread max |dev| {np.abs(arc_off_c).max():.2f} m; "
     f"stripe direction (grad v) vs raw centreline tangent: median {np.median(ang):.1f} deg, max {ang.max():.1f} deg "
     f"(raw = unsmoothed design polyline; differences come from the lib's Chaikin smoothing)")

# ---- wall UV continuity on TERRAIN and on ROCK_SKIN (per-edge jump between neighbouring faces)


def uv_jumps(d, face_mask=None, tol=1e-4):
    edge = {}
    for p, vs in enumerate(d["polys"]):
        if face_mask is not None and not face_mask[p]:
            continue
        a = int(d["ls"][p])
        k = len(vs)
        for j in range(k):
            v0, v1 = vs[j], vs[(j + 1) % k]
            key = (min(v0, v1), max(v0, v1))
            edge.setdefault(key, []).append({v0: d["uv"][a + j], v1: d["uv"][a + (j + 1) % k]})
    jumps = []
    for key, L_ in edge.items():
        if len(L_) != 2:
            continue
        jm = max(float(np.abs(L_[0][v] - L_[1][v]).max()) for v in key)
        jumps.append(jm)
    jumps = np.array(jumps) if jumps else np.zeros(1)
    return int((jumps > tol).sum()), float(jumps.max()), len(jumps)


ter = [n for n in look if n.startswith("TERRAIN")][0]
td = look[ter]
wall = np.abs(td["pn"][:, 2]) < 0.5
nj, mj, ne = uv_jumps(td, wall)
info(f"TERRAIN wall UV: {ne} interior wall edges, {nj} with a UV jump, max jump {mj:.3f} UV")
skins = sorted(n for n in look if n.startswith("ROCK_SKIN"))
sj = [uv_jumps(look[n]) for n in skins]
# cross-piece: same world position, different piece -> UV equal modulo integer?
pos_uv = {}
for n in skins:
    d = look[n]
    for li, v in enumerate(d["lv"].tolist()):
        key = tuple(np.round(d["W"][v], 4))
        pos_uv.setdefault(key, set()).add((n, round(float(d["uv"][li, 0]), 4), round(float(d["uv"][li, 1]), 4)))
cross = []
for key, s in pos_uv.items():
    ns = {t[0] for t in s}
    if len({(t[1]) for t in s}) > 1:
        us = np.array([t[1] for t in s])
        frac = (us - us.min()) % 1.0
        frac = np.minimum(frac, 1 - frac)
        cross.append(float(frac.max()))
cross = np.array(cross) if cross else np.zeros(1)
gate("WALL_UV_CONTINUOUS", nj <= max(4, 0.01 * ne) and sum(s[0] for s in sj) <= 0.02 * max(1, sum(s[2] for s in sj)),
     f"TERRAIN wall: {nj}/{ne} shared edges with a UV jump (max {mj:.2f}); ROCK_SKIN per-piece jumps "
     f"{sum(s[0] for s in sj)}/{sum(s[2] for s in sj)} edges (max {max(s[1] for s in sj):.2f}); across piece boundaries "
     f"{len(cross)} shared positions, u mismatch modulo 1 tile: max {cross.max():.3f}, >0.01 at {int((cross > 0.01).sum())}")

# ================================================================ (5) skin: up faces, roughness, wall hidden
up_info = []
for n in skins:
    d = look[n]
    cen = np.array([d["W"][vs].mean(0) for vs in d["polys"]])
    up = d["pn"][:, 2] > 0.3
    up_info.append((n, int(up.sum()), float(cen[up, 2].max()) if up.any() else 0.0))
info(f"skin up-facing faces (nz > 0.3) per piece: {up_info}")
if H != "10":
    NR = 13
    stats = []
    for n in skins:
        d = look[n]
        if len(d["W"]) % NR:
            stats.append((n, "rows?"))
            continue
        Wr = d["W"].reshape(-1, NR, 3)
        sdv = P.signed_dist_m(D, Wr[:, :, 0].ravel(), Wr[:, :, 1].ravel()).reshape(Wr.shape[:2])
        stats.append(sdv[:, 1:])
    S = np.concatenate([s for s in stats if not isinstance(s, tuple)], 0)
    along_std = float(np.mean(S.std(0)))
    dS = np.abs(np.diff(S, axis=0))
    jag = float((dS > 0.2).mean())
    vert_std = float(np.mean(S.std(1)))
    # tortuosity of a mid row vs its own 9-col moving average
    rough = []
    for n in skins:
        Wr = look[n]["W"].reshape(-1, NR, 3)[:, 6, :2]
        L_raw = np.linalg.norm(np.diff(Wr, axis=0), axis=1).sum()
        k = 9
        sm = np.stack([np.convolve(Wr[:, c], np.ones(k) / k, mode="valid") for c in range(2)], 1)
        L_sm = np.linalg.norm(np.diff(sm, axis=0), axis=1).sum() * len(Wr) / max(len(sm), 1)
        rough.append(L_raw / max(L_sm, 1e-6))
    gate("SKIN_IS_JAGGED", along_std > 0.15 and jag > 0.03 and vert_std > 0.1,
         f"strata skin, signed distance of every vertex to the scoring shore (rows below the cap): mean along-shore std {along_std:.2f} m, "
         f"adjacent-column steps > 0.2 m: {100 * jag:.1f}% of column pairs, mean per-column vertical std {vert_std:.2f} m, offset range "
         f"{S.min():.2f}..{S.max():.2f} m; mid-row plan tortuosity vs 9-col smooth {np.mean(rough):.3f} (smooth extrusion = 0 / 0 % / 0 / 1.000)")
else:
    tops, cnt = [], 0
    for n in skins:
        d = look[n]
        for vs in d["polys"]:
            if len(vs) == 6:
                cnt += 1
                tops.append(float(d["W"][vs, 2].mean()))
    tops = np.array(tops)
    gate("SKIN_IS_JAGGED", cnt > 200 and tops.std() > 0.3,
         f"basalt: {cnt} hex cap faces (column segments), top z mean {tops.mean():.2f} std {tops.std():.2f} m, range {tops.min():.2f}..{tops.max():.2f}")

# wall hidden from several viewpoints
tb = bvh(look, [ter])
sb = bvh(look, skins)
allb = bvh(look, [ter] + skins)
twall_tree = bvh(look, [ter])
loops = [np.array(L_) for L_ in D.loops]
samples = []
for L_ in loops:
    seg = np.roll(L_, -1, 0) - L_
    sl = np.linalg.norm(seg, axis=1)
    cs = np.concatenate([[0], np.cumsum(sl)])
    for s in np.arange(0.5, cs[-1], 2.0):
        i = int(np.searchsorted(cs, s, side="right") - 1)
        t = (s - cs[i]) / max(sl[i], 1e-9)
        p = L_[i] + seg[i] * t
        tg = seg[i] / max(sl[i], 1e-9)
        nrm = np.array([tg[1], -tg[0]])
        if P.signed_dist_m(D, np.array([p[0] + 2 * nrm[0]]), np.array([p[1] + 2 * nrm[1]]))[0] < 0:
            nrm = -nrm
        samples.append((p, nrm, tg))
rng2 = np.random.default_rng(5)
exp = {"aerial": [0, 0], "low": [0, 0], "oblique": [0, 0]}
band = {}
for p, nrm, tg in samples:
    # skip shore points whose outside is land within 30 m (narrow channels): the viewpoint would be inside rock
    for z in (0.3, 1.5, 3.0, 4.5, PZ - 0.6):
        o = Vector((p[0] + nrm[0] * 6, p[1] + nrm[1] * 6, z))
        h = tb.ray_cast(o, Vector((-nrm[0], -nrm[1], 0)), 30)
        if h[0] is None or abs(h[1].z) > 0.5:
            continue
        Wp = h[0]
        for vn, off in (("aerial", (40, 0, 15)), ("low", (40, 0, 2.0)), ("oblique", (25, 20, 8))):
            V = Vector((Wp.x + nrm[0] * off[0] + tg[0] * off[1], Wp.y + nrm[1] * off[0] + tg[1] * off[1], Wp.z + off[2]))
            if V.z < 0.3:
                continue
            if P.signed_dist_m(D, np.array([V.x]), np.array([V.y]))[0] < 1.0:
                continue
            dv = (Wp - V)
            dist = dv.length
            hh = allb.ray_cast(V, dv.normalized(), dist + 0.05)
            if hh[0] is None:
                continue
            ht = tb.ray_cast(V, dv.normalized(), dist + 0.05)
            exp[vn][1] += 1
            is_terrain_first = ht[0] is not None and abs(ht[3] - hh[3]) < 1e-5 and (ht[0] - Wp).length < 0.3
            if is_terrain_first:
                exp[vn][0] += 1
                zb = "z<1" if Wp.z < 1 else ("1-3" if Wp.z < 3 else ("3-5" if Wp.z < 5 else ">=5"))
                band[zb] = band.get(zb, 0) + 1
tot_exp = sum(v[0] for v in exp.values())
tot = sum(v[1] for v in exp.values())
gate("WALL_HIDDEN_FROM_VIEWPOINTS", tot_exp <= 0.03 * tot,
     f"{len(samples)} shore samples x 5 wall heights x 3 viewpoints (aerial 40 m out +15 m, low 40 m out +2 m, oblique 25 m out 20 m "
     f"along +8 m): smooth TERRAIN wall seen first {tot_exp}/{tot} rays ({100 * tot_exp / max(tot, 1):.1f}%); per view "
     f"{ {k: f'{v[0]}/{v[1]}' for k, v in exp.items()} }; exposed by wall height {band}")

# ================================================================ (6) FBX re-import
raw = open(FBX, "rb").read()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX)
mats = sorted(m.name for m in bpy.data.materials)
dotted = [m for m in mats if "." in m]
per = {}
noUV = []
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    nm = [m.name for m in o.data.materials if m]
    k = o.name.split("_")[0] if not o.name.startswith(GP) else o.name
    per.setdefault(k, set()).update(nm)
    if any(m.startswith("LK_") for m in nm) and len(o.data.uv_layers) != 1:
        noUV.append((o.name, len(o.data.uv_layers)))
imgs = [i.name for i in bpy.data.images]
blend_mats = {n: sorted(set(d["mats"])) for n, d in look.items() if "mats" in d}
fbx_mats = {o.name: sorted({m.name for m in o.data.materials if m}) for o in bpy.data.objects if o.type == "MESH"}
diff = [n for n in blend_mats if n in fbx_mats and blend_mats[n] != fbx_mats[n]]
missing = [n for n in blend_mats if n not in fbx_mats]
gate("FBX_REIMPORT_MATERIALS_UVS", not dotted and not noUV and not imgs and not diff and not missing,
     f"{len(mats)} materials {mats}; '.001'-style names {dotted}; LK_ meshes without exactly 1 UV layer {noUV[:5]}; images {imgs}; "
     f"raw bytes 'Texture::' {raw.count(b'Texture::')}, '.png' {raw.count(b'.png')}; per-object material sets equal to the blend: "
     f"{len(blend_mats) - len(diff) - len(missing)}/{len(blend_mats)} (diff {diff[:4]}, missing {missing[:4]})")
info("FBX materials by prefix: " + "; ".join(f"{k}: {sorted(v)}" for k, v in sorted(per.items())))
json.dump(dict(hole=H, gates=RES), open(os.path.join(OUT, f"review_gates_hole{H}.json"), "w"), indent=1)
print(f"[review] hole {H}: {sum(g['ok'] for g in RES)}/{len(RES)} PASS; FAIL {[g['name'] for g in RES if not g['ok']]}")
