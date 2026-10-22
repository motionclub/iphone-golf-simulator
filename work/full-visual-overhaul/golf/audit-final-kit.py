import bpy,json
from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.wm.open_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/ResortEvergreenBough.blend'))
report={};deps=bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
 if o.type!='MESH':continue
 evaluated=o.evaluated_get(deps);m=evaluated.to_mesh();m.calc_loop_triangles()
 report[o.name]={'export_triangles':len(m.loop_triangles),'export_vertices':len(m.vertices),'source_vertices':len(o.data.vertices),'materials':[x.name for x in m.materials if x]};evaluated.to_mesh_clear()
(root/'proof/full-visual-overhaul/golf/geology-kit-manifest.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
