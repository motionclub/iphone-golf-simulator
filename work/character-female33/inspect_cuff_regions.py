import bpy,bmesh,numpy as np,json
from pathlib import Path
from mathutils import Vector
w=Path('work/character-female33');bpy.ops.wm.open_mainfile(filepath=str(w/'Female_Baseline.blend'));o=bpy.data.objects['Kit_Top'];rig=next(x for x in bpy.data.objects if x.type=='ARMATURE');bm=bmesh.new();bm.from_mesh(o.data)
# Keep the existing main garment; collar/trim construction will reuse the male template.
seen=set();components=[]
for v in bm.verts:
 if v in seen:continue
 seen.add(v);q=[v];part=[]
 while q:
  n=q.pop();part.append(n)
  for edge in n.link_edges:
   k=edge.other_vert(n)
   if k not in seen:seen.add(k);q.append(k)
 components.append(part)
main=set(max(components,key=len));bmesh.ops.delete(bm,geom=[v for v in bm.verts if v not in main],context='VERTS')
for side in ['Left','Right']:
 a=rig.matrix_world@rig.data.bones[side+'UpperArm'].head_local;axis=(rig.matrix_world@rig.data.bones[side+'LowerArm'].head_local-a).normalized();cut=a+axis*.105
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=cut,plane_no=axis)
 allowed={v for v in bm.verts if (v.co-cut).dot(axis)>1e-6};seen=set();groups=[]
 for v in allowed:
  if v in seen:continue
  seen.add(v);todo=[v];part=[]
  while todo:
   n=todo.pop();part.append(n)
   for e in n.link_edges:
    k=e.other_vert(n)
    if k in allowed and k not in seen:seen.add(k);todo.append(k)
  groups.append(part)
 rows=[]
 for group in sorted(groups,key=len,reverse=True):
  P=np.array([v.co for v in group]);rows.append({'count':len(P),'min':P.min(0).tolist(),'max':P.max(0).tolist(),'mean':P.mean(0).tolist()})
 print(side,json.dumps(rows),flush=True)
