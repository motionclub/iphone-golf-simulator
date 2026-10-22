"""Ray-probe pixels of the tee proof camera (900x1600, fov 60 vertical, CameraRig.FrameAddress) against a blend.
Blender -b X.blend --python pixel_probe.py -- x,y x,y ...   (shot = tee | approach)"""
import sys, math, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
YD = 0.9144
args = sys.argv[sys.argv.index("--") + 1:]
shot = args[0]
pix = [tuple(int(v) for v in a.split(",")) for a in args[1:]]
V, F, owner, names = [], [], [], []
for ob in bpy.data.objects:
    if ob.type != 'MESH' or ob.name not in bpy.context.scene.objects or "ASSET_LIBRARY" in [c.name for c in ob.users_collection]:
        continue
    if ob.name.startswith(("DRESS_SMOKE", "LAVA_LIGHT")):
        continue
    me = ob.data; mw = ob.matrix_world; base = len(V)
    V += [tuple(mw @ v.co) for v in me.vertices]
    for p in me.polygons:
        F.append(tuple(base + i for i in p.vertices)); owner.append((len(names), p.material_index))
    names.append(ob.name)
BVH = BVHTree.FromPolygons(V, F)
def gz(x, y):
    h = BVH.ray_cast(Vector((x, y, 60)), Vector((0, 0, -1)), 200)
    while h[0] is not None:
        if names[owner[h[2]][0]].startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER")):
            return h[0].z
        h = BVH.ray_cast(h[0] - Vector((0, 0, 0.01)), Vector((0, 0, -1)), 200)
if shot == "tee":
    ball, aim = (0, 0), (14.3, 66.2)
else:
    ball, aim = (107.1, 159.3), (261, 164.7)
bx, by = ball[0] * YD, ball[1] * YD
b = Vector((bx, by, gz(bx, by) + 0.055))
a = Vector((aim[0] * YD - bx, aim[1] * YD - by, 0)).normalized()
loc = b - a * 4.5 * YD + Vector((0, 0, 2.4 * YD)); look = b + a * 1.5 * YD
fov = 60.0
W, H = 900, 1600
fwd = (look - loc).normalized(); right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd).normalized()
ty = math.tan(math.radians(fov) / 2); tx = ty * W / H
print("cam loc", tuple(round(c, 3) for c in loc), "ball", tuple(round(c, 3) for c in b))
for (px, py) in pix:
    u = (px + 0.5) / W * 2 - 1; v = 1 - (py + 0.5) / H * 2
    d = (fwd + right * (u * tx) + up * (v * ty)).normalized()
    h = BVH.ray_cast(loc, d, 3000)
    if h[0] is None:
        print(px, py, "sky"); continue
    ob = bpy.data.objects[names[owner[h[2]][0]]]
    mi = owner[h[2]][1]
    mat = ob.data.materials[mi].name if mi < len(ob.data.materials) and ob.data.materials[mi] else None
    print(px, py, ob.name, mat, "hit course yd", (round(h[0].x / YD, 1), round(h[0].y / YD, 1), round(h[0].z, 3)), "dist m", round(h[3], 1))
