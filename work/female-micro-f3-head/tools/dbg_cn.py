import sys, bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
fo = bpy.data.objects['Face_F']; me = fo.data
print('has_custom_normals', me.has_custom_normals, 'loops', len(me.loops), 'polys', len(me.polygons))
mi = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get('material_index', mi)
mats = [m.name for m in me.materials]
V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
cn = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
sm = np.array([p.use_smooth for p in me.polygons])
print('smooth polys', int(sm.sum()), 'flat', int((~sm).sum()))
for name in ('Face_LipUp', 'Face_Lip', 'Face_Seam'):
    k = mats.index(name); polys = [p for p in me.polygons if p.material_index == k]
    # corner normals of loops of these polys: compare with the face normal
    angs = []
    for p in polys[:2000]:
        ls = list(range(p.loop_start, p.loop_start + p.loop_total))
        for l in ls: angs.append(np.degrees(np.arccos(np.clip(np.dot(cn[l], np.array(p.normal)), -1, 1))))
    print(name, 'polys', len(polys), 'angle(corner normal, face normal): mean %.1f max %.1f' % (np.mean(angs), np.max(angs)), 'smooth', all(p.use_smooth for p in polys))
