import bpy,sys,json
from pathlib import Path
R=Path.cwd();O=R/'work/reference-rebuild/face-finish30-lids/ordered-strip1';sys.path.insert(0,str(O));from repair import repair
report={}
for sex in ['Male','Female']:
 source=R/f'work/reference-rebuild/face-finish30/ears/{sex}_OriginalFaceFinish30Ears.blend';bpy.ops.wm.open_mainfile(filepath=str(source));body=bpy.data.objects['Body'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST';rig.animation_data_clear();report[sex]=repair(body,sex)
 bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{sex}_Face30OrderedLids.blend'))
 for ob in bpy.context.scene.objects:ob.select_set(ob.name in ['Body','ReferenceFeatures']or ob.type=='ARMATURE')
 bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.fbx(filepath=str(O/f'{sex}_Face30OrderedLids.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False,path_mode='STRIP',use_armature_deform_only=False)
 print('STRIP_REPORT',report[sex],flush=True)
(O/'SOURCE_REPORT.json').write_text(json.dumps(report,indent=2))
