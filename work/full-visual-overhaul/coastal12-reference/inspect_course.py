import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[3]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/'Unity/Assets/Resources/Course/hole_12.fbx'),use_anim=False)
for o in bpy.data.objects:
 if o.type=='MESH':print(o.name,len(o.data.vertices),[round(v,3) for v in o.location],flush=True)
markers=[{'name':o.name,'at':list(o.matrix_world.translation)} for o in bpy.data.objects if o.name.startswith('PLANT_')]
print('PLANT_MARKERS',len(markers),markers[:5],flush=True)
(R/'work/full-visual-overhaul/coastal12-reference/source-object-markers.json').write_text(json.dumps(markers,indent=2))
