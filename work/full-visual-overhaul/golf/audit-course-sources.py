import bpy,json
from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
report={}
for n in [7,8,9,10,12,13,14,15,16,17,18,19,20,21,22,23]:
 bpy.ops.wm.open_mainfile(filepath=str(root/f'blender/hole_{n:02}.blend'))
 markers=[o.name for o in bpy.data.objects if o.name.startswith('PLANT_')]
 report[n]={'markers':len(markers),'types':{typ:sum(o.split('_')[2]==typ for o in markers) for typ in ['T','B','R','S']},'tree_objects':[o.name for o in bpy.data.objects if 'TREE' in o.name or 'SHRUB' in o.name],'landmark_objects':[o.name for o in bpy.data.objects if any(x in o.name for x in ['TEMPLE','STAIR','LIGHTHOUSE','LAVA','BASALT','WINDMILL','RUIN'])]}
(root/'proof/full-visual-overhaul/golf/source-catalog.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
