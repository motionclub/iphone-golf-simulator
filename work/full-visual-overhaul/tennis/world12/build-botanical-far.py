import bpy,json
from pathlib import Path
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=R/'work/full-visual-overhaul/tennis/world12'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'Unity/Assets/Resources/Course/Resort/BotanicalKit.fbx'))
keep={'SHRUB_0':.19,'SHRUB_1':.19,'BUSH_BROAD':.23,'FERN':.36,'FLOWER_CORAL':.35}
report={}
for o in list(bpy.context.scene.objects):
 if o.type!='MESH' or o.name not in keep:bpy.data.objects.remove(o,do_unlink=True);continue
 bpy.context.view_layer.objects.active=o;o.select_set(True);o.data.calc_loop_triangles();before=len(o.data.loop_triangles)
 original_bounds=[list(v) for v in o.bound_box]
 modifier=o.modifiers.new('Distant sporting botanical silhouette','DECIMATE');modifier.ratio=keep[o.name];modifier.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=modifier.name)
 name=o.name;o.name=name+'_FAR';o.data.name=o.name
 o.data.calc_loop_triangles();report[o.name]={'source_triangles':before,'far_triangles':len(o.data.loop_triangles),'source_bounds':original_bounds,'far_bounds':[list(v) for v in o.bound_box],'palette':[m.name for m in o.data.materials]}
 o.select_set(False)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath=str(W/'TennisUnderstoryFar.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=False,add_leaf_bones=False,path_mode='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=str(W/'TennisUnderstoryFar.blend'));(W/'understory-lod-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('UNDERSTORY_FAR_COMPLETE',json.dumps({k:(v['source_triangles'],v['far_triangles']) for k,v in report.items()}))
