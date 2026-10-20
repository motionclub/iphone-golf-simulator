import numpy as np,json
from pathlib import Path
W=Path(__file__).resolve().parent;data=np.load(W/'baseline/mesh.npz');base=np.load(W/'crown.npy');co=base.copy();e=data['edges'];counts=np.bincount(e.ravel(),minlength=len(co))
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
def lap(p):
 v=np.zeros_like(p);np.add.at(v,e[:,0],p[e[:,1]]);np.add.at(v,e[:,1],p[e[:,0]]);return v/np.maximum(counts[:,None],1)-p
x,y,z=base.T
# Depth-only jaw sculpt: retract the lower facial plane and fair the
# under-chin/throat transition. Front/back X/Z outlines remain intact.
front=1-smooth(-.142,-.095,y); jaw=smooth(1.442,1.46,z)*(1-smooth(1.515,1.539,z))
co[:,1]+=.005*front*jaw*(1-smooth(.060,.083,abs(x)))
co[:,0]*=1-.16*front*jaw
neck=smooth(1.39,1.425,z)*(1-smooth(1.51,1.527,z))*(1-smooth(.071,.096,abs(x)))
for _ in range(24):
 d=lap(co);co[:,1]+=.25*neck*d[:,1]
# Fair the front chin volume locally, retaining the posterior jaw angle.
chin=front*jaw*(1-smooth(.065,.080,abs(x)))
for _ in range(8):co+=.20*chin[:,None]*lap(co)
np.save(W/'jaw.npy',co)
assert np.array_equal(co[:,:][data['co'][:,2]<1.38],data['co'][data['co'][:,2]<1.38])
(W/'jaw-edit.json').write_text(json.dumps({'part':'jaw/chin/neck','method':'Existing coordinate depth sculpt: lower-face retraction and positive local depth fairing. X/Z silhouette coordinates retained; nose and upper face excluded; no remesh.','retraction_metres':.005,'changed_vertices_since_crown':int(np.sum(np.any(co!=base,axis=1))),'maximum_displacement_since_crown_metres':float(np.linalg.norm(co-base,axis=1).max())},indent=2))
