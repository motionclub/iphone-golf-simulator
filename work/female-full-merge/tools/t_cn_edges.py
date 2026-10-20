import bpy, numpy as np
o = bpy.data.objects['Body_F']; src = o.data
n = len(src.vertices); nl = len(src.loops); nf = len(src.polygons); ne = len(src.edges)
V = np.empty(n*3, np.float32); src.vertices.foreach_get('co', V)
cv = np.empty(nl, np.int32); src.loops.foreach_get('vertex_index', cv)
ce = np.empty(nl, np.int32); src.loops.foreach_get('edge_index', ce)
ev = np.empty(ne*2, np.int32); src.edges.foreach_get('vertices', ev)
ls = np.empty(nf, np.int32); src.polygons.foreach_get('loop_start', ls)
lt = np.empty(nf, np.int32); src.polygons.foreach_get('loop_total', lt)
mat = np.empty(nf, np.int32); src.polygons.foreach_get('material_index', mat)
uv = np.empty(nl*2, np.float32); src.uv_layers[0].data.foreach_get('uv', uv)
raw = np.empty(nl*2, np.int32); src.attributes['custom_normal'].data.foreach_get('value', raw)
cn0 = np.empty(nl*3, np.float32); src.corner_normals.foreach_get('vector', cn0)
def build(name, explicit_edges):
    new = bpy.data.meshes.new(name)
    new.vertices.add(n); new.vertices.foreach_set('co', V)
    new.loops.add(nl); new.loops.foreach_set('vertex_index', cv)
    new.polygons.add(nf); new.polygons.foreach_set('loop_start', ls); new.polygons.foreach_set('loop_total', lt)
    if explicit_edges:
        new.edges.add(ne); new.edges.foreach_set('vertices', ev); new.loops.foreach_set('edge_index', ce)
        new.update()
    else:
        new.update(calc_edges=True)
    new.polygons.foreach_set('use_smooth', np.ones(nf, bool)); new.polygons.foreach_set('material_index', mat)
    new.uv_layers.new(name='UVMap').data.foreach_set('uv', uv)
    a = new.attributes.new('custom_normal', 'INT16_2D', 'CORNER'); a.data.foreach_set('value', raw)
    new.update()
    cn1 = np.empty(nl*3, np.float32); new.corner_normals.foreach_get('vector', cn1)
    d = np.degrees(np.arccos(np.clip((cn0.reshape(-1,3)*cn1.reshape(-1,3)).sum(1), -1, 1)))
    print(name, 'explicit_edges' if explicit_edges else 'calc_edges', 'validate changed:', new.validate(verbose=False), ' max deg', float(d.max()), ' loops>0.001deg', int((d>0.001).sum()), ' bitwise-equal corner normals', bool(np.array_equal(cn0, cn1)))
    return new
build('A_calc', False); build('B_explicit', True)
# loop-order sensitivity: how are edges numbered by calc_edges vs source?
new = bpy.data.meshes.new('C'); new.vertices.add(n); new.vertices.foreach_set('co', V); new.loops.add(nl); new.loops.foreach_set('vertex_index', cv)
new.polygons.add(nf); new.polygons.foreach_set('loop_start', ls); new.polygons.foreach_set('loop_total', lt); new.update(calc_edges=True)
ev2 = np.empty(len(new.edges)*2, np.int32); new.edges.foreach_get('vertices', ev2)
k1 = set(map(tuple, np.sort(ev.reshape(-1,2),1).tolist())); k2 = set(map(tuple, np.sort(ev2.reshape(-1,2),1).tolist()))
print('same edge SET:', k1 == k2, ' same edge ORDER:', np.array_equal(np.sort(ev.reshape(-1,2),1), np.sort(ev2.reshape(-1,2),1)))
