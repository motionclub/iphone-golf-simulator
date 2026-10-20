"""Bake the analytic high construction surface into each updated low shell's tangent UV frame."""
from pathlib import Path
import json,math,sys,numpy as np
from PIL import Image
from golf_surface_field import field
R=Path(__file__).resolve().parents[3];W=R/'work/golf-look';D=W/'maps';D.mkdir(exist_ok=True)
stats=[]
for sex in ['Male','Female']:
 for path in sorted((W/'export/kit_v2').glob(sex+'_Kit_*.npz')):
  piece=path.stem[len(sex)+1:];
  if len(sys.argv)>1 and path.stem!=sys.argv[1]:continue
  data=np.load(path);P=data['P'];UV=data['uv'];CN=data['normal'];tri=data['tri'];tl=data['triloops'];mi=data['material'];roles=data['materials']
  S=2048 if piece=='Kit_Top' else 512 if any(k in piece for k in ['Head','Glove']) else 1024
  pos=np.zeros((S,S,3),np.float32);nrm=pos.copy();tan=pos.copy();bit=pos.copy();aogeom=np.zeros((S,S),np.float32);occupied=np.zeros((S,S),bool);mat=np.zeros((S,S),np.uint8);hits=np.zeros((S,S),np.uint8);zone=np.full((S,S),-1,np.float32);zoneTrim=np.zeros((S,S),np.float32)
  a3=a2=0;ambiguous=0;worst=0
  for ti,(ids,loops,role) in enumerate(zip(tri,tl,mi)):
   v=P[ids];uv=UV[loops];e1=v[1]-v[0];e2=v[2]-v[0];du=uv[1]-uv[0];dv=uv[2]-uv[0];den=du[0]*dv[1]-du[1]*dv[0]
   a3+=np.linalg.norm(np.cross(e1,e2))*.5;a2+=abs(den)*.5
   if abs(den)<1e-10:continue
   t=(e1*dv[1]-e2*du[1])/den;t/=max(np.linalg.norm(t),1e-10)
   b=(-e1*dv[0]+e2*du[0])/den;b/=max(np.linalg.norm(b),1e-10)
   uv=uv*S;mn=np.maximum(np.floor(uv.min(0)).astype(int),0);mx=np.minimum(np.ceil(uv.max(0)).astype(int),S-1)
   if (mx<mn).any():continue
   xx,yy=np.meshgrid(np.arange(mn[0],mx[0]+1)+.5,np.arange(mn[1],mx[1]+1)+.5);dd=den*S*S
   w1=((xx-uv[0,0])*(uv[2,1]-uv[0,1])-(yy-uv[0,1])*(uv[2,0]-uv[0,0]))/dd
   w2=((uv[1,0]-uv[0,0])*(yy-uv[0,1])-(uv[1,1]-uv[0,1])*(xx-uv[0,0]))/dd;w0=1-w1-w2
   inside=(w0>=0)&(w1>=0)&(w2>=0)
   if not inside.any():continue
   yyidx,xxidx=np.where(inside);iy=yyidx+mn[1];ix=xxidx+mn[0];wt=np.stack([w0[inside],w1[inside],w2[inside]],1)
   q=wt@v;nn=wt@CN[loops];nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-9)
   tt=t[None,:]-nn*(nn@t)[:,None];tt/=np.maximum(np.linalg.norm(tt,axis=1)[:,None],1e-9)
   bb=np.cross(nn,tt);bb*=np.sign(bb@b)[:,None]
   prior=hits[iy,ix]>0
   if prior.any():
    dd=np.linalg.norm(pos[iy[prior],ix[prior]]-q[prior],axis=1);ambiguous+=int((dd>.0001).sum());worst=max(worst,float(dd.max()))
   pos[iy,ix]=q;nrm[iy,ix]=nn;tan[iy,ix]=tt;bit[iy,ix]=bb;occupied[iy,ix]=True;mat[iy,ix]=role;hits[iy,ix]+=1
   if "ao" in data:aogeom[iy,ix]=wt@data["ao"][ids]
   zone[iy,ix]=data["fabric"][ti];zoneTrim[iy,ix]=data["trim"][ti]
  stats.append(dict(sex=sex,piece=piece,sharedEdgeHits=int((hits>1).sum()),ambiguousOver100Microns=ambiguous,maxPositionDifferenceMm=worst*1000))
(W/'data/uv_overlap_final.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2),flush=True)
