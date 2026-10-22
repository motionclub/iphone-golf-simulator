"""UV density / anisotropy of the ground meshes of an installed postcard hole (Blender headless, numpy in Blender's python).
usage: Blender -b --factory-startup --python uv_ground.py -- <8|9|10> [blend|fbx]
Per object (FAIRWAY / GREEN / TEE_BOX / TERRAIN* / BUNKER / CART_PATH): triangles, area-weighted share of triangles whose UV->3D Jacobian has a singular-value ratio > 2 / > 4,
p95 and max of the ratio, and the area-weighted median texel scale (metres of ground per UV unit, s_max and s_min).
"""
import bpy, sys, os
import numpy as np
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
args = sys.argv[sys.argv.index('--') + 1:]
n = args[0]; src = args[1] if len(args) > 1 else 'blend'
if src == 'blend':
    bpy.ops.wm.open_mainfile(filepath=R + f'blender/hole_{int(n):02d}.blend')
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=R + f'Unity/Assets/Resources/Course/hole_{int(n):02d}.fbx')
PRE = ('FAIRWAY', 'GREEN', 'TEE_BOX', 'TERRAIN', 'BUNKER', 'CART_PATH')
print('hole', n, src)
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    if o.type != 'MESH' or not o.name.startswith(PRE): continue
    me = o.data
    if not me.uv_layers:
        print(o.name, 'NOUV'); continue
    uv = me.uv_layers.active.data
    M = np.array(o.matrix_world)[:3, :3]
    me.calc_loop_triangles()
    ratios = []; areas = []; smax = []; smin = []
    for t in me.loop_triangles:
        p = [M @ np.array(me.vertices[i].co) for i in t.vertices]
        u = [np.array(uv[l].uv) for l in t.loops]
        e1, e2 = p[1] - p[0], p[2] - p[0]; d1, d2 = u[1] - u[0], u[2] - u[0]
        a3 = np.linalg.norm(np.cross(e1, e2)) / 2
        if a3 < 1e-9: continue
        Muv = np.array([[d1[0], d2[0]], [d1[1], d2[1]]])
        det = np.linalg.det(Muv)
        if abs(det) < 1e-12:
            ratios.append(999.0); areas.append(a3); smax.append(0); smin.append(0); continue
        Pm = np.stack([e1, e2], 1) @ np.linalg.inv(Muv)
        s = np.linalg.svd(Pm, compute_uv=False)
        ratios.append(s[0] / max(s[1], 1e-9)); areas.append(a3); smax.append(s[0]); smin.append(s[1])
    if not ratios: continue
    A = np.array(ratios); W = np.array(areas); SM = np.array(smax); sm = np.array(smin)
    def wmed(x):
        i = np.argsort(x); c = np.cumsum(W[i]); return float(x[i][np.searchsorted(c, c[-1] / 2)])
    big = A > 4
    extra = '  [r>4: %d tris, %.1f m2, largest %.1f m2, worst ratio %.1f]' % (int(big.sum()), float(W[big].sum()), float(W[big].max()) if big.any() else 0.0, float(min(A.max(), 9999)))
    print('%-24s tris %6d  area %9.0f m2  ratio>2 %5.1f %%  >4 %5.1f %%  p95 %6.2f  max %7.1f  m/UV: max %7.2f min %7.2f (median)'
          % (o.name, len(A), W.sum(), 100 * float(np.average(A > 2, weights=W)), 100 * float(np.average(A > 4, weights=W)), float(np.percentile(A, 95)), float(A.max()), wmed(SM), wmed(sm)) + extra)
