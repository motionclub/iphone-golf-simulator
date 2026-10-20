import json,pathlib,sys,numpy as np
R=pathlib.Path.cwd();W=R/'work/reference-rebuild/forehand-pole1';D=R/'proof/reference-rebuild/character-motion-matrices17'
can=json.loads((D/'poses/male_intro.json').read_text())['parts'];sample=json.loads((D/'matrices/male_ForehandOpen_4.json').read_text());profile=json.loads((R/'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_Male.json').read_text())
names=can[0]['bones'];ni={n:i for i,n in enumerate(names)};mat=np.array(sample['parts'][0]['skinMatrices']).reshape(-1,4,4);bind=np.array(can[0]['bindposes']).reshape(-1,4,4);rt=np.array(can[0]['rendererToRoot']).reshape(4,4);bone=rt[None]@mat@np.linalg.inv(bind)
segments=[('Spine','Chest'),('Chest','Neck'),('LeftShoulder','LeftUpperArm'),('LeftUpperArm','LeftLowerArm'),('LeftLowerArm','LeftHand'),('RightShoulder','RightUpperArm'),('RightUpperArm','RightLowerArm'),('RightLowerArm','RightHand')]
def arr(p,k,n):return np.array(p[k]).reshape(-1,n)
def xf(m,v):return v@m[:3,:3].T+m[:3,3]
def smooth(a,b,x):t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def pose(p,b,v):
 ids=arr(p,'indices',4).astype(int);weights=arr(p,'weights',4);rt=np.array(p['rendererToRoot']).reshape(4,4);b=b@np.array(p['bindposes']).reshape(-1,4,4);return np.einsum('nbij,nb,nj->ni',b[ids],weights,np.column_stack([v,np.ones(len(v))]))[:,:3]
def top_pose(b):
 dirs=np.array([b[ni[y],:3,3]-b[ni[x],:3,3] for x,y in segments]);dirs/=np.linalg.norm(dirs,axis=1)[:,None];feat=np.array([dirs[i]@dirs[j] for i in range(8) for j in range(i+1,8)]);dist=np.array([np.mean((feat-np.array(a['feature']))**2) for a in profile['anchors']]);ww=1/np.maximum(dist,1e-8)**2;ww*=(1-smooth(.025,.30,dist.min()))/ww.sum();v=arr(can[1],'vertices',3)+sum(np.array(a['deltas']).reshape(-1,3)*w for a,w in zip(profile['anchors'],ww));return pose(can[1],b,v),ww
S=bone[ni['RightUpperArm'],:3,3];E=bone[ni['RightLowerArm'],:3,3];H=bone[ni['RightHand'],:3,3];axis=(H-S)/np.linalg.norm(H-S)
def swivel(deg):
 angle=np.radians(deg);x,y,z=axis;K=np.array([[0,-z,y],[z,0,-x],[-y,x,0]]);rot=np.eye(3)+np.sin(angle)*K+(1-np.cos(angle))*(K@K);M=np.eye(4);M[:3,:3]=rot;M[:3,3]=S-rot@S;b=bone.copy()
 for name in ['RightUpperArm','RightLowerArm']:b[ni[name]]=M@b[ni[name]]
 return b
body=can[0];bv=arr(body,'vertices',3);br=xf(rt,bv);ids=arr(body,'indices',4).astype(int);weights=arr(body,'weights',4);bt=arr(body,'triangles',3);mask=json.loads((R/'work/reference-rebuild/garment-weight-transition/mask-cuff2/BodyMask_male-current-matrix-canonical.json').read_text());keep=np.ones(len(bt),bool);keep[mask['alwaysCoveredFaceIndices']]=False;bt=bt[keep]
right=(weights*np.isin(ids,[ni['RightLowerArm']])).sum(1);hand=(weights*np.isin(ids,[ni['RightHand']])).sum(1);arm=(right>.75)&(hand<.2)
rows=[]
try:
 from mathutils.bvhtree import BVHTree
 from mathutils import Vector
except:BVHTree=None
for deg in [-90,-75,-60,-45,-30,-15,0,15,30,45,60,75,90]:
 b=swivel(deg);bp=pose(body,b,bv);tp,ww=top_pose(b);tt=arr(can[1],'triangles',3);row={'degrees':deg,'elbowMetres':b[ni['RightLowerArm'],:3,3].tolist(),'wristTranslationMm':float(np.linalg.norm(b[ni['RightHand'],:3,3]-H)*1000),'wristMatrixMaxError':float(np.max(np.abs(b[ni['RightHand']]-bone[ni['RightHand']])))}
 if BVHTree:
  tv=arr(can[1],'vertices',3);tr=xf(np.array(can[1]['rendererToRoot']).reshape(4,4),tv);tn=arr(can[1],'normals',3)@np.array(can[1]['rendererToRoot']).reshape(4,4)[:3,:3].T;outer=(tn[:,0]*tr[:,0]+tn[:,2]*(tr[:,2]-.03))>0;torso=(tr[:,1]<1.2)&(np.abs(tr[:,0])<.23);use=tt[torso[tt].all(1)&outer[tt].all(1)];bvh=BVHTree.FromPolygons([Vector(p) for p in tp],[tuple(t) for t in use],all_triangles=True)
  signs=[]
  for p in bp[arm]:
   hit,n,_,dd=bvh.find_nearest(Vector(p));signed=float((Vector(p)-hit).dot(n));signs.append(signed)
  signs=np.array(signs);row['forearmVerticesInsideTorsoCloth']=int((signs<-.002).sum());row['deepestSignedMm']=float(signs.min()*1000);row['forearmVertexCount']=int(arm.sum())
 rows.append(row);np.savez_compressed(W/f'swivel_{deg}.npz',body=bp,bodyTriangles=bt,top=tp,topTriangles=tt,bones=b,bodyRest=br)
print(json.dumps({'sampleTime':sample['time'],'sourceShoulder':S.tolist(),'sourceElbow':E.tolist(),'sourceWrist':H.tolist(),'rows':rows},indent=2));(W/'analysis.json').write_text(json.dumps(rows,indent=2))
