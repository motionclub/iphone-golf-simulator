import bpy, sys
out, obj, dx, dy, dz = sys.argv[sys.argv.index('--')+1:][:5]
dx,dy,dz=float(dx),float(dy),float(dz)
hit=0
for ob in bpy.data.objects:
    if ob.name==obj or ob.name.startswith(obj+'.'):
        ob.location.x+=dx; ob.location.y+=dy; ob.location.z+=dz; hit+=1
print('moved',hit,obj)
vl=bpy.context.view_layer
for ob in vl.objects: ob.select_set(False)
for ob in vl.objects:
    if ob.type in ('MESH','EMPTY') and not ob.hide_viewport:
        try: ob.select_set(True)
        except: pass
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={'MESH','EMPTY'}, axis_forward='-Z', axis_up='Y', apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_anim=False, use_mesh_modifiers=True, add_leaf_bones=False, path_mode='AUTO')
