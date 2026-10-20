import json,numpy as np
from pathlib import Path
R=Path.cwd();O=R/'work/reference-rebuild/golf-wrist30-surface';P=R/'proof/reference-rebuild/golf-wrist29-continuous3/poses'
def load(label):
 p=next(x for x in json.load(open(P/(label+'.json')))['parts'] if x['name']=='Body');v=np.array(p['vertices']).reshape(-1,3);posed=np.array(p['posedVertices']).reshape(-1,3);w=np.array(p['weights']).reshape(-1,4);ix=np.array(p['indices']).reshape(-1,4);b=np.array(p['bindposes']).reshape(-1,4,4);m=np.array(p['skinMatrices']).reshape(-1,4,4);n=p['bones'];tr=np.array(p['triangles']).reshape(-1,3);rest=np.linalg.inv(b);current=m@rest;dense=np.zeros((len(v),len(n)))
 for k in range(4):dense[np.arange(len(v)),ix[:,k]]+=w[:,k]
 return p,v,posed,w,ix,b,m,n,tr,rest,current,dense
if __name__=='__main__':
 for label in ['female_Putter_address','female_Driver_top','male_Putter_address','male_Driver_top']:
  p,v,posed,w,ix,b,m,n,tr,rest,cur,dense=load(label);print(label,'oracle',p['bakeOracleMaxMetres'])
  for side in ['Right','Left']:
   I=[n.index(side+x) for x in ['LowerArm','Hand','MiddleProximal']];L,H,M=rest[I,:3,3];axis=(H-L)/np.linalg.norm(H-L);rad=v-H;along=rad@axis;rad-=along[:,None]*axis;mask=(dense[:,I[0]]+dense[:,I[1]]>.9)&(along>-.14)&(along<.08)
   print(side,'rest LHM',rest[I,:3,3].round(4).tolist(),'current',cur[I,:3,3].round(4).tolist())
   for s in np.arange(-.12,.071,.01):
    ids=np.flatnonzero(mask&(along>=s)&(along<s+.01))
    if len(ids):print(round(s*1000),len(ids),'Hweight',round(dense[ids,I[1]].mean(),3),'centroid rest',v[ids].mean(0).round(4).tolist(),'posed',posed[ids].mean(0).round(4).tolist(),'radius',round(np.linalg.norm(rad[ids],axis=1).mean()*1000,1))
