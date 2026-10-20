import bpy, numpy as np, json
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-parallel-limbs/export/HeroBase_Female_Body_limbs.fbx')
ms=[o for o in bpy.data.objects if o.type=='MESH']
for o in ms:
    me=o.data; n=len(me.vertices); co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); V=co.reshape(-1,3)
    M=np.array(o.matrix_world); Vw=(V@M[:3,:3].T)+M[:3,3]
    me.calc_loop_triangles()
    json.dump({'verts':n,'tris':len(me.loop_triangles),'height':float(Vw[:,2].max()-Vw[:,2].min()),'materials':[m.name for m in me.materials],'scale':list(o.scale),'custom_normals':bool(me.has_custom_normals)},open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-parallel-limbs/data/fbx_verify.json','w'))
    print(o.name,'verts',n,'tris',len(me.loop_triangles),'scale',tuple(round(x,4) for x in o.scale),'mats',[m.name for m in me.materials],'bbox min',Vw.min(0).round(4),'max',Vw.max(0).round(4),'height',round(float(Vw[:,2].max()-Vw[:,2].min()),5),'custom normals',me.has_custom_normals)
