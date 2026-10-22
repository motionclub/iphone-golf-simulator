"""Export the same authored club builder used by golf into editable/native assets.
Run: Blender -b --python <this script>. Geometry is in metres about original grip.
"""
import bpy, json, sys, pathlib
from mathutils import Vector
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'blender/scripts'))
import golf_clubs
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
OUT = ROOT / 'GolfArcade/Unity/CharacterAssets'
SOURCE = ROOT / 'ArtDir/hero/kit/premium/source'
SOURCE.mkdir(parents=True, exist_ok=True)
UNITY = ROOT / 'Unity/Assets/Resources/Golf/Equipment'
UNITY.mkdir(parents=True, exist_ok=True)
FINISHES = {
 'chrome': ((.86,.87,.89),1,.88), 'satin': ((.72,.73,.75),1,.62),
 'gunmetal': ((.30,.31,.33),1,.68), 'carbon': ((.05,.052,.058),0,.70),
 'black': ((.035,.035,.04),0,.45), 'grip': ((.05,.05,.055),0,.15),
 'accent': ((.05,.62,.62),0,.55), 'white': ((.92,.92,.90),0,.5),
 'groove': ((.10,.10,.11),1,.5)
}
def native(v): return [round(v.x,7),round(v.z,7),round(-v.y,7)]
report = []
for c in golf_clubs.CLUBS:
 ob = golf_clubs.build(c); bpy.context.collection.objects.link(ob)
 me = ob.data; me.calc_loop_triangles()
 # A loop vertex preserves sharp split normals at scorelines, sole and crown edges.
 positions=[]; normals=[]; parts=[[] for _ in me.materials]; used={}
 for tri in me.loop_triangles:
  for li in tri.loops:
   if li not in used:
    used[li]=len(positions)//3
    positions.extend(native(me.vertices[me.loops[li].vertex_index].co))
    normals.extend(native(me.corner_normals[li].vector))
   parts[tri.material_index].append(used[li])
 materials=[]
 for mat,indices in zip(me.materials,parts):
  name=mat.name.removeprefix('CLUB '); color,metal,smooth=FINISHES[name]
  materials.append(dict(name=name,color=list(color),metallic=metal,roughness=1-smooth,indices=indices))
 payload=dict(version=1,id=c,units='metres',gripOrigin=[0,0,0],
  shaftAxis=[0,-1,0],buttAxis=[0,1,0],toeAxis=[1,0,0],faceAxis=[0,0,1],
  gripRange=[-.160,.0715],loftDegrees=golf_clubs.LOFT[c],soleY=golf_clubs.SOLE[c],
  source='blender/scripts/golf_clubs.py',positions=positions,normals=normals,materials=materials)
 (OUT/f'NativeGolfEquipment_{c}.json').write_text(json.dumps(payload,separators=(',',':')))
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.fbx(filepath=str(UNITY/(c+'.fbx')),use_selection=True,
  object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',
  axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,add_leaf_bones=False,
  bake_anim=False,path_mode='AUTO')
 report.append(dict(id=c,vertices=len(positions)//3,triangles=len(me.loop_triangles),
  materials=[m['name'] for m in materials],soleY=payload['soleY'],loft=payload['loftDegrees']))
 # Preserve authored root-local space in the source file; spread only by object transform.
 ob.location.x=golf_clubs.CLUBS.index(c)*.30
 for mat in me.materials:
  name=mat.name.removeprefix('CLUB '); color,metal,smooth=FINISHES[name]
  bs=mat.node_tree.nodes.get('Principled BSDF')
  bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal
  bs.inputs['Roughness'].default_value=1-smooth;mat.diffuse_color=(*color,1)
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'Premium_GolfEquipment.blend'))
(ROOT/'proof/full-visual-overhaul/characters/native-equipment-source.json').write_text(json.dumps(dict(axisContract='native (x,y,z) = Blender (x,z,-y); grip origin exact; shaft down -Y, toe +X, face +Z',clubs=report),indent=2))
print('NATIVE_GOLF_EQUIPMENT_SOURCE',json.dumps(report))
