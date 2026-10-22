"""Hole 10 CRATER: scene build (a rim ribbon and a pillar-green standing in a lava crater, one flat play height).

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/hole10_build.py
    ... -- --out DIR    (optional: write the .blend / overview / FBX into DIR instead of the repo, for experiments)

Writes blender/hole_10.blend, blender/previews/hole_10_overview.png and Unity/Assets/Resources/Course/hole_10.fbx (+ .meta).
A short sequence of postcard_lib calls plus this hole's scenery, which reads the SCENERY dict of hole10_design.py:

    terrain   rim ribbon + tee slab + green bulb, top at PLAY_Z (6 m above the lava). The lava ellipse (HAZARDS[0]) is cut out of
              it, so the bulb is a pillar: build_terrain(undercut_m=6) hangs undercut walls from every boundary loop, down to z = -6
              (below the lava, so the column goes all the way into it). Walls are dark basalt (MAT_ROCK_DARK / MAT_CLIFF_DARK).
    lava      ONE plane at z = 0 named WATER_LAVA, MAT_LAVA (orange, static). It scores as water: outside the shore, or in the ellipse.
    wall_ring the far crater wall: three staggered rows of tall flat-topped basalt columns (30-52 m above the lava) round the crater centre.
    stacks    the 11 basalt stacks standing in the lava (SCENERY['stacks']), 6.5-12 m above the lava, lowered where they would hide
              the next landing pad or the green from a ball-eye / tee-camera view (see clear_sightlines).
    boulders  rubble at the foot of the cliffs and the pillar (library rocks half sunk in the lava), kept off the lava carry.
Every rock is an instance of one of six hidden meshes in ASSET_LIBRARY: the four library rocks of hole 7 and two copies of CLIFF_ROCK whose
top spike is pulled flat (ROCK_WALL_FLAT) or blunt (ROCK_WALL_BLUNT); all of them use MAT_ROCK_DARK / MAT_CLIFF_DARK only.
"""
import sys
import os
import math
import random

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import postcard_lib as P  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(args[args.index("--out") + 1]) if "--out" in args else None

STACK_MAX_H, STACK_MIN_H = 12.0, 6.5       # m above the lava (brief: none above about 12 m)
STACK_FLOOR_H = 3.5                         # never lowered below this for sightlines
OVERVIEW_RES = (1600, 1000)


# ----------------------------------------------------------------------------- rocks
def rock_variant(D, src_key, key, pole_k):
    """A COPY of a library rock mesh whose top pole is pulled down towards the upper ring (pole_k = 0: onto it, a flat pentagon top, a
    basalt column when the instance is stretched tall; 1 = the original spike). Hidden in ASSET_LIBRARY like the originals."""
    me = D.rock_lib[src_key].data.copy()
    me.name = key
    zmax = max(v.co.z for v in me.vertices)
    ring = [v.co.z for v in me.vertices if 0.0 < v.co.z < 0.8 * zmax]
    ring_z = sum(ring) / len(ring)
    for v in me.vertices:
        if v.co.z > 0.8 * zmax:
            v.co.z = ring_z + (zmax - ring_z) * pole_k
    ob = bpy.data.objects.new(key, me)
    P.get_collection("ASSET_LIBRARY").objects.link(ob)
    ob.hide_render = ob.hide_viewport = True
    co = np.array([v.co[:] for v in me.vertices])
    D.rock_lib[key] = ob
    D.rock_bbox[key] = (Vector(co.min(0)), Vector(co.max(0)))


def dark_rocks(D):
    """Crater rock is dark basalt: every library mesh (shared by all instances) uses MAT_ROCK_DARK / MAT_CLIFF_DARK only."""
    rock_variant(D, "CLIFF_ROCK", "ROCK_WALL_FLAT", 0.0)
    rock_variant(D, "CLIFF_ROCK", "ROCK_WALL_BLUNT", 0.45)
    for key, ob in D.rock_lib.items():
        ob.data.materials.clear()
        ob.data.materials.append(D.mats["MAT_ROCK_DARK" if key in ("ROCK_LARGE", "ROCK_MEDIUM", "ROCK_SMALL") else "MAT_CLIFF_DARK"])


def dark_walls(D):
    """The terrain walls are banded MAT_ROUGH (grass lip) / MAT_CLIFF / MAT_CLIFF_DARK: swap the upper rock band to MAT_ROCK_DARK."""
    me = D.terrain.data
    me.materials[1] = D.mats["MAT_ROCK_DARK"]
    me.materials[2] = D.mats["MAT_CLIFF_DARK"]


