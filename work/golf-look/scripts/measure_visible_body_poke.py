"""Independent exposed-body diagnostic; hidden self contacts are not visible poke.
Same frozen body and the entire assembled worn kit, both handednesses.
"""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,mesh_tris,evaluated_co,activate_clip
from follow_lib import bvh_from,evaluated_normals
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];rig=bpy.data.objects['Rig_'+sex];sc=bpy.context.scene
rig.data.pose_position='REST';bpy.context.view_layer.update();B0=mesh_co(body);BT=mesh_tris(body.data);bt=bvh_from(B0,BT);home=set()
for name in ['Golf_Polo']+(['Golf_Trousers'] if sex=='Male' else []):
 o=bpy.data.objects[name];bind=np.array([q.vector[:] for q in o.data.attributes['GolfSourceBind'].data]);tri=mesh_tris(o.data)
 if name=='Golf_Polo':
  a=o.data.attributes['GolfOuterFace'];o.data.calc_loop_triangles();tri=np.array([q.vertices[:] for q in o.data.loop_triangles if a.data[q.polygon_index].value==1])
 for t in tri:
  if (np.linalg.norm(bind[t],axis=1)<.1).any():continue
  loc,n,k,d=bt.find_nearest(tuple(bind[t].mean(0)));home.add(k)
# Visible skirt region and shoe/glove patches use the authored garment extent.
groups={g.index:g.name for g in body.vertex_groups};dom=[groups[max(v.groups,key=lambda g:g.weight).group] if v.groups else '' for v in body.data.vertices]
for k,t in enumerate(BT):
 bones=[dom[i] for i in t];p=B0[t]
 if sex=='Female' and all(any(s in n for s in ['Hips','Spine','UpperLeg']) for n in bones) and p[:,2].min()>.825 and p[:,2].max()<.995:home.add(k)
 if all(any(s in n for s in ['Foot','Toes']) for n in bones) and p[:,2].max()<.11:home.add(k)
tri=BT[sorted(home)];pieces=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Golf_')];rows=[];rig.data.pose_position='POSE'
def apply():
 for o in pieces:
  if not o.get('GolfCorrectiveProfile') or not o.data.shape_keys:continue
  pr=json.loads(o['GolfCorrectiveProfile']);dirs=np.array([np.array(rig.pose.bones[b].head)-np.array(rig.pose.bones[a].head) for a,b in pr['segments']]);dirs/=np.maximum(np.linalg.norm(dirs,axis=1)[:,None],1e-10);f=np.array([dirs[i]@dirs[j] for i in range(8) for j in range(i+1,8)]);d=np.array([np.mean((f-a['feature'])**2) for a in pr['anchors']]);wt=np.maximum(d,1e-10)**-2;wt/=wt.sum()
  for k,a in enumerate(pr['anchors'][1:],1):o.data.shape_keys.key_blocks[a['shape']].value=float(wt[k])
 bpy.context.view_layer.update()
for hand in ['RH','LH']:
 for state in ['ReadyIdle','Top','Impact','Finish']:
  action='ReadyIdle' if hand=='RH' and state=='ReadyIdle' else f'GolfProof_{hand}_{state}';activate_clip(rig,action);sc.frame_set(-1);sc.frame_set(0);bpy.context.view_layer.update();apply();dg=bpy.context.evaluated_depsgraph_get();B=evaluated_co(body,dg);N=evaluated_normals(body,dg);bodyTree=bvh_from(B,BT);vertices=[];faces=[]
  for o in pieces:
   if o.name==('Golf_Glove_Right' if hand=='RH' else 'Golf_Glove_Left'):continue
   Q=evaluated_co(o,dg);T=mesh_tris(o.data);faces.extend((T+len(vertices)).tolist());vertices.extend(Q.tolist())
  garment=bvh_from(np.array(vertices),np.array(faces));points=np.concatenate([B[np.unique(tri)],B[tri].mean(1),(B[tri[:,0]]+B[tri[:,1]])*.5,(B[tri[:,1]]+B[tri[:,2]])*.5,(B[tri[:,2]]+B[tri[:,0]])*.5]);normals=np.concatenate([N[np.unique(tri)],N[tri].mean(1),(N[tri[:,0]]+N[tri[:,1]])*.5,(N[tri[:,1]]+N[tri[:,2]])*.5,(N[tri[:,2]]+N[tri[:,0]])*.5]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-10)
  exposed=[];directions=[Vector(q) for q in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]]
  for p,n in zip(points,normals):
   for d in [Vector(tuple(n))]+directions:
    if d.dot(Vector(tuple(n)))<.2:continue
    origin=Vector(tuple(p))+d*.00003
    # Self-occluded surface cannot protrude through visible clothing.
    if bodyTree.ray_cast(origin,d,10)[0] is not None:continue
    if garment.ray_cast(origin,d,10)[0] is not None:continue
    q,normal,k,dist=garment.find_nearest(tuple(p));exposed.append((dist*1000,p.tolist(),n.tolist()));break
  exposed.sort(reverse=True,key=lambda q:q[0]);row=dict(action=action,coveredBodyTriangles=len(tri),samples=len(points),exposedSamples=len(exposed),exposedOver3mm=sum(e[0]>3 for e in exposed),maximumExposedDistanceMm=exposed[0][0] if exposed else 0,worst=exposed[:15]);rows.append(row);print(action,row['exposedSamples'],row['exposedOver3mm'],round(row['maximumExposedDistanceMm'],3),flush=True)
(W/f'data/visible_body_poke_{sex}.json').write_text(json.dumps(dict(poses=rows,scope='authored corresponding body triangles; body vertices, centroids, edge midpoints; exterior skin-normal and six cardinal visibility rays against complete assembled kit; hidden contact excluded; dense interior/boundary certification and head/glove still separate'),indent=2))
