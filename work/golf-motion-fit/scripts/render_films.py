"""Synchronized geometry review: eight 45-degree views and overhead in one frame.
15 fps films sample the continuous 120 Hz masters. This is a fit review, not a
runtime shader or final human-acceptance substitute.
"""
import bpy,sys,math,json,time
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1];args=sys.argv[sys.argv.index('--')+1:];sex=args[0];sheets='--sheets' in args;families=[a for a in args[1:] if not a.startswith('--')] or None
sc=bpy.context.scene;rig=bpy.data.objects['Rig_'+sex];club=bpy.data.objects['GolfClub'];manifest=json.loads((W/f'export/golf_manifest_{sex}.json').read_text())
sc.world=bpy.data.worlds.new('GolfMotionReviewWorld');sc.world.color=(.11,.13,.16)
sc.render.film_transparent=False
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=960;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
sh=sc.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL';sh.show_shadows=False;sh.show_specular_highlight=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD';sc.world.color=(.11,.13,.16)
for m in bpy.data.materials:
 if m.use_nodes:
  bs=m.node_tree.nodes.get('Principled BSDF')
  if bs:m.diffuse_color=bs.inputs['Base Color'].default_value
for m in bpy.data.objects['Body_'+('F' if sex=='Female' else 'M')].data.materials:
 if m:m.diffuse_color=(.55,.31,.19,1)
source=[o for o in bpy.data.objects if o==rig or o.name=='GolfClub' or (o.type=='MESH' and not o.hide_render and o.name.startswith(('Body_','Face_','Hair_','Golf')))]
# Keep both glove variants in the review; each clip displays its own lead glove.
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith(('Golf_Glove_','GolfClubFace')) and o not in source:source.append(o)
clusters=[];clusterRoots=[]
for view in range(12):
 parent=bpy.data.objects.new('StudioView_'+str(view),None);sc.collection.objects.link(parent)
 col=view%4;row=view//4;parent.location=((col-1.5)*2.4,0,(2-row)*2.4)
 parent.rotation_euler=(math.pi/2,0,0) if view==8 else (0,0,(view if view<8 else 0)*math.pi/4)
 if view in [9,10]:parent.scale=(4.0,4.0,4.0) if view==9 else (2.8,2.8,2.8)
 if view==8:parent.location.z+=1.15
 copies={o:o.copy() for o in source}
 for old,new in copies.items():
  new.name=f'V{view}_{old.name}';sc.collection.objects.link(new);new.hide_render=False;new.hide_set(False)
  new.parent=copies.get(old.parent,parent)
  if old.parent_type=='BONE':new.parent=parent;new.parent_type='OBJECT';new.matrix_parent_inverse.identity()
  for modifier in new.modifiers:
   if modifier.type=='ARMATURE':modifier.object=copies[rig]
  if new.animation_data:
   for tr in new.animation_data.nla_tracks:tr.mute=True
 clusters.append(copies);clusterRoots.append(parent)
for o in source:o.hide_render=True
for view in [9,10]:
 for o in clusters[view].values():o.hide_render=True
