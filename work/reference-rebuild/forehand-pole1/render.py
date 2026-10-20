import bpy,pathlib,numpy as np
from mathutils import Vector
W=pathlib.Path.cwd()/'work/reference-rebuild/forehand-pole1'
def mat(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*c,1);n.inputs['Roughness'].default_value=.72;return m
for degree in (0,30,60,90):
 bpy.ops.wm.read_factory_settings(use_empty=True);q=np.load(W/f'swivel_{degree}.npz');skin=mat('skin',(.57,.29,.17));cloth=mat('cloth',(.70,.105,.060))
 for part,material in [('body',skin),('top',cloth)]:
  p=q[part];v=np.column_stack([p[:,0],-p[:,2],p[:,1]]);t=q[part+'Triangles'];mesh=bpy.data.meshes.new(part);mesh.from_pydata(v.tolist(),[],t.tolist());mesh.update();mesh.materials.append(material);ob=bpy.data.objects.new(part,mesh);bpy.context.collection.objects.link(ob)
  for f in mesh.polygons:f.use_smooth=True
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=800;sc.render.resolution_y=850;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('world');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.55,.55,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.4;sc.view_settings.view_transform='AgX';target=Vector((.26,-.06,1.13))
 for pos,power,size in [((-.8,-2,3),400,3),((2,-1,2),160,3)]:
  bpy.ops.object.light_add(type='AREA',location=pos);ob=bpy.context.object;ob.data.energy=power;ob.data.size=size;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
 for view,offset in [('front',(-.32,-4,.2)),('side',(3,-1,.15))]:
  bpy.ops.object.camera_add(location=target+Vector(offset));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=.93;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;sc.render.filepath=str(W/f'swivel_{degree}_{view}.png');bpy.ops.render.render(write_still=True)
