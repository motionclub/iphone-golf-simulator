import bpy
from pathlib import Path
from mathutils import Vector
R=Path.cwd();O=R/'work/reference-rebuild/face-finish30-lids/ordered-strip1'
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_Face30OrderedLids.blend'));sc=bpy.context.scene;body=bpy.data.objects['Body'];feat=bpy.data.objects['ReferenceFeatures'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST';rig.animation_data_clear()
 import importlib.util
 spec=importlib.util.spec_from_file_location('clearance',O/'apply-corneal-clearance.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);print(mod.apply_corneal_clearance(body,feat,sex),flush=True)
 for ob in sc.objects:
  if ob.type=='MESH':ob.hide_render=ob not in [body,feat]
 for m in body.data.materials:
  nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');source=out.inputs['Surface'].links[0].from_socket;geo=nt.nodes.new('ShaderNodeNewGeometry');tr=nt.nodes.new('ShaderNodeBsdfTransparent');mix=nt.nodes.new('ShaderNodeMixShader');nt.links.new(geo.outputs['Backfacing'],mix.inputs[0]);nt.links.new(source,mix.inputs[1]);nt.links.new(tr.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs['Surface'])
 eyeids={i for p in feat.data.polygons if 'Sclera' in feat.data.materials[p.material_index].name for i in p.vertices};eye=sum((feat.matrix_world@feat.data.vertices[i].co for i in eyeids),Vector())/len(eyeids);target=eye+Vector((0,0,-.009));sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=720;sc.render.resolution_y=380;sc.render.resolution_percentage=100;sc.camera.data.ortho_scale=.22;sc.camera.location=eye+Vector((.06,-1.1,.015));sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler()
 for pct in [50]:
  for ob in [body,feat]:
   for k in ob.data.shape_keys.key_blocks:k.value=1 if k.name=='Hero_Blink_Half' else 0
  bpy.context.view_layer.update();sc.render.filepath=str(O/f'{sex.lower()}_lids_cornea_{pct}.png');bpy.ops.render.render(write_still=True)
