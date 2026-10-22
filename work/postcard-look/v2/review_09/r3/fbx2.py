import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=sys.argv[-1])
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith(('PLANT_','DRESS_BLOCK','ROCK_')) and o.matrix_world.translation.length<1e-3 and 'SURF' not in o.name and not o.name.startswith('ROCK_SKIN'):
        print(o.name,'hide_vp',o.hide_viewport,'hide_render',o.hide_render,'hide_get',o.hide_get() if bpy.context.view_layer.objects.get(o.name) else None, tuple(round(x,2) for x in o.dimensions), 'verts',len(o.data.vertices))
