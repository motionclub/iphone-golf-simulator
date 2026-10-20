"""Read original editable course metadata; never save or export canonical files."""
import bpy,json,math
from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');rows=[]
prefixes=['TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER','CART_PATH','ICE_POOL','ICE_RIVER']
for n in [7,8,9,10,12,13,14,15,16,17,18,19,20,21,22,23]:
 bpy.ops.wm.open_mainfile(filepath=str(root/f'blender/hole_{n:02}.blend'))
 ground=[o for o in bpy.data.objects if o.type=='MESH' and any(o.name.startswith(p) for p in prefixes)]
 changed=[{'mesh':o.name,'keys':list(o.data.shape_keys.key_blocks.keys())} for o in ground if o.data.shape_keys]
 all_keys=[{'mesh':o.name,'keys':list(o.data.shape_keys.key_blocks.keys())} for o in bpy.data.objects if o.type=='MESH' and o.data.shape_keys]
 normals=[]
 for o in ground:
  if not o.name.startswith('TERRAIN'):continue
  centre=sum((o.matrix_world@v.co for v in o.data.vertices),Vector())/len(o.data.vertices) if False else o.matrix_world.translation
  # Relative normal orientation around the whole source island is recorded only
  # as geometry metadata; world transforms can contain several islands.
  vertical=sum(abs(p.normal.z)<.5 for p in o.data.polygons)
  normals.append({'mesh':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'vertical_polygons':vertical})
 rows.append({'hole':n,'ground_mesh_count':len(ground),'ground_shape_keys':changed,'all_shape_keys':all_keys,'terrain_metadata':normals,'ground_importBlendShapes_changes_ground':bool(changed)})
(root/'proof/full-visual-overhaul/golf/source-ground-shapekeys.json').write_text(json.dumps(rows,indent=2));print(json.dumps({'holes':len(rows),'ground_shape_key_holes':[r['hole'] for r in rows if r['ground_shape_keys']],'water_shape_key_holes':[r['hole'] for r in rows if r['all_shape_keys']]},indent=2))
