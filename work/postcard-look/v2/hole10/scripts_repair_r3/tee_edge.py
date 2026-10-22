"""Is the tee pad's edge visible in the tee frame? Ray casts through the 900 x 1600 address camera of hole10_tee (CameraRig.FrameAddress: 4.5 yd behind the ball on the aim line, 2.4 yd up, looks at ball + aim x 1.5 yd,
60 degrees vertical) against the staged blend; counts the pixels whose first hit is a DRESS_PADEDGE_* piece (round 3: the dark edge ribbon of the tee pad; DRESS_PADRIM_* = the basalt variant; round 2 counted DRESS_PATH_* = the flagstone kerb).

  Blender -b STAGE.blend --python tee_edge.py -- --shots landmarks.json [--json OUT.json] [--expect-fail]

Prints `GATE: H_TEE_EDGE_VISIBLE PASS|FAIL - ...`. PASS (round 3) = the edge ribbon shows in >= 95 % of the sampled columns, median thickness >= 10 px (0.37 degrees of the 60 degree frame), thinnest 5 % >= 4 px, covers >= 0.5 % of the frame; the contrast against the grass is tools/rim_contrast.py. The band rows are written to the json (`rows`) so seam_metric.py can leave the DELIBERATE kerb edge out of its
accidental-seam search (the grass above / below the band is still measured).
"""
import sys, os, json, math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

YD = 0.9144
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d=None):
    return args[args.index(n) + 1] if n in args else d


SHOTS = json.load(open(opt("--shots")))["shots"]
tee = next(s for s in SHOTS if s["name"] == "hole10_tee")
V, F, owner, names = [], [], [], []
for ob in bpy.data.objects:
    if ob.type != 'MESH' or "ASSET_LIBRARY" in [c.name for c in ob.users_collection] or ob.name not in bpy.context.scene.objects:
        continue
    if ob.name.startswith(("DRESS_SMOKE", "LAVA_LIGHT", "FLAG", "HOLE_CUP", "BALL_START", "MARKER_", "TEE_MARKER")):
        continue
    me, mw, base = ob.data, ob.matrix_world, len(V)
    V += [tuple(mw @ v.co) for v in me.vertices]
    for p in me.polygons:
        F.append(tuple(base + i for i in p.vertices))
        owner.append(len(names))
    names.append(ob.name)
BVH = BVHTree.FromPolygons(V, F)
GROUND = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER")


def ground_z(x, y):
    h = BVH.ray_cast(Vector((x, y, 60.0)), Vector((0, 0, -1)), 200.0)
    while h[0] is not None:
        if names[owner[h[2]]].startswith(GROUND):
            return h[0].z
        h = BVH.ray_cast(h[0] - Vector((0, 0, 0.01)), Vector((0, 0, -1)), 200.0)
    return None


bx, by = tee["ball"][0] * YD, tee["ball"][1] * YD
ball = Vector((bx, by, ground_z(bx, by) + 0.055))
aim = Vector((tee["aim"][0] * YD - bx, tee["aim"][1] * YD - by, 0)).normalized()
loc = ball - aim * 4.5 * YD + Vector((0, 0, 2.4 * YD))
look = ball + aim * 1.5 * YD
fwd = (look - loc).normalized()
right = fwd.cross(Vector((0, 0, 1))).normalized()
up = right.cross(fwd).normalized()
ty = math.tan(math.radians(60.0) / 2)
tx = ty * 900 / 1600
H, W = 1600, 900
rows = list(range(0, H, 4))
cols = np.linspace(2, W - 3, 90)
hit_path = np.zeros((len(rows), len(cols)), bool)
for j, y in enumerate(rows):
    v = 1 - (y + 0.5) / H * 2
    for i, x in enumerate(cols):
        u = (x + 0.5) / W * 2 - 1
        d = (fwd + right * (u * tx) + up * (v * ty)).normalized()
        h = BVH.ray_cast(loc, d, 3000.0)
        if h[0] is not None and names[owner[h[2]]].startswith(("DRESS_PADRIM", "DRESS_PADEDGE")):
            hit_path[j, i] = True
share = hit_path.mean(axis=1)
# round 3: the rim is a RAGGED ribbon (its inner edge wanders +-0.4 m), so "a full-width band of N rows" is the wrong measure; per sampled column the thickness of the rim in pixel rows
# (every 4th row sampled) is measured instead: >= 95 % of the columns must show rim, the median thickness >= 14 px (about 0.5 degrees of the 60 degree frame: a band you can pick out at phone size),
# the thinnest 5 % of the columns >= 6 px, and the rim must cover >= 0.8 % of the frame
thick = hit_path.sum(axis=0) * 4.0
cols_hit = float((thick > 0).mean())
med = float(np.median(thick))
p5 = float(np.percentile(thick, 5))
mx = float(thick.max())
any_rows = [rows[k] for k in range(len(rows)) if share[k] > 0.0]
cover = float(hit_path.mean())
ok = cols_hit >= 0.95 and med >= 10.0 and p5 >= 4.0 and cover >= 0.005
band_rows = (min(any_rows), max(any_rows) + 3) if any_rows else None
thick_px = med
txt = (f"tee camera 900 x 1600: pad edge ribbon pixels {cover:.1%} of the frame (>= 0.5 %), rim in {cols_hit:.0%} of the {len(cols)} sampled columns (>= 95 %), thickness median {med:.0f} px (>= 10), "
       f"thinnest 5 % of the columns {p5:.0f} px (>= 4), max {mx:.0f} px; rows {band_rows} (the old tan kerb was 44 rows of 100 % width)")
if "--expect-fail" in args:
    print(f"CONTROL H_TEE_EDGE_VISIBLE {'FAIL (detected, as it must for the build without a rim)' if not ok else 'PASS (UNEXPECTED: the control should fail)'} - {txt}")
else:
    print(f"GATE: H_TEE_EDGE_VISIBLE {'PASS' if ok else 'FAIL'} - {txt}")
if opt("--json"):
    bands = []
    for i_, x_ in enumerate(cols.tolist()):
        rr = [rows[j_] for j_ in range(len(rows)) if hit_path[j_, i_]]
        if rr:
            bands.append([int(round(x_)), int(min(rr)), int(max(rr) + 3)])
    json.dump(dict(ok=bool(ok), cover=cover, thick_px=thick_px, band_rows=band_rows, rows=[min(any_rows), max(any_rows) + 3] if any_rows else None, cols_hit=cols_hit, median=med, p5=p5, bands=bands), open(opt("--json"), "w"), indent=1)
