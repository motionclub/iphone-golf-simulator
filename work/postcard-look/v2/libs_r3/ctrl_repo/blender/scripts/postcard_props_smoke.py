"""postcard_props_smoke: gates + contact sheets for postcard_props_lib (POSTCARD_LOOK role A4, v2 2026-10-04). Headless only:

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/postcard_props_smoke.py \
        -- [--no-render] [--no-holes] [--no-baseline] [--holes 08,09,10] [--scratch DIR] [--sheet PNG] [--baseline DIR]

1. Plants_C.png -> Unity/Assets/Resources/Course/Look/ (deterministic: two generations byte-identical, 256 x 256).
2. Library gates on every library mesh: face budgets, rock shape (>= 60 welded vertices, >= 100 faces, not an icosahedron /
   icosphere / UV sphere blob: ROCK_SHAPE_NOT_BLOB, NO_12_VERTEX_ROCK), tapering sea stacks (SEASTACK_TAPERED), hex-column wall
   towers (WALL_COLUMNS_HEX), UVs (box projection at the contract tiles, nominal-scale baked tiles / inside the plant swatches /
   non-degenerate), materials, names, no animation, determinism. NEGATIVE CONTROLS prove the thresholds fail the old shapes (the
   old two-block sea stack, an icosahedron, a subdivided / split / noised icosphere, a UV sphere, a 4x-stretched wall instance).
3. Contact sheets (EEVEE, the real Look/ textures) -> work/postcard-look/v2/props/ (props_sheet_v2.png, seastack_sheet.png).
4. Hole tests in a SCRATCH dir only (never writes blender/hole_NN.blend or the FBXs): P.start(design, out_dir=scratch) + terrain +
   play surfaces + a stone-path strip + the whole dressing (scatter with and WITHOUT a region, sea stacks, outcrop + arch + vines,
   smoke cards, legacy rocks + swap): triangle budget, safety (rays against FAIRWAY/GREEN/TEE_BOX/BUNKER), land + ground rule
   (SCATTER_DEFAULT_ON_LAND, PLANT_ON_WATER_ZERO), instancing, no instance stretched past 2x, FBX writes each geometry once.
5. The three BASELINE hole blends (work/postcard-look/baseline/blender): swap_legacy_rocks, then SWAP_NO_STRETCH_2X_<hole> and the
   instance-scale statistics (v2/props/swap_stats.json).
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
V2 = os.path.join(REPO, "work", "postcard-look", "v2", "props")
SCRATCH = os.path.abspath(ARGS[ARGS.index("--scratch") + 1]) if "--scratch" in ARGS else os.path.join(V2, "scratch")
SHEET = os.path.abspath(ARGS[ARGS.index("--sheet") + 1]) if "--sheet" in ARGS else os.path.join(V2, "props_sheet_v2.png")
BASELINE = os.path.abspath(ARGS[ARGS.index("--baseline") + 1]) if "--baseline" in ARGS else \
    os.path.join(REPO, "work", "postcard-look", "baseline", "blender")
DO_BASELINE = "--no-baseline" not in ARGS
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


# ----------------------------------------------------------------------------- negative controls (the OLD shapes)
def _mesh_obj(name, V, F, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    me.update()
    for pl in me.polygons:
        pl.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _bm_to_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def neg_icosphere(name, subdiv, radius=1.0, noise=0.0, stretch=(1, 1, 1), uv_sphere=False, split=False, seed=3):
    import bmesh
    bm = bmesh.new()
    if uv_sphere:
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=radius)
    else:
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    rnd = np.random.RandomState(seed)
    for v in bm.verts:
        f = 1.0 + noise * rnd.uniform(-1, 1)
        v.co = Vector((v.co.x * stretch[0] * f, v.co.y * stretch[1] * f, v.co.z * stretch[2] * f))
    if split:                                            # every face gets its own vertices (flat-shaded export / split mesh)
        V, F = [], []
        for fc in bm.faces:
            F.append([len(V) + i for i in range(len(fc.verts))])
            V.extend(v.co.copy() for v in fc.verts)
        bm.free()
        return _mesh_obj(name, V, F)
    return _bm_to_obj(name, bm)


def old_seastack_chunks(rng, height, base_r, top_r, lean=(0.0, 0.0), buttress=4, crown=2):
    """VERBATIM the v1 sea stack (two flat-topped cores + shoulder + buttresses + crown), kept as the negative control."""
    import random as _r  # noqa: F401
    zb = -3.0
    a = rng.uniform(0, math.tau)
    sh = (math.cos(a) * base_r * 0.32 + lean[0] * height, math.sin(a) * base_r * 0.32 + lean[1] * height)
    z_mid = height * rng.uniform(0.5, 0.62)
    p1, c1 = PL._core_pts(rng, zb, z_mid, base_r, base_r * 0.8, (0, 0), (sh[0] * 0.3, sh[1] * 0.3))
    p2, c2 = PL._core_pts(rng, z_mid - height * 0.12, height, base_r * 0.68, top_r, (sh[0] * 0.6, sh[1] * 0.6), sh, levels=5)
    chunks = [dict(pts=p1, merge=0.05), dict(pts=p2, merge=0.05)]
    for j in range(buttress):
        cx, cy, z, r = c1[min(len(c1) - 1, rng.randrange(0, 3))]
        aa = a + math.pi + rng.uniform(-1.6, 1.6) if j < 2 else rng.uniform(0, math.tau)
        br = r * rng.uniform(0.45, 0.6)
        hz = (height - zb) * rng.uniform(0.1, 0.18)
        c = (cx + math.cos(aa) * r * 0.8, cy + math.sin(aa) * r * 0.72, max(zb + hz * 0.7, rng.uniform(-0.5, height * 0.22)))
        chunks.append(dict(c=c, r=(br, br * 0.9, hz), n=16, block=0.6, chips=3, chip_range=(0.7, 0.88), flat_top=0.8,
                           flat_bottom=0.8, top_tilt=0.1))
    cx, cy, z, r = c2[-1]
    for j in range(crown):
        aa = rng.uniform(0, math.tau)
        cr = r * rng.uniform(0.5, 0.65)
        chunks.append(dict(c=(cx + math.cos(aa) * r * 0.4, cy + math.sin(aa) * r * 0.4, z + rng.uniform(-0.6, 0.5)),
                           r=(cr, cr * 0.9, cr * 0.8), n=14, block=0.6, chips=2, flat_top=0.75, flat_bottom=0.8, top_tilt=0.15))
    return chunks


def old_seastack(kind, which):
    import random
    if which == "A":
        rng = random.Random(909)
        ch = old_seastack_chunks(rng, 17.0, 3.8, 1.7, lean=(0.015, -0.01))
        ob = PL._chunks_mesh(kind, rng, ch, mats=("LK_ROCK", "LK_ROUGH"), mat_fn=PL._grass_cap(17.0 * 0.45), ground=None)
    else:
        rng = random.Random(1001)
        ch = old_seastack_chunks(rng, 12.0, 3.4, 2.1, lean=(0.05, 0.02), buttress=3)
        ob = PL._chunks_mesh(kind, rng, ch, mats=("LK_ROCK", "LK_ROUGH"), mat_fn=PL._grass_cap(12.0 * 0.4), ground=None)
    return ob.data


def column_stats(me):
    """Hex-prism evidence of a basalt mesh: column tops (n-gons with 6-7 corners facing up), distinct top levels, chipped tops,
    vertical side share."""
    co, tris, _tp = PL._np_mesh(me)
    nrm, area, lt = PL._poly_arrays(me)
    tops, chipped, zs = 0, 0, []
    for p in me.polygons:
        if p.normal.z > 0.85 and len(p.vertices) in (6, 7):
            tops += 1
            if len(p.vertices) == 7:
                chipped += 1
            zs.append(sum(me.vertices[i].co.z for i in p.vertices) / len(p.vertices))
    vert = float((area[np.abs(nrm[:, 2]) < 0.2]).sum() / max(area.sum(), 1e-9))
    levels = len(set(round(z / 0.25) for z in zs))
    zs = np.array(zs) if zs else np.zeros(1)
    return dict(tops=tops, chipped=chipped, levels=levels, z_spread=float(zs.max() - zs.min()), vertical=vert,
                faces=len(me.polygons), dims=tuple(float(v) for v in (co.max(0) - co.min(0))))


def uv_density_ratio(me, tile):
    """Per face sqrt(UV area / (world area at the nominal scale / tile^2)): 1.0 = the tile is exactly its contract size when the
    instance has the nominal scale lk_uv_scale (axis-facing faces; oblique faces measure lower by cos)."""
    s = float(me.get("lk_uv_scale", 1.0))
    uv = uv_array(me)
    ls = np.zeros(len(me.polygons), np.int64)
    lt = np.zeros(len(me.polygons), np.int64)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    out = []
    for p in me.polygons:
        a = uv[ls[p.index]]
        ua = 0.0
        for j in range(1, lt[p.index] - 1):
            b, c = uv[ls[p.index] + j], uv[ls[p.index] + j + 1]
            ua += abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2
        wa = p.area * s * s / (tile * tile)
        if wa > 1e-9:
            out.append(math.sqrt(ua / wa))
    return np.array(out)


def shape_gates(lib, rep, hashes):
    """NO_12_VERTEX_ROCK, ROCK_SHAPE_NOT_BLOB, SEASTACK_TAPERED, WALL_COLUMNS_HEX (+ the v1 gate ids ROCK_VERTS_60, NO_ICOSAHEDRON,
    BASALT_COLUMNS) with negative controls that must FAIL."""
    th = PL.SHAPE_TH
    rock_meshes = {k: ob.data for k, ob in lib.items() if k.startswith("ROCK_")}
    for k in ("ROCK_BOULDER_A_WET", "ROCK_SLAB_A_WET", "ROCK_BLOCK_A_BASALT", "ROCK_BOULDER_B_BASALT", "ROCK_SEASTACK_B_WET",
              "ROCK_CRAG_A_WET", "ROCK_SPIRE_A_WET"):
        rock_meshes[k] = PL.library_object(k).data
    shape = {k: PL.rock_shape_report(me) for k, me in rock_meshes.items()}
    vmin = min(r["verts"] for r in shape.values())
    fmin = min(r["faces"] for r in shape.values())
    low = {k: (r["verts"], r["faces"]) for k, r in shape.items() if r["verts"] < th["min_verts"] or r["faces"] < th["min_faces"]}
    gate("ROCK_VERTS_60", not low, f"{len(shape)} library rock meshes (twins included): min welded verts {vmin} (>= 60), min faces "
         f"{fmin} (>= 100); short: {low or 'none'}")
    ico = [k for k, r in shape.items() if r["verts"] <= 12 or (r["verts"], r["faces"]) == (12, 20)]
    gate("NO_ICOSAHEDRON", not ico, f"rock meshes with <= 12 verts / 12-vertex 20-face icosahedra: {ico or 'none'}")

    # --- legacy scene check: assert_no_legacy_rocks fails on icosahedra and passes after the swap
    fresh()
    for i in range(3):
        neg_icosphere(f"ROCK_MEDIUM.{i:03d}", 1, 3.0).data.name = "ROCK_MEDIUM"
    before = PL.assert_no_legacy_rocks(None, raise_on_fail=False)
    raised = False
    try:
        PL.assert_no_legacy_rocks(None)
    except RuntimeError:
        raised = True
    PL.swap_legacy_rocks(None)
    after = PL.assert_no_legacy_rocks(None, raise_on_fail=False)
    gate("NO_12_VERTEX_ROCK", not low and not before["ok"] and raised and after["ok"],
         f"library: min {vmin} welded verts / {fmin} faces over {len(shape)} rock meshes; scene with 3 icosahedra: assert_no_legacy_rocks "
         f"FAILS before the swap (offenders {len(before['offenders'])}, raises {raised}) and PASSES after (rocks {after['rocks']}, "
         f"min verts {after['min_verts']}); the hole tests re-assert after every swap")
    fresh()
    PL.write_plants_atlas()
    for k in PL.ensure_library():
        pass

    # --- blob test: library rocks pass, the old shapes FAIL
    lib_bad = {k: r["why"] for k, r in shape.items() if not r["ok"]}
    fresh()
    negs = {
        "icosahedron (12 verts)": neg_icosphere("NEG_ICO", 1, 2.0),
        "icosphere sub 2 (42 verts)": neg_icosphere("NEG_ICO2", 2, 2.0),
        "icosphere sub 3 (162 verts)": neg_icosphere("NEG_ICO3", 3, 2.0),
        "split icosahedron (60 verts, flat)": neg_icosphere("NEG_ICOS", 1, 2.0, split=True),
        "stretched icosphere sub 3": neg_icosphere("NEG_ICOX", 3, 1.0, stretch=(2.2, 1.4, 0.8)),
        "noised icosphere sub 3 (8 %)": neg_icosphere("NEG_ICON", 3, 2.0, noise=0.08),
        "UV sphere 16 x 10": neg_icosphere("NEG_UVS", 0, 2.0, uv_sphere=True),
    }
    neg_rep = {n: PL.rock_shape_report(ob.data) for n, ob in negs.items()}
    neg_pass = [n for n, r in neg_rep.items() if r["ok"]]
    gate("ROCK_SHAPE_NOT_BLOB", not lib_bad and not neg_pass,
         f"{len(shape)} library rocks all pass (welded verts >= {th['min_verts']}, faces >= {th['min_faces']}, >= {th['min_facets']} facet "
         f"orientations in {th['facet_deg']:.0f} degree cones, normalised radius CV >= {th['blob_radius_cv']}); radius CV "
         f"{min(r['radius_cv'] for r in shape.values()):.2f}..{max(r['radius_cv'] for r in shape.values()):.2f}, facets "
         f"{min(r['facets'] for r in shape.values())}..{max(r['facets'] for r in shape.values())}; failing: {lib_bad or 'none'}. "
         f"NEGATIVE CONTROLS all FAIL: " + "; ".join(f"{n}: {'FAIL' if not r['ok'] else 'PASS (!)'} [{r['verts']}v/{r['faces']}f, rcv {r['radius_cv']:.3f}]"
                                                    for n, r in neg_rep.items()))
    for ob in negs.values():
        bpy.data.objects.remove(ob, do_unlink=True)

    # --- sea stacks (needs the library again: negatives built in a scene that also holds the old stacks)
    fresh()
    PL.write_plants_atlas()
    sea = {k: PL.library_object(k).data for k in PL.SEASTACK_KINDS}
    sr = {k: PL.seastack_report(me) for k, me in sea.items()}
    old = {"old A (two flat-topped cores)": old_seastack("NEG_OLD_SEASTACK_A", "A"), "old B (leaning two cores)": old_seastack("NEG_OLD_SEASTACK_B", "B")}
    old_rep = {n: PL.seastack_report(me) for n, me in old.items()}
    hts = [sr[k]["height"] for k in PL.SEASTACK_KINDS]
    fcs = [sr[k]["faces"] for k in PL.SEASTACK_KINDS]
    nat = [PL.SPIRE_SPECS[k]["height"] + 3.0 for k in PL.SEASTACK_KINDS]
    ok = all(r["ok"] for r in sr.values()) and all(150 <= f <= PL.SPIRE_MAX_FACES + 10 for f in fcs) and all(abs(h - n) < 0.6 for h, n in zip(hts, nat)) \
        and len(set(round(h) for h in hts)) == len(hts) and all(not r["ok"] for r in old_rep.values())
    gate("SEASTACK_TAPERED", ok,
         "; ".join(f"{k.replace('ROCK_SEASTACK_', '')}: {r['faces']} faces, {r['slices']} slices (distinct {r['distinct']}), taper w90/w10 "
                   f"{r['taper']:.2f} (<= {th['taper_max']}), max band widening {r['band_rise']:.2f} (<= {th['band_rise_max']}), flat cap "
                   f"{r['cap_share']:.0%} of base (<= {th['cap_max']:.0%}), {r['facets']} facet orientations (>= {th['spire_facets']}), bbox fill "
                   f"from 0/45/90/135 deg {'/'.join(f'{f:.2f}' for f in r['fills'])} (<= {th['fill_max']})" for k, r in sr.items() for _ in [0])
         + f". Mesh heights {'/'.join(f'{h:.0f}' for h in hts)} m for A/B/C/D/E (13/18/24/16/21 m above the water + 3 m under it). NEGATIVE: " +
         "; ".join(f"{n}: {'FAIL' if not r['ok'] else 'PASS (!)'} ({'; '.join(r['why'][:3])})" for n, r in old_rep.items()))
    # the spire kinds of the swap must pass too
    sp = PL.seastack_report(PL.library_object("ROCK_SPIRE_A").data)
    gate("SPIRE_TAPERED", sp["ok"], f"ROCK_SPIRE_A taper {sp['taper']:.2f}, fills {'/'.join(f'{f:.2f}' for f in sp['fills'])}, "
         f"{sp['faces']} faces, facets {sp['facets']}")
    for me in old.values():
        pass

    # --- columns: clusters, wall segments, the three tower sizes
    fresh()
    PL.write_plants_atlas()
    cl_kinds = list(PL.BASALT_KINDS) + list(PL.WALL_KINDS) + list(PL.TOWER_KINDS)
    cs = {k: column_stats(PL.library_object(k).data) for k in cl_kinds}
    det = [(k, v["vertical"], v["tops"]) for k, v in cs.items()]
    cl_ok = sum(1 for k in PL.BASALT_KINDS if cs[k]["tops"] >= 8 and cs[k]["vertical"] >= 0.6) >= 4
    wl_ok = all(cs[k]["tops"] >= 12 and cs[k]["vertical"] >= 0.6 for k in PL.WALL_KINDS)
    gate("BASALT_COLUMNS", cl_ok and wl_ok and len(set(hashes[k] for k in PL.BASALT_KINDS)) >= 4,
         "; ".join(f"{k} {v['tops']} column tops, {v['vertical']:.0%} vertical area" for k, v in cs.items()))
    tw = {k: cs[k] for k in PL.TOWER_KINDS}
    dens = {k: uv_density_ratio(PL.library_object(k).data, 8.0) for k in PL.TOWER_KINDS}
    sizes = [max(tw[k]["dims"][0], tw[k]["dims"][1]) for k in PL.TOWER_KINDS]
    heights = [tw[k]["dims"][2] for k in PL.TOWER_KINDS]
    ok_tw = all(v["tops"] >= 12 and v["levels"] >= 4 and v["chipped"] >= 0.15 * v["tops"] and v["vertical"] >= 0.6 and v["faces"] <= 500
                for v in tw.values())
    ok_sz = sizes[0] < sizes[1] < sizes[2] and heights[0] < heights[1] < heights[2] and sizes[1] >= 1.25 * sizes[0] and sizes[2] >= 1.25 * sizes[1]
    ok_uv = all(0.8 <= float(np.median(d)) <= 1.2 and float(np.mean((d > 0.5) & (d < 1.5))) >= 0.97 for d in dens.values())
    gate("WALL_COLUMNS_HEX", ok_tw and ok_sz and ok_uv,
         "; ".join(f"{k.replace('ROCK_WALL_BASALT_', 'TOWER_')}: {v['tops']} hex column tops (>= 12), {v['levels']} distinct top levels over "
                   f"{v['z_spread']:.1f} m, {v['chipped']} chipped tops, {v['vertical']:.0%} vertical area, {v['faces']} faces, "
                   f"{v['dims'][0]:.0f} x {v['dims'][1]:.0f} x {v['dims'][2]:.0f} m (incl. 6 m buried), UV: tile 8 m at the nominal scale "
                   f"{PL.library_object(k).data.get('lk_uv_scale', 1.0)} -> density ratio median {float(np.median(dens[k])):.2f}"
                   for k, v in tw.items()))


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
    shape_gates(lib, rep, hashes)
    fresh()
    PL.write_plants_atlas()
    lib = PL.ensure_library()
    for k in ("ROCK_BOULDER_A_WET", "ROCK_SLAB_A_WET", "ROCK_BLOCK_A_BASALT", "ROCK_BOULDER_B_BASALT"):
        lib[k] = PL.library_object(k)
    hashes = {k: mesh_hash(PL.library_object(k).data) for k in PL.BUILDERS}
    # UVs
    bad_tile, bad_deg, bad_sw = [], [], []
    for k, ob in sorted(lib.items()):
        me = ob.data
        uv = uv_array(me)
        mats = [m.name for m in me.materials]
        vidx, co, pol, nrm, mi = PL._loop_arrays(me)
        if k.startswith(("ROCK_", "DRESS_BLOCK")):
            tiles = [(PL.TILE[m] or 4.0) for m in mats]
            exp = PL.box_uv_expected(me, tiles)
            plant_loop = np.isin(mi[pol], [i for i, m in enumerate(mats) if m == "LK_PLANTS"])      # a shrub crown: atlas-swatch UVs (UV_IN_SWATCH), not box UVs
            err = float(np.abs(exp[~plant_loop] - uv[~plant_loop]).max())
            if err > 1e-4 or any(m != "LK_PLANTS" and PL.TILE[m] != {"LK_ROCK": 4.0, "LK_ROCK_WET": 4.0, "LK_BASALT": 8.0, "LK_MASONRY": 4.0,
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
        plant_slots_ = [i for i, m in enumerate(mats) if m == "LK_PLANTS"]
        if k.startswith("PLANT_") or plant_slots_:
            for p in range(len(me.polygons)):
                if not k.startswith("PLANT_") and int(mi[p]) not in plant_slots_:
                    continue
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
    gate("UV_IN_SWATCH", not bad_sw, f"{sum(1 for k in lib if k.startswith('PLANT_'))} plant meshes + the shrub crown faces of the {len(PL.SPIRE_KINDS)} spires, every face inside one "
         f"swatch {int(PL.SW_MARGIN * 64)} px inside its border; bad: {bad_sw or 'none'}")

    wrong = []
    for k, ob in lib.items():
        mats = [m.name for m in ob.data.materials]
        if k.startswith("PLANT_"):
            if mats != ["LK_PLANTS"]:
                wrong.append((k, mats))
        elif "LK_PLANTS" in mats and not (k in PL.SPIRE_KINDS or any(k == q + sfx for q in PL.SPIRE_KINDS for sfx in ("_WET", "_BASALT"))):   # only the shrub crown of a spire
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
        ob = PL.place(None, k, (cx, y, z), yaw, scale, allow_low=True)      # reference-ground test scene
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
    sh = PL.scatter(None, ["PLANT_SHRUB_A", "PLANT_SHRUB_B", "PLANT_SHRUB_C"], 40, region=reg, masks=[off_fw_big], seed=2, z=0.0, allow_low=True)
    fl = PL.scatter(None, {"PLANT_FLOWER_PURPLE": 2, "PLANT_FLOWER_WHITE": 1, "PLANT_FLOWER_YELLOW": 1}, 80, region=reg,
                    masks=[off_fw], seed=3, z=0.0, allow_low=True)
    tu = PL.scatter(None, {"PLANT_TUFT_A": 3, "PLANT_TUFT_B": 2, "PLANT_TUFT_C": 1}, 600, region=reg, masks=[off_fw], seed=1,
                    z=0.0, allow_low=True)
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
    V, F = _tri_soup(objs)
    return BVHTree.FromPolygons(V, F), [o.name for o in objs]


def _tri_soup(objs, up_only=None):
    """World-space vertices + loop triangles of mesh objects (proper triangulation: n-gons are NOT fanned). up_only: keep only
    triangles whose unit normal.z > up_only."""
    V, F = [], []
    for o in objs:
        co, tris, _tp = PL._np_mesh(o.data)
        mw = np.array(o.matrix_world)
        w = co @ mw[:3, :3].T + mw[:3, 3]
        if up_only is not None:
            nv = np.cross(w[tris[:, 1]] - w[tris[:, 0]], w[tris[:, 2]] - w[tris[:, 0]])
            tris = tris[nv[:, 2] > up_only * np.maximum(np.linalg.norm(nv, axis=1), 1e-12)]
        base = len(V)
        V.extend(map(tuple, w.tolist()))
        F.extend(tuple(t) for t in (tris + base).tolist())
    return V, F


def ground_bvh():
    """Independent (not PL.ground_sampler) BVH of the TOP faces of TERRAIN / FAIRWAY / GREEN / TEE_BOX / BUNKER meshes."""
    objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER"))]
    V, F = _tri_soup(objs, up_only=0.2)
    return BVHTree.FromPolygons(V, F), [o.name for o in objs]


def ground_z(bvh, x, y, ztop=60.0):
    hit = bvh.ray_cast(Vector((x, y, ztop)), Vector((0, 0, -1)), 200.0)
    return None if hit[0] is None else float(hit[0].z)


def make_path(D, half_w=0.8, inset=4.0, spacing=3.0):
    """A DRESS_PATH_00 ribbon through the land rough (inset m inside the cliff edge): stands in for A3's stone path, so the
    scatter's path mask is exercised. Returns the centre polyline [(x, y), ...] ([] when the hole has no suitable stretch)."""
    best = []
    for L in D.loops:
        Pn = np.asarray(L, float)
        n = len(Pn)
        seg = np.hypot(*(np.roll(Pn, -1, 0) - Pn).T)
        cum = np.concatenate([[0], np.cumsum(seg)])
        k = int(cum[-1] / spacing)
        run, runs = [], []
        for i in range(k):
            s = (i + 0.5) * cum[-1] / k
            j = min(int(np.searchsorted(cum, s, side="right") - 1), n - 1)
            t = (s - cum[j]) / max(seg[j], 1e-9)
            a, b = Pn[j], Pn[(j + 1) % n]
            p = a + (b - a) * t
            d = (b - a) / max(seg[j], 1e-9)
            q = p + np.array([-d[1], d[0]]) * inset
            c = P.lie_codes_m(D, np.array([q[0]]), np.array([q[1]]))[0]
            sd = P.signed_dist_m(D, np.array([q[0]]), np.array([q[1]]))[0]
            if c in (P.LIE_ROUGH, P.LIE_OOB) and sd <= -3.0:
                run.append((float(q[0]), float(q[1])))
            else:
                if len(run) > 1:
                    runs.append(run)
                run = []
        if len(run) > 1:
            runs.append(run)
        for r in runs:
            if len(r) > len(best):
                best = r
    if len(best) < 2:
        return []
    verts, faces = [], []
    zz = D.play_z + 0.04
    for (x0, y0), (x1, y1) in zip(best[:-1], best[1:]):
        d = np.array([x1 - x0, y1 - y0])
        ln = float(np.hypot(*d))
        if ln < 1e-6:
            continue
        nrm = np.array([-d[1], d[0]]) / ln * half_w
        b = len(verts)
        verts += [(x0 - nrm[0], y0 - nrm[1], zz), (x1 - nrm[0], y1 - nrm[1], zz), (x1 + nrm[0], y1 + nrm[1], zz), (x0 + nrm[0], y0 + nrm[1], zz)]
        faces.append((b, b + 1, b + 2, b + 3))
    me = bpy.data.meshes.new("DRESS_PATH_00")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new("DRESS_PATH_00", me)
    PL._collection_for("DRESS_PATH").objects.link(ob)
    ob.parent = P.get_root()
    return best


