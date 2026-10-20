"""blender -b --factory-startup --python noop_test.py -- <base.blend>   : which rebuild methods leave decoded corner normals untouched?"""
import sys, numpy as np, bpy, bmesh
base = sys.argv[sys.argv.index('--') + 1]
def snap():
    me = bpy.data.objects['Body_M'].data
    cn = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', cn)
    V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V)
    return cn.reshape(-1, 3), V.reshape(-1, 3)
bpy.ops.wm.open_mainfile(filepath=base)
me = bpy.data.objects['Body_M'].data; ob = bpy.data.objects['Body_M']
c0, V0 = snap()
raw = np.zeros(len(me.loops) * 2, np.int32); me.attributes['custom_normal'].data.foreach_get('value', raw)
F = [tuple(p.vertices) for p in me.polygons]
edges0 = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get('vertices', edges0)
# method 1: clear_geometry + from_pydata + restore raw
mats = [m for m in me.materials]
me.clear_geometry(); me.from_pydata([tuple(v) for v in V0.tolist()], [], F)
me.polygons.foreach_set('use_smooth', [True] * len(me.polygons)); me.update()
for m in mats:
    if m not in list(me.materials): me.materials.append(m)
a = me.attributes.new('custom_normal', 'INT16_2D', 'CORNER'); a.data.foreach_set('value', raw); me.update()
c1, _ = snap()
ang = np.degrees(np.arccos(np.clip((c0 * c1).sum(1), -1, 1)))
edges1 = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get('vertices', edges1)
print('method1 clear_geometry+from_pydata: worst', ang.max(), 'corners>0.01deg', int((ang > 0.01).sum()), 'of', len(ang), '| edge arrays equal', np.array_equal(edges0, edges1), len(edges0) // 2, len(edges1) // 2)
