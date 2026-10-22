import bpy,sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=sys.argv[-1])
n=0
for o in bpy.data.objects:
    if o.type=='MESH' and o.matrix_world.translation.length<1e-6: print(o.name,tuple(o.dimensions)); n+=1
print('origin objs',n, 'total',len([o for o in bpy.data.objects if o.type=='MESH']))
