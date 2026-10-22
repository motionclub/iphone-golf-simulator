import bpy,bmesh,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
w=Path('work/character-finish32');data=json.loads((w/'refined/poses/male_intro.json').read_text());body=data['parts'][0];top=next(p for p in data['parts'] if p['name']=='Kit_Top')
P=np.array(top['vertices']).reshape(-1,3);N=np.array(top['normals']).reshape(-1,3);T=np.array(top['triangles']).reshape(-1,3);WI=np.array(top['indices']).reshape(-1,4);W=np.array(top['weights']).reshape(-1,4)
BP=np.array(body['vertices']).reshape(-1,3);BN=np.array(body['normals']).reshape(-1,3);BT=np.array(body['triangles']).reshape(-1,3);BWI=np.array(body['indices']).reshape(-1,4);BW=np.array(body['weights']).reshape(-1,4)
restTree=BVHTree.FromPolygons([Vector(p) for p in BP],BT.tolist(),all_triangles=True)
clearance=np.zeros(len(P))
for i,p in enumerate(P):
 hit,n,fi,dist=restTree.find_nearest(Vector(p));normal=BN[BT[fi]].mean(0);normal/=max(1e-10,np.linalg.norm(normal));side=np.dot(N[i],normal);clearance[i]=.002+.004*min(1,max(0,(side+.2)/.4))
