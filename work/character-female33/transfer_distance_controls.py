import json,numpy as np
from pathlib import Path
w=Path('work/character-female33')
text=(w/'matrix-cuff-fit-profile.json').read_text();prefix=text.split(',"anchors":',1)[0];full=json.loads(prefix+'}');del text,prefix
source=json.loads((w/'distance-source/poses/female_intro.json').read_text());t=next(x for x in source['parts'] if x['name']=='Kit_Top');P=np.array(t['vertices']).reshape(-1,3);N=np.array(t['normals']).reshape(-1,3);nv=len(P);W=np.array(t['weights']).reshape(-1,4);WI=np.array(t['indices']).reshape(-1,4);bones=t['bones'];mass=(W*np.isin(WI,[bones.index(x) for x in ['LeftUpperArm','RightUpperArm']])).sum(1);f=np.clip((mass-.15)/.25,0,1);f=f*f*(3-2*f);controls=full['controls'];B=[]
for c in controls:
 name=c['bone'];swing=name.startswith('Swing_');name=name.removeprefix('Swing_');weights=(W*(WI==bones.index(name))).sum(1)
 if name in ['LeftUpperArm','RightUpperArm']:weights*=f if swing else 1-f
 row,col=c['row'],c['column'];dp=np.zeros_like(P);dn=np.zeros_like(N);dp[:,row]=weights*(P[:,col] if col<3 else 1)
 if col<3:dn[:,row]=weights*N[:,col]*.02
 B.append(np.concatenate([dp.ravel(),dn.ravel()]))
B=np.array(B);k=len(full['projection'])//len(controls);projection=np.array(full['projection']).reshape(k,-1);shapes=np.linalg.pinv(projection.T,rcond=1e-10)@B;errorBasis=B-projection.T@shapes;C=np.load(w/'matrix-cuff-fit-profile-basis.npz')['C'];pos=normal=0
for i in range(0,len(C),12):
 error=C[i:i+12]@errorBasis;pos=max(pos,float(np.linalg.norm(error[:,:nv*3].reshape(-1,nv,3),axis=2).max()));normal=max(normal,float(np.linalg.norm(error[:,nv*3:].reshape(-1,nv,3),axis=2).max()/.02))
report={'vertices':nv,'shapes':k,'samples':len(C),'maxPositionErrorMm':pos*1000,'maxNormalVectorError':normal,'sameControlProjectionAsFull':True};print(report,flush=True);assert pos<=.0005 and normal<=.035,report
anchors=[{'shape':f'Matrix{i:03d}','deltas':np.round(s[:nv*3],8).tolist(),'normalDeltas':np.round(s[nv*3:]/.02,8).tolist()} for i,s in enumerate(shapes)]
profile={'vertexCount':nv,'vertices':P.ravel().tolist(),'normals':N.ravel().tolist(),'controls':controls,'projection':projection.ravel().tolist(),'anchors':anchors};(w/'matrix-distance-profile.json').write_text(json.dumps(profile,separators=(',',':')));(w/'matrix-distance-profile-report.json').write_text(json.dumps(report,indent=2));print('PASS',flush=True)
