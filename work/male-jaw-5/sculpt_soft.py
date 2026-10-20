from pathlib import Path
import numpy as np,json
W=Path(__file__).resolve().parent;d=np.load(W/'baseline/mesh.npz');b=d['co'];tri=d['tri'];c=np.load(W/'outline.npy');x,y,z=c.T
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
# Raise the side of the existing mandible toward its angle below the ear.
# The reference's chin stays lower than the jaw angle; its stubble is ignored.
weight=smooth(.026,.064,abs(x))*(1-smooth(.077,.091,abs(x)))
weight*=smooth(-.137,-.078,y)*(1-smooth(-.003,.024,y))
weight*=smooth(1.360,1.430,z)*(1-smooth(1.495,1.540,z))
p=c.copy();p[:,2]+=.006*weight
def n(co):
 t=co[tri];return np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
bn=n(b)
for fraction in [1,.85,.7,.55,.4,.25]:
 q=c+(p-c)*fraction;rev=int(np.sum(np.einsum('ij,ij->i',bn,n(q))<0))
 if not rev:break
assert rev==0
np.save(W/'soft.npy',q);np.save(W/'scope.npy',np.load(W/'scope.npy')|(weight>0))
out={'method':'Accepted lower-face profile correction plus reference-guided local mandibular-angle lift on existing vertices with continuous falloffs; no remesh.','baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'angle_step_fraction':fraction,'changed_vertices':int(np.sum(np.any(q!=b,axis=1))),'maximum_displacement_metres':float(np.max(np.linalg.norm(q-b,axis=1))),'triangle_normal_reversals':rev,'body_below_1_35m_unchanged':bool(np.array_equal(q[b[:,2]<=1.35],b[b[:,2]<=1.35]))}
(W/'soft-edit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
