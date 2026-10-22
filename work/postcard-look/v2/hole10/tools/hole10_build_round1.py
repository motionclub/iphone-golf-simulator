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

LOOK PASS (POSTCARD_LOOK continue, 2026-10-04; order of the brief: scoring build -> look_materials -> snapshot_ground -> scenery ->
retarget_materials -> cliff skin -> lava -> assign_uvs LAST -> compare_ground -> audits -> render -> save -> export_look_fbx):
    wall ring     the far crater wall = ring of postcard_props_lib basalt TOWERS (ROCK_WALL_BASALT_S/M/L) and wall SEGMENTS (_A/_B/_C, hex-prism
                  column clusters), uniform scale 0.58-1.6 x a +-5 % per-axis jitter (never stretched, never near the 0.5 limit: a scale AT the limit reads 0.4999 after the FBX float round trip),
                  three staggered rows 295-355 yd from the crater centre, the inner row terraced low (16-30 m above the lava), the outer row tall
                  (40-56 m), 9 % gaps, and a low "window" (15-23 m) in the headings the tee shot looks through so the volcano shows above it.
                  Replaces the 154 ROCK_WALL_FLAT / ROCK_WALL_BLUNT / CLIFF_ROCK icosahedra of the flat build (none is ever created now).
    stacks        the 11 SCENERY stacks standing in the lava = library basalt pieces (ROCK_BASALT_E / F / C / A mains + 1-2 low satellites standing
                  in the lava), 6.5-12 m above the lava, lowered (uniform scale, floor MIN_SCALE) until no sight line from the tee / pads is cut
                  (the legacy clear_sightlines gate, re-expressed for the library pieces: H_SIGHTLINES_CLEAR).
    rubble        library basalt rocks at the cliff foot, kept off the lava carry (the legacy `carry` corridor, H_RUBBLE).
    skin          basalt columns on the rim loops and a tapered bowl on the pillar loop (build_cliff_skin(basalt), follow_undercut 1.0), in
                  pieces of <= 15 m of shore so every wall piece near a LAVA_LIGHT is a small mesh (widest 24 yd allowed) (GolfLook: a renderer only gets the
                  lights nearest its bounds); the top of the wall is covered (CRATER_WALL_COVERED).
    lava          subdivided WATER_LAVA (LK_LAVA, static) + 5 LAVA_LIGHT_nn empties 2.3 m over the lava: 3 along the rim shoulder between the
                  drive and the neck end (the lava rim of the landmark shot), 2 round the pillar.
    plants        agave clumps (tee pad + rim), dark shrubs and tufts on the grass shelf (rim ribbon, tee slab, pillar collar) through PL.scatter
                  (land mask, 1.5 m clear of the markers, 6 m clear of the pin, off the play surfaces).
    backdrop      DRESS_CONE (volcano with glowing joints, LK_BASALT) behind the wall ring in the line of the tee shot + 3 DRESS_SMOKE_nn wisps (LK_SMOKE).
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

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(args[args.index("--out") + 1]) if "--out" in args else None
RENDER = "--no-render" not in args

STACK_MAX_H, STACK_MIN_H = 12.0, 6.5       # m above the lava (brief: none above about 12 m)
MIN_SCALE = 0.58                            # library instances never go below this x their jitter (>= 0.55): the no-stretch gate's 0.5 limit with margin for the FBX float round trip
OVERVIEW_RES = (1600, 1000)
SKIN_PIECE_M = 15.0                         # m of shore per ROCK_SKIN piece (LAVA_LIGHT rule: wall pieces beside a light are small meshes)
GATES = []


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


# ----------------------------------------------------------------------------- far crater wall (library towers + wall segments)
TOWER_NAT = {"ROCK_WALL_BASALT_S": (20.4, 14.2), "ROCK_WALL_BASALT_M": (32.5, 20.6), "ROCK_WALL_BASALT_L": (48.5, 31.0)}     # (m above z = 0, plan width) at scale 1
SEG_NAT = {"ROCK_WALL_BASALT_A": (42.9, 41.5), "ROCK_WALL_BASALT_B": (36.9, 37.7), "ROCK_WALL_BASALT_C": (29.5, 31.1)}       # long wall segments (front = -Y)
# row: (t between r_inner and r_outer, height range above the lava (m), share of wall SEGMENTS, share of towers S / M / L): the inner row is low
# and terraced, the outer row tall, so the far wall rises like a stepped crater wall instead of one level fence.
TEE_XY = (0.0, 0.0)
WINDOW = (-10.0, 40.0)            # headings from the tee (deg from +D toward +X) where the far wall is kept low ...
WINDOW_H = (15.0, 23.0)           # ... (m above the lava) so the background volcano and its smoke show above it in the phone tee frame (its top edge is 8 deg above the horizon)
RING_ROWS = ((0.0, (16.0, 30.0), 0.45, (0.5, 0.5, 0.0)), (0.5, (28.0, 44.0), 0.15, (0.2, 0.55, 0.25)), (1.0, (40.0, 56.0), 0.0, (0.0, 0.35, 0.65)))


