import bpy, sys, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
for o in bpy.data.objects:
    if o.type!='MESH' or o.name.startswith(("DRESS_RUIN","DRESS_ARCH","TERRAIN","ROCK_SKIN","WATER")): continue
    co=np.array([tuple(v.co) for v in o.data.vertices]); 
    if len(co)==0: continue
    W=co@np.array(o.matrix_world)[:3,:3].T+np.array(o.matrix_world)[:3,3]
    if W[:,2].max()>9.0 and abs(W[:,0].mean()+60)<15 and abs(W[:,1].mean()-100)<20:
        print("TALL", o.name, W.min(0).round(1).tolist(), W.max(0).round(1).tolist(), [m.name for m in o.data.materials])
