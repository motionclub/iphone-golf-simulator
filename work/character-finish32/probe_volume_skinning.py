import json,numpy as np
from pathlib import Path
from mathutils import Matrix
w=Path('work/character-finish32');data=json.loads((w/'refined/poses/male_intro.json').read_text());b=data['parts'][0];t=next(p for p in data['parts'] if p['name']=='Kit_Top');P=np.array(t['vertices']).reshape(-1,3);N=np.array(t['normals']).reshape(-1,3);WI=np.array(t['indices']).reshape(-1,4);W=np.array(t['weights']).reshape(-1,4)
def mul(a,b):return np.concatenate([(a[...,:1]*b[...,:1]-(a[...,1:]*b[...,1:]).sum(-1,keepdims=True)),a[...,:1]*b[...,1:]+b[...,:1]*a[...,1:]+np.cross(a[...,1:],b[...,1:])],axis=-1)
def rotate(q,v):return v+2*np.cross(q[:,1:],np.cross(q[:,1:],v)+q[:,:1]*v)
anchors=[]
for label in ['male_SliceApproach_3','male_SliceApproach_4','male_SliceApproach_5','male_SliceApproach_8']:
 d=json.loads((w/'collision-poses/matrices'/f'{label}.json').read_text());parts={p['name']:p for p in d['parts']};bm=np.array(parts[b['name']]['skinMatrices']).reshape(-1,4,4);mp=dict(zip(b['bones'],bm));tm=np.array([mp[n] for n in t['bones']]);M=(tm[WI]*W[:,:,None,None]).sum(1);q0=np.einsum('nij,nj->ni',M[:,:3,:3],P)+M[:,:3,3]
 R=np.array([tuple(Matrix(m.tolist()).to_quaternion()) for m in tm]);D=.5*mul(np.concatenate([np.zeros((len(tm),1)),tm[:,:3,3]],axis=1),R);rs=R[WI];ds=D[WI];sign=np.where((rs*rs[:,:1]).sum(-1,keepdims=True)<0,-1,1);real=(rs*sign*W[:,:,None]).sum(1);dual=(ds*sign*W[:,:,None]).sum(1);length=np.linalg.norm(real,axis=1,keepdims=True);real/=length;dual/=length;dual-=real*(real*dual).sum(1,keepdims=True);conj=real.copy();conj[:,1:]*=-1;translation=2*mul(dual,conj)[:,1:];q=rotate(real,P)+translation;norm=rotate(real,N)
 inv=np.linalg.inv(M[:,:3,:3]);delta=np.einsum('nij,nj->ni',inv,q-q0);nr=np.einsum('nij,nj->ni',inv,norm);nr/=np.maximum(1e-10,np.linalg.norm(nr,axis=1,keepdims=True));nd=nr-N
 if label.endswith('_4'):base=json.loads((w/'tailored-fit-welded.json').read_text())['anchors'][0]
 else:base=json.loads((w/f'{label}-fit.json').read_text())
 anchors.append({'shape':label,'feature':base['feature'],'deltas':delta.ravel().tolist(),'normalDeltas':nd.ravel().tolist()});print(label,'posedMaxMm',np.linalg.norm(q-q0,axis=1).max()*1000,'restMaxMm',np.linalg.norm(delta,axis=1).max()*1000,flush=True)
(w/'volume-skinning-probe.json').write_text(json.dumps({'vertexCount':len(P),'vertices':t['vertices'],'normals':t['normals'],'anchors':anchors},separators=(',',':')))
