"""Hole 10 CRATER: scene build + POSTCARD_LOOK pass (a rim ribbon and a pillar-green standing in a lava crater, one flat play height).

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/hole10_build.py
    ... -- --out DIR    (write the .blend / overview / FBX into DIR instead of the repo: ALWAYS use this for experiments and staging)
    ... -- --out DIR --no-render   (skip the EEVEE overview still)

With no --out it writes blender/hole_10.blend, blender/previews/hole_10_overview.png and Unity/Assets/Resources/Course/hole_10.fbx (+ .meta
only when none exists). Deterministic: fixed seeds everywhere (random.Random(1010..) here, hole-number seeded libs), so two runs give the same
vertex counts and the same geometry hash (printed as [hole10_build] HASH).

SCORING CORE (unchanged since the flat build, same calls in the same order):
    terrain   rim ribbon + tee slab + green bulb, top at PLAY_Z (6 m above the lava). The lava ellipse (HAZARDS[0]) is cut out of
              it, so the bulb is a pillar: build_terrain(undercut_m=6) hangs undercut walls from every boundary loop, down to z = -6.
    lava      flat WATER_LAVA plane (replaced by the subdivided LK_LAVA mesh of postcard_look_lib.build_lava; still scores as water).
    gameplay  FLAG / HOLE_CUP / BALL_START / TEE_MARKER_1/2 / MARKER_TEE/PIN/UP exactly as before.

LOOK PASS (POSTCARD_LOOK continue, round 3 2026-10-04; order of the brief: scoring build -> look_materials -> snapshot_ground -> scenery ->
retarget_materials -> cliff skin -> lava -> assign_uvs LAST -> compare_ground -> audits -> render -> save -> export_look_fbx):
    near wall     the bowl: two terraced rows of tangent library wall segments (ROCK_WALL_BASALT_N1..N3, F2 / F3: hex-column segments with RAGGED tops, tilted and chipped, a smooth
                  ridge along the ring, uniform scale 0.58-1.7), 30 yd beyond the farthest shore point of each heading (never closer than 214 yd to the centre), pushed out round the stacks,
                  tops up to 58 m, low (13-18 m) in the headings the tee shot looks through so the volcano still shows (hole10_look.near_wall).
    far ring      the 295-355 yd ring of the brief (hole10_design wall_ring): two rows of the ragged F1 / F2 / F3 segments (scale up to 1.9), a macro skyline (ridges, saddles, 7 spires),
                  tops 18-74 m; replaces the 154 ROCK_WALL_FLAT / ROCK_WALL_BLUNT / CLIFF_ROCK icosahedra of the flat build (hole10_look.far_ring).
    crust         round 3: the cooled crust over the crater floor (ROCK_CRUST_nn, hole10_look.crust_field): a jittered hex lattice of 4.3 m plates (library hex-column primitive, tops
                  1.4-3.6 m above the lava, tilted / chipped, small basalt stumps on some), cut by winding lava rivers and a few pools, 24 yd off every play surface, 38 yd off the line of
                  play, 25 yd off the tee -> C chord and off every lava light, grouped in 52 m cells (>= 100 faces each). Replaces round 2's 56 floating plateaus.
    uv windows    round 3: every wall / stack / crust / skin face is mapped to ONE slice of the Basalt_C / Basalt_E tile (hole10_look.author_uv): ~20-40 % of the side faces take a slice that starts on a
                  glow line (the glow runs along the face edge = in the joint between two columns), the rest and every top take glow-free slices, the v density is low (long streaks).
    stacks        the 11 SCENERY stacks standing in the lava = library basalt pieces (ROCK_BASALT_E / F / C / A mains + 1-2 low satellites standing
                  in the lava), 6.5-12 m above the lava, lowered (uniform scale, floor MIN_SCALE) until no sight line from the tee / pads is cut
                  (the legacy clear_sightlines gate, re-expressed for the library pieces: H_SIGHTLINES_CLEAR; the crust is checked the same way).
    rubble        library basalt rocks at the cliff foot, kept off the lava carry (the legacy `carry` corridor, H_RUBBLE).
    skin          basalt columns on the rim loops and a tapered bowl on the pillar loop (build_cliff_skin(basalt), follow_undercut 1.0; round 3: columns 1.4-2.4 m wide pushed out only 5-40 cm, so they read
                  as clean prisms), in pieces of <= 15 m of shore (a short tail is joined into its neighbour: no rock under 60 welded vertices); the top of the wall is covered (CRATER_WALL_COVERED).
    lava          subdivided WATER_LAVA (LK_LAVA, static) + 5 LAVA_LIGHT_nn empties 2.3 m over the lava: 3 on the rim side 9 yd off the shore (the lava rim of the landmark shot), 2 round the pillar.
    plants        agave clumps (tee pad + rim), dark shrubs and tufts on the grass shelf (rim ribbon, tee slab, pillar collar) through PL.scatter
                  (land mask, 1.5 m clear of the markers, 6 m clear of the pin, off the play surfaces).
    backdrop      DRESS_CONE: the volcano behind the wall ring in the line of the tee shot with five winding LK_LAVA flows from the rim to the foot and a molten crater (hole10_look.build_cone),
                  + 3 DRESS_SMOKE_nn wisps (LK_SMOKE).
Everything new is ROCK_ / PLANT_ / DRESS_ / WATER_ / LAVA_ (no collision prefix); top surfaces of TERRAIN / FAIRWAY / GREEN / TEE_BOX / BUNKER
are bit-identical to the flat build (compare_ground, the A5 verifier and work/postcard-look/v2/hole10/tools/play_unchanged.py).
NOT built (on purpose): extra DRESS_SAND_* patches (crater.jpg has 4-5 bunkers; a visual-only sand patch on the fairway would read as a hazard that
is not one), a second green, any animated lava, bloom.
"""
import sys
import os
import math
import random
import hashlib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import postcard_lib as P  # noqa: E402
import postcard_look_lib as L  # noqa: E402
import postcard_props_lib as PL  # noqa: E402
import hole10_look as HL  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(args[args.index("--out") + 1]) if "--out" in args else None
RENDER = "--no-render" not in args

