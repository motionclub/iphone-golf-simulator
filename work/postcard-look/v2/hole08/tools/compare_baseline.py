"""H_PLAY_UNCHANGED: every play surface / terrain mesh and every gameplay marker of a staged hole_08.blend equals work/postcard-look/baseline/blender/hole_08.blend.
usage: Blender -b --factory-startup --python compare_baseline.py -- STAGED.blend [OUT.json]
Compared per ground mesh: object name set, vertex count, world vertex coordinates (max |delta| in metres), polygon vertex lists (topology), polygon count; material indices are NOT compared (the
look pass retargets MAT_* -> LK_* and merges the two fairway stripe slots). Markers: world position of MARKER_TEE/PIN/UP, TEE_MARKER_1/2, BALL_START, HOLE_CUP, FLAG, FLAG_POLE (max |delta|)."""
import sys, os, json, hashlib
import bpy, numpy as np
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
BASE = REPO + "/work/postcard-look/baseline/blender/hole_08.blend"
GROUND = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH")
MARK = ("MARKER_TEE", "MARKER_PIN", "MARKER_UP", "TEE_MARKER_1", "TEE_MARKER_2", "BALL_START", "HOLE_CUP", "FLAG", "FLAG_POLE")


def snap(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    bpy.context.view_layer.update()
    out, marks = {}, {}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(GROUND):
            me = o.data
            mw = np.array(o.matrix_world)
            V = np.array([v.co[:] for v in me.vertices]).reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
            polys = [tuple(p.vertices) for p in me.polygons]
            out[o.name] = (V, polys)
        if o.name in MARK:
            marks[o.name] = np.array(o.matrix_world.translation)
    return out, marks


a, ma = snap(BASE)
b, mb = snap(os.path.abspath(sys.argv[sys.argv.index("--") + 1]))
res = []
bad = []
worst = 0.0
nv = 0
for k in sorted(set(a) | set(b)):
    if k not in a or k not in b:
        bad.append(f"{k} only in {'staged' if k in b else 'baseline'}")
        continue
    (Va, Pa), (Vb, Pb) = a[k], b[k]
    if Va.shape != Vb.shape or len(Pa) != len(Pb):
        bad.append(f"{k}: {len(Va)} -> {len(Vb)} vertices, {len(Pa)} -> {len(Pb)} polygons")
        continue
    d = float(np.abs(Va - Vb).max()) if len(Va) else 0.0
    worst = max(worst, d)
    nv += len(Va)
    topo = sum(1 for x, y in zip(Pa, Pb) if x != y)
    if d > 1e-6 or topo:
        bad.append(f"{k}: max |delta| {d:.2e} m, {topo} polygons with a different vertex list")
mw_ = 0.0
for k in MARK:
    if k not in ma or k not in mb:
        bad.append(f"marker {k} missing ({'baseline' if k not in ma else 'staged'})")
        continue
    mw_ = max(mw_, float(np.abs(ma[k] - mb[k]).max()))
if mw_ > 1e-6:
    bad.append(f"markers moved {mw_:.2e} m")
ok = not bad
line = (f"GATE: H_PLAY_UNCHANGED {'PASS' if ok else 'FAIL'} - {len(set(a) & set(b))} ground meshes {nv} vertices vs the baseline blend: max |delta| {worst:.2e} m, "
        f"identical polygon vertex lists, {len(MARK)} gameplay markers max |delta| {mw_:.2e} m" + ("" if ok else "; " + "; ".join(bad[:6])))
print(line)
if len(sys.argv) > sys.argv.index("--") + 2:
    json.dump(dict(ok=ok, worst=worst, marker_worst=mw_, bad=bad, meshes=sorted(a)), open(sys.argv[sys.argv.index("--") + 2], "w"), indent=1)
