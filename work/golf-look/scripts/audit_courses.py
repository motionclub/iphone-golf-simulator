import bpy,json,hashlib,re
from pathlib import Path
r=Path.cwd();w=r/'work/golf-look';rows=[]
for n in range(7,11):
 p=r/f'blender/hole_{n:02}.blend'; before=hashlib.sha256(p.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(p))
 mats={}; objects=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH' or o.hide_render:continue
  o.data.calc_loop_triangles(); tris=len(o.data.loop_triangles)
  objects.append(dict(name=o.name,tris=tris,slots=len(o.data.materials),instances=o.data.users))
  for m in o.data.materials:
   if not m:continue
   imgs=[dict(name=x.image.name,size=list(x.image.size),path=x.image.filepath) for x in m.node_tree.nodes if x.type=='TEX_IMAGE' and x.image] if m.use_nodes else []
   mats[m.name]=imgs
 row=dict(hole=n,input=str(p.relative_to(r)),sha256=before,source_stable=before==hashlib.sha256(p.read_bytes()).hexdigest(),source_mesh_triangles=sum(o['tris'] for o in objects),renderer_material_slots_upper_bound=sum(o['slots'] for o in objects),not_measured=['visible triangles','GPU draw calls','frame time','shader instructions','skin clipping','shirt L*'],materials=mats,objects=objects)
 rows.append(row)
 print(n,row['source_mesh_triangles'],row['renderer_material_slots_upper_bound'],len(mats),flush=True)
(w/'data/course_mesh_audit.json').write_text(json.dumps(rows,indent=2)+'\n')