STACK_MAX_H, STACK_MIN_H = 12.0, 6.5       # m above the lava (brief: none above about 12 m)
MIN_SCALE = HL.MIN_SCALE                    # library instances never go below this x their jitter (>= 0.55): the no-stretch gate's 0.5 limit with margin for the FBX float round trip
OVERVIEW_RES = (1600, 1000)
SKIN_PIECE_M = 15.0                         # m of shore per ROCK_SKIN piece (LAVA_LIGHT rule: wall pieces beside a light are small meshes)
GATES = []
KINDS_VAR = {}                                # kind -> UV-phase variant kinds (filled by the build, read by make_stack)
VRND = random.Random(1050)                    # variant picks of the stacks (a separate stream: the stacks' own geometry stays exactly as before)


def gate(name, ok, detail):
    GATES.append((name, bool(ok), str(detail)))
    print(f"GATE: {name} {'PASS' if ok else 'FAIL'} - {detail}", flush=True)


# ----------------------------------------------------------------------------- scoring core helpers (unchanged from the flat build)
def dark_walls(D):
    """The terrain walls are banded MAT_ROUGH (grass lip) / MAT_CLIFF / MAT_CLIFF_DARK: swap the upper rock band to MAT_ROCK_DARK
    (retarget_materials(CRATER_OVERRIDES) then maps every one of them to LK_BASALT)."""
    me = D.terrain.data
    me.materials[1] = D.mats["MAT_ROCK_DARK"]
    me.materials[2] = D.mats["MAT_CLIFF_DARK"]


def top_z(ob):
    mw = ob.matrix_world
    return max((mw @ v.co).z for v in ob.data.vertices)


def footprint(ob):
    mw = ob.matrix_world
    ps = [mw @ v.co for v in ob.data.vertices]
    return (min(p.x for p in ps), min(p.y for p in ps), max(p.x for p in ps), max(p.y for p in ps))


# the wall / mesa / UV-variant helpers live in hole10_look.py (HL)

# ----------------------------------------------------------------------------- stacks in the lava (library basalt pieces)
# (kind, natural height above z = 0, natural footprint diameter): visible heights of the library meshes (z 0 = lava line)
STACK_KINDS = (("ROCK_BASALT_E", 12.6, 10.4), ("ROCK_BASALT_F", 8.8, 6.9), ("ROCK_BASALT_C", 10.2, 5.5), ("ROCK_BASALT_A", 5.0, 7.8))
SAT_KINDS = (("ROCK_BASALT_A", 5.0, 7.8), ("ROCK_BASALT_B", 3.6, 7.2), ("ROCK_BASALT_D", 1.7, 9.6))


