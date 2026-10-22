import json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
w=Path('work/character-finish32');data=json.loads((w/'twist-source/poses/male_intro.json').read_text());b=data['parts'][0];t=next(p for p in data['parts'] if p['name']=='Kit_Top');old=next(p for p in json.loads((w/'refined/poses/male_intro.json').read_text())['parts'] if p['name']=='Kit_Top');P=np.array(t['vertices']).reshape(-1,3);N=np.array(t['normals']).reshape(-1,3);WI=np.array(t['indices']).reshape(-1,4);W=np.array(t['weights']).reshape(-1,4);OP=np.array(old['vertices']).reshape(-1,3);OWI=np.array(old['indices']).reshape(-1,4);OW=np.array(old['weights']).reshape(-1,4);binds=np.array(b['bindposes']).reshape(-1,4,4);joints=np.linalg.inv(binds)[:,:3,3];rest=dict(zip(b['bones'],joints));kd=KDTree(len(OP))
for i,p in enumerate(OP):kd.insert(Vector(p),i)
kd.balance();oid=np.array([kd.find(Vector(p))[1] for p in P]);anchors=[]
for sample in [3,4,8]:
 f=w/f'collision-poses/matrices/male_SliceApproach_{sample}.json';d=json.loads(f.read_text());bm=np.array(d['parts'][0]['skinMatrices']).reshape(-1,4,4);actual=dict(zip(b['bones'],bm));desired={n:m.copy() for n,m in actual.items()}
 for side in ['Left','Right']:
  name=side+'UpperArm';a=rest[name];axis=rest[side+'LowerArm']-a;axis/=np.linalg.norm(axis);parent=actual[side+'Shoulder'][:3,:3];direction=actual[name][:3,:3]@axis;pre=parent@axis;swing=np.array(Vector(pre).rotation_difference(Vector(direction)).to_matrix());R=swing@parent;desired[name][:3,:3]=R;desired[name][:3,3]=actual[name][:3,:3]@a+actual[name][:3,3]-R@a
 M=(np.array([actual[n] for n in t['bones']])[WI]*W[:,:,None,None]).sum(1);D=(np.array([desired[n] for n in old['bones']])[OWI[oid]]*OW[oid,:,None,None]).sum(1);OM=(np.array([actual[n] for n in old['bones']])[OWI[oid]]*OW[oid,:,None,None]).sum(1)
 def smooth(a,z,x):
  u=np.clip((x-a)/(z-a),0,1);return u*u*(3-2*u)
 field=np.maximum(smooth(.145,.215,abs(P[:,0])),smooth(1.17,1.30,P[:,2]))
 D=OM+(D-OM)*field[:,None,None]
 q=np.einsum('nij,nj->ni',D[:,:3,:3],P)+D[:,:3,3];q0=np.einsum('nij,nj->ni',M[:,:3,:3],P)+M[:,:3,3];inv=np.linalg.inv(M[:,:3,:3]);delta=np.einsum('nij,nj->ni',inv,q-q0);nn=np.einsum('nij,nj->ni',D[:,:3,:3],N);nn=np.einsum('nij,nj->ni',inv,nn);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-9);anchors.append({'shape':f.stem,'feature':[],'deltas':delta.ravel().tolist(),'normalDeltas':(nn-N).ravel().tolist()});print(f.stem,'maxDelta',np.max(np.linalg.norm(delta,axis=1)),flush=True)
(w/'twist-field-profile.json').write_text(json.dumps({'vertexCount':len(P),'vertices':P.ravel().tolist(),'normals':N.ravel().tolist(),'anchors':anchors},separators=(',',':')));q=json.loads((w/'twist-source-queue.json').read_text());q[0]['name']='character-finish32-twist-field';q[0]['env']['VISUAL_CHARACTER_OUT']=str(w.resolve()/'twist-field');q[0]['env']['VISUAL_CHARACTER_TEST_PROFILE']=str(w.resolve()/'twist-field-profile.json');(w/'twist-field-queue.json').write_text(json.dumps(q,indent=2))
