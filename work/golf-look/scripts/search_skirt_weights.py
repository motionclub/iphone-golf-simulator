"""Read-only search for a compact skirt envelope across the eight actual poses."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Matrix
W=Path(__file__).resolve().parents[1]
rig=bpy.data.objects['Rig_Female'];body=bpy.data.objects['Body_F'];sc=bpy.context.scene
names={g.index:g.name for g in body.vertex_groups}
ids=[v.index for v in body.data.vertices if .68<v.co.z<1.025 and abs(v.co.x)<.32 and sum(g.weight for g in v.groups if names[g.group] in ['Hips','Spine','LeftUpperLeg','RightUpperLeg'])>.35]
bind=np.array([tuple(body.data.vertices[i].co) for i in ids]);rest={b.name:np.array(rig.matrix_world@b.matrix_local) for b in rig.data.bones}
poses=[]
for act in [a for a in bpy.data.actions if a.name=='ReadyIdle' or (a.name.startswith('GolfProof_') and '.' not in a.name)]:
 rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 sc.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);me=ev.to_mesh()
 co=np.array([tuple(me.vertices[i].co) for i in ids]);ev.to_mesh_clear()
 m=np.array(ev.matrix_world);co=co@m[:3,:3].T+m[:3,3]
 skin={n:np.array(rig.matrix_world@rig.pose.bones[n].matrix)@np.linalg.inv(rest[n]) for n in rest}
 poses.append((act.name,co,skin))
assert len(poses)==8
rows=[]
for coeff in [0,.1,.2,.3,.4,.5,.6]:
 for split in [.08,.16,.24]:
  t=np.clip((.995-bind[:,2])/(.995-.68),0,1);leg=coeff*t
  s=np.clip((bind[:,0]+split)/ (2*split),0,1);s=s*s*(3-2*s)
  clouds=[]
  for _,co,skin in poses:
   mats=(1-leg)[:,None,None]*skin['Hips']+(leg*s)[:,None,None]*skin['LeftUpperLeg']+(leg*(1-s))[:,None,None]*skin['RightUpperLeg']
   inv=np.linalg.inv(mats);clouds.append(np.einsum('nij,nj->ni',inv[:,:3,:3],co)+inv[:,:3,3])
  cloud=np.concatenate(clouds);rings=[]
  for z in [.995,.96,.92,.88,.84,.80,.76,.72]:
   near=cloud[np.abs(cloud[:,2]-z)<.03]
   if len(near)<20:near=cloud[np.argsort(np.abs(cloud[:,2]-z))[:200]]
   rings.append(dict(z=z,width=float(np.ptp(near[:,0])),depth=float(np.ptp(near[:,1]))))
  row=dict(coefficient=coeff,split=split,rings=rings,score=max(r['width']+r['depth'] for r in rings),max_displacement_mm=float(np.linalg.norm(np.array(clouds)-bind,axis=-1).max()*1000))
  rows.append(row)
rows.sort(key=lambda r:r['score'])
(W/'data/skirt_weight_search.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows[:4],indent=2),flush=True)
