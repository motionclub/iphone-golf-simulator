"""Local multi-pose fit using corresponding body normals, not nearest folds."""
import bpy,sys,json,numpy as np,shutil
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,mesh_tris,evaluated_co,activate_clip,bone_weight_matrix
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];o=bpy.data.objects['Golf_Polo'];names=[b.name for b in rig.data.bones]
P=mesh_co(body);T=mesh_tris(body.data);weights=bone_weight_matrix(body,names);rest=np.stack([np.array(b.matrix_local.inverted()) for b in rig.data.bones]);normals=[];skins=[];acts=[]
for hand in ['RH','LH']:
 for state in ['ReadyIdle','Top','Impact','Finish']:
  act='ReadyIdle' if hand=='RH' and state=='ReadyIdle' else f'GolfProof_{hand}_{state}';acts.append(act)
  activate_clip(rig,act);bpy.context.scene.frame_set(0);bpy.context.view_layer.update();Q=evaluated_co(body,bpy.context.evaluated_depsgraph_get())
  M=np.stack([np.array(rig.matrix_world@rig.pose.bones[n].matrix)@rest[j] for j,n in enumerate(names)]);S=np.einsum('vb,bij->vij',weights,M);skins.append(S)
  N=np.zeros_like(Q);f=np.cross(Q[T[:,1]]-Q[T[:,0]],Q[T[:,2]]-Q[T[:,0]])
  for j in range(3):np.add.at(N,T[:,j],f)
  N/=np.maximum(np.linalg.norm(N,axis=1)[:,None],1e-12);normals.append(N)
# Rest offset constraints are linear because body weights are retained.
A=np.stack([np.einsum('vij,vi->vj',S[:,:3,:3],N) for S,N in zip(skins,normals)])
bindn=np.array([v.normal[:] for v in body.data.vertices]);dot=np.einsum('kvi,vi->kv',A,bindn)
region=(abs(P[:,0])>.12)&(abs(P[:,0])<.34)&(P[:,2]>1.16)&(P[:,2]<1.46)&(P[:,1]>.005);ids=np.where(region & (dot.min(axis=0)<.20))[0]
initial=bindn*.0047;D=initial.copy();floor=.0008
for iteration in range(180):
 for k in range(len(acts)):
  a=A[k,ids];v=floor-np.einsum('vi,vi->v',a,D[ids]);D[ids]+=a*(np.maximum(v,0)/np.maximum(np.einsum('vi,vi->v',a,a),1e-8))[:,None]
 # Smooth the *local correction*, avoiding the rejected nearest-fold fitter.
 if iteration%6==0:
  accum=np.zeros_like(D);count=np.zeros(len(P))
  for j,l in [(0,1),(1,2),(2,0)]:
   np.add.at(accum,T[:,j],D[T[:,l]]-initial[T[:,l]]);np.add.at(accum,T[:,l],D[T[:,j]]-initial[T[:,j]])
   np.add.at(count,T[:,j],1);np.add.at(count,T[:,l],1)
  D[ids]=.88*D[ids]+.12*(initial[ids]+accum[ids]/np.maximum(count[ids,None],1))
length=np.linalg.norm(D,axis=1);res=np.einsum('kvi,vi->kv',A,D)
out=dict(selected=int(len(ids)),max_offset_mm=float(length[ids].max()*1000),per_pose_min_mm={a:float(res[k,ids].min()*1000) for k,a in enumerate(acts)},status='candidate; actual surface visibility must pass')
print(json.dumps(out),flush=True);(W/f'data/polo_fold_fit_{sex}.json').write_text(json.dumps(out,indent=2)+'\n')
if length[ids].max()>.020:raise RuntimeError('Local offset exceeds 20 mm; do not save')
kd=KDTree(len(P))
for i,p in enumerate(P):kd.insert(p,i)
kd.balance();selected=set(ids);C=mesh_co(o)
for v in o.data.vertices:
 _,i,dist=kd.find(v.co)
 if i in selected and dist<.035:
  # Move both walls equally; the 2.2 mm inward thickness is preserved.
  def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
  p=P[i];ease=.010
  v.co+=Vector(D[i]-bindn[i]*ease)
o.data.update()
for obj in list(bpy.data.objects):
 if obj.name=='Golf_SeatPanel':bpy.data.objects.remove(obj,do_unlink=True)
path=Path(bpy.data.filepath);backup=W/'rollback/polo_fold_fit'/path.name;backup.parent.mkdir(exist_ok=True)
if not backup.exists():shutil.copy2(path,backup)
activate_clip(rig,'ReadyIdle');bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(path))
coords=[tuple(v.co) for v in o.data.vertices]
draft=W/f'export/Golf_{sex}_Draft.blend';bpy.ops.wm.open_mainfile(filepath=str(draft));o=bpy.data.objects['Golf_Polo'];assert len(o.data.vertices)==len(coords)
for v,c in zip(o.data.vertices,coords):v.co=c
for obj in list(bpy.data.objects):
 if obj.name=='Golf_SeatPanel':bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(draft))
