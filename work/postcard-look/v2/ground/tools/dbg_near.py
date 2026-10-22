import sys, numpy as np, bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
x0, y0 = float(sys.argv[sys.argv.index("--")+2]), float(sys.argv[sys.argv.index("--")+3])
for o in bpy.data.objects:
    if o.name.startswith("WATER_SURF"):
        W = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
        c = W[:, :2].mean(0)
        if np.hypot(c[0]-x0, c[1]-y0) < 25:
            print(o.name, "center", c.round(1), "extent", (W[:, :2].max(0)-W[:, :2].min(0)).round(1), o.get("surf_kind"))