def tri_count(objs):
    t = 0
    for ob in objs:
        ob.data.calc_loop_triangles()
        t += len(ob.data.loop_triangles)
    return t


def lie_water(D, objs):
    X = np.array([o.location.x for o in objs])
    Y = np.array([o.location.y for o in objs])
    if len(X) == 0:
        return np.zeros(0, bool)
    return P.lie_codes_m(D, X, Y) == P.LIE_WATER


def sea_points(D, n, lo=8.0, hi=26.0, seed=0):
    import random
    rng = random.Random(1000 + seed)
    reg = PL.region_band(D, lo, hi, "sea")
    X, Y, _z = reg(rng, 4000)
    pts = []
    for x, y in zip(X.tolist(), Y.tolist()):
        if all(math.hypot(x - a, y - b) > 14.0 for a, b in pts):
            pts.append((x, y))
        if len(pts) >= n:
            break
    return pts


HOLE_STATS = {}


def hole_test(tag, lib_hashes):
    import random
    fresh()
    D = P.start(f"hole{tag}_design", out_dir=os.path.join(SCRATCH, f"hole{tag}"))
    t0 = time.time()
    P.build_terrain(D)
    P.build_play_surfaces(D)
    if tag == "10":
        P.build_water(D, 'WATER_LAVA', 'MAT_LAVA', shallow_material=None, foam_material=None, crest=False)
    else:
        P.build_water(D)
    P.build_gameplay(D)                                  # TEE_MARKER_1/2, HOLE_CUP, FLAG, BALL_START: the marker mask needs them
    t_build = time.time() - t0
    path_pts = make_path(D)
    t0 = time.time()
    var = "BASALT" if tag == "10" else None          # crater: basalt twins in/at the lava
    # --- the dressing. Plants use the DEFAULT region (None) = the whole real land; rocks keep their zones.
    rocks = PL.scatter_rocks(D, 30, zone="rim", seed=4, variant=var) + PL.scatter_rocks(D, 30, zone="sea", seed=5, variant=var)
    shrubs = PL.scatter(D, ["PLANT_SHRUB_A", "PLANT_SHRUB_B", "PLANT_SHRUB_C"], 40, seed=2)
    flowers = PL.scatter(D, {"PLANT_FLOWER_PURPLE": 2, "PLANT_FLOWER_WHITE": 1, "PLANT_FLOWER_YELLOW": 1}, 80, seed=3)
    tufts = PL.scatter(D, {"PLANT_TUFT_A": 3, "PLANT_TUFT_B": 2, "PLANT_TUFT_C": 1}, 600, seed=1)
    agave = PL.scatter(D, {"PLANT_AGAVE_A": 1, "PLANT_AGAVE_B": 1}, 20, seed=6)
    t_sc = time.time() - t0
    props = rocks + shrubs + flowers + tufts + agave
    plants = shrubs + flowers + tufts + agave
    tris = tri_count(props)
    print(f"hole {tag}: terrain+play {t_build:.1f}s, scatter {t_sc:.1f}s: rocks {len(rocks)}, shrubs {len(shrubs)}, flowers {len(flowers)}, "
          f"tufts {len(tufts)}, agave {len(agave)}, path {'yes' if path_pts else 'none'}, tris {tris}", flush=True)
    # --- SCATTER_DEFAULT_ON_LAND: every default-region plant is on the real land, >= 1 m from the shore, on a ground top
    bvh_g, gnames = ground_bvh()
    px, py = D.hole.pin[0] * P.YD, D.hole.pin[1] * P.YD
    markers = [(o.matrix_world.translation.x, o.matrix_world.translation.y) for o in bpy.data.objects
               if o.name.startswith(("TEE_MARKER", "HOLE_CUP", "BALL_START"))]
    X = np.array([o.location.x for o in plants])
    Y = np.array([o.location.y for o in plants])
    water = P.lie_codes_m(D, X, Y) == P.LIE_WATER
    sd = P.signed_dist_m(D, X, Y)
    dzs, zmin = [], 1e9
    for o in plants:
        g = ground_z(bvh_g, o.location.x, o.location.y)
        dzs.append(99.0 if g is None else abs(o.location.z - g))
        zmin = min(zmin, o.location.z)
    dzs = np.array(dzs)
    pin_min = float(np.hypot(X - px, Y - py).min())
    mk_min = min((math.hypot(x - a, y - b) for x, y in zip(X.tolist(), Y.tolist()) for a, b in markers), default=99.0)
    if path_pts:
        pp = np.array(path_pts)
        A, B = pp[:-1], pp[1:]
        pd = float(P._dist_pts_segs(np.stack([X, Y], 1), A, B).min())
    else:
        pd = 99.0
    ok_land = (not water.any()) and float(sd.max()) <= -0.999 and float(dzs.max()) <= 0.05 and zmin >= 5.0 and pin_min >= 6.0 \
        and len(markers) >= 3 and mk_min >= 1.5 and pd >= 0.8 + 0.2 and len(plants) >= 40
    gate(f"SCATTER_DEFAULT_ON_LAND_{tag}", ok_land,
         f"{len(plants)} plants from scatter(region=None): on water {int(water.sum())}; nearest to a shore edge {-float(sd.max()):.2f} m (>= 1.0, "
         f"independent distance field); base vs ray cast onto {len(gnames)} TERRAIN/FAIRWAY/GREEN/TEE_BOX/BUNKER meshes: max |dz| "
         f"{float(dzs.max()):.3f} m (<= 0.05), lowest z {zmin:.2f} (>= 5.0); pin {pin_min:.1f} m (>= 6), {len(markers)} gameplay markers (TEE_MARKER_1/2, HOLE_CUP, BALL_START) {mk_min:.1f} m (>= 1.5); "
         f"nearest to the {'DRESS_PATH ribbon (0.8 m half width)' if path_pts else 'no path on this hole'} {pd:.2f} m (>= 1.0)")
    # --- PLANT_ON_WATER_ZERO: adversarial scatters (huge regions, other seeds / counts, safe=False, sea regions)
    adv_total, adv_water, adv_ground_bad, calls = 0, 0, 0, 0
    kinds_sets = [{"PLANT_TUFT_A": 1}, ["PLANT_SHRUB_A", "PLANT_SHRUB_B"], {"PLANT_FLOWER_PURPLE": 1, "PLANT_FLOWER_WHITE": 1},
                  ["PLANT_AGAVE_B"], ["PLANT_PINE_A", "PLANT_TREE_A"]]
    x0, y0, x1, y1 = P._shore_bbox_m(D, 0.0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    big = max(x1 - x0, y1 - y0) + 300.0
    regions = {
        "None": None,
        "rect +300 m": (x0 - 300, y0 - 300, x1 + 300, y1 + 300),
        "disc over the sea": PL.region_disc(cx, cy, big),
        "polyline over water": PL.region_polyline([(x0 - 100, y0 - 100), (x1 + 100, y1 + 100), (x0 - 100, y1 + 100)], 60.0),
        "band 3-26 m SEA": PL.region_band(D, 3.0, 26.0, "sea"),
        "band 0-6 m land": PL.region_band(D, 0.2, 6.0),
    }
    adv = []
    for si, (seed, count) in enumerate(((11, 40), (12, 150), (13, 600))):
        for rn, reg in regions.items():
            for ki, ks in enumerate(kinds_sets):
                if (si + ki) % 2 and rn not in ("None", "band 3-26 m SEA"):
                    continue                                  # keep the run short: every region / kind pair appears at least once
                if si == 2 and rn not in ("None", "rect +300 m", "disc over the sea"):
                    continue
                safe = not (rn == "rect +300 m" and si == 2)  # the unsafe call: no play-surface / pin masks, ONLY the land rule
                out = PL.scatter(D, ks, count, region=reg, seed=seed + ki, safe=safe, register=False, respect=False)
                calls += 1
                adv += out
    Xa = np.array([o.location.x for o in adv]) if adv else np.zeros(0)
    Ya = np.array([o.location.y for o in adv]) if adv else np.zeros(0)
    wa = (P.lie_codes_m(D, Xa, Ya) == P.LIE_WATER) if adv else np.zeros(0, bool)
    sda = P.signed_dist_m(D, Xa, Ya) if adv else np.zeros(0)
    bad_list = []
    for o in adv:
        g = ground_z(bvh_g, o.location.x, o.location.y)
        if g is None or abs(o.location.z - g) > 0.05 or o.location.z < 5.0:
            bad_list.append((o.name, tuple(round(v, 3) for v in o.location), g))
    bad_g = len(bad_list)
    raised = False
    try:
        PL.scatter(D, ["PLANT_TUFT_A"], 5, surface="sea", seed=1)
    except ValueError:
        raised = True
    gate(f"PLANT_ON_WATER_ZERO_{tag}", int(wa.sum()) == 0 and float(sda.max() if len(sda) else -9) <= -0.999 and bad_g == 0 and raised
         and len(adv) >= 200,
         f"{calls} adversarial scatter calls ({len(regions)} regions x {len(kinds_sets)} kind sets x seeds 11-13 x counts 40/150/600, the 600-count rect call with safe=False) placed "
         f"{len(adv)} plants: ON WATER {int(wa.sum())} (hard gate 0), nearest to a shore edge {-float(sda.max()) if len(sda) else 0:.2f} m, "
         f"bases off the ground (|dz| > 0.05 or z < 5) {bad_g} {bad_list[:2]}; the 'sea band' region placed "
         f"{sum(1 for o in adv if False)} on water by construction; scatter(surface='sea') for plants raises ValueError: {raised}")
    for o in adv:
        bpy.data.objects.remove(o, do_unlink=True)
    PL.reset_scatter(D)
    # --- the rest of the dressing (stacks, outcrop + arch, vines, smoke) for the whole-scene stretch gate
    stacks = []
    for i, (sx, sy) in enumerate(sea_points(D, 3, seed=int(tag))):
        stacks += PL.place_sea_stack(D, sx, sy, (14.0, 22.0, 32.0)[i % 3], 3.5, seed=i)
    extra = list(stacks)
    pts = sea_points(D, 1, 6.0, 20.0, seed=7 + int(tag))
    if pts:
        extra.append(PL.place_outcrop(D, pts[0][0], pts[0][1], 5.0, 6.4, seed=8))
        arch = PL.build_masonry_arch(D, (pts[0][0], pts[0][1], 5.0), 171.2, span_m=7.5, height_m=11.0, seed=8, base_rock=True)
        extra += arch["base"] + arch["vines"] + arch["fallen"]
    extra += PL.hang_vines_on_cliff(D, 7.0, seed=6)
    smoke = PL.build_smoke_cards(D, [((cx, cy, 40.0), 70.0, 90.0), ((cx + 90, cy, 30.0), 40.0, 50.0)])
    # --- rays: no land prop footprint on a play surface; pin clearance
    bvh, names = play_bvh()
    viol = []
    for ob in props:
        x, y, z = ob.location
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
    in_water = [o.name for o, w in zip(props, lie_water(D, props)) if w and o.location.z >= D.play_z - 1.0]
    pin_all = min(math.hypot(o.location.x - px, o.location.y - py) for o in props)
    gate(f"SCATTER_SAFE_{tag}", not viol and not in_water and pin_all >= 6.0,
         f"{len(props)} props; footprint rays hitting {len(names)} play meshes (fairway/first cut/green/apron/tee/bunker+lip): "
         f"{len(viol)} {viol[:3]}; land props standing in water: {len(in_water)}; nearest prop to the pin {pin_all:.1f} m (>= 6)")
    meshes = {ob.data.name for ob in props}
    libok = all(ob.data.get("lk_kind") == ob.data.name and bpy.data.objects.get(ob.data.name) is not None for ob in props)
    gate(f"INSTANCED_{tag}", libok and len(meshes) <= 30 and len(props) >= 10 * len(meshes),
         f"{len(props)} prop objects share {len(meshes)} library meshes (linked duplicates, every mesh is a hidden library mesh)")
    gate(f"HOLE_BUDGET_{tag}", tris <= 150000,
         f"placed {len(tufts)} tufts + {len(shrubs)} shrubs + {len(flowers)} flowers + {len(agave)} agave + {len(rocks)} rocks = {tris} tris (<= 150k)")
    bad = [ob.name for ob in props + extra + smoke if not ob.name.startswith(PL.NAME_PREFIXES) or ob.name.startswith(PL.GROUND_PREFIXES)]
    gate(f"PROP_NAMES_{tag}", not bad, f"collision-prefix / non-section-2 names: {bad[:5] or 'none'}")
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
                   f"{len(rocks)} rocks = {tris} tris, {len(stacks)} stack parts")
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
    # --- legacy swap on a scene with the old stand-ins (icosahedra + a hole-9 style ROCK_STACK_nn) + the whole-scene stretch gate
    P.import_rocks(D)
    legacy = P.scatter_rocks(D, count=10, zone="sea", seed=9) + P.scatter_rocks(D, count=6, zone="foot", seed=10)
    legacy.append(P.place_rock(D, "CLIFF", (P.m(-60, 150)[0], P.m(-60, 150)[1], -2.0), scale=(0.4, 0.4, 1.2)))
    legacy.append(P.place_rock(D, "LARGE", (P.m(-30, 120)[0], P.m(-30, 120)[1], 3.0), scale=(1.1, 1.0, 5.0)))
    st = neg_icosphere("ROCK_STACK_01", 1, 1.0)
    st.data.name = "ROCK_STACK_01"
    for i, v in enumerate(st.data.vertices):
        v.co = Vector((v.co.x * 6.5, v.co.y * 6.5, (v.co.z * 12.0) + 6.0))
    st.location = (P.m(40, 140)[0], P.m(40, 140)[1], 0.0)
    legacy.append(st)
    bpy.context.view_layer.update()
    left_before = len(PL.legacy_rocks())
    rep = []
    swapped = PL.swap_legacy_rocks(D, objs=None, basalt=(tag == "10"), report=rep)
    bpy.context.view_layer.update()
    chk = PL.assert_no_legacy_rocks(D, raise_on_fail=False)
    errs = [r["err"] for r in rep]
    kinds = sorted({o.data.name for o in swapped})
    gate(f"LEGACY_SWAP_{tag}", len(PL.legacy_rocks()) == 0 and chk["ok"] and all(o.name.startswith("ROCK_") for o in swapped)
         and chk["min_verts"] >= 60 and left_before == len(legacy),
         f"{left_before} legacy stand-ins (icosahedra + a ROCK_STACK_01 mesh) -> {len(swapped)} library instances of {kinds}; box size error "
         f"mean {np.mean(errs):.3f} max {max(errs):.3f} (sum of |log ratio| over the axes); legacy rocks left {len(PL.legacy_rocks())}; "
         f"assert_no_legacy_rocks ok {chk['ok']} over {chk['rocks']} ROCK_* objects, min welded verts {chk['min_verts']}")
    sr = PL.stretch_report()
    gate(f"SWAP_NO_STRETCH_2X_scene_{tag}", sr["ok"] and sr["n"] >= 500,
         f"whole dressed scene: {sr['n']} library instances (scatter, stacks, outcrop, arch bases, vines, swap): scale {sr['min_scale']:.2f}.."
         f"{sr['max_scale']:.2f}, max/min {sr['max_ratio']:.2f}; violations {len(sr['violations'])} {sr['violations'][:3]}")
    all_inst = [o for o, _s in PL.instance_scales()]
    HOLE_STATS[tag] = dict(tris=tri_count(all_inst), props=len(all_inst), meshes=len({o.data.name for o in all_inst}),
                           plant_tris=tri_count(props), n_plants=len(plants))
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


