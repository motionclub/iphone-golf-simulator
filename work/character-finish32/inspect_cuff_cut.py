import bpy,bmesh,numpy as np
from mathutils import Vector
from pathlib import Path
w=Path('work/character-finish32');bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_SleeveFinish.blend'));o=bpy.data.objects['Kit_Top'];rig=next(x for x in bpy.data.objects if x.type=='ARMATURE');bm=bmesh.new();bm.from_mesh(o.data)
for side in ['Left','Right']:
 a=rig.matrix_world@rig.data.bones[side+'UpperArm'].head_local;axis=(rig.matrix_world@rig.data.bones[side+'LowerArm'].head_local-a).normalized();cut=a+axis*.115
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=cut,plane_no=axis,clear_inner=False,clear_outer=False)
 delete=[v for v in bm.verts if v.co.x*a.x>0 and abs(v.co.x)>.205 and v.co.z>1.10 and (v.co-cut).dot(axis)>1e-6];bmesh.ops.delete(bm,geom=delete,context='VERTS');edges=[e for e in bm.edges if e.is_boundary and all(abs((v.co-cut).dot(axis))<2e-5 and abs(v.co.x)>.205 and v.co.x*a.x>0 and v.co.z>1.10 for v in e.verts)];adj={}
 for e in edges:
  x,y=e.verts;adj.setdefault(x,set()).add(y);adj.setdefault(y,set()).add(x)
 seen=set();loops=[]
 for v in adj:
  if v in seen:continue
  q=[v];seen.add(v);ids=[]
  while q:
   z=q.pop();ids.append(z)
   for n in adj[z]:
    if n not in seen:seen.add(n);q.append(n)
  loops.append(ids)
 print(side,'removed',len(delete),'boundarydegrees',set(len(v) for v in adj.values()),'loops',[(len(l),min((v.co-cut).length for v in l),max((v.co-cut).length for v in l)) for l in loops],flush=True)
