import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'Unity/Assets/Resources/Course/hole_12.fbx'),use_anim=False)
a=[]
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('TERRAIN'):
  a.append({'name':o.name,'verts':[list(o.matrix_world@v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'slots':[p.material_index for p in o.data.polygons],'materials':[m.name for m in o.data.materials]})
print('FBX_TERRAINS',[(o['name'],len(o['verts']),o['materials'],[(min(v[i] for v in o['verts']),max(v[i] for v in o['verts'])) for i in range(3)]) for o in a],flush=True)
(R/'work/full-visual-overhaul/coastal12-cliff-replacement/live_fbx_meshes.json').write_text(json.dumps(a))
