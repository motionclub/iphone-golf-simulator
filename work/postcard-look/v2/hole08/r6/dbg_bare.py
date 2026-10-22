import sys
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO+"/blender/scripts"); sys.dont_write_bytecode=True
import bpy, numpy as np
from mathutils import Vector
import hole08_look as K
blend=sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.open_mainfile(filepath=blend)
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
cam=Vector(K.ARCH_CAM["pos"]); look=Vector(K.ARCH_CAM["look"])
out=[]
for j in range(80):
    py=(j+0.5)/80*1600
    if py<0.6*1600: continue
    for i in range(45):
        px=(i+0.5)/45*900
        d=K._cam_ray(cam,look,px,py,900,1600,60.0)
        ok,loc,n,idx,ob,m=sc.ray_cast(dg,cam,d,distance=900.0)
        if ok and ob.name.startswith("ROCK_OUTCROP"):
            me=ob.data; mat=me.materials[me.polygons[idx].material_index].name
            if mat.split(".")[0] in ("LK_ROCK","LK_CLIFF"):
                out.append((int(px),int(py),round(loc.z,2),tuple(round(c,2) for c in n),mat))
for o in out: print(o)
