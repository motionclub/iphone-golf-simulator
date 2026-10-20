"""Pose-space garment fit only; no body, bones, weights or clips are edited."""
import bpy,sys,json,numpy as np,shutil
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import mesh_co,mesh_tris,evaluated_co,bone_weight_matrix,activate_clip
from follow_lib import bvh_from
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];sc=bpy.context.scene;rig.data.pose_position='POSE'
path=Path(bpy.data.filepath);backup=W/'rollback/fit_correctives'/path.name;backup.parent.mkdir(exist_ok=True)
if not backup.exists():shutil.copy2(path,backup)
names=[b.name for b in rig.data.bones];rest=np.stack([np.array(b.matrix_local.inverted()) for b in rig.data.bones]);profile=json.loads(bpy.data.objects['Golf_Polo']['GolfCorrectiveProfile']);segments=profile['segments']
pieces=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Golf_') and not o.name.startswith(('Golf_Cap','Golf_Visor','Golf_CurvedBrim','Golf_BrimStitch','Golf_Glove'))]
base={o.name:mesh_co(o) for o in pieces};weights={o.name:bone_weight_matrix(o,names) for o in pieces};targets={o.name:[] for o in pieces};reports=[]
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
def exterior(tree,p,loc,n):
 target=np.array(loc+n*.0035)
 if not inside(tree,target) and np.linalg.norm(target-p)<.035:return target
 # A nearest triangle can be an internal face where the posed body overlaps.
 # Follow several rays to an actual exterior, choosing the shortest local exit.
 options=[]
 for direction in [n,Vector((1,0,0)),Vector((-1,0,0)),Vector((0,1,0)),Vector((0,-1,0)),Vector((0,0,1)),Vector((0,0,-1))]:
  origin=Vector(tuple(p))
  for _ in range(8):
   hit,normal,idx,d=tree.ray_cast(origin,direction,.035)
   if hit is None:break
   candidate=np.array(hit+direction*.0035)
   if np.linalg.norm(candidate-p)>.035:break
   if not inside(tree,candidate):options.append(candidate);break
   origin=hit+direction*.00001
 return min(options,key=lambda q:np.linalg.norm(q-p)) if options else None
for ai,anchor in enumerate(profile['anchors']):
 activate_clip(rig,anchor['action']);sc.frame_set(-1);sc.frame_set(0);bpy.context.view_layer.update()
 # Retain the existing shoulder solution as the initial surface in each pose.
 top=bpy.data.objects['Golf_Polo']
 for k,a in enumerate(profile['anchors'][1:],1):top.data.shape_keys.key_blocks[a['shape']].value=1 if ai==k else 0
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();B=evaluated_co(body,dg);tree=bvh_from(B,mesh_tris(body.data));M=np.stack([np.array(rig.matrix_world@rig.pose.bones[n].matrix)@rest[k] for k,n in enumerate(names)]);row=[]
 for o in pieces:
  Q=evaluated_co(o,dg);original=Q.copy();S=np.einsum('vb,bij->vij',weights[o.name],M);tris=mesh_tris(o.data)
  # Projection is accepted only after independent odd-crossing body tests.
  # Nearest-face signed values alone misclassify the concave armpit void.
  for iteration in range(3):
   shift=np.zeros_like(Q);count=np.zeros(len(Q));tests=[(i,p) for i,p in enumerate(Q)]
   for i,p in tests:
    loc,n,idx,d=tree.find_nearest(tuple(p))
    if d>.065 or (Vector(tuple(p))-loc).dot(n)>=-.0004 or not inside(tree,p):continue
    target=exterior(tree,p,loc,n)
    if target is not None:shift[i]=target-p;count[i]=1
   # Check the actual triangle interiors, distributing a centroid correction
   # to its three endpoints instead of certifying vertices alone.
   for tri in tris:
    p=Q[tri].mean(0);loc,n,idx,d=tree.find_nearest(tuple(p))
    if d>.065 or (Vector(tuple(p))-loc).dot(n)>=-.001 or not inside(tree,p):continue
    target=exterior(tree,p,loc,n)
    if target is None:continue
    delta=target-p
    for i in tri:shift[i]+=delta;count[i]+=1
   valid=count>0;shift[valid]/=count[valid,None];candidate=Q+shift
   bounded=np.linalg.norm(candidate-original,axis=1)<=.040;Q[bounded]=candidate[bounded]
   if np.linalg.norm(shift,axis=1).max()<.0002:break
  shift=Q-original;maximum=float(np.linalg.norm(shift,axis=1).max())
  if maximum>.055:raise RuntimeError((sex,anchor['action'],o.name,'fit shift too large',maximum))
  fitted=np.linalg.solve(S[:,:3,:3],(Q-S[:,:3,3])[:,:,None])[:,:,0];targets[o.name].append(fitted);row.append(dict(piece=o.name,maxShiftMm=maximum*1000,verticesChanged=int((np.linalg.norm(shift,axis=1)>.0001).sum())))
 print(anchor['action'],[(r['piece'],round(r['maxShiftMm'],2)) for r in row if r['verticesChanged']],flush=True);reports.append(dict(action=anchor['action'],pieces=row))
for a in profile['anchors']:a['shape']=a['shape'].replace('GolfShoulder_','GolfFit_')
profile['scope']='pose-space garment fit; ray-validated body clearance, original locked body/rig/weights/clips unchanged'
for o in pieces:
 if o.data.shape_keys:o.shape_key_clear()
 for v,p in zip(o.data.vertices,targets[o.name][0]):v.co=p
 o.shape_key_add(name='Basis')
 for k,a in enumerate(profile['anchors'][1:],1):key=o.shape_key_add(name=a['shape']);key.data.foreach_set('co',targets[o.name][k].astype(np.float32).ravel());key.value=0
 o['GolfCorrectiveProfile']=json.dumps(profile)
activate_clip(rig,'ReadyIdle');sc.frame_set(-1);sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(path))
payload={o.name:dict(coords=mesh_co(o),keys={k.name:[tuple(v.co) for v in k.data] for k in o.data.shape_keys.key_blocks}) for o in pieces}
draft=W/f'export/Golf_{sex}_Draft.blend';bpy.ops.wm.open_mainfile(filepath=str(draft))
for name,data in payload.items():
 o=bpy.data.objects[name];assert len(o.data.vertices)==len(data['coords'])
 if o.data.shape_keys:o.shape_key_clear()
 for v,p in zip(o.data.vertices,data['coords']):v.co=p
 for keyname,coords in data['keys'].items():key=o.shape_key_add(name=keyname);key.data.foreach_set('co',np.array(coords,np.float32).ravel());key.value=0
 o['GolfCorrectiveProfile']=json.dumps(profile)
bpy.ops.wm.save_as_mainfile(filepath=str(draft));(W/f'data/polo_correctives_{sex}.json').write_text(json.dumps(profile,indent=2)+'\n');(W/f'data/fit_correctives_{sex}.json').write_text(json.dumps(dict(sex=sex,poses=reports,scope=profile['scope'],status='candidate; full deformed shell verification required'),indent=2)+'\n')