def make_stack(D, s, top, rnd):
    """One stack = ONE main library basalt piece (kind chosen so that a uniform scale in [0.6, 1.6] gives `top` m above the lava and the
    design footprint 2 r) + 1-2 lower satellites standing in the lava beside it (their feet touch the main foot, never on top of it)."""
    x, y = P.m(s["x"], s["d"])
    rad = s["r"] * P.YD
    best = None
    for kind, nat_h, nat_w in STACK_KINDS:
        s_h, s_w = top / nat_h, 2 * rad / nat_w
        sc = math.sqrt(s_h * s_w)
        cost = abs(math.log(s_h / s_w)) + (3.0 if not 0.6 <= sc <= 1.6 else 0.0) + rnd.uniform(0, 0.15)
        if best is None or cost < best[0]:
            best = (cost, kind, nat_h, nat_w)
    _, kind, nat_h, nat_w = best
    yaw = rnd.uniform(0, math.tau)
    sc = min(1.8, max(MIN_SCALE, top / nat_h))
    main = PL.place(D, HL.pick_variant(KINDS_VAR, kind, VRND), (x, y, 0.0), yaw, (sc * rnd.uniform(0.95, 1.05), sc * rnd.uniform(0.95, 1.05), sc))
    obs = [main]
    n_sat = 2 if rad >= 6.0 * P.YD else 1
    a0 = rnd.uniform(0, math.tau)
    for j in range(n_sat):
        sk, sh, sw = SAT_KINDS[rnd.randrange(len(SAT_KINDS))]
        ss = rnd.uniform(0.66, 0.95)
        a = a0 + j * math.pi * rnd.uniform(0.8, 1.2)
        off = 0.5 * nat_w * sc + 0.32 * sw * ss
        obs.append(PL.place(D, HL.pick_variant(KINDS_VAR, sk, VRND), (x + off * math.cos(a), y + off * math.sin(a), 0.0), rnd.uniform(0, math.tau), (ss, ss, ss * rnd.uniform(0.9, 1.1))))
    return dict(obs=obs, main=main, nat_h=nat_h, top=top, scale0=sc, sat_scale0=[o.scale.z for o in obs[1:]])


def refit_stack(st, f):
    """Lower a whole stack: every piece scaled uniformly by f about its own origin (z 0 = lava line), floor 0.5."""
    for o in st["obs"]:
        sx, sy, sz = o.scale
        k = min(1.0, max(f, MIN_SCALE / min(sx, sy, sz)))
        o.scale = (sx * k, sy * k, sz * k)


def sightlines(D):
    """(eye, target) pairs a player can look along: ball eye (1.8 m) and camera height (4.5 m) on the tee, A, B, C, and the tee camera (5.5 m,
    24 m behind the tee), to dense ring samples of every later landing pad and of the green disc, plus the flag top. Metres above the lava."""
    pz = D.play_z
    st = [Vector((*P.m(*p), pz)) for p in D.CENTERLINE]                     # tee, A, B, C, pin
    ring = lambda c, r, n: [c + Vector((r * math.cos(a), r * math.sin(a), 0.5)) for a in np.linspace(0, math.tau, n, endpoint=False)]
    pad = lambda c: [c + Vector((0, 0, 0.5))] + ring(c, 3 * P.YD, 8) + ring(c, 6 * P.YD, 16)
    green = ([st[4] + Vector((0, 0, 0.7))] + ring(st[4], 4 * P.YD, 12) + ring(st[4], 9 * P.YD, 24) + ring(st[4], 15 * P.YD, 48)
             + [st[4] + Vector((0, 0, 9.5))])
    later = [pad(st[1]) + pad(st[2]) + pad(st[3]) + green, pad(st[2]) + pad(st[3]) + green, pad(st[3]) + green, green]
    first = (st[1] - st[0]).normalized()
    eyes = [(st[0] - first * 24 + Vector((0, 0, 5.5)), later[0])]
    for k, ts in enumerate(later):
        for h in (1.8, 4.5):
            eyes.append((st[k] + Vector((0, 0, h)), ts))
    return [(e, t) for e, ts in eyes for t in ts]


def stack_bvh(stacks_):
    V, T, who = [], [], []
    for i, st in enumerate(stacks_):
        for ob in st["obs"]:
            base = len(V)
            V += [tuple(ob.matrix_world @ v.co) for v in ob.data.vertices]
            for p in ob.data.polygons:
                T.append(tuple(base + k for k in p.vertices))
                who.append(i)
    return BVHTree.FromPolygons(V, T), who


def blocked_lines(D, stacks_):
    """Stack indices that cut a sight line (corridor = eye 0.8 m left / centre / right) and the number of cut lines."""
    bpy.context.view_layer.update()
    bvh, who = stack_bvh(stacks_)
    bad, ncut = set(), 0
    for eye0, tgt in sightlines(D):
        d0 = tgt - eye0
        side = Vector((-d0.y, d0.x, 0.0)).normalized() * 0.8
        cut = False
        for eye in (eye0 - side, eye0, eye0 + side):
            d = tgt - eye
            hit = bvh.ray_cast(eye, d.normalized(), d.length - 0.05)
            if hit[0] is not None:
                bad.add(who[hit[2]])
                cut = True
        ncut += cut
    return bad, ncut


