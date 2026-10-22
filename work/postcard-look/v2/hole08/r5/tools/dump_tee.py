import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, numpy as np
from mathutils import Vector
import postcard_lib as P
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
for n in ("TEE_BOX","FAIRWAY","FAIRWAY_FIRSTCUT","TERRAIN_NEEDLE","GREEN","GREEN_APRON","BUNKER_01","BUNKER_01_LIP","DRESS_PATH_00","DRESS_PATH_01","CART_PATH"):
    ob=bpy.data.objects.get(n)
    if not ob: print(n,"MISSING"); continue
    V=np.array([ob.matrix_world@v.co for v in ob.data.vertices])
    print(n, len(V), "z range %.3f..%.3f"%(V[:,2].min(),V[:,2].max()), "x %.2f..%.2f y %.2f..%.2f"%(V[:,0].min(),V[:,0].max(),V[:,1].min(),V[:,1].max()), "mats",[m.name if m else None for m in ob.data.materials], "uv",ob.data.uv_layers.keys(), "polys",len(ob.data.polygons))
ob=bpy.data.objects["TEE_BOX"]
V=np.array([ob.matrix_world@v.co for v in ob.data.vertices])
# boundary of tee box
import bmesh
bm=bmesh.new(); bm.from_mesh(ob.data)
b=[e for e in bm.edges if len(e.link_faces)==1]
print("tee boundary edges",len(b))
pts=sorted({(round(v.co.x,2),round(v.co.y,2),round(v.co.z,3)) for e in b for v in e.verts}, key=lambda p:(p[1],p[0]))
print(pts[:5], pts[-5:])
print("y max of tee", V[:,1].max())
# heights of fairway near tee: ray cast
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
for y in (-4,-2,0,2,4,5,6,7,8,9,10,12):
    row=[]
    for x in (-3,0,3):
        ok,loc,nrm,idx,o,mw=sc.ray_cast(dg,Vector((x,y,20)),Vector((0,0,-1)),distance=80)
        row.append((o.name if ok else None, round(loc.z,3) if ok else None))
    print(y,row)
