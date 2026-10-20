"""Body poke against closed outer wear envelopes; the lining is not the wear volume."""
import bpy,bmesh,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,mesh_tris,evaluated_co,activate_clip
from follow_lib import bvh_from
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];sc=bpy.context.scene;rig.data.pose_position='REST';bpy.context.view_layer.update();P=mesh_co(body);T=mesh_tris(body.data)
groups={g.index:g.name for g in body.vertex_groups};dominant=[groups[max(v.groups,key=lambda g:g.weight).group] if v.groups else '' for v in body.data.vertices]
def region(i):
 p=P[i];bone=dominant[i]
 if any(k in bone for k in ['Foot','Toes']):return 'Shoe_L' if bone.startswith('Left') else 'Shoe_R'
 if any(k in bone for k in ['UpperLeg','LowerLeg','Hips','Spine']) and (.120 if sex=='Male' else .825)<p[2]<1.005:return 'Bottom'
 if p[2]<.985:return None
 if bone in ['Spine','Chest','UpperChest'] or 'Shoulder' in bone:return 'Top'
 if 'UpperArm' in bone:
  side='Left' if bone.startswith('Left') else 'Right';b=rig.data.bones[side+'UpperArm'];axis=b.tail_local-b.head_local
  if (Vector(tuple(p))-b.head_local).dot(axis)/axis.length_squared<.70:return 'Top'
 return None
classification=[region(i) for i in range(len(P))];covered={k:np.array([t for t in T if all(classification[i]==k for i in t)]) for k in ['Top','Bottom','Shoe_L','Shoe_R']}
names={'Top':['Golf_Polo'],'Bottom':['Golf_Trousers'] if sex=='Male' else ['Golf_PleatedSkort','Golf_InnerShorts'],'Shoe_L':['Golf_Shoe_L'],'Shoe_R':['Golf_Shoe_R']};objects=[bpy.data.objects[n] for v in names.values() for n in v];rows=[];rig.data.pose_position='POSE'
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
def envelope(o,Q):
 bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();attr=bm.faces.layers.int.get('GolfOuterFace');outer=None
 if o.name=='Golf_Polo':outer=[f for f in bm.faces if f[attr]==1]
 elif o.name.startswith(('Golf_Trousers','Golf_PleatedSkort','Golf_InnerShorts')):
  n=len(o.data.vertices)//2;outer=[f for f in bm.faces if all(v.index<n for v in f.verts)]
 if outer is not None:bmesh.ops.delete(bm,geom=[f for f in bm.faces if f not in set(outer)],context='FACES')
 for v in bm.verts:v.co=Q[v.index]
 boundary=[e for e in bm.edges if e.is_boundary];filled=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)['faces'];bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.index_update();V=np.array([v.co[:] for v in bm.verts]);F=np.array([[v.index for v in f.verts] for f in bm.faces]);count=len(filled);bm.free();return bvh_from(V,F),count
def apply():
 for o in objects:
  if not o.get('GolfCorrectiveProfile') or not o.data.shape_keys:continue
  pr=json.loads(o['GolfCorrectiveProfile']);dirs=np.array([np.array(rig.pose.bones[b].head)-np.array(rig.pose.bones[a].head) for a,b in pr['segments']]);dirs/=np.maximum(np.linalg.norm(dirs,axis=1)[:,None],1e-10);f=np.array([dirs[i]@dirs[j] for i in range(8) for j in range(i+1,8)]);ds=np.array([np.mean((f-a['feature'])**2) for a in pr['anchors']]);wt=np.maximum(ds,1e-10)**-2;wt/=wt.sum()
  for k,a in enumerate(pr['anchors'][1:],1):o.data.shape_keys.key_blocks[a['shape']].value=float(wt[k])
 bpy.context.view_layer.update()
for hand in ['RH','LH']:
 for state in ['ReadyIdle','Top','Impact','Finish']:
  action='ReadyIdle' if hand=='RH' and state=='ReadyIdle' else f'GolfProof_{hand}_{state}';activate_clip(rig,action);sc.frame_set(-1);sc.frame_set(0);bpy.context.view_layer.update();apply();dg=bpy.context.evaluated_depsgraph_get();B=evaluated_co(body,dg);results=[]
  for kind,tri in covered.items():
   volumes=[envelope(bpy.data.objects[n],evaluated_co(bpy.data.objects[n],dg)) for n in names[kind]];points=np.concatenate([B[np.unique(tri)],B[tri].mean(1),(B[tri[:,0]]+B[tri[:,1]])*.5,(B[tri[:,1]]+B[tri[:,2]])*.5,(B[tri[:,2]]+B[tri[:,0]])*.5]);depth=[];worst=None;maximum=0
   for p in points:
    if any(inside(tree,p) for tree,_ in volumes):depth.append(0);continue
    d=min(tree.find_nearest(tuple(p))[3] for tree,_ in volumes);depth.append(d)
    if d>maximum:maximum=d;worst=p.tolist()
   v=np.array(depth);r=dict(piece=kind,coveredBodyTriangles=len(tri),samples=len(points),closureFaces=sum(c for _,c in volumes),pokeMaxMm=maximum*1000,over3mm=int((v>.003).sum()),worstWorld=worst);results.append(r)
  rows.append(dict(action=action,pieces=results));print(action,[(r['piece'],round(r['pokeMaxMm'],2),r['over3mm']) for r in results],flush=True)
(W/f'data/worn_envelope_{sex}.json').write_text(json.dumps(dict(sex=sex,scope='closed outer wear envelopes with virtual cuffs/neck/hems; all declared covered-body vertices, triangle centroids and edge midpoints; remaining boundary and triangle-interior coverage plus glove/head proof required',poses=rows),indent=2)+'\n')
