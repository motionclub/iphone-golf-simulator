import sys, bpy, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
me = bpy.data.objects['Face_F'].data
mi = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi)
mats = [m.name for m in me.materials]
print('last 1136 polys material sequence (run-length):')
seq = [mats[k] for k in mi[-1136:]]
runs = []; prev = None
for s in seq:
    if s == prev: runs[-1][1] += 1
    else: runs.append([s, 1]); prev = s
print(runs)
print('first new poly loop_start', me.polygons[len(me.polygons) - 1136].loop_start, 'of total loops', len(me.loops))
p = me.polygons[len(me.polygons) - 1136]
print('poly verts', list(p.vertices), 'loop vertex ids', [me.loops[l].vertex_index for l in range(p.loop_start, p.loop_start + p.loop_total)])
# compare corner normals vs face normal on a Seam strip poly (should have ~0 tilt)
cn = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
for k in (0, 200, 600, 1000, 1100):
    p = me.polygons[len(me.polygons) - 1136 + k]
    print(k, mats[p.material_index], 'face n', np.round(p.normal, 2), 'corner n', [tuple(np.round(cn[l], 2)) for l in range(p.loop_start, p.loop_start + p.loop_total)])
