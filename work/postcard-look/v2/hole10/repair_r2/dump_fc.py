import bpy, sys, json
import numpy as np
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0])
out = {}
for name in ("FAIRWAY_FIRSTCUT", "FAIRWAY", "TEE_BOX", "GREEN", "GREEN_APRON", "BUNKER_01", "BUNKER_02"):
    o = bpy.data.objects[name]; me = o.data
    M = np.array(o.matrix_world)
    co = np.array([M @ np.array([*v.co, 1.0]) for v in me.vertices])[:, :3]
    out[name] = dict(co=co.tolist(), polys=[list(p.vertices) for p in me.polygons], mats=[p.material_index for p in me.polygons])
json.dump(out, open(args[1], 'w'))
print("ok", {k: (len(v['co']), len(v['polys'])) for k, v in out.items()})
