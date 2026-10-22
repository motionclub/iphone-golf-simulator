"""Fit the retained placket/buttons against the existing polo in all eight poses."""
import bpy,sys,json,shutil,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,evaluated_co,activate_clip
from follow_lib import bvh_from
w=Path(__file__).resolve().parents[1];sex=sys.argv[-1];path=Path(bpy.data.filepath);bk=w/'rollback/placket_pose_r32';bk.mkdir(exist_ok=True)
for p in [path,w/f'export/Golf_{sex}_SwingProof.blend']:shutil.copy2(p,bk/p.name)
o=bpy.data.objects['Golf_Polo'];rig=bpy.data.objects['Rig_'+sex];profile=json.loads(o['GolfCorrectiveProfile']);co=mesh_co(o);adj=[set() for _ in co]
for e in o.data.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();parts=[]
for i in range(len(co)):
 if i in seen:continue
 stack=[i];seen.add(i);ids=[]
 while stack:
  v=stack.pop();ids.append(v)
  for j in adj[v]:
   if j not in seen:seen.add(j);stack.append(j)
 if 40<=len(ids)<=56 and abs(co[ids].mean(0)[0])<.025:parts.append(ids)
assert len(parts)==4
outer=o.data.attributes['GolfOuterFace'];o.data.calc_loop_triangles();tris=np.array([q.vertices[:] for q in o.data.loop_triangles if outer.data[q.polygon_index].value==1 and np.linalg.norm(np.array(o.data.attributes['GolfSourceBind'].data[q.vertices[0]].vector))>.1]);rest=np.array(rig.data.bones['Chest'].matrix_local.inverted());targets=[];rows=[]
for ai,a in enumerate(profile['anchors']):
 activate_clip(rig,a['action']);bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0)
 for k,item in enumerate(profile['anchors'][1:],1):o.data.shape_keys.key_blocks[item['shape']].value=float(ai==k)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();Q=evaluated_co(o,dg);tree=bvh_from(Q,tris);M=np.array(rig.matrix_world@rig.pose.bones['Chest'].matrix)@rest;inv=np.linalg.inv(M);normal=M[:3,:3]@np.array([0,-1,0.]);normal/=np.linalg.norm(normal);N=Vector(normal);updated={}
 for ids in parts:
  isButton=len(ids)==50
  points=[Q[ids].mean(0)] if isButton else Q[ids]
  result=[]
  for p in points:
   hit,n,k,d=tree.ray_cast(Vector(p)+N*.15,-N,.4);assert hit is not None,(sex,a['action'],p)
   result.append(np.array(hit)+normal*(.004 if isButton else .0025))
  if isButton:new=Q[ids]+(result[0]-Q[ids].mean(0))
  else:new=np.array(result)+normal[None,:]*np.clip(co[ids,1]-np.median(co[ids,1]),-.001,.001)[:,None]
  for i,p in zip(ids,new):updated[i]=(inv@np.r_[p,1])[:3]
 targets.append(updated);rows.append(dict(action=a['action'],constructionVertices=len(updated),surfaceGapMm='placket 1.5–3.5, button centre 4'))
for ai,a in enumerate(profile['anchors']):
 key=o.data.shape_keys.key_blocks['Basis' if ai==0 else a['shape']]
 for i,p in targets[ai].items():
  key.data[i].co=p
  if ai==0:o.data.vertices[i].co=p
for key in o.data.shape_keys.key_blocks:key.value=0
activate_clip(rig,'ReadyIdle');bpy.context.scene.frame_set(-1);bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.save_as_mainfile(filepath=str(w/f'export/Golf_{sex}_SwingProof.blend'))
(w/f'data/placket_pose_{sex}_r32.json').write_text(json.dumps(dict(rows=rows,status='candidate; construction/identity/export pending'),indent=2));print('PLACKET_POSE',sex,flush=True)
