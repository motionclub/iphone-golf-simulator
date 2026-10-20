import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
w=Path('work/character-finish32');data=json.loads((w/'stable-shell/poses/male_intro.json').read_text());body=data['parts'][0];top=next(p for p in data['parts'] if p['name']=='Kit_Top');old=next(p for p in json.loads((w/'sleeve/poses/male_intro.json').read_text())['parts'] if p['name']=='Kit_Top')
P=np.array(top['vertices']).reshape(-1,3);N=np.array(top['normals']).reshape(-1,3);T=np.array(top['triangles']).reshape(-1,3);WI=np.array(top['indices']).reshape(-1,4);W=np.array(top['weights']).reshape(-1,4);OP=np.array(old['vertices']).reshape(-1,3);OWI=np.array(old['indices']).reshape(-1,4);OW=np.array(old['weights']).reshape(-1,4)
BP=np.array(body['vertices']).reshape(-1,3);BT=np.array(body['triangles']).reshape(-1,3);BWI=np.array(body['indices']).reshape(-1,4);BW=np.array(body['weights']).reshape(-1,4)
k=KDTree(len(OP))
for j,p in enumerate(OP):k.insert(Vector(p),j)
k.balance();oldids=np.array([k.find(Vector(p))[1] for p in P]);active=(P[:,2]>1.09)&(P[:,2]<1.414)&(abs(P[:,0])>.09);ids=np.flatnonzero(active);F=T[np.all(active[T],axis=1)]
_,alias=np.unique(np.round(P,6),axis=0,return_inverse=True);an=alias.max()+1;ac=np.bincount(alias);E=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]);E=np.concatenate([E,E[:,::-1]]);ea,eb=E.T;ec=np.bincount(ea,minlength=len(P));anchors=[]
def sync(delta):
 merged=np.zeros((an,3));np.add.at(merged,alias,delta);return (merged/ac[:,None])[alias]
for sample in [3,4,8]:
 file=w/f'collision-poses/matrices/male_SliceApproach_{sample}.json';d=json.loads(file.read_text());bm=np.array(d['parts'][0]['skinMatrices']).reshape(-1,4,4);mp={n:bm[j] for j,n in enumerate(body['bones'])};tm=np.array([mp[n] for n in top['bones']]);M=(tm[WI]*W[:,:,None,None]).sum(1);OM=(np.array([mp[n] for n in old['bones']])[OWI[oldids]]*OW[oldids,:,None,None]).sum(1);BM=(bm[BWI]*BW[:,:,None,None]).sum(1);q0=np.einsum('nij,nj->ni',M[:,:3,:3],P)+M[:,:3,3];q=np.einsum('nij,nj->ni',OM[:,:3,:3],P)+OM[:,:3,3];q=np.where(active[:,None],q,q0);bq=np.einsum('nij,nj->ni',BM[:,:3,:3],BP)+BM[:,:3,3]
 me=bpy.data.meshes.new('FittingProxy');me.from_pydata(bq.tolist(),[],BT.tolist());me.update();ob=bpy.data.objects.new('FittingProxy',me);bpy.context.collection.objects.link(ob);bmsh=bmesh.new();bmsh.from_mesh(me);bmesh.ops.remove_doubles(bmsh,verts=list(bmsh.verts),dist=.00001);bmesh.ops.holes_fill(bmsh,edges=[e for e in bmsh.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bmsh,faces=list(bmsh.faces));bmsh.to_mesh(me);bmsh.free();bpy.context.view_layer.objects.active=ob;ob.select_set(True);me.remesh_voxel_size=.0025;bpy.ops.object.voxel_remesh();me=ob.data;tree=BVHTree.FromPolygons([v.co for v in me.vertices],[list(f.vertices) for f in me.polygons]);print('PROXY',sample,len(me.vertices),flush=True)
 relax=np.clip((abs(P[:,0])-.12)/.06,0,1)*np.clip((.34-abs(P[:,0]))/.025,0,1)*np.clip((P[:,2]-1.10)/.04,0,1)*np.clip((1.42-P[:,2])/.06,0,1)
 for it in range(70):
  mean=np.zeros_like(q);np.add.at(mean,ea,q[eb]);mean/=np.maximum(ec[:,None],1);q+=sync((mean-q)*(.12*relax[:,None]));corr=np.zeros_like(q);count=np.zeros(len(q));worst=0;neg=0
  for j,s in enumerate(np.concatenate([q[ids],q[F].mean(1)])):
   hit,n,fi,dist=tree.find_nearest(Vector(s));normal=np.array(n);signed=np.dot(s-hit,normal)
   if signed>=.004 or dist>.15:continue
   vs=[ids[j]] if j<len(ids) else F[j-len(ids)];move=normal*min(.015,.004-signed)
   for v in vs:corr[v]+=move;count[v]+=1
   if signed<0:neg+=1;worst=max(worst,-signed)
  corr/=np.maximum(count[:,None],1);q+=sync(corr)*active[:,None]
  if it%20==0:print('ITER',sample,it,neg,worst,flush=True)
 inv=np.linalg.inv(M[:,:3,:3]);delta=np.einsum('nij,nj->ni',inv,q-q0);cross=np.cross(q[T[:,1]]-q[T[:,0]],q[T[:,2]]-q[T[:,0]]);nn=np.zeros_like(N)
 for j in range(3):np.add.at(nn,T[:,j],cross)
 ns=np.zeros((an,3));np.add.at(ns,alias,nn);nn=ns[alias];nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-9);restN=np.einsum('nij,nj->ni',inv,nn);restN/=np.maximum(np.linalg.norm(restN,axis=1)[:,None],1e-9);nd=np.where(active[:,None],restN-N,0)
 anchors.append({'shape':file.stem,'feature':[],'deltas':delta.ravel().tolist(),'normalDeltas':nd.ravel().tolist()});print('DONE',sample,'delta',np.max(np.linalg.norm(delta,axis=1)),'singular',np.linalg.svd(M[:,:3,:3],compute_uv=False)[:,-1].min(),flush=True);bpy.data.objects.remove(ob,do_unlink=True)
(w/'stable-shell-profile.json').write_text(json.dumps({'vertexCount':len(P),'vertices':P.ravel().tolist(),'normals':N.ravel().tolist(),'anchors':anchors},separators=(',',':')))
q=json.loads((w/'stable-shell-queue.json').read_text());q[0]['name']='character-finish32-stable-probe';q[0]['env']['VISUAL_CHARACTER_OUT']=str(w.resolve()/'stable-probe');q[0]['env']['VISUAL_CHARACTER_TEST_PROFILE']=str(w.resolve()/'stable-shell-profile.json');q[0]['env']['VISUAL_CHARACTER_CLOTH_CLIPS']='SliceApproach';(w/'stable-probe-queue.json').write_text(json.dumps(q,indent=2))
