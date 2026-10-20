import bpy,bmesh,json
from pathlib import Path
w=Path('work/character-finish32');bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Refined.blend'));o=bpy.data.objects['Kit_Top'];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();edges=[e for e in bm.edges if e.is_boundary];adj={}
for e in edges:
 a,b=e.verts;adj.setdefault(a.index,set()).add(b.index);adj.setdefault(b.index,set()).add(a.index)
seen=set()
for i in adj:
 if i in seen:continue
 q=[i];seen.add(i);ids=[]
 while q:
  j=q.pop();ids.append(j)
  for k in adj[j]:
   if k not in seen:seen.add(k);q.append(k)
 if len(ids)<10:continue
 p=[bm.verts[j].co for j in ids];print('LOOP',len(ids),'min',[min(v[a] for v in p) for a in range(3)],'max',[max(v[a] for v in p) for a in range(3)],flush=True)
