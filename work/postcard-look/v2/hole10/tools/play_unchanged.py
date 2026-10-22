"""H_PLAY_UNCHANGED: the play surfaces, terrain, markers and gameplay placeholders of a staged hole_10.blend equal the BASELINE blend
(work/postcard-look/baseline/blender/hole_10.blend, the flat scoring build) vertex for vertex, polygon for polygon.

  Blender -b STAGED.blend --python play_unchanged.py -- [--baseline PATH]

Compares, by name, every TERRAIN / FAIRWAY / GREEN / TEE_BOX / BUNKER / CART_PATH mesh (world vertices, polygon vertex indices) and the nine
placeholders (FLAG, FLAG_POLE, HOLE_CUP, BALL_START, TEE_MARKER_1/2, MARKER_TEE/PIN/UP: world positions). Material slots are NOT compared
(MAT_* -> LK_* is the intended change). Prints `GATE: H_PLAY_UNCHANGED PASS|FAIL - ...`; exit 1 on FAIL.
"""
import sys
sys.dont_write_bytecode = True
import os
import numpy as np
import bpy

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BASE = args[args.index("--baseline") + 1] if "--baseline" in args else \
    "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/baseline/blender/hole_10.blend"
GROUND = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH")
PLACE = ("FLAG", "FLAG_POLE", "HOLE_CUP", "BALL_START", "TEE_MARKER_1", "TEE_MARKER_2", "MARKER_TEE", "MARKER_PIN", "MARKER_UP")

stage_names = {o.name for o in bpy.data.objects if o.type in ('MESH', 'EMPTY') and "ASSET_LIBRARY" not in [c.name for c in o.users_collection]}
cur = {n: bpy.data.objects[n] for n in stage_names if n.startswith(GROUND) or n in PLACE}
with bpy.data.libraries.load(BASE, link=False) as (src, dst):
    want = [n for n in src.objects if n.startswith(GROUND) or n in PLACE or n == "HOLE_10_ROOT"]
    want_names = list(want)
    dst.objects = want
want = want_names
base_objs = {}
for o in bpy.data.objects:
    if o.library is None and o.name not in stage_names and o.name.rsplit(".", 1)[0] in want and o.name.rsplit(".", 1)[-1].isdigit():
        base_objs[o.name.rsplit(".", 1)[0]] = o
# an appended object whose name did not clash keeps its name: those that are not in stage_names are the baseline's
for n in want:
    if n not in base_objs and bpy.data.objects.get(n) is not None and n not in stage_names:
        base_objs[n] = bpy.data.objects[n]


def world(o):
    me = o.data
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    M = np.array(o.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


def polys(o):
    return [tuple(p.vertices) for p in o.data.polygons]


problems, nv, npoly, worst = [], 0, 0, 0.0
names = sorted(n for n in cur if n.startswith(GROUND))
base_names = sorted(n for n in base_objs if n.startswith(GROUND))
if names != base_names:
    problems.append(f"ground mesh names differ: staged-only {sorted(set(names) - set(base_names))}, baseline-only {sorted(set(base_names) - set(names))}")
for n in names:
    b = base_objs.get(n)
    if b is None:
        continue
    A, B = world(cur[n]), world(b)
    if A.shape != B.shape:
        problems.append(f"{n}: {len(B)} baseline vertices, {len(A)} now")
        continue
    d = float(np.abs(A - B).max()) if len(A) else 0.0
    worst = max(worst, d)
    nv += len(A)
    pa, pb = polys(cur[n]), polys(b)
    npoly += len(pa)
    if pa != pb:
        problems.append(f"{n}: polygon topology differs")
    if d > 0.0:
        problems.append(f"{n}: max vertex move {d:.3e} m")
mk_worst = 0.0
for n in PLACE:
    a, b = cur.get(n), base_objs.get(n)
    if a is None or b is None:
        problems.append(f"placeholder {n} missing ({'staged' if a is None else 'baseline'})")
        continue
    # appended baseline objects have no evaluated matrix_world: compare the local transform (and the parent chain's local transforms)
    def chain(o):
        loc, rot, sc, par = [], [], [], []
        while o is not None:
            loc.append(np.array(o.location)); rot.append(np.array(o.rotation_euler)); sc.append(np.array(o.scale)); par.append(o.parent.name.rsplit(".", 1)[0] if o.parent else None)
            o = o.parent
        return loc, rot, sc, par
    ca, cb = chain(a), chain(b)
    if len(ca[0]) != len(cb[0]) or ca[3] != cb[3]:
        problems.append(f"placeholder {n}: parent chain differs {ca[3]} vs {cb[3]}")
        continue
    mk_worst = max(mk_worst, max(float(np.abs(x - y).max()) for k in range(3) for x, y in zip(ca[k], cb[k])))
ok = not problems and worst == 0.0 and mk_worst == 0.0
print(f"GATE: H_PLAY_UNCHANGED {'PASS' if ok else 'FAIL'} - {len(names)} ground meshes {names}: {nv} vertices / {npoly} polygons identical to the baseline blend "
      f"(max |delta| {worst:.3e} m, topology equal); {len(PLACE)} gameplay placeholders max |delta| {mk_worst:.3e} m; problems {problems[:4] or 'none'}")
sys.exit(0 if ok else 1)
