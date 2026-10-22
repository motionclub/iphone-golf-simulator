from pathlib import Path
import numpy as np,json
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist30-fingers';reports=[]
for label in ('female_Driver_top','female_Putter_address','male_Driver_top'):
 d=json.loads((R/'proof/reference-rebuild/golf-wrist29-continuous3/poses'/f'{label}.json').read_text());p=next(v for v in d['parts'] if v['name']=='Body');names=p['bones'];V=np.array(p['vertices']).reshape(-1,3);T=np.array(p['triangles']).reshape(-1,3);weights=np.array(p['weights']).reshape(-1,4);idx=np.array(p['indices']).reshape(-1,4);bind=np.array(p['bindposes']).reshape(-1,4,4);rest=np.linalg.inv(bind);skin=np.array(p['skinMatrices']).reshape(-1,4,4);posed=np.zeros_like(V)
 for k in range(4):posed+=weights[:,k,None]*(np.einsum('nij,nj->ni',skin[idx[:,k],:3,:3],V)+skin[idx[:,k],:3,3])
 dense=np.zeros((len(V),len(names)))
 for k in range(4):dense[np.arange(len(V)),idx[:,k]]+=weights[:,k]
 side='Right';dig=['Thumb','Index','Middle','Ring','Little'];mass=np.stack([dense[:,[i for i,n in enumerate(names) if n.startswith(side+dg)]].sum(1) for dg in dig],axis=1);mask=mass.sum(1)>.5
 def edges(P):
  q=P[T];return np.stack([np.linalg.norm(q[:,1]-q[:,0],axis=1),np.linalg.norm(q[:,2]-q[:,1],axis=1),np.linalg.norm(q[:,0]-q[:,2],axis=1)],axis=1)
 old=edges(V);new=edges(posed);ratios=new/np.maximum(old,1e-10);tm=mask[T].all(1);worst=np.where(tm)[0][np.argsort(ratios[tm].max(1))[-10:]][::-1];rs=[]
 for ti in worst:
  ids=T[ti];rs.append({'triangle':int(ti),'vertices':ids.tolist(),'maxEdgeStretch':float(ratios[ti].max()),'restEdgeMm':(old[ti]*1000).tolist(),'posedEdgeMm':(new[ti]*1000).tolist(),'weights':[{names[i]:float(w) for i,w in enumerate(dense[v]) if w>.001} for v in ids]})
 # Each welded source position should carry one weight field.
 aliases={}
 for v in np.where(mask)[0]:aliases.setdefault(tuple(np.round(V[v],6)),[]).append(v)
 diffs=[]
 for key,ids in aliases.items():
  if len(ids)>1:
   delta=float(np.abs(dense[ids]-dense[ids[0]]).sum(1).max())
   if delta>1e-4:diffs.append({'vertices':ids,'weightL1':delta,'posedSeparationMm':float(np.linalg.norm(posed[ids]-posed[ids[0]],axis=1).max()*1000)})
 report={'label':label,'fourFingerVertices':int(mask.sum()),'triangles':int(tm.sum()),'stretchPercentiles':np.percentile(ratios[tm].max(1),[50,90,99,100]).tolist(),'weldWeightSplits':len(diffs),'maxAliasSeparationMm':max((r['posedSeparationMm'] for r in diffs),default=0),'worstTriangles':rs,'worstAliases':sorted(diffs,key=lambda r:r['posedSeparationMm'],reverse=True)[:8]};reports.append(report);print(label,report['stretchPercentiles'],'alias',report['weldWeightSplits'],report['maxAliasSeparationMm'],'worst',rs[0])
(W/'finger-source-analysis.json').write_text(json.dumps(reports,indent=2)+'\n')
