import bpy, sys, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=sys.argv[-1])
ms=[o for o in bpy.data.objects if o.type=='MESH']
print('meshes',len(ms))
at0=[(o.name,o.hide_viewport,o.hide_render) for o in ms if o.name.startswith(('PLANT','ROCK','DRESS')) and o.matrix_world.translation.length<0.5]
print('prop objs within 0.5m of origin:',len(at0),at0[:12])
print('hidden',sum(o.hide_viewport for o in ms))
tri=0
for o in ms:
    o.data.calc_loop_triangles(); tri+=len(o.data.loop_triangles)
print('tris',tri)
# tallest / scales
mats=set(m.name for o in ms for m in o.data.materials); print(sorted(mats))
