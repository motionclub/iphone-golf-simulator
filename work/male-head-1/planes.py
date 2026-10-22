import numpy as np,json
from pathlib import Path
W=Path(__file__).resolve().parent; base=np.load(W/'ears.npy'); c=base.copy(); x,y,z=base.T
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
front=1-smooth(-.143,-.105,y)
bridge=np.exp(-(x/.012)**2-((z-1.574)/.030)**2)
socket=sum(np.exp(-((x-s*.041)/.025)**2-((z-1.584)/.014)**2) for s in [-1,1])
cheek=sum(np.exp(-((x-s*.046)/.026)**2-((z-1.556)/.020)**2) for s in [-1,1])
brow=sum(np.exp(-((x-s*.039)/.029)**2-((z-1.610)/.010)**2) for s in [-1,1])
c[:,1]+=front*(-.011*bridge+.0035*socket-.0035*cheek-.002*brow)
np.save(W/'planes.npy',c)
(W/'planes-edit.json').write_text(json.dumps({'part':'broad facial planes','method':'Depth-only continuous nasal bridge, shallow orbital recesses, brow and cheek volumes on the existing head. No face objects, textures or remesh.','maximum_depth_change_metres':float(abs(c[:,1]-base[:,1]).max()),'X_Z_unchanged':bool(np.array_equal(c[:,[0,2]],base[:,[0,2]]))},indent=2))
