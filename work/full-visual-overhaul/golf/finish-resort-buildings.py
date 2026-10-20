"""Secondary resort building craftsmanship, preserving source course meshes and bounds."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector,Matrix
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
report={}
for n in [15,17,20]:
 bpy.ops.wm.open_mainfile(filepath=str(root/f'blender/hole_{n:02}.blend'))
 selected=[];items={}
 for o in bpy.data.objects:
  if o.type!='MESH' or not any(o.name.startswith(p) for p in ['CABIN','FARMHOUSE','WINDMILL','JETTY','BOAT','BRIDGE','FENCE','HOUSE','GATE','TEMPLE','RUIN','STAIR','LIGHTHOUSE','BENCH','SHACK']):continue
  if 'SAIL' in o.name:continue
  me=o.data;bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table()
  wood=next((i for i,m in enumerate(me.materials) if m and m.name=='MAT_WOOD_LIGHT'),None)
  if wood is None:
   material=bpy.data.materials.new('MAT_WOOD_LIGHT');material.diffuse_color=(.49,.34,.19,1);me.materials.append(material);wood=len(me.materials)-1
  candidates=[]
  for f in list(bm.faces):
   name=me.materials[f.material_index].name if f.material_index<len(me.materials) else ''
   if name not in ['MAT_WINDOW','MAT_SLATE']:continue
   if len(f.verts)!=4 or abs(f.normal.z)>.30 or f.calc_area()<.4:continue
   coordinates=[v.co.copy() for v in f.verts];a=(coordinates[1]-coordinates[0]).normalized();b=f.normal.cross(a).normalized()
   center=sum(coordinates,Vector())/4;u=[(p-center).dot(a) for p in coordinates];v=[(p-center).dot(b) for p in coordinates];W=max(u)-min(u);H=max(v)-min(v)
   if max(W,H)>3.6 or min(W,H)<.35:continue
   # Thin reverse faces of the same window cube are excluded by outward-center proximity.
   if any((center-old[0]).length<.30 for old in candidates):continue
   candidates.append((center,a,b,f.normal.copy(),W,H))
  def oriented_box(center,a,b,normal,width,height,depth):
   vs=bmesh.ops.create_cube(bm,size=1)['verts'];ids=set(vs)
   for v in vs:v.co=center+a*v.co.x*width+b*v.co.y*height+normal*v.co.z*depth
   for f in bm.faces:
    if all(v in ids for v in f.verts):f.material_index=wood
  for center,a,b,normal,W,H in candidates:
   center+=normal*.07
   for side in [-1,1]:
    oriented_box(center+a*side*(W*.5+.025),a,b,normal,.13,H+.21,.18)
    oriented_box(center+b*side*(H*.5+.025),a,b,normal,W+.21,.13,.18)
   oriented_box(center,a,b,normal,.065,H,.19)
   oriented_box(center,a,b,normal,W,.065,.19)
  bm.to_mesh(me);bm.free();me.update()
  bevel=o.modifiers.new('Resort crafted edges','BEVEL');bevel.width=.035;bevel.segments=1;bevel.limit_method='ANGLE';bevel.angle_limit=.5
  normal=o.modifiers.new('Resort broad weighted normals','WEIGHTED_NORMAL');normal.keep_sharp=True
  selected.append(o);items[o.name]={'framed_windows':len(candidates),'source_kept_separate':True}
 for o in bpy.data.objects:o.select_set(o in selected)
 if selected:
  bpy.ops.wm.save_as_mainfile(filepath=str(root/f'work/full-visual-overhaul/golf/ResortBuildings_{n:02}.blend'))
  bpy.ops.export_scene.fbx(filepath=str(root/f'Unity/Assets/Resources/Course/Resort/Finish_{n:02}.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=False,use_mesh_modifiers=True,bake_anim=False,path_mode='STRIP')
 report[n]=items
(root/'proof/full-visual-overhaul/golf/building-finish-manifest.json').write_text(json.dumps(report,indent=2));print('BUILDING_FINISH_COMPLETE',json.dumps(report))
