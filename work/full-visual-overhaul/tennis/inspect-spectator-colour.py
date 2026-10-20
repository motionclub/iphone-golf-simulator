import bpy,json
from pathlib import Path
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(r/'Unity/Assets/Resources/Tennis/Premium/TennisSpectators.fbx'))
data=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 a=o.data.color_attributes.active_color
 values=sorted(set(tuple(round(v,3) for v in c.color) for c in a.data)) if a else []
 data.append({'name':o.name,'colours':values})
(r/'work/full-visual-overhaul/tennis/spectator-export-colours.json').write_text(json.dumps(data,indent=2));print(json.dumps(data))
