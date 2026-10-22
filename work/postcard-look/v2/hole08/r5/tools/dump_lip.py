import sys, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
ob=bpy.data.objects["BUNKER_01_LIP"]; me=ob.data
print("polys",len(me.polygons),"verts",len(me.vertices),"smooth",[p.use_smooth for p in me.polygons][:5], "mats",[m.name for m in me.materials])
lay=me.uv_layers.active.data
import postcard_look_lib as L
print("UV_WARP", L.UV_WARP)
rows=[]
for p in me.polygons:
    idx=list(range(p.loop_start,p.loop_start+p.loop_total))
    V=np.array([me.vertices[me.loops[i].vertex_index].co for i in idx]); U=np.array([lay[i].uv for i in idx])
    # jacobian by least squares: U = A [x y] + b
    A=np.c_[V[:,0],V[:,1],np.ones(len(V))]
    sol,res,_,_=np.linalg.lstsq(A,U,rcond=None)
    J=sol[:2].T   # 2x2: du/dx du/dy; dv/dx dv/dy
    det=np.linalg.det(J)
    ang=math.degrees(math.atan2(J[1,0],J[0,0]))
    c=V.mean(0)
    rows.append((round(c[0],1),round(c[1],1),round(c[2],2),round(p.normal.z,2),round(det*36,2),round(ang,1)))
for r in sorted(rows)[:70]: print("LIP",r)