region=(BP[:,2]>.92)&(BP[:,2]<1.43)&(abs(BP[:,0])<.37);ST=BT[np.all(region[BT],axis=1)]
active=(P[:,2]>1.06)&(P[:,2]<1.413)&(abs(P[:,0])>.06);ids=np.flatnonzero(active);F=T[np.all(active[T],axis=1)]
_,alias=np.unique(np.round(P,6),axis=0,return_inverse=True);an=alias.max()+1;ac=np.bincount(alias);E=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]);E=np.concatenate([E,E[:,::-1]]);ea,eb=E.T;ec=np.bincount(ea,minlength=len(P))
segments=[('Spine','Chest'),('Chest','Neck'),('LeftShoulder','LeftUpperArm'),('LeftUpperArm','LeftLowerArm'),('LeftLowerArm','LeftHand'),('RightShoulder','RightUpperArm'),('RightUpperArm','RightLowerArm'),('RightLowerArm','RightHand')]
binds=np.array(body['bindposes']).reshape(-1,4,4);restjoints=np.linalg.inv(binds)[:,:3,3];anchors=[];reports=[]
for file in sorted((w/'collision-poses/matrices').glob('*.json')):
 if file.stem!='male_SliceApproach_3':continue
 d=json.loads(file.read_text());parts={p['name']:p for p in d['parts']};bm=np.array(parts[body['name']]['skinMatrices']).reshape(-1,4,4);mp={n:bm[j] for j,n in enumerate(body['bones'])};tm=np.array([mp[n] for n in top['bones']]);M=(tm[WI]*W[:,:,None,None]).sum(1);BM=(bm[BWI]*BW[:,:,None,None]).sum(1);q0=np.einsum('nij,nj->ni',M[:,:3,:3],P)+M[:,:3,3];q=q0.copy();bq=np.einsum('nij,nj->ni',BM[:,:3,:3],BP)+BM[:,:3,3];bn=np.einsum('nij,nj->ni',BM[:,:3,:3],BN);bn/=np.maximum(1e-10,np.linalg.norm(bn,axis=1))[:,None];
 mesh=bpy.data.meshes.new('FittingProxy');mesh.from_pydata(bq.tolist(),[],ST.tolist());mesh.update();ob=bpy.data.objects.new('FittingProxy',mesh);bpy.context.collection.objects.link(ob);bmsh=bmesh.new();bmsh.from_mesh(mesh);bmesh.ops.delete(bmsh,geom=[v for v in bmsh.verts if not v.link_faces],context='VERTS');bmesh.ops.holes_fill(bmsh,edges=[e for e in bmsh.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bmsh,faces=list(bmsh.faces));bmsh.to_mesh(mesh);bmsh.free();bpy.context.view_layer.objects.active=ob;ob.select_set(True);mesh.remesh_voxel_size=.003;bpy.ops.object.voxel_remesh();mesh=ob.data;bmsh=bmesh.new();bmsh.from_mesh(mesh)
 for step in range(3):bmesh.ops.smooth_vert(bmsh,verts=list(bmsh.verts),factor=.5,use_axis_x=True,use_axis_y=True,use_axis_z=True)
 bmesh.ops.recalc_face_normals(bmsh,faces=list(bmsh.faces));bmsh.to_mesh(mesh);bmsh.free();mesh.update();tree=BVHTree.FromPolygons([v.co for v in mesh.vertices],[list(f.vertices) for f in mesh.polygons]);print('PROXY',len(mesh.vertices),len(mesh.polygons),flush=True)

 history=[]
 relax=np.clip((np.abs(P[:,0])-.13)/.035,0,1)*np.clip((.36-np.abs(P[:,0]))/.03,0,1)*np.clip((P[:,2]-1.10)/.055,0,1)*np.clip((1.42-P[:,2])/.05,0,1)
 for iteration in range(50):
  mean=np.zeros_like(q);np.add.at(mean,ea,q[eb]);mean/=np.maximum(ec[:,None],1);q+=.35*(mean-q)*relax[:,None];merged=np.zeros((an,3));np.add.at(merged,alias,q-q0);q=q0+(merged/ac[:,None])[alias]
  corr=np.zeros_like(P);count=np.zeros(len(P));negative=0;worst=0
  for j,s in enumerate(np.concatenate([q[ids],q[F].mean(1)])):
   hit,n,fi,dist=tree.find_nearest(Vector(s))
   if dist>.06:continue
   normal=np.array(n);signed=np.dot(s-hit,normal);wanted=clearance[ids[j]] if j<len(ids) else clearance[F[j-len(ids)]].mean();need=wanted+.002-signed
   if need<=0:continue
   if signed<0:negative+=1;worst=max(worst,-signed)
   vs=[ids[j]] if j<len(ids) else F[j-len(ids)];move=normal*min(need,.008)
   for v in vs:corr[v]+=move;count[v]+=1
  corr/=np.maximum(count[:,None],1)
  for _ in range(3):
   acc=np.zeros_like(P);np.add.at(acc,ea,corr[eb]);corr=.6*corr+.4*acc/np.maximum(ec[:,None],1)
  synced=np.zeros((an,3));np.add.at(synced,alias,corr);corr=(synced/ac[:,None])[alias];q+=corr*active[:,None]
  history.append([negative,worst*1000])
 restDelta=np.einsum('nij,nj->ni',np.linalg.inv(M[:,:3,:3]),q-q0);joints=np.einsum('nij,nj->ni',bm[:,:3,:3],restjoints)+bm[:,:3,3];jm=dict(zip(body['bones'],joints));dirs=np.array([jm[z]-jm[a] for a,z in segments]);dirs/=np.linalg.norm(dirs,axis=1)[:,None];feature=[float(np.dot(dirs[a],dirs[z])) for a in range(8) for z in range(a+1,8)]
 # Compute garment normal deltas from the actual corrected bind-space shape.
 pp=q;cross=np.cross(pp[T[:,1]]-pp[T[:,0]],pp[T[:,2]]-pp[T[:,0]]);baseCross=np.cross(q0[T[:,1]]-q0[T[:,0]],q0[T[:,2]]-q0[T[:,0]]);nn=np.zeros_like(N);nb=np.zeros_like(N)
 for s in range(3):np.add.at(nn,T[:,s],cross);np.add.at(nb,T[:,s],baseCross)
 sharedN=np.zeros((an,3));sharedB=np.zeros((an,3));np.add.at(sharedN,alias,nn);np.add.at(sharedB,alias,nb);nn=sharedN[alias];nb=sharedB[alias];nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-10);nb/=np.maximum(np.linalg.norm(nb,axis=1)[:,None],1e-10);posedNormal=np.einsum('nij,nj->ni',M[:,:3,:3],N);posedNormal/=np.maximum(np.linalg.norm(posedNormal,axis=1)[:,None],1e-10);targetNormal=posedNormal+nn-nb;targetNormal/=np.maximum(np.linalg.norm(targetNormal,axis=1)[:,None],1e-10);restNormal=np.einsum('nij,nj->ni',np.linalg.inv(M[:,:3,:3]),targetNormal);restNormal/=np.maximum(np.linalg.norm(restNormal,axis=1)[:,None],1e-10);nd=restNormal-N
 anchors.append({'shape':file.stem,'feature':feature,'deltas':restDelta.ravel().tolist(),'normalDeltas':nd.ravel().tolist()});row={'pose':file.stem,'history':history,'maxDeltaMm':float(np.linalg.norm(restDelta,axis=1).max()*1000)};reports.append(row);print(row,flush=True)
profile={'vertexCount':len(P),'vertices':P.ravel().tolist(),'normals':N.ravel().tolist(),'anchors':anchors};(w/'tailored-fit-union.json').write_text(json.dumps(profile,separators=(',',':')));(w/'tailored-fit-union-report.json').write_text(json.dumps(reports,indent=2))
