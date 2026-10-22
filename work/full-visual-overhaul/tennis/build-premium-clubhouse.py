"""Preserve the authored resort footprint; add manufactured finish to its house."""
import bpy,bmesh,math,json
from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
source=root/'ArtDir/env_v4/tools/build_env_v4.py'
namespace={'__file__':str(source)}
exec(source.read_text().split('\nreset()\nos.makedirs')[0],namespace)
for key in ['reset','beach_house','paint','add_box','add_cyl']:
 globals()[key]=namespace[key]
reset()
ob=beach_house('TennisClubhouse')
bm=bmesh.new();bm.from_mesh(ob.data)
TEAL,WOOD,STONE,TRIM=5,6,11,12
def box(cell,c,s):paint(bm,cell,add_box(bm,c,s))
# The existing identity / envelope stays intact. Small details have actual depth:
# shutter louvres, window sills, squared column capitals, eave fascia, roof ridge.
for i in range(6):
 x=-9+i*3.6
 for side in [-1,1]:
  sx=x+side*.97
  for row in range(8):box(TEAL,(sx,-5.64,1.4+row*.23),(.50,.055,.045))
 box(STONE,(x,-5.70,1.26),(1.47,.27,.12))
for i in range(5):
 x=-8.2+i*3.35
 for side in [-1,1]:
  for row in range(7):box(TEAL,(x+side*.87,-3.50,5.16+row*.20),(.50,.065,.035))
 box(STONE,(x,-3.62,5.08),(1.29,.27,.10))
for i in range(7):
 x=-10+i*20/6
 box(STONE,(x,-8,1.0),(.54,.54,.24))
 box(TRIM,(x,-8,4.20),(.54,.54,.18))
box(TRIM,(-1.5,-3.83,7.94),(18.23,.12,.23))
box(TRIM,(-1.5,5.63,7.94),(18.23,.12,.23))
box(WOOD,(-1.5,.9,10.19),(9.85,.25,.18))
for i in range(13):box(STONE,(-9.3+i*1.3,-6.82,.79),(.025,2.47,.035))
bm.to_mesh(ob.data);bm.free()
# Split by existing semantic palette UVs so glass, plaster, timber, roof and
# ceramic receive independent physical responses while keeping the atlas intact.
uv=ob.data.uv_layers.active
for i in range(16):
 m=bpy.data.materials.new('CLUBHOUSE_'+str(i).zfill(2));m.diffuse_color=(1,1,1,1)
 ob.data.materials.append(m)
for p in ob.data.polygons:
 u=sum(uv.data[j].uv.x for j in p.loop_indices)/len(p.loop_indices)
 p.material_index=max(0,min(15,int(u*16)))
bpy.context.view_layer.objects.active=ob;ob.select_set(True)
bevel=ob.modifiers.new('Cut edges and rounded joinery','BEVEL');bevel.width=.028
bevel.segments=2;bevel.limit_method='ANGLE';bevel.angle_limit=math.radians(34)
bpy.ops.object.modifier_apply(modifier=bevel.name)
# Flat panels remain flat, the tiny chamfers catch a clean highlight.
for p in ob.data.polygons:p.use_smooth=False
asset=root/'Unity/Assets/Resources/Tennis/Premium';asset.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.fbx(filepath=str(asset/'TennisClubhouse.fbx'),use_selection=True,
 object_types={'MESH'},axis_forward='-Z',axis_up='Y',apply_unit_scale=True,
 apply_scale_options='FBX_SCALE_UNITS',mesh_smooth_type='FACE',bake_anim=False,add_leaf_bones=False)
out=root/'work/full-visual-overhaul/tennis';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'TennisClubhouse.blend'))
ob.data.calc_loop_triangles()
report={'triangles':len(ob.data.loop_triangles),'vertices':len(ob.data.vertices),
 'materials':len(ob.data.materials),'dimensions':list(ob.dimensions),
 'identity':'original EnvV4 beach house; unchanged two-storey and lookout envelope'}
(root/'proof/full-visual-overhaul/tennis/clubhouse-manifest.json').write_text(json.dumps(report,indent=2))
print(report)