def clear_sightlines(D, stacks_):
    """Lower any stack that cuts a sight line (8 percent per round, scale floor 0.5) until none does. Returns (rounds, remaining)."""
    for rnd_ in range(60):
        bad, ncut = blocked_lines(D, stacks_)
        if not bad:
            return rnd_, 0
        stuck = [i for i in bad if max(min(o.scale) for o in stacks_[i]["obs"]) <= MIN_SCALE + 1e-3]
        if len(stuck) == len(bad):
            return rnd_, ncut
        for i in bad:
            refit_stack(stacks_[i], 0.92)
    return -1, blocked_lines(D, stacks_)[1]


# ----------------------------------------------------------------------------- backdrop geometry choices
def tee_eye(D):
    return Vector((0.0, 0.0, D.play_z + P.Z_TEE + 2.2))


def lava_light_points(D):
    """5 LAVA_LIGHT empties (x, y, z m) 2.3 m over the lava: 3 along the rim shoulder between the tee shot's landing area and the neck end (the lava rim of the
    landmark shot), 2 round the pillar. Round 3: the rim lights sit 9 yd off the shore (found by a radial search on the lie mirror), so they light the cliff skin
    they are for and the crust field (which must stay 25 yd off every light, H_ROCK_CHUNKING) loses as little as possible."""
    pin = np.array(P.m(*D.hole.pin))
    cr = D.scenery["crater"]
    ccx, ccy = P.m(cr["cx"], cr["cd"])
    pts = []
    for ang_deg in (148.0, 128.0, 113.0):                                          # inner (crater) side of the rim ribbon, over the lava
        a = math.radians(ang_deg)
        rr = np.linspace(95.0, 175.0, 321)
        sd = P.signed_dist_m(D, ccx + rr * math.cos(a), ccy + rr * math.sin(a))      # > 0 outside the dry land
        k = int(np.argmin(np.abs(np.where(rr < 150.0, 1e3, sd - 9.0 * P.YD))))
        pts.append((ccx + float(rr[k]) * math.cos(a), ccy + float(rr[k]) * math.sin(a)))
    pts.append((pin[0] - 31.0, pin[1] - 4.0))                                      # west of the pillar, over the lava
    pts.append((pin[0] + 20.0, pin[1] - 27.0))                                     # north-east of the pillar (towards the crater centre)
    return pts


# ----------------------------------------------------------------------------- preview still
def frame_overview(D, res, margin=1.12):
    """Re-frame CAM_HOLE_OVERVIEW (same angle as the lib) on the land with a margin of lava, for a landscape still."""
    cam = bpy.data.objects["CAM_HOLE_OVERVIEW"]
    R = cam.rotation_euler.to_matrix()
    right, up, view = R @ Vector((1, 0, 0)), R @ Vector((0, 1, 0)), R @ Vector((0, 0, -1))
    pts = [Vector((*P.m(x, d), z)) for x, d in D.SHORE for z in (D.play_z + 2.0, -6.0)]
    rs, us = [p.dot(right) for p in pts], [p.dot(up) for p in pts]
    cr, cu = (min(rs) + max(rs)) / 2, (min(us) + max(us)) / 2
    cam.data.ortho_scale = max(max(rs) - min(rs), (max(us) - min(us)) * res[0] / res[1]) * margin
    cam.location = right * cr + up * cu - view * 1500.0


def geometry_hash():
    """sha256 over every exported MESH object: name, world matrix, polygon / vertex counts, the vertices of its mesh (rounded 1e-4), its material names and its UV0 loops (rounded 1e-4)."""
    h = hashlib.sha256()
    n_obj = n_v = n_f = 0
    for ob in sorted((o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_viewport and o.name in bpy.context.scene.objects),
                     key=lambda o: o.name):
        me = ob.data
        co = np.empty(len(me.vertices) * 3, np.float64)
        me.vertices.foreach_get("co", co)
        h.update(ob.name.encode())
        h.update(np.round(np.array(ob.matrix_world), 4).tobytes())
        h.update(np.round(co, 4).tobytes())
        h.update(str((len(me.vertices), len(me.polygons))).encode())
        h.update("|".join(m.name if m else "" for m in me.materials).encode())
        if len(me.uv_layers):                                                    # round 3: the authored UV windows are part of the look, so they are part of the hash
            uv = np.empty(len(me.loops) * 2, np.float64)
            me.uv_layers[0].data.foreach_get("uv", uv)
            h.update(np.round(uv, 4).tobytes())
        n_obj += 1
        n_v += len(me.vertices)
        n_f += len(me.polygons)
    return h.hexdigest(), n_obj, n_v, n_f


# ============================================================================= the build
D = P.start("hole10_design", out_dir=OUT)
SC = D.scenery
D.mod.SCENERY["tee_box_m"] = (SC["tee_box"]["width"] * P.YD, SC["tee_box"]["depth"] * P.YD)   # the lib reads metres; the design says yards

