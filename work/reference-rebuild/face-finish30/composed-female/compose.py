import bpy,pathlib,json,hashlib,importlib.util
R=pathlib.Path.cwd();B=R/'work/reference-rebuild/face-finish30/final';O=R/'work/reference-rebuild/face-finish30/composed-female';report={};sp=importlib.util.spec_from_file_location('lids',R/'work/reference-rebuild/face-finish30-lids/apply-lids.py');mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(B/f'{sex}_OriginalFaceFinish30Final.blend'));body=bpy.data.objects['Body'];op=mod.apply_lids(body,sex)if sex=='Female'else{'sex':sex,'eyelids':'accepted Smooth1/eye13 unchanged; male operation pending'};rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST';rig.animation_data_clear();blend=O/f'{sex}_OriginalFaceFinish30Composed.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
 for ob in bpy.context.scene.objects:
  ob.select_set(ob.name in ('Body','ReferenceFeatures')or ob.type=='ARMATURE')
  if ob.type=='MESH'and ob.data.shape_keys:
   for key in ob.data.shape_keys.key_blocks:key.value=0
 bpy.context.view_layer.objects.active=body;fbx=O/f'{sex}_OriginalFaceFinish30Composed.fbx';bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False,path_mode='STRIP',use_armature_deform_only=False)
 report[sex]={'source':str(B/f'{sex}_OriginalFaceFinish30Final.blend'),'blend':str(blend),'blendSha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'fbx':str(fbx),'fbxSha256':hashlib.sha256(fbx.read_bytes()).hexdigest(),'bodyVertices':len(body.data.vertices),'bodyTriangles':len(body.data.polygons),'operation':op,'femaleEyeOperationSha256':hashlib.sha256((R/'work/reference-rebuild/face-finish30-lids/female-operation.npz').read_bytes()).hexdigest()if sex=='Female'else None};print(report[sex],flush=True)
(O/'STAGED_EXPORT.json').write_text(json.dumps(report,indent=2)+'\n')
