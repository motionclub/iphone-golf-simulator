"""Garment-only inverse-LBS sleeve sculpt from independently sampled live poses.
Body geometry is read-only reference. No culling, skeleton, skin or UV changes.
"""
import bpy,sys,pathlib,json,numpy as np,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path(__file__).resolve().parents[3];W=R/'work/full-visual-overhaul/garment-coverage';D=R/'proof/full-visual-overhaul/character-pose-data-1/poses'
label=sys.argv[-1];data=json.loads((D/(label+'.json')).read_text());body,top=data['parts'];sex=data['sex']
assert max(p['bakeOracleMaxMetres'] for p in [body,top])<.00002
def array(part,key,n):return np.array(part[key],float).reshape(-1,n)
def transform(matrix,p):return p@matrix[:3,:3].T+matrix[:3,3]
def rows(part):
 m=np.array(part['rendererToRoot']).reshape(4,4)
 return m,transform(m,array(part,'vertices',3)),transform(m,array(part,'posedVertices',3))
Bm,Br,Bp=rows(body);Tm,Tr,Tp=rows(top);BT=np.array(body['triangles']).reshape(-1,3);TT=np.array(top['triangles']).reshape(-1,3)
BI=np.array(body['indices']).reshape(-1,4);BW=array(body,'weights',4);TI=np.array(top['indices']).reshape(-1,4);TW=array(top,'weights',4)
def mass(part,indices,weights,names):
 ids=np.array([part['bones'].index(n) for n in names if n in part['bones']]);return np.sum(weights*np.isin(indices,ids),axis=1)
def smooth(a,b,x):t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def repair(part,base,posed):
 ids=np.array(part['indices']).reshape(-1,4);old=array(part,'weights',4);new=old.copy();names=part['bones']
 armIDs=[names.index(n) for n in ['LeftUpperArm','RightUpperArm','LeftShoulder','RightShoulder'] if n in names]
 torsoIDs=[names.index(n) for n in ['Spine','Chest','UpperChest'] if n in names]
 torso=(old*np.isin(ids,torsoIDs)).sum(1)
 x=np.abs(base[:,0]);y=base[:,1];shoulder=1.28 if sex=='Female' else 1.33
 low=1.05 if sex=='Female' else 1.08;high=1.16 if sex=='Female' else 1.21
 field=smooth(.065,.105,x)*(1-smooth(.140,.190,x))*(1-smooth(high,shoulder,y))*smooth(low,low+.03,y)*smooth(.07,.28,torso)*.90
 removed=np.zeros(len(base))
 for j in range(4):
  take=old[:,j]*np.isin(ids[:,j],armIDs)*field
  new[:,j]-=take;removed+=take
 for j in range(4):new[:,j]+=removed*(old[:,j]*np.isin(ids[:,j],torsoIDs))/np.maximum(torso,1e-12)
 assert np.max(np.abs(new.sum(1)-old.sum(1)))<1e-8
 outside=field<1e-12;assert np.array_equal(new[outside],old[outside])
 skin=np.array(part['skinMatrices']).reshape(-1,4,4);oldMix=np.sum(skin[ids]*old[:,:,None,None],axis=1);newMix=np.sum(skin[ids]*new[:,:,None,None],axis=1)
 p=array(part,'vertices',3);hom=np.column_stack([p,np.ones(len(p))]);oldPos=np.einsum('nij,nj->ni',oldMix,hom)[:,:3];newPos=np.einsum('nij,nj->ni',newMix,hom)[:,:3]
 m=np.array(part['rendererToRoot']).reshape(4,4);delta=(newPos-oldPos)@m[:3,:3].T;result=posed+delta
 changed=(np.abs(new-old).max(1)>1e-7)
 return result,new,{'name':part['name'],'vertexCount':len(p),'changedWeightsVertices':int(changed.sum()),'maxPoseDeltaMetres':float(np.linalg.norm(delta,axis=1).max()),'outsideWeightsExact':bool(np.array_equal(new[outside],old[outside])),'indicesExact':True,'restPositionsExact':True,'weights':new.ravel().tolist()}
