import bpy,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(W/'export'/f'Golf_{sex}_Draft.blend'))
 for o in bpy.data.objects:
  if o.type=='MESH' and o.name.startswith(('Golf_Trousers','Golf_Seat','Golf_Pocket','Golf_Pleated','Golf_Inner')):
   p=[v.co for v in o.data.vertices];print('BOTTOM',sex,o.name,len(p),len(o.data.polygons),[round(min(v[i] for v in p),4) for i in range(3)],[round(max(v[i] for v in p),4) for i in range(3)],'shapes',len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0,flush=True)