# ---- 1. scoring core (identical calls to the flat build)
P.build_terrain(D, undercut_m=6.0)
dark_walls(D)
P.build_play_surfaces(D)
P.build_water(D, "WATER_LAVA", "MAT_LAVA", shallow_material=None, foam_material=None, crest=False)
P.build_gameplay(D)

# ---- 2. look materials + the proof that the play surfaces do not move
L.look_materials(D)
snap = L.snapshot_ground(D)

# ---- 3. scenery: library basalt only (no icosahedron anywhere; the legacy ROCK_WALL_FLAT/BLUNT/CLIFF/ROCK instances are never created)
HL.register_kinds()
wall_kinds = ["ROCK_WALL_BASALT_" + k for k in ("N1", "N2", "N3", "F1", "F2", "F3")]
kinds_var = HL.uv_variants(wall_kinds, random.Random(1030), p_glow=0.20)
KINDS_VAR.update(HL.uv_variants(["ROCK_BASALT_" + k for k in "ABCDEF"], random.Random(1031), p_glow=0.30))      # the stacks' library kinds too
near, near_th, near_R = HL.near_wall(D, SC["wall_ring"], kinds_var)
ring = HL.far_ring(D, SC["wall_ring"], kinds_var)
rnd_st = random.Random(1011)
hs = [s["h"] for s in SC["stacks"]]
stacks = [make_stack(D, s, STACK_MIN_H + (s["h"] - min(hs)) / (max(hs) - min(hs)) * (STACK_MAX_H - STACK_MIN_H), rnd_st) for s in SC["stacks"]]
lights_xy = [(x, y) for x, y in lava_light_points(D)]
stacks_xy = [(*P.m(s_["x"], s_["d"]), s_["r"] * P.YD + 9.0) for s_ in SC["stacks"]]
crust, crust_kept, crust_planned = HL.crust_field(D, SC["wall_ring"], None, near_th, near_R, stacks_xy, lights_xy, random.Random(1062))
mesas = [dict(obs=[o], kind="crust") for o in crust]                     # pseudo-stacks: the sight-line gate treats the crust like the stacks
rounds, sight_left = clear_sightlines(D, stacks + mesas)
c_st, pin_st = P.m(*D.CENTERLINE[-2]), P.m(*D.CENTERLINE[-1])        # keep the lava carry itself free of rubble
carry = [(c_st[0] + (pin_st[0] - c_st[0]) * k / 14.0, c_st[1] + (pin_st[1] - c_st[1]) * k / 14.0, 24.0) for k in range(15)]
stack_foot = [(o.location.x, o.location.y, 0.45 * max(PL.lib_bbox(o.data.name)[1].x - PL.lib_bbox(o.data.name)[0].x, 1.0) * o.scale.x + 3.0)
              for st in stacks for o in st["obs"]]
foot = PL.scatter_rocks(D, 30, zone="foot", seed=4, variant="BASALT", avoid=carry + stack_foot,
                        region=PL.region_band(D, 1.8, 7.0, "sea"))

# plants on the grass shelf: agave clumps (the crater.jpg spiky clusters round the tee pad and along the rim), dark shrubs, tufts. Land-masked,
# 1.5 m off the markers, 6 m off the pin, never on a play surface (PL.scatter safe masks). Big things first (later calls keep their distance).
tee_agave = PL.scatter(D, {"PLANT_AGAVE_B": 3, "PLANT_AGAVE_A": 1}, 14, region=PL.region_disc(0.0, 0.0, 19.0), seed=12, scale_range=(1.5, 2.0), min_gap=3.0)
agave = tee_agave + PL.scatter(D, {"PLANT_AGAVE_B": 3, "PLANT_AGAVE_A": 1}, 22, region=PL.region_band(D, 0.5, 5.0), seed=13, scale_range=(1.4, 2.0), min_gap=6.0)
shrubs = PL.scatter(D, ["PLANT_SHRUB_A", "PLANT_SHRUB_B"], 14, region=PL.region_band(D, 0.8, 6.0), seed=14, scale_range=(1.1, 1.6), min_gap=6.0)
tufts = PL.scatter(D, {"PLANT_TUFT_A": 3, "PLANT_TUFT_B": 2}, 170, region=PL.region_band(D, 0.3, 7.0), seed=15, scale_range=(1.0, 1.5))

# background volcano + smoke wisps (visual only, built after the lava: see 5.)
CONE_C = (float(args[args.index("--cone") + 1].split(",")[0]), float(args[args.index("--cone") + 1].split(",")[1])) if "--cone" in args else (170.0, 440.0)
cone = HL.build_cone(D, (CONE_C[0], CONE_C[1], -8.0), base_r=125.0, height=135.0, seed=1, notch_deg=250.0)

