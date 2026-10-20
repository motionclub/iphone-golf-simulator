import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(root/'Unity/Assets/Resources/Tennis/TropicalV3/TropicalTennisResort.fbx'))
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH': continue
 p=[o.matrix_world@Vector(c) for c in o.bound_box]
 o.data.calc_loop_triangles()
 rows.append({'name':o.name,'materials':[m.name for m in o.data.materials if m],'tris':len(o.data.loop_triangles),'min':[min(q[i] for q in p) for i in range(3)],'max':[max(q[i] for q in p) for i in range(3)]})
(root/'work/full-visual-overhaul/tennis/arena_objects.json').write_text(json.dumps(rows,indent=2))
print('Imported objects',len(rows))
