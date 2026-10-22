import bpy, collections, sys
c = collections.defaultdict(lambda: collections.Counter())
for ob in bpy.data.objects:
    if ob.type != 'MESH': continue
    pre = ob.name.split('_')[0] + '_' + (ob.name.split('_')[1] if '_' in ob.name else '')
    for sl in ob.material_slots:
        c[pre][sl.material.name if sl.material else 'None'] += 1
for k in sorted(c): print(k, dict(c[k]))
