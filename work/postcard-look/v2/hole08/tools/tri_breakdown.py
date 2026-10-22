import sys, re
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
import postcard_lib as P
class DD: pass
D = DD(); D.out_dir=None
import postcard_look_lib as L
ex = P._export_objects(DD) if False else None
objs=[o for o in bpy.data.objects if o.type=='MESH' and not any(c.name=="ASSET_LIBRARY" for c in o.users_collection)]
agg={}
for o in objs:
    o.data.calc_loop_triangles()
    t=len(o.data.loop_triangles)
    k=re.sub(r"[._]?\d+$","",o.name); k=re.sub(r"\.\d+$","",k)
    a=agg.setdefault(k,[0,0]); a[0]+=t; a[1]+=1
tot=sum(v[0] for v in agg.values())
print("TOTAL", tot)
for k,v in sorted(agg.items(), key=lambda kv:-kv[1][0])[:25]: print(f"{k:28s} {v[0]:8d} tris {v[1]:5d} objs")
