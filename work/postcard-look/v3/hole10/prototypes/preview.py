"""Actual scratch connected-column silhouettes; these are not Game view proof."""
import os,sys,math,json
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
import bpy,numpy as np
from mathutils import Vector
import postcard_look_lib as L
OUT=os.path.dirname(__file__)
paths=[]
for nm in ('near10m_rows4_top15','near6m_rows7_top25'):
 bpy.ops.wm.open_mainfile(filepath=OUT+'/attempt2/'+nm+'/fixture.blend')
 sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE'
 sc.render.resolution_x=800;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
 sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB'
 sc.render.film_transparent=False;sc.view_settings.view_transform='Standard'
 if sc.world is None:sc.world=bpy.data.worlds.new('PREVIEW_WORLD')
 sc.world.use_nodes=True
 sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.11,.14,.18,1)
 sc.world.node_tree.nodes['Background'].inputs[1].default_value=.5
 ob=next(o for o in bpy.data.objects if o.name=='ROCK_WALL_COMPACT')
 for o in bpy.data.objects:
  if o.type=='MESH' and o!=ob:o.hide_render=True
 v=np.array([tuple(v.co) for v in ob.data.vertices]);lo,hi=v.min(0),v.max(0);center=(lo+hi)*.5
 light=bpy.data.lights.new('PREVIEW_KEY','SUN');light.energy=2.
 sun=bpy.data.objects.new('PREVIEW_KEY',light);sc.collection.objects.link(sun)
 sun.rotation_euler=(math.radians(35),math.radians(-15),math.radians(-25))
 mat=bpy.data.materials.new('PREVIEW_CLAY');mat.diffuse_color=(.21,.24,.27,1);mat.use_nodes=True
 bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.21,.24,.27,1);bs.inputs['Roughness'].default_value=.92
 original=list(ob.data.materials);ob.data.materials.clear();ob.data.materials.append(mat)
 for az in (0,45,135):
  cam=bpy.data.objects.new('PREVIEW_CAM',bpy.data.cameras.new('PREVIEW_CAM'));sc.collection.objects.link(cam)
  a=math.radians(az);distance=float(max(hi-lo))*2.2
  cam.location=center+np.array([math.sin(a)*distance,-math.cos(a)*distance,distance*.25])
  cam.rotation_euler=(Vector(center)-cam.location).to_track_quat('-Z','Y').to_euler()
  cam.data.type='ORTHO';cam.data.ortho_scale=float(hi[2]-lo[2])*1.2;sc.camera=cam
  path=OUT+'/attempt2/'+nm+'/clay_az'+str(az)+'.png';sc.render.filepath=path
  bpy.ops.render.render(write_still=True);paths.append(path);bpy.data.objects.remove(cam,do_unlink=True)
 ob.data.materials.clear()
 for m in original:ob.data.materials.append(m)
with open(OUT+'/preview_paths.json','w') as f:json.dump(paths,f,indent=2)
