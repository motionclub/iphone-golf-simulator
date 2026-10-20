from pathlib import Path
import numpy as np,json
W=Path(__file__).resolve().parent;d=np.load(W/'baseline/mesh.npz');b=d['co'];o=np.load(W/'original_coordinates.npy');c=np.load(W/'fit.npy');edges=d['edges'];a,e=edges.T;count=np.bincount(np.r_[a,e],minlength=len(b))
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
weight=smooth(.600,.637,abs(o[:,0]))*(1-smooth(.838,.875,o[:,2]))*smooth(.745,.775,o[:,2])
for _ in range(10):
 avg=np.column_stack([np.bincount(np.r_[a,e],weights=np.r_[c[e,k],c[a,k]],minlength=len(b))/count for k in range(3)])
 c+=(avg-c)*weight[:,None]*.32
np.save(W/'rounded.npy',c)
q=json.loads((W/'fit-edit.json').read_text());q.pop('profiles');q['method']='Distal-hand and thumb unfolding with shared front/back palm/finger contour correction, then local positive coordinate fairing of collapsed distal finger surfaces. Existing mesh only; wrist, head, torso, legs and arm depth above wrist retained.';q['changed_vertices']=int(np.sum(np.any(c!=b,axis=1)));q['maximum_displacement_metres']=float(np.max(np.linalg.norm(c-b,axis=1)));(W/'rounded-edit.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
