"""Raise the female contact stretch without changing joint rotations or marker times."""
from pathlib import Path
import numpy as np
import loco,kin
p=Path(loco.DATA)/'gen_serve_female.npz';z=np.load(p);d={k:z[k] for k in z.files};np.savez_compressed(Path(loco.WORK)/'r3/before_contact_lift_female.npz',**d)
rig=loco.Hero('female').rig;hip=rig.idx['Hips']
for f,lift in [(49,.0075),(50,.015),(51,.015),(52,.015),(53,.010),(54,.003)]:
 b=np.array([kin.quat_to_mat(v) for v in d['quats'][f]]);Q,P=rig.fk(b,d['hips'][f]);frame=Q[rig.parent[hip]]@rig.rel_rot[hip];d['hips'][f]+=frame.T@np.array([0.,0.,lift])
np.savez_compressed(p,**d);print('FEMALE_CONTACT_STRETCH 15 mm, fixed rotations and times')
