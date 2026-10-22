from pathlib import Path
import json,numpy as np
R=Path.cwd();W=R/'work/reference-rebuild/garment-weight-transition/mask3';D=R/'proof/reference-rebuild/character-motion-matrices17'
def arr(p,k,n):return np.array(p[k]).reshape(-1,n)
def xf(m,v):return v@m[:3,:3].T+m[:3,3]
def skin(p,v,m):
 ids=arr(p,'indices',4).astype(int);w=arr(p,'weights',4);q=np.zeros_like(v)
 for j in range(4):q+=(np.einsum('nij,nj->ni',m[ids[:,j],:3,:3],v)+m[ids[:,j],:3,3])*w[:,j,None]
 return q
raw=json.loads((D/'poses/female_intro.json').read_text());body,top=raw['parts'][:2];profile=json.loads((R/'Unity/Assets/Resources/Tennis/Correctives/SleeveFit_Female.json').read_text());bt=arr(body,'triangles',3).astype(int);tt=arr(top,'triangles',3).astype(int);mask2=json.loads((W.parent/'mask-cuff2/BodyMask_female-current-matrix-canonical.json').read_text());keep=np.ones(len(bt),bool);keep[mask2['alwaysCoveredFaceIndices']]=False
rest=xf(arr(body,'rendererToRoot',4),arr(body,'vertices',3));bi=arr(body,'indices',4).astype(int);bw=arr(body,'weights',4);names=body['bones'];bind=arr(body,'rendererToRoot',4)[None]@np.linalg.inv(arr(body,'bindposes',16).reshape(-1,4,4));head=(bw*np.isin(bi,[names.index('Head'),names.index('Neck')])).sum(1);arm=(bw*np.isin(bi,[names.index(n) for n in ['LeftUpperArm','RightUpperArm','LeftLowerArm','RightLowerArm']])).sum(1)
facts={}
for side in ['Left','Right']:
 a=bind[names.index(side+'UpperArm'),:3,3];b=bind[names.index(side+'LowerArm'),:3,3];axis=b-a;facts[side]={'t':(rest-a)@axis/(axis@axis),'mass':(bw*np.isin(bi,[names.index(side+'UpperArm'),names.index(side+'Shoulder')])).sum(1)}
def replay(label):
 s=json.loads((D/'matrices'/f'{label}.json').read_text());parts={p['name']:p for p in s['parts']};bpart=parts[body['name']];tpart=parts[top['name']];weights=np.array(tpart['shapeWeights'])/100;sw=np.array([weights[tpart['shapeNames'].index('TailoredSleeve_'+a['shape'])] for a in profile['anchors']]);delta=np.array([a['deltas'] for a in profile['anchors']]).reshape(len(sw),-1,3);bp=xf(arr(bpart,'rendererToRoot',4),skin(body,arr(body,'vertices',3),arr(bpart,'skinMatrices',16).reshape(-1,4,4)));tp=xf(arr(tpart,'rendererToRoot',4),skin(top,arr(profile,'vertices',3)+np.einsum('s,sni->ni',sw,delta),arr(tpart,'skinMatrices',16).reshape(-1,4,4)));return bp,tp

class BVHTree:
 @staticmethod
 def FromPolygons(v,t,all_triangles=True):return np.asarray(v)[np.asarray(t)]
def raycast(tris,ori,di):
 a=tris[:,0];e1=tris[:,1]-a;e2=tris[:,2]-a;h=np.cross(di,e2);det=np.einsum('ni,ni->n',e1,h);valid=det < -1e-10
 inv=np.zeros(len(det));inv[valid]=1/det[valid];s=ori-a;u=np.einsum('ni,ni->n',s,h)*inv;q=np.cross(s,e1);v=q@di*inv;d=np.einsum('ni,ni->n',e2,q)*inv
 valid&=(u>=0)&(v>=0)&(u+v<=1)&(d>0);d[~valid]=np.inf;i=d.argmin()
 return None if not np.isfinite(d[i]) else (int(i),float(d[i]),ori+di*d[i])
cam=np.array([2.4,1.3,4.1]);target=np.array([0,.83,.1]);fw=target-cam;fw/=np.linalg.norm(fw);right=np.cross([0,1,0],fw);right/=np.linalg.norm(right);up=np.cross(fw,right)
# Unity right=X for forward=Z; perspective frame pixels use its camera-local right.
camRight=np.cross([0,1,0],fw);camRight/=np.linalg.norm(camRight);camUp=np.cross(fw,camRight)
def ray(x,y):
 di=fw+camRight*((x+.5-450)/600*np.tan(np.deg2rad(17)))+camUp*((600-y-.5)/600*np.tan(np.deg2rad(17)));return di/np.linalg.norm(di)
def facefacts(f):
 ids=bt[f];v=rest[ids];return {'face':int(f),'vertices':ids.tolist(),'rest':v.tolist(),'armMass':arm[ids].tolist(),'headMass':head[ids].tolist(),'side':{s:{k:val[ids].tolist() for k,val in vals.items()} for s,vals in facts.items()},'weights':[{names[int(n)]:float(w) for n,w in zip(bi[i],bw[i]) if w>1e-5} for i in ids]}
