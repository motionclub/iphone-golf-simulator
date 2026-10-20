import json,numpy as np,itertools
from pathlib import Path
w=Path('work/character-female33');text=(w/'matrix-cuff-fit-profile.json').read_text();d=json.loads(text.split(',"anchors":',1)[0]+'}');del text
src=json.loads((w/'fitted-construction/poses/female_intro.json').read_text());t=next(p for p in src['parts'] if p['name']=='Kit_Top');d['vertices']=t['vertices'];d['normals']=t['normals'];d['vertexCount']=len(t['vertices'])//3;P=np.array(d['vertices']).reshape(-1,3);N=np.array(d['normals']).reshape(-1,3);nv=len(P);controls=d['controls'];names=t['bones'];W=np.array(t['weights']).reshape(-1,4);I=np.array(t['indices']).reshape(-1,4);dense=np.array([(W*(I==j)).sum(1) for j in range(len(names))]).T
allowed={c['bone'].removeprefix('Swing_') for c in controls}|{'Chest'};missing=sum(dense[:,j] for j,name in enumerate(names) if name not in allowed);print('Unrepresented weight',float(np.max(missing)),flush=True)
def sm(a,b,x):
 u=np.clip((x-a)/(b-a),0,1);return u*u*(3-2*u)
mass=dense[:,names.index('LeftUpperArm')]+dense[:,names.index('RightUpperArm')];f=sm(.15,.40,mass);B=[]
for c in controls:
 name=c['bone'];swing=name.startswith('Swing_');name=name.removeprefix('Swing_');ww=dense[:,names.index(name)].copy()
 if name in ['LeftUpperArm','RightUpperArm']:ww*=f if swing else 1-f
 row,col=c['row'],c['column'];dp=np.zeros_like(P);dn=np.zeros_like(N);dp[:,row]=ww*(P[:,col] if col<3 else 1)
 if col<3:dn[:,row]=ww*N[:,col]*.02
 B.append(np.concatenate([dp.ravel(),dn.ravel()]))
B=np.array(B);C=np.load(w/'matrix-cuff-fit-profile-basis.npz')['C'];k=len(d['projection'])//len(controls);M=np.array(d['projection']).reshape(k,-1);shapes=(np.linalg.pinv(C@M.T,rcond=1e-8)@C)@B;E=B-M.T@shapes;pos=normal=0
for i in range(0,len(C),12):
 e=C[i:i+12]@E;pos=max(pos,float(np.linalg.norm(e[:,:nv*3].reshape(-1,nv,3),axis=2).max()));normal=max(normal,float(np.linalg.norm(e[:,nv*3:].reshape(-1,nv,3),axis=2).max()/.02))
report={'vertices':nv,'shapes':k,'maxErrorMm':pos*1000,'maxNormalError':normal,'femaleGarmentSurfaceBindings':True};print(report,flush=True);assert pos<.0005 and normal<.035
np.savez_compressed(w/'fitted-construction-matrix-basis.npz',weights=dense,boneNames=np.array(names),B=B)
d['anchors']=[{'shape':f'Matrix{i:03d}','deltas':np.round(s[:nv*3],8).tolist(),'normalDeltas':np.round(s[nv*3:]/.02,8).tolist()} for i,s in enumerate(shapes)];(w/'matrix-fitted-construction-profile.json').write_text(json.dumps(d,separators=(',',':')));(w/'fitted-construction-report.json').write_text(json.dumps(report,indent=2));print('DONE',flush=True)
