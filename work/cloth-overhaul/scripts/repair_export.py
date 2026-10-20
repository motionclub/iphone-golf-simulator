import bpy,sys
from pathlib import Path
R=Path(sys.argv[sys.argv.index('--')+1]);W=R/'work/cloth-overhaul'
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(W/f'export/Cloth_{sex}.blend'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');kit=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.endswith('_High')]
 for o in kit:
  mod=next((m for m in o.modifiers if m.type=='ARMATURE'),None)
  if mod is None:mod=o.modifiers.new('ExistingRig','ARMATURE');mod.object=rig
 bpy.ops.wm.save_as_mainfile(filepath=str(W/f'export/Cloth_{sex}.blend'))
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
 for o in kit:o.select_set(True)
 bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(W/f'export/{sex}_Kit.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='STRIP')
 print('Re-exported',sex,flush=True)
