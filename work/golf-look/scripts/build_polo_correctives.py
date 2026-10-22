"""Small garment-only shoulder correctives; the locked body/rig is read-only."""
import bpy,sys,json,numpy as np,shutil
from pathlib import Path
from mathutils.kdtree import KDTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,mesh_tris,evaluated_co,activate_clip,bone_weight_matrix
from follow_lib import bvh_from
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];o=bpy.data.objects['Golf_Polo'];names=[b.name for b in rig.data.bones]
segments=[['Spine','Chest'],['Chest','Neck'],['LeftShoulder','LeftUpperArm'],['LeftUpperArm','LeftLowerArm'],['LeftLowerArm','LeftHand'],['RightShoulder','RightUpperArm'],['RightUpperArm','RightLowerArm'],['RightLowerArm','RightHand']]
def feature():
 d=np.array([np.array(rig.pose.bones[b].head)-np.array(rig.pose.bones[a].head) for a,b in segments]);d/=np.maximum(np.linalg.norm(d,axis=1)[:,None],1e-10)
 return [float(d[i]@d[j]) for i in range(8) for j in range(i+1,8)]
P=mesh_co(body);T=mesh_tris(body.data);C=mesh_co(o);wb=bone_weight_matrix(body,names);wc=bone_weight_matrix(o,names);rest=np.stack([np.array(b.matrix_local.inverted()) for b in rig.data.bones]);kd=KDTree(len(P))
for i,p in enumerate(P):kd.insert(p,i)
kd.balance();lineage=o.data.attributes.get('GolfSourceVertex');assert lineage,'Explicit source lineage is required'
source=np.array([a.value for a in lineage.data]);valid=np.linalg.norm(C-P[source],axis=1)<.030
source[~valid]=np.array([kd.find(p)[1] for p in C[~valid]])
region=(abs(C[:,0])>.10)&(abs(C[:,0])<.40)&(C[:,2]>1.05)&(C[:,2]<1.46)
outer=o.data.attributes['GolfOuterFace'];main=np.zeros(len(C),bool)
for f in o.data.polygons:
 if outer.data[f.index].value==1:
  main[list(f.vertices)]=True
region&=main;ids=np.where(region)[0];rows=[];target=[]
bind_attr=o.data.attributes.get('GolfSourceBind');assert bind_attr,'Continuous source lineage is required for cut vertices'
BP=np.array([a.vector[:] for a in bind_attr.data]);tree=bvh_from(P,T);source_tri=[];bary=[]
for i in ids:
 loc,n,ti,dist=tree.find_nearest(tuple(BP[i]));assert dist<.005,('Invalid source bind',i,dist)
 v=P[T[ti]];edges=np.column_stack([v[1]-v[0],v[2]-v[0]]);uv=np.linalg.lstsq(edges,np.array(loc)-v[0],rcond=None)[0]
 source_tri.append(T[ti]);bary.append([1-uv.sum(),uv[0],uv[1]])
source_tri=np.array(source_tri);bary=np.array(bary)
for hand in ['RH','LH']:
 for state in ['ReadyIdle','Top','Impact','Finish']:
  act='ReadyIdle' if hand=='RH' and state=='ReadyIdle' else f'GolfProof_{hand}_{state}';activate_clip(rig,act);bpy.context.scene.frame_set(0);bpy.context.view_layer.update();Q=evaluated_co(body,bpy.context.evaluated_depsgraph_get())
  M=np.stack([np.array(rig.matrix_world@rig.pose.bones[n].matrix)@rest[j] for j,n in enumerate(names)]);S=np.einsum('vb,bij->vij',wc,M)
  N=np.zeros_like(Q);f=np.cross(Q[T[:,1]]-Q[T[:,0]],Q[T[:,2]]-Q[T[:,0]])
  for j in range(3):np.add.at(N,T[:,j],f)
  N/=np.maximum(np.linalg.norm(N,axis=1)[:,None],1e-12)
  posed=np.einsum('vij,vj->vi',S[:,:3,:3],C)+S[:,:3,3]
  body_point=np.einsum('vi,vij->vj',bary,Q[source_tri]);n=np.einsum('vi,vij->vj',bary,N[source_tri]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-10)
  signed=np.einsum('vi,vi->v',posed[ids]-body_point,n);amount=np.maximum(.0035-signed,0)
  # A smooth compact shoulder correction, not a full-body collision fitter.
  shift=n*amount[:,None];delta=np.zeros_like(C);delta[ids]=np.linalg.solve(S[ids,:3,:3],shift[:,:,None])[:,:,0]
  worst=int(np.argmax(amount));print('SHOULDER',act,'max_mm',float(amount[worst]*1000),'cloth',C[ids[worst]].tolist(),'body',P[source[ids[worst]]].tolist(),flush=True)
  if np.linalg.norm(shift,axis=1).max()>.022:raise RuntimeError('Shoulder correction exceeds 22 mm')
  target.append(delta);rows.append(dict(action=act,shape='GolfShoulder_'+hand+'_'+state,feature=feature(),maxPosedShiftMm=float(np.linalg.norm(shift,axis=1).max()*1000),changedVertices=int((amount>.0001).sum())))
base=target[0];
if o.data.shape_keys:o.shape_key_clear()
o.shape_key_add(name='Basis')
for k in range(1,len(rows)):
 key=o.shape_key_add(name=rows[k]['shape']);key.data.foreach_set('co',(C+target[k]).astype(np.float32).ravel());key.value=0
# The RH Ready basis stays unchanged unless a measured correction is necessary.
for v,p in zip(o.data.vertices,C+base):v.co=p
o.data.shape_keys.key_blocks['Basis'].data.foreach_set('co',(C+base).astype(np.float32).ravel())
profile=dict(sex=sex,segments=segments,anchors=rows,scope='garment shoulder only; no body, rig, weights or rest-matrix edits')
o['GolfCorrectiveProfile']=json.dumps(profile)
activate_clip(rig,'ReadyIdle');bpy.context.scene.frame_set(0)
path=Path(bpy.data.filepath);bk=W/'rollback/polo_correctives'/path.name;bk.parent.mkdir(exist_ok=True)
if not bk.exists():shutil.copy2(path,bk)
bpy.ops.wm.save_as_mainfile(filepath=str(path));coords=[tuple(v.co) for v in o.data.vertices];keys={k.name:[tuple(v.co) for v in k.data] for k in o.data.shape_keys.key_blocks}
draft=W/f'export/Golf_{sex}_Draft.blend';bpy.ops.wm.open_mainfile(filepath=str(draft));o=bpy.data.objects['Golf_Polo'];assert len(o.data.vertices)==len(coords)
if o.data.shape_keys:o.shape_key_clear()
for v,p in zip(o.data.vertices,coords):v.co=p
for name,values in keys.items():key=o.shape_key_add(name=name);key.data.foreach_set('co',np.array(values,np.float32).ravel());key.value=0
o['GolfCorrectiveProfile']=json.dumps(profile);bpy.ops.wm.save_as_mainfile(filepath=str(draft))
(W/f'data/polo_correctives_{sex}.json').write_text(json.dumps(profile,indent=2)+'\n');print(json.dumps(profile,indent=2),flush=True)
