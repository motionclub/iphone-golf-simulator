import bpy,pathlib
from mathutils import Vector
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish30/ears'
for sex in ('Male','Female'):
 for case,source in [('before',R/f'work/reference-rebuild/face-finish30/final/{sex}_OriginalFaceFinish30Final.blend'),('after',O/f'{sex}_OriginalFaceFinish30Ears.blend')]:
  bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;body=bpy.data.objects['Body'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST';rig.animation_data_clear()
  for ob in sc.objects:
   if ob.type=='MESH':ob.hide_render=ob!=body
  for key in body.data.shape_keys.key_blocks:key.value=0
  gi=body.vertex_groups['LOOP_helix_R'].index;ps=[body.matrix_world@v.co for v in body.data.vertices if any(g.group==gi and g.weight>.25 for g in v.groups)];target=sum(ps,Vector())/len(ps)
  if target.x<0:target.x*=-1
  sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=420;sc.render.resolution_y=480;sc.render.resolution_percentage=100;sc.camera.data.ortho_scale=.120;sc.camera.location=target+Vector((.60,-.65,.065));sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{sex.lower()}_ear_{case}.png');bpy.ops.render.render(write_still=True)
