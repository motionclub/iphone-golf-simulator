"""Measure body poke-through along the posed skin's outward surface normals."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,mesh_tris,evaluated_co,activate_clip
from follow_lib import bvh_from
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];sc=bpy.context.scene;rig.data.pose_position='REST';bpy.context.view_layer.update();P=mesh_co(body);T=mesh_tris(body.data)
groups={g.index:g.name for g in body.vertex_groups};dominant=[groups[max(v.groups,key=lambda g:g.weight).group] if v.groups else '' for v in body.data.vertices]
def cover(i):
 p=P[i];bone=dominant[i]
 if any(k in bone for k in ['Foot','Toes']):return 'Shoe_L' if bone.startswith('Left') else 'Shoe_R'
 if any(k in bone for k in ['UpperLeg','LowerLeg','Hips','Spine']) and (.120 if sex=='Male' else .825)<p[2]<1.005:return 'Bottom'
 if p[2]<.985:return None
 if bone in ['Spine','Chest','UpperChest'] or 'Shoulder' in bone:return 'Top'
 if 'UpperArm' in bone:
  side='Left' if bone.startswith('Left') else 'Right';b=rig.data.bones[side+'UpperArm'];axis=b.tail_local-b.head_local;t=(Vector(tuple(p))-b.head_local).dot(axis)/axis.length_squared
  if t<.70:return 'Top'
 return None
classification=[cover(i) for i in range(len(P))];covered={k:np.array([t for t in T if all(classification[i]==k for i in t)]) for k in ['Top','Bottom','Shoe_L','Shoe_R']}
def piece(o):
 n=o.name
 if n=='Golf_Polo':return 'Top'
 if n.startswith(('Golf_Trousers','Golf_PleatedSkort','Golf_InnerShorts')):return 'Bottom'
 for side in ['L','R']:
  if n.startswith(('Golf_Shoe_'+side,'Golf_SaddlePanel_'+side,'Golf_Nub_'+side)):return 'Shoe_'+side
 return None
objects=[o for o in bpy.data.objects if o.type=='MESH' and piece(o)];rows=[];rig.data.pose_position='POSE'
def apply():
 for o in objects:
  if not o.get('GolfCorrectiveProfile') or not o.data.shape_keys:continue
  pr=json.loads(o['GolfCorrectiveProfile']);dirs=np.array([np.array(rig.pose.bones[b].head)-np.array(rig.pose.bones[a].head) for a,b in pr['segments']]);dirs/=np.maximum(np.linalg.norm(dirs,axis=1)[:,None],1e-10);f=np.array([dirs[i]@dirs[j] for i in range(8) for j in range(i+1,8)]);ds=np.array([np.mean((f-a['feature'])**2) for a in pr['anchors']]);wt=np.maximum(ds,1e-10)**-2;wt/=wt.sum()
  for k,a in enumerate(pr['anchors'][1:],1):o.data.shape_keys.key_blocks[a['shape']].value=float(wt[k])
 bpy.context.view_layer.update()
for hand in ['RH','LH']:
 for state in ['ReadyIdle','Top','Impact','Finish']:
  action='ReadyIdle' if hand=='RH' and state=='ReadyIdle' else f'GolfProof_{hand}_{state}';activate_clip(rig,action);sc.frame_set(-1);sc.frame_set(0);bpy.context.view_layer.update();apply();dg=bpy.context.evaluated_depsgraph_get();B=evaluated_co(body,dg)
  bm=body.evaluated_get(dg).to_mesh();N=np.array([v.normal[:] for v in bm.vertices]);body.evaluated_get(dg).to_mesh_clear();results=[]
  for kind,tri in covered.items():
   verts=[];faces=[]
   for o in objects:
    if piece(o)!=kind:continue
    q=evaluated_co(o,dg);ot=mesh_tris(o.data);faces.extend((ot+len(verts)).tolist());verts.extend(q.tolist())
   tree=bvh_from(np.array(verts),np.array(faces));points=np.concatenate([B[np.unique(tri)],B[tri].mean(1),(B[tri[:,0]]+B[tri[:,1]])*.5,(B[tri[:,1]]+B[tri[:,2]])*.5,(B[tri[:,2]]+B[tri[:,0]])*.5]);normals=np.concatenate([N[np.unique(tri)],N[tri].mean(1),(N[tri[:,0]]+N[tri[:,1]])*.5,(N[tri[:,1]]+N[tri[:,2]])*.5,(N[tri[:,2]]+N[tri[:,0]])*.5]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-10)
   distances=[];missing=0;worst=None;maximum=0
   for p,n in zip(points,normals):
    origin=Vector(tuple(p));direction=Vector(tuple(n));loc,normal,idx,d=tree.ray_cast(origin,direction,.15)
    if loc is not None:distances.append(-d);continue
    loc,normal,idx,d=tree.ray_cast(origin,-direction,.15)
    if loc is None:missing+=1;continue
    distances.append(d)
    if d>maximum:maximum=d;worst=p.tolist()
   v=np.array(distances);r=dict(piece=kind,coveredBodyTriangles=len(tri),samples=len(points),unresolvedRays=missing,pokeMaxMm=maximum*1000,over3mm=int((v>.003).sum()),worstWorld=worst);results.append(r)
  rows.append(dict(action=action,pieces=results));print(action,[(r['piece'],round(r['pokeMaxMm'],2),r['over3mm'],r['unresolvedRays']) for r in results],flush=True)
(W/f'data/body_cover_{sex}.json').write_text(json.dumps(dict(sex=sex,scope='declared torso/sleeve, lower-body and shoe regions; all fully covered body triangles sampled at vertices, centroids and edge midpoints; outward posed skin-normal rays through the complete corresponding garment; boundary triangles, unsampled interiors, glove and headwear still require proof',poses=rows),indent=2)+'\n')
