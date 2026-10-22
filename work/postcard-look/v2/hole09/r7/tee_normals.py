import bpy, numpy as np, sys
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
bpy.ops.import_scene.fbx(filepath='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole09/stage/hole_09.fbx')
for ob in bpy.data.objects:
    if ob.type=='MESH' and ob.name.split('.')[0] in ('TEE_BOX','FAIRWAY'):
        me=ob.data
        me.calc_loop_triangles()
        try:
            ln=np.array([l.normal[:] for l in me.loops])
        except Exception as e:
            ln=None
        pn=np.array([p.normal[:] for p in me.polygons])
        print(ob.name, 'polys',len(me.polygons), 'poly normal z min/max', pn[:,2].min(), pn[:,2].max(), 'has_custom', me.has_custom_normals)
        if ln is not None:
            up=[]
            for p in me.polygons:
                if p.normal.z>0.9:
                    for li in p.loop_indices: up.append(ln[li])
            up=np.array(up); print('  loop normals on up polys: z min', up[:,2].min(), 'max',up[:,2].max(), 'xy abs max', np.abs(up[:,:2]).max())
        print('  uv layers', [u.name for u in me.uv_layers], 'tris', len(me.loop_triangles))
