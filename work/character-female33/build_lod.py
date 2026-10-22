import bpy,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-female33'
bpy.ops.wm.open_mainfile(filepath=str(w/'Female_Polo_Fitted.blend'));o=bpy.data.objects['Kit_Top'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');source=o.data.copy();verts=[v.co.copy() for v in source.vertices];faces=[list(f.vertices) for f in source.polygons];original=BVHTree.FromPolygons(verts,faces);before=sum(len(f.vertices)-2 for f in source.polygons)
report=None
for ratio in [.42,.55,.68,.82,1.0]:
 o.data=source.copy();bpy.context.view_layer.objects.active=o
 if ratio<1:
  mod=o.modifiers.new('DistanceSurface','DECIMATE');mod.decimate_type='COLLAPSE';mod.ratio=ratio;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
 low=BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons]);error=max([low.find_nearest(v)[3] for v in verts]+[original.find_nearest(v.co)[3] for v in o.data.vertices])
 if error<=.0015:report={'sourceTriangles':before,'distanceTriangles':sum(len(f.vertices)-2 for f in o.data.polygons),'maximumTwoWayErrorMm':error*1000,'ratio':ratio};break
for v in o.data.vertices:
 weights=sorted([(g.group,g.weight) for g in v.groups if g.weight>.0001],key=lambda x:-x[1])[:4];total=sum(v for _,v in weights)
 if total<=0:raise RuntimeError('Unbound vertex')
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 for i,val in weights:o.vertex_groups[i].add([v.index],val/total,'REPLACE')
for f in o.data.polygons:f.use_smooth=True
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Female_Polo_FittedDistance.blend'))
bpy.ops.export_scene.fbx(filepath=str(w/'FemalePoloDistance.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
(w/'polo-distance-source.json').write_text(json.dumps(report,indent=2));print(report)
