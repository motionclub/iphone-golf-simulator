import bpy,math
from mathutils import Vector
from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');bpy.ops.wm.open_mainfile(filepath=str(root/'work/full-visual-overhaul/tennis/CrowdSourceProbe.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=768;sc.render.resolution_y=768;sc.render.resolution_percentage=100
sc.world=bpy.data.worlds.new('Neutral');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.3,.4,.55,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
for m in bpy.data.materials:
 if m.use_nodes:
  p=m.node_tree.nodes.get('Principled BSDF')
  if p:p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=.6
bpy.ops.object.light_add(type='AREA',location=(-2,-3,4));bpy.context.object.data.energy=280;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=4
bpy.ops.object.camera_add(location=(2,-3.8,2));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.85))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=55;sc.camera=cam
sc.view_settings.view_transform='AgX';sc.render.filepath=str(root/'proof/full-visual-overhaul/tennis/crowd-source-blender.png');bpy.ops.render.render(write_still=True)
