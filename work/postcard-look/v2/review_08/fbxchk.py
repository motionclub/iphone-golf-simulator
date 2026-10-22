import bpy, collections, numpy as np
bpy.ops.import_scene.fbx(filepath='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole08/stage/hole_08.fbx')
c=collections.Counter(); tri=0
for o in bpy.data.objects:
    if o.type=='MESH':
        c[o.name.split('.')[0][:14]]+=1
        tri+=sum(len(p.vertices)-2 for p in o.data.polygons)
print(len(bpy.data.objects),tri)
at=[o.name for o in bpy.data.objects if o.type=='MESH' and abs(o.matrix_world.translation.x)<1e-6 and abs(o.matrix_world.translation.y)<1e-6 and o.name.startswith('PLANT')]
print('PLANT at origin in FBX',at)
print({o.name for o in bpy.data.objects if o.type=='EMPTY'})
mats=collections.Counter(m.name for m in bpy.data.materials); print(mats)
