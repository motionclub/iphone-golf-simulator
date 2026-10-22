import bpy, sys
import numpy as np
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
args = sys.argv[sys.argv.index('--') + 1:]; n = args[0]; name = args[1]
bpy.ops.wm.open_mainfile(filepath=R + f'blender/hole_{int(n):02d}.blend')
o = bpy.data.objects[name]; me = o.data; uv = me.uv_layers.active.data; M = np.array(o.matrix_world)[:3, :3]; T = np.array(o.matrix_world)[:3, 3]
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
    if r > 2: bad.append((r, a3, (p[0] + p[1] + p[2]) / 3, u[0], u[1], u[2]))
print(name, 'bad tris', len(bad), 'of', len(me.loop_triangles), 'bad area %.0f m2' % sum(b[1] for b in bad))
C = np.array([b[2] for b in bad]); Aa = np.array([b[1] for b in bad])
print('centroid x range %.1f..%.1f  y range %.1f..%.1f (blender m); in yards x %.1f..%.1f d %.1f..%.1f' % (C[:,0].min(), C[:,0].max(), C[:,1].min(), C[:,1].max(), C[:,0].min()*1.0936, C[:,0].max()*1.0936, C[:,1].min()*1.0936, C[:,1].max()*1.0936))
# coarse grid of bad area (20 m cells)
cells = {}
for b in bad:
    k = (int(b[2][0] // 20) * 20, int(b[2][1] // 20) * 20); cells[k] = cells.get(k, 0) + b[1]
for k, v in sorted(cells.items(), key=lambda kv: -kv[1])[:12]: print('cell x%5d y%5d  bad area %7.1f m2' % (k[0], k[1], v))
for b in sorted(bad, key=lambda b: -b[1])[:8]: print('r %.1f area %.1f m2 at (%.1f, %.1f, %.1f) uv0 %s uv1 %s uv2 %s' % (min(b[0], 9999), b[1], b[2][0], b[2][1], b[2][2], np.round(b[3], 3), np.round(b[4], 3), np.round(b[5], 3)))
