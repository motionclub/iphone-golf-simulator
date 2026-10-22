import bpy, sys, os
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
sys.dont_write_bytecode = True
import hole10_look as HL
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0])
ob = bpy.data.objects["FAIRWAY_FIRSTCUT"]
W, tv, tl, uv0 = HL.mesh_tris_uv(ob)
uv0 = uv0.copy()
r = HL.unfold_sliver_uv(ob, 10.0)
print("R", r)
W, tv, tl, uv1 = HL.mesh_tris_uv(ob)
ch = np.nonzero(np.abs(uv1 - uv0).max(axis=1) > 1e-9)[0]
loops_changed = ch
print("loops changed", len(ch))
for t in range(len(tv)):
    d = np.abs(uv1[tl[t]] - uv0[tl[t]]).max(axis=1)
    if d.max() > 1e-9:
        print("tri", t, "verts", tv[t].tolist(), "move of each vertex UV (m):", np.round(np.hypot(*(uv1[tl[t]] - uv0[tl[t]]).T) * 10.0, 2).tolist(), "world", np.round(W[tv[t]][:, :2], 1).tolist())
