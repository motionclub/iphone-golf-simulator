import bpy,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent;OUT=P/'artist3';bpy.ops.wm.open_mainfile(filepath=str(OUT/'CoastalBotany.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=20;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=1280;s.render.resolution_y=960;s.render.resolution_percentage=100;s.render.film_transparent=False
s.world=bpy.data.worlds.new('Actual source proof');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.40,.53,.62,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
bpy.ops.mesh.primitive_plane_add(size=100,location=(0,0,-.03));floor=bpy.context.object;m=bpy.data.materials.new('Olive');m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.21,.28,.18,1);floor.data.materials.append(m)
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.8;sun.data.angle=.15;sun.rotation_euler=(.42,-.38,-.49)
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.lens=52
plants=[o for o in bpy.data.objects if o.type=='MESH' and o!=floor]
def shot(name,selected,loc,aim):
 for o in plants:o.hide_render=o.name not in selected
 cam.location=loc;cam.rotation_euler=(Vector(aim)-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
for l,x in zip('ABC',[-8,0,8]):
 for suffix in ['', '_FAR']:bpy.data.objects['CONIFER_'+l+suffix].location.x=x
shot('artist-final-near',['CONIFER_'+l for l in 'ABC'],(13,-37,14),(0,0,7.5))
shot('artist-final-far',['CONIFER_'+l+'_FAR' for l in 'ABC'],(13,-37,14),(0,0,7.5))
for n,x in [('SHRUB_A',-2),('SHRUB_B',0),('FERN',2)]:bpy.data.objects[n].location.x=x
shot('artist-final-understory',['SHRUB_A','SHRUB_B','FERN'],(3,-7,3.2),(0,0,.65))
