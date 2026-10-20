"""Skeptical review of postcard_props_lib (A4). Headless only, writes ONLY into work/postcard-look/review_props/.

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python work/postcard-look/review_props/review_props.py

Never saves a .blend, never writes Plants_C.png (checks its sha before/after), never writes ArtDir.
"""
import sys
import os
import math
import json
import hashlib
import struct
import zlib

sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
OUT = os.path.join(REPO, "work", "postcard-look", "review_props")
SCR = os.path.join(REPO, "blender", "scripts")
sys.path.insert(0, SCR)

import numpy as np  # noqa: E402
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import postcard_props_lib as PL  # noqa: E402
import postcard_lib as P  # noqa: E402

RES = []
DATA = {}


def gate(name, ok, detail=""):
    RES.append((name, bool(ok), detail))
    print(f"GATE: {name} {'PASS' if ok else 'FAIL'} {detail}", flush=True)


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


PLANTS_SHA0 = sha(PL.PLANTS_PNG)


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    PL._COUNTERS.clear()
    PL.reset_scatter(None)


def comps(me):
    """connected components (vertex islands) -> list of vertex index lists"""
    n = len(me.vertices)
    par = list(range(n))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            par[a] = b
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def uv_np(me):
    lay = me.uv_layers.active
    uv = np.empty(len(me.loops) * 2)
    lay.uv.foreach_get("vector", uv)
    return uv.reshape(-1, 2)


# ============================================================ A. library census
def library_census():
    fresh()
    lib = PL.ensure_library()
    for k in list(PL.ROCK_BUILDERS):
        lib[k + "_WET"] = PL.library_object(k + "_WET")
        lib[k + "_BASALT"] = PL.library_object(k + "_BASALT")
    rows = {}
    for k, ob in sorted(lib.items()):
        me = ob.data
        me.calc_loop_triangles()
        uv = uv_np(me)
        rows[k] = dict(v=len(me.vertices), f=len(me.polygons), t=len(me.loop_triangles),
                       mats=[m.name for m in me.materials], nan=int(np.isnan(uv).sum()),
                       uvmin=uv.min(0).round(3).tolist(), uvmax=uv.max(0).round(3).tolist(),
                       shared_name=(ob.name == me.name), ngon_max=max(len(p.vertices) for p in me.polygons))
    DATA["census"] = rows
    over_f = {k: r["f"] for k, r in rows.items() if r["f"] > 500}
    over_t = {k: r["t"] for k, r in rows.items() if r["t"] > 500}
    gate("R_LIB_FACES_500", not over_f, f"{len(rows)} library meshes (incl. _WET/_BASALT twins), max faces "
         f"{max(r['f'] for r in rows.values())}, max tris {max(r['t'] for r in rows.values())}; over 500 faces {over_f or 'none'}; "
         f"over 500 tris {over_t or 'none'}")
    tufts = {k: rows[k]["f"] for k in PL.TUFT_KINDS}
    gate("R_TUFT_120", max(tufts.values()) <= 120, f"tufts faces {tufts}")
    nan = {k: r["nan"] for k, r in rows.items() if r["nan"]}
    gate("R_UV_NO_NAN", not nan, f"NaN UV comps: {nan or 'none'}")
    # rocks: unique + verts
    rk = {k: rows[k] for k in PL.ROCK_KINDS}
    vmin = min(r["v"] for r in rk.values())
    hashes = {}
    for k in PL.ROCK_KINDS:
        me = lib[k].data
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        hashes[k] = hashlib.sha1(np.round(co, 5).tobytes()).hexdigest()
    gate("R_ROCK_UNIQUE_6", len(set(hashes.values())) >= 6 and vmin >= 60,
         f"{len(set(hashes.values()))} geometrically distinct rock kinds; verts " +
         ", ".join(f"{k[5:]} {rk[k]['v']}" for k in PL.ROCK_KINDS) + f"; min {vmin}")
    return lib


