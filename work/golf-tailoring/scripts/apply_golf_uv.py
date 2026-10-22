import bpy,sys,numpy as np
from pathlib import Path
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];folder=W/'export/kit_v2';rig=bpy.data.objects['Rig_'+sex]
for o in bpy.data.objects:
 if o.type!='MESH' or not o.name.startswith('Kit_'):continue
 d=np.load(folder/f'{sex}_{o.name}.npz');o.data.calc_loop_triangles()
 assert len(o.data.uv_layers.active.data)==len(d['uv'])
 assert np.array_equal(np.array([q.vertices[:] for q in o.data.loop_triangles]),d['tri'])
 for v,uv in zip(o.data.uv_layers.active.data,d['uv']):v.uv=uv
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in bpy.data.objects:
 if o.type=='MESH' and (o.name.startswith('Kit_') or o.name=='Hair_F'):
  o.hide_set(False);o.hide_viewport=False;o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(folder/f'Golf_{sex}_Kit.fbx'),use_selection=True,global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,use_triangles=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='STRIP',object_types={'MESH','ARMATURE'})
bpy.ops.wm.save_as_mainfile(filepath=str(folder/f'Golf_{sex}_KitUV.blend'))
