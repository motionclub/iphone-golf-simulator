import json,numpy as np
from pathlib import Path
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist30-fingers';reports=[]
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
for path in sorted((R/'proof/reference-rebuild/golf-wrist29-continuous3/poses').glob('female*.json')):
 d=json.loads(path.read_text());p=next(v for v in d['parts'] if v['name']=='Body');names=p['bones'];V=np.array(p['vertices']).reshape(-1,3);tri=np.array(p['triangles']).reshape(-1,3);weights=np.array(p['weights']).reshape(-1,4);indices=np.array(p['indices']).reshape(-1,4);bind=np.array(p['bindposes']).reshape(-1,4,4);rest=np.linalg.inv(bind);skin=np.array(p['skinMatrices']).reshape(-1,4,4);dense=np.zeros((len(V),len(names)))
 for k in range(4):dense[np.arange(len(V)),indices[:,k]]+=weights[:,k]
 changed=dense.copy();counts={}
 for side in ('Left','Right'):
  hand=names.index(side+'Hand');handMass=dense[:,[i for i,n in enumerate(names) if n==side+'Hand' or any(n.startswith(side+dg) for dg in ('Thumb','Index','Middle','Ring','Little'))]].sum(1);bestDist=np.full(len(V),np.inf);choice=np.full(len(V),-1);station=np.zeros(len(V));sets=[];lengths=[]
  for di,digit in enumerate(('Index','Middle','Ring','Little')):
   ids=[names.index(side+digit+j) for j in ('Proximal','Intermediate','Distal')];P,M,D=rest[ids,:3,3];tail=D+(D-M)/np.linalg.norm(D-M)*.018;points=[P,M,D,tail];lens=[np.linalg.norm(points[j+1]-points[j]) for j in range(3)];sets.append(ids);lengths.append(lens);prefix=0
   for j in range(3):
    axis=(points[j+1]-points[j])/lens[j];along=(V-points[j])@axis;clamp=np.clip(along,0,lens[j]);dist=np.linalg.norm(V-(points[j]+clamp[:,None]*axis),axis=1);valid=dist<bestDist;bestDist[valid]=dist[valid];choice[valid]=di;station[valid]=prefix+clamp[valid];prefix+=lens[j]
  for di,digit in enumerate(('Index','Middle','Ring','Little')):
   ids=sets[di];first,second,_=lengths[di];strength=smooth(.002,.016,station)*(1-smooth(.010,.016,bestDist))*smooth(.2,.6,handMass)*(choice==di);basal=smooth(0,.014,station);mid=smooth(first-.007,first+.007,station);end=smooth(first+second-.006,first+second+.006,station);field=np.zeros_like(dense);field[:,hand]=1-basal;field[:,ids[0]]=basal*(1-mid);field[:,ids[1]]=mid*(1-end);field[:,ids[2]]=end;changed=changed*(1-strength[:,None])+field*strength[:,None];counts[side+digit]=int((strength>1e-6).sum())
 def skinning(W):
  out=np.zeros_like(V)
  for i in range(len(names)):
   mask=W[:,i]>0;out[mask]+=(V[mask]@skin[i,:3,:3].T+skin[i,:3,3])*W[mask,i,None]
  return out
 old=skinning(dense);new=skinning(changed);mask=np.abs(changed-dense).sum(1)>1e-6;tm=mask[tri].any(1)
 def ratios(P):
  q=P[tri];v=V[tri];a=np.stack([np.linalg.norm(q[:,(j+1)%3]-q[:,j],axis=1) for j in range(3)],1);b=np.stack([np.linalg.norm(v[:,(j+1)%3]-v[:,j],axis=1) for j in range(3)],1);return(a/np.maximum(b,1e-10)).max(1)
 before=ratios(old);after=ratios(new);r={'label':d['label'],'changedCounts':counts,'changedVertices':int(mask.sum()),'maxWeightL1':float(abs(changed-dense).sum(1).max()),'maxPosedShiftMm':float(np.linalg.norm(new-old,axis=1).max()*1000),'affectedEdgeStretchBefore':np.percentile(before[tm],[50,90,99,100]).tolist(),'affectedEdgeStretchAfter':np.percentile(after[tm],[50,90,99,100]).tolist(),'indexTriangle22311BeforeAfter':[float(before[22311]),float(after[22311])],'worsenedAffectedTriangles':int((after[tm]>before[tm]+.1).sum())};reports.append(r);print(r)
 if d['label']=='female_Driver_top':np.savez_compressed(W/'female-field-proof.npz',vertices=V,oldWeights=dense,newWeights=changed,posedBefore=old,posedAfter=new,triangles=tri,bones=np.array(names),bindposes=bind,skinMatrices=skin)
(W/'chain-source-proof.json').write_text(json.dumps(reports,indent=2)+'\n')
