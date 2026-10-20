from pathlib import Path
import sys,json,numpy as np
sys.path.insert(0,str(Path('../../work/match-anim-set/scripts').resolve()));import kin
k=kin.Rig(str(Path('../../work/match-anim-set/data/rig_female.json').resolve()));d=json.loads(Path('data/grip_Female_LH.json').read_text())
for side,sd in [('L','Left'),('R','Right')]:
 h=k.idx[sd+'Hand'];A=np.array(d[side]['anchor']);inv=np.linalg.inv(k.Mrest[h]);local=A@inv
 for digit in ['Index','Middle','Thumb']:
  names=[sd+digit+x for x in ['Proximal','Intermediate','Distal']];ids=[k.idx[n] for n in names]
  print(side,digit,'rest handle joints',[(local@np.r_[k.Mrest[i,:3,3],1])[:3].round(3).tolist() for i in ids])
  for closure in [0,60,120,180,240]:
   B=np.tile(np.eye(3),(k.n,1,1))
   for nm,v in d[side]['angles'].items():B[k.idx[nm]]=kin.rx(np.radians(v))
   for i,ratio in zip(ids,[.35,.45,.275]):B[i]=kin.rx(np.radians(closure*ratio))
   Q,P=k.fk(B);print(closure,[(local@np.r_[P[i],1])[:3].round(3).tolist() for i in ids])
