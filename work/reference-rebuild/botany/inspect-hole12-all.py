import bpy,json
from pathlib import Path
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(R/'Unity/Assets/Resources/Course/hole_12.fbx'))
r=[]
for o in bpy.data.objects:
 if o.type=='MESH':
  r.append({'name':o.name,'type':o.type,'position':list(o.matrix_world.translation),'dimensions':list(o.dimensions),'scale':list(o.scale),'materials':[m.name for m in o.data.materials] if o.type=='MESH' else []})
(R/'work/reference-rebuild/botany/hole12-all-renderers.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r))
