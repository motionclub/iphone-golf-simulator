import bpy, sys, numpy as np
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import postcard_lib as P
D = P.start("hole09_design", out_dir="/tmp/dbg9")
bpy.ops.wm.open_mainfile(filepath="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole09/stage/hole_09.blend")
D = P._ST["D"]
bpy.data.objects["TERRAIN_SPLIT"]
D.terrain = bpy.data.objects["TERRAIN_SPLIT"]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith("ROCK_") and "_WET" in o.name and o.location.z > -0.2:
        Wv=np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices])
        c2=Wv[:,:2].mean(0)
        try:
            sd=float(P.signed_dist_m(D, np.array([c2[0]]), np.array([c2[1]]))[0])
        except Exception as e:
            sd=str(e)
        print(o.name, round(Wv[:,2].min(),2), round(Wv[:,2].max(),2), sd)