def fit(D, ob, kind, center, dims, R):
    """Scale / place the rock instance `ob` so its (unrotated-frame) bounding box is `dims` big, centred on `center`, rotated by R."""
    mn, mx = D.rock_bbox[P._rock_key(kind)]
    size, ctr = mx - mn, (mn + mx) * 0.5
    sc = Vector((dims[0] / size.x, dims[1] / size.y, dims[2] / size.z))
    ob.scale = sc
    ob.rotation_euler = R.to_euler()
    ob.location = Vector(center) - R @ Vector((ctr.x * sc.x, ctr.y * sc.y, ctr.z * sc.z))
    return ob


def top_z(ob):
    mw = ob.matrix_world
    return max((mw @ v.co).z for v in ob.data.vertices)


# ----------------------------------------------------------------------------- far crater wall
def wall_ring(D, W):
    """Three staggered rows of tall columns between r_inner and r_outer round the crater centre, rising outward (inner row about
    30-40 m above the lava, outer row 44-52 m). The lava plane cuts every column at its widest ring, so the waterline is clean."""
    rnd = random.Random(1010)
    cx, cy = P.m(W["cx"], W["cd"])
    r0, r1 = W["r_inner"] * P.YD, W["r_outer"] * P.YD
    h0, h1 = W["h_min"], W["h_max"]
    out = []
    for k, t in enumerate((0.0, 0.5, 1.0)):
        r = r0 + (r1 - r0) * t
        n = int(2 * math.pi * r / 36.0)
        for i in range(n):
            th = 2 * math.pi * (i + 0.5 * (k % 2) + rnd.uniform(-0.2, 0.2)) / n
            rr = r + rnd.uniform(-5.0, 5.0)
            h = h0 + (h1 - h0) * (0.10 + 0.60 * t) + rnd.uniform(-0.12, 0.24) * (h1 - h0)
            h = min(max(h, h0 + 1.5), h1 - 1.5)
            wide, deep = rnd.uniform(32.0, 48.0), rnd.uniform(30.0, 44.0)
            base_z = -0.45 * h
            kind = rnd.choice(("ROCK_WALL_FLAT", "ROCK_WALL_FLAT", "ROCK_WALL_BLUNT", "CLIFF"))
            ob = P.place_rock(D, kind, (0, 0, 0))
            out.append(fit(D, ob, kind, (cx + rr * math.cos(th), cy + rr * math.sin(th), base_z + (h - base_z) / 2),
                           (wide, deep, h - base_z), Matrix.Rotation(th + math.pi / 2 + rnd.uniform(-0.5, 0.5), 3, "Z")))
    return out


# ----------------------------------------------------------------------------- stacks in the lava
STACK_PARTS = (("LARGE", 1.0), ("MEDIUM", 0.64), ("MEDIUM", 0.42))


def make_stack(D, s, top):
    """One stack = three overlapping library rocks (wide foot, narrower waist, small cap) from 1.6 m below the lava up to `top`."""
    x, y = P.m(s["x"], s["d"])
    st = dict(x=x, y=y, rad=s["r"] * P.YD, rot=D.rng.uniform(0, math.tau),
              jit=[(D.rng.uniform(-0.1, 0.1), D.rng.uniform(-0.1, 0.1)) for _ in STACK_PARTS],
              obs=[P.place_rock(D, kind, (0, 0, 0)) for kind, _ in STACK_PARTS])
    refit_stack(D, st, top)
    return st


def refit_stack(D, st, top):
    z0 = -1.6
    hseg = (top - z0) / 2.375                      # three segments, each 1.15 hseg tall, overlapping by 0.5 hseg: top = z0 + 2.375 hseg
    for j, ((kind, wk), ob) in enumerate(zip(STACK_PARTS, st["obs"])):
        c = Vector((st["x"] + st["jit"][j][0] * st["rad"], st["y"] + st["jit"][j][1] * st["rad"], z0 + hseg * 0.5 + hseg * 0.65 * j))
        fit(D, ob, kind, c, (2 * st["rad"] * wk, 2 * st["rad"] * wk * 0.92, hseg * 1.15), Matrix.Rotation(st["rot"] + j * 0.7, 3, "Z"))
    st["top"] = top


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


