import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
ob=bpy.data.objects["DRESS_PATH_01"]
V=np.array([v.co[:] for v in ob.data.vertices])
tb=bpy.data.objects["TEE_BOX"]; T=np.array([v.co[:] for v in tb.data.vertices])
# tee outline: x,y of tee vertices on the front (y>2.5)
front=sorted([(round(x,2),round(y,2)) for x,y,z in T if y>2.0])
print("TEEFRONT",front)
# path vertices with |x|<-1.9.. along y: for columns x in [-1.5,-1.35] print y,z
sel=V[(V[:,0]>-1.55)&(V[:,0]<-1.30)&(V[:,1]>2.4)&(V[:,1]<4.8)]
sel=sel[np.argsort(sel[:,1])]
for p in sel: print("PV %.3f %.3f %.4f"%tuple(p))
