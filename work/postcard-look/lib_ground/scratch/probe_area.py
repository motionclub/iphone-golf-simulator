import sys, bpy, numpy as np
from mathutils import Vector
x, y, r = [float(a) for a in sys.argv[sys.argv.index("--") + 1:]]
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith("WATER"): continue
    co = np.array([o.matrix_world @ v.co for v in o.data.vertices])
    k = np.hypot(co[:,0]-x, co[:,1]-y) < r
    if k.any():
        extra = ""
        if "Col" in o.data.color_attributes:
            a = np.array([c.color[3] for c in o.data.color_attributes["Col"].data]); extra = f" A in area {a[k].min():.2f}..{a[k].max():.2f}"
        print(o.name, o.get("surf_kind"), int(k.sum()), "verts, z", round(co[k,2].min(),3), extra)
