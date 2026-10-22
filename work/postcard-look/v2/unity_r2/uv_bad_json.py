import bpy, sys, json
import numpy as np
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
args = sys.argv[sys.argv.index('--') + 1:]; n, name, out = args[0], args[1], args[2]
bpy.ops.wm.open_mainfile(filepath=R + f'blender/hole_{int(n):02d}.blend')
o = bpy.data.objects[name]; me = o.data; uv = me.uv_layers.active.data
M = np.array(o.matrix_world)[:3, :3]; T = np.array(o.matrix_world)[:3, 3]
me.calc_loop_triangles(); res = []
for t in me.loop_triangles:
    p = [M @ np.array(me.vertices[i].co) + T for i in t.vertices]; u = [np.array(uv[l].uv) for l in t.loops]
    e1, e2 = p[1] - p[0], p[2] - p[0]; d1, d2 = u[1] - u[0], u[2] - u[0]
    a3 = float(np.linalg.norm(np.cross(e1, e2)) / 2)
    if a3 < 1e-9: continue
    det = d1[0] * d2[1] - d2[0] * d1[1]
    if abs(det) < 1e-12: r = 1e3
    else:
        Pu = (e1 * d2[1] - e2 * d1[1]) / det; Pv = (e2 * d1[0] - e1 * d2[0]) / det
        g = np.array([[Pu @ Pu, Pu @ Pv], [Pu @ Pv, Pv @ Pv]]); w = np.linalg.eigvalsh(g); r = float(np.sqrt(w[1] / max(w[0], 1e-30)))
    # unity yards: x = bx*1.0936, y = bz*1.0936, z = by*1.0936
    res.append(dict(ratio=min(r, 1e3), area=a3, verts=[[float(q[0] * 1.0936), float(q[2] * 1.0936), float(q[1] * 1.0936)] for q in p]))
json.dump(res, open(out, 'w'))
print('wrote', len(res), 'triangles', sum(1 for r in res if r['ratio'] > 4), 'with ratio > 4')