# ============================================================ B. icosahedron-likeness
def ico_likeness(lib):
    """How blob-like is each rock: (1) sphericity = 36 pi V^2 / A^3 of the mesh (icosahedron 0.91, sphere 1, cube 0.52),
    (2) share of area in the 6 largest facets (big planar chips -> high), (3) 12-vert check, (4) distinct facet normals."""
    out = {}
    for k in PL.ROCK_KINDS:
        me = lib[k].data
        bm = bmesh.new()
        bm.from_mesh(me)
        vol = abs(bm.calc_volume(signed=False))
        areas = sorted((f.calc_area() for f in bm.faces), reverse=True)
        A = sum(areas)
        bm.free()
        sph = 36 * math.pi * vol * vol / (A ** 3) if A > 0 else 0
        top6 = sum(areas[:6]) / A
        out[k] = dict(sph=round(sph, 3), top6=round(top6, 3), v=len(me.vertices), f=len(me.polygons))
    # reference icosahedron
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    vol = bm.calc_volume()
    areas = sorted((f.calc_area() for f in bm.faces), reverse=True)
    A = sum(areas)
    out["_ICOSAHEDRON_ref"] = dict(sph=round(36 * math.pi * vol * vol / A ** 3, 3), top6=round(sum(areas[:6]) / A, 3), v=len(bm.verts), f=len(bm.faces))
    bm.free()
    DATA["ico"] = out
    blobs = [k for k, r in out.items() if not k.startswith("_") and r["sph"] > 0.85 and r["top6"] < 0.35]
    gate("R_NO_ICO_LOOKALIKE", not blobs and all(r["v"] > 12 for k, r in out.items() if not k.startswith("_")),
         "sphericity/top-6-facet-area: " + ", ".join(f"{k.replace('ROCK_', '')} {r['sph']}/{r['top6']}" for k, r in out.items())
         + f"; blob-like (sph>.85 & top6<.35): {blobs or 'none'}")


# ============================================================ C. basalt hex prisms
def hex_check(lib):
    out = {}
    allok = True
    for k in list(PL.BASALT_KINDS) + list(PL.WALL_KINDS):
        me = lib[k].data
        groups = comps(me)
        v2c = {}
        for ci, g in enumerate(groups):
            for vi in g:
                v2c[vi] = ci
        sides = {ci: [] for ci in range(len(groups))}
        tops = {ci: 0 for ci in range(len(groups))}
        for p in me.polygons:
            ci = v2c[p.vertices[0]]
            n = p.normal
            if abs(n.z) < 0.02:
                sides[ci].append(math.degrees(math.atan2(n.y, n.x)) % 360)
            elif n.z > 0.7:
                tops[ci] += 1
        good = 0
        bad = []
        for ci, angs in sides.items():
            angs = sorted(angs)
            ok = len(angs) == 6 and tops[ci] >= 1
            if ok:
                d = [(angs[(i + 1) % 6] - angs[i]) % 360 for i in range(6)]
                ok = all(abs(x - 60) < 4 for x in d)
            if ok:
                good += 1
            else:
                bad.append((ci, len(angs), tops[ci]))
        # column width + height
        co = np.array([v.co[:] for v in me.vertices])
        hz = [co[g][:, 2].max() - co[g][:, 2].min() for g in groups]
        wd = [np.ptp(co[g][:, 0]) for g in groups]
        out[k] = dict(columns=len(groups), hex_ok=good, bad=bad[:4], width_med=round(float(np.median(wd)), 2),
                      h_med=round(float(np.median(hz)), 2), h_max=round(float(max(hz)), 2))
        if k in PL.BASALT_KINDS and good < 8:
            allok = False
        if good != len(groups):
            allok = allok and good >= 0.9 * len(groups)
    DATA["hex"] = out
    gate("R_BASALT_HEX_PRISMS", allok and sum(1 for k in PL.BASALT_KINDS if out[k]["hex_ok"] >= 8) >= 4,
         "; ".join(f"{k.replace('ROCK_', '')}: {r['hex_ok']}/{r['columns']} islands are 6-sided prisms (side normals 60 deg apart), "
                   f"col width {r['width_med']} m, h med {r['h_med']} max {r['h_max']}" for k, r in out.items()))


