"""Refine existing golf collar/placket only; frozen hero and main shell untouched."""
import bpy,sys,json,shutil,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
w=Path(__file__).resolve().parents[1];sex=sys.argv[-1];path=Path(bpy.data.filepath);bk=w/'rollback/polo_construction_r29';bk.mkdir(exist_ok=True)
for p in [path,w/f'export/Golf_{sex}_SwingProof.blend']:shutil.copy2(p,bk/p.name)
o=bpy.data.objects['Golf_Polo'];rig=bpy.data.objects['Rig_'+sex];rig.animation_data.action=None;rig.data.pose_position='REST'
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();adj=[set() for _ in o.data.vertices]
for e in o.data.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();comps=[]
for i in range(len(adj)):
 if i in seen:continue
 todo=[i];seen.add(i);ids=[]
 while todo:
  a=todo.pop();ids.append(a)
  for b in adj[a]:
   if b not in seen:seen.add(b);todo.append(b)
 comps.append(ids)
comps.sort(key=len,reverse=True);main=set(comps[0]);collar=comps[1];assert len(collar)==819
co=np.array([v.co[:] for v in o.data.vertices]);target=co.copy();o.data.calc_loop_triangles();tris=[tuple(t.vertices) for t in o.data.loop_triangles if all(i in main for i in t.vertices)];surface=BVHTree.FromPolygons(co.tolist(),tris)
# Keep the stand, shorten the lower front points into a compact self-fabric collar.
hinge=1.405 if sex=='Male' else 1.350
for i in collar:
 if co[i,1]<-.015 and co[i,2]<hinge:
  t=min(1,max(0,(hinge-co[i,2])/.070));target[i,2]=hinge+(co[i,2]-hinge)*.58;target[i,0]*=1-.10*t
# Fit the existing placket and three buttons against the existing polo exterior.
construction=[collar];rows=[]
for ids in comps[2:]:
 q=co[ids];centre=q.mean(0)
 if len(ids)<40 or abs(centre[0])>.025:continue
 isButton=len(ids)==50;construction.append(ids);height=centre[2]
 if isButton:
  hit=surface.ray_cast(Vector((float(centre[0]),-1,float(height))),Vector((0,1,0)))
  assert hit[0] is not None,(sex,height)
  target[ids,1]=hit[0].y-.004+(q[:,1]-centre[1])*.35
 else:
  mid=float(np.median(q[:,1]))
  for i in ids:
   hit=surface.ray_cast(Vector((float(co[i,0]),-1,float(co[i,2]))),Vector((0,1,0)))
   assert hit[0] is not None,(sex,i)
   target[i,1]=hit[0].y-.0025+np.clip(co[i,1]-mid,-.001,.001)
 rows.append(dict(vertices=len(ids),component='button' if isButton else 'placket'))
# Construction follows the existing Chest bone consistently in every proof pose.
for ids in construction:
 for g in o.vertex_groups:g.remove(ids)
 o.vertex_groups['Chest'].add(ids,1,'REPLACE')
 for i in ids:
  o.data.vertices[i].co=target[i]
  for k in o.data.shape_keys.key_blocks:k.data[i].co=target[i]
rig.data.pose_position='POSE';a=bpy.data.actions['ReadyIdle'];rig.animation_data.action=a
if a.slots:rig.animation_data.action_slot=a.slots[0]
bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.save_as_mainfile(filepath=str(w/f'export/Golf_{sex}_SwingProof.blend'))
(w/f'data/polo_construction_{sex}_r29.json').write_text(json.dumps(dict(rows=rows,collarVertices=len(collar),changedVertices=sum(map(len,construction)),status='candidate; own-eye/export/identity pending'),indent=2))
print('POLO_CONSTRUCTION',sex,rows,flush=True)
