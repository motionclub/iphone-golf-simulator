"""Append shared layered/chamfered geological modules to the botanical kit."""
import bpy,math,random,json
from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
bpy.ops.wm.open_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/BotanicalKit.blend'))
# Source kit was saved before its proof layout; asset pivots remain at origin.
stone=bpy.data.materials['RESORT_STONE'];rng=random.Random(1007)
for index in range(3):
 verts=[];faces=[];sides=8;rings=5
 for k in range(rings):
  t=k/(rings-1)
  # Offset shelves, chamfered corners and a broad fracture create real shading forms.
  radius=.90+rng.uniform(-.10,.10);shiftx=rng.uniform(-.055,.055);shifty=rng.uniform(-.055,.055)
  for j in range(sides):
   a=j*math.tau/sides+math.pi/8
   x=math.cos(a)*radius*.62+shiftx;y=math.sin(a)*radius*.58+shifty
   z=t+(rng.uniform(-.025,.025) if k not in [0,rings-1] else 0)
   # Middle shelf retracts at the fracture.
   if k==2:x*=.83;y*=.83
   verts.append((x,y,z))
 for k in range(rings-1):
  for j in range(sides):faces.append((k*sides+j,k*sides+(j+1)%sides,(k+1)*sides+(j+1)%sides,(k+1)*sides+j))
 faces.append(tuple(reversed(range(sides))));faces.append(tuple((rings-1)*sides+j for j in range(sides)))
 me=bpy.data.meshes.new(f'CLIFF_BLOCK_{index}');me.from_pydata(verts,[],faces);me.materials.append(stone);me.update();o=bpy.data.objects.new(me.name,me);bpy.context.collection.objects.link(o)
 bevel=o.modifiers.new('Worn ledge bevels','BEVEL');bevel.width=.028;bevel.segments=2;bevel.limit_method='ANGLE';bevel.angle_limit=.3
 weighted=o.modifiers.new('Geology weighted normals','WEIGHTED_NORMAL');weighted.keep_sharp=True
 for polygon in me.polygons:polygon.use_smooth=False
# Save editable source separate from the initial botany build.
bpy.ops.wm.save_as_mainfile(filepath=str(root/'work/full-visual-overhaul/golf/ResortGeologyKit.blend'))
for o in bpy.data.objects:o.select_set(o.type=='MESH')
bpy.ops.export_scene.fbx(filepath=str(root/'Unity/Assets/Resources/Course/Resort/BotanicalKit.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',bake_space_transform=False,bake_anim=False,use_mesh_modifiers=True,path_mode='STRIP')
report={}
deps=bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
 if o.type=='MESH':
  ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();report[o.name]={'triangles':len(me.loop_triangles),'vertices':len(me.vertices)};ev.to_mesh_clear()
(root/'proof/full-visual-overhaul/golf/geology-kit-manifest.json').write_text(json.dumps(report,indent=2))
print('GEOLOGY_KIT_COMPLETE',json.dumps(report))