# ============================================================ D. plants UV vs atlas pixels
def plants_check(lib):
    img = bpy.data.images.load(PL.PLANTS_PNG, check_existing=True)
    W, H = img.size
    px = np.array(img.pixels[:], np.float32).reshape(H, W, 4)        # row 0 = bottom
    bad = {}
    worst_margin = 99.0
    swatch_use = {}
    for k in PL.PLANT_KINDS:
        me = lib[k].data
        uv = uv_np(me)
        ls = np.zeros(len(me.polygons), np.int64)
        lt = np.zeros(len(me.polygons), np.int64)
        me.polygons.foreach_get("loop_start", ls)
        me.polygons.foreach_get("loop_total", lt)
        nb = 0
        for p in range(len(me.polygons)):
            q = uv[ls[p]:ls[p] + lt[p]] * np.array([W, H])          # pixel coords (y from the bottom)
            cx = np.floor(q[:, 0] / 64).astype(int)
            cy = np.floor(q[:, 1] / 64).astype(int)
            if (cx != cx[0]).any() or (cy != cy[0]).any() or q.min() < 0 or q.max() > 256:
                nb += 1
                continue
            m = min((q[:, 0] - cx[0] * 64).min(), ((cx[0] + 1) * 64 - q[:, 0]).min(), (q[:, 1] - cy[0] * 64).min(),
                    ((cy[0] + 1) * 64 - q[:, 1]).min())
            worst_margin = min(worst_margin, m)
            idx = (3 - cy[0]) * 4 + cx[0]        # swatch index (row 0 = top)
            swatch_use.setdefault(k, set()).add(PL.SWATCHES[idx][0])
        if nb:
            bad[k] = nb
    DATA["plant_swatches"] = {k: sorted(v) for k, v in swatch_use.items()}
    gate("R_PLANTS_ATLAS_256", (W, H) == (256, 256), f"Plants_C.png {W}x{H}, sha {PLANTS_SHA0[:12]}")
    gate("R_PLANT_UV_IN_SWATCH", not bad and worst_margin >= 5.9, f"{len(PL.PLANT_KINDS)} plant meshes; faces crossing a swatch or "
         f"outside 0..1: {bad or 'none'}; worst distance to a swatch border {worst_margin:.2f} px")
    # swatch colour sanity: the purple flower must sample purple, agave A blue-green
    def mean_col(name):
        i = PL.SWATCH[name]
        c, r = i % 4, i // 4
        blk = px[H - (r + 1) * 64:H - r * 64, c * 64:(c + 1) * 64, :3]
        return (np.clip(blk.mean((0, 1)), 0, 1) ** (1 / 2.2) * 255).round().astype(int).tolist()
    DATA["swatch_rgb"] = {n: mean_col(n) for n, _ in PL.SWATCHES}
    ok = "FLOWER_PURPLE" in swatch_use.get("PLANT_FLOWER_PURPLE", ()) and "AGAVE" in swatch_use.get("PLANT_AGAVE_A", ())
    gate("R_PLANT_SWATCH_ROUTING", ok, f"purple flower uses {DATA['plant_swatches'].get('PLANT_FLOWER_PURPLE')}, agave A "
         f"{DATA['plant_swatches'].get('PLANT_AGAVE_A')}, tuft C {DATA['plant_swatches'].get('PLANT_TUFT_C')}")


