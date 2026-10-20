"""Local chin-volume fairing with boundary falloff; preserve the existing mesh."""
from pathlib import Path
import numpy as np,json
W=Path(__file__).resolve().parent;d=np.load(W/'baseline/mesh.npz');b=d['co'];edges=d['edges'];tri=d['tri'];x,y,z=b.T
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
jaw=smooth(1.427,1.448,z)*(1-smooth(1.508,1.537,z))
jaw*=1-smooth(.065,.099,abs(x));jaw*=1-smooth(-.048,-.006,y)
neck=smooth(1.35,1.377,z)*(1-smooth(1.421,1.451,z))
neck*=1-smooth(.063,.095,abs(x))
weight=np.maximum(jaw,neck)
e0,e1=edges.T;counts=np.bincount(np.r_[e0,e1],minlength=len(b));c=b.copy()
for iteration in range(12):
 avg=np.column_stack([np.bincount(np.r_[e0,e1],weights=np.r_[c[e1,k],c[e0,k]],minlength=len(b))/counts for k in range(3)])
 # Positive fairing removes only local ridges; low coefficient and the
 # spatial falloff limit motion of the plate's lower-face volume.
 c+=(avg-c)*weight[:,None]*.38
 # Retain the calibrated center depth on the front and rear throat.
 center=1-smooth(.002,.012,abs(x));profile=weight*center
 c[:,1]=c[:,1]*(1-profile*.6)+b[:,1]*profile*.6
c[weight==0]=b[weight==0]
def n(co):
 t=co[tri];return np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
scope=np.max(b[tri,2],axis=1)>1.35;rev=int(np.sum(np.einsum('ij,ij->i',n(c),n(b))[scope]<0))
assert rev==0 and np.array_equal(c[z<1.35],b[z<1.35])
np.save(W/'volume.npy',c)
out={'method':'Local positive coordinate fairing of existing chin, under-chin and lower-neck volume with continuous boundary falloffs and central throat depth retention. No remesh or replacement mesh.','baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'changed_vertices':int(np.sum(np.any(c!=b,axis=1))),'maximum_displacement_metres':float(np.max(np.linalg.norm(c-b,axis=1))),'body_below_1_35m_unchanged':True,'head_triangle_normal_reversals':rev}
(W/'volume-edit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
