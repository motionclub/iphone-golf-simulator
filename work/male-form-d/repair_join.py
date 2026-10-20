"""Unfold the small front shoulder intersection using existing mesh coordinates."""
from pathlib import Path
import numpy as np,json
W=Path(__file__).parent
d=np.load(W/'baseline/mesh.npz');base=d['co'];e=d['edges'];f=d['faces']
c=np.load(W/'revised_coordinates.npy')
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
count=np.bincount(e.ravel(),minlength=len(c))[:,None]
def lap(c):
    s=np.zeros_like(c);np.add.at(s,e[:,0],c[e[:,1]]);np.add.at(s,e[:,1],c[e[:,0]])
    return s/np.maximum(count,1)-c
w=(1-smooth(.06,.14,abs(abs(c[:,0])-.165)))*(1-smooth(.028,.085,abs(c[:,2]-1.225)))*(1-smooth(-.07,-.025,c[:,1]))
for _ in range(200):c+=.35*w[:,None]*lap(c)
np.save(W/'revised_coordinates.npy',c)
v=c[f];n=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]);m=v.mean(axis=1)
q=(m[:,2]>1.16)&(m[:,2]<1.30)&(abs(m[:,0])<.26)&(m[:,1]<-.065)
report=json.loads((W/'coordinate-edit.json').read_text())
report['front_join_repair']='Positive local Laplacian coordinate fairing to unfold the deltoid/pectoral intersection; topology unchanged.'
report['maximum_displacement_metres']=float(np.linalg.norm(c-base,axis=1).max())
report['front_join_backward_faces']=int(((n[:,1]>0)&q).sum())
(W/'coordinate-edit.json').write_text(json.dumps(report,indent=2))
print('JOIN_REPAIR',report['front_join_backward_faces'])
