import bpy,json
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
rows=[]
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(W.parent/'golf-look/export'/f'Golf_{sex}_Draft.blend'))
 result=[]
 for o in bpy.data.objects:
  if o.type=='MESH' and (o.name.startswith('Golf_') or o.name=='Body_'+sex[0]):
   p=np.array([v.co[:] for v in o.data.vertices]);result.append(dict(name=o.name,n=len(p),min=p.min(0).tolist(),max=p.max(0).tolist(),shapes=[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],groups=[g.name for g in o.vertex_groups],matrix=[list(r) for r in o.matrix_world]))
 rows.append(dict(sex=sex,objects=result))
(W/'data/source_geometry.json').write_text(json.dumps(rows,indent=2))
print('INSPECT_OK')
