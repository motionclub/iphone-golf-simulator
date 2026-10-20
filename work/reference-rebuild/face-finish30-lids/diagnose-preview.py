import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
R=Path.cwd();O=R/'work/reference-rebuild/face-finish30-lids';report={}
for mode in ['uv','cull','uv-cull']:
 bpy.ops.wm.open_mainfile(filepath=str(O/'Female_Face30Lids.blend'));sc=bpy.context.scene;body=bpy.data.objects['Body'];feat=bpy.data.objects['ReferenceFeatures'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST';rig.animation_data_clear()
 for ob in sc.objects:
  if ob.type=='MESH':ob.hide_render=ob not in [body,feat]
 if 'uv' in mode:
  me=body.data;attr=me.color_attributes.get('ActualPigmentDiagnostic')or me.color_attributes.new(name='ActualPigmentDiagnostic',type='FLOAT_COLOR',domain='CORNER')
  for li,u in enumerate(me.uv_layers[0].data):
   masks=np.clip((np.array(u.uv)*64-.5)/63,0,1);lip,dark=masks;dark=min(1,dark*(1+.65*min(1,lip*4)));c=(1-lip)+np.array([.95,.68,.69])*lip;c*=((1-dark)+np.array([.62,.44,.42])*dark);attr.data[li].color=(*c,1)
  for m in me.materials:
   if not m or not m.use_nodes:continue
   nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');col=nt.nodes.new('ShaderNodeVertexColor');col.layer_name='ActualPigmentDiagnostic';nt.links.new(col.outputs['Color'],bs.inputs['Base Color'])
 if 'cull' in mode:
  for m in body.data.materials:
   if not m or not m.use_nodes:continue
   nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');source=out.inputs['Surface'].links[0].from_socket;geo=nt.nodes.new('ShaderNodeNewGeometry');tr=nt.nodes.new('ShaderNodeBsdfTransparent');mix=nt.nodes.new('ShaderNodeMixShader');nt.links.new(geo.outputs['Backfacing'],mix.inputs[0]);nt.links.new(source,mix.inputs[1]);nt.links.new(tr.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs['Surface'])
 eyeids={i for p in feat.data.polygons if 'Sclera' in feat.data.materials[p.material_index].name for i in p.vertices};eye=sum((feat.matrix_world@feat.data.vertices[i].co for i in eyeids),Vector())/len(eyeids);target=eye+Vector((0,0,-.009));sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=720;sc.render.resolution_y=380;sc.render.resolution_percentage=100;sc.camera.data.ortho_scale=.22;sc.camera.location=eye+Vector((.06,-1.1,.015));sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler()
 for ob in [body,feat]:
  for k in ob.data.shape_keys.key_blocks:k.value=(2 if ob==feat else 1)if k.name=='Hero_Blink'else 0
 bpy.context.view_layer.update();sc.render.filepath=str(O/f'female_diagnostic_{mode}_100.png');bpy.ops.render.render(write_still=True)
