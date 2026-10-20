import bpy,pathlib
from mathutils import Vector
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/characters'
for sex in ('Male','Female'):
 ss=sex.lower();bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_ReferenceBody_Smooth.blend'));body=bpy.data.objects['Body'];eye=Vector(body['ReferenceEyeMidpoint'])
 sc=bpy.context.scene;sc.use_nodes=False;sc.render.film_transparent=False;world=bpy.data.worlds.new('GraftStudio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.36,.42,1);world.node_tree.nodes['Background'].inputs[1].default_value=.3;sc.world=world;target=eye+Vector((0,0,-.030))
 for name,delta,power,size in [('Key',(-.55,-.7,.75),25,1),('Fill',(.55,-.7,.2),18,1),('Rim',(.3,.35,.55),40,.75)]:
  ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.size=size;lo=bpy.data.objects.new(name,ld);sc.collection.objects.link(lo);lo.location=target+Vector(delta);lo.rotation_euler=(target-lo.location).to_track_quat('-Z','Y').to_euler()
 cd=bpy.data.cameras.new('GraftPortrait');cam=bpy.data.objects.new('GraftPortrait',cd);sc.collection.objects.link(cam);sc.camera=cam;cd.type='ORTHO';cd.ortho_scale=.42;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=32;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=600;sc.render.resolution_y=700;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=-.6
 for angle,delta in [('front',(0,-1.1,.01)),('threequarter',(.58,-1.1,.025))]:
  cam.location=target+Vector(delta);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{ss}_graft_smooth_{angle}.png');bpy.ops.render.render(write_still=True)
