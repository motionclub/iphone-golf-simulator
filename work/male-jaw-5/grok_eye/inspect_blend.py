import bpy
from mathutils import Vector
print("=== OBJECTS ===")
for o in bpy.data.objects:
    print(f"{o.type:10} {o.name:40} hide_r={o.hide_render} loc={tuple(round(x,3) for x in o.location)}")
print("=== CAMERAS DETAIL ===")
for o in bpy.data.objects:
    if o.type=="CAMERA":
        c=o.data
        os=getattr(c,"ortho_scale",None)
        print(f"CAM {o.name}: type={c.type} ortho_scale={os} lens={c.lens} loc={tuple(round(x,3) for x in o.location)} rot={tuple(round(x,3) for x in o.rotation_euler)}")
print("SCENE CAM", bpy.context.scene.camera.name if bpy.context.scene.camera else None)
print("RES", bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y)
print("ENGINE", bpy.context.scene.render.engine)
body=bpy.data.objects.get("Body_M")
if body:
    import numpy as np
    co=np.array([v.co[:] for v in body.data.vertices])
    print("BODY verts", len(co), "bounds min", co.min(0), "max", co.max(0), "center", co.mean(0))
    # approximate regions
    hands = co[(co[:,2]>0.7)&(co[:,2]<1.2)&(np.abs(co[:,0])>0.15)]
    feet = co[co[:,2]<0.15]
    chin = co[(co[:,2]>1.35)&(co[:,2]<1.55)&(co[:,1]<-0.05)]
    shoulders = co[(co[:,2]>1.25)&(co[:,2]<1.45)]
    waist = co[(co[:,2]>0.9)&(co[:,2]<1.05)]
    print("hand pts", len(hands), "feet", len(feet), "chin", len(chin))
    if len(shoulders): print("shoulder width x", shoulders[:,0].max()-shoulders[:,0].min())
    if len(waist): print("waist width x", waist[:,0].max()-waist[:,0].min(), "depth y", waist[:,1].max()-waist[:,1].min())
print("MATERIALS", [m.name for m in bpy.data.materials])
for m in bpy.data.materials:
    if m.use_nodes:
        print("MAT", m.name, [n.type for n in m.node_tree.nodes])
