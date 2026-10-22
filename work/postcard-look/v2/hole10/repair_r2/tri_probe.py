import bpy, sys, math
import numpy as np
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0])
o = bpy.data.objects["FAIRWAY_FIRSTCUT"]; me = o.data; lay = me.uv_layers.active.data
for pi in (641, 640, 477, 343):
    p = me.polygons[pi]
    idx = list(p.loop_indices)
    P = np.array([list(me.vertices[me.loops[l].vertex_index].co) for l in idx])
    U = np.array([lay[l].uv[:] for l in idx]) * 10.0
    print('poly', pi, 'verts', [me.loops[l].vertex_index for l in idx])
    for i in range(3):
        j = (i + 1) % 3
        print('  edge', i, j, 'world %.1f m' % np.hypot(*(P[i, :2] - P[j, :2])), 'uv %.1f m' % np.hypot(*(U[i] - U[j])), 'P', np.round(P[i], 1), 'UV m', np.round(U[i], 1))
