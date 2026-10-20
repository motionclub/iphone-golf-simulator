"""Candidate garment rest-position correction across the eight proof poses.

Frozen body, rig and actions are read only. This is an iterative candidate fit,
not a G7 certificate: triangle interiors and garment edges still need checking.
"""
import bpy,sys,json,hashlib,shutil
import numpy as np
from pathlib import Path
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,mesh_tris,evaluated_co,activate_clip,bone_weight_matrix
from follow_lib import bvh_from
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];sc=bpy.context.scene
rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M']
bones=[b.name for b in rig.data.bones];rest=np.stack([np.array(b.matrix_local.inverted()) for b in rig.data.bones])
identity=lambda:hashlib.sha256(repr(([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in body.data.vertices],[(b.name,tuple(map(tuple,b.matrix_local))) for b in rig.data.bones])).encode()).hexdigest()
before=identity();body_tri=mesh_tris(body.data)
poses=[]
for hand in ['RH','LH']:
 for state in ['ReadyIdle','Top','Impact','Finish']:
  act='ReadyIdle' if hand=='RH' and state=='ReadyIdle' else f'GolfProof_{hand}_{state}'
  activate_clip(rig,act);sc.frame_set(0);bpy.context.view_layer.update()
  co=evaluated_co(body,bpy.context.evaluated_depsgraph_get())
  M=np.stack([np.array(rig.matrix_world@rig.pose.bones[n].matrix)@rest[j] for j,n in enumerate(bones)])
  poses.append((act,bvh_from(co,body_tri),M))
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
sc.frame_set(0);bpy.context.view_layer.update();bv=bvh_from(evaluated_co(body,bpy.context.evaluated_depsgraph_get()),body_tri)
rows=[]
names=['Golf_Polo','Golf_Trousers' if sex=='Male' else 'Golf_InnerShorts','Golf_Shoe_L','Golf_Shoe_R']
for name in names:
 o=bpy.data.objects[name];initial=mesh_co(o);co=initial.copy();weights=bone_weight_matrix(o,bones)
 matrices=[np.einsum('vb,bij->vij',weights,M) for _,_,M in poses]
 wall=np.array([v.normal.dot(bv.find_nearest(tuple(v.co))[1]) for v in o.data.vertices])
 clearance=np.where(wall>.15,.0045,.0025)
 history=[]
 for iteration in range(12):
  corrections=np.zeros_like(co);worst=np.zeros(len(co));inside=0
  for (act,tree,_),M in zip(poses,matrices):
   posed=np.einsum('vij,vj->vi',M[:,:3,:3],co)+M[:,:3,3]
   for i,p in enumerate(posed):
    loc,n,idx,dist=tree.find_nearest(tuple(p),.04)
    if loc is None:continue
    normal=np.array(n);signed=np.dot(p-np.array(loc),normal)
    violation=clearance[i]-signed
    if violation>0:
     inside+=1;grad=M[i,:3,:3].T@normal
     delta=grad*(violation/max(np.dot(grad,grad),1e-8))
     if violation>worst[i]:worst[i]=violation;corrections[i]=delta
  length=np.linalg.norm(corrections,axis=1);corrections*=np.minimum(1,.003/np.maximum(length,1e-9))[:,None]
  co+=corrections*.7
  displacement=co-initial;length=np.linalg.norm(displacement,axis=1)
  co=initial+displacement*np.minimum(1,.028/np.maximum(length,1e-9))[:,None]
  history.append(dict(iteration=iteration,max_violation_mm=float(worst.max()*1000),candidate_samples=inside,moved=int((worst>0).sum())))
  print('CLEARANCE',sex,name,history[-1],flush=True)
  if worst.max()<.0003:break
 for v,p in zip(o.data.vertices,co):v.co=p
 o.data.update()
 rows.append(dict(piece=name,vertices=len(co),max_bind_change_mm=float(np.linalg.norm(co-initial,axis=1).max()*1000),history=history))
assert before==identity(),'Frozen body or rig changed'
activate_clip(rig,'ReadyIdle');sc.frame_set(0)
path=Path(bpy.data.filepath);backup=W/'rollback/clearance_inputs'/path.name;backup.parent.mkdir(exist_ok=True)
if not backup.exists():shutil.copy2(path,backup)
bpy.ops.wm.save_as_mainfile(filepath=str(path))
# Sync ONLY corrected candidate garment coordinates to the corresponding draft.
values={n:[tuple(v.co) for v in bpy.data.objects[n].data.vertices] for n in names}
draft=W/f'export/Golf_{sex}_Draft.blend';backup=W/'rollback/clearance_inputs'/draft.name
if not backup.exists():shutil.copy2(draft,backup)
bpy.ops.wm.open_mainfile(filepath=str(draft))
for n,coords in values.items():
 o=bpy.data.objects[n];assert len(o.data.vertices)==len(coords)
 for v,p in zip(o.data.vertices,coords):v.co=p
 o.data.update()
bpy.ops.wm.save_as_mainfile(filepath=str(draft))
(W/f'data/clearance_fit_{sex}.json').write_text(json.dumps(dict(sex=sex,rows=rows,body_rest_unchanged=True,status='candidate fit; rerun independent G7 diagnostics and own-eye crops'),indent=2)+'\n')
