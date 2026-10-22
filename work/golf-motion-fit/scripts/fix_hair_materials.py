import bpy
from pathlib import Path
W=Path(__file__).resolve().parents[1]
for o in bpy.data.objects:
 if o.name.startswith('Golf_Hair_') and o.type=='MESH':
  for p in o.data.polygons:p.material_index=0
bpy.ops.wm.save_as_mainfile(filepath=str(W/'export/Golf_Female_Dressed.blend'));print('HAIR_MATERIAL_INDICES_FIXED')