# ---- 4. retarget the flat materials, cladding, lava
L.retarget_materials(D, overrides=L.CRATER_OVERRIDES)         # MAT_CLIFF / MAT_CLIFF_DARK / MAT_ROCK_DARK -> LK_BASALT (grass lip band too, see skin)
loops = L.terrain_top_loops(D)
pin = P.m(*D.hole.pin)
pillar = [i for i, (Pl, _) in enumerate(loops) if P.point_in_poly(pin, [tuple(p) for p in Pl])]
rim = [i for i in range(len(loops)) if i not in pillar]
skins = L.build_cliff_skin(D, style="basalt", loops=rim, follow_undercut=0.0, piece_m=SKIN_PIECE_M, disp_m=(0.05, 0.4), basalt_width_m=(1.4, 2.4))
skins += L.build_cliff_skin(D, style="basalt", loops=pillar, follow_undercut=1.0, seed=1, piece_m=SKIN_PIECE_M, disp_m=(0.05, 0.4), basalt_width_m=(1.4, 2.4))
def merge_tiny_skins(objs, min_verts=70):
    """A cladding piece with fewer than `min_verts` welded vertices (the short tail of a loop) is joined into its nearest neighbour piece: no rock under 60 welded vertices
    (the brief), and no hole in the cladding."""
    objs = list(objs)
    tiny = [o for o in objs if PL.welded_vertex_count(o.data) < min_verts]
    for t in tiny:
        rest = [o for o in objs if o is not t and o not in tiny]
        c = np.array(t.matrix_world.translation) + np.mean([np.array(v.co) for v in t.data.vertices], axis=0)
        tgt = min(rest, key=lambda o: float(np.linalg.norm(np.mean([np.array(v.co) for v in o.data.vertices], axis=0) - c)))
        bpy.ops.object.select_all(action='DESELECT')
        t.select_set(True)
        tgt.select_set(True)
        bpy.context.view_layer.objects.active = tgt
        bpy.ops.object.join()
        objs.remove(t)
    return objs, len(tiny)


skins, n_tiny = merge_tiny_skins(skins)
rnd_skin = random.Random(1070)
for sk_ in skins:                                              # glow in the joints, not a continuous dash lattice (the lib box UV)
    HL.UV_STATS[sk_.name] = HL.author_uv(sk_.data, rnd_skin, uf=0.78, vf=0.55, p_glow=0.26)
lava = L.build_lava(D, lights=5, light_points=[(x, y, 2.3) for x, y in lava_light_points(D)])
L.assign_uvs(D)                                                # LAST

# ---- 5. smoke wisps (their own meshes, LK_SMOKE), 3 cards: two behind the wall window of the tee shot (they rise over the wall, bottoms low so the
#         phone tee frame, which only reaches 8 deg above the horizon, shows their lower wisps) and one over the east wall ring (approach side)
smoke = []
smoke += PL.build_smoke_cards(D, [((38.0, 392.0, 20.0), 120.0, 140.0)], seed=1, face=(0.0, 0.0))
smoke += PL.build_smoke_cards(D, [((226.0, 372.0, 26.0), 135.0, 160.0)], seed=2, face=(0.0, 0.0))
smoke += PL.build_smoke_cards(D, [((560.0, 150.0, 34.0), 150.0, 170.0)], seed=7, face=(107.0, 146.0))

# ---- 6. cameras, light, previews
P.build_cameras_and_light(D)
frame_overview(D, OVERVIEW_RES)
bpy.context.preferences.filepaths.save_version = 0       # no hole_10.blend1 next to the scene
bpy.context.view_layer.update()

# ---- 7. gates of the build itself
ok, detail = L.compare_ground(D, snap)
gate("H_LOOK_TOP_SURFACES_UNCHANGED", ok, detail)
for name, ok, detail in L.audit_look(D):
    gate("LIB_" + name, ok, detail)
for name, ok, detail in L.v2_gates(D, pockets=None):
    gate("LIB_" + name, ok, detail)

# ---- 7b. gates that need the postcard_lib handle (lie mirror, ground ray cast)
plants = [o for o in bpy.data.objects if o.name.startswith("PLANT_") and o.type == 'MESH' and "ASSET_LIBRARY" not in [c.name for c in o.users_collection]]
px_ = np.array([o.matrix_world.translation.x for o in plants])
py_ = np.array([o.matrix_world.translation.y for o in plants])
pz_ = np.array([o.matrix_world.translation.z for o in plants])
water_ = P.lie_codes_m(D, px_, py_) == P.LIE_WATER
sd_ = P.signed_dist_m(D, px_, py_)
gz_ = PL.ground_sampler(D)(px_, py_)
dz_ = np.abs(pz_ - gz_)
gate("H_NO_PLANT_ON_WATER", len(plants) > 0 and not water_.any() and float(sd_.max()) <= -0.999 and float(np.nanmax(dz_)) <= 0.05 and float(pz_.min()) >= D.play_z - 0.2,
     f"{len(plants)} PLANT_ objects: on water (lie mirror) {int(water_.sum())}, nearest to a shore / lava edge {-float(sd_.max()):.2f} m (>= 1.0), base vs the ray-cast collider top max |dz| "
     f"{float(np.nanmax(dz_)):.3f} m (<= 0.05), lowest base z {float(pz_.min()):.2f} m (play {D.play_z})")
