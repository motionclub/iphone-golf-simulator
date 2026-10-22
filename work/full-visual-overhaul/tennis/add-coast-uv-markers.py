import bpy
from pathlib import Path
W=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/full-visual-overhaul/tennis')
bpy.ops.wm.open_mainfile(filepath=str(W/'TennisCoast-v3.blend'))
for name,p in [('COAST_SHORE_ORIGIN',(-242.5,-187.5,0)),('COAST_SHORE_U',(-242.5+477.5,-187.5,0)),('COAST_SHORE_V',(-242.5,-187.5+632.5,0))]:
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=p
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(W/'TennisCoast-v3.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,global_scale=1,bake_anim=False,add_leaf_bones=False,path_mode='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=str(W/'TennisCoast-v3.blend'))
