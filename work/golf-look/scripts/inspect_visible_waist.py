"""Trace exposed waist pixels to frozen body triangles; no mesh edits."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import evaluated_co,mesh_tris,activate_clip
from follow_lib import bvh_from
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];sc=bpy.context.scene
bt=mesh_tris(body.data);gn={g.index:g.name for g in body.vertex_groups};rows=[]
for state in ['ReadyIdle','Top','Impact','Finish']:
 activate_clip(rig,'ReadyIdle' if state=='ReadyIdle' else 'GolfProof_RH_'+state);sc.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();b=evaluated_co(body,dg);bodyTree=bvh_from(b,bt)
 coords=[];tris=[];offset=0
 for o in bpy.data.objects:
  if o.type!='MESH' or not o.name.startswith('Golf_') or o.name=='Golf_Glove_Right':continue
  co=evaluated_co(o,dg);t=mesh_tris(o.data);coords.extend(co.tolist());tris.extend((t+offset).tolist());offset+=len(co)
 kitTree=bvh_from(np.array(coords),np.array(tris))
 target=Vector((0,0,.87));el=math.radians(5);az=math.radians(28);d=3.1;eye=target+Vector((d*math.cos(el)*math.sin(az),-d*math.cos(el)*math.cos(az),d*math.sin(el)))
 orient=(target-eye).to_track_quat('-Z','Y').to_matrix();counts=Counter();samples=[]
 # Full camera projection at the delivered 600x800 pose-sheet framing.
 for py in range(160,720,3):
  for px in range(60,540,3):
   ray=orient@Vector(((px+.5-300)/600*.036,(400-py-.5)/600*.036,-.050));ray.normalize()
   loc,n,t,dist=bodyTree.ray_cast(eye,ray,10)
   if loc is None:continue
   ids=bt[t];bind=np.array([tuple(body.data.vertices[i].co) for i in ids]).mean(axis=0)
   if not .45<bind[2]<1.15 or abs(bind[0])>.33:continue
   weights=Counter()
   for idx in ids:
    for g in body.data.vertices[idx].groups:weights[gn[g.group]]+=g.weight/3
   dominant=weights.most_common(1)[0][0]
   if any(k in dominant for k in ['Arm','Hand','Finger','Thumb','Index','Middle','Ring','Little']):continue
   kl,kn,kt,kd=kitTree.ray_cast(eye,ray,10)
   if kl is not None and kd<=dist+.001:continue
   counts[int(t)]+=1;samples.append(dict(x=px,y=py,triangle=int(t),kitBehindMm=(kd-dist)*1000 if kl is not None else None))
 details=[]
 for t,count in counts.most_common(24):
  vs=[body.data.vertices[i] for i in bt[t]];details.append(dict(triangle=t,pixels=count,bind=[list(v.co) for v in vs],weights=[{gn[g.group]:g.weight for g in v.groups} for v in vs]))
 row=dict(state=state,exposedWaistSamples=len(samples),triangles=details,samples=samples);rows.append(row);print(state,len(samples),[(t,c) for t,c in counts.most_common(8)],flush=True)
(W/f'data/visible_waist_{sex}.json').write_text(json.dumps(dict(source=bpy.data.filepath,scope='camera-visible waist diagnostic only; no full G7 certification',rows=rows),indent=2)+'\n')
