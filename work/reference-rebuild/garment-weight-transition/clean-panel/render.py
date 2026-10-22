import bpy,pathlib,numpy as np
from mathutils import Vector
R=pathlib.Path.cwd();W=R/'work/reference-rebuild/garment-weight-transition/clean-panel'
def material(name,c):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*c,1);n.inputs['Roughness'].default_value=.76;n.inputs['Specular IOR Level'].default_value=.15;return m

def mesh(name,p,t,m,offset):
 q=np.column_stack([p[:,0]+offset[0],-p[:,2],p[:,1]+offset[1]]);me=bpy.data.meshes.new(name);me.from_pydata(q.tolist(),[],t.tolist());me.update();me.materials.append(m);ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
 for f in me.polygons:f.use_smooth=True
 return ob
for sex in ('male','female'):
 for action in ('Serve','Forehand'):
  bpy.ops.wm.read_factory_settings(use_empty=True);skin=material('Unchanged Body display crop',(.57,.29,.17));cloth=material('Same plain cloth',(.70,.105,.060) if sex=='male' else (.35,.53,.05))
  for row in range(3):
   q=np.load(W/f'{sex}_{action}_{row}.npz');bp=q['body'];bt=q['bodyTriangles'];tt=q['topTriangles'];br=q['bodyRest'];ids=q['bodyIndices'];weights=q['bodyWeights'];names=q['bodyNames'].tolist();head=(weights*np.isin(ids,[names.index('Head'),names.index('Neck')])).sum(1);display=(br[:,1]>.99)&(head<.5);bt=bt[display[bt].all(1)]
   for col,variant in enumerate(('before','after')):mesh(f'{row}_{variant}_BodyDisplay',bp,bt,skin,(col*.85,-row*.88));mesh(f'{row}_{variant}_Top',q[variant],q['beforeTriangles'] if variant=='before' else tt,cloth,(col*.85,-row*.88))
  sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=1500;sc.render.resolution_y=1900;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('Same studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.4,.43,.47,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.3;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';target=Vector((.425,0,.38))
  for pos,power,size in [((-.7,-2,3),420,3),((2,-1,1.7),160,3)]:
   bpy.ops.object.light_add(type='AREA',location=pos);ob=bpy.context.object;ob.data.energy=power;ob.data.size=size;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
  bpy.ops.object.camera_add(location=(.425,-4.5,.65));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.94;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;sc.render.filepath=str(W/f'{sex}_{action}_source-before-after.png');bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{sex}_{action}_SourceComparison.blend'))
