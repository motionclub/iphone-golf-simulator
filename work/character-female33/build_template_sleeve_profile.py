import json,numpy as np,itertools
from pathlib import Path
w=Path('work/character-female33');text=(w/'matrix-cuff-fit-profile.json').read_text();d=json.loads(text.split(',"anchors":',1)[0]+'}');del text
src=json.loads((w/'cuff-fit-source/poses/female_intro.json').read_text());t=next(p for p in src['parts'] if p['name']=='Kit_Top');P=np.array(d['vertices']).reshape(-1,3);N=np.array(d['normals']).reshape(-1,3);nv=len(P);controls=d['controls'];names=[x for x in t['bones'] if x=='Chest' or any(c['bone']==x for c in controls)];W=np.array(t['weights']).reshape(-1,4);I=np.array(t['indices']).reshape(-1,4);dense=np.array([(W*(I==t['bones'].index(n))).sum(1) for n in names]).T
mass=dense[:,names.index('LeftUpperArm')]+dense[:,names.index('RightUpperArm')]
def sm(a,b,x):
 u=np.clip((x-a)/(b-a),0,1);return u*u*(3-2*u)
template=np.load(w/'male-template-correspondence.npz');SP=template['P'];SN=template['N']
mov=sm(.01,.12,mass)*(1-sm(.78,.98,mass));grid={};cell=.016
for i,p in enumerate(SP):grid.setdefault(tuple(np.floor(p/cell).astype(int)),[]).append(i)
cache={};rows=[];cols=[];weights=[]
for i in np.flatnonzero(mov>0):
 p=SP[i];key=tuple(np.floor(p/cell).astype(int))
 if key not in cache:cache[key]=np.array([j for shift in itertools.product([-1,0,1],repeat=3) for j in grid.get(tuple(a+s for a,s in zip(key,shift)),[])])
 ids=cache[key];dist=((SP[ids]-p)**2).sum(1);keep=(dist<cell**2)&(abs(SN[ids]@SN[i])>.45);ids=ids[keep];ww=np.exp(-dist[keep]/.008**2);ww/=ww.sum();rows.extend([i]*len(ids));cols.extend(ids.tolist());weights.extend(ww.tolist())
rows=np.array(rows);cols=np.array(cols);weights=np.array(weights)
for iteration in range(12):
 avg=np.stack([np.bincount(rows,weights=weights*dense[cols,j],minlength=nv) for j in range(len(names))],axis=1);dense+=(avg-dense)*mov[:,None]*.5
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
report={'vertices':nv,'shapes':k,'transitionVertices':int(sum(mov>0)),'maxErrorMm':pos*1000,'maxNormalError':normal,'cuffsAndTorsoPreserved':True};print(report,flush=True);assert pos<.0005 and normal<.035
np.savez_compressed(w/'template-sleeve-bindings.npz',weights=dense,boneNames=np.array(names),B=B)
d['anchors']=[{'shape':f'Matrix{i:03d}','deltas':np.round(s[:nv*3],8).tolist(),'normalDeltas':np.round(s[nv*3:]/.02,8).tolist()} for i,s in enumerate(shapes)];(w/'matrix-template-sleeve-profile.json').write_text(json.dumps(d,separators=(',',':')));(w/'template-sleeve-report.json').write_text(json.dumps(report,indent=2));print('DONE',flush=True)
