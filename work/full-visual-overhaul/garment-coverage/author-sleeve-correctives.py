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
target=Tp.copy();clearance=[];selected=np.where(mask>.0001)[0]
for i in selected:
 a=rest.find_nearest(Vector(Tr[i]));b=posed.find_nearest(Vector(Tp[i]))
 if not a[0] or not b[0]:continue
 gap=np.clip(a[3],.014,.032)
 # Preserve volume against the live rounded skin reference. The source mesh
 # still carries its same turned-edge thickness and actual surface topology.
 desired=np.array(b[0])+np.array(b[1])*gap
 delta=(desired-Tp[i])*mask[i];length=np.linalg.norm(delta)
 if length>.055:delta*=.055/length
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
deltaRoot=target-Tp;length=np.linalg.norm(deltaRoot,axis=1);limit=length>.065;deltaRoot[limit]*=(.065/length[limit])[:,None];target=Tp+deltaRoot
skin=np.array(top['skinMatrices']).reshape(-1,4,4);mix=np.sum(skin[TI]*TW[:,:,None,None],axis=1)
meshTarget=transform(np.linalg.inv(Tm),target);hom=np.column_stack([meshTarget,np.ones(len(meshTarget))]);bindTarget=np.einsum('nij,nj->ni',np.linalg.inv(mix),hom)[:,:3]
P=array(top,'vertices',3);delta=bindTarget-P;delta[outside]=0
predicted=np.einsum('nij,nj->ni',mix,np.column_stack([P+delta,np.ones(len(P))]))[:,:3];oracle=np.linalg.norm(predicted-meshTarget,axis=1)
assert oracle[~outside].max()<.000002
# Pose normals derive from the final sculpt, then invert the exact weighted
# matrix. This avoids retaining the folded sleeve's old lighting field.
normal=np.zeros_like(meshTarget);cross=np.cross(meshTarget[TT[:,1]]-meshTarget[TT[:,0]],meshTarget[TT[:,2]]-meshTarget[TT[:,0]])
for j in range(3):np.add.at(normal,TT[:,j],cross)
normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-10)
bindNormal=np.einsum('nij,nj->ni',np.linalg.inv(mix[:,:3,:3]),normal);bindNormal/=np.maximum(np.linalg.norm(bindNormal,axis=1)[:,None],1e-10)
dn=bindNormal-array(top,'normals',3);dn[outside]=0
segments=[('Spine','Chest'),('Chest','Neck'),('LeftShoulder','LeftUpperArm'),('LeftUpperArm','LeftLowerArm'),('LeftLowerArm','LeftHand'),('RightShoulder','RightUpperArm'),('RightUpperArm','RightLowerArm'),('RightLowerArm','RightHand')]
bind=np.array(body['bindposes']).reshape(-1,4,4);sm=np.array(body['skinMatrices']).reshape(-1,4,4);joint=sm@np.linalg.inv(bind)
dirs=[]
for a,b in segments:
 v=joint[body['bones'].index(b),:3,3]-joint[body['bones'].index(a),:3,3];dirs.append(v/np.linalg.norm(v))
features=[float(dirs[i]@dirs[j]) for i in range(8) for j in range(i+1,8)]
out=W/'sleeve-correctives';out.mkdir(exist_ok=True)
report={'sex':sex,'name':label,'vertexCount':len(P),'feature':features,'deltas':delta.ravel().tolist(),'normalDeltas':dn.ravel().tolist(),'maxPoseDeltaMetres':float(np.linalg.norm(deltaRoot,axis=1).max()),'changedVertices':int((np.linalg.norm(delta,axis=1)>1e-6).sum()),'inverseOracleMaxMetres':float(oracle[~outside].max()),'gate':'SOURCE CANDIDATE; runtime visual review required'}
(out/(label+'.json')).write_text(json.dumps(report,separators=(',',':')))
# Editable evaluated comparison in a common source coordinate system.
bpy.ops.wm.read_factory_settings(use_empty=True);conv=lambda p:np.column_stack([p[:,0],-p[:,2],p[:,1]])
def material(name,col):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*col,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.72;return m
skinmat=material('Read-only live body reference',(.62,.31,.15));cloth=material('Current fitted polo',(.78,.33,.27) if sex=='Female' else (.06,.48,.51))
for side,topPos in [(0,Tp),(1,target)]:
 for name,pts,tris,mat in [('Body',Bp,BT,skinmat),('Top',topPos,TT,cloth)]:
  verts=conv(pts);verts[:,0]+=side*.85;mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts.tolist(),[],tris.tolist());mesh.materials.append(mat);mesh.update();ob=bpy.data.objects.new(('BEFORE_' if side==0 else 'AFTER_')+name,mesh);bpy.context.collection.objects.link(ob)
  for f in mesh.polygons:f.use_smooth=True
sc=bpy.context.scene;sc.world=bpy.data.worlds.new('Source review world');sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=20;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=1600;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.world.color=(.55,.60,.61);sc.view_settings.view_transform='AgX'
for pos,power,size in [((-.9,-3,4),650,4),((2,-1,2),260,3)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((.45,0,1.25))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.48,-3.6,1.43));cam=bpy.context.object;cam.rotation_euler=(Vector((.43,0,1.24))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.7;sc.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=str(out/(label+'.blend')));sc.render.filepath=str(out/(label+'-comparison.png'));bpy.ops.render.render(write_still=True)
print(json.dumps({k:v for k,v in report.items() if k not in ['deltas','normalDeltas','feature']}),flush=True)
