"""Compose after local strip geometry/fairing. No eye-part or rig changes.
The full eye-part retreat is 12mm in runtime, Half only0.7mm. The Half
lid must retain its open corneal clearance rather than receding toward Full.
"""
import numpy as np
from pathlib import Path
O=Path(__file__).resolve().parents[1]
def apply_half_clearance(body,sex):
 prefix=43900 if sex=='Male'else 34366
 original=np.unique(np.load(O/f'{sex.lower()}-lids.npz')['edges'])
 ids=np.r_[original,np.arange(prefix,len(body.data.vertices))]
 basis=body.data.shape_keys.key_blocks['Basis'];half=body.data.shape_keys.key_blocks['Hero_Blink_Half'];changed=0;maximum=0
 for i in ids:
  k=half.data[int(i)];y=min(basis.data[int(i)].co.y,k.co.y);delta=k.co.y-y
  if delta>1e-8:changed+=1;maximum=max(maximum,delta);k.co.y=y
 return {'sex':sex,'halfDepthChanged':changed,'maxForwardMm':maximum*1000,'basisAndFullUnchanged':True,'featuresUnchanged':True}
