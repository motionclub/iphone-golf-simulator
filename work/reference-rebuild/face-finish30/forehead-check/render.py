import bpy,pathlib
from mathutils import Vector
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish30/forehead-check'
for case,source in [('before',R/'work/reference-rebuild/face-finish30/ears/Female_OriginalFaceFinish30Ears.blend'),('after',O/'Female_OriginalFaceFinish30Forehead.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;body=bpy.data.objects['Body'];feat=bpy.data.objects['ReferenceFeatures'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST';rig.animation_data_clear()
 for ob in sc.objects:
  if ob.type=='MESH':ob.hide_render=ob not in(body,feat)
 for ob in(body,feat):
  for key in ob.data.shape_keys.key_blocks:key.value=0
 mat=bpy.data.materials.new('Matched diagnostic satin');mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.55,.32,.20,1);bsdf.inputs['Roughness'].default_value=.30
 for i in range(len(body.data.materials)):body.data.materials[i]=mat
 bpy.context.view_layer.update();ids={i for p in feat.data.polygons if 'Sclera' in feat.data.materials[p.material_index].name for i in p.vertices};eye=sum((feat.matrix_world@feat.data.vertices[i].co for i in ids),Vector())/len(ids);target=eye+Vector((0,0,.045));sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=32;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=480;sc.render.resolution_y=480;sc.render.resolution_percentage=100;sc.camera.data.ortho_scale=.29;sc.camera.location=eye+Vector((.18,-1.1,.025));sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'forehead_{case}.png');bpy.ops.render.render(write_still=True)
