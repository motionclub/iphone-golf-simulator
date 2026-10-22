import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, numpy as np, bmesh
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
ob=bpy.data.objects["DRESS_PATH_01"]
bm=bmesh.new(); bm.from_mesh(ob.data)
b={v.index for e in bm.edges if len(e.link_faces)==1 for v in e.verts}
V=np.array([v.co[:] for v in bm.verts])
for y0 in np.arange(-2,8,0.4):
    sel=[i for i in b if y0<=V[i,1]<y0+0.4]
    xs=sorted(V[i,0] for i in sel)
    print("y %.1f..%.1f boundary x range"%(y0,y0+0.4), (round(xs[0],2), round(xs[-1],2)) if xs else None, "n",len(xs), "z",sorted({round(V[i,2],3) for i in sel})[:3])
print("path UV layer", ob.data.uv_layers.keys())