bodyTarget,bodyWeights,bodyReport=repair(body,Br,Bp);weightedTop,topWeights,topReport=repair(top,Tr,Tp)
originalTp=Tp.copy();originalBp=Bp.copy();Tp=weightedTop;Bp=bodyTarget
bodyMass=mass(body,BI,BW,['Hips','Spine','Chest','UpperChest','LeftShoulder','RightShoulder','LeftUpperArm','RightUpperArm'])
valid=(Br[:,1]>.98)&(Br[:,1]<1.425)&(bodyMass>.70);faces=[tuple(f) for f in BT if valid[f].all()]
rest=BVHTree.FromPolygons([Vector(v) for v in Br],faces,all_triangles=True);posed=BVHTree.FromPolygons([Vector(v) for v in Bp],faces,all_triangles=True)
arm=mass(top,TI,TW,['LeftShoulder','RightShoulder','LeftUpperArm','RightUpperArm','LeftLowerArm','RightLowerArm'])
def smooth(a,b,x):t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
mask=smooth(.035,.30,arm)*(Tr[:,1]>1.055)
# Include the armpit gusset's torso-owned vertices so the junction is rounded
# continuously rather than leaving a stationary chest-to-sleeve triangle.
underarm=(np.abs(Tr[:,0])>(.15 if sex=='Male' else .105))&(Tr[:,1]>1.12)&(Tr[:,1]<(1.30 if sex=='Male' else 1.24))
mask=np.maximum(mask,underarm.astype(float)*.80)
# Include every side-panel vertex, including the torso-owned bottom of the
# gusset. Leaving these pinned preserved the original triangular sail.
sidePanel=(np.abs(Tr[:,0])>.055)&(Tr[:,1]>1.045)&(Tr[:,1]<1.345)
mask=np.maximum(mask,sidePanel.astype(float)*.98)
# Preserve detached sewn collar and placket pieces. Their imported limb
# influence does not make them sleeve cloth.
parent=list(range(len(Tr)))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
def join(a,b):
 a=find(a);b=find(b)
 if a!=b:parent[b]=a
weld={}
for i,p in enumerate(array(top,'vertices',3)):
 key=tuple(np.round(p*100000).astype(int))
 if key in weld:join(i,weld[key])
 else:weld[key]=i
for a,b,c in TT:join(int(a),int(b));join(int(a),int(c))
components={}
for i in range(len(Tr)):components.setdefault(find(i),[]).append(i)
for ids in components.values():
 q=Tr[ids];mi=q.min(0);ma=q.max(0);size=ma-mi
 if mi[1]>(1.20 if sex=='Female' else 1.26) and ma[1]>(1.38 if sex=='Female' else 1.43) and .12<size[0]<.34:mask[ids]=0
 # Buttons and front placket retain their exact attachment geometry.
 if size[0]<.055 and np.max(np.abs(q[:,0]))<.05:mask[ids]=0
target=Tp.copy();clearance=[];selected=np.where(mask>.0001)[0]
bodyNormals=np.zeros_like(Bp)
cross=np.cross(Bp[BT[:,1]]-Bp[BT[:,0]],Bp[BT[:,2]]-Bp[BT[:,0]])
for j in range(3):np.add.at(bodyNormals,BT[:,j],cross)
bodyNormals/=np.maximum(np.linalg.norm(bodyNormals,axis=1)[:,None],1e-10)
def barycentric(p,tri):
 a,b,c=tri;v0=b-a;v1=c-a;v2=p-a
 d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1
 denom=d00*d11-d01*d01
 if abs(denom)<1e-14:return np.array([1.,0.,0.])
 v=(d11*d20-d01*d21)/denom;w=(d00*d21-d01*d20)/denom
 return np.array([1-v-w,v,w])
for i in selected:
 a=rest.find_nearest(Vector(Tr[i]));b=posed.find_nearest(Vector(Tp[i]))
 if a[0] is None or b[0] is None:continue
 gap=np.clip(a[3],.004,.030)
 tri=np.array(faces[b[2]]);bary=barycentric(np.array(b[0]),Bp[tri])
 normal=(bodyNormals[tri]*bary[:,None]).sum(0);normal/=max(np.linalg.norm(normal),1e-10)
 desired=np.array(b[0])+normal*gap
 delta=(desired-Tp[i])*mask[i];length=np.linalg.norm(delta)
 if length>.140:delta*=.140/length
 target[i]+=delta;clearance.append(gap)
# Smooth the sculpt along the existing garment topology. Original UV splits
# are welded only for the field; all source indices and UV seams stay intact.
groups={};parents=[]
for p in array(top,'vertices',3):
 key=tuple(np.round(p*100000).astype(int));parents.append(groups.setdefault(key,len(groups)))
parents=np.array(parents);count=len(groups);adj=[set() for _ in range(count)]
for tri in TT:
 ids=parents[tri]
 for i in ids:adj[i].update(int(j) for j in ids if i!=j)
base=np.zeros((count,3));sculpt=np.zeros_like(base);weights=np.zeros(count);sizes=np.bincount(parents)
np.add.at(base,parents,Tp);np.add.at(sculpt,parents,target);np.maximum.at(weights,parents,mask);base/=sizes[:,None];sculpt/=sizes[:,None]
for _ in range(8):
 new=sculpt.copy()
 for i in np.where(weights>.001)[0]:
  if adj[i]:new[i]+=(sculpt[list(adj[i])].mean(0)-sculpt[i])*.13*weights[i]
 sculpt=new
target=sculpt[parents];outside=mask<.0001;target[outside]=Tp[outside]
deltaRoot=target-Tp;length=np.linalg.norm(deltaRoot,axis=1);limit=length>.150;deltaRoot[limit]*=(.150/length[limit])[:,None];target=Tp+deltaRoot

