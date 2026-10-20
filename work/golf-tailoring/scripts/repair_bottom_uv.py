"""Detach folded submillimetre chart slivers into a padded reserved UV strip."""
from pathlib import Path
import numpy as np,json,sys,math
W=Path(__file__).resolve().parents[1]
def ambiguous(d,S):
 pos=np.zeros((S,S,3),np.float32);owner=np.full((S,S),-1,np.int32);bad=set();hits=0
 for k,(ids,loops) in enumerate(zip(d['tri'],d['triloops'])):
  u=d['uv'][loops]*S;den=np.linalg.det(np.stack([u[1]-u[0],u[2]-u[0]]))
  if abs(den)<1e-9:continue
  lo=np.maximum(np.floor(u.min(0)).astype(int),0);hi=np.minimum(np.ceil(u.max(0)).astype(int),S-1)
  if (hi<lo).any():continue
  x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
  b=((x-u[0,0])*(u[2,1]-u[0,1])-(y-u[0,1])*(u[2,0]-u[0,0]))/den
  c=((u[1,0]-u[0,0])*(y-u[0,1])-(u[1,1]-u[0,1])*(x-u[0,0]))/den;a=1-b-c
  inside=(a>=0)&(b>=0)&(c>=0);yy,xx=np.where(inside);iy=yy+lo[1];ix=xx+lo[0]
  q=np.stack([a[inside],b[inside],c[inside]],1)@d['P'][ids];old=owner[iy,ix];conflict=(old>=0)&(np.linalg.norm(pos[iy,ix]-q,axis=1)>.0001)
  if conflict.any():bad.add(k);bad.update(old[conflict].tolist());hits+=int(conflict.sum())
  pos[iy,ix]=q;owner[iy,ix]=k
 return bad,hits
rows=[]
for sex in ['Male','Female']:
 p=W/f'export/kit_v2/{sex}_Kit_Bottom.npz';d=dict(np.load(p));S=1024;bad,hits=ambiguous(d,S)
 assert len(np.unique(d['triloops']))==d['triloops'].size
 original_hits=hits;detached=0;reserved_total=0
 for iteration in range(8):
  if not bad:break
  shapes=[];density=700
  for k in sorted(bad):
   v=d['P'][d['tri'][k]];x=v[1]-v[0];length=np.linalg.norm(x);x/=max(length,1e-12);e=v[2]-v[0];along=e@x;height=np.sqrt(max(0,e@e-along*along))
   uv=np.array([[0,0],[length,0],[along,height]])*density;uv-=uv.min(0);shapes.append((k,uv))
  max_extent=max((u.max() for _,u in shapes),default=0);cell=math.ceil(max_extent)+14;columns=S//cell;reserve=math.ceil(len(shapes)/max(1,columns))*cell+6
  assert reserve<S*.25,'Unexpectedly large folded-chart area'
  d['uv'][:,1]=d['uv'][:,1]*(1-reserve/S)+reserve/S
  for j,(k,u) in enumerate(shapes):d['uv'][d['triloops'][k]]=(u+np.array([j%columns*cell+7,j//columns*cell+7]))/S
  detached+=len(bad);reserved_total+=reserve;bad,new_hits=ambiguous(d,S)
  print('UV_SLIVER',sex,iteration,'remaining',len(bad),new_hits,flush=True)
 assert not bad,(sex,len(bad),new_hits)
 np.savez_compressed(p,**d);row=dict(sex=sex,detachedTriangles=detached,originalAmbiguousTexels=original_hits,finalAmbiguousTexels=0,reservedPixels=reserved_total,geometryChanged=False);rows.append(row);print(row,flush=True)
(W/'data/uv_sliver_repair.json').write_text(json.dumps(rows,indent=2)+'\n')
