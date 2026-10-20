"""Unfold local hand distortion using corresponding existing thumb vertices."""
from pathlib import Path
import numpy as np,json
W=Path(__file__).resolve().parent;d=np.load(W/'baseline/mesh.npz');b=d['co'];o=np.load(W/'original_coordinates.npy');x,y,z=o.T
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
# The historical point correspondence was checked against the current edges.
# Continue only the distal hands; no other part is reset or replaced.
weight=smooth(.50,.54,abs(x))*(1-smooth(.900,.953,z))*smooth(.745,.770,z)
c=b+(o-b)*weight[:,None]
# Bring the restored narrow thumb mass toward the plate's fuller tip.
thumb=(1-smooth(.594,.615,abs(x)))*smooth(.554,.567,abs(x))
thumb*=smooth(.821,.840,z)*(1-smooth(.885,.908,z))*weight
c[:,0]+=np.sign(x)*thumb*(.008+.18*(abs(x)-.582))
c[:,2]-=.002*thumb
np.save(W/'hands.npy',c)
out={'part':'distal hands / thumb volume','baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'method':'Local existing-coordinate unfolding using verified historical thumb vertex correspondence, continuous wrist falloff and plate-guided thumb placement. Current head, torso, legs and arm depth above wrist retained. No restart, remesh or replacement mesh.','changed_vertices':int(np.sum(np.any(c!=b,axis=1))),'maximum_displacement_metres':float(np.max(np.linalg.norm(c-b,axis=1))),'hand_scope':'Original corresponding vertices with |X|>0.50m and Z<0.953m, fades to zero at wrist; no changes below Z 0.745m.','no_vertices_added_removed':True,'head_unchanged':bool(np.array_equal(c[b[:,2]>1.35],b[b[:,2]>1.35]))}
(W/'hands-edit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
