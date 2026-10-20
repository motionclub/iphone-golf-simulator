"""Garment-only shoulder pose correctives on the continuous articulated hero.
The eight anchors and their actual bone features remain editable in the master.
"""
import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_'+('F' if sex=='Female' else 'M')];polo=bpy.data.objects['Golf_Polo'];sc=bpy.context.scene
names=[b.name for b in rig.data.bones];index={n:i for i,n in enumerate(names)};restInv=np.array([np.array(b.matrix_local.inverted()) for b in rig.data.bones]);weights=np.zeros((len(polo.data.vertices),len(names)))
for v in polo.data.vertices:
 for g in v.groups:
  nm=polo.vertex_groups[g.group].name
  if nm in index:weights[v.index,index[nm]]=g.weight
for tr in rig.animation_data.nla_tracks:tr.mute=True
if polo.data.shape_keys:polo.data.shape_keys.animation_data_clear()
for key in list(polo.data.shape_keys.key_blocks):
 if key.name.startswith('GolfShoulder_'):polo.shape_key_remove(key)
for key in polo.data.shape_keys.key_blocks:key.value=0
anchors=[]
def feature():
 R=np.array(rig.pose.bones['UpperChest'].matrix)[:3,:3];out=[]
 for side in ['Left','Right']:
  for a,b in [('UpperArm','LowerArm'),('LowerArm','Hand')]:
   v=np.array(rig.pose.bones[side+b].head)-np.array(rig.pose.bones[side+a].head);v/=np.linalg.norm(v);out.extend(R.T@v)
 return list(map(float,out))
rig.data.pose_position='POSE'
for motion,hand,t in [('AddressIron','RH',0)]+[(m,h,t) for m,t in [('Drive',1.55),('Drive',3.4),('BallPickup',1.15),('GoodShot',1.0)] for h in ['RH','LH']]:
 rig.animation_data.action=bpy.data.actions[f'{motion}_{sex}_{hand}'];sc.frame_set(round(t*120));bpy.context.view_layer.update();f=feature()
 if motion=='AddressIron':anchors.append(dict(name=None,features=f));continue
 coverage=body.modifiers.get('Golf outfit coverage')
 # Visible skin is the collision target; covered body faces remain reversible.
 if coverage:coverage.show_viewport=True
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();bo=body.evaluated_get(deps);bm=bo.to_mesh();bm.calc_loop_triangles();bvh=BVHTree.FromPolygons([bo.matrix_world@v.co for v in bm.vertices],[tuple(p.vertices) for p in bm.loop_triangles],all_triangles=True)
 po=polo.evaluated_get(deps);pm=po.to_mesh();key=polo.shape_key_add(name='GolfShoulder_'+str(len(anchors)-1),from_mix=False)
 for point,base in zip(key.data,polo.data.shape_keys.key_blocks['Basis'].data):point.co=base.co
 mat=np.array([np.array(b.matrix) for b in rig.pose.bones])@restInv
 moved=0;maximum=0
 for v in polo.data.vertices:
  if v.co.z<.930:continue
  point=po.matrix_world@pm.vertices[v.index].co;nearest,normal,_,distance=bvh.find_nearest(point)
  signed=(point-nearest).dot(normal)
  if signed>=.004 or distance>.035:continue
  delta=np.array(normal)*(.004-signed);skin=np.einsum('b,bij->ij',weights[v.index],mat)[:3,:3]
  U,S,V=np.linalg.svd(skin);offset=V.T@((U.T@delta)/np.maximum(S,.5));length=float(np.linalg.norm(offset));maximum=max(maximum,length)
  if length>.080:raise RuntimeError('Shoulder correction exceeds 80 mm; refine weights first: '+str((v.index,tuple(v.co),signed,length,[(names[i],float(w)) for i,w in enumerate(weights[v.index]) if w>0],np.linalg.svd(skin)[1].tolist())))
  key.data[v.index].co=polo.data.shape_keys.key_blocks['Basis'].data[v.index].co+Vector(offset);moved+=1
 # Regularize the garment delta field before baking it. Independent nearest
 # surface pushes can create spikes across short trim edges.
 adjacency=[[] for v in polo.data.vertices]
 for edge in polo.data.edges:
  a,b=edge.vertices;adjacency[a].append(b);adjacency[b].append(a)
 base=np.array([v.co[:] for v in polo.data.shape_keys.key_blocks['Basis'].data]);delta=np.array([v.co[:] for v in key.data])-base
 for iteration in range(6):
  averaged=delta.copy()
  for i,neighbors in enumerate(adjacency):
   if neighbors:averaged[i]=delta[i]*.5+delta[neighbors].mean(0)*.5
  delta=averaged
 for point,co in zip(key.data,base+delta):point.co=co
 anchors.append(dict(name=key.name,features=f,movedVertices=moved,maxDeltaM=maximum))
 bo.to_mesh_clear();po.to_mesh_clear();
 if coverage:coverage.show_viewport=True
 print('POLO_ANCHOR',sex,motion,hand,moved,maximum,flush=True)
(W/f'data/shoulder_anchors_{sex}.json').write_text(json.dumps(anchors,indent=2)+'\n')
rig.animation_data.action=bpy.data.actions[f'Drive_{sex}_RH'];sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(W/f'export/Golf_{sex}_Dressed.blend'),compress=True)
print('POLO_FIT_COMPLETE',sex,flush=True)
