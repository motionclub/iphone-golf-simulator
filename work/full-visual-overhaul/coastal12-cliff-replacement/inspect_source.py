import bpy,json
from collections import Counter
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[3]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/hole_12.blend'))
a=[]
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('TERRAIN'):
  print('SOURCE',o.name,'bounds',[(round(min((o.matrix_world@v.co)[i] for v in o.data.vertices),3),round(max((o.matrix_world@v.co)[i] for v in o.data.vertices),3)) for i in range(3)],'verts',len(o.data.vertices),'faces',len(o.data.polygons),'matrix',list(o.matrix_world), 'materials',[m.name for m in o.data.materials],flush=True)
  a.append({'name':o.name,'verts':[list(o.matrix_world@v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'slots':[p.material_index for p in o.data.polygons],'materials':[m.name for m in o.data.materials]})
print('ROOT',[(o.name,list(o.matrix_world)) for o in bpy.data.objects if o.name.startswith('MARKER') or o.name=='HOLE_12_ROOT'],flush=True)
(R/'work/full-visual-overhaul/coastal12-cliff-replacement/source_meshes.json').write_text(json.dumps(a))
