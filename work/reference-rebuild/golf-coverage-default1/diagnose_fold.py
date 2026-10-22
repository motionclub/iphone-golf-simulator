from pathlib import Path
import json,numpy as np,sys
sys.path.insert(0,'work/reference-rebuild/golf-garment-panel1');from common import arr,xf
R=Path.cwd();W=R/'work/reference-rebuild/golf-coverage-default1';S=R/'proof/reference-rebuild/golf-cloth-control16'
def norm(v):return v/np.linalg.norm(v,axis=-1,keepdims=True)
def mesh(p):
 rt=np.array(p['rendererToRoot']).reshape(4,4);v=xf(rt,arr(p,'posedVertices',3));return v,arr(p,'triangles',3).astype(int),rt
s=json.loads((S/'poses/female_Driver_top.json').read_text());body,top=s['parts'][:2];bp,bt,rt=mesh(body);tp,tt,rt=mesh(top)
center=(bp.min(0)+bp.max(0))*.5;cam=center+np.array([2.5,.3,3.8]);forward=norm(center-cam);right=norm(np.cross(np.array([0,1,0]),forward));up=np.cross(forward,right)
# Unity camera view right = cross(up, forward).
def hit(p,t,x,y):
 ray=norm(forward+right*((x/900*2-1)*.75*np.tan(np.deg2rad(17)))+up*((1-y/1200*2)*np.tan(np.deg2rad(17))))
 a=p[t[:,0]];e1=p[t[:,1]]-a;e2=p[t[:,2]]-a;cross=np.cross(ray,e2);det=np.einsum('ij,ij->i',e1,cross);inv=np.divide(1,det,out=np.zeros_like(det),where=abs(det)>1e-9);v=cam-a;u=np.einsum('ij,ij->i',v,cross)*inv;q=np.cross(v,e1);v2=q@ray*inv;dist=np.einsum('ij,ij->i',e2,q)*inv;ok=(u>=0)&(v2>=0)&(u+v2<=1)&(dist>0)&(abs(det)>1e-9);ids=np.where(ok)[0];ids=ids[np.argsort(dist[ids])]
 return [(int(i),float(dist[i]),np.array([1-u[i]-v2[i],u[i],v2[i]]),ray) for i in ids[:4]]
rest=xf(rt,arr(top,'vertices',3));ns=arr(top,'posedNormals',3)@rt[:3,:3].T;rows=[]
for x,y in [(395,455),(400,459),(410,465),(418,472),(390,450),(404,463),(415,460),(385,464),(426,467)]:
 found=hit(tp,tt,x,y);out=[]
 for face,dist,bary,ray in found:
  points=tp[tt[face]];gn=norm(np.cross(points[1]-points[0],points[2]-points[0]));sn=norm((ns[tt[face]]*bary[:,None]).sum(0));out.append(dict(face=face,distance=dist,restCenter=rest[tt[face]].mean(0).tolist(),front=bool(gn@ray<0),geometricVsShadingNormal=float(gn@sn),normalDirection=sn.tolist(),triangle=tt[face].tolist()))
 rows.append(dict(pixel=[x,y],hits=out));print(x,y,out)
(W/'female-driver-fold-rays.json').write_text(json.dumps(rows,indent=2))
