import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
for pre in ("DRESS_ARCH","DRESS_RUIN"):
    P=np.vstack([np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices]) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(pre)])
    print(pre,"min",P.min(0).round(2),"max",P.max(0).round(2),"center",P.mean(0).round(2), "yd", (P.mean(0)/0.9144).round(2))
