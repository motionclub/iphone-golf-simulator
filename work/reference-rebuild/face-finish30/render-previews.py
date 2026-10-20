"""Matched CPU Blender portraits of accepted source and one finish candidate."""
import bpy,pathlib
from mathutils import Vector
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish30'
for sex in ('Male','Female'):
 for case,source in [('before',R/f'work/reference-rebuild/face-finish29/smooth-mouth1/{sex}_OriginalFaceFinish29Smooth1.blend'),('after',O/f'{sex}_OriginalFaceFinish30.blend')]:
  bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;body=bpy.data.objects['Body'];feat=bpy.data.objects['ReferenceFeatures'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST';rig.animation_data_clear()
  for ob in sc.objects:
   if ob.type=='MESH':ob.hide_render=ob not in (body,feat)
  for ob in (body,feat):
   for key in ob.data.shape_keys.key_blocks:key.value=0
  # Match lip3 in preview only; saved candidate UV/pigment buffers stay unchanged.
  col=body.data.color_attributes.get('SkinPigment');mask={}
  for loop in body.data.loops:mask[loop.vertex_index]=tuple(body.data.uv_layers[0].data[loop.index].uv)
  for i,uv in mask.items():
   a=max(0,min(1,(uv[0]*64-.5)/63));b=max(0,min(1,(uv[1]*64-.5)/63));old=[(1+((.93,.66,.68)[k]-1)*a)*(1+((.64,.49,.48)[k]-1)*b)for k in range(3)];lip=(.95,.68,.69)if sex=='Male' else(.94,.61,.64);b2=min(1,b*(1+.65*min(1,a*4)));new=[(1+(lip[k]-1)*a)*(1+((.62,.44,.42)[k]-1)*b2)for k in range(3)];c=col.data[i].color;col.data[i].color=tuple([c[k]/old[k]*new[k]for k in range(3)]+[c[3]])
  bpy.context.view_layer.update();ids={i for p in feat.data.polygons if 'Sclera' in feat.data.materials[p.material_index].name for i in p.vertices};eye=sum((feat.matrix_world@feat.data.vertices[i].co for i in ids),Vector())/len(ids);target=eye+Vector((0,0,-.024));sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=480;sc.render.resolution_y=560;sc.render.resolution_percentage=100;sc.camera.data.ortho_scale=.39
  for angle,offset in [('front',(0,-1.1,.015)),('threequarter',(.42,-1.1,.025))]:
   sc.camera.location=eye+Vector(offset);sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{sex.lower()}_source_{case}_{angle}.png');bpy.ops.render.render(write_still=True);print('FACE_PREVIEW',sex,case,angle,flush=True)
