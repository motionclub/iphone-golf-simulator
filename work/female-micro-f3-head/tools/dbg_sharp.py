import sys, bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
for nm in ('Body_F', 'Face_F'):
    me = bpy.data.objects[nm].data
    sm = np.array([p.use_smooth for p in me.polygons])
    print(nm, 'polys', len(me.polygons), 'smooth', int(sm.sum()), 'flat', int((~sm).sum()), 'has_custom', me.has_custom_normals, 'attrs', [a.name for a in me.attributes])
    if nm == 'Face_F':
        mi = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi)
        mats = [m.name for m in me.materials]
        for k, m in enumerate(mats):
            sel = mi == k
            if sel.any(): print('   ', m, int(sel.sum()), 'flat', int((~sm[sel]).sum()))
print('uv layers Body_F', [l.name for l in bpy.data.objects['Body_F'].data.uv_layers], 'Face_F', [l.name for l in bpy.data.objects['Face_F'].data.uv_layers])
