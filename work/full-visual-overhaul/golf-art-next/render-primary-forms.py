import bpy,pathlib,math
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[3];W=R/'work/full-visual-overhaul/golf-art-next'
bpy.ops.wm.open_mainfile(filepath=str(W/'PrimaryLandscapeForms.blend'))
for ob in bpy.data.objects:ob.hide_render=True
for mat in bpy.data.materials:
 mat.use_nodes=True;b=mat.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=mat.diffuse_color;b.inputs['Roughness'].default_value=.8
for row,name in enumerate(['BLUFF_0','SHRUB_0']):
 for col,prefix in enumerate(['BEFORE_','']):
  ob=bpy.data.objects[prefix+name];ob.hide_render=False;ob.location=(col*2.4,row*2.35,0);ob.scale=(1,1,1.6 if row==0 else 1.0)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.03));ground=bpy.context.object;ground.hide_render=False;m=bpy.data.materials.new('Muted sand proof plane');m.diffuse_color=(.24,.29,.25,1);ground.data.materials.append(m)
sc=bpy.context.scene;sc.world=bpy.data.worlds.new('Art source world');sc.world.color=(.22,.28,.33);sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.view_settings.view_transform='AgX';sc.render.resolution_x=1700;sc.render.resolution_y=1150;sc.render.resolution_percentage=100
for p,power,size in [((-3,-4,7),800,4),((6,1,6),300,3)]:
 bpy.ops.object.light_add(type='AREA',location=p);o=bpy.context.object;o.hide_render=False;o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector((1.2,1.1,.6))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(4.8,-7.5,6.2));cam=bpy.context.object;cam.rotation_euler=(Vector((1.2,1.1,.65))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=6.8;sc.camera=cam
sc.render.filepath=str(W/'primary-forms-before-after.png');bpy.ops.render.render(write_still=True)
