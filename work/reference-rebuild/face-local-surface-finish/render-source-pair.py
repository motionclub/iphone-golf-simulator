"""Matched CPU Blender source portraits; never Unity art acceptance."""
import bpy,pathlib,json
from mathutils import Vector
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-local-surface-finish'
for case,source in [('before',R/'work/reference-rebuild/original-blink-finish/Male_OriginalSeamBlinkFinish1.blend'),('after',O/'Male_OriginalSeamLocalSurfaceFinish1.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;body=bpy.data.objects['Body'];feat=bpy.data.objects['ReferenceFeatures'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST';rig.animation_data_clear()
 for ob in sc.objects:
  if ob.type=='MESH':ob.hide_render=ob not in (body,feat)
 for ob in (body,feat):
  for k in ob.data.shape_keys.key_blocks:k.value=0
 bpy.context.view_layer.update();ids={i for p in feat.data.polygons if 'Sclera' in feat.data.materials[p.material_index].name for i in p.vertices};eye=sum((feat.matrix_world@feat.data.vertices[i].co for i in ids),Vector())/len(ids);target=eye+Vector((0,0,-.018));sc.cycles.device='CPU';sc.cycles.samples=32;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=600;sc.render.resolution_y=700;sc.render.resolution_percentage=100;sc.camera.data.ortho_scale=.39
 for angle,delta in [('front',(0,-1.1,.015)),('threequarter',(.42,-1.1,.025))]:
  sc.camera.location=eye+Vector(delta);sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'male_source_{case}_{angle}.png');bpy.ops.render.render(write_still=True);print('SOURCE_PAIR',case,angle,flush=True)
