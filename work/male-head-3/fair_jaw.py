"""Local existing-coordinate fairing; keep the calibrated central profile and X/Z."""
from pathlib import Path
import numpy as np,json
W=Path(__file__).resolve().parent;d=np.load(W/'baseline/mesh.npz');b=d['co'];edges=d['edges'];tri=d['tri'];x,y,z=b.T
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
# The center profile is retained; high-frequency depth artifacts on the jaw
# surface are faired with a smooth spatial weight, not projected row by row.
jaw=smooth(1.428,1.453,z)*(1-smooth(1.512,1.540,z))
jaw*=1-smooth(.077,.103,abs(x));jaw*=1-smooth(-.055,-.020,y)
neck=smooth(1.35,1.38,z)*(1-smooth(1.43,1.46,z))
neck*=1-smooth(.060,.089,abs(x))
center=smooth(.009,.027,abs(x))
weight=np.maximum(jaw,neck)*center
e0,e1=edges.T;counts=np.bincount(np.r_[e0,e1],minlength=len(b));c=b.copy()
for _ in range(20):
 avg=np.bincount(np.r_[e0,e1],weights=np.r_[c[e1,1],c[e0,1]],minlength=len(b))/counts
 delta=(avg-c[:,1])*weight*.7
 c[:,1]+=delta
c[weight==0]=b[weight==0]
def n(co):
 t=co[tri];return np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
scope=np.max(b[tri,2],axis=1)>1.35;rev=int(np.sum(np.einsum('ij,ij->i',n(c),n(b))[scope]<0))
assert rev==0 and np.array_equal(c[:,[0,2]],b[:,[0,2]])
np.save(W/'fair.npy',c)
out={'method':'Local depth-only positive coordinate fairing of existing jaw and lower-neck vertices with spatial falloffs; calibrated central profile and every X/Z coordinate retained. No remesh.','baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'changed_vertices':int(np.sum(np.any(c!=b,axis=1))),'maximum_displacement_metres':float(np.max(np.linalg.norm(c-b,axis=1))),'body_below_1_35m_unchanged':bool(np.array_equal(c[z<1.35],b[z<1.35])),'X_Z_coordinates_unchanged':True,'head_triangle_normal_reversals':rev}
(W/'fair-edit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