skin=np.array(top['skinMatrices']).reshape(-1,4,4);mix=np.sum(skin[TI]*topWeights[:,:,None,None],axis=1)
meshTarget=transform(np.linalg.inv(Tm),target);hom=np.column_stack([meshTarget,np.ones(len(meshTarget))]);bindTarget=np.einsum('nij,nj->ni',np.linalg.inv(mix),hom)[:,:3]
P=array(top,'vertices',3);delta=bindTarget-P;delta[outside]=0
predicted=np.einsum('nij,nj->ni',mix,np.column_stack([P+delta,np.ones(len(P))]))[:,:3];oracle=np.linalg.norm(predicted-meshTarget,axis=1)
assert oracle[~outside].max()<.000002
normal=np.zeros_like(meshTarget);cross=np.cross(meshTarget[TT[:,1]]-meshTarget[TT[:,0]],meshTarget[TT[:,2]]-meshTarget[TT[:,0]])
for j in range(3):np.add.at(normal,TT[:,j],cross)
normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-10)
bindNormal=np.einsum('nij,nj->ni',np.linalg.inv(mix[:,:3,:3]),normal);bindNormal/=np.maximum(np.linalg.norm(bindNormal,axis=1)[:,None],1e-10)
dn=bindNormal-array(top,'normals',3);dn[outside]=0
out=W/'axilla-field-3';out.mkdir(exist_ok=True)
report={'sex':sex,'name':label,'parts':[bodyReport,topReport],'deltas':delta.ravel().tolist(),'normalDeltas':dn.ravel().tolist(),'vertexCount':len(P),'maxSculptDeltaMetres':float(np.linalg.norm(deltaRoot,axis=1).max()),'inverseOracleMaxMetres':float(oracle[~outside].max()),'gate':'SOURCE CANDIDATE; actual dynamic review required'}
(out/(label+'.json')).write_text(json.dumps(report,separators=(',',':')))
segments=[('Spine','Chest'),('Chest','Neck'),('LeftShoulder','LeftUpperArm'),('LeftUpperArm','LeftLowerArm'),('LeftLowerArm','LeftHand'),('RightShoulder','RightUpperArm'),('RightUpperArm','RightLowerArm'),('RightLowerArm','RightHand')]
bind=np.array(body['bindposes']).reshape(-1,4,4);sm=np.array(body['skinMatrices']).reshape(-1,4,4);joint=sm@np.linalg.inv(bind)
dirs=[]
for a,b in segments:
 v=joint[body['bones'].index(b),:3,3]-joint[body['bones'].index(a),:3,3];dirs.append(v/np.linalg.norm(v))
features=[float(dirs[i]@dirs[j]) for i in range(8) for j in range(i+1,8)]
report['feature']=features
(out/(label+'.json')).write_text(json.dumps(report,separators=(',',':')))
# Editable evaluated comparison in a common source coordinate system.
bpy.ops.wm.read_factory_settings(use_empty=True);conv=lambda p:np.column_stack([p[:,0],-p[:,2],p[:,1]])
def material(name,col):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*col,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.72;return m
skinmat=material('Read-only live body reference',(.62,.31,.15));cloth=material('Current fitted polo',(.78,.33,.27) if sex=='Female' else (.06,.48,.51))
for side,topPos in [(0,originalTp),(1,target)]:
 for name,pts,tris,mat in [('Body',originalBp if side==0 else bodyTarget,BT,skinmat),('Top',topPos,TT,cloth)]:
  verts=conv(pts);verts[:,0]+=side*.85;mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts.tolist(),[],tris.tolist());mesh.materials.append(mat);mesh.update();ob=bpy.data.objects.new(('BEFORE_' if side==0 else 'AFTER_')+name,mesh);bpy.context.collection.objects.link(ob)
  for f in mesh.polygons:f.use_smooth=True
sc=bpy.context.scene;sc.world=bpy.data.worlds.new('Source review world');sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=20;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=1600;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.world.color=(.55,.60,.61);sc.view_settings.view_transform='AgX'
for pos,power,size in [((-.9,-3,4),650,4),((2,-1,2),260,3)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((.45,0,1.25))-o.location).to_track_quat('-Z','Y').to_euler()
focus=np.median(conv(originalTp),axis=0);focus[0]=.43
bpy.ops.object.camera_add(location=(focus[0]+.05,focus[1]-3.6,focus[2]+.19));cam=bpy.context.object;cam.rotation_euler=(Vector(focus.tolist())-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.7;sc.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=str(out/(label+'.blend')));sc.render.filepath=str(out/(label+'-comparison.png'));bpy.ops.render.render(write_still=True)
print(json.dumps({'sex':sex,'name':label,'parts':[{k:v for k,v in p.items() if k!='weights'} for p in report['parts']]}),flush=True)