def clear_sightlines(D, stacks_):
    """Lower any stack that cuts a sight line (8 percent per round, never below STACK_FLOOR_H) until none does. Returns the rounds used."""
    lines = sightlines(D)
    for rnd_ in range(60):
        bpy.context.view_layer.update()
        V, T, who = [], [], []
        for i, st in enumerate(stacks_):
            for ob in st["obs"]:
                base = len(V)
                V += [tuple(ob.matrix_world @ v.co) for v in ob.data.vertices]
                for p in ob.data.polygons:
                    T.append(tuple(base + k for k in p.vertices))
                    who.append(i)
        bvh = BVHTree.FromPolygons(V, T)
        bad = set()
        for eye0, tgt in lines:
            d0 = tgt - eye0
            side = Vector((-d0.y, d0.x, 0.0)).normalized() * 0.8              # a corridor, not a hair: eye 0.8 m left / centre / right
            for eye in (eye0 - side, eye0, eye0 + side):
                d = tgt - eye
                hit = bvh.ray_cast(eye, d.normalized(), d.length - 0.05)
                if hit[0] is not None:
                    bad.add(who[hit[2]])
        if not bad:
            return rnd_
        for i in bad:
            refit_stack(D, stacks_[i], max(STACK_FLOOR_H, stacks_[i]["top"] * 0.92))
    return -1


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


def lava_as_unity_sees_it():
    """For the preview still only: Unity reads MAT_LAVA's floats as sRGB, Blender reads them as linear (a washed-out yellow). Render with
    the sRGB-correct values, then put the exported raw floats back. Returns the restore function."""
    b = next(n for n in bpy.data.materials["MAT_LAVA"].node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    keep = (tuple(b.inputs["Base Color"].default_value), tuple(b.inputs["Emission Color"].default_value), b.inputs["Emission Strength"].default_value)
    lin = P.rgb(*(round(c * 255) for c in P.LAVA_RGB))
    b.inputs["Base Color"].default_value = b.inputs["Emission Color"].default_value = lin
    b.inputs["Emission Strength"].default_value = 0.8

    def restore():
        b.inputs["Base Color"].default_value, b.inputs["Emission Color"].default_value, b.inputs["Emission Strength"].default_value = keep
    return restore


# ----------------------------------------------------------------------------- the build
D = P.start("hole10_design", out_dir=OUT)
SC = D.scenery
D.mod.SCENERY["tee_box_m"] = (SC["tee_box"]["width"] * P.YD, SC["tee_box"]["depth"] * P.YD)   # the lib reads metres; the design says yards

P.build_terrain(D, undercut_m=6.0)
dark_walls(D)
P.build_play_surfaces(D)
P.build_water(D, "WATER_LAVA", "MAT_LAVA", shallow_material=None, foam_material=None, crest=False)
P.import_rocks(D)
dark_rocks(D)

ring = wall_ring(D, SC["wall_ring"])
hs = [s["h"] for s in SC["stacks"]]
stacks = [make_stack(D, s, STACK_MIN_H + (s["h"] - min(hs)) / (max(hs) - min(hs)) * (STACK_MAX_H - STACK_MIN_H)) for s in SC["stacks"]]
rounds = clear_sightlines(D, stacks)
c_st, pin_st = P.m(*D.CENTERLINE[-2]), P.m(*D.CENTERLINE[-1])        # keep the lava carry itself free of rubble
carry = [(c_st[0] + (pin_st[0] - c_st[0]) * k / 14.0, c_st[1] + (pin_st[1] - c_st[1]) * k / 14.0, 24.0) for k in range(15)]
foot = P.scatter_rocks(D, count=40, seed=4, zone="foot", kinds=("LARGE", "MEDIUM"), scale=(0.8, 1.5), z=(-1.0, -0.1), min_gap=9.0, avoid=carry)

P.build_gameplay(D)
P.build_cameras_and_light(D)
frame_overview(D, OVERVIEW_RES)
restore = lava_as_unity_sees_it()
P.render_overview(D, res=OVERVIEW_RES)
restore()
bpy.context.preferences.filepaths.save_version = 0       # no hole_10.blend1 next to the scene
P.save(D)
P.export_fbx(D)

st = P.stats(D)
tops = [top_z(o) for o in ring]
stops = [max(top_z(o) for o in s["obs"]) for s in stacks]
print(f"[hole10_build] wall ring {len(ring)} rocks, tops {min(tops):.1f}..{max(tops):.1f} m above the lava; {len(stacks)} stacks "
      f"({', '.join('%.1f' % t for t in stops)} m measured, sightline rounds {rounds}); foot rubble {len(foot)}; objects {st['objects']} tris {st['tris']}")
