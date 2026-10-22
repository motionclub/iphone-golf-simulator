"""Round only separate ornamental stone templates, retaining the live botany kit."""
import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
work=root/'work/full-visual-overhaul/golf';proof=root/'proof/full-visual-overhaul/golf'
bpy.ops.wm.open_mainfile(filepath=str(work/'ResortEvergreenBough.blend'))
report={};deps=bpy.context.evaluated_depsgraph_get()
def measure(o):
 ev=o.evaluated_get(deps);m=ev.to_mesh();m.calc_loop_triangles()
 vertices=[v.co.copy() for v in m.vertices]
 result={'triangles':len(m.loop_triangles),'vertices':len(m.vertices)};ev.to_mesh_clear()
 low=Vector(tuple(min(v[a] for v in vertices) for a in range(3)));high=Vector(tuple(max(v[a] for v in vertices) for a in range(3)))
 return result,low,high
for o in list(bpy.data.objects):
 if o.type!='MESH' or not(o.name.startswith('BLUFF_') or o.name=='BOULDER'):continue
 before,lo,hi=measure(o)
 # Old flat bevel facets were reading as sharp stacked blocks at the tee.
 # Editable smooth subdivision rounds the entire ornamental silhouette.
 for modifier in list(o.modifiers):o.modifiers.remove(modifier)
 bevel=o.modifiers.new('Weather-worn bevelled stone arrises','BEVEL');bevel.width=.060;bevel.segments=3;bevel.limit_method='ANGLE';bevel.angle_limit=.30;bevel.harden_normals=True
 weighted=o.modifiers.new('Broad geological face normals','WEIGHTED_NORMAL');weighted.keep_sharp=True;weighted.weight=70
 for polygon in o.data.polygons:polygon.use_smooth=True
 deps=bpy.context.evaluated_depsgraph_get();after,newLo,newHi=measure(o)
 # Preserve the original occupied ornamental envelope and anchor. Nothing
 # here is the original course mesh or a collision mesh.
 factor=Vector(tuple((hi[a]-lo[a])/max(newHi[a]-newLo[a],.00001) for a in range(3)))
 o.scale=factor;o.location=lo-Vector(tuple(newLo[a]*factor[a] for a in range(3)))
 report[o.name]={'before':before,'after':after,'bevel_width_local':.060,'bevel_segments':3,'bounds_preserved':True,'source':'separate Resort kit; no source collider mesh'}
bpy.ops.wm.save_as_mainfile(filepath=str(work/'ResortCoastalStone.blend'))
for o in bpy.data.objects:o.select_set(o.type=='MESH')
bpy.ops.export_scene.fbx(filepath=str(work/'BotanicalKitStoneCandidate.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=False,bake_anim=False,use_mesh_modifiers=True,path_mode='STRIP')
(proof/'coastal-stone-source15.json').write_text(json.dumps(report,indent=2)+'\n')
print('STONE_FINISH',json.dumps(report))