pin_xy = np.array(P.m(*D.hole.pin))
mk = [np.array(o.matrix_world.translation)[:2] for o in bpy.data.objects if o.name in ("TEE_MARKER_1", "TEE_MARKER_2", "MARKER_TEE", "BALL_START", "HOLE_CUP", "MARKER_PIN", "FLAG_POLE")]
d_pin = float(np.hypot(px_ - pin_xy[0], py_ - pin_xy[1]).min())
d_mk = min(float(np.hypot(px_ - m_[0], py_ - m_[1]).min()) for m_ in mk)
gate("H_PLANTS_CLEAR_OF_PIN_AND_TEE", d_pin >= 6.0 and d_mk >= 1.5,
     f"nearest plant to the pin {d_pin:.1f} m (>= 6; brief >= 1.5), nearest to any of {len(mk)} tee / pin / cup / ball markers {d_mk:.2f} m (>= 1.5)")
bad_s, ncut = blocked_lines(D, stacks + mesas)
gate("H_SIGHTLINES_CLEAR", not bad_s and ncut == 0,
     f"legacy clear_sightlines gate re-expressed for the library stacks: {len(sightlines(D))} sight lines (ball eye 1.8 m / camera 4.5 m on the tee, A, B, C and the tee camera to every later pad and the green) cut by {ncut}; rounds used {rounds}")
tuft_n = sum(1 for o in plants if "TUFT" in o.name)
gate("H_SHELF_PLANTS", len(plants) >= 10 and tuft_n >= 40,
     f"{len(plants)} plants on the grass shelf: {len(agave)} agave, {len(shrubs)} shrubs, {len(tufts)} tufts (all land-masked PL.scatter, one shared LK_PLANTS material, instanced)")

def world_xy(obs):
    out = []
    for o in obs:
        mw = np.array(o.matrix_world)
        co = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        out.append(co @ mw[:3, :3].T + mw[:3, 3])
    return np.vstack(out)


nw = world_xy(near)
sd_near = P.signed_dist_m(D, nw[:, 0], nw[:, 1])
cxm, cym = P.m(SC["wall_ring"]["cx"], SC["wall_ring"]["cd"])
r_near = np.hypot(nw[:, 0] - cxm, nw[:, 1] - cym)
near_tops = [top_z(o) for o in near]
gate("H_NEAR_WALL", len(near) >= 60 and float(sd_near.min()) >= 14.0 * P.YD and float(r_near.min()) >= 190.0 * P.YD and 12.0 <= min(near_tops) and max(near_tops) <= 60.0,
     f"{len(near)} near-wall library segments (ROCK_WALL_BASALT_N*/F*), nearest vertex {float(sd_near.min()) / P.YD:.1f} yd from any play surface / shore (>= 14), "
     f"{float(r_near.min()) / P.YD:.0f}..{float(r_near.max()) / P.YD:.0f} yd from the crater centre, tops {min(near_tops):.1f}..{max(near_tops):.1f} m above the lava (12..60)")
if crust:
    mv = world_xy(crust)
    sd_mesa = P.signed_dist_m(D, mv[:, 0], mv[:, 1])
    clx = [P.m(*p) for p in D.CENTERLINE]
    d_line = min(float(HL.seg_dist(mv[:, 0], mv[:, 1], *clx[i], *clx[i + 1]).min()) for i in range(len(clx) - 1))
    d_chord = float(HL.seg_dist(mv[:, 0], mv[:, 1], *clx[0], *clx[3]).min())
    d_light = min(float(np.hypot(mv[:, 0] - lx, mv[:, 1] - ly).min()) for lx, ly in lights_xy)
    crust_tops = [top_z(o) for o in crust]
    n_faces = sum(len(o.data.polygons) for o in crust)
    gate("H_CRUST", len(crust) >= 20 and crust_kept >= 500 and float(sd_mesa.min()) >= 24.0 * P.YD and d_line >= 38.0 * P.YD and d_chord >= 25.0 * P.YD
         and max(crust_tops) <= HL.CRUST_TOP_MAX and d_light >= 25.0 * P.YD,
         f"{len(crust)} crust chunks (ROCK_CRUST_nn, {crust_kept} of {crust_planned} planned hex plates {HL.CRUST_COL_R:.1f} m, {n_faces} faces): nearest vertex {float(sd_mesa.min()) / P.YD:.1f} yd from any play surface (>= 24), "
         f"{d_line / P.YD:.1f} yd from the line of play (>= 38), {d_chord / P.YD:.1f} yd from the tee -> C chord (>= 25), {d_light / P.YD:.1f} yd from the nearest lava light (>= 25), "
         f"highest top {max(crust_tops):.2f} m above the lava (<= {HL.CRUST_TOP_MAX:.1f}, below every sight line from z >= {D.play_z:.0f})")
