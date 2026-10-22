import bpy,pathlib,json,hashlib
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish30/forehead-check';report={}
for sex in ('Female',):
 src=O/f'{sex}_OriginalFaceFinish30Forehead.blend';bpy.ops.wm.open_mainfile(filepath=str(src));body=bpy.data.objects['Body'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST';rig.animation_data_clear()
 for ob in bpy.context.scene.objects:
  ob.select_set(ob.name in ('Body','ReferenceFeatures')or ob.type=='ARMATURE')
  if ob.type=='MESH' and ob.data.shape_keys:
   for key in ob.data.shape_keys.key_blocks:key.value=0
 bpy.context.view_layer.objects.active=body;out=O/f'{sex}_OriginalFaceFinish30Forehead.fbx';bpy.ops.export_scene.fbx(filepath=str(out),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False,path_mode='STRIP',use_armature_deform_only=False)
 report[sex]={'blend':str(src),'blendSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'fbx':str(out),'fbxSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'vertices':len(body.data.vertices),'triangles':len(body.data.polygons),'status':'broad source visually improved; actual Unity pending; eyelid operation separate'}
(O/'STAGED_EXPORT.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
