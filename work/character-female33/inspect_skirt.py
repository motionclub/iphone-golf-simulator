import bpy,numpy as np,json
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath='work/character-female33/Female_KitBaseline.blend');o=bpy.data.objects['Kit_Bottom'];p=np.array([v.co for v in o.data.vertices]);adj=[set() for _ in p]
for e in o.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();rows=[]
for i in range(len(p)):
 if i in seen:continue
 todo=[i];seen.add(i);ids=[]
 while todo:
  a=todo.pop();ids.append(a)
  for b in adj[a]:
   if b not in seen:seen.add(b);todo.append(b)
 weights={}
 for i in ids:
  for g in o.data.vertices[i].groups:weights[o.vertex_groups[g.group].name]=weights.get(o.vertex_groups[g.group].name,0)+g.weight/len(ids)
 rows.append({'n':len(ids),'min':p[ids].min(0).tolist(),'max':p[ids].max(0).tolist(),'weights':weights})
print(json.dumps(sorted(rows,key=lambda r:-r['n']),indent=2))
