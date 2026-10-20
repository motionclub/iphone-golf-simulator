import json,numpy as np
from pathlib import Path
O=Path('work/reference-rebuild/face-finish30-lids');d=json.loads(Path('proof/reference-rebuild/face-finish30-lids-normal0/poses/female_closed.json').read_text());m=d['parts'][0]
p=np.array(m['vertices']).reshape(-1,3);posed=np.array(m['posedVertices']).reshape(-1,3);M=np.array(m['skinMatrices']).reshape(-1,4,4);ix=np.array(m['indices']).reshape(-1,4);w=np.array(m['weights']).reshape(-1,4);B=(M[ix]*w[:,:,None,None]).sum(1);unskin=np.linalg.solve(B[:,:3,:3],(posed-B[:,:3,3])[...,None])[...,0];op=np.load(O/'female-operation.npz');src=op['after']*np.array([-1,1,1]);full=(np.load(O/'female-lids.npz')['Hero_Blink']+op['Hero_Blink'])*np.array([-1,1,1]);a=np.flatnonzero(op['mask']>0)
# Unity preserves most of the source order, but UV splits and import optimization may reorder.
lookup={tuple(np.round(v,6)):i for i,v in enumerate(src)};pairs=[]
for j,v in enumerate(p):
 i=lookup.get(tuple(np.round(v,6)))
 if i is not None and op['mask'][i]>0:pairs.append((i,j))
prefixError=np.linalg.norm(p[a]-src[a],axis=1);assert prefixError.max()<1e-6; pairs=np.c_[a,a];err=np.linalg.norm(unskin[pairs[:,1]]-full[pairs[:,0]],axis=1)
# Exact bone-conjugated base normals under the diagnostic have no moving deltas.
N=np.array(m['normals']).reshape(-1,3);posedN=np.array(m['posedNormals']).reshape(-1,3);np.savez_compressed(O/'actual-female-closed.npz',basis=p,closed=unskin,triangles=np.array(m['triangles']).reshape(-1,3),normals=N,sourcePairs=pairs)
report={'actualFile':'proof/reference-rebuild/face-finish30-lids-normal0/poses/female_closed.json','mappedEyelidVertices':len(pairs),'maxPositionErrorMm':float(err.max()*1000),'medianPositionErrorMm':float(np.median(err)*1000),'p99PositionErrorMm':float(np.quantile(err,.99)*1000),'largest':[{'source':int(pairs[k,0]),'actual':int(pairs[k,1]),'errorMm':float(err[k]*1000)}for k in np.argsort(err)[-8:]]};(O/'ACTUAL_GEOMETRY_CONTRACT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
