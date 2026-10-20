"""One local clearance correction from actual sampled strokes, work only."""
import bpy,pathlib,json,numpy as np,heapq
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();W=R/'work/reference-rebuild/garment-stroke-coverage';D=R/'proof/reference-rebuild/character-cloth14-control/poses';REPORT={}
def arr(p,k,n):return np.array(p[k],float).reshape(-1,n)
def xf(m,p):return p@m[:3,:3].T+m[:3,3]
def S(a,b,x):t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def pose(part,v):
 ids=arr(part,'indices',4).astype(int);w=arr(part,'weights',4);skin=np.array(part['skinMatrices']).reshape(-1,4,4);mix=np.sum(skin[ids]*w[:,:,None,None],axis=1);q=np.einsum('nij,nj->ni',mix,np.column_stack([v,np.ones(len(v))]))[:,:3];return xf(np.array(part['rendererToRoot']).reshape(4,4),q),mix
segments=[('Spine','Chest'),('Chest','Neck'),('LeftShoulder','LeftUpperArm'),('LeftUpperArm','LeftLowerArm'),('LeftLowerArm','LeftHand'),('RightShoulder','RightUpperArm'),('RightUpperArm','RightLowerArm'),('RightLowerArm','RightHand')]
def features(top):
 bone=np.array(top['rendererToRoot']).reshape(4,4)[None,:,:]@np.array(top['skinMatrices']).reshape(-1,4,4)@np.linalg.inv(np.array(top['bindposes']).reshape(-1,4,4));dirs=[]
 for a,b in segments:
  v=bone[top['bones'].index(b),:3,3]-bone[top['bones'].index(a),:3,3];dirs.append(v/np.linalg.norm(v))
 return np.array([dirs[i]@dirs[j] for i in range(8) for j in range(i+1,8)])
def geom_normals(v,t):
 n=np.zeros_like(v);area=np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]])
 for j in range(3):np.add.at(n,t[:,j],area)
 return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12),area