# ----------------------------------------------------------------------------- 5: the baseline hole blends
SWAP_STATS = {}


def baseline_swap_test(tag):
    path = os.path.join(BASELINE, f"hole_{tag}.blend")
    if not os.path.isfile(path):
        gate(f"SWAP_NO_STRETCH_2X_{tag}", False, f"missing {path}")
        return
    bpy.ops.wm.open_mainfile(filepath=path)
    PL._COUNTERS.clear()
    PL.reset_scatter(None)
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()[:12]
    n_legacy = len(PL.legacy_rocks())
    legacy_ext = {}
    for lo in PL.legacy_rocks():
        lw = np.array([list(lo.matrix_world @ v.co) for v in lo.data.vertices])
        legacy_ext[lo.name] = (float(lw[:, 2].min()), float(lw[:, 2].max()))
    rep = []
    t0 = time.time()
    out = PL.swap_legacy_rocks(None, basalt=(tag == "10"), report=rep, seed=1)
    dt = time.time() - t0
    bpy.context.view_layer.update()
    sr = PL.stretch_report()
    cr = PL.swap_composition_report()
    chk = PL.assert_no_legacy_rocks(None, raise_on_fail=False)
    tris = tri_count(out)
    grp = {}
    for o in out:
        grp.setdefault(o["lk_swap"], []).append(o)
    d_bot, d_top, d_tail = [], [], []
    members = {r["legacy"]: r["members"] for r in rep}
    cls = {r["legacy"]: r["cls"] for r in rep}
    for k, v in grp.items():
        pz = np.concatenate([np.array([list(o.matrix_world @ vv.co) for vv in o.data.vertices])[:, 2] for o in v])
        if cls[k] == "stack":                    # a spire's 3 m x scale underwater tail is designed in (never visible): measure what is below THAT
            d_tail.append(float(pz.min()) + 3.0 * float(v[0].matrix_world.to_scale().z))
            d_bot.append(0.0)
        else:
            d_bot.append(float(pz.min()) - min(legacy_ext[m][0] for m in members[k]))
        d_top.append(float(pz.max()) - max(legacy_ext[m][1] for m in members[k]))
    n_stack = len(d_tail)
    d_tail = d_tail or [0.0]
    kinds = {}
    for o in out:
        kinds[o.data.name] = kinds.get(o.data.name, 0) + 1
    errs = np.array([r["err"] for r in rep]) if rep else np.zeros(1)
    xs = np.array([sc for _o, sc in PL.instance_scales()]) if sr["n"] else np.zeros((1, 3))
    SWAP_STATS[tag] = dict(blend=os.path.relpath(path, REPO), sha12=sha, legacy=n_legacy, instances=len(out), tris=tris, kinds=kinds,
                           scale_min=[float(v) for v in xs.min(0)], scale_max=[float(v) for v in xs.max(0)], max_ratio=sr["max_ratio"],
                           violations=len(sr["violations"]), box_err_mean=float(errs.mean()), box_err_max=float(errs.max()),
                           multi_instance_plans=sum(1 for r in rep if r["instances"] > 1), seconds=round(dt, 2),
                           stack_class=sum(1 for r in rep if r["cls"] == "stack"), vertical_stacks=len(cr["vertical_stacks"]),
                           identical_clones=len(cr["clones"]), bottom_delta_min=min(d_bot), top_delta_min=min(d_top), top_delta_max=max(d_top))
    ok = sr["ok"] and sr["n"] == len(out) and chk["ok"] and len(PL.legacy_rocks()) == 0 and n_legacy > 0
    extra = ""
    if tag == "10":
        ring = [r for r in rep if min(r["box"][0], r["box"][1]) > 22.0 and r["box"][2] > 40.0]
        towers = [r for r in ring if r["kind"] in PL.TOWER_KINDS]
        extra = f"; wall ring (box > 22 m wide and > 40 m tall): {len(ring)} legacy rocks -> {len(towers)} single tower instances (S/M/L), others {len(ring) - len(towers)}"
        ok = ok and len(ring) >= 100 and len(towers) == len(ring)
    gate(f"SWAP_NO_STRETCH_2X_{tag}", ok,
         f"baseline hole_{tag}.blend (sha {sha}): {n_legacy} legacy rocks -> {len(out)} instances ({SWAP_STATS[tag]['multi_instance_plans']} composed of "
         f"several); per-axis scale {xs.min():.2f}..{xs.max():.2f} (limit 0.5..2.0), max/min {sr['max_ratio']:.2f} (limit 2.0), violations "
         f"{len(sr['violations'])}; kinds {len(kinds)}; assert_no_legacy_rocks ok {chk['ok']} (min verts {chk['min_verts']}); swapped tris {tris}; "
         f"box size error mean {errs.mean():.3f} max {errs.max():.3f}{extra}")
    gate(f"SWAP_NO_STACKED_CLONES_{tag}", cr["ok"] and cr["pieces"] == len(out),
         f"baseline hole_{tag}: {cr['groups']} legacy boxes -> {cr['pieces']} pieces; pieces stacked vertically on another piece of the same box "
         f"(same plan xy, heights differ): {len(cr['vertical_stacks'])} {cr['vertical_stacks'][:3]}; identical clones (same kind, scale within 3 %, "
         f"same yaw mod 90): {len(cr['clones'])} {cr['clones'][:3]}; sea-stack boxes composed as ONE spire + satellites + skirt: "
         f"{SWAP_STATS[tag]['stack_class']}; nz tiles never > 1")
    gate(f"SWAP_ANCHORED_{tag}", min(d_bot) >= -0.2 and min(d_tail) >= -0.5 and min(d_top) >= -1.5 and max(d_top) <= 1.0,
         f"baseline hole_{tag}: replacement vs legacy vertices over {len(grp)} boxes: lowest point delta min {min(d_bot):+.2f} m on the {len(grp) - n_stack} plain boxes "
         f"(>= -0.2: never buried deeper than the legacy), {n_stack} sea-stack groups: lowest point above the spire's designed 3 m x scale underwater tail "
         f"{min(d_tail):+.2f} m (>= -0.5, skirt boulders included); top delta {min(d_top):+.2f} .. {max(d_top):+.2f} m (within -1.5 .. +1.0)")


