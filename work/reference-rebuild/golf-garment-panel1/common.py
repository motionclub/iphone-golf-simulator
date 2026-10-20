from pathlib import Path
import json
import numpy as np
R=Path.cwd();W=R/'work/reference-rebuild/golf-garment-panel1';D=R/'proof/reference-rebuild/golf-cloth-control16'
UNITS=1.0936
SEGMENTS=[('Spine','Chest'),('Chest','Neck'),('LeftShoulder','LeftUpperArm'),('LeftUpperArm','LeftLowerArm'),('LeftLowerArm','LeftHand'),('RightShoulder','RightUpperArm'),('RightUpperArm','RightLowerArm'),('RightLowerArm','RightHand')]
def arr(p,k,n):return np.asarray(p[k],float).reshape(-1,n)
def xf(m,p):return p@m[:3,:3].T+m[:3,3]
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
def dense(p,names):
 indices=arr(p,'indices',4).astype(int);weights=arr(p,'weights',4);d=np.zeros((len(weights),len(names)))
 for k in range(4):
  ix=np.array([names.index(p['bones'][j]) for j in indices[:,k]])
  d[np.arange(len(weights)),ix]+=weights[:,k]
 return d
def skin(p,positions,ids=None,weights=None,matrices=None):
 ids=arr(p,'indices',4).astype(int) if ids is None else ids;weights=arr(p,'weights',4) if weights is None else weights
 matrices=arr(p,'skinMatrices',16).reshape(-1,4,4) if matrices is None else matrices
 result=np.zeros_like(positions)
 for k in range(4):
  m=matrices[ids[:,k]];result+=(np.einsum('nij,nj->ni',m[:,:3,:3],positions)+m[:,:3,3])*weights[:,k,None]
 return result
def skin_normals(p,n,ids=None,weights=None,matrices=None):
 ids=arr(p,'indices',4).astype(int) if ids is None else ids;weights=arr(p,'weights',4) if weights is None else weights
 matrices=arr(p,'skinMatrices',16).reshape(-1,4,4) if matrices is None else matrices
 result=np.zeros_like(n)
 for k in range(4):result+=np.einsum('nij,nj->ni',matrices[ids[:,k],:3,:3],n)*weights[:,k,None]
 return result/np.maximum(np.linalg.norm(result,axis=1)[:,None],1e-12)
def top_weights(sex,part,matrices=None):
 m=arr(part,'skinMatrices',16).reshape(-1,4,4) if matrices is None else matrices
 binds=arr(part,'bindposes',16).reshape(-1,4,4);bone=m@np.linalg.inv(binds);names=part['bones']
 directions=[]
 for a,b in SEGMENTS:
  v=bone[names.index(b),:3,3]-bone[names.index(a),:3,3];directions.append(v/np.linalg.norm(v))
 features=np.array([directions[i]@directions[j] for i in range(8) for j in range(i+1,8)])
 profile=json.loads((R/f'Unity/Assets/Resources/Golf/Correctives/{sex}.json').read_text())
 dist=np.array([np.mean((features-np.array(a['feature']))**2) for a in profile['anchors']]);weights=1/np.maximum(dist,1e-10)**2;weights/=weights.sum()
 byname={a['shape']:w for a,w in zip(profile['anchors'],weights)}
 raw=np.load(W/f'{sex}_production-top.npz');return np.array([byname[str(n)] for n in raw['shapeNames']])
def source(sex):
 snap=json.loads((D/f'poses/{sex.lower()}_Driver_top.json').read_text());body,top=snap['parts'][:2]
 raw=dict(np.load(W/f'{sex}_production-top.npz'))
 assert len(raw['vertices'])==len(arr(top,'vertices',3));assert np.array_equal(raw['triangles'],arr(top,'triangles',3))
 return body,top,raw
def geom(p,tri):
 area=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]])
 normals=np.zeros_like(p)
 for k in range(3):np.add.at(normals,tri[:,k],area)
 return normals/np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12),area
def bary(p,tri):
 a,b,c=tri;v0=b-a;v1=c-a;v2=p-a;d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1;den=d00*d11-d01*d01
 if abs(den)<1e-18:return np.array([1.,0,0])
 v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;q=np.maximum([1-v-w,v,w],0);return q/q.sum()