else:
    gate("H_CRUST", False, "no crust placed")
uvs = HL.UV_STATS
side_n = sum(v["side"] for v in uvs.values())
glow_n = sum(v["glow"] for v in uvs.values())
top_n = sum(v["top"] for v in uvs.values())
top_free = sum(v["top_glow_free"] for v in uvs.values())
TX = HL.texture_measure()                      # the window constants of hole10_look re-measured from the Basalt_E / Basalt_C PNGs on disk (stale constants = a failed gate, not a quiet drift)
tex_ok = TX["zone_glow_max"] <= 2e-4 and TX["edge_glow_min"] >= 0.04 and TX["profile_dev"] <= 0.01
gate("H_UV_WINDOWS", len(uvs) >= 60 and top_n == top_free and 0.15 <= glow_n / max(side_n, 1) <= 0.45 and tex_ok,
     f"{len(uvs)} UV-window meshes (wall / stack variants, crust chunks, skin pieces): {side_n} side faces, {glow_n} of them ({glow_n / max(side_n, 1):.0%}) carry a Basalt_E glow line on their edge (target 15-45 %), "
     f"{top_n} top faces all take glow-free slices ({top_free}); window constants vs the PNGs on disk: glow share inside the {len(HL.ZONES)} glow-free zones max {TX['zone_glow_max']:.4%} (<= 0.02 %), "
     f"narrowest edge window at each of the {len(HL.GLOW_U)} glow lines holds {TX['edge_glow_min']:.1%} glow (>= 4 %), Basalt_C luminance profile deviation {TX['profile_dev']:.4f} (<= 0.01), glow texels {TX['glow_mean']:.2%} of the tile; "
     f"the texture-sampled glow measures at the authored UVs are in the stage gates (H_GLOW_JOINTS)")

st = P.stats(D)
tops = [top_z(o) for o in ring]
stops = [max(top_z(o) for o in s["obs"]) for s in stacks]
print(f"[hole10_build] near wall {len(near)} segments, far ring {len(ring)} segments (tops {min(tops):.1f}..{max(tops):.1f} m above the lava), {len(crust)} crust chunks; {len(stacks)} stacks "
      f"({', '.join('%.1f' % t for t in stops)} m measured, sightline rounds {rounds}, lines still cut {sight_left}); foot rubble {len(foot)}; "
      f"plants {len(agave)} agave {len(shrubs)} shrubs {len(tufts)} tufts; skin pieces {len(skins)} ({n_tiny} short tail pieces joined into a neighbour); smoke {len(smoke)}; objects {st['objects']} tris {st['tris']}")
G_HASH, G_OBJ, G_V, G_F = geometry_hash()
print(f"[hole10_build] HASH {G_HASH} objects {G_OBJ} verts {G_V} faces {G_F}")

if RENDER:
    for nm_ in ("BALL_START", "HOLE_CUP", "MARKER_TEE", "MARKER_PIN", "MARKER_UP"):   # Unity hides these placeholders: hide them in the preview too
        if bpy.data.objects.get(nm_) is not None:
            bpy.data.objects[nm_].hide_render = True
    P.render_overview(D, res=OVERVIEW_RES)
    for nm_ in ("BALL_START", "HOLE_CUP", "MARKER_TEE", "MARKER_PIN", "MARKER_UP"):
        if bpy.data.objects.get(nm_) is not None:
            bpy.data.objects[nm_].hide_render = False
# save like P.save but WITHOUT relative_remap: the LK_* image paths stay the absolute Unity/Assets/Resources/Course/Look/*.png paths they were loaded
# with, so the .blend works from the staging folder AND after it is copied to blender/hole_10.blend (relative paths remapped against the staging folder
# would break on the copy)
_blend = P._blend_path(D)
P._guard_target(D, _blend)
os.makedirs(os.path.dirname(_blend), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=_blend, relative_remap=False)
L.export_look_fbx(D)
fails = [n for n, ok, _ in GATES if not ok]
print(f"[hole10_build] done: {len(GATES)} build gates, {len(fails)} failed {fails}")