def wall_ring(D, W):
    """Three staggered rows of library basalt TOWERS (ROCK_WALL_BASALT_S/M/L) and wall SEGMENTS (_A/_B/_C, tangent, face inward) between r_inner
    and r_outer round the crater centre, rising outward (inner row 16-30 m above the lava, middle 28-44, outer 40-56). Pieces are laid along
    each row by arc length with random widths and about 9 % gaps, so the skyline is irregular. Every scale is UNIFORM (x a few % jitter) inside
    [0.55, 1.7]: nothing is stretched. The lava plane cuts every piece at z = 0; the 6 m x scale under it is buried."""
    rnd = random.Random(1010)
    cx, cy = P.m(W["cx"], W["cd"])
    r0, r1 = W["r_inner"] * P.YD, W["r_outer"] * P.YD
    out = []
    for k, (t, (hlo, hhi), seg_share, mix) in enumerate(RING_ROWS):
        r = r0 + (r1 - r0) * t
        th = rnd.uniform(0.0, 0.2) + k * 0.07
        th_end = th + 2 * math.pi
        while th < th_end:
            rr = r + rnd.uniform(-6.0, 6.0)
            h = rnd.uniform(hlo, hhi)
            hd = math.degrees(math.atan2(cx + rr * math.cos(th + 0.5 * 34.0 / rr) - TEE_XY[0], cy + rr * math.sin(th + 0.5 * 34.0 / rr) - TEE_XY[1]))
            if WINDOW[0] <= hd <= WINDOW[1]:                                # the window in the wall the tee shot looks through (volcano + smoke behind it)
                h = min(h, rnd.uniform(WINDOW_H[0], WINDOW_H[1]))
            in_window = WINDOW[0] <= hd <= WINDOW[1]
            if rnd.random() < seg_share:
                kind = "ROCK_WALL_BASALT_C" if in_window else list(SEG_NAT)[rnd.randrange(3)]
                nat_h, nat_w = SEG_NAT[kind]
                s = min(0.95, max(MIN_SCALE, h / nat_h))
                yaw = th - math.pi / 2 + rnd.uniform(-0.08, 0.08)           # local -Y (the stepped front) faces the crater centre
                sc3 = (s * rnd.uniform(0.96, 1.04), s * rnd.uniform(0.96, 1.04), s)
                width = nat_w * s
            else:
                u = rnd.random() * sum(mix)
                kind = "ROCK_WALL_BASALT_S" if u < mix[0] else ("ROCK_WALL_BASALT_M" if u < mix[0] + mix[1] else "ROCK_WALL_BASALT_L")
                if in_window and kind == "ROCK_WALL_BASALT_L":
                    kind = "ROCK_WALL_BASALT_M"                                 # an L tower cannot go below 28 m at the 0.58 scale floor
                nat_h, nat_w = TOWER_NAT[kind]
                s = min(1.6, max(MIN_SCALE, h / nat_h))
                yaw = rnd.uniform(0, math.tau)
                sc3 = (s * rnd.uniform(0.95, 1.05), s * rnd.uniform(0.95, 1.05), s)
                width = nat_w * s
            dth = width * 0.95 / rr
            if rnd.random() < 0.09:                                       # a gap: the row behind shows through
                th += dth
                continue
            tc = th + 0.5 * dth
            out.append(PL.place(D, kind, (cx + rr * math.cos(tc), cy + rr * math.sin(tc), 0.0), yaw=yaw, scale=sc3))
            th += dth
    return out


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
    main = PL.place(D, kind, (x, y, 0.0), yaw, (sc * rnd.uniform(0.95, 1.05), sc * rnd.uniform(0.95, 1.05), sc))
    obs = [main]
    n_sat = 2 if rad >= 6.0 * P.YD else 1
    a0 = rnd.uniform(0, math.tau)
    for j in range(n_sat):
        sk, sh, sw = SAT_KINDS[rnd.randrange(len(SAT_KINDS))]
        ss = rnd.uniform(0.66, 0.95)
        a = a0 + j * math.pi * rnd.uniform(0.8, 1.2)
        off = 0.5 * nat_w * sc + 0.32 * sw * ss
        obs.append(PL.place(D, sk, (x + off * math.cos(a), y + off * math.sin(a), 0.0), rnd.uniform(0, math.tau), (ss, ss, ss * rnd.uniform(0.9, 1.1))))
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
    """5 LAVA_LIGHT empties (x, y, z m) 2.2-2.4 m over the lava: 3 along the rim shoulder between the tee shot's landing area and the neck end
    (the lava rim of the landmark shot), 2 round the pillar."""
    pin = np.array(P.m(*D.hole.pin))
    cr = D.scenery["crater"]
    ccx, ccy = P.m(cr["cx"], cr["cd"])
    pts = []
    for ang_deg, rad in ((148.0, 130.0), (128.0, 126.0), (113.0, 118.0)):          # inner (crater) side of the rim ribbon, over the lava
        a = math.radians(ang_deg)
        pts.append((ccx + rad * math.cos(a), ccy + rad * math.sin(a)))
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
    """sha256 over every exported MESH object: name, world matrix, polygon / vertex counts and the vertices of its mesh (rounded 1e-4)."""
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
ring = wall_ring(D, SC["wall_ring"])
rnd_st = random.Random(1011)
hs = [s["h"] for s in SC["stacks"]]
stacks = [make_stack(D, s, STACK_MIN_H + (s["h"] - min(hs)) / (max(hs) - min(hs)) * (STACK_MAX_H - STACK_MIN_H), rnd_st) for s in SC["stacks"]]
rounds, sight_left = clear_sightlines(D, stacks)
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
tufts = PL.scatter(D, {"PLANT_TUFT_A": 3, "PLANT_TUFT_B": 2}, 300, region=PL.region_band(D, 0.3, 7.0), seed=15, scale_range=(1.0, 1.5))

