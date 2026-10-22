import bpy,json,pathlib
R=pathlib.Path(__file__).resolve().parents[3]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/'Unity/Assets/Resources/Course/hole_12.fbx'))
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('TERRAIN'):
  points=[]
  for f in o.data.polygons:
   if o.data.materials[f.material_index].name=='MAT_ROUGH':
    ps=[o.matrix_world@o.data.vertices[i].co for i in f.vertices];points.extend(ps)
  print(o.name,[(min(p[i] for p in points),max(p[i] for p in points)) for i in range(3)])