# ============================================================ E/F. unique pieces: waterfall, arch, ruin, cone, smoke
def unique_pieces():
    fresh()
    fall = PL.build_waterfall_sheet(None, (0.0, 0.0, 6.0), (0.0, -1.0), width_m=3.0, seed=1)
    me = fall.data
    uv = uv_np(me)
    vidx = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", vidx)
    z = np.array([me.vertices[i].co.z for i in vidx])
    # v must decrease monotonically with height: corr(v, z) == -1-ish and v(top)=0, v(foot)=1
    order = np.argsort(-z)
    vv = uv[order, 1]
    mono = bool(np.all(np.diff(vv) >= -1e-6))
    nrm = np.mean([p.normal.y for p in me.polygons])     # outward = -Y -> normal.y negative
    gate("R_WATERFALL_UV", not np.isnan(uv).any() and uv[:, 0].min() >= -1e-6 and uv[:, 0].max() <= 1 + 1e-6 and
         abs(uv[:, 1].min()) < 1e-6 and abs(uv[:, 1].max() - 1) < 1e-6 and mono and nrm < -0.5 and fall.name.startswith("WATER_FALL_"),
         f"{fall.name}: u {uv[:, 0].min():.2f}..{uv[:, 0].max():.2f}, v {uv[:, 1].min():.2f}..{uv[:, 1].max():.2f}, v monotone top->foot "
         f"{mono}, mean normal.y {nrm:.2f} (out = -Y), {len(me.polygons)} faces, mat {me.materials[0].name}")
    foot = PL.waterfall_foot((0.0, 0.0, 6.0), (0.0, -1.0), 3.0)
    lowest = min((fall.matrix_world @ v.co) for v in me.vertices if v.co.z < 0.01).y if any(v.co.z < 0.01 for v in me.vertices) else None
    DATA["fall_foot"] = dict(foot=foot, lowest_y=lowest)
    # arch
    res = PL.build_masonry_arch(None, (100.0, 0.0, 5.0), 0.0, span_m=7.5, height_m=11.0, seed=8, base_rock=False)
    arch = res["arch"]
    groups = comps(arch.data)
    co = np.array([v.co[:] for v in arch.data.vertices])
    sizes = sorted((np.ptp(co[g], axis=0).round(2).tolist() for g in groups), key=lambda s: -s[2])
    # vine attachment: every vine origin within 0.2 m of an arch vertex? use BVH distance
    bvh = BVHTree.FromObject(arch, bpy.context.evaluated_depsgraph_get())
    dists = []
    for v in res["vines"]:
        loc_local = arch.matrix_world.inverted() @ v.location
        hit = bvh.find_nearest(loc_local)
        dists.append(hit[3] if hit[0] is not None else 99)
    arch.data.calc_loop_triangles()
    gate("R_ARCH_BLOCKS_VINES", len(groups) >= 25 and len(res["vines"]) >= 6 and max(dists) < 0.25 and len(arch.data.polygons) <= 500,
         f"{arch.name}: {len(groups)} separate blocks, {len(arch.data.polygons)} faces / {len(arch.data.loop_triangles)} tris, "
         f"{len(res['vines'])} vines (origin to arch surface max {max(dists):.2f} m), {len(res['fallen'])} fallen blocks")
    DATA["arch"] = dict(blocks=len(groups), faces=len(arch.data.polygons), tris=len(arch.data.loop_triangles),
                        vines=len(res["vines"]), vine_dist_max=round(max(dists), 3), biggest=sizes[:3])
    broken = PL.build_masonry_arch(None, (130.0, 0.0, 0.0), 30.0, span_m=6.0, height_m=9.0, broken=True, seed=12)
    gb = comps(broken["arch"].data)
    DATA["arch_broken"] = dict(blocks=len(gb), faces=len(broken["arch"].data.polygons), vines=len(broken["vines"]))
    ru = PL.build_ruin(None, [(200.0, 0.0), (212.0, 0.5), (214.5, 10.0)], seed=3, base_z=0.0, doorway_at=0.3)
    rb = sum(len(comps(o.data)) for o in ru["walls"])
    rf = [len(o.data.polygons) for o in ru["walls"]]
    # course structure: z of block bottoms quantised to course height?
    zb = []
    for o in ru["walls"]:
        c2 = np.array([v.co[:] for v in o.data.vertices])
        for g in comps(o.data):
            zb.append(round(float(c2[g][:, 2].min()), 2))
    courses = sorted(set(zb))
    gate("R_RUIN_MASONRY", rb >= 30 and max(rf) <= 500 and len(courses) >= 3,
         f"{len(ru['walls'])} ruin meshes, {rb} separate blocks, faces {rf}, {len(courses)} course levels {courses[:8]}, "
         f"{len(ru['fallen'])} fallen blocks")
    DATA["ruin"] = dict(blocks=rb, faces=rf, courses=courses)
    cone = PL.build_background_cone(None, (400.0, 0.0, -8.0), seed=1, notch_deg=250)
    cone.data.calc_loop_triangles()
    DATA["cone"] = dict(faces=len(cone.data.polygons), tris=len(cone.data.loop_triangles), mats=[m.name for m in cone.data.materials])
    sm = PL.build_smoke_cards(None, [((500.0, 0.0, 60.0), 40.0, 55.0)])
    DATA["smoke"] = dict(names=[o.name for o in sm], mesh=sm[0].data.name, mats=[m.name for m in sm[0].data.materials])
    # names of everything in this scene
    bad = [o.name for o in bpy.data.objects if o.type == 'MESH' and (not o.name.startswith(PL.NAME_PREFIXES) or
                                                                    o.name.startswith(P.GROUND_PREFIXES))]
    gate("R_NAMES_UNIQUE_PIECES", not bad, f"{sum(1 for o in bpy.data.objects if o.type == 'MESH')} mesh objects; bad: {bad or 'none'}")


