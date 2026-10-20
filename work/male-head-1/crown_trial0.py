import numpy as np, json
from pathlib import Path
W=Path(__file__).resolve().parent
base=np.load(W/'baseline/mesh.npz')['co']; c=base.copy(); s=1.7/593
row=654-base[:,2]/s; d=base[:,1]/s-8.6606529209622; x=base[:,0]/s
# Project the existing scalp vertices onto a continuous elliptical dome.
# The ellipse follows the frozen bald crown widths, without new topology.
q=np.column_stack((x/32.15,(d+27)/41.6,(96.4-row)/37.2))
norm=np.linalg.norm(q,axis=1); p=q/np.maximum(norm[:,None],1e-9)
target=np.column_stack((p[:,0]*32.15*s,(p[:,1]*41.6-27+8.6606529209622)*s,(654-(96.4-p[:,2]*37.2))*s))
t=np.clip((100-row)/11,0,1); w=t*t*(3-2*t)
c=base+w[:,None]*(target-base)
np.save(W/'crown.npy',c)
(W/'crown-edit.json').write_text(json.dumps({'part':'cranial dome','baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'method':'Existing scalp coordinate projection to a continuous elliptical dome with an 11-pixel forehead transition; no remesh.','changed_vertices':int(np.sum(np.any(c!=base,axis=1))),'maximum_displacement_metres':float(np.linalg.norm(c-base,axis=1).max()),'body_below_1_58m_unchanged':bool(np.array_equal(c[base[:,2]<1.58],base[base[:,2]<1.58]))},indent=2))
