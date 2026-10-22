import json,numpy as np,itertools
from pathlib import Path
w=Path('work/character-female33');text=(w/'matrix-cuff-fit-profile.json').read_text();d=json.loads(text.split(',"anchors":',1)[0]+'}');del text
src=json.loads((w/'cuff-fit-source/poses/female_intro.json').read_text());t=next(x for x in src['parts'] if x['name']=='Kit_Top');b=src['parts'][0];P=np.array(d['vertices']).reshape(-1,3);N=np.array(d['normals']).reshape(-1,3);nv=len(P);controls=d['controls'];names=[x for x in t['bones'] if x=='Chest' or any(c['bone']==x for c in controls)];dense=np.zeros((nv,len(names)));BP=np.array(b['vertices']).reshape(-1,3);BW=np.array(b['weights']).reshape(-1,4);BI=np.array(b['indices']).reshape(-1,4);keep=BP[:,2]>.90;BP=BP[keep];BW=BW[keep];BI=BI[keep];D=np.zeros((len(BP),len(names)))
for j in range(4):
 for bi,name in enumerate(b['bones']):
  target=name if name in names else 'Hips' if 'Leg' in name else 'Chest';D[:,names.index(target)]+=BW[:,j]*(BI[:,j]==bi)
cell=.03;grid={}
for i,p in enumerate(BP):grid.setdefault(tuple(np.floor(p/cell).astype(int)),[]).append(i)
cache={}
for i,p in enumerate(P):
 key=tuple(np.floor(p/cell).astype(int))
 if key not in cache:
  ids=[]
  for reach in [1,2,3]:
   ids=[j for shift in itertools.product(range(-reach,reach+1),repeat=3) for j in grid.get(tuple(a+s for a,s in zip(key,shift)),[])]
   if len(ids)>=16:break
  cache[key]=np.array(ids)
 ids=cache[key];dist=((BP[ids]-p)**2).sum(1);order=np.argpartition(dist,15)[:16];chosen=ids[order];ww=1/(dist[order]+.000025);ww/=ww.sum();dense[i]=(D[chosen]*ww[:,None]).sum(0)
# The turned cuff is one ring attached to her upper arm, as in the accepted male polo.
oldW=np.array(t['weights']).reshape(-1,4);oldI=np.array(t['indices']).reshape(-1,4)
for side in ['Left','Right']:
 name=side+'UpperArm';mass=(oldW*(oldI==t['bones'].index(name))).sum(1);f=np.clip((mass-.60)/.35,0,1);f=f*f*(3-2*f);dense*=1-f[:,None];dense[:,names.index(name)]+=f
order=np.argsort(-dense,axis=1)[:,:4];mask=np.zeros_like(dense);np.put_along_axis(mask,order,1,axis=1);dense*=mask;dense/=dense.sum(1)[:,None];mass=dense[:,names.index('LeftUpperArm')]+dense[:,names.index('RightUpperArm')];f=np.clip((mass-.15)/.25,0,1);f=f*f*(3-2*f);B=[]
for c in controls:
 name=c['bone'];swing=name.startswith('Swing_');name=name.removeprefix('Swing_');ww=dense[:,names.index(name)].copy()
 if name in ['LeftUpperArm','RightUpperArm']:ww*=f if swing else 1-f
 row,col=c['row'],c['column'];dp=np.zeros_like(P);dn=np.zeros_like(N);dp[:,row]=ww*(P[:,col] if col<3 else 1)
 if col<3:dn[:,row]=ww*N[:,col]*.02
 B.append(np.concatenate([dp.ravel(),dn.ravel()]))
B=np.array(B);C=np.load(w/'matrix-cuff-fit-profile-basis.npz')['C'];k=len(d['projection'])//len(controls);M=np.array(d['projection']).reshape(k,-1);shapes=(np.linalg.pinv(C@M.T,rcond=1e-8)@C)@B;E=B-M.T@shapes;pos=normal=0
for i in range(0,len(C),12):
 e=C[i:i+12]@E;pos=max(pos,float(np.linalg.norm(e[:,:nv*3].reshape(-1,nv,3),axis=2).max()));normal=max(normal,float(np.linalg.norm(e[:,nv*3:].reshape(-1,nv,3),axis=2).max()/.02))
report={'maxErrorMm':pos*1000,'normalError':normal,'vertices':nv,'shapeCount':k,'sourceGeometryUnchanged':True,'bodyBindingsUnchanged':True,'method':'Garment-only transfer of female body bindings; identical shared matrix control system'};print(report,flush=True);assert pos<.001 and normal<.035
np.savez_compressed(w/'female-bindings.npz',weights=dense,boneNames=np.array(names),B=B);d['anchors']=[{'shape':f'Matrix{i:03d}','deltas':np.round(s[:nv*3],8).tolist(),'normalDeltas':np.round(s[nv*3:]/.02,8).tolist()} for i,s in enumerate(shapes)];(w/'matrix-female-binding-profile.json').write_text(json.dumps(d,separators=(',',':')));(w/'female-binding-report.json').write_text(json.dumps(report,indent=2));print('DONE',flush=True)
