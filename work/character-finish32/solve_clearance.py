import bpy,json,math,time
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32';d=w/'collision-poses';data=json.loads((d/'poses/male_intro.json').read_text());body=data['parts'][0];top=next(p for p in data['parts'] if p['name']=='Kit_Top')
P=np.array(top['vertices']).reshape(-1,3);original=P.copy();T=np.array(top['triangles']).reshape(-1,3);BI=np.array(top['indices']).reshape(-1,4);BW=np.array(top['weights']).reshape(-1,4)
BP=np.array(body['vertices']).reshape(-1,3);BT=np.array(body['triangles']).reshape(-1,3);BN=np.array(body['normals']).reshape(-1,3);BBI=np.array(body['indices']).reshape(-1,4);BBW=np.array(body['weights']).reshape(-1,4)
# Only skin normally covered by the polo; crossed forearms/hands must not balloon the torso.
region=(BP[:,2]>.93)&(BP[:,2]<1.475)&(abs(BP[:,0])<.365);BT=BT[np.all(region[BT],axis=1)]
fn=np.cross(BP[BT[:,1]]-BP[BT[:,0]],BP[BT[:,2]]-BP[BT[:,0]])
if np.median(np.sum(fn*BN[BT].mean(1),axis=1))<0:BT=BT[:,::-1]
active=(abs(P[:,0])>.067)&(P[:,2]>1.055)&(P[:,2]<1.415);ids=np.flatnonzero(active);FT=T[np.all(active[T],axis=1)]
_,alias=np.unique(np.round(P,6),axis=0,return_inverse=True);aliasN=alias.max()+1;aliasCount=np.bincount(alias)
edges=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]);edges=np.concatenate([edges,edges[:,::-1]]);ea,eb=edges.T;ec=np.bincount(ea,minlength=len(P))
poses=[]
for file in sorted((d/'matrices').glob('*.json')):
 report=json.loads(file.read_text());parts={p['name']:p for p in report['parts']};ms=np.array(parts[top['name']]['skinMatrices']).reshape(-1,4,4);bs=np.array(parts[body['name']]['skinMatrices']).reshape(-1,4,4)
 M=np.sum(ms[BI]*BW[:,:,None,None],axis=1);BM=np.sum(bs[BBI]*BBW[:,:,None,None],axis=1);BPos=np.einsum('nij,nj->ni',BM[:,:3,:3],BP)+BM[:,:3,3]
 tree=BVHTree.FromPolygons([Vector(v) for v in BPos],BT.tolist(),all_triangles=True)
 poses.append((file.stem,M,np.linalg.inv(M[:,:3,:3]),tree))
print('POSES',len(poses),'ACTIVE',len(ids),'FACE_SAMPLES',len(FT),flush=True)
rows=[]
for iteration in range(7):
 corrections=np.zeros_like(P);score=np.zeros(len(P));worst=0;bad=0;perpose=[]
 for label,M,inv,tree in poses:
  q=np.einsum('nij,nj->ni',M[:,:3,:3],P)+M[:,:3,3];samples=np.concatenate([q[ids],q[FT].mean(1)]);poseBad=0;poseWorst=0
  for si,sample in enumerate(samples):
   hit,n,_,dist=tree.find_nearest(Vector(sample))
   if dist>.032:continue
   signed=(Vector(sample)-hit).dot(n);need=.004-signed
   if need<=0:continue
   # Keep a bounded source adjustment. This is authored geometry, never a per-frame rewrite.
   need=min(need,.012);move=np.array(n)*need;vIds=[ids[si]] if si<len(ids) else FT[si-len(ids)]
   for vi in vIds:
    delta=inv[vi]@move;size=np.linalg.norm(delta)
    if size>score[vi]:score[vi]=size;corrections[vi]=delta
   poseBad+=1;poseWorst=max(poseWorst,-signed)
  if poseBad:perpose.append({'pose':label,'samples':poseBad,'depthMm':poseWorst*1000})
  bad+=poseBad;worst=max(worst,poseWorst)
 # Synchronize UV aliases and diffuse each contact over its immediate cloth neighbors.
 for _ in range(3):
  acc=np.zeros_like(P);np.add.at(acc,ea,corrections[eb]);corrections=.70*corrections+.30*acc/np.maximum(ec[:,None],1)
 synced=np.zeros((aliasN,3));np.add.at(synced,alias,corrections);corrections=(synced/aliasCount[:,None])[alias]
 corrections*=active[:,None];length=np.linalg.norm(corrections,axis=1);corrections*=np.minimum(1,.004/np.maximum(length,1e-10))[:,None]
 P+=corrections;total=P-original;size=np.linalg.norm(total,axis=1);P=original+total*np.minimum(1,.024/np.maximum(size,1e-10))[:,None]
 row={'iteration':iteration,'samplesInsideClearance':bad,'maxPenetrationMm':worst*1000,'maxSourceChangeMm':float(np.linalg.norm(P-original,axis=1).max()*1000),'worstPoses':sorted(perpose,key=lambda x:-x['depthMm'])[:5]};rows.append(row);print(json.dumps(row),flush=True)
(w/'clearance-report.json').write_text(json.dumps(rows,indent=2));np.savez(w/'clearance-result.npz',original=original,positions=P)
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Sleeve.blend'));o=bpy.data.objects['Kit_Top'];m=o.data;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');kd=KDTree(len(original))
for i,p in enumerate(original):kd.insert(Vector((-p[0],p[1],p[2])),i)
kd.balance()
for v in m.vertices:
 _,i,error=kd.find(v.co)
 if error>3e-6:raise RuntimeError('Source correspondence '+str(error))
 delta=P[i]-original[i];v.co+=Vector((-delta[0],delta[1],delta[2]))
m.update()
if m.has_custom_normals:bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_Clearance.blend'))
bpy.ops.export_scene.fbx(filepath=str(r/'Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
