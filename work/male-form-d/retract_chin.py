"""Small depth-only lower chin correction; frozen frontal contours preserved."""
from pathlib import Path
import numpy as np,json
W=Path(__file__).parent;d=np.load(W/'baseline/mesh.npz');base=d['co'];e=d['edges'];c=np.load(W/'revised_coordinates.npy')
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
w=smooth(1.431,1.447,c[:,2])*(1-smooth(1.499,1.531,c[:,2]))*(1-smooth(-.137,-.095,c[:,1]))*(1-smooth(.065,.100,abs(c[:,0])))
c[:,1]+=.008*w
count=np.bincount(e.ravel(),minlength=len(c))
for _ in range(24):
    s=np.zeros(len(c));np.add.at(s,e[:,0],c[e[:,1],1]);np.add.at(s,e[:,1],c[e[:,0],1]);c[:,1]+=.20*w*(s/np.maximum(count,1)-c[:,1])
np.save(W/'revised_coordinates.npy',c)
report=json.loads((W/'coordinate-edit.json').read_text());report['final_chin_retraction_metres']=.008;report['final_chin_note']='Depth-only retraction and local fairing of the projecting lower face; no stubble/strap, textures or upper-face revisions.'
report['maximum_displacement_metres']=float(np.linalg.norm(c-base,axis=1).max());(W/'coordinate-edit.json').write_text(json.dumps(report,indent=2))
print('CHIN_DEPTH_CORRECTION',.008)
