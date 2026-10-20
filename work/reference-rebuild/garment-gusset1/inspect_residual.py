from pathlib import Path
s=Path('work/reference-rebuild/garment-gusset1/check_patch.py').read_text();exec(s[:s.index('import sys')])
bp,before,after,rawafter,stats=deform('female_Forehand_1');cam=np.array([2.4,1.3,4.1]);fw=target-cam;fw/=np.linalg.norm(fw);camRight=np.cross([0,1,0],fw);camRight/=np.linalg.norm(camRight);camUp=np.cross(fw,camRight)
bz,bid=image(bp,bt[keep]);tz,tid=image(after,nt);phys=np.full_like(bid,-1);hit=bid>=0;phys[hit]=np.where(keep)[0][bid[hit]];reg=np.isin(phys,[6385,6386,6396,6397,6753,6754,15928,15929,15931,15934,15936,15937,19373]);bad=reg&(tid>=0)&(bz<tz-.0008);rows=[]
for f in np.unique(tid[bad]):
 ids=nt[f];rows.append({'face':int(f),'sourceFace':int(p['parents'][f]),'pixels':int((bad&(tid==f)).sum()),'deficitMm':float(np.max((tz-bz)[bad&(tid==f)])*1000),'free':free[ids].tolist(),'ids':ids.tolist(),'clearanceDisplacementMm':(np.linalg.norm(after[ids]-rawafter[ids],axis=1)*1000).tolist(),'posedEdgeMaxMm':float(max(np.linalg.norm(after[ids[j]]-after[ids[(j+1)%3]]) for j in range(3))*1000)})
(Z/'residual-diagnosis.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
