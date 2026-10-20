import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1];args=sys.argv[sys.argv.index('--')+1:];sex=args[0];family=args[1] if len(args)>1 else 'Drive';hand=args[2] if len(args)>2 else 'RH'
sc=bpy.context.scene;rig=bpy.data.objects['Rig_'+sex];club=bpy.data.objects['GolfClub'];ident=f'{family}_{sex}_{hand}'
manifest=json.loads((W/f'export/golf_manifest_{sex}.json').read_text());d=next(x for x in manifest['clips'] if x['id']==ident)
rig.animation_data.action=bpy.data.actions[ident];club.animation_data.action=bpy.data.actions[ident+'_Equipment']
for o in bpy.data.objects:
 if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data:
  action=bpy.data.actions.get(ident+'_'+o.name+'_Correctives')
  if action:o.data.shape_keys.animation_data.action=action
  for tr in o.data.shape_keys.animation_data.nla_tracks:tr.mute=True
for tr in rig.animation_data.nla_tracks:tr.mute=True
for tr in club.animation_data.nla_tracks:tr.mute=True
for o in bpy.data.objects:
 if o.type=='LIGHT':o.hide_render=True
 if o.name.startswith('Golf_Glove_'):o.hide_render=o.name!=('Golf_Glove_Left' if hand=='RH' else 'Golf_Glove_Right')
for o in bpy.data.objects:
 if o.name.startswith('GolfClubFace'):o.hide_render=o.get('GolfEquipment','iron')!=d['equipment'];o.location.y=d['clubLength']
length=d['clubLength'];bpy.data.objects['GolfClubFace'].location.y=length;bpy.data.objects['GolfClubContact'].location.y=length
shaft=bpy.data.objects['GolfShaft'];shaft.location.y=(length+.12)/2;shaft.scale.z=(length-.12)/.84
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=12;sc.cycles.use_denoising=True
sc.render.resolution_x=640;sc.render.resolution_y=800;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
sc.world=bpy.data.worlds.new('GolfReviewWorld');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.18,.23,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.45
sc.view_settings.view_transform='AgX'
body=bpy.data.objects['Body_'+('F' if sex=='Female' else 'M')]
for material in body.data.materials:
 if material and material.use_nodes:
  bs=material.node_tree.nodes.get('Principled BSDF')
  if bs:bs.inputs['Base Color'].default_value=(.55,.31,.19,1);bs.inputs['Roughness'].default_value=.38
for name,pos,power,size in [('GolfKey',(2,-4,4),500,3),('GolfFill',(-3,-2,2.5),220,3),('GolfRim',(1,2,3.5),350,2)]:
 l=bpy.data.lights.new(name,'AREA');l.energy=power;l.shape='DISK';l.size=size;o=bpy.data.objects.new(name,l);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.010));floor=bpy.context.object;floor.name='GolfReviewFloor';m=bpy.data.materials.new('GolfReviewFloor');m.diffuse_color=(.12,.17,.23,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=m.diffuse_color;floor.data.materials.append(m)

if '--fast' in args:
 sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=480;sc.render.resolution_y=600
 sc.display.shading.show_specular_highlight=False;sc.display.shading.show_shadows=False
 for material in bpy.data.materials:
  if material.use_nodes:
   bs=material.node_tree.nodes.get('Principled BSDF')
   if bs:material.diffuse_color=bs.inputs['Base Color'].default_value
 sc.display.shading.light='STUDIO';sc.display.shading.studiolight_rotate_z=.5;sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=True
 for material in body.data.materials:
  if material:material.diffuse_color=(.55,.31,.19,1)
out=W/('proof-fast' if '--fast' in args else 'proof')/ident;out.mkdir(parents=True,exist_ok=True)
stages=[('Address',0),('Top',d['backswingTop']),('Impact',d['impact']),('Finish',d['duration'])]
if '--sample' in args:stages=[('Sample',float(args[args.index('--sample')+1]))]
for label,t in stages:
 if t is None:continue
 sc.frame_set(int(t*120),subframe=t*120-int(t*120))
 for angle in ([0,180] if '--all' not in args else range(0,360,45)):
  sc.camera=bpy.data.objects[f'Review_{angle:03d}'];sc.render.filepath=str(out/f'{label}_{angle:03d}.png');bpy.ops.render.render(write_still=True)
sc.frame_set(0);bpy.context.view_layer.update();hands=(rig.pose.bones['LeftHand'].head+rig.pose.bones['RightHand'].head)/2;cam=bpy.data.objects['Review_Hands'];cam.location=hands+Vector((0,-2,.05));cam.rotation_euler=(hands-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.37;sc.camera=cam;sc.render.filepath=str(out/'Grip.png');bpy.ops.render.render(write_still=True)
print('REVIEW_COMPLETE',ident,flush=True)
