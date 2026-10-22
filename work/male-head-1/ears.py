import numpy as np,json
from pathlib import Path
W=Path(__file__).resolve().parent; data=np.load(W/'baseline/mesh.npz');base=np.load(W/'jaw.npy');co=base.copy();e=data['edges'];counts=np.bincount(e.ravel(),minlength=len(co))
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
def lap(p):
 v=np.zeros_like(p);np.add.at(v,e[:,0],p[e[:,1]]);np.add.at(v,e[:,1],p[e[:,0]]);return v/np.maximum(counts[:,None],1)-p
x,y,z=base.T
# Recess the side ear masses toward the back of the skull. Their locked
# front/back height and widths are retained; the change is entirely depth.
ear=smooth(.060,.106,abs(x))*smooth(1.48,1.505,z)*(1-smooth(1.586,1.606,z))
co[:,1]+=.009*ear
forehead=smooth(1.572,1.596,z)*(1-smooth(1.647,1.665,z))*(1-smooth(.070,.085,abs(x)))
for _ in range(10):co+=.16*forehead[:,None]*lap(co)
for _ in range(16):co[:,1]+=.20*ear*lap(co)[:,1]
ear_round=smooth(.076,.098,abs(x))*smooth(1.485,1.507,z)*(1-smooth(1.576,1.592,z))
for _ in range(18):co+=.22*ear_round[:,None]*lap(co)
np.save(W/'ears.npy',co)
(W/'ears-edit.json').write_text(json.dumps({'part':'ear placement and forehead transition','method':'Existing coordinate depth sculpt and local volume fairing; ear depth moved toward the posterior skull by up to 9 mm with a continuous falloff. Forehead transition and ear volume rounded locally; no remesh.','maximum_ear_depth_shift_metres':.009,'changed_vertices_since_jaw':int(np.sum(np.any(co!=base,axis=1)))},indent=2))