def author(sex,label,profile):
 snap=json.loads((D/(label+'.json')).read_text());body,top=snap['parts'][:2];tm=np.array(top['rendererToRoot']).reshape(4,4);base=np.array(profile['vertices']).reshape(-1,3);assert np.max(np.linalg.norm(base-arr(top,'vertices',3),axis=1))<.00005
 f=features(top);dist=np.array([np.mean((f-np.array(a['feature']))**2) for a in profile['anchors']]);w=1/np.maximum(dist,1e-8)**2;w*=(1-S(.025,.30,dist.min()))/w.sum();oldDelta=sum(np.array(a['deltas']).reshape(-1,3)*p for a,p in zip(profile['anchors'],w));oldDn=sum(np.array(a['normalDeltas']).reshape(-1,3)*p for a,p in zip(profile['anchors'],w));before,mix=pose(top,base+oldDelta)
 bp=xf(np.array(body['rendererToRoot']).reshape(4,4),arr(body,'posedVertices',3));bt=arr(body,'triangles',3).astype(int);tt=arr(top,'triangles',3).astype(int);br=xf(tm,base);bn,_=geom_normals(bp,bt);bvh=BVHTree.FromPolygons([Vector(p) for p in bp],[tuple(t) for t in bt],all_triangles=True)
 def hit(p):
  h,n,idx,d=bvh.find_nearest(Vector(p));return np.array(h),np.array(n),float((Vector(p)-h).dot(n)),idx,d
 # Coordinate-coincident UV aliases are one physical garment vertex.
 groups={};parent=np.array([groups.setdefault(tuple(np.round(p*1e5).astype(int)),len(groups)) for p in base]);count=len(groups);sizes=np.bincount(parent);gBefore=np.zeros((count,3));np.add.at(gBefore,parent,before);gBefore/=sizes[:,None];gRest=np.zeros((count,3));np.add.at(gRest,parent,br);gRest/=sizes[:,None]
 edges=np.unique(np.sort(np.concatenate([parent[tt[:,[0,1]]],parent[tt[:,[1,2]]],parent[tt[:,[2,0]]]]),axis=1),axis=0);edges=edges[edges[:,0]!=edges[:,1]];adj=[set() for _ in range(count)]
 for a,b in edges:adj[a].add(int(b));adj[b].add(int(a))
 component=np.arange(count)
 def find(i):
  while component[i]!=i:component[i]=component[component[i]];i=component[i]
  return i
 for a,b in edges:
  a=find(a);b=find(b)
  if a!=b:component[b]=a
 comp=np.array([find(i) for i in range(count)]);labels,num=np.unique(comp,return_counts=True);main=labels[num.argmax()]
 # Main sewn sleeve/gusset/side panel only. Detached cuffs, collar, placket,
 # hems and shoulder piping preserve the inherited blended geometry exactly.
 allowed=(comp==main)&(gRest[:,1]>1.075)&(gRest[:,1]<(1.415 if sex=='Male' else 1.36))&(np.abs(gRest[:,0])>.055)&(np.abs(gRest[:,0])<.288)
 # Preserve the open sewn shell boundary, including collar and sleeve edge.
 ge=parent[tt];ec={}
 for tri in ge:
  for a,b in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
   if a!=b:key=tuple(sorted((int(a),int(b))));ec[key]=ec.get(key,0)+1
 boundary=set(v for edge,n in ec.items() if n==1 for v in edge);allowed[list(boundary)]=False
 signed=np.array([hit(p)[2] for p in gBefore]);near=np.array([hit(p)[4] for p in gBefore]);seeds=allowed&(signed<.004)&(near<.055);distance=np.full(count,np.inf);queue=[]
 for i in np.where(seeds)[0]:distance[i]=0;heapq.heappush(queue,(0.,int(i)))
 while queue:
  d,i=heapq.heappop(queue)
  if d!=distance[i] or d>.028:continue
  for j in adj[i]:
   nd=d+np.linalg.norm(gRest[j]-gRest[i])
   if allowed[j] and nd<distance[j]:distance[j]=nd;heapq.heappush(queue,(nd,j))
 support=(1-S(.006,.028,distance))*allowed;target=gBefore.copy();delta=np.zeros_like(target)
 for i in np.where(seeds)[0]:
  h,n,gap,_,_=hit(gBefore[i]);delta[i]=n*max(0,.006-gap)
 # Smooth only correction vectors, not the existing garment volume or folds.
 # Clearance is enforced afterward; no new sculpt direction or body edits.
 for _ in range(12):
  new=delta.copy()
  for i in np.where(support>.0001)[0]:
   if adj[i]:new[i]+=(delta[list(adj[i])].mean(0)-delta[i])*.23*support[i]
  delta=new
 delta*=support[:,None];length=np.linalg.norm(delta,axis=1);limit=length>.045;delta[limit]*=(.045/length[limit])[:,None];target=gBefore+delta
 for _ in range(5):
  for i in np.where(seeds)[0]:
   h,n,gap,_,_=hit(target[i])
   if gap<.006:target[i]+=n*(.006-gap)
 # Keep paired aliases exact. Each source duplicate retains its original
 # tiny posed offset, with a shared physical displacement field.
 change=target-gBefore;after=before+change[parent];fixed=support[parent]<.0001;after[fixed]=before[fixed];_,oldArea=geom_normals(before,tt);oldLen=np.linalg.norm(oldArea,axis=1);rollback=set()
 for cycle in range(8):
  _,area=geom_normals(after,tt);flips=np.where((oldLen>1e-7)&(np.sum(oldArea*area,axis=1)<0))[0]
  if not len(flips):break
  seed=set(parent[tt[flips]].ravel());fade={i:0. for i in seed};ring=seed
  for fraction in (.35,.70):
   ring=set().union(*(adj[i] for i in ring))-set(fade)
   for i in ring:fade[i]=fraction
  for i,fraction in fade.items():change[i]*=fraction;rollback.add(i)
  after=before+change[parent];after[fixed]=before[fixed]
 # A positive source clearance must never become an intersection.
 clamp=0
 for i in np.where(support>.0001)[0]:
  if signed[i]<=0:continue
  gap=hit(gBefore[i]+change[i])[2]
  if gap<=0:
   original=change[i].copy()
   for attempt in range(24):
    factor=.5**(attempt+1)
    if hit(gBefore[i]+original*factor)[2]>0:change[i]=original*factor;break
   else:change[i]=0
   clamp+=1
 after=before+change[parent];after[fixed]=before[fixed];newSigned=np.array([hit(p)[2] for p in gBefore+change]);_,newArea=geom_normals(after,tt);flips=np.where((oldLen>1e-7)&(np.sum(oldArea*newArea,axis=1)<0))[0];newIntersections=int(((signed>0)&(newSigned<=0)&(support>.0001)).sum());remaining=int((seeds&(newSigned<.001)).sum())
 local=xf(np.linalg.inv(tm),after);bindTarget=np.einsum('nij,nj->ni',np.linalg.inv(mix),np.column_stack([local,np.ones(len(local))]))[:,:3];newDelta=bindTarget-base;newDelta[fixed]=oldDelta[fixed]
 normals,_=geom_normals(after,tt);nl=normals@tm[:3,:3];bindNormals=np.einsum('nij,nj->ni',np.linalg.inv(mix[:,:3,:3]),nl);bindNormals/=np.maximum(np.linalg.norm(bindNormals,axis=1)[:,None],1e-12);nd=bindNormals-np.array(profile['normals']).reshape(-1,3);nd[fixed]=oldDn[fixed]
 anchor={'shape':label,'feature':f.tolist(),'deltas':newDelta.ravel().tolist(),'normalDeltas':nd.ravel().tolist()};metrics={'sex':sex,'label':label,'seedPhysicalVertices':int(seeds.sum()),'movedVertices':int((np.linalg.norm(after-before,axis=1)>.000001).sum()),'maximumPoseDisplacementMm':float(np.linalg.norm(after-before,axis=1).max()*1000),'initialSeedMinClearanceMm':float(signed[seeds].min()*1000) if seeds.any() else 0,'finalSeedMinClearanceMm':float(newSigned[seeds].min()*1000) if seeds.any() else 0,'remainingSeedVerticesBelow1mmClearance':remaining,'triangleReversals':int(len(flips)),'newBodyIntersections':newIntersections,'rollbackPhysicalVertices':len(rollback),'clearanceClamps':clamp,'protectedPositionError':float(np.linalg.norm(after[fixed]-before[fixed],axis=1).max()),'protectedNormalDeltaError':float(np.max(np.abs(nd[fixed]-oldDn[fixed]))),'status':'WORK-ONLY candidate; root review and actual intervening-frame coverage pending'}
 (W/(label+'-anchor.json')).write_text(json.dumps(anchor,separators=(',',':')));REPORT[label]=metrics;print('STROKE_SOURCE',metrics,flush=True)
 return bp,bt,before,after,tt

