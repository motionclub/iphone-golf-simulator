import bpy
from pathlib import Path
p=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/golf-motion-fit/export/Golf_Male_Master.blend')
bpy.ops.wm.open_mainfile(filepath=str(p));o=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));print('GROUPS',[g.name for g in o.vertex_groups]);print('SOURCE',len(o.data.vertices),sum(len(v.groups) for v in o.data.vertices));
for mod in o.modifiers:
 if mod.type=='NODES':mod.show_viewport=False;mod.show_render=False
bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();print('EVAL',len(m.vertices),sum(len(v.groups) for v in m.vertices))
