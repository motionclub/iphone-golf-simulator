"""Local lower-face coordinate sculpt; retain existing projected support points."""
from pathlib import Path
import numpy as np,json
W=Path(__file__).resolve().parent;d=np.load(W/'baseline/mesh.npz');b=d['co'];edges=d['edges'];tri=d['tri'];x,y,z=b.T
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
# The frozen head-detail profile and existing outline constrain this local edit.
# No vertex/face replacement. Volume below the chin is allowed to relax only
# inside the front/back support envelope; projected boundary X/Z remain fixed.
jaw=smooth(1.426,1.448,z)*(1-smooth(1.505,1.536,z))*(1-smooth(-.045,-.008,y))
neck=smooth(1.350,1.378,z)*(1-smooth(1.428,1.450,z))
rx=np.interp(z,[1.35,1.38,1.405,1.425,1.44,1.465,1.49,1.515,1.54],[.110,.100,.096,.082,.076,.075,.082,.091,.098])
support=1-smooth(.62,.84,abs(x)/rx)
weight=np.maximum(jaw,neck)*(1-smooth(.073,.097,abs(x)))
e0,e1=edges.T;counts=np.bincount(np.r_[e0,e1],minlength=len(b));c=b.copy()
for _ in range(24):
 avg=np.column_stack([np.bincount(np.r_[e0,e1],weights=np.r_[c[e1,k],c[e0,k]],minlength=len(b))/counts for k in range(3)])
 delta=(avg-c)*weight[:,None]*.28
 delta[:,[0,2]]*=support[:,None]
 # Keep the calibrated center profile while relaxing off-centre jaw ripples.
 delta[:,1]*=smooth(.004,.016,abs(x))
 c+=delta
c[weight==0]=b[weight==0]
def normals(co):
 t=co[tri];return np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
base_n=normals(b);p=c.copy()
for fraction in [1,.85,.7,.55,.4,.25]:
 c=b+(p-b)*fraction
 rev=int(np.sum(np.einsum('ij,ij->i',base_n,normals(c))<0))
 if not rev:break
assert rev==0
np.save(W/'fair.npy',c)
np.save(W/'scope.npy',weight>0)
q={'method':'Local lower-face/neck existing-coordinate fairing with projected support preservation and central profile depth retained; no remesh.','baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'accepted_step_fraction':fraction,'changed_vertices':int(np.sum(np.any(c!=b,axis=1))),'maximum_displacement_metres':float(np.max(np.linalg.norm(c-b,axis=1))),'triangle_normal_reversals':rev,'body_below_1_35m_unchanged':bool(np.array_equal(c[z<=1.35],b[z<=1.35]))}
(W/'fair-edit.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
