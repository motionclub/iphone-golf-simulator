"""Reference-guided rounded jaw depth on existing vertices, not a new mesh."""
from pathlib import Path
import numpy as np,json
W=Path(__file__).resolve().parent;d=np.load(W/'baseline/mesh.npz');b=d['co'];tri=d['tri'];x,y,z=b.T
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
# Front/throat depths and chin height come from the fixed head-detail profile
# calipers, rather than stubble or pixel-by-pixel surface extrusion.
kn=np.array([[1.38,-.075,.060,.003],[1.395,-.0772,.060,.004],[1.41,-.0785,.059,.003],[1.425,-.0847,.058,-.002],[1.44,-.0904,.059,-.007],[1.449,-.108,.061,-.011],[1.455,-.127,.065,-.017],[1.47,-.150,.073,-.032],[1.485,-.147,.078,-.037],[1.50,-.152,.081,-.043],[1.515,-.152,.082,-.045],[1.54,-.160,.086,-.043]])
grid=np.arange(1.35,1.56,.0005);kernel=np.exp(-np.arange(-18,19)**2/(2*6**2));kernel/=kernel.sum()
params=np.column_stack([np.convolve(np.interp(grid,kn[:,0],kn[:,k]),kernel,mode='same') for k in range(1,4)])
f,rx,cy=[np.interp(z,grid,params[:,k]) for k in range(3)]
u=np.clip(abs(x)/rx,0,.98);target=cy+(f-cy)*np.sqrt(1-u*u)
weight=smooth(1.425,1.448,z)*(1-smooth(1.508,1.535,z))
weight*=1-smooth(.072,.093,abs(x));weight*=1-smooth(-.100,-.057,y)
weight*=smooth(.006,.020,abs(x))
c=b.copy();c[:,1]+=weight*.70*(target-y)
# Fair the depth field locally to avoid a change in derivative at its border.
edges=d['edges'];a,e=edges.T;count=np.bincount(np.r_[a,e],minlength=len(b))
for _ in range(4):
 avg=np.bincount(np.r_[a,e],weights=np.r_[c[e,1],c[a,1]],minlength=len(b))/count;c[:,1]+=(avg-c[:,1])*weight*.3
c[weight==0]=b[weight==0]
def n(co):
 t=co[tri];return np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
scope=np.max(b[tri,2],axis=1)>1.35;proposed=c.copy();fraction=1.0
for fraction in [1.0,.75,.5,.375,.25,.125]:
 c=b+(proposed-b)*fraction
 rev=int(np.sum(np.einsum('ij,ij->i',n(c),n(b))[scope]<0))
 if rev==0:break
assert rev==0 and np.array_equal(c[:,[0,2]],b[:,[0,2]])
np.save(W/'loft.npy',c)
out={'method':'Rounded local jaw depth guided by fixed central chin/throat profile calipers; existing vertex coordinates only with continuous falloffs. Central profile and X/Z preserved. No remesh.','baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'accepted_step_fraction':fraction,'changed_vertices':int(np.sum(np.any(c!=b,axis=1))),'maximum_displacement_metres':float(np.max(np.linalg.norm(c-b,axis=1))),'body_below_1_425m_unchanged':True,'X_Z_coordinates_unchanged':True,'head_triangle_normal_reversals':rev}
(W/'loft-edit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