def repair_gates():
    """v2 repair (review P): NO tiled stacks / identical clones, swap never leaves a short or blob rock, place()/scatter() without D refuse the
    sea. Every gate has a negative control (the old behaviour) that must FAIL."""
    import bmesh  # noqa: F401
    # --- A. composition gate: the old v1 plans (vertical crag pair, 2 x 2 lattice of identical spires) FAIL it, the new cluster passes
    fresh()
    pair = [PL.place(None, "ROCK_CRAG_A_WET", (0.0, 0.0, -4.0), 0.0, 1.5), PL.place(None, "ROCK_CRAG_A_WET", (0.0, 0.0, 2.6), 0.0, 1.5)]
    lat = [PL.place(None, "ROCK_SEASTACK_A_WET", (x, y, 0.0), (0.0 if (x > 0) else math.pi), 1.2) for x in (-5.0, 5.0) for y in (-5.0, 5.0)]
    for o in pair:
        o["lk_swap"] = "OLD_STACK_02"
    for o in lat:
        o["lk_swap"] = "OLD_STACK_04"
    neg = PL.swap_composition_report()
    fresh()
    new = []
    for i, (h, r) in enumerate(((19.3, 9.5), (11.3, 5.0), (14.0, 7.0), (12.0, 3.0))):
        for o in PL.place_sea_stack(None, i * 40.0, 0.0, h, r, seed=i + 1):
            o["lk_swap"] = f"NEW_{i}"
            new.append(o)
    pos = PL.swap_composition_report()
    sums = {}
    for o in new:
        sums.setdefault(o["lk_swap"], []).append(o.data.name)
    gate("SWAP_COMPOSITION_GATE", (not neg["ok"]) and len(neg["vertical_stacks"]) >= 1 and len(neg["clones"]) >= 3 and pos["ok"] and pos["pieces"] == len(new),
         f"NEGATIVE (the v1 plans): a vertical pair of ROCK_CRAG_A_WET {len(neg['vertical_stacks'])} stacked pair(s) and a 2 x 2 lattice of identical "
         f"ROCK_SEASTACK_A_WET {len(neg['clones'])} identical pair(s) -> FAIL as required; NEW place_sea_stack clusters (radius 9.5 / 5 / 7 / 3 m): "
         f"{pos['pieces']} pieces, stacked pairs {len(pos['vertical_stacks'])}, identical clones {len(pos['clones'])}, pieces per stack {[len(v) for v in sums.values()]}, "
         f"main kinds {[v[0] for v in sums.values()]}")

    # --- B. a tall legacy stack (hole 9 style ROCK_STACK_nn, 14 x 15 x 21 m, z -4..17) becomes ONE spire + lower satellites + skirt
    fresh()
    st = neg_icosphere("ROCK_STACK_01", 1, 1.0)
    st.data.name = "ROCK_STACK_01"
    for v in st.data.vertices:
        v.co = Vector((v.co.x * 7.2, v.co.y * 7.4, v.co.z * 10.6 + 6.6))
    st.location = (30.0, 40.0, 0.0)
    thin = neg_icosphere("ROCK_LARGE.001", 1, 1.0)
    thin.data.name = "ROCK_LARGE"
    for v in thin.data.vertices:
        v.co = Vector((v.co.x * 1.1, v.co.y * 1.1, v.co.z * 7.5 + 4.5))
    thin.location = (-30.0, 40.0, 0.0)
    bpy.context.view_layer.update()
    zt = {"ROCK_STACK_01": 17.2, "ROCK_LARGE.001": 12.0}
    rep = []
    out = PL.swap_legacy_rocks(None, report=rep, seed=3)
    bpy.context.view_layer.update()
    grp = {}
    for o in out:
        grp.setdefault(o["lk_swap"], []).append(o)
    ok = True
    notes = []
    for k, objs in grp.items():
        main = objs[0]
        zs = np.array([(main.matrix_world @ v.co).z for v in main.data.vertices])
        spire = main.data.name.startswith(("ROCK_SEASTACK", "ROCK_SPIRE"))
        vert = sum(1 for o in objs if o is not main and (o.matrix_world.translation.xy - main.matrix_world.translation.xy).length < 1.0)
        notes.append(f"{k}: {len(objs)} pieces {[o.data.name for o in objs]}, main summit {zs.max():.1f} m (legacy {zt[k]:.1f})")
        ok = ok and spire and abs(float(zs.max()) - zt[k]) <= 0.8 and vert == 0
    cr = PL.swap_composition_report()
    sr = PL.stretch_report()
    gate("SWAP_TALL_IS_ONE_SPIRE", ok and cr["ok"] and sr["ok"] and len(out) >= 2 and all(r["cls"] == "stack" for r in rep),
         f"tall legacy boxes -> ONE tapering spire at the legacy summit (+ satellites / skirt boulders beside it, never on it): {'; '.join(notes)}; "
         f"composition ok {cr['ok']}, stretch ok {sr['ok']} (scale {sr['min_scale']:.2f}..{sr['max_scale']:.2f})")

    # --- C. mutants: the swap must not leave a <60-vertex rock behind (replace or raise) and replaces a blob of any vertex count
    fresh()
    neg_icosphere("ROCK_SKIN_BAD", 1, 2.0)
    raised = False
    try:
        PL.swap_legacy_rocks(None)
    except RuntimeError as e:
        raised = "ROCK_SKIN_BAD" in str(e)
    fresh()
    big = neg_icosphere("ROCK_BIGICO", 3, 2.5)
    big.location = (0.0, 0.0, 8.0)
    sh = PL.rock_shape_report(big.data)
    flagged = PL._is_legacy_rock(big)
    bpy.context.view_layer.update()
    out = PL.swap_legacy_rocks(None)
    chk = PL.assert_no_legacy_rocks(None, raise_on_fail=False)
    left = [o.name for o in bpy.data.objects if o.name.startswith("ROCK_BIGICO")]
    gate("SWAP_REFUSES_SHORT_AND_BLOB", raised and flagged and sh["blob"] and not left and chk["ok"] and len(out) >= 1,
         f"12-vertex ROCK_SKIN_BAD: swap raises RuntimeError naming it {raised}; 162-vertex blob ROCK_BIGICO (rock_shape_report blob {sh['blob']}, "
         f"radius CV {sh['radius_cv']:.3f}) flagged legacy {flagged}, replaced by {sorted({o.data.name for o in out})} (left {left or 'none'}), "
         f"assert_no_legacy_rocks ok {chk['ok']}")

    # --- D. plants never on the sea through place() / scatter(D=None)
    fresh()
    res = {}
    for nm, fn in (("place z=0", lambda: PL.place(None, "PLANT_TUFT_A", (0, 0, 0.0))),
                   ("place z=0.2", lambda: PL.place(None, "PLANT_SHRUB_A", (0, 0, 0.2))),
                   ("scatter(None, region)", lambda: PL.scatter(None, "PLANT_TUFT_A", 50, region=(-200, -200, 200, 200), seed=1)),
                   ("scatter(None, z=0)", lambda: PL.scatter(None, "PLANT_TUFT_A", 50, region=(-200, -200, 200, 200), seed=1, z=0.0))):
        try:
            fn()
            res[nm] = "PLACED"
        except ValueError:
            res[nm] = "refused"
    fine = PL.place(None, "PLANT_TUFT_A", (0, 0, 5.98))
    low_ok = len(PL.scatter(None, "PLANT_TUFT_A", 10, region=(0, 0, 20, 20), seed=1, z=0.0, allow_low=True)) > 0
    gate("PLANT_PLACE_GUARDS", all(v == "refused" for v in res.values()) and fine is not None and low_ok,
         f"plants without a land mask: {res}; place at z 5.98 ok {fine is not None}; allow_low=True test-scene escape works {low_ok}")


