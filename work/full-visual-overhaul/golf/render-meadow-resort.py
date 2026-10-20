import bpy
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=root/'work/full-visual-overhaul/golf'
bpy.ops.wm.open_mainfile(filepath=str(w/'MeadowCountryClub.blend'))
with bpy.data.libraries.load(str(w/'ResortSummerOak.blend'),link=False) as (source,dest):dest.objects=['OAK']
tree=dest.objects[0];bpy.context.collection.objects.link(tree)
pivot=tree.data.uv_layers['BotanicalPivot'];centres={}
for polygon in tree.data.polygons:
 for loop in polygon.loop_indices:centres[tree.data.loops[loop].vertex_index]=pivot.data[loop].uv.x
for index,c in centres.items():
 if c>=0:tree.data.vertices[index].co.z=c+(tree.data.vertices[index].co.z-c)*5/14
tree.location=(-19,2,0);tree.scale=(5,5,14)
for pos,size in [((18,4,0),(4.7,4.7,12)),((-14,14,0),(5.2,5.2,14)),((23,16,0),(5.8,5.8,15))]:
 o=tree.copy();o.data=tree.data.copy();bpy.context.collection.objects.link(o);o.location=pos;o.scale=size
world=bpy.data.worlds.new('Meadow sunny summer');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.25,.39,.54,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7;bpy.context.scene.world=world
bpy.ops.mesh.primitive_plane_add(size=200);o=bpy.context.object;o.name='Studio grass';m=bpy.data.materials.new('Grass');m.diffuse_color=(.16,.27,.14,1);o.data.materials.append(m)
for name,energy,loc,size in [('Key',3700,(-14,-20,27),8),('Fill',1700,(20,5,20),12)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,5))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Meadow source proof');o=bpy.data.objects.new('Meadow source proof',d);bpy.context.collection.objects.link(o);o.location=(35,-48,23);o.rotation_euler=(Vector((0,2,5))-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=56;bpy.context.scene.camera=o
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1600;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.render.filepath=str(root/'proof/full-visual-overhaul/golf/meadow-countryclub-source16.png');bpy.ops.render.render(write_still=True)
