import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/export/StandardKit_Male.blend')
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.endswith('_Black'):
        idx = np.zeros(len(o.data.polygons), np.int32); o.data.polygons.foreach_get('material_index', idx)
        print(o.name, "slots", [m.name for m in o.data.materials], "faces slot1:", int((idx==1).sum()), "slot0:", int((idx==0).sum()))