# background volcano + smoke wisps (visual only, built after the lava: see 5.)
CONE_C = (float(args[args.index("--cone") + 1].split(",")[0]), float(args[args.index("--cone") + 1].split(",")[1])) if "--cone" in args else (170.0, 440.0)
cone = PL.build_background_cone(D, (CONE_C[0], CONE_C[1], -8.0), base_r=125.0, height=135.0, seed=1, notch_deg=250.0)

# ---- 4. retarget the flat materials, cladding, lava
L.retarget_materials(D, overrides=L.CRATER_OVERRIDES)         # MAT_CLIFF / MAT_CLIFF_DARK / MAT_ROCK_DARK -> LK_BASALT (grass lip band too, see skin)
loops = L.terrain_top_loops(D)
pin = P.m(*D.hole.pin)
pillar = [i for i, (Pl, _) in enumerate(loops) if P.point_in_poly(pin, [tuple(p) for p in Pl])]
rim = [i for i in range(len(loops)) if i not in pillar]
skins = L.build_cliff_skin(D, style="basalt", loops=rim, follow_undercut=0.0, piece_m=SKIN_PIECE_M)
skins += L.build_cliff_skin(D, style="basalt", loops=pillar, follow_undercut=1.0, seed=1, piece_m=SKIN_PIECE_M)
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
bad_s, ncut = blocked_lines(D, stacks)
gate("H_SIGHTLINES_CLEAR", not bad_s and ncut == 0,
     f"legacy clear_sightlines gate re-expressed for the library stacks: {len(sightlines(D))} sight lines (ball eye 1.8 m / camera 4.5 m on the tee, A, B, C and the tee camera to every later pad and the green) cut by {ncut}; rounds used {rounds}")
tuft_n = sum(1 for o in plants if "TUFT" in o.name)
gate("H_SHELF_PLANTS", len(plants) >= 10 and tuft_n >= 40,
     f"{len(plants)} plants on the grass shelf: {len(agave)} agave, {len(shrubs)} shrubs, {len(tufts)} tufts (all land-masked PL.scatter, one shared LK_PLANTS material, instanced)")

st = P.stats(D)
tops = [top_z(o) for o in ring]
stops = [max(top_z(o) for o in s["obs"]) for s in stacks]
print(f"[hole10_build] wall ring {len(ring)} library towers, tops {min(tops):.1f}..{max(tops):.1f} m above the lava; {len(stacks)} stacks "
      f"({', '.join('%.1f' % t for t in stops)} m measured, sightline rounds {rounds}, lines still cut {sight_left}); foot rubble {len(foot)}; "
      f"plants {len(agave)} agave {len(shrubs)} shrubs {len(tufts)} tufts; skin pieces {len(skins)}; smoke {len(smoke)}; objects {st['objects']} tris {st['tris']}")
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
