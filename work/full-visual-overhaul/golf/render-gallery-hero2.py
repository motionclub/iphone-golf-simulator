import bpy,math
from pathlib import Path
from mathutils import Vector
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=R/'work/full-visual-overhaul/golf';P=R/'proof/full-visual-overhaul/golf'
bpy.ops.wm.open_mainfile(filepath=str(W/'GolfGalleryHero2.blend'))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.resolution_x=1536;sc.render.resolution_y=768;sc.render.resolution_percentage=100
sc.world=bpy.data.worlds.new('Gallery hero studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.28,.36,.46,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
bpy.ops.object.light_add(type='AREA',location=(4,-4,5));bpy.context.object.data.energy=1300;bpy.context.object.data.size=8
bpy.ops.object.camera_add(location=(5,-12,2.8));cam=bpy.context.object;cam.rotation_euler=(Vector((5,-.05,.90))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=13;sc.camera=cam;sc.view_settings.view_transform='AgX';sc.render.filepath=str(P/'gallery-hero2-source.png');bpy.ops.render.render(write_still=True)
for name,x in [('male',0),('female',2.1)]:
 cam.data.ortho_scale=.43;cam.location=(x+.20,-3,1.57);cam.rotation_euler=(Vector((x,-.02,1.565))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.resolution_x=720;sc.render.resolution_y=720;sc.render.filepath=str(P/f'gallery-hero2-{name}-face.png');bpy.ops.render.render(write_still=True)

# Review the real distant geometry independently, including enlarged face
# topology and representative whole-body scale.
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render='_FAR' not in o.name
for name,x in [('male',0),('female',2.1)]:
 cam.data.ortho_scale=.43;cam.location=(x+.20,-3,1.57);cam.rotation_euler=(Vector((x,-.02,1.565))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.resolution_x=720;sc.render.resolution_y=720;sc.render.filepath=str(P/f'gallery-hero2-{name}-far-face.png');bpy.ops.render.render(write_still=True)
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render='_FAR' in o.name
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith(('ARM_L','ARM_R')) and '_FAR' not in o.name:o.rotation_euler.x=math.radians(-158 if o.name.startswith('ARM_L') else -166)
cam.data.ortho_scale=3.1;cam.location=(.95,-8,1.8);cam.rotation_euler=(Vector((.95,0,1.5))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.filepath=str(P/'gallery-hero2-cheer-source.png');bpy.ops.render.render(write_still=True)
