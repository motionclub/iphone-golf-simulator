"""Proof-camera/layout fix only; never edits authored target arrays."""
import bpy,pathlib,json,numpy as np
from mathutils import Vector
R=pathlib.Path.cwd();BASE=R/'work/reference-rebuild/garment-stroke-coverage';W=BASE/'v2-panels';D=R/'proof/reference-rebuild/character-cloth14-control/poses'
src=(BASE/'author_stroke_envelopes.py').read_text();exec(src[src.index('def arr('):src.index('def author(')])
def material(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.76;n.inputs['Specular IOR Level'].default_value=.15;return m

def mesh(name,p,t,m,offset):
 q=np.column_stack([p[:,0]+offset[0],-p[:,2],p[:,1]+offset[1]]);me=bpy.data.meshes.new(name);me.from_pydata(q.tolist(),[],t.tolist());me.update();me.materials.append(m);ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
 for f in me.polygons:f.use_smooth=True
 return ob

for sex in ('Male','Female'):
 p=json.loads((BASE/f'SleeveFit_{sex}.json').read_text())
 for action in ('Forehand',):
  bpy.ops.wm.read_factory_settings(use_empty=True);skin=material('Unchanged actual Body torso crop',(.57,.29,.17));cloth=material('Same plain garment',(.70,.105,.060) if sex=='Male' else (.35,.53,.05))
  for row in range(3):
   label=f'{sex.lower()}_{action}_{row}';snap=json.loads((D/(label+'.json')).read_text());body,top=snap['parts'][:2];base=np.array(p['vertices']).reshape(-1,3);f=features(top);dist=np.array([np.mean((f-np.array(a['feature']))**2) for a in p['anchors']]);w=1/np.maximum(dist,1e-8)**2;w*=(1-S(.025,.30,dist.min()))/w.sum();old=sum(np.array(a['deltas']).reshape(-1,3)*weight for a,weight in zip(p['anchors'],w));before,_=pose(top,base+old);anchor=json.loads((W/(label+'-anchor.json')).read_text());after,_=pose(top,base+np.array(anchor['deltas']).reshape(-1,3));bp=xf(np.array(body['rendererToRoot']).reshape(4,4),arr(body,'posedVertices',3));bt=arr(body,'triangles',3).astype(int);tt=arr(top,'triangles',3).astype(int)
   # Display crop only: all original Body is retained in collision/reference
   # data. Exclude heads/legs here so adjacent sampled-row bodies cannot
   # occlude one another. This never changes the production Body asset.
   rest=xf(np.array(body['rendererToRoot']).reshape(4,4),arr(body,'vertices',3));ids=arr(body,'indices',4).astype(int);weights=arr(body,'weights',4);headIds=[body['bones'].index(n) for n in ['Head','Neck']];head=(weights*np.isin(ids,headIds)).sum(1);display=(rest[:,1]>.99)&(head<.5);bt=bt[display[bt].all(1)]
   for col,(q,n) in enumerate(((before,'BEFORE'),(after,'AFTER'))):mesh(f'{row}_{n}_BodyTorso',bp,bt,skin,(col*.85,-row*.88));mesh(f'{row}_{n}_Top',q,tt,cloth,(col*.85,-row*.88))
  sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=1500;sc.render.resolution_y=1900;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('Same studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.4,.43,.47,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.3;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';target=Vector((.425,0,.38))
  for pos,power,size in [((-.7,-2,3),420,3),((2,-1,1.7),160,3)]:
   bpy.ops.object.light_add(type='AREA',location=pos);ob=bpy.context.object;ob.data.energy=power;ob.data.size=size;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
  bpy.ops.object.camera_add(location=(.425,-4.5,.65));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.94;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;sc.render.filepath=str(W/f'{sex.lower()}_{action}_source-before-after.png');bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{sex}_{action}_TorsoProof.blend'))
