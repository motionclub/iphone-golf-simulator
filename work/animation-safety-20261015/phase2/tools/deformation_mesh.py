"""Read FemaleDeformationAudit Unity mesh dumps (rest, posed, triangles, skin)."""
import numpy as np,struct
from pathlib import Path

def read(path):
 with open(path+'.bin','rb') as f:
  n,nt,nb=np.fromfile(f,'i4',3);assert Path(path+'.bin').stat().st_size==12+n*56+nt*4,'Incomplete baked mesh dump';p=np.fromfile(f,'f4',n*3).reshape(-1,3);q=np.fromfile(f,'f4',n*3).reshape(-1,3);tri=np.fromfile(f,'i4',nt).reshape(-1,3);b=np.fromfile(f,np.dtype([('bi','i4',4),('bw','f4',4)]),n)
 names=[s.split(' ',1)[1]for s in Path(path+'-bones.txt').read_text().splitlines()]
 return p,q,tri,b,names
