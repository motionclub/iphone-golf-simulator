# usage: Blender -b --factory-startup --python uv_bad.py -- <blend> <objname> [ratio]
import bpy, sys
import numpy as np
args = sys.argv[sys.argv.index('--') + 1:]
blend, name = args[0], args[1]
th = float(args[2]) if len(args) > 2 else 2.0
bpy.ops.wm.open_mainfile(filepath=blend)
o = bpy.data.objects[name]; me = o.data; uv = me.uv_layers.active.data
M = np.array(o.matrix_world)[:3, :3]; T = np.array(o.matrix_world)[:3, 3]
me.calc_loop_triangles(); bad = []
for t in me.loop_triangles:
    p = [M @ np.array(me.vertices[i].co) + T for i in t.vertices]; u = [np.array(uv[l].uv) for l in t.loops]
    e1, e2 = p[1] - p[0], p[2] - p[0]; d1, d2 = u[1] - u[0], u[2] - u[0]
    a3 = np.linalg.norm(np.cross(e1, e2)) / 2
    if a3 < 1e-9: continue
    Muv = np.array([[d1[0], d2[0]], [d1[1], d2[1]]]); det = np.linalg.det(Muv)
    if abs(det) < 1e-12: r = 999999.0
    else:
        s = np.linalg.svd(np.stack([e1, e2], 1) @ np.linalg.inv(Muv), compute_uv=False); r = s[0] / max(s[1], 1e-9)
    if r > th: bad.append((r, a3, (p[0] + p[1] + p[2]) / 3, u[0], u[1], u[2], t.polygon_index, tuple(t.vertices)))
print(name, 'tris', len(me.loop_triangles), 'polys', len(me.polygons), 'verts', len(me.vertices), 'bad(>%g)' % th, len(bad), 'bad area %.0f m2' % sum(b[1] for b in bad))
for b in sorted(bad, key=lambda b: -b[1])[:12]:
    print('r %.1f area %.1f m2 at (%.1f, %.1f, %.2f) poly %d verts %s uv0 %s uv1 %s uv2 %s' % (min(b[0], 9999), b[1], b[2][0], b[2][1], b[2][2], b[6], b[7], np.round(b[3], 3), np.round(b[4], 3), np.round(b[5], 3)))
