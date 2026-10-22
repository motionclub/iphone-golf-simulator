import bpy,json,collections
from pathlib import Path
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');res={}
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/golf-motion-fit/export/Golf_{sex}_Master.blend'))
 res[sex]={}
 for o in bpy.data.objects:
  if o.type=='MESH' and o.name.startswith(('Body','Face','Kit_Top')):
   o.data.calc_loop_triangles();counts=collections.Counter(o.data.materials[t.material_index].name for t in o.data.loop_triangles)
   res[sex][o.name]={'roles':dict(counts),'mods':[(m.name,m.type) for m in o.modifiers]}
print(json.dumps(res,indent=2))
