import json,numpy as np,itertools
from pathlib import Path
w=Path('work/character-female33');text=(w/'matrix-cuff-fit-profile.json').read_text();d=json.loads(text.split(',"anchors":',1)[0]+'}');del text
src=json.loads((w/'cuff-fit-source/poses/female_intro.json').read_text());t=next(p for p in src['parts'] if p['name']=='Kit_Top');P=np.array(d['vertices']).reshape(-1,3);N=np.array(d['normals']).reshape(-1,3);nv=len(P);controls=d['controls'];names=t['bones'];W=np.array(t['weights']).reshape(-1,4);I=np.array(t['indices']).reshape(-1,4);dense=np.array([(W*(I==j)).sum(1) for j in range(len(names))]).T
hem=np.clip((1.085-P[:,2])/.09,0,1);hem=hem*hem*(3-2*hem)
dense*=1-hem[:,None];dense[:,names.index('Hips')]+=hem
source=np.load(w/'male-template-correspondence.npz');MP=source['P']*[-1,1,1];MN=source['N']*[-1,1,1];frames=json.loads((w/'template-bindframes.json').read_text());boneP={};boneN={};averageP=np.zeros_like(P);averageN=np.zeros_like(N)
for j,name in enumerate(names):
 T=np.array(frames[name]);boneP[name]=MP@T[:3,:3].T+T[:3,3];normal=MN@np.linalg.inv(T[:3,:3]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-8);boneN[name]=normal;averageP+=dense[:,j,None]*boneP[name];averageN+=dense[:,j,None]*normal
def smooth(a,b,x):
 u=np.clip((x-a)/(b-a),0,1);return u*u*(3-2*u)
fitDelta=(P-averageP)*(1-smooth(.99,1.075,P[:,2]))[:,None]
waistRad=averageP.copy();waistRad[:,1]+=.005;waistRad[:,2]=0;waistRad/=np.maximum(np.linalg.norm(waistRad,axis=1)[:,None],1e-8)
fitDelta+=waistRad*(.009*hem)[:,None];fitDelta[:,2]-=.020*hem

# A small radial ease around each female upper arm clears the existing body at the shoulders.
sourceBinds=np.array(t['bindposes']).reshape(-1,4,4);heads=np.linalg.inv(sourceBinds)[:,:3,3]
for side in ['Left','Right']:
 j=names.index(side+'UpperArm');a=heads[j];axis=heads[names.index(side+'LowerArm')]-a;axis/=np.linalg.norm(axis);rad=averageP-a;rad-=((rad@axis)[:,None]*axis);rad/=np.maximum(np.linalg.norm(rad,axis=1)[:,None],1e-8)
 ease=.007*smooth(.08,.65,dense[:,j]);fitDelta+=rad*ease[:,None]
for name in names:boneP[name]+=fitDelta
averageP+=fitDelta
d['baseVertices']=averageP.ravel().tolist();d['baseNormals']=averageN.ravel().tolist()
def sm(a,b,x):
 u=np.clip((x-a)/(b-a),0,1);return u*u*(3-2*u)
mass=dense[:,names.index('LeftUpperArm')]+dense[:,names.index('RightUpperArm')];f=sm(.15,.40,mass);B=[]
for c in controls:
 name=c['bone'];swing=name.startswith('Swing_');name=name.removeprefix('Swing_');ww=dense[:,names.index(name)].copy()
 if name in ['LeftUpperArm','RightUpperArm']:ww*=f if swing else 1-f
 row,col=c['row'],c['column'];dp=np.zeros_like(P);dn=np.zeros_like(N);dp[:,row]=ww*(boneP[name][:,col] if col<3 else 1)
 if col<3:dn[:,row]=ww*boneN[name][:,col]*.02
 B.append(np.concatenate([dp.ravel(),dn.ravel()]))
B=np.array(B);assert np.isfinite(B).all() and np.isfinite(averageP).all() and np.isfinite(averageN).all();C=np.load(w/'matrix-cuff-fit-profile-basis.npz')['C'];k=len(d['projection'])//len(controls);M=np.array(d['projection']).reshape(k,-1);shapes=(np.linalg.pinv(C@M.T,rcond=1e-8)@C)@B;E=B-M.T@shapes;pos=normal=0
for i in range(0,len(C),12):
 e=C[i:i+12]@E;pos=max(pos,float(np.linalg.norm(e[:,:nv*3].reshape(-1,nv,3),axis=2).max()));normal=max(normal,float(np.linalg.norm(e[:,nv*3:].reshape(-1,nv,3),axis=2).max()/.02))
if pos >= .0005 or normal >= .035:
 # Add only the residual modes introduced by the female waistband fit.
 vals,U=np.linalg.eigh(C.T@C/len(C));L=np.sqrt(np.maximum(vals,0))[:,None]*U.T;T=L@E;vals,U=np.linalg.eigh(T@T.T);order=np.argsort(-vals);vals=vals[order];U=U[:,order];V=(U[:,:12].T@T)/np.sqrt(np.maximum(vals[:12],1e-20))[:,None]
 for count in [2,4,8,12]:
  extraMap=E@V[:count].T;extraScale=np.maximum(np.abs(C@extraMap).max(0)*1.15,.01);extraShapes=V[:count]*extraScale[:,None];extraProjection=(extraMap/extraScale).T;residual=E-extraProjection.T@extraShapes;pos=normal=0
  for i in range(0,len(C),12):
   e=C[i:i+12]@residual;pos=max(pos,float(np.linalg.norm(e[:,:nv*3].reshape(-1,nv,3),axis=2).max()));normal=max(normal,float(np.linalg.norm(e[:,nv*3:].reshape(-1,nv,3),axis=2).max()/.02))
  if pos<.0005 and normal<.035:break
 M=np.concatenate([M,extraProjection]);shapes=np.concatenate([shapes,extraShapes]);k=len(M);d['projection']=M.ravel().tolist()
report={'vertices':nv,'shapes':k,'maxErrorMm':pos*1000,'maxNormalError':normal,'femaleGarmentSurfaceBindings':True};print(report,flush=True);assert pos<.0005 and normal<.035
np.savez_compressed(w/'direct-fit-matrix-basis.npz',weights=dense,boneNames=np.array(names),B=B)
d['anchors']=[{'shape':f'Matrix{i:03d}','deltas':np.round(s[:nv*3],8).tolist(),'normalDeltas':np.round(s[nv*3:]/.02,8).tolist()} for i,s in enumerate(shapes)];(w/'matrix-direct-fit-profile.json').write_text(json.dumps(d,separators=(',',':')));(w/'direct-fit-report.json').write_text(json.dumps(report,indent=2));print('DONE',flush=True)
