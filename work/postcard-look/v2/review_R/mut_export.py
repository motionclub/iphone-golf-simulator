import bpy, sys
args = sys.argv[sys.argv.index('--')+1:]
out, raise_obj, dz = args[0], args[1], float(args[2])
if raise_obj != 'none':
    for ob in bpy.data.objects:
        if ob.name == raise_obj or ob.name.startswith(raise_obj + '.'):
            ob.location.z += dz; print('raised', ob.name, dz)
vl = bpy.context.view_layer
for ob in vl.objects: ob.select_set(False)
n=0
for ob in vl.objects:
    if ob.type in ('MESH','EMPTY') and not ob.hide_viewport:
        try:
            ob.select_set(True); n+=1
        except Exception as e: pass
print('selected', n)
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={'MESH','EMPTY'}, axis_forward='-Z', axis_up='Y', apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_anim=False, use_mesh_modifiers=True, add_leaf_bones=False, path_mode='AUTO')
print('exported', out)
