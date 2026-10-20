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
 for part in ['Top','Bottom','Shoe_L','Shoe_R']:
  d=dict(np.load(W/f'export/kit_v2/{sex}_Kit_{part}.npz'));S=2048 if part=='Top' else 1024
  bad,hits=ambiguous(d,S);rows.append(dict(sex=sex,part=part,ambiguousTexels=hits,triangles=len(bad)))
  print(rows[-1],flush=True)
(W/'data/uv_check.json').write_text(json.dumps(rows,indent=2))
assert all(r['ambiguousTexels']==0 for r in rows)
