import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Matrix
from mathutils.kdtree import KDTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import activate_clip,evaluated_co,bone_weight_matrix,mesh_co,mesh_tris
from follow_lib import bvh_from
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];names=[b.name for b in rig.data.bones]
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
ids=[8207,8302,1975,3023,12303] if sex=='Female' else [14474,6412,12183,13273,17402]
pieces=['Golf_Polo','Golf_PleatedSkort' if sex=='Female' else 'Golf_Trousers','Golf_Shoe_L'];trees={}
for n in pieces:
 o=bpy.data.objects[n];t=KDTree(len(o.data.vertices))
 for v in o.data.vertices:t.insert(v.co,v.index)
 t.balance();trees[n]=t
rows=[]
for i in ids:
 v=body.data.vertices[i];row=dict(body_vertex=i,bind=list(v.co),normal=list(v.normal),weights={body.vertex_groups[g.group].name:g.weight for g in v.groups},pieces={})
 for n,t in trees.items():
  co,j,d=t.find(v.co);o=bpy.data.objects[n];q=o.data.vertices[j]
  if d<.08:row['pieces'][n]=dict(bind_nearest_vertex=j,bind_distance_mm=d*1000,bind_co=list(q.co),bind_normal=list(q.normal),weights={o.vertex_groups[g.group].name:g.weight for g in q.groups})
 rows.append(row)
for state in ['ReadyIdle','Top','Impact','Finish']:
 activate_clip(rig,'ReadyIdle' if state=='ReadyIdle' else 'GolfProof_RH_'+state);bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();b=evaluated_co(body,dg)
 skin=np.stack([np.array(rig.matrix_world@rig.pose.bones[n].matrix)@np.array(rig.data.bones[n].matrix_local.inverted()) for n in names])
 for n in pieces:
  o=bpy.data.objects[n];w=bone_weight_matrix(o,names);M=np.einsum('vb,bij->vij',w,skin);co=mesh_co(o);pred=np.einsum('vij,vj->vi',M[:,:3,:3],co)+M[:,:3,3];actual=evaluated_co(o,dg);tree=bvh_from(actual,mesh_tris(o.data))
  print('MATH',state,n,float(np.linalg.norm(pred-actual,axis=1).max()*1000),flush=True)
  for row in rows:
   if n in row['pieces']:
    loc,normal,idx,dist=tree.find_nearest(tuple(b[row['body_vertex']]));row['pieces'][n][state]=dict(distance_mm=dist*1000,signed_mm=float(np.dot(b[row['body_vertex']]-np.array(loc),normal)*1000),triangle=idx)
(W/f'data/clearance_lineage_diagnostics_{sex}.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2),flush=True)