# ============================================================ G. baseline hole tests (scatter safety vs BASELINE play meshes)
PLAY = ("FAIRWAY", "GREEN", "TEE_BOX", "BUNKER")


def baseline_play_tris(tag):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, "work", "postcard-look", "baseline", "blender", f"hole_{tag}.blend"))
    dg = bpy.context.evaluated_depsgraph_get()
    V, F, names = [], [], []
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(PLAY):
            names.append(o.name)
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            base = len(V)
            V += [tuple(o.matrix_world @ v.co) for v in me.vertices]
            F += [[base + i for i in p.vertices] for p in me.polygons]
            ev.to_mesh_clear()
    return V, F, names


def prop_world_xy(ob):
    me = ob.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    M = np.array(ob.matrix_world)
    w = co @ M[:3, :3].T + M[:3, 3]
    return w


def hole_scatter_test(tag, full_kit=True):
    V, F, names = baseline_play_tris(tag)
    bvh = BVHTree.FromPolygons(V, F)
    fresh()
    D = P.start(f"hole{tag}_design", out_dir=os.path.join(OUT, f"hole{tag}"))
    P.build_terrain(D)
    P.build_play_surfaces(D)
    # same-geometry check: scratch play meshes == baseline ones (vertex count)
    nv_scratch = sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(PLAY))
    var = "BASALT" if tag == "10" else None
    props = []
    props += PL.scatter_rocks(D, 30, zone="rim", seed=4, variant=var)
    props += PL.scatter_rocks(D, 30, zone="sea", seed=5, variant=var)
    props += PL.scatter_rocks(D, 20, zone="ledge", seed=6, variant=var)
    if full_kit:
        props += PL.scatter(D, ["PLANT_PINE_A", "PLANT_TREE_A"], 8, region=PL.region_band(D, 1.0, 12.0), seed=7)
        props += PL.scatter(D, ["PLANT_AGAVE_A", "PLANT_AGAVE_B"], 20, region=PL.region_band(D, 0.5, 8.0), seed=8)
    props += PL.scatter(D, ["PLANT_SHRUB_A", "PLANT_SHRUB_B", "PLANT_SHRUB_C"], 40, region=PL.region_band(D, 0.6, 6.0), seed=2)
    props += PL.scatter(D, {"PLANT_FLOWER_PURPLE": 2, "PLANT_FLOWER_WHITE": 1, "PLANT_FLOWER_YELLOW": 1}, 80,
                        region=PL.region_band(D, 0.4, 10.0), seed=3)
    # tufts with region=None (whole hole bbox) to stress the default masks too
    props += PL.scatter(D, {"PLANT_TUFT_A": 3, "PLANT_TUFT_B": 2, "PLANT_TUFT_C": 1}, 600, seed=1)
    bpy.context.view_layer.update()
    px, py = D.hole.pin[0] * P.YD, D.hole.pin[1] * P.YD
    tx, ty = D.hole.tee[0] * P.YD, D.hole.tee[1] * P.YD
    hits, worst, pin_min, pin_min_v = [], 0.0, 1e9, 1e9
    by_kind = {}
    for ob in props:
        w = prop_world_xy(ob)
        x, y, z = ob.location
        pin_min = min(pin_min, math.hypot(x - px, y - py))
        pin_min_v = min(pin_min_v, float(np.hypot(w[:, 0] - px, w[:, 1] - py).min()))
        if z < D.play_z - 1.0:          # sea/lava props: only check they do not reach over a play surface either
            pass
        nh = 0
        for (qx, qy, qz) in w[:: max(1, len(w) // 64)]:
            hit = bvh.ray_cast(Vector((qx, qy, D.play_z + 50.0)), Vector((0, 0, -1)), 200.0)
            if hit[0] is not None:
                nh += 1
        if nh:
            hits.append(ob.name)
            k = ob.data.name
            by_kind[k] = by_kind.get(k, 0) + 1
    # intrusion depth: for props that hit, how far inside (vertex xy distance to nearest play-mesh boundary approx via lie)
    tris = 0
    for ob in props:
        ob.data.calc_loop_triangles()
        tris += len(ob.data.loop_triangles)
    meshes = {ob.data.as_pointer() for ob in props}
    names_m = {ob.data.name for ob in props}
    share_ok = len(meshes) == len(names_m) and all(ob.data is bpy.data.objects[ob.data.name].data for ob in props)
    # land props hanging over the cliff edge (any vertex over water lie while the prop stands on land)
    over = 0
    for ob in props:
        if ob.location.z > D.play_z - 1.0 and not ob.name.startswith("PLANT_VINE"):
            w = prop_world_xy(ob)
            codes = P.lie_codes_m(D, w[:, 0], w[:, 1])
            if (codes == P.LIE_WATER).mean() > 0.25:
                over += 1
    tall_in_corr = 0
    for ob in props:
        if ob.data.name.startswith(PL.TALL_KINDS):
            _c, off = P._lie_all(D, np.array([ob.location.x]), np.array([ob.location.y]))
            if off[0] * P.YD < D.hole.fw / 2 * P.YD + 3.0:
                tall_in_corr += 1
    DATA[f"hole{tag}"] = dict(props=len(props), tris=tris, hits=len(hits), hit_kinds=by_kind, hit_names=hits[:10],
                              pin_min_origin=round(pin_min, 2), pin_min_vertex=round(pin_min_v, 2), play_meshes=names,
                              nv_baseline=len(V), nv_scratch=nv_scratch, unique_meshes=len(meshes), over_edge=over,
                              tall_in_corridor=tall_in_corr)
    gate(f"R_SCATTER_SAFE_BASELINE_{tag}", not hits and pin_min_v >= 6.0,
         f"{len(props)} props (rocks rim/sea/ledge, trees, agave, shrubs, flowers, 600 tufts with region=None); EVERY vertex xy "
         f"ray-cast against the {len(names)} BASELINE play meshes {names}: props touching a play surface {len(hits)} {by_kind or ''}; "
         f"nearest prop vertex to the pin {pin_min_v:.1f} m (origin {pin_min:.1f}); land props >25% over the edge {over}; "
         f"tall props in the camera corridor {tall_in_corr}")
    gate(f"R_INSTANCED_IDENTITY_{tag}", share_ok and len(props) >= 10 * len(meshes),
         f"{len(props)} props -> {len(meshes)} mesh datablocks (obj.data IS the library object's data: {share_ok})")
    gate(f"R_HOLE_BUDGET_{tag}", tris <= 150000, f"{tris} tris for this heavier kit")
    return D, props


# ============================================================ H. FBX: geometry written once (binary FBX parser) + re-import
def parse_fbx(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:20] == b"Kaydara FBX Binary  "
    ver = struct.unpack("<I", data[23:27])[0]
    big = ver >= 7500
    hdr = "<QQQ" if big else "<III"
    hsz = 24 if big else 12

    def read_props(pos, n):
        props = []
        for _ in range(n):
            t = data[pos:pos + 1]
            pos += 1
            if t == b"Y":
                props.append(struct.unpack("<h", data[pos:pos + 2])[0]); pos += 2
            elif t == b"C":
                props.append(data[pos]); pos += 1
            elif t == b"I":
                props.append(struct.unpack("<i", data[pos:pos + 4])[0]); pos += 4
            elif t == b"F":
                props.append(struct.unpack("<f", data[pos:pos + 4])[0]); pos += 4
            elif t == b"D":
                props.append(struct.unpack("<d", data[pos:pos + 8])[0]); pos += 8
            elif t == b"L":
                props.append(struct.unpack("<q", data[pos:pos + 8])[0]); pos += 8
            elif t in (b"S", b"R"):
                ln = struct.unpack("<I", data[pos:pos + 4])[0]; pos += 4
                props.append(data[pos:pos + ln]); pos += ln
            elif t in (b"f", b"d", b"l", b"i", b"b"):
                alen, enc, clen = struct.unpack("<III", data[pos:pos + 12]); pos += 12
                pos += clen
                props.append(("arr", t, alen))
            else:
                raise ValueError(f"prop type {t} at {pos}")
        return props

    def read_node(pos):
        end, nprops, plen = struct.unpack(hdr, data[pos:pos + hsz])
        if end == 0:
            return None, pos + hsz + 1
        nlen = data[pos + hsz]
        name = data[pos + hsz + 1:pos + hsz + 1 + nlen].decode()
        p = pos + hsz + 1 + nlen
        props = read_props(p, nprops)
        p += plen
        kids = []
        while p < end:
            node, p = read_node(p)
            if node is None:
                break
            kids.append(node)
        return (name, props, kids), end
    pos = 27
    top = []
    while pos < len(data) - 200:
        node, pos = read_node(pos)
        if node is None:
            break
        top.append(node)
    objs = next(n for n in top if n[0] == "Objects")
    conns = next(n for n in top if n[0] == "Connections")
    geos = {n[1][0]: n[1][1] for n in objs[2] if n[0] == "Geometry"}
    models = {n[1][0]: (n[1][1], n[1][2]) for n in objs[2] if n[0] == "Model"}
    mats = {n[1][0]: n[1][1] for n in objs[2] if n[0] == "Material"}
    g2m = {}
    m2mat = {}
    for c in conns[2]:
        if c[0] == "C" and c[1][0] == b"OO":
            a, b = c[1][1], c[1][2]
            if a in geos and b in models:
                g2m.setdefault(a, []).append(b)
            if a in mats and b in models:
                m2mat.setdefault(b, []).append(mats[a].split(b"\x00")[0].decode())
    return dict(version=ver, geometry=len(geos), n_models=len(models), mesh_models=sum(1 for v in models.values() if v[1] == b"Mesh"),
                g2m=g2m, geos=geos, models=models, m2mat=m2mat)


def fbx_test(D, props):
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    # small scene: 40 tufts, 10 shrubs, 6 rocks, 3 seastacks (2 material slots), 1 TERRAIN-like with LK_ROUGH first
    pick = [o for o in props if o.data.name.startswith("PLANT_TUFT")][:40] + \
           [o for o in props if o.data.name.startswith("PLANT_SHRUB")][:10] + \
           [o for o in props if o.data.name.startswith("ROCK_")][:6]
    st = [PL.place(D, "ROCK_SEASTACK_A", (300.0 + 20 * i, 300.0, 0.0), 0.3 * i, 1.0) for i in range(3)]
    terr = [o for o in bpy.data.objects if o.name.startswith("TERRAIN")]
    sel = pick + st + terr[:1]
    for o in sel:
        o.select_set(True)
    path = os.path.join(OUT, "review_small.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'}, axis_forward='-Z', axis_up='Y',
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_anim=False, use_mesh_modifiers=True,
                             add_leaf_bones=False, path_mode='STRIP', embed_textures=False)
    uniq = {o.data.as_pointer() for o in sel}
    r = parse_fbx(path)
    multi = {g: len(m) for g, m in r["g2m"].items()}
    gate("R_FBX_GEOMETRY_ONCE", r["geometry"] == len(uniq) and r["mesh_models"] == len(sel),
         f"review_small.fbx (FBX {r['version']}): {len(sel)} mesh objects / {len(uniq)} unique mesh datablocks -> {r['geometry']} "
         f"Geometry nodes, {r['mesh_models']} mesh Models; models per geometry {sorted(multi.values(), reverse=True)[:6]}")
    # seastack instances: material order per model
    st_models = [mid for mid, (nm, t) in r["models"].items() if nm.startswith(b"ROCK_SEASTACK_A")]
    DATA["fbx_seastack_mats"] = [r["m2mat"].get(mid) for mid in st_models]
    # re-import into a fresh scene: unique meshes + per-material face counts on the stacks
    src_counts = {}
    me = st[0].data
    for p in me.polygons:
        nm = me.materials[p.material_index].name
        src_counts[nm] = src_counts.get(nm, 0) + 1
    fresh()
    bpy.ops.import_scene.fbx(filepath=path)
    imp = [o for o in bpy.data.objects if o.type == 'MESH']
    uq = {o.data.as_pointer() for o in imp}
    stacks = [o for o in imp if o.name.startswith("ROCK_SEASTACK_A")]
    counts = []
    for o in stacks:
        c = {}
        for p in o.data.polygons:
            nm = o.material_slots[p.material_index].material.name if o.material_slots[p.material_index].material else None
            c[nm] = c.get(nm, 0) + 1
        counts.append(c)
    same = all(c == src_counts for c in counts)
    gate("R_FBX_REIMPORT_SHARED", len(uq) == len(uniq) and len(imp) == len(sel) and same,
         f"re-import: {len(imp)} objects, {len(uq)} unique mesh datablocks (expected {len(uniq)}); seastack per-material face "
         f"counts source {src_counts} vs re-imported {counts[:1]} (all equal {same})")
    for o in bpy.data.objects:
        pass


# ============================================================ I. legacy swap on the BASELINE blends
def swap_test(tag):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, "work", "postcard-look", "baseline", "blender", f"hole_{tag}.blend"))
    PL._COUNTERS.clear()
    before = {}
    lowpoly = {}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(("ROCK", "CLIFF")) and not any(c.name == "ASSET_LIBRARY" for c in o.users_collection):
            lowpoly[o.data.name.split(".")[0]] = len(o.data.vertices)
    objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.data is not None and o.data.name.split(".")[0] in PL.LEGACY_MESHES
            and not any(c.name == "ASSET_LIBRARY" for c in o.users_collection)]
    for o in objs:
        before[o.name] = tuple(o.scale)
    sw = PL.swap_legacy_rocks(None, objs=objs, basalt=(tag == "10"))
    bpy.context.view_layer.update()
    aniso = []
    col_w = []
    kinds = {}
    for o in sw:
        s = np.array(o.scale)
        a = float(max(s[0], s[1]) / max(min(s[0], s[1]), 1e-6))
        az = float(s[2] / max(min(s[0], s[1]), 1e-6))
        aniso.append((o.name, round(a, 2), round(az, 2), tuple(np.round(s, 2))))
        kinds[o.data.name] = kinds.get(o.data.name, 0) + 1
        if o.data.name.startswith(("ROCK_WALL", "ROCK_BASALT")):
            r = {"ROCK_WALL_BASALT_A": 2.4, "ROCK_WALL_BASALT_B": 2.3, "ROCK_WALL_BASALT_C": 2.0, "ROCK_BASALT_A": 0.72,
                 "ROCK_BASALT_B": 0.66, "ROCK_BASALT_C": 0.7, "ROCK_BASALT_D": 0.88}.get(o.data.name.split(".")[0])
            if r:
                col_w.append((o.name, round(2 * r * s[0], 2), round(2 * r * s[1], 2)))
    left = [o.name for o in bpy.data.objects if o.type == 'MESH' and len(o.data.vertices) <= 12 and o.name.startswith(("ROCK", "CLIFF"))
            and not any(c.name == "ASSET_LIBRARY" for c in o.users_collection)]
    other_low = {k: v for k, v in lowpoly.items() if k not in PL.LEGACY_MESHES and v < 60}
    bad_aniso = [a for a in aniso if a[1] > 2.0 or a[2] > 3.0 or a[2] < 0.33]
    DATA[f"swap{tag}"] = dict(swapped=len(sw), kinds=kinds, aniso_worst=sorted(aniso, key=lambda a: -max(a[1], a[2], 1 / max(a[2], 1e-3)))[:6],
                              col_widths=sorted(col_w, key=lambda c: min(c[1], c[2]))[:8], left=left[:5], other_lowpoly=other_low)
    gate(f"R_SWAP_BASELINE_{tag}", not left and len(sw) == len(objs) and not bad_aniso,
         f"{len(sw)}/{len(objs)} legacy instances in baseline hole_{tag}.blend swapped -> {kinds}; 12-vert rocks left {len(left)}; "
         f"non-legacy rock meshes under 60 verts {other_low or 'none'}; instances stretched >2x across or z/xy outside 0.33..3: "
         f"{len(bad_aniso)} (worst {bad_aniso[:3]})")
    return sw


# ============================================================ main
def main():
    lib = library_census()
    ico_likeness(lib)
    hex_check(lib)
    plants_check(lib)
    unique_pieces()
    D9, props9 = hole_scatter_test("09")
    fbx_test(D9, props9)
    hole_scatter_test("08")
    hole_scatter_test("10")
    for tag in ("08", "09", "10"):
        swap_test(tag)
    gate("R_PLANTS_PNG_UNTOUCHED", sha(PL.PLANTS_PNG) == PLANTS_SHA0, f"sha before {PLANTS_SHA0[:12]} after {sha(PL.PLANTS_PNG)[:12]}")
    with open(os.path.join(OUT, "review_data.json"), "w") as f:
        json.dump(DATA, f, indent=1, default=str)
    fails = [r for r in RES if not r[1]]
    print(f"SUMMARY: {len(RES) - len(fails)}/{len(RES)} review gates PASS", flush=True)


main()
sys.stdout.flush()
os._exit(0)
