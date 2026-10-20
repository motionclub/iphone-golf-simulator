import json,numpy as np,time
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
w=Path('work/character-finish32');data=json.loads((w/'twist-source/poses/male_intro.json').read_text());b=data['parts'][0];t=next(p for p in data['parts'] if p['name']=='Kit_Top');old=next(p for p in json.loads((w/'refined/poses/male_intro.json').read_text())['parts'] if p['name']=='Kit_Top')
P=np.array(t['vertices']).reshape(-1,3);N=np.array(t['normals']).reshape(-1,3);WI=np.array(t['indices']).reshape(-1,4);W=np.array(t['weights']).reshape(-1,4);OP=np.array(old['vertices']).reshape(-1,3);OWI=np.array(old['indices']).reshape(-1,4);OW=np.array(old['weights']).reshape(-1,4);binds=np.array(b['bindposes']).reshape(-1,4,4);rest=dict(zip(b['bones'],np.linalg.inv(binds)[:,:3,3]));kd=KDTree(len(OP))
for i,p in enumerate(OP):kd.insert(Vector(p),i)
kd.balance();oid=np.array([kd.find(Vector(p))[1] for p in P]);BP=np.array(b['vertices']).reshape(-1,3);BT=np.array(b['triangles']).reshape(-1,3);BWI=np.array(b['indices']).reshape(-1,4);BW=np.array(b['weights']).reshape(-1,4)
region=(abs(BP[:,0])<.21)&(BP[:,2]>1.03)&(BP[:,2]<1.31);ST=BT[np.all(region[BT],axis=1)];active=(abs(P[:,0])>.08)&(abs(P[:,0])<.21)&(P[:,2]>1.06)&(P[:,2]<1.31);activeids=np.flatnonzero(active)
featureBones=['Spine','UpperChest','LeftShoulder','LeftUpperArm','RightShoulder','RightUpperArm'];featureScale=5.0
files=sorted((w/'twist-motion-data/matrices').glob('*.json'))+sorted((w/'collision-poses/matrices').glob('*.json'));names=[];features=[];deltas=[];normalDeltas=[];minSingular=[]
def smooth(a,z,x):
 u=np.clip((x-a)/(z-a),0,1);return u*u*(3-2*u)
field=np.maximum(smooth(.145,.215,abs(P[:,0])),smooth(1.17,1.30,P[:,2]))
for fi,f in enumerate(files):
 d=json.loads(f.read_text());bm=np.array(d['parts'][0]['skinMatrices']).reshape(-1,4,4);actual=dict(zip(b['bones'],bm));desired={n:m.copy() for n,m in actual.items()};feature=[];invChest=np.linalg.inv(actual['Chest'])
 for name in featureBones:
  rel=invChest@actual[name];feature.extend(rel[:3,:2].T.ravel().tolist());feature.extend((rel[:3,3]*featureScale).tolist())
 for side in ['Left','Right']:
  name=side+'UpperArm';a=rest[name];axis=rest[side+'LowerArm']-a;axis/=np.linalg.norm(axis);parent=actual[side+'Shoulder'][:3,:3];direction=actual[name][:3,:3]@axis;pre=parent@axis;R=np.array(Vector(pre).rotation_difference(Vector(direction)).to_matrix())@parent;desired[name][:3,:3]=R;desired[name][:3,3]=actual[name][:3,:3]@a+actual[name][:3,3]-R@a
 M=(np.array([actual[n] for n in t['bones']])[WI]*W[:,:,None,None]).sum(1);D=(np.array([desired[n] for n in old['bones']])[OWI[oid]]*OW[oid,:,None,None]).sum(1);OM=(np.array([actual[n] for n in old['bones']])[OWI[oid]]*OW[oid,:,None,None]).sum(1);D=OM+(D-OM)*field[:,None,None];q=np.einsum('nij,nj->ni',D[:,:3,:3],P)+D[:,:3,3];q0=np.einsum('nij,nj->ni',M[:,:3,:3],P)+M[:,:3,3]
 BM=(bm[BWI]*BW[:,:,None,None]).sum(1);bq=np.einsum('nij,nj->ni',BM[:,:3,:3],BP)+BM[:,:3,3];tree=BVHTree.FromPolygons([Vector(p) for p in bq],ST.tolist(),all_triangles=True)
 for i in activeids:
  hit,n,j,dist=tree.find_nearest(Vector(q[i]));signed=np.dot(q[i]-hit,n)
  if signed<.006 and dist<.025:q[i]=np.array(hit)+np.array(n)*.006
 inv=np.linalg.inv(M[:,:3,:3]);delta=np.einsum('nij,nj->ni',inv,q-q0);nn=np.einsum('nij,nj->ni',D[:,:3,:3],N);nn=np.einsum('nij,nj->ni',inv,nn);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-9)
 if not np.all(np.isfinite(delta)) or np.max(abs(delta))>2:raise ValueError('Invalid garment target '+f.stem)
 names.append(f.parent.parent.name+':'+f.stem);features.append(feature);deltas.append(delta.astype(np.float32));normalDeltas.append((nn-N).astype(np.float32))
 if fi%25==0:print('TARGET',fi,len(files),f.stem,flush=True)
features=np.array(features);deltas=np.array(deltas);normalDeltas=np.array(normalDeltas);np.savez_compressed(w/'twist-motion-targets.npz',names=names,features=features,deltas=deltas,normalDeltas=normalDeltas)
# Select a bounded first set by rotation-and-position coverage, retaining the difficult contact poses.
distance=((features[:,None,:]-features[None,:,:])**2).mean(2);selected=[i for i,n in enumerate(names) if n.startswith('collision-poses:male_SliceApproach_') and n.rsplit('_',1)[1] in ['3','4','8']]
while len(selected)<96:
 closest=distance[:,selected].min(1);closest[selected]=-1;candidate=int(np.argmax(closest))
 if closest[candidate]<1e-7:break
 selected.append(candidate)
anchors=[]
for order,i in enumerate(selected):
 anchors.append({'shape':f'Pose{order:03d}','sample':names[i],'feature':np.round(features[i],7).tolist(),'deltas':np.round(deltas[i].ravel(),7).tolist(),'normalDeltas':np.round(normalDeltas[i].ravel(),7).tolist()})
profile={'vertexCount':len(P),'vertices':P.ravel().tolist(),'normals':N.ravel().tolist(),'featureBones':featureBones,'featurePositionScale':featureScale,'anchors':anchors};out=w/'twist-motion-profile.json';out.write_text(json.dumps(profile,separators=(',',':')));report={'samples':len(names),'anchors':len(anchors),'maxFeatureRmsDistance':float(np.sqrt(distance[:,selected].min(1).max())),'bytes':out.stat().st_size,'selectedSamples':[names[i] for i in selected]};(w/'twist-motion-profile-report.json').write_text(json.dumps(report,indent=2));print('PROFILE',report,flush=True)
