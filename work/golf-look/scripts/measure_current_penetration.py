"""Read-only full-piece surface samples against the posed locked body."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import evaluated_co,mesh_tris,activate_clip
from follow_lib import bvh_from
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];sc=bpy.context.scene
rig.data.pose_position='POSE';pieces=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Golf_')];rows=[]
def correct():
 for o in pieces:
  if not o.get('GolfCorrectiveProfile') or not o.data.shape_keys:continue
  profile=json.loads(o['GolfCorrectiveProfile']);dirs=np.array([np.array(rig.pose.bones[b].head)-np.array(rig.pose.bones[a].head) for a,b in profile['segments']]);dirs/=np.maximum(np.linalg.norm(dirs,axis=1)[:,None],1e-10)
  feature=np.array([dirs[i]@dirs[j] for i in range(8) for j in range(i+1,8)]);dist=np.array([np.mean((feature-a['feature'])**2) for a in profile['anchors']]);weights=np.maximum(dist,1e-10)**-2;weights/=weights.sum()
  for k,a in enumerate(profile['anchors'][1:],1):o.data.shape_keys.key_blocks[a['shape']].value=float(weights[k])
 bpy.context.view_layer.update()
def inside(tree,p):
 votes=0
 for direction in [(1,.137,.347),(.219,1,.413),(.319,.179,1)]:
  origin=Vector(tuple(p));direction=Vector(direction).normalized();count=0
  for _ in range(64):
   loc,n,idx,d=tree.ray_cast(origin,direction,10)
   if loc is None:break
   count+=1;origin=loc+direction*.00001
  votes+=count%2
 return votes>=2
for hand in ['RH','LH']:
 for state in ['ReadyIdle','Top','Impact','Finish']:
  action='ReadyIdle' if hand=='RH' and state=='ReadyIdle' else f'GolfProof_{hand}_{state}';activate_clip(rig,action);sc.frame_set(-1);sc.frame_set(0);bpy.context.view_layer.update();correct();dg=bpy.context.evaluated_depsgraph_get();B=evaluated_co(body,dg);tree=bvh_from(B,mesh_tris(body.data));parts=[]
  for o in pieces:
   if o.name==('Golf_Glove_Right' if hand=='RH' else 'Golf_Glove_Left'):continue
   co=evaluated_co(o,dg);tri=mesh_tris(o.data)
   if o.name=='Golf_Polo':
    attr=o.data.attributes['GolfOuterFace'];o.data.calc_loop_triangles();valid=[q.index for q in o.data.loop_triangles if attr.data[q.polygon_index].value==1];tri=tri[valid]
   elif o.name=='Golf_Trousers':tri=tri[~(tri>=len(o.data.vertices)//2).all(axis=1)]
   if not len(tri):continue
   pts=np.concatenate([co[np.unique(tri)],co[tri].mean(axis=1),(co[tri[:,0]]+co[tri[:,1]])*.5,(co[tri[:,1]]+co[tri[:,2]])*.5,(co[tri[:,2]]+co[tri[:,0]])*.5]);signed=[];worst=None;depth=0
   for i,p in enumerate(pts):
    loc,n,idx,dist=tree.find_nearest(tuple(p));s=float((Vector(tuple(p))-loc).dot(n));
    if s<-.0001 and not inside(tree,p):s=0
    signed.append(s)
    if s<depth:depth=s;worst=p.tolist()
   signed=np.array(signed);row=dict(piece=o.name,samples=len(pts),penetrationMaxMm=-depth*1000,over3mm=int((signed<-.003).sum()),worstWorld=worst);parts.append(row)
  r=dict(action=action,pieces=parts);rows.append(r);print(action,[(p['piece'],round(p['penetrationMaxMm'],2),p['over3mm']) for p in parts if p['over3mm']],flush=True)
(W/f'data/surface_penetration_{sex}.json').write_text(json.dumps(dict(sex=sex,poses=rows,scope='all selected outer-piece vertices, triangle centroids and edge midpoints against nearest posed Body triangle; ray-validated interior depth; outer-piece vertices, triangle centroids and edge midpoints; maximum unsampled triangle radius still requires a bound'),indent=2)+'\n')
