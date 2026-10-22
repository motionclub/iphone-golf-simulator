import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(root/'Unity/Assets/Resources/Tennis/Crowd/crowd_male.fbx'))
for o in bpy.context.scene.objects:
 if o.type=='ARMATURE':print('RIG',o.name,'action',o.animation_data.action.name if o.animation_data and o.animation_data.action else '',len(o.data.bones))
bpy.context.scene.frame_set(20)
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=[ev.matrix_world@p.co for p in me.vertices];lo=Vector(tuple(min(p[a] for p in v) for a in range(3)));hi=Vector(tuple(max(p[a] for p in v) for a in range(3)))
  print('MESH',o.name,len(me.polygons),'bounds',list(lo),list(hi));ev.to_mesh_clear()
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/full-visual-overhaul/tennis/CrowdSourceProbe.blend'))
