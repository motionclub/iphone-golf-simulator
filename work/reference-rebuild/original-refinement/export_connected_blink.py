import bpy,pathlib
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/original-refinement'
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_OriginalSeamBlink.blend'));sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1.0
 for ob in sc.objects:ob.select_set(ob.name in ('Body','ReferenceFeatures') or ob.type=='ARMATURE')
 bpy.context.view_layer.objects.active=bpy.data.objects['Body']
 bpy.ops.export_scene.fbx(filepath=str(O/f'{sex}_OriginalSeamBlink.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False,path_mode='STRIP',use_armature_deform_only=False)
 print('ORIGINAL_SEAM_EXPORT',sex,len(bpy.data.objects['Body'].data.vertices),len(bpy.data.objects['ReferenceFeatures'].data.vertices))
