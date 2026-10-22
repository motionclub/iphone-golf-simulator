import pathlib,json,bpy,numpy as np
from mathutils import Vector
R=pathlib.Path.cwd();W=R/'work/reference-rebuild/garment-weight-transition/mask-check';SEWN=R/'work/reference-rebuild/garment-weight-transition/sewn-panel';D=R/'proof/reference-rebuild/character-cloth14/poses'
q=(R/'work/reference-rebuild/garment-stroke-coverage/author_stroke_envelopes.py').read_text();exec(q[q.index('def arr('):q.index('def author(')])
def material(name,c):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*c,1);n.inputs['Roughness'].default_value=.76;n.inputs['Specular IOR Level'].default_value=.15
 # Match actual opaque renderer's Cull Back in source proof.
 geo=m.node_tree.nodes.new('ShaderNodeNewGeometry');trans=m.node_tree.nodes.new('ShaderNodeBsdfTransparent');mix=m.node_tree.nodes.new('ShaderNodeMixShader');out=m.node_tree.nodes['Material Output'];m.node_tree.links.new(geo.outputs['Backfacing'],mix.inputs[0]);m.node_tree.links.new(n.outputs[0],mix.inputs[1]);m.node_tree.links.new(trans.outputs[0],mix.inputs[2]);m.node_tree.links.new(mix.outputs[0],out.inputs['Surface']);return m

def mesh(name,p,t,m,offset):
 q=np.column_stack([p[:,0]+offset[0],-p[:,2],p[:,1]+offset[1]]);me=bpy.data.meshes.new(name);me.from_pydata(q.tolist(),[],t.tolist());me.update();me.materials.append(m);ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
 for f in me.polygons:f.use_smooth=True
 return ob
for sex in ('male','female'):
 b=json.loads((D/f'{sex}_Forehand_1.json').read_text())['parts'][0];rt=np.array(b['rendererToRoot']).reshape(4,4);rest=xf(rt,arr(b,'vertices',3));tri=arr(b,'triangles',3).astype(int);idx=arr(b,'indices',4).astype(int);weights=arr(b,'weights',4);names=b['bones'];bind=rt[None]@np.linalg.inv(np.array(b['bindposes']).reshape(-1,4,4));head=(weights*np.isin(idx,[names.index('Head'),names.index('Neck')])).sum(1);armIDs=[names.index(n) for n in ['LeftUpperArm','RightUpperArm','LeftLowerArm','RightLowerArm']];arm=(weights*np.isin(idx,armIDs)).sum(1);torso=(rest[:,1]>(1.125 if sex=='male' else 1.11))&(rest[:,1]<(1.407 if sex=='male' else 1.354))&(arm<.45)&(head<.035)
 sleeve=np.zeros(len(rest),bool)
 for side in ('Left','Right'):
  a=bind[names.index(side+'UpperArm'),:3,3];c=bind[names.index(side+'LowerArm'),:3,3];axis=c-a;t=(rest-a)@axis/(axis@axis);mass=(weights*np.isin(idx,[names.index(side+'UpperArm'),names.index(side+'Shoulder')])).sum(1);sleeve|=(mass>.25)&(t<(.30 if sex=='male' else .32))&(rest[:,1]>(1.175 if sex=='male' else 1.145))&(head<.035)
 mask=torso|sleeve;remove=mask[tri].all(1);data={'sex':sex,'bodyVertexCount':len(rest),'bodyTriangleCount':len(tri),'alwaysCoveredFaceIndices':np.where(remove)[0].tolist(),'removedTriangles':int(remove.sum()),'sourceRestVertices':b['vertices'],'sourceTriangles':b['triangles'],'basis':b['rendererToRoot'],'contract':'Conservative outfit render mask only. Complete editable Body retained. Torso above waist margin, below collar/neck; upper arm mask stops well inside mid-bicep sleeve. All face/neck/exposed arm/hand/leg coordinates and weights unchanged.'};(W/f'BodyMask_{sex}.json').write_text(json.dumps(data,separators=(',',':')));print(sex,'mask',data['removedTriangles'],flush=True)
 for action in ('Serve','Forehand'):
  bpy.ops.wm.read_factory_settings(use_empty=True);skin=material('Unchanged Body display',(.57,.29,.17));cloth=material('Same cloth - CullBack',(.70,.105,.060) if sex=='male' else (.35,.53,.05))
  for row in range(3):
   q=np.load(SEWN/f'{sex}_{action}_{row}.npz');bp=q['body'];bt=q['bodyTriangles'];display=(rest[:,1]>.99)&(head<.5);baseFaces=display[bt].all(1);masked=baseFaces&~remove
   for col,variant in enumerate(('control','mask-original','mask-sewn')):
    btRender=bt[baseFaces if col==0 else masked];top=q['before'] if col<2 else q['after'];tt=q['beforeTriangles'] if col<2 else q['topTriangles'];mesh(f'{row}_{variant}_Body',bp,btRender,skin,(col*.85,-row*.88));mesh(f'{row}_{variant}_Top',top,tt,cloth,(col*.85,-row*.88))
  sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=20;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=2000;sc.render.resolution_y=1900;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('Same studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.4,.43,.47,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.3;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';target=Vector((.85,0,.40))
  for pos,power,size in [((-.7,-2,3),420,3),((2,-1,1.7),160,3)]:
   bpy.ops.object.light_add(type='AREA',location=pos);ob=bpy.context.object;ob.data.energy=power;ob.data.size=size;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
  bpy.ops.object.camera_add(location=(.85,-4.5,.65));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=3.08;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;sc.render.filepath=str(W/f'{sex}_{action}_control-mask-sewn.png');bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{sex}_{action}_MaskComparison.blend'))
