import sys, os
sys.dont_write_bytecode = True
import numpy as np, bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
for o in bpy.data.objects:
    if o.name.startswith("TERRAIN"):
        Z = np.array([v.co.z for v in o.data.vertices])
        u = np.unique(np.round(Z, 2))
        print(o.name, len(Z), "unique z:", u.tolist()[:60])
