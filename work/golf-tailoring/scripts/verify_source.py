import bpy,numpy as np,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(W/'export'/f'Golf_{sex}_Draft.blend'))
 for o in bpy.data.objects:
  if o.type!='MESH' or o.name not in ['Golf_Polo','Golf_Trousers','Golf_PleatedSkort','Golf_Belt']:continue
  p=np.array([v.co[:] for v in o.data.vertices]);ks=o.data.shape_keys.key_blocks
  print(sex,o.name,'basis delta',np.max(np.abs(p-np.array([v.co[:] for v in ks[0].data]))),'bounds',p.min(0),p.max(0),'shapemax',max(np.max(np.linalg.norm(np.array([v.co[:] for v in k.data])-p,axis=1)) for k in ks))
