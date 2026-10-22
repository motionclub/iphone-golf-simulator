import bpy, numpy as np, json
for cw in ('White', 'Black'):
    for k in ('Shoe', 'Sock'):
        o = bpy.data.objects[f'Kit_{k}_R_{cw}']
        mi = np.zeros(len(o.data.polygons), np.int32); o.data.polygons.foreach_get('material_index', mi)
        tv = np.zeros(len(o.data.polygons), np.int32); o.data.attributes['kit_tag'].data.foreach_get('value', tv)
        tg = json.loads(o.data['kit_tagnames'])
        print(cw, k, [m.name for m in o.data.materials], 'faces per slot', np.bincount(mi).tolist(), 'slot1 tags:', sorted({tg[t] for t in tv[mi == 1]}))
