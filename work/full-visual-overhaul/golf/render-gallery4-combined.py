import bpy,math
from pathlib import Path
from mathutils import Vector
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=R/'work/golf-art-exports';P=W/'proof'
candidate=W/'GolfGalleryHero4.blend';bpy.ops.wm.open_mainfile(filepath=str(candidate if candidate.exists() else R/'ArtDir/golf/source/GolfGalleryHero4.blend'))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.resolution_x=1536;sc.render.resolution_y=768;sc.render.resolution_percentage=100
sc.world=bpy.data.worlds.new('Gallery hero studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.28,.36,.46,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
bpy.ops.object.light_add(type='AREA',location=(4,-4,5));bpy.context.object.data.energy=1300;bpy.context.object.data.size=8
bpy.ops.object.camera_add(location=(5,-12,2.8));cam=bpy.context.object;cam.rotation_euler=(Vector((5,-.05,.90))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=13;sc.camera=cam;sc.view_settings.view_transform='AgX';sc.render.resolution_x=1000;sc.render.resolution_y=1000
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith(('ARM_L','ARM_R')) and '_FAR' not in o.name:o.rotation_euler=(math.radians(-158 if o.name.startswith('ARM_L') else -166),math.radians(-12 if o.name.startswith('ARM_L') else 10),0)
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('HEAD') and '_FAR' not in o.name:o.rotation_euler=(math.radians(-5.7),0,math.radians(6.5))
cam.data.ortho_scale=3.1;cam.location=(.95,-8,1.8);cam.rotation_euler=(Vector((.95,0,1.5))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.filepath=str(P/'gallery-hero4-cheer-source.png');bpy.ops.render.render(write_still=True)

# The distant pieces inherit the exact same live neck/shoulder transforms.
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render='_FAR' not in o.name
sc.render.filepath=str(P/'gallery-hero4-cheer-far-source.png');bpy.ops.render.render(write_still=True)
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render='_FAR' in o.name
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith(('ARM_L','ARM_R')) and '_FAR' not in o.name:o.rotation_euler=(math.radians(-24 if o.name.startswith('ARM_L') else -131),math.radians(-12 if o.name.startswith('ARM_L') else 10),0)
sc.render.filepath=str(P/'gallery-hero4-fistpump-source.png');bpy.ops.render.render(write_still=True)
