"""tee_parallax_check.py - the texture jump a camera sees where the raised TEE_BOX (z +0.24) ends over the FAIRWAY (z +0.14), measured on the finished blend (round 3, review: 'a faint straight ruler line crosses the
whole tee frame', Game-view rows 556 / 557 of hole09_1_tee.png).

The tee box is a flat plate 10 cm over the fairway with no riser. From the address camera (4.5 yd behind the ball, 2.4 yd up: 11.9 deg down at the far edge) the plate hides a strip of fairway 0.1 / tan(11.9 deg)
= 0.48 m wide behind its far edge: the picture jumps from the plate's texture at the edge to the fairway texture 0.48 m further on, although both meshes carry the same world function (centerline UV): a texture
phase jump across the whole frame width, in the picture of a mottled (1-3 m blotch) albedo it is a straight line.

Gate TEE_EDGE_UV_CONTINUOUS: for rays of the address camera that cross the far edge (x -3.5..+3.5 m = the frame at that distance), the UV (x tile = 10 m) of the last TEE_BOX hit and of the first FAIRWAY hit
differ by at most 0.10 m of texture (the unshifted build: 0.47 m).

  Blender -b BLEND --python tee_parallax_check.py -- [--json out.json]
"""
import sys, json, math
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
YD = 0.9144
def opt(n, d=None):
    return A[A.index(n) + 1] if n in A and A.index(n) + 1 < len(A) else d

def pack(ob):
    me = ob.data
    me.calc_loop_triangles()
    mw = np.array(ob.matrix_world)
    verts = [Vector(tuple(mw[:3, :3] @ np.array(v.co) + mw[:3, 3])) for v in me.vertices]
    tr = [(lt.vertices[:], lt.loops[:]) for lt in me.loop_triangles]
    return me, verts, tr, BVHTree.FromPolygons(verts, [t[0] for t in tr])

def uv_at(pk, idx, p):
    me, verts, tr, bvh = pk
    uv = me.uv_layers.active.data
    vi, li = tr[idx]
    a, b, c = [verts[i] for i in vi]
    T = np.array([[a.x - c.x, b.x - c.x], [a.y - c.y, b.y - c.y]])
    r = np.array([p.x - c.x, p.y - c.y])
    l1, l2 = np.linalg.solve(T, r)
    l3 = 1 - l1 - l2
    return l1 * np.array(uv[li[0]].uv) + l2 * np.array(uv[li[1]].uv) + l3 * np.array(uv[li[2]].uv)

tb, fw = bpy.data.objects["TEE_BOX"], bpy.data.objects["FAIRWAY"]
pt, pf = pack(tb), pack(fw)
tile = 10.0
# the address camera of a tee shot (CameraRig.FrameAddress): ball at the tee marker, 4.5 yd behind it, 2.4 yd up, looking 1.5 yd ahead; the aim is the first station of the centerline
tee = bpy.data.objects.get("MARKER_TEE")
ball = np.array([0.0, 0.0])
aim = np.array([3.0, 60.0]) * YD
d = (aim - ball) / np.linalg.norm(aim - ball)
tz = max(v.z for v in pt[1])
cam = Vector((ball[0] - d[0] * 4.5 * YD, ball[1] - d[1] * 4.5 * YD, tz + 0.06 * YD + 2.4 * YD))
res = []
for x0 in np.linspace(-3.4, 3.4, 15):
    # walk the far edge: ground points p(y) on the line x = x0 (play direction), y from 5 to 8 m
    last_t, first_f = None, None
    for y in np.arange(5.0, 8.0, 0.002):
        p = Vector((x0, y, tz - 0.05))
        dirv = (p - cam).normalized()
        ht = pt[3].ray_cast(cam, dirv, 200.0)
        hf = pf[3].ray_cast(cam, dirv, 200.0)
        if ht[0] is not None:
            last_t = (ht[0], ht[2], y)
        elif hf[0] is not None and last_t is not None:
            first_f = (hf[0], hf[2], y)
            break
    if last_t is None or first_f is None:
        continue
    ut = uv_at(pt, last_t[1], last_t[0])
    uf = uv_at(pf, first_f[1], first_f[0])
    du = (ut - uf)
    du[1] = ((du[1] + 0.5) % 1.0) - 0.5                 # the two objects' integer V shifts differ: only the fractional part matters (the texture tiles)
    du[0] = ((du[0] + 0.5) % 1.0) - 0.5
    res.append((float(x0), float(np.hypot(*du) * tile), float(first_f[0].y - last_t[0].y)))
mx = max(r[1] for r in res) if res else 99.0
mean = float(np.mean([r[1] for r in res])) if res else 99.0
ok = bool(res) and mx <= 0.10
print(f"GATE: TEE_EDGE_UV_CONTINUOUS {'PASS' if ok else 'FAIL'} - {len(res)} camera rays across the far edge of the tee box (x -3.4..3.4 m): texture jump between the last plate hit and the first fairway hit max {mx:.3f} m, mean {mean:.3f} m (limit 0.10 m; a plate 10 cm over the fairway hides {0.1 / math.tan(math.radians(11.9)):.2f} m of it from this camera); ground hidden behind the edge max {max(r[2] for r in res):.2f} m" if res else "GATE: TEE_EDGE_UV_CONTINUOUS FAIL - no ray crossed the edge")
j = opt("--json")
if j:
    json.dump(dict(ok=ok, max=mx, mean=mean, rays=res), open(j, "w"), indent=1)
