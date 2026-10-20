import bpy
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
work=root/'work/full-visual-overhaul/golf'
bpy.ops.wm.open_mainfile(filepath=str(work/'ResortCoastalStone.blend'))
stone=bpy.data.materials.new('Quiet sunlit limestone proof');stone.diffuse_color=(.52,.49,.42,1)
for o in list(bpy.data.objects):
 if o.type!='MESH':continue
 if o.name not in ['BLUFF_0','BLUFF_1','BLUFF_2','BOULDER']:o.hide_render=True;continue
 index=0 if o.name=='BOULDER' else int(o.name[-1])+1
 o.location+=Vector((index*5,-5,0));o.scale=Vector((o.scale.x*4,o.scale.y*4,o.scale.z*7))
 o.data.materials.clear();o.data.materials.append(stone)
 for face in o.data.polygons:face.material_index=0
with bpy.data.libraries.load(str(work/'ResortEvergreenBough.blend'),link=False) as (source,dest):dest.objects=['BLUFF_0','BLUFF_1','BLUFF_2','BOULDER']
for o in dest.objects:
 bpy.context.collection.objects.link(o);index=0 if o.name.startswith('BOULDER') else int(o.name.split('.')[0][-1])+1
 o.location=Vector((index*5,5,0));o.scale=Vector((4,4,7));o.data.materials.clear();o.data.materials.append(stone)
 for face in o.data.polygons:face.material_index=0
world=bpy.data.worlds.new('Coastal stone studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.25,.32,1);world.node_tree.nodes['Background'].inputs[1].default_value=.6;bpy.context.scene.world=world
bpy.ops.mesh.primitive_plane_add(size=200);floor=bpy.context.object;floor.name='Studio floor';m=bpy.data.materials.new('Floor');m.diffuse_color=(.11,.16,.17,1);floor.data.materials.append(m)
for name,energy,loc,size in [('Key',2700,(-7,-8,18),7),('Fill',1600,(15,4,13),10)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((8,0,3))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Stone proof');o=bpy.data.objects.new('Stone proof',d);bpy.context.collection.objects.link(o);o.location=(23,-27,22);o.rotation_euler=(Vector((8,0,3))-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=29;bpy.context.scene.camera=o
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1600;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.render.filepath=str(root/'proof/full-visual-overhaul/golf/coastal-stone-rounding15.png');bpy.ops.render.render(write_still=True)
