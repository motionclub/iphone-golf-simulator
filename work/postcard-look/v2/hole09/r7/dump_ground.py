import bpy, sys
for ob in bpy.data.objects:
    if ob.type=='MESH' and ob.name.split('_')[0] in ('TERRAIN','FAIRWAY','GREEN','TEE','BUNKER','CART'):
        m=ob.data
        mats=[s.material.name if s.material else None for s in ob.material_slots]
        import collections
        c=collections.Counter(p.material_index for p in m.polygons)
        zs=[v.co.z for v in m.vertices]
        xs=[v.co.x for v in m.vertices]; ys=[v.co.y for v in m.vertices]
        print(ob.name, len(m.polygons), mats, dict(c), 'x[%.1f,%.1f] y[%.1f,%.1f] z[%.2f,%.2f]'%(min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)), [a.name for a in m.attributes][:8], [u.name for u in m.uv_layers])