def _prev_lib3():
    """The props library as it stood at the START of repair round 3 (2026-10-05, review 3 of the install: a brown curved strand across the right pier of the hole 8 arch): the frozen
    copy that is the NEGATIVE CONTROL of the round-3 gates. None when missing."""
    import importlib.util
    path = os.path.join(REPO, "work", "postcard-look", "v2", "libs_r3", "backup", "postcard_props_lib.py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("postcard_props_lib_prev3", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["postcard_props_lib_prev3"] = mod
    spec.loader.exec_module(mod)
    return mod


def _prev_lib2():
    """The props library as it stood at the START of repair round 2 (2026-10-04, review 3: hairline slivers across the arch face, tapered-obelisk stacks): the frozen copy
    that is the NEGATIVE CONTROL of the round-2 arch / stack gates. None when missing."""
    import importlib.util
    path = os.path.join(REPO, "work", "postcard-look", "v2", "libs_r2", "backup", "postcard_props_lib.py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("postcard_props_lib_prev2", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["postcard_props_lib_prev2"] = mod
    spec.loader.exec_module(mod)
    return mod


def _prev_lib():
    """The props library as it stood before the 2026-10-04 repair round 1 (frozen copy, used as the NEGATIVE CONTROL of the arch / stack look gates).
    None when the frozen file is missing (the controls are then skipped and said so)."""
    import importlib.util
    path = os.path.join(REPO, "work", "postcard-look", "v2", "libs_r1", "backup", "postcard_props_lib.py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("postcard_props_lib_prev", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["postcard_props_lib_prev"] = mod
    spec.loader.exec_module(mod)
    return mod


def _arch_front_depth(mod, span, height, broken, seed, step=0.02):
    """Build one arch with `mod` and ray-cast it from the front along +Y on a `step` grid: returns (facts dict, depth map (nz, nx) of the first
    hit measured from the start plane, nan = miss, xs, zs, the BVH, object)."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    r = mod.build_masonry_arch(None, (0, 0, 0.0), 0.0, span_m=span, height_m=height, seed=seed, base_rock=False, vines=False, broken=broken)
    ob = r["arch"]
    me = ob.data
    nf = len(me.polygons)
    cnx = np.array([q.normal.x for q in me.polygons])
    ccx = np.array([q.center.x for q in me.polygons])
    ccz = np.array([q.center.z for q in me.polygons])
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
    d = r["dims"]
    depth = max(1.0, 0.17 * span)
    y_start = -depth / 2 - 0.5
    xs = np.arange(-(d["r_in"] + d["pw"]) + 0.1, d["r_in"] + d["pw"] - 0.1, step)
    zs = np.arange(0.45, height - 0.2, step)
    Dm = np.full((len(zs), len(xs)), np.nan)
    for i, z in enumerate(zs.tolist()):
        for j, x in enumerate(xs.tolist()):
            h = bvh.ray_cast(Vector((x, y_start, z)), Vector((0, 1, 0)), depth + 1.0)
            if h[0] is not None:
                Dm[i, j] = h[0].y - y_start
    facts = dict(faces=nf, dims=d, cnx=cnx, ccx=ccx, ccz=ccz, bvh=bvh, depth=depth, span=span, height=height, broken=broken)
    return facts, Dm, xs, zs


def _deep_slits(Dm, k=2, relief_m=0.03):
    """Cells whose first hit is more than `relief_m` deeper than BOTH cells k steps (4 cm) to either side, along x and along z: a narrow deep gap
    (a mortar slot) shows up, a step edge or a shallow V-groove does not."""
    def rel(A, axis):
        return A - np.maximum(np.roll(A, k, axis), np.roll(A, -k, axis))
    rl = np.fmax(rel(Dm, 0), rel(Dm, 1))
    rl[:k] = 0
    rl[-k:] = 0
    rl[:, :k] = 0
    rl[:, -k:] = 0
    rl = np.nan_to_num(rl, nan=0.0)
    return int((rl > relief_m).sum()), float(rl.max()), int(np.isfinite(Dm).sum())


def round2_gates():
    """2026-10-04 repair round 1 (review K/L: the ruin arch has dark slivers and a notched edge; the sea stacks look like faceted grey blobs)."""
    prev = _prev_lib()
    # --- ARCH: exact-fit blocks (no see-through gap, no deep mortar slot, coplanar pier faces, face budget), measured on the real mesh
    for tag, span, height, broken, seed in (("08", 7.5, 11.0, False, 8), ("09_BROKEN", 6.0, 9.0, True, 12)):
        fresh()
        PL.ensure_library(["ROCK_OUTCROP_A"])
        facts, Dm, xs, zs = _arch_front_depth(PL, span, height, broken, seed)
        d, bvh = facts["dims"], facts["bvh"]
        r_in, r_out, zsp, pw = d["r_in"], d["r_out"], d["zs"], d["pw"]
        n_ = int(round(math.pi * (r_in + (r_out - r_in) / 2) / max(0.7, 0.12 * span)))
        n_ += 1 - n_ % 2

        def solid(x, z):
            ax = abs(x)
            if d.get("plinth_h", 0.36) + 0.03 < z < zsp - 0.03 and r_in + 0.03 < ax < r_in + pw - 0.03:
                return not (broken and x < 0 and z > zsp - 1.9)
            rr = math.hypot(x, z - zsp)
            if z > zsp + 0.03 and r_in + 0.03 < rr < r_out - 0.06:
                ang = math.atan2(z - zsp, x)
                return not (broken and ang > math.pi * (n_ // 2 - 1) / n_ - 0.03)
            return False
        n_solid, n_miss = 0, 0
        for i, z in enumerate(zs.tolist()):
            for j, x in enumerate(xs.tolist()):
                if solid(x, z):
                    n_solid += 1
                    if not math.isfinite(Dm[i, j]):
                        n_miss += 1
        gate(f"ARCH_NO_SEE_THROUGH_{tag}", n_miss == 0,
             f"{n_solid} rays at 2 cm through the solid part of the masonry (3 cm inside every block edge): {n_miss} pass through (sky)")
        sel = (np.abs(facts["cnx"]) > 0.999) & (facts["ccz"] > 0.5) & (facts["ccz"] < zsp - 0.2) & (np.abs(facts["ccx"]) > r_in + pw - 0.01)
        spread = float(np.abs(np.abs(facts["ccx"][sel]) - (r_in + pw)).max()) if sel.any() else 99.0
        gate(f"ARCH_PIER_COPLANAR_{tag}", sel.any() and spread < 1e-4,
             f"{int(sel.sum())} outer pier faces of the courses lie within {spread * 1000:.3f} mm of x = +-(r_in + pw): every course is flush")
        n_new, rmax, n_hit = _deep_slits(Dm)
        ctrl = "control skipped (frozen previous library missing)"
        ctrl_ok = True
        if prev is not None:
            fresh()
            prev._COUNTERS.clear()
            _f, Dm_old, _x, _z = _arch_front_depth(prev, span, height, broken, seed)
            n_old, rmax_old, _h = _deep_slits(Dm_old)
            ctrl_ok = n_old > 50 * max(n_new, 1) and n_old > 200
            ctrl = f"NEGATIVE CONTROL (the previous arch, 5 cm mortar gaps): {n_old} slot cells, max relief {rmax_old * 100:.1f} cm -> {'detected' if ctrl_ok else 'BLIND'}"
        gate(f"ARCH_NO_DEEP_SLITS_{tag}", n_new <= max(4, 0.0002 * n_hit) and ctrl_ok,
             f"{n_new} of {n_hit} cells ({100 * n_new / max(n_hit, 1):.4f} %, limit 0.02 %) are > 3 cm deeper than both cells 4 cm to either side (max relief "
             f"{rmax * 100:.1f} cm); {ctrl}")
        gate(f"ARCH_FACES_{tag}", facts["faces"] <= 500, f"{facts['faces']} polygons (<= 500), blocks with chamfered joints (V-grooves 2.2 cm), {d.get('parts')}")
    # --- SEA STACKS: smooth-shaded, strata ledges (pairs of rings < 25 cm apart), not the previous round's flat-shaded faceted spires
    def craggy(me):
        co, tris, tp = PL._np_mesh(me)
        ef = {}
        for q in me.polygons:
            vs = list(q.vertices)
            for i in range(len(vs)):
                ef.setdefault(tuple(sorted((vs[i], vs[(i + 1) % len(vs)]))), []).append(q.index)
        sharp = np.zeros(len(me.edges), bool)
        sh = me.attributes.get("sharp_edge")
        if sh is not None:
            sh.data.foreach_get("value", sharp)
        ed = np.empty(len(me.edges) * 2, np.int32)
        me.edges.foreach_get("vertices", ed)
        idx = {tuple(sorted(e)): i for i, e in enumerate(ed.reshape(-1, 2).tolist())}
        inner = [k for k, v in ef.items() if len(v) == 2]
        smooth = sum(1 for k in inner if not sharp[idx[k]]) / max(len(inner), 1)
        sl = me.attributes.get("lk_slice")
        v = np.empty(len(me.vertices), np.int32)
        sl.data.foreach_get("value", v)
        zmean = {int(s_): float(co[v == s_][:, 2].mean()) for s_ in set(v.tolist()) if s_ >= 0}
        zs_ = sorted(z for z in zmean.values() if z >= 0.0)
        pairs = sum(1 for a_, b_ in zip(zs_[:-1], zs_[1:]) if b_ - a_ < 0.25)
        return smooth, pairs
    fresh()
    kinds = list(PL.SEASTACK_KINDS) + ["ROCK_SPIRE_A"]
    cur = {k: craggy(PL.library_object(k).data) for k in kinds}
    ok = all(sm >= 0.45 and pr >= 4 for sm, pr in cur.values())
    ctrl = "control skipped (frozen previous library missing)"
    ctrl_ok = True
    if prev is not None:
        fresh()
        prev._COUNTERS.clear()
        old = {k: craggy(prev.library_object(k).data) for k in kinds}
        ctrl_ok = all(not (sm >= 0.45 and pr >= 4) for sm, pr in old.values())
        ctrl = "NEGATIVE CONTROL (the previous flat-shaded spires): " + ", ".join(f"{k.replace('ROCK_', '')} {sm:.2f}/{pr}" for k, (sm, pr) in old.items()) + \
            f" -> {'all FAIL as they must' if ctrl_ok else 'SOME PASS (!)'}"
    gate("SEASTACK_CRAGGY", ok and ctrl_ok,
         "smooth-edge share / ledge pairs: " + ", ".join(f"{k.replace('ROCK_', '')} {sm:.2f}/{pr}" for k, (sm, pr) in cur.items()) +
         f" (need >= 0.45 smooth interior edges and >= 4 ledge pairs: two rings < 25 cm apart); {ctrl}")


def _arch_leaks(mod, span, height, broken, seed, step=0.08):
    """Oblique see-through test of the arch built by `mod`: rays from 28 directions (azimuth +-70 deg round the front normal, elevation -12..45 deg, 25 m out) to sample points
    in the middle plane of the SOLID masonry (3-4 cm inside every block edge). In a closed solid the first hit is a FRONT face (normal facing the ray source); a first hit on a
    BACK face, or none, means the ray entered the stone through a crack. Returns (points, rays, leaking rays, faces)."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    r = mod.build_masonry_arch(None, (0, 0, 0.0), 0.0, span_m=span, height_m=height, seed=seed, base_rock=False, vines=False, broken=broken, name="DRESS_ARCH_00")
    ob = r["arch"]
    me = ob.data
    nf = len(me.polygons)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
    d = r["dims"]
    r_in, r_out, zsp, pw = d["r_in"], d["r_out"], d["zs"], d["pw"]
    n_ = int(round(math.pi * (r_in + (r_out - r_in) / 2) / max(0.7, 0.12 * span)))
    n_ += 1 - n_ % 2
    pts = []
    for x in np.arange(-(r_in + pw), r_in + pw, step):
        for z in np.arange(d.get("plinth_h", 0.36) + 0.06, height - 0.1, step):
            ax = abs(x)
            if z < zsp - 0.03 and r_in + 0.04 < ax < r_in + pw - 0.04:
                ok = not (broken and x < 0 and z > zsp - 1.9)
            else:
                rr = math.hypot(x, z - zsp)
                ok = False
                if z > zsp + 0.03 and r_in + 0.04 < rr < r_out - 0.08:
                    ang = math.atan2(z - zsp, x)
                    ok = not (broken and ang > math.pi * (n_ // 2 - 1) / n_ - 0.03)
            if ok:
                pts.append(Vector((x, 0.0, z)))
    cams = []
    for az in (-70, -45, -20, 0, 20, 45, 70):
        for el in (-12, 8, 28, 45):
            e_, a_ = math.radians(el), math.radians(az)
            cams.append(Vector((math.sin(a_) * math.cos(e_), -math.cos(a_) * math.cos(e_), math.sin(e_))) * 25.0)
    leaks, nray = 0, 0
    for P0 in pts:
        for c in cams:
            dv = -c.normalized()
            h = bvh.ray_cast(P0 + c, dv, 25.5)
            nray += 1
            if h[0] is None or h[1].dot(dv) > 0:
                leaks += 1
    return len(pts), nray, leaks, nf


def round3_gates():
    """2026-10-04 repair round 2 (review 3): hole 8's ruin arch still showed hairline slivers across its face; the sea stacks read as tapered obelisks with bright green pyramid caps."""
    prev = _prev_lib2()
    # --- ARCH: no oblique see-through (the round-1 gates only cast frontal rays), joints on the mortar rows of the texture, joint faces on a mortar row of the albedo
    for tag, span, height, broken, seed in (("08", 9.144, 12.166, False, 8), ("09_BROKEN", 6.0, 9.0, True, 12), ("SMALL", 4.0, 6.5, False, 2)):
        fresh()
        PL.ensure_library(["ROCK_OUTCROP_A"])
        npts, nray, leaks, nf = _arch_leaks(PL, span, height, broken, seed)
        ctrl = "control skipped (frozen start-of-round library missing)"
        ctrl_ok = True
        if prev is not None:
            fresh()
            prev._COUNTERS.clear()
            _n, nray_o, leaks_o, _nf = _arch_leaks(prev, span, height, broken, seed)
            ctrl_ok = leaks_o >= 10
            ctrl = f"NEGATIVE CONTROL (the arch of the start of this round: wedges with a 0-9 mm random front offset): {leaks_o} of {nray_o} rays leak -> {'detected' if ctrl_ok else 'BLIND'}"
        gate(f"ARCH_NO_OBLIQUE_LEAK_{tag}", leaks == 0 and ctrl_ok,
             f"{npts} sample points inside the solid masonry x 28 oblique directions = {nray} rays: {leaks} first hits on a back face / none ({nf} polygons); {ctrl}")
    fresh()
    r = PL.build_masonry_arch(None, (0, 0, 0.0), 0.0, span_m=9.144, height_m=12.166, seed=8, base_rock=False, vines=False, name="DRESS_ARCH_00")
    me, d = r["arch"].data, r["dims"]
    pitch, phase, v_row, depth = PL.masonry_grid()
    img = PL._image("Masonry_C")
    w_, h_ = int(img.size[0]), int(img.size[1])
    prof = np.array(img.pixels[:], np.float32).reshape(h_, w_, 4)[:, :, :3].mean(2).mean(1)

    def joint_lum(z, voff):
        v = ((z - voff) / PL.TILE["LK_MASONRY"]) % 1.0
        y = int(v * h_) % h_
        return float(np.mean([prof[(y + k) % h_] for k in (-1, 0, 1)]))
    # exposed horizontal faces = the plinth top, the top of the last pier course (the spring line) and every haunch row top: all are joint planes of the grid
    zj = sorted({round(float(q.center.z), 4) for q in me.polygons if q.normal.z > 0.999 and q.center.z > 0.2})
    zj = [z for z in zj if z <= d["zs"] + 0.5 * d["r_out"] * 0.8 + 0.01]
    uvl = me.uv_layers.active.data
    mortar, big, n_poly = 0, 0, len(me.polygons)
    for q in me.polygons:
        vs = [uvl[li].uv[1] for li in q.loop_indices]
        if max(vs) - min(vs) < 0.012 and abs(sum(vs) / len(vs) - v_row) < 0.004:
            mortar += 1
            if q.area > 0.3:
                big += 1
    lum_new = float(np.mean([joint_lum(z, d["voff"]) for z in zj]))
    prev_ctrl = ""
    ctrl_ok = True
    if prev is not None:
        fresh()
        prev._COUNTERS.clear()
        ro = prev.build_masonry_arch(None, (0, 0, 0.0), 0.0, span_m=9.144, height_m=12.166, seed=8, base_rock=False, vines=False, name="DRESS_ARCH_00")
        mo = ro["arch"].data
        zo = sorted({round(float(q.center.z), 4) for q in mo.polygons if q.normal.z > 0.999 and q.center.z > 0.2})
        zo = [z for z in zo if z <= ro["dims"]["zs"] + 0.5 * ro["dims"]["r_out"] * 0.8 + 0.01]
        lum_old = float(np.mean([joint_lum(z, 0.0) for z in zo])) if zo else float(prof.mean())
        ctrl_ok = (prof.mean() - lum_old) < 0.5 * depth
        prev_ctrl = f"; NEGATIVE CONTROL (round-1 arch, joints at random heights, no UV phase): {len(zo)} joint planes, mean luminance there {lum_old:.3f} (stone {prof.mean():.3f}) -> {'detected' if ctrl_ok else 'BLIND'}"
    fold_ok = abs(((d["zs"] - d["plinth_h"]) / pitch) - round((d["zs"] - d["plinth_h"]) / pitch)) < 1e-6
    gate("ARCH_JOINTS_ON_MORTAR_ROWS", (prof.mean() - lum_new) >= 0.6 * depth and fold_ok and ctrl_ok,
         f"{len(zj)} exposed joint planes (plinth top, spring line, haunch row tops) at z {zj[0]:.2f} .. {zj[-1]:.2f}: the painted Masonry_C luminance there is {lum_new:.3f} against a stone mean "
         f"{prof.mean():.3f} (mortar rows {prof.min():.3f}, depth {depth:.3f}; need the joints >= 0.6 x depth darker), pier height = {round((d['zs'] - d['plinth_h']) / pitch)} x the "
         f"measured pitch {pitch:.3f} m (phase {phase:.3f} m, UV phase voff {d['voff']:.3f} m){prev_ctrl}")
    gate("ARCH_JOINT_FACES_MORTAR_UV", mortar >= 100 and big == 0,
         f"{mortar} chamfer / strip faces of {n_poly} carry the mortar UV (a mortar ROW of the albedo at v {v_row:.4f}, V extent < 0.012 = 6 px, isotropic or squeezed <= 3.5:1); "
         f"{big} of them are larger than 0.3 m2 (must be 0)")
    # --- VINES: the stalk keeps a real width at the tip (the review's 1 px white line)
    fresh()
    w_tip, w_top = [], []
    for k in PL.VINE_KINDS:
        m = PL.library_object(k).data
        co = np.array([v.co[:] for v in m.vertices])
        z0 = co[:, 2].min()
        # the stalk rings are the first 3 vertices of each ring; leaves are octahedra: take the ring at the very bottom of the stalk = vertices of the stalk strip at z of the stalk end
        ring_end = co[np.abs(co[:, 2] - (-PL.VINE_LENGTH[k])) < 1e-6]
        ring_top = co[np.abs(co[:, 2] - 0.0) < 1e-6]
        w_tip.append(max(float(np.linalg.norm(a - b)) for a in ring_end for b in ring_end) if len(ring_end) >= 3 else 0.0)
        w_top.append(max(float(np.linalg.norm(a - b)) for a in ring_top for b in ring_top) if len(ring_top) >= 3 else 0.0)
    gate("VINE_TIP_WIDTH", min(w_tip) >= 0.027 and min(w_top) >= 0.04,
         f"stalk width (the longest side of the 3-corner ring) at the tip {min(w_tip) * 100:.1f}..{max(w_tip) * 100:.1f} cm (>= 2.7 cm = 1.5 px at 25 m), at the top {min(w_top) * 100:.1f}..{max(w_top) * 100:.1f} cm (>= 4 cm)")
    # --- SEA STACKS: shrub crown instead of a pyramid, asymmetric axis, exact height, muted greens
    fresh()
    PL.write_plants_atlas()
    rows, ok_all = [], True
    allowed_sw = {PL.SWATCH[n_] for n_ in ("G_DEEP", "G_DARK", "OLIVE_DARK", "G_MID", "OLIVE")}
    for k in PL.SPIRE_KINDS:
        m = PL.library_object(k).data
        co, tris, _tp = PL._np_mesh(m)
        _vi, co3, pol, nrm, mi = PL._loop_arrays(m)
        mats = [x.name for x in m.materials]
        ps = [i for i, n_ in enumerate(mats) if n_ == "LK_PLANTS"]
        n_crown = int(np.isin(mi, ps).sum())
        zmax = float(co[:, 2].max())
        Hs = PL.SPIRE_SPECS[k]["height"]
        hc_t = min(1.7, 0.085 * Hs + 0.2)
        # crown extent vs the neck 0.3 m under it
        crown_pts = np.array([co3[vv][:2] for q in np.nonzero(np.isin(mi, ps))[0] for vv in [int(t_) for t_ in m.polygons[int(q)].vertices]])
        crown_w = float(np.ptp(crown_pts[:, 0])) if len(crown_pts) else 0.0
        sec = PL.mesh_section(co, tris, Hs - hc_t - 0.35)[:, :2]
        neck_w = float(np.ptp(sec[:, 0])) if len(sec) else 1.0
        # swatches used by the crown faces
        uvs = me_uv = m.uv_layers.active.data
        cells = set()
        for q in np.nonzero(np.isin(mi, ps))[0]:
            u_, v_ = uvs[m.polygons[int(q)].loop_indices[0]].uv
            cells.add(int(math.floor(v_ * 4)) * 4 + int(math.floor(u_ * 4)))
        # the atlas rows: row 0 at the TOP of the image, v 0 at the bottom: swatch index = (3 - floor(v*4)) * 4 + floor(u*4)
        sw_idx = {(3 - c // 4) * 4 + (c % 4) for c in cells}
        # axis offset: centroid of the section at 15 % vs 85 % of the height above the water
        def cen(f):
            q = PL.mesh_section(co, tris, f * Hs)[:, :2]
            return q.mean(0) if len(q) else np.zeros(2)
        off = float(np.linalg.norm(cen(0.85) - cen(0.15))) / Hs
        good = n_crown >= 25 and abs(zmax - Hs) < 0.06 and 0.95 <= crown_w / max(neck_w, 1e-6) <= 1.9 and sw_idx <= allowed_sw and off >= 0.04
        ok_all &= good
        rows.append(f"{k.replace('ROCK_', '')}: crown {n_crown} faces, summit {zmax:.2f} m (design {Hs:g}), crown / neck width {crown_w / max(neck_w, 1e-6):.2f}, axis offset {off:.2f} H, swatches {sorted(sw_idx)} {'ok' if good else 'BAD'}")
    ctrl = ""
    ctrl_ok = True
    if prev is not None:
        fresh()
        prev._COUNTERS.clear()
        mo = prev.library_object("ROCK_SEASTACK_A").data
        mats_o = [x.name for x in mo.materials]
        n_plants_o = int(sum(1 for q in mo.polygons if mats_o[q.material_index] == "LK_PLANTS"))
        ctrl_ok = n_plants_o == 0
        ctrl = f"; NEGATIVE CONTROL (the start-of-round stack): {n_plants_o} LK_PLANTS faces, grass roof only -> {'detected' if ctrl_ok else 'BLIND'}"
    gate("SPIRE_SHRUB_CROWN", ok_all and ctrl_ok,
         "; ".join(rows) + f" (need >= 25 dome faces in LK_PLANTS, summit at the design height +-6 cm, crown 0.95-1.9 x the neck, only the muted swatches G_DEEP / G_DARK / OLIVE_DARK / G_MID / OLIVE, "
         f"axis offset >= 0.04 x the height){ctrl}")


def _extrados_step(mod, span, height, seed):
    """Depth step between the ring face and the haunch face along the extrados of the right half of an arch built by `mod`: front rays (+Y, 2 cm grid) at r_out -+ 0.08 m on every
    z row of the haunch zone; returns (list of |step| in metres, max, p95, n pairs, the dims)."""
    facts, Dm, xs, zs = _arch_front_depth(mod, span, height, False, seed)
    d = facts["dims"]
    r_out, zsp = d["r_out"], d["zs"]
    steps = []
    for zi, z in enumerate(zs.tolist()):
        dz = z - zsp
        if dz < 0.25 or dz > 0.80 * r_out - 0.3:
            continue
        xe = math.sqrt(max(r_out * r_out - dz * dz, 0.0))
        j_in = int(round((xe - 0.08 - xs[0]) / 0.02))
        j_out = int(round((xe + 0.08 - xs[0]) / 0.02))
        if not (0 <= j_in < len(xs) and 0 <= j_out < len(xs)):
            continue
        a, b = Dm[zi, j_in], Dm[zi, j_out]
        if math.isfinite(a) and math.isfinite(b):
            steps.append(abs(float(b - a)))
    arr = np.array(steps) if steps else np.zeros(1)
    return steps, float(arr.max()), float(np.percentile(arr, 95)), len(steps), d


def round4_gates():
    """2026-10-05 repair round 3 (review 3 of the installed holes): the hole 8 arch shows ONE long brown curved strand across the right pier. Root cause = the 12 cm deep step between the
    ring and the recessed haunch with a mortar-UV strip on it: a long, smooth, brown 3 px line that no other joint has."""
    prev = _prev_lib3()
    rows, ok = [], True
    for tag, span, height, seed in (("08", 9.144, 12.166, 8), ("SMALL", 4.0, 6.5, 2), ("07", 7.5, 11.0, 8)):
        fresh()
        PL.ensure_library(["ROCK_OUTCROP_A"])
        steps, smax, p95, n, d = _extrados_step(PL, span, height, seed)
        good = n >= 10 and smax <= 0.05
        ok &= good
        rows.append(f"{tag}: {n} z rows, step ring->haunch max {smax * 100:.1f} cm, p95 {p95 * 100:.1f} cm {'ok' if good else 'BAD'}")
    ctrl, ctrl_ok = "control skipped (frozen start-of-round library missing)", True
    if prev is not None:
        fresh()
        prev._COUNTERS.clear()
        _s, omax, op95, on, _d = _extrados_step(prev, 9.144, 12.166, 8)
        ctrl_ok = omax >= 0.10
        ctrl = f"NEGATIVE CONTROL (the start-of-round arch, 12 cm recess): max step {omax * 100:.1f} cm, p95 {op95 * 100:.1f} cm -> {'detected' if ctrl_ok else 'BLIND'}"
    gate("ARCH_EXTRADOS_NO_STEP", ok and ctrl_ok,
         "; ".join(rows) + f" (limit 5 cm: the ring / haunch boundary is a normal V-groove joint, not a step that carries a long brown strip); {ctrl}")
    # the mortar-UV strip faces on the extrados are at most 5 cm wide (a joint line, not a band)
    def wide_faces(mod):
        fresh()
        r = mod.build_masonry_arch(None, (0, 0, 0.0), 0.0, span_m=9.144, height_m=12.166, seed=8, base_rock=False, vines=False, name="DRESS_ARCH_00")
        me = r["arch"].data
        uvl = me.uv_layers.active.data
        v_row = mod.masonry_grid()[2]
        n = 0
        for q in me.polygons:
            vs = [uvl[li].uv[1] for li in q.loop_indices]
            if max(vs) - min(vs) < 0.012 and abs(sum(vs) / len(vs) - v_row) < 0.004:           # mortar-UV faces: chamfers + strips
                ys = [me.vertices[i].co.y for i in q.vertices]
                if max(ys) - min(ys) > 0.06:                                                      # deeper than 6 cm = a step wall painted as a strip, not a chamfer
                    n += 1
        return n
    wide = wide_faces(PL)
    ctrl, ctrl_ok = "control skipped", True
    if prev is not None:
        prev._COUNTERS.clear()
        wo = wide_faces(prev)
        ctrl_ok = wo >= 5
        ctrl = f"NEGATIVE CONTROL (start-of-round arch): {wo} such faces -> {'detected' if ctrl_ok else 'BLIND'}"
    gate("ARCH_NO_DEEP_MORTAR_STRIP", wide == 0 and ctrl_ok,
         f"{wide} mortar-UV faces of DRESS_ARCH_00 are deeper than 6 cm (a step wall painted as a brown strip); chamfers and 4.5 cm strips only; {ctrl}")


def main():
    t = time.time()
    hashes, rep = library_gates()
    repair_gates()
    round2_gates()
    round3_gates()
    round4_gates()
    # budget worst case (library maxima, independent of placement)
    tri = {k: v["tris"] for k, v in rep.items()}
    worst = (600 * max(tri[k] for k in PL.TUFT_KINDS) + 40 * max(tri[k] for k in ("PLANT_SHRUB_A", "PLANT_SHRUB_B", "PLANT_SHRUB_C")) +
             80 * max(tri[k] for k in ("PLANT_FLOWER_PURPLE", "PLANT_FLOWER_WHITE", "PLANT_FLOWER_YELLOW")) +
             60 * max(tri[k] for k in PL.ROCK_KINDS if not k.startswith(("ROCK_SEASTACK", "ROCK_SPIRE", "ROCK_OUTCROP"))))
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
        extra_paths = render_extra_sheets()
    if DO_BASELINE:
        for tag in HOLES:
            baseline_swap_test(tag)
    # ---- budget
    lib_over = {k: v["faces"] for k, v in rep.items() if v["faces"] > 500}
    tuft_max = max(rep[k]["faces"] for k in PL.TUFT_KINDS)
    hs = "; ".join(f"hole {t}: dressed scene {HOLE_STATS[t]['tris']} tris ({HOLE_STATS[t]['props']} instances of {HOLE_STATS[t]['meshes']} meshes)"
                   for t in HOLE_STATS)
    bs = "; ".join(f"baseline hole {t} swap: {SWAP_STATS[t]['instances']} instances, {SWAP_STATS[t]['tris']} tris" for t in SWAP_STATS)
    gate("PROPS_BUDGET", not lib_over and tuft_max <= 120 and all(v["tris"] <= 250000 for v in HOLE_STATS.values())
         and all(v["tris"] <= 150000 for v in SWAP_STATS.values()) and bool(HOLE_STATS or not DO_HOLES),
         f"{len(rep)} library meshes, max {max(v['faces'] for v in rep.values())} faces (<= 500; over: {lib_over or 'none'}), tufts {tuft_max} faces "
         f"(<= 120); {hs}; {bs}")
    if SWAP_STATS:
        import json
        with open(os.path.join(V2, "swap_stats.json"), "w") as f:
            json.dump(SWAP_STATS, f, indent=1)
    if DO_RENDER:
        out, shape = compose_sheet(paths + HOLE_PANELS, SHEET, cols=3)
        gate("PROPS_SHEET", os.path.isfile(out), f"{os.path.relpath(out, REPO)} {shape[1]}x{shape[0]} ({len(paths) + len(HOLE_PANELS)} panels); "
             f"extra sheets {[os.path.relpath(p, REPO) for p in extra_paths]}")
    fails = [r for r in RESULTS if not r[1]]
    gate("PROPS_SMOKE_PASS", not fails, f"{len(RESULTS) - len(fails)}/{len(RESULTS)} gates pass before this line in {time.time() - t:.1f}s; "
         f"failing: {[r[0] for r in fails] or 'none'}")
    fails = [r for r in RESULTS if not r[1]]
    print(f"SUMMARY: {len(RESULTS) - len(fails)}/{len(RESULTS)} gates PASS in {time.time() - t:.1f}s", flush=True)
    return 1 if fails else 0


def render_extra_sheets():
    """seastack_sheet.png (old stacks vs the new spires from 3 azimuths) and towers_sheet.png (columns / crags / sizes)."""
    paths = []
    # --- sea stacks: old A, old B, new A, B, C, SPIRE_A; azimuth = instance yaw 0 / 120 / 240
    for az, tag in ((0, "a"), (120, "b"), (240, "c")):
        fresh()
        setup_scene((1500, 560))
        water = ref_mat("REF_WATER", (36, 104, 168), rough=0.15)
        ref_plane("REF_WATER_S", 0, 0, 0.0, 600, 600, water.name)
        PL.write_plants_atlas()
        x = -34.0
        items = [("old A", old_seastack("NEG_OLD_SEASTACK_A", "A")), ("old B", old_seastack("NEG_OLD_SEASTACK_B", "B"))]
        for nm, me in items:
            ob = bpy.data.objects.new("REF_" + nm, me)
            bpy.context.scene.collection.objects.link(ob)
            ob.location = (x, 0, 0)
            ob.rotation_euler = (0, 0, math.radians(az))
            x += 11.0
        for k in PL.SEASTACK_KINDS + ("ROCK_SPIRE_A",):
            PL.place(None, k, (x, 0, 0), math.radians(az) + 0.3)
            x += 11.0
        ref_figure(-40, -8, 0.0)
        cam = camera("CAM_S", Vector((4, -92, 15)), Vector((4, 0, 11)), lens=30)
        names = ["OLD A", "OLD B"] + [f"{k.replace('ROCK_', '').replace('SEASTACK_', '')} {PL.SPIRE_SPECS[k]['height']:.0f} m"
                                      for k in PL.SEASTACK_KINDS + ("ROCK_SPIRE_A",)]
        for i, nm in enumerate(names):
            label(nm, (-34 + 11 * i, -9.0, 0.3), 0.9, cam, (255, 255, 255))
        title(cam, f"SEA STACKS  azimuth {az} deg: old two-block stacks (left, FAIL) vs the tapering spires (right)")
        sc = bpy.context.scene
        sc.camera = cam
        path = os.path.join(SCRATCH, f"seastack_az{az}.png")
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        paths.append(path)
    out, shape = compose_sheet(paths, os.path.join(V2, "seastack_sheet.png"), cols=1)
    # --- towers + clusters + crags
    fresh()
    setup_scene((1500, 620))
    PL.write_plants_atlas()
    water = ref_mat("REF_WATER", (36, 104, 168), rough=0.15)
    ref_plane("REF_WATER_T", 0, 0, 0.0, 800, 800, water.name)
    lava = ref_mat("REF_LAVA", (255, 110, 30), emission=2.0, image="Lava_E")
    x = -62.0
    kinds = ["ROCK_CRAG_A", "ROCK_CRAG_B", "ROCK_BASALT_F", "ROCK_BASALT_E", "ROCK_WALL_BASALT_S", "ROCK_WALL_BASALT_M", "ROCK_WALL_BASALT_L"]
    labs = []
    for k in kinds:
        mn, mx = PL.lib_bbox(k)
        w = mx.x - mn.x
        PL.place(None, k, (x + w / 2 - (mn.x + mx.x) / 2, 0, 0), 0.3, 1.0)
        labs.append((x + w / 2, k.replace("ROCK_", "")))
        x += w + 5.0
    ref_figure(-66, -10, 0.0)
    cam = camera("CAM_T", Vector((0, -150, 28)), Vector((0, 0, 20)), lens=30)
    for cx_, nm in labs:
        label(nm, (cx_, -14.0, 0.4), 1.4, cam, (255, 255, 255))
    title(cam, "CRAGS + BASALT 8 m / 12 m clusters + wall-ring TOWERS S / M / L", size=0.04)
    sc = bpy.context.scene
    sc.camera = cam
    path = os.path.join(V2, "towers_sheet.png")
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return [out, path]


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    if "--no-exit" not in ARGS:
        os._exit(code)