cam=bpy.data.cameras.new('StudioCamera');cam.type='ORTHO';cam.ortho_scale=7.2;camera=bpy.data.objects.new('StudioCamera',cam);sc.collection.objects.link(camera);camera.location=(0,-15,3.4);camera.rotation_euler=(Vector((0,0,3.4))-camera.location).to_track_quat('-Z','Y').to_euler();sc.camera=camera
for d in manifest['clips']:
 if families and d['motion'] not in families:continue
 ident=d['id'];rig.animation_data.action=bpy.data.actions[ident];club.animation_data.action=bpy.data.actions[ident+'_Equipment'];out=W/('sheet-frames' if sheets else 'film-frames')/ident;out.mkdir(parents=True,exist_ok=True)
 for copies in clusters:
  copies[rig].animation_data.action=bpy.data.actions[ident];copies[club].animation_data.action=bpy.data.actions[ident+'_Equipment']
  for old,new in copies.items():
   if old.type=='MESH' and old.data.shape_keys and old.data.shape_keys.animation_data:
    act=bpy.data.actions.get(ident+'_'+old.name+'_Correctives')
    if act:old.data.shape_keys.animation_data.action=act
    for tr in old.data.shape_keys.animation_data.nla_tracks:tr.mute=True
   if old.name.startswith('Golf_Glove_'):new.hide_render=old.name!=('Golf_Glove_Left' if d['handedness']=='right' else 'Golf_Glove_Right')
   if old.name.startswith('GolfClubFace'):new.location.y=d['clubLength'];new.hide_render=old.get('GolfEquipment','iron')!=d['equipment']
   if old.name=='GolfShaft':new.location.y=(d['clubLength']+.12)/2;new.scale.z=(d['clubLength']-.12)/.84
 for view in [9,10]:
  for o in clusters[view].values():o.hide_render=True
 # Close-ups are separate camera crops; they must never occlude adjacent views.
 closeData=bpy.data.cameras.new('Close_'+ident);closeData.type='ORTHO';closeCamera=bpy.data.objects.new('Close_'+ident,closeData);sc.collection.objects.link(closeCamera)
 scratch=W/('sheet-scratch' if sheets else 'film-scratch')/ident;scratch.mkdir(parents=True,exist_ok=True)
 times=[0,d['backswingTop'] if d['backswingTop'] is not None else d['duration']/3,d['impact'] if d['impact'] is not None else d['duration']*2/3,d['duration']] if sheets else [f/15 for f in range(round(d['duration']*15)+1)]
 for f,t in enumerate(times):
  frame=t*120;sc.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
  for view,copies in enumerate(clusters):
   if view in [9,10]:
    target=(copies[rig].pose.bones['LeftHand'].head+copies[rig].pose.bones['RightHand'].head)/2 if view==9 else copies[rig].pose.bones['Hips'].head
    col=view%4;row=view//4;clusterRoots[view].location=Vector(((col-1.5)*2.4,0,(2-row)*2.4+1.15))-clusterRoots[view].rotation_euler.to_matrix()@(target*clusterRoots[view].scale.x)
   if view==11:clusterRoots[view].rotation_euler.z=2*math.pi*t/max(.001,d['duration'])
   for old,new in copies.items():
    if old.parent_type=='BONE':new.matrix_basis=old.matrix_world.copy()
  sc.camera=camera;sc.render.resolution_x=960;sc.render.resolution_y=720
  sc.render.filepath=str(out/f'{f:04d}.png');bpy.ops.render.render(write_still=True)
  for view,copies in enumerate(clusters):
   for o in copies.values():o.hide_render=True
  for o in source:
   o.hide_render=False
   if o.name.startswith('Golf_Glove_'):o.hide_render=o.name!=('Golf_Glove_Left' if d['handedness']=='right' else 'Golf_Glove_Right')
   if o.name.startswith('GolfClubFace'):o.hide_render=o.get('GolfEquipment','iron')!=d['equipment'];o.location.y=d['clubLength']
   if o.name=='GolfShaft':o.location.y=(d['clubLength']+.12)/2;o.scale.z=(d['clubLength']-.12)/.84
  sc.camera=closeCamera;sc.render.resolution_x=240;sc.render.resolution_y=240
  for label,scale,target in [('hands',.34,(rig.pose.bones['LeftHand'].head+rig.pose.bones['RightHand'].head)/2),('waist',.65,rig.pose.bones['Hips'].head)]:
   closeCamera.location=target+Vector((0,-3,.04));closeCamera.rotation_euler=(target-closeCamera.location).to_track_quat('-Z','Y').to_euler();closeData.ortho_scale=scale
   sc.render.filepath=str(scratch/f'{f:04d}_{label}.png');bpy.ops.render.render(write_still=True)
  for o in source:o.hide_render=True
  for view,copies in enumerate(clusters):
   if view in [9,10]:continue
   for old,new in copies.items():
    new.hide_render=False
    if old.name.startswith('Golf_Glove_'):new.hide_render=old.name!=('Golf_Glove_Left' if d['handedness']=='right' else 'Golf_Glove_Right')
    if old.name.startswith('GolfClubFace'):new.hide_render=old.get('GolfEquipment','iron')!=d['equipment']
 (out/'metadata.json').write_text(json.dumps(dict(clip=ident,fps=None if sheets else 15,times=times if sheets else None,labels=['Address' if d['backswingTop'] is not None else 'Start','Top' if d['backswingTop'] is not None else 'One-third','Impact' if d['impact'] is not None else 'Two-thirds','Finish'] if sheets else None,views=list(range(0,360,45))+['overhead','hands','waist','360'],duration=d['duration']),indent=2))
 print('FILM_COMPLETE',ident,flush=True)
print('ALL_FILMS_COMPLETE',sex,flush=True)
