import bpy, numpy as np
# Test 1: from-scratch mesh + attributes.new('custom_normal')
me = bpy.data.meshes.new('t'); me.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0.5,0.5,0.8)], [], [(0,1,2,3)]); me.update()
try:
    a = me.attributes.new('custom_normal', 'INT16_2D', 'CORNER'); print('CREATE_OK', a.name, a.data_type, a.domain, 'has_custom_normals=', me.has_custom_normals)
except Exception as e: print('CREATE_ERR', repr(e))
# Test 2: take the real base Body_F, rebuild from arrays (no edits), compare computed corner normals, raw codes, uv, mats
o = bpy.data.objects['Body_F']; src = o.data
n = len(src.vertices); nl = len(src.loops); nf = len(src.polygons)
V = np.empty(n*3, np.float32); src.vertices.foreach_get('co', V)
cv = np.empty(nl, np.int32); src.loops.foreach_get('vertex_index', cv)
ls = np.empty(nf, np.int32); src.polygons.foreach_get('loop_start', ls)
lt = np.empty(nf, np.int32); src.polygons.foreach_get('loop_total', lt)
assert (np.diff(ls) == lt[:-1]).all() and ls[0] == 0, 'loops not contiguous in face order'
mat = np.empty(nf, np.int32); src.polygons.foreach_get('material_index', mat)
uv = np.empty(nl*2, np.float32); src.uv_layers[0].data.foreach_get('uv', uv)
raw = np.empty(nl*2, np.int32); src.attributes['custom_normal'].data.foreach_get('value', raw)
cn0 = np.empty(nl*3, np.float32); src.corner_normals.foreach_get('vector', cn0)
new = bpy.data.meshes.new('Body_F_rebuild')
new.vertices.add(n); new.vertices.foreach_set('co', V)
new.loops.add(nl); new.loops.foreach_set('vertex_index', cv)
new.polygons.add(nf); new.polygons.foreach_set('loop_start', ls); new.polygons.foreach_set('loop_total', lt)
new.update(calc_edges=True)
print('edges', len(new.edges), 'orig', len(src.edges))
new.polygons.foreach_set('use_smooth', np.ones(nf, bool)); new.polygons.foreach_set('material_index', mat)
new.uv_layers.new(name='UVMap').data.foreach_set('uv', uv)
try:
    a = new.attributes.new('custom_normal', 'INT16_2D', 'CORNER'); a.data.foreach_set('value', raw); print('rebuild: custom_normal created')
except Exception as e:
    print('rebuild create err', repr(e))
new.update()
print('validate (True = it changed something):', new.validate(verbose=True))
cn1 = np.empty(nl*3, np.float32); new.corner_normals.foreach_get('vector', cn1)
d = np.degrees(np.arccos(np.clip((cn0.reshape(-1,3)*cn1.reshape(-1,3)).sum(1), -1, 1)))
print('CORNER NORMAL rebuild vs source: max deg', float(d.max()), ' loops >0.001deg:', int((d>0.001).sum()), ' has_custom_normals', new.has_custom_normals)
raw2 = np.empty(nl*2, np.int32); new.attributes['custom_normal'].data.foreach_get('value', raw2); print('raw identical:', np.array_equal(raw, raw2))
