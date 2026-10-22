"""ball_cover.py - REPORT-ONLY measurement (not a gate): how much of the Rough ridge can hide a ball that rests on it, because a non-colliding prop stands over it.

    Blender -b --factory-startup --python ball_cover.py -- --blend STAGE/hole_09.blend [--step 1.5] [--json OUT.json]

The ridge is Rough (the lie comes from Hole.LieAt, frozen) and every prop on it is visual only (no collider), so a ball can come to rest INSIDE a rock, a knoll, a
masonry block or a plant. For a regular grid of ball positions on the ridge top (lie Rough, >= 2 m inside the shore) it reports, per prop class and for the
whole ridge, the share of positions

  * INSIDE a prop (an upward ray from the ball crosses a prop surface an odd number of times): the ball cannot be seen from any side;
  * OCCLUDED from the phone address camera (4.5 yd behind the ball, 2.4 yd up, four aim headings) by a prop between the camera and the ball.

Positions within 8 yd of the dry safe ridge route (the corridor a ridge player uses) are reported separately: no prop is allowed there (gate H_LEGACY_ROUTE_CLEAR).
Nothing is changed in the blend.
"""
import json
import math
import os
import sys

sys.dont_write_bytecode = True
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", "blender", "scripts"))
sys.path.insert(0, SCRIPTS)
import postcard_lib as P  # noqa: E402
import postcard_look_lib as L  # noqa: E402
import hole09_look as HL  # noqa: E402

YD = P.YD
A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d=None):
    return A[A.index(n) + 1] if n in A and A.index(n) + 1 < len(A) else d


BLEND = os.path.abspath(opt("--blend"))
STEP = float(opt("--step", "1.5"))
JS = opt("--json")

D = P.start("hole09_design", out_dir="/tmp/hole09_ballcover_scratch")
D.mod.SCENERY["tee_box_m"] = (10.4, 13.2)
bpy.ops.wm.open_mainfile(filepath=BLEND)
D.terrain = bpy.data.objects[D.terrain_name]
loops = L.terrain_top_loops(D, D.terrain)
D.loops = [[(float(x), float(y)) for x, y in Pl] for Pl, _ in loops]
D.loop_kinds = ["outer" if P.signed_area(np.array(l_)) > 0 else "hole" for l_ in D.loops]
D._distfield = None
pz = D.play_z


def klass(n):
    if n.startswith("DRESS_KNOLL"):
        return "knoll"
    if n.startswith(("DRESS_RUIN", "DRESS_ARCH", "DRESS_BLOCK")):
        return "masonry"
    if n.startswith("ROCK_CRAG"):
        return "crag"
    if n.startswith(("ROCK_SEASTACK", "ROCK_SPIRE")):
        return "stack"
    if n.startswith("PLANT_"):
        return "plant"
    if n.startswith("ROCK_") and not n.startswith("ROCK_SKIN"):
        return "rock"
    return None


V, F, K = [], [], []
cls_id = {}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    c = klass(o.name)
    if c is None:
        continue
    if all(col.name == "ASSET_LIBRARY" for col in o.users_collection):
        continue                                                   # hidden library prototypes at the origin
    mw = o.matrix_world
    me = o.data
    me.calc_loop_triangles()
    base = len(V)
    V += [tuple(mw @ v.co) for v in me.vertices]
    for t in me.loop_triangles:
        F.append([base + i for i in t.vertices])
        K.append(cls_id.setdefault(c, len(cls_id)))
names = {v: k for k, v in cls_id.items()}
bvh = BVHTree.FromPolygons(V, F, epsilon=0.0)
Kn = np.array(K)

route = HL.route_m(D)
ridge_side = HL.mask_ridge_side(D)
xs = np.arange(-120.0, 5.0, STEP)
ys = np.arange(-40.0, 480.0, STEP)
X, Y = np.meshgrid(xs, ys)
X, Y = X.ravel(), Y.ravel()
sd = P.signed_dist_m(D, X, Y)
lie = P.lie_codes_m(D, X, Y)
ok = ridge_side(X, Y) & (sd <= -2.0) & (lie == 5)               # 5 = Rough (LIE_NAMES)
X, Y = X[ok], Y[ok]
dr = HL.dist_to_poly(route, X, Y)
print(f"ridge ball positions: {len(X)} (grid {STEP} m, Rough, >= 2 m inside the shore); {int((dr < 8 * YD).sum())} within 8 yd of the route")

DIRS = [(0.0, 1.0), (0.0, -1.0), (1.0, 0.0), (-1.0, 0.0)]


def first_hits(origin, direction, maxd):
    """All ray hits (distance, face index) up to maxd, in order (an odd count for an upward ray = the origin is inside a closed prop)."""
    out, o, d0, trav = [], Vector(origin), Vector(direction), 0.0
    for _ in range(40):
        h = bvh.ray_cast(o, d0, maxd - trav)
        if h[0] is None:
            break
        out.append((trav + h[3], h[2]))
        trav += h[3] + 1e-4
        o = h[0] + d0 * 1e-4
    return out


inside = np.zeros(len(X), bool)
inside_cls = [None] * len(X)
occl = np.zeros((len(X), len(DIRS)), bool)
for i in range(len(X)):
    o = (float(X[i]), float(Y[i]), pz + 0.0213)
    hits = first_hits(o, (0.0, 0.0, 1.0), 60.0)
    if len(hits) % 2 == 1:
        inside[i] = True
        inside_cls[i] = names[int(Kn[hits[0][1]])]
    for j, (dx, dy) in enumerate(DIRS):
        cam = Vector((o[0] - dx * 4.5 * YD, o[1] - dy * 4.5 * YD, o[2] + 2.4 * YD))
        vec = Vector(o) - cam
        dist = vec.length
        h = bvh.ray_cast(cam, vec.normalized(), dist - 0.03)
        occl[i, j] = h[0] is not None
corr = dr < 8 * YD
res = dict(n=int(len(X)), n_corridor=int(corr.sum()))
res["inside_share_all"] = float(inside.mean())
res["inside_share_corridor"] = float(inside[corr].mean()) if corr.any() else 0.0
res["inside_share_off_route"] = float(inside[~corr].mean())
res["inside_by_class_off_route"] = {k: float(np.mean([(c == k) for c, cc in zip(inside_cls, corr) if not cc])) for k in sorted(set(names.values()))}
res["inside_by_class_corridor"] = {k: float(np.mean([(c == k) for c, cc in zip(inside_cls, corr) if cc])) for k in sorted(set(names.values()))}
res["occluded_share_off_route_any_heading"] = float(occl[~corr].any(1).mean())
res["occluded_share_off_route_mean_heading"] = float(occl[~corr].mean())
res["occluded_share_corridor_mean_heading"] = float(occl[corr].mean()) if corr.any() else 0.0
print("BALL_COVER", json.dumps(res, indent=1))
if JS:
    json.dump(res, open(JS, "w"), indent=1)
