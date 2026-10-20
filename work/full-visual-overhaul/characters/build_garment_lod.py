"""Create silhouette-preserving match-distance garment meshes, retain close-up construction.
Blender -b --python this.py -- <repo> <Male|Female>
The original source/production meshes are never modified.
"""
import bpy,sys,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(sys.argv[sys.argv.index('--')+1]); sex=sys.argv[sys.argv.index('--')+2]
P=R/'proof/full-visual-overhaul/characters'; P.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/f'work/cloth-overhaul/export/Cloth_{sex}.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='REST'
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.name.endswith('_High'):bpy.data.objects.remove(o,do_unlink=True)
meshes=[o for o in bpy.data.objects if o.type=='MESH']; report=[]
for o in meshes:
 source=o.data.copy();verts=[v.co.copy() for v in source.vertices];polys=[list(p.vertices) for p in source.polygons]
 orig=BVHTree.FromPolygons(verts,polys); before=sum(len(p.vertices)-2 for p in source.polygons)
 # Collapse only as much as a 1.5mm surface envelope permits. Seams/material borders
 # and detached construction remain mesh islands, so collar, placket and laces survive.
 accepted=None
 for ratio in [.42,.55,.68,.82]:
  if accepted is not None:break
  o.data=source.copy(); bpy.context.view_layer.objects.active=o
  mod=o.modifiers.new('MatchDistanceConstruction','DECIMATE');mod.decimate_type='COLLAPSE';mod.ratio=ratio;mod.use_collapse_triangulate=True
  bpy.ops.object.modifier_apply(modifier=mod.name)
  low=BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons])
  # Both directions: large features cannot disappear merely because new vertices
  # happen to remain near the original surface.
  errors=[low.find_nearest(v)[3] for v in verts]+[orig.find_nearest(v.co)[3] for v in o.data.vertices]
  maxerr=max(errors) if errors else 0
  if maxerr<=.0015:
   accepted={'name':o.name,'source_triangles':before,'lod_triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'ratio':ratio,'max_surface_error_mm':maxerr*1000}
 if accepted is None:
  o.data=source;accepted={'name':o.name,'source_triangles':before,'lod_triangles':before,'ratio':1,'max_surface_error_mm':0}
 # Normalize and cap weights only if Blender's collapse interpolated them.
 for v in o.data.vertices:
  weights=sorted([(g.group,g.weight) for g in v.groups if g.weight>.0001],key=lambda x:-x[1])[:4]
  total=sum(w for _,w in weights)
  for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
  for index,w in weights:o.vertex_groups[index].add([v.index],w/total,'REPLACE')
 for f in o.data.polygons:f.use_smooth=True
 report.append(accepted)
for o in bpy.data.objects:o.select_set(False)
for o in meshes+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig
sourcepath=R/f'ArtDir/hero/kit/premium/source/Tennis_{sex}_MatchDistance.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(sourcepath))
fbx=R/f'Unity/Assets/Resources/Tennis/KitsLOD/{sex}.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='STRIP')
res={'sex':sex,'source':str(sourcepath),'fbx':str(fbx),'bone_names':[b.name for b in rig.data.bones],'meshes':report,'source_triangles':sum(r['source_triangles'] for r in report),'lod_triangles':sum(r['lod_triangles'] for r in report),'gates':{'surface_envelope_max_mm':1.5,'Unity_import_bindings':'UNVERIFIED','reference_visual_comparison':'UNVERIFIED','phone_performance':'UNVERIFIED'}}
(P/f'garment-lod-{sex.lower()}.json').write_text(json.dumps(res,indent=2))
print('GARMENT_LOD '+sex+' '+str(res['source_triangles'])+' -> '+str(res['lod_triangles']))
