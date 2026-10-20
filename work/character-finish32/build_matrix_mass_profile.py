import json,numpy as np,time
from pathlib import Path
from mathutils import Vector
w=Path('work/character-finish32');data=json.loads((w/'refined/poses/male_intro.json').read_text());b=data['parts'][0];t=next(p for p in data['parts'] if p['name']=='Kit_Top');P=np.array(t['vertices']).reshape(-1,3);N=np.array(t['normals']).reshape(-1,3);WI=np.array(t['indices']).reshape(-1,4);W=np.array(t['weights']).reshape(-1,4);nv=len(P);binds=np.array(b['bindposes']).reshape(-1,4,4);rest=dict(zip(b['bones'],np.linalg.inv(binds)[:,:3,3]));normalScale=.02
def smooth(a,z,x):
 u=np.clip((x-a)/(z-a),0,1);return u*u*(3-2*u)
mass=(W*np.isin(WI,[t['bones'].index(n) for n in ['LeftUpperArm','RightUpperArm']])).sum(1);field=smooth(.15,.40,mass);channels=[];controlWeights=[]
for bone,name in enumerate(t['bones']):
 weights=(W*(WI==bone)).sum(1)
 if weights.max()<1e-7 or name=='Chest':continue
 if name in ['LeftUpperArm','RightUpperArm']:
  channels.extend([name,'Swing_'+name]);controlWeights.extend([weights*(1-field),weights*field])
 else:channels.append(name);controlWeights.append(weights)
B=[];controls=[]
for name,weights in zip(channels,controlWeights):
 for row in range(3):
  for col in range(4):
   dp=np.zeros_like(P);dn=np.zeros_like(N);dp[:,row]=weights*(P[:,col] if col<3 else 1)
   if col<3:dn[:,row]=weights*N[:,col]*normalScale
   B.append(np.concatenate([dp.ravel(),dn.ravel()]));controls.append({'bone':name,'row':row,'column':col})
B=np.array(B);print('BASIS',B.shape,'MB',B.nbytes/1e6,flush=True);files=sorted((w/'twist-motion-data/matrices').glob('*.json'))+sorted((w/'collision-poses/matrices').glob('*.json'));C=[]
for f in files:
 d=json.loads(f.read_text());actual=dict(zip(b['bones'],np.array(d['parts'][0]['skinMatrices']).reshape(-1,4,4)));invChest=np.linalg.inv(actual['Chest']);allMatrices={name:m for name,m in actual.items()}
 for side in ['Left','Right']:
  name=side+'UpperArm';a=rest[name];axis=rest[side+'LowerArm']-a;axis/=np.linalg.norm(axis);parent=actual[side+'Shoulder'][:3,:3];R=np.array(Vector(parent@axis).rotation_difference(Vector(actual[name][:3,:3]@axis)).to_matrix())@parent;m=actual[name].copy();m[:3,:3]=R;m[:3,3]=actual[name][:3,:3]@a+actual[name][:3,3]-R@a;allMatrices['Swing_'+name]=m
 relative={name:invChest@allMatrices[name] for name in channels};C.append([relative[a['bone']][a['row'],a['column']]-(1 if a['row']==a['column'] else 0) for a in controls])
C=np.array(C);cov=C.T@C/len(C);vals,U=np.linalg.eigh(cov);L=(np.sqrt(np.maximum(vals,0))[:,None]*U.T);T=L@B;del L;gram=T@T.T;vals,U=np.linalg.eigh(gram);order=np.argsort(-vals);vals=vals[order];U=U[:,order];keep=vals>1e-14;V=(U[:,keep].T@T)/np.sqrt(vals[keep])[:,None];del T;projection=B@V.T;coeff=C@projection;residual=(C@B).astype(np.float32);chosen=None;metrics=[]
for rank in range(1,len(V)+1):
 for i in range(0,len(C),16):residual[i:i+16]-=(coeff[i:i+16,rank-1,None]*V[rank-1]).astype(np.float32)
 if rank not in [48,60,72,80,84,88,92,96,120,len(V)]:continue
 pos=float(np.linalg.norm(residual[:,:nv*3].reshape(-1,nv,3),axis=2).max());normal=float(np.linalg.norm(residual[:,nv*3:].reshape(-1,nv,3),axis=2).max()/normalScale);row={'shapes':rank,'maxPositionMm':pos*1000,'maxNormalVectorError':normal};metrics.append(row);print('RANK',row,flush=True)
 if pos<=.0005 and normal<=.035:chosen=rank;break
if chosen is None:chosen=len(V)
# Keep coefficients in a moderate range; the paired basis and linear map are rescaled together.
scale=np.maximum(np.abs(coeff[:,:chosen]).max(0)*1.15,.01);shapes=V[:chosen]*scale[:,None];map=(projection[:,:chosen]/scale).T;anchors=[]
for k in range(chosen):
 anchors.append({'shape':f'Matrix{k:03d}','deltas':np.round(shapes[k,:nv*3],8).tolist(),'normalDeltas':np.round(shapes[k,nv*3:]/normalScale,8).tolist()})
profile={'vertexCount':nv,'vertices':P.ravel().tolist(),'normals':N.ravel().tolist(),'controls':controls,'projection':np.round(map.ravel(),10).tolist(),'anchors':anchors};out=w/'matrix-mass-profile.json';out.write_text(json.dumps(profile,separators=(',',':')));report={'sourceVertices':nv,'samples':len(C),'controls':len(controls),'rank':chosen,'validation':metrics,'bytes':out.stat().st_size,'normalScale':normalScale,'method':'Current bone affine coefficients, fixed Chest-bound garment morph basis; no nearest-pose interpolation.'};(w/'matrix-mass-profile-report.json').write_text(json.dumps(report,indent=2));np.savez_compressed(w/'matrix-mass-profile-basis.npz',B=B,C=C,V=V[:chosen],projection=map,scale=scale);print('DONE',report,flush=True)