def material(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.76;n.inputs['Specular IOR Level'].default_value=.15;return m

def mesh(name,p,t,m,offset):
 q=np.column_stack([p[:,0]+offset[0],-p[:,2],p[:,1]+offset[1]]);me=bpy.data.meshes.new(name);me.from_pydata(q.tolist(),[],t.tolist());me.update();me.materials.append(m);ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
 for f in me.polygons:f.use_smooth=True
 return ob

for sex in ('Male','Female'):
 profile=json.loads((R/f'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_{sex}.json').read_text());staged=json.loads(json.dumps(profile))
 for action in ('Serve','Forehand'):
  rows=[]
  for time in range(3):
   label=f'{sex.lower()}_{action}_{time}';rows.append(author(sex,label,profile))
   # Keep all accepted anchors byte-identical in content. No hierarchy/source
   # changes; appended controls use the same invariant direction features.
   anchor=json.loads((W/(label+'-anchor.json')).read_text())
   if REPORT[label]['movedVertices']>0:staged['anchors'].append(anchor)
  bpy.ops.wm.read_factory_settings(use_empty=True);skin=material('Unchanged actual Body',(.57,.29,.17));cloth=material('Same plain shirt',(.70,.105,.060) if sex=='Male' else (.35,.53,.05))
  for row,(bp,bt,before,after,tt) in enumerate(rows):
   for col,(p,n) in enumerate(((before,'BEFORE'),(after,'AFTER'))):mesh(f'{row}_{n}_Body',bp,bt,skin,(col*.85,-row*.72));mesh(f'{row}_{n}_Top',p,tt,cloth,(col*.85,-row*.72))
  sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=1500;sc.render.resolution_y=1700;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('Same studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.4,.43,.47,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.3;sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';target=Vector((.425,0,.82))
  for pos,power,size in [((-.7,-2,3),420,3),((2,-1,1.7),160,3)]:
   bpy.ops.object.light_add(type='AREA',location=pos);ob=bpy.context.object;ob.data.energy=power;ob.data.size=size;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
  bpy.ops.object.camera_add(location=(.425,-4.5,.95));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=2.05;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;sc.render.filepath=str(W/f'{sex.lower()}_{action}_source-before-after.png');bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{sex}_{action}_LocalizedCoverage.blend'))
 (W/f'SleeveFit_{sex}.json').write_text(json.dumps(staged,separators=(',',':')))
(W/'stroke-source-report.json').write_text(json.dumps(REPORT,indent=2)+'\n')
