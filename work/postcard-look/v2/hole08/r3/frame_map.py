"""where do the tee-camera pixels land on the ground (course yards)? TEE_BOX extent, ball, markers."""
import sys, math
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
YD = 0.9144
blend = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=blend)
bpy.context.view_layer.update()
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
tb = bpy.data.objects["TEE_BOX"]
mw = np.array(tb.matrix_world)
V = np.array([v.co[:] for v in tb.data.vertices]) @ mw[:3, :3].T + mw[:3, 3]
print("TEE_BOX x", V[:,0].min()/YD, V[:,0].max()/YD, "y", V[:,1].min()/YD, V[:,1].max()/YD, "z", V[:,2].min(), V[:,2].max())
for n in ("BALL_START", "MARKER_TEE", "MARKER_TEE_L", "MARKER_TEE_R"):
    if n in bpy.data.objects:
        print(n, [c/YD for c in bpy.data.objects[n].matrix_world.translation[:2]], bpy.data.objects[n].matrix_world.translation.z)
print([o.name for o in bpy.data.objects if o.name.startswith("MARKER") or o.name.startswith("BALL")])
bx, by = 0.0, 0.0
ax, ay = 19.0*YD, 178.0*YD
ok, loc, nrm, idx, ob, _m = sc.ray_cast(dg, Vector((bx, by, 40.0)), Vector((0, 0, -1)), distance=80.0)
bz = loc.z
dv = Vector((ax - bx, ay - by, 0.0)).normalized()
cam = Vector((bx, by, bz)) - dv * 4.5 * YD + Vector((0, 0, 2.4 * YD))
look = (Vector((bx, by, bz)) + dv * 1.5 * YD - cam).normalized()
right = look.cross(Vector((0, 0, 1))).normalized(); up = right.cross(look).normalized()
tv = math.tan(math.radians(30.0)); th = tv * 900 / 1600
print("cam", cam, "look", look, "dv", dv)
for py in (0, 20, 30, 40, 50, 60, 70, 80, 90, 100):
    row = []
    for px in (0, 50, 100):
        ndc_x = px/100*2-1; ndc_y = -(py/100)*2+1
        d = (look + right*(ndc_x*th) + up*(ndc_y*tv)).normalized()
        ok, loc, nrm, i, ob, _m = sc.ray_cast(dg, cam, d, distance=900.0)
        row.append(f"({loc.x/YD:6.1f},{loc.y/YD:6.1f}) {ob.name[:12] if ok else '-'}" if ok else "sky")
    print(f"y{py:3d}%:", " | ".join(row))
# ball pixel
d = (Vector((0,0,bz)) - cam).normalized()
x = d.dot(right)/ (d.dot(look)) / th; y = d.dot(up)/(d.dot(look))/tv
print("ball ndc", x, y, "-> px", (x+1)/2*900, (1-y)/2*1600)
