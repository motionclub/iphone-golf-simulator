from pathlib import Path
import json,numpy as np
R=Path.cwd();O=R/'work/reference-rebuild/gusset-actual-repair';p=json.loads((O/'UnderarmGusset_Female_Full.json').read_text());base=json.loads((R/'proof/reference-rebuild/character-motion-matrices17/poses/female_intro.json').read_text())['parts'][0]
def arr(x,k,n):return np.array(x[k]).reshape(-1,n)
v=arr(base,'vertices',3);bi=arr(base,'indices',4).astype(int);bw=arr(base,'weights',4);t=arr(base,'triangles',3).astype(int);a=json.loads((O/'bodyband-prototype-Full.json').read_text());bm=[{int(j):w for j,w in m.items()} for m in a['bodyMaps']];offset=np.array(p['bodyOffsets']);rows=[]
for label in ['female_intro','female_Forehand_0','female_Forehand_1']:
 parts=json.loads((R/f'proof/reference-rebuild/gusset-bodyband-cuff2/poses/{label}.json').read_text())['parts'];body=next(x for x in parts if x['name']=='Body_F');top=next(x for x in parts if x['name']=='Kit_Top');rt=arr(body,'rendererToRoot',4);m=rt[None]@arr(body,'skinMatrices',16).reshape(-1,4,4);bv=np.zeros_like(v)
 for k in range(4):bv+=(np.einsum('nij,nj->ni',m[bi[:,k],:3,:3],v)+m[bi[:,k],:3,3])*bw[:,k,None]
 gn=np.zeros_like(v);f=np.cross(bv[t[:,1]]-bv[t[:,0]],bv[t[:,2]]-bv[t[:,0]])
 for k in range(3):np.add.at(gn,t[:,k],f)
 gn/=np.maximum(np.linalg.norm(gn,axis=1)[:,None],1e-12);rt=arr(top,'rendererToRoot',4);actual=arr(top,'posedVertices',3)@rt[:3,:3].T+rt[:3,3];diff=[]
 for i,d in enumerate(bm):
  if not d:continue
  point=sum(bv[j]*w for j,w in d.items());norm=sum(gn[j]*w for j,w in d.items());norm/=np.linalg.norm(norm);diff.append(np.linalg.norm(actual[i]-point-norm*offset[i]))
 rows.append({'sample':label,'bodyPanelVertices':len(diff),'maximumErrorMetres':max(diff),'rmsErrorMetres':float(np.sqrt(np.mean(np.array(diff)**2)))})
(O/'bodyband-actual-contract.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
