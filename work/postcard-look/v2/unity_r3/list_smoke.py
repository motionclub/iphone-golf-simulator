import bpy, sys
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/hole_10.blend")
for o in sorted(bpy.data.objects, key=lambda o:o.name):
    if o.name.startswith(("DRESS_SMOKE","DRESS_CONE")) or o.name.startswith("LAVA_LIGHT"):
        bb=[o.matrix_world@Vector(c) for c in o.bound_box] if o.type=="MESH" else [o.matrix_world.translation]
        mn=Vector((min(b.x for b in bb),min(b.y for b in bb),min(b.z for b in bb))); mx=Vector((max(b.x for b in bb),max(b.y for b in bb),max(b.z for b in bb)))
        mats=[m.name for m in o.data.materials] if o.type=="MESH" else []
        nv=len(o.data.vertices) if o.type=="MESH" else 0
        print("OBJ",o.name,o.type,"verts",nv,"min",tuple(round(v,1) for v in mn),"max",tuple(round(v,1) for v in mx),mats)
