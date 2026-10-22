import bpy, sys, numpy as np
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import postcard_lib as P
bpy.ops.wm.open_mainfile(filepath="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole09/stage/hole_09.blend")
D = P.start("hole09_design", out_dir="/tmp/x") if False else None
rows=[]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith("ROCK_") and "_WET" in o.name:
        Wv=np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices])
        rows.append((o.name, Wv[:,2].min(), Wv[:,2].max(), o.location.z, tuple(round(s,2) for s in o.scale)))
print(len(rows))
for r in rows[:12]: print(r)
