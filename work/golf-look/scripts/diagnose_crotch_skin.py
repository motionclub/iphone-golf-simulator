import bpy,sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,mesh_tris,evaluated_co,activate_clip,bone_weight_matrix
W=Path(__file__).resolve().parents[1];rig=bpy.data.objects['Rig_Male'];body=bpy.data.objects['Body_M'];names=[b.name for b in rig.data.bones]
P=mesh_co(body);T=mesh_tris(body.data);weights=bone_weight_matrix(body,names);rest=np.stack([np.array(b.matrix_local.inverted()) for b in rig.data.bones]);ids=np.where((abs(P[:,0])<.08)&(P[:,2]>.60)&(P[:,2]<.99))[0]
rows=[]
for hand in ['RH','LH']:
 for state in ['ReadyIdle','Top','Impact','Finish']:
  act='ReadyIdle' if hand=='RH' and state=='ReadyIdle' else f'GolfProof_{hand}_{state}'
  activate_clip(rig,act);bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();Q=evaluated_co(body,dg)
  M=np.stack([np.array(rig.matrix_world@rig.pose.bones[n].matrix)@rest[j] for j,n in enumerate(names)]);S=np.einsum('vb,bij->vij',weights,M)
  pred=np.einsum('vij,vj->vi',S[:,:3,:3],P)+S[:,:3,3];delta=np.linalg.norm(Q-pred,axis=1)
  N=np.zeros_like(Q);f=np.cross(Q[T[:,1]]-Q[T[:,0]],Q[T[:,2]]-Q[T[:,0]])
  for j in range(3):np.add.at(N,T[:,j],f)
  N/=np.maximum(np.linalg.norm(N,axis=1)[:,None],1e-12)
  bindn=np.array([v.normal[:] for v in body.data.vertices]);posedn=np.einsum('vij,vj->vi',S[:,:3,:3],bindn);dot=np.einsum('vi,vi->v',N,posedn)
  rows.append(dict(action=act,max_body_prediction_mm=float(delta.max()*1000),crotch_prediction_mm=float(delta[ids].max()*1000),negative_det=int((np.linalg.det(S[ids,:3,:3])<0).sum()),inward_normal_count=int((dot[ids]<0).sum()),normal_dot_min=float(dot[ids].min()),worst=[dict(id=int(i),bind=P[i].tolist(),dot=float(dot[i]),det=float(np.linalg.det(S[i,:3,:3]))) for i in ids[np.argsort(dot[ids])[:8]]]))
out=dict(shape_keys=None if body.data.shape_keys is None else [dict(name=k.name,value=k.value) for k in body.data.shape_keys.key_blocks],modifiers=[dict(name=m.name,type=m.type) for m in body.modifiers],rows=rows)
(W/'data/crotch_skin_diagnostic.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2),flush=True)
