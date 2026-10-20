import bpy,math
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.wm.open_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/ResortPalmDroop.blend'))
show={'PINE':((0,0,0),(2,2,8)),'PALM':((5,0,0),(2.7,2.7,8)),'SHRUB_0':((-2,-4,0),(2.5,2.5,3)),'SHRUB_1':((3,-4,0),(2.5,2.5,3)),'BLUFF_0':((10,2,0),(4,3,7))}
for o in bpy.data.objects:
 if o.type!='MESH':continue
 if o.name not in show:o.hide_render=True;continue
 position,scale=show[o.name];o.location=position;o.scale=scale
 if o.name in ['PINE','PALM']:
  uv=o.data.uv_layers.get('BotanicalPivot');centres={}
  for poly in o.data.polygons:
   for loop in poly.loop_indices:centres[o.data.loops[loop].vertex_index]=uv.data[loop].uv.x
  for index,c in centres.items():
   if c>=0:o.data.vertices[index].co.z=c+(o.data.vertices[index].co.z-c)*scale[0]/scale[2]
world=bpy.data.worlds.new('Landscape studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.32,.42,1);world.node_tree.nodes['Background'].inputs[1].default_value=.8;bpy.context.scene.world=world
bpy.ops.mesh.primitive_plane_add(size=200);floor=bpy.context.object;floor.name='Studio floor';m=bpy.data.materials.new('Floor');m.diffuse_color=(.12,.18,.12,1);floor.data.materials.append(m)
for name,energy,loc,size in [('Key',2200,(-7,-6,14),9),('Fill',1800,(9,4,13),10)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((3,0,4))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Landscape proof');o=bpy.data.objects.new('Landscape proof',d);bpy.context.collection.objects.link(o);o.location=(19,-25,16);o.rotation_euler=(Vector((4,0,3.6))-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=22;bpy.context.scene.camera=o
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1440;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.render.filepath=str(root/'proof/full-visual-overhaul/golf/landscape-palm-droop.png');bpy.ops.render.render(write_still=True)
