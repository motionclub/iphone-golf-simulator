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
 return result,{'name':part['name'],'vertexCount':len(p),'changedWeightsVertices':int(changed.sum()),'maxPoseDeltaMetres':float(np.linalg.norm(delta,axis=1).max()),'outsideWeightsExact':bool(np.array_equal(new[~changed],old[~changed])),'indicesExact':True,'restPositionsExact':True,'weights':new.ravel().tolist()}
bodyTarget,bodyReport=repair(body,Br,Bp);target,topReport=repair(top,Tr,Tp)
out=W/'axilla-field-1';out.mkdir(exist_ok=True)
report={'sex':sex,'name':label,'parts':[bodyReport,topReport],'gate':'SOURCE CANDIDATE; actual dynamic review required'}
(out/(label+'.json')).write_text(json.dumps(report,separators=(',',':')))
segments=[('Spine','Chest'),('Chest','Neck'),('LeftShoulder','LeftUpperArm'),('LeftUpperArm','LeftLowerArm'),('LeftLowerArm','LeftHand'),('RightShoulder','RightUpperArm'),('RightUpperArm','RightLowerArm'),('RightLowerArm','RightHand')]
bind=np.array(body['bindposes']).reshape(-1,4,4);sm=np.array(body['skinMatrices']).reshape(-1,4,4);joint=sm@np.linalg.inv(bind)
dirs=[]
for a,b in segments:
 v=joint[body['bones'].index(b),:3,3]-joint[body['bones'].index(a),:3,3];dirs.append(v/np.linalg.norm(v))
features=[float(dirs[i]@dirs[j]) for i in range(8) for j in range(i+1,8)]
# Editable evaluated comparison in a common source coordinate system.
bpy.ops.wm.read_factory_settings(use_empty=True);conv=lambda p:np.column_stack([p[:,0],-p[:,2],p[:,1]])
def material(name,col):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*col,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.72;return m
skinmat=material('Read-only live body reference',(.62,.31,.15));cloth=material('Current fitted polo',(.78,.33,.27) if sex=='Female' else (.06,.48,.51))
for side,topPos in [(0,Tp),(1,target)]:
 for name,pts,tris,mat in [('Body',Bp if side==0 else bodyTarget,BT,skinmat),('Top',topPos,TT,cloth)]:
  verts=conv(pts);verts[:,0]+=side*.85;mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts.tolist(),[],tris.tolist());mesh.materials.append(mat);mesh.update();ob=bpy.data.objects.new(('BEFORE_' if side==0 else 'AFTER_')+name,mesh);bpy.context.collection.objects.link(ob)
  for f in mesh.polygons:f.use_smooth=True
sc=bpy.context.scene;sc.world=bpy.data.worlds.new('Source review world');sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=20;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=1600;sc.render.resolution_y=1100;sc.render.resolution_percentage=100;sc.world.color=(.55,.60,.61);sc.view_settings.view_transform='AgX'
for pos,power,size in [((-.9,-3,4),650,4),((2,-1,2),260,3)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((.45,0,1.25))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.48,-3.6,1.43));cam=bpy.context.object;cam.rotation_euler=(Vector((.43,0,1.24))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.7;sc.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=str(out/(label+'.blend')));sc.render.filepath=str(out/(label+'-comparison.png'));bpy.ops.render.render(write_still=True)
print(json.dumps({'sex':sex,'name':label,'parts':[{k:v for k,v in p.items() if k!='weights'} for p in report['parts']]}),flush=True)
