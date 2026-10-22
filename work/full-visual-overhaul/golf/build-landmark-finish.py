"""Separate bevel-finished landmark candidates. Never overwrites source course files."""
import bpy,json
from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
report={}
for n in [7,8,9,10,12,13,14,15,16,17,18,19,20,21,22,23]:
 bpy.ops.wm.open_mainfile(filepath=str(root/f'blender/hole_{n:02}.blend'))
 selected=[];counts={}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  if not any(o.name.startswith(x) for x in ['TEMPLE','RUIN','STAIR','LIGHTHOUSE','BRIDGE','BENCH','FENCE','HOUSE','SHACK','GATE','WINDMILL']):continue
  if 'SAIL' in o.name:continue
  if len(o.data.polygons)>20000:continue
  mod=o.modifiers.new('Resort edge craftsmanship','BEVEL');mod.width=.075 if n==19 else .045;mod.segments=2;mod.limit_method='ANGLE';mod.angle_limit=.60
  mod.profile=.55;mod.affect='EDGES';mod.use_clamp_overlap=True
  normal=o.modifiers.new('Broad surface weighted normals','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=35
  selected.append(o);counts[o.name]={'source_vertices':len(o.data.vertices),'bevel_metres':mod.width}
 for o in bpy.data.objects:o.select_set(o in selected)
 if not selected:report[n]={'assets':0};continue
 bpy.ops.export_scene.fbx(filepath=str(root/f'Unity/Assets/Resources/Course/Resort/Finish_{n:02}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',global_scale=1,bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='OFF',bake_anim=False,path_mode='STRIP')
 bpy.ops.wm.save_as_mainfile(filepath=str(root/f'work/full-visual-overhaul/golf/Finish_{n:02}.blend'))
 report[n]={'assets':len(selected),'objects':counts}
(root/'proof/full-visual-overhaul/golf/landmark-manifest.json').write_text(json.dumps(report,indent=2))
print('LANDMARK_EXPORT_COMPLETE',json.dumps({n:v['assets'] for n,v in report.items()}))
