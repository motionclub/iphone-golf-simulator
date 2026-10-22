import sys, bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=sys.argv[sys.argv.index("--") + 1])
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    m = o.data
    a = m.color_attributes[0]
    print(a.name, a.data_type, a.domain, hasattr(a.data[0], "color_srgb"))
    lin = np.empty(len(a.data) * 4, dtype=np.float32); a.data.foreach_get("color", lin); lin = lin.reshape(-1, 4)
    sr = np.array([tuple(d.color_srgb) for d in a.data], dtype=np.float32)
    # per-vertex via loops
    vi = np.empty(len(m.loops), dtype=np.int32); m.loops.foreach_get("vertex_index", vi)
    for k in range(0, len(a.data), 4):
        print(" corner", k, "vert", vi[k], "linear", lin[k].round(4), "srgb", sr[k].round(4))
