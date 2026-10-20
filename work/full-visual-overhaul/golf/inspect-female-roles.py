import bpy,json
from pathlib import Path
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');bpy.ops.wm.open_mainfile(filepath=str(R/'work/golf-motion-fit/export/Golf_Female_Master.blend'));o=bpy.data.objects['Body_F'];out={}
for mi,m in enumerate(o.data.materials):
 vs={i for p in o.data.polygons if p.material_index==mi for i in p.vertices};v=[o.matrix_world@o.data.vertices[i].co for i in vs]
 out[m.name]={'min':[min(c[j] for c in v) for j in range(3)],'max':[max(c[j] for c in v) for j in range(3)],'head_polys':sum(1 for p in o.data.polygons if p.material_index==mi and p.center.z>1.4)}
print(json.dumps(out,indent=2))
