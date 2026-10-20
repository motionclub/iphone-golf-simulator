"""Dedicated current-hero model and lazy per-motion FBXs; no V4 rebinding."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Matrix
import numpy as np
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];club=bpy.data.objects['GolfClub'];sc=bpy.context.scene
manifest=json.loads((W/f'export/golf_manifest_{sex}.json').read_text());out=W/'export/fbx';out.mkdir(exist_ok=True)
grips=json.loads((W/f'data/grip_{sex}.json').read_text());leftGrips=json.loads((W/f'data/grip_{sex}_LH.json').read_text());reflection=np.diag([-1.,1.,1.])
markers=[]
for hand in ['RH','LH']:
 for side,word in [('L','Left'),('R','Right')]:
  anchor=np.array((grips if hand=='RH' else leftGrips)[side]['anchor'])
  name=f'GolfWrist_{hand}_{word}';marker=bpy.data.objects.get(name)
  if marker is None:marker=bpy.data.objects.new(name,None);sc.collection.objects.link(marker)
  marker.parent=club;marker.matrix_basis=Matrix(anchor.tolist());markers.append(marker)
gear=[o for o in bpy.data.objects if o==club or o.name.startswith(('GolfClubFace','GolfHandle','GolfShaft','GolfClubContact'))]+markers
sockets=[o for o in bpy.data.objects if o.name=='Hand_Racket']
model=[rig]+gear+sockets+[o for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith(('Body_','Face_')) or (o.name.startswith('Golf_') and '_High' not in o.name))]
for tr in rig.animation_data.nla_tracks:tr.mute=True
for tr in club.animation_data.nla_tracks:tr.mute=True
for o in model:
 if o.type=='MESH' and o.data.shape_keys:
  o.data.shape_keys.animation_data_clear()
  for key in o.data.shape_keys.key_blocks:key.value=0
rig.animation_data.action=None;club.animation_data.action=None;rig.data.pose_position='REST';club.location=(0,0,0);club.rotation_quaternion=(1,0,0,0)
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
sc.frame_set(0);bpy.context.view_layer.update()
def export(path,objects,animation):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.hide_set(False);o.hide_viewport=False;o.select_set(True)
 bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'ARMATURE','MESH','EMPTY'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,mesh_smooth_type='OFF',use_triangles=True,add_leaf_bones=False,bake_anim=animation,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_force_startend_keying=True,bake_anim_step=1,bake_anim_simplify_factor=0,path_mode='STRIP',use_armature_deform_only=False)
export(out/f'Golf_{sex}_Model.fbx',model,False)
if '--model-only' in sys.argv:
 print('MODEL_FBX_COMPLETE',sex,flush=True);sys.exit(0)
rig.data.pose_position='POSE';sc.render.fps=120;sc.render.fps_base=1
for entry in manifest['clips']:
 for obj in gear:
  if obj.name.startswith('GolfClubFace') or obj.name=='GolfClubContact':obj.location.y=entry['clubLength']
  if obj.name=='GolfShaft':obj.location.y=(entry['clubLength']+.12)/2;obj.scale.z=(entry['clubLength']-.12)/.84
 ident=entry['id'];rig.animation_data.action=bpy.data.actions[ident];club.animation_data.action=bpy.data.actions[ident+'_Equipment'];sc.frame_start=0;sc.frame_end=entry['frames']-1;sc.frame_set(0)
 export(out/f'{ident}.fbx',[rig]+gear+sockets,True)
 entry['clipPath']='Golf/Animations/'+ident;entry['correctivePath']='Golf/Animations/Correctives/'+ident
 print('FBX_COMPLETE',ident,flush=True)
(W/f'export/golf_manifest_{sex}.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('ALL_FBX_COMPLETE',sex,flush=True)
