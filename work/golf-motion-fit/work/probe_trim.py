import bpy
from mathutils import Vector
for o in bpy.data.objects:
 if o.name!='Kit_Top':continue
 adj=[[] for v in o.data.vertices]
 for e in o.data.edges:a,b=e.vertices;adj[a].append(b);adj[b].append(a)
 seen=set()
 for start in range(len(adj)):
  if start in seen:continue
  todo=[start];ids=[];seen.add(start)
  while todo:
   i=todo.pop();ids.append(i)
   for j in adj[i]:
    if j not in seen:seen.add(j);todo.append(j)
  center=sum((o.data.vertices[i].co for i in ids),Vector())/len(ids)
  print('ISLAND',len(ids),tuple(center),min(o.data.vertices[i].co.z for i in ids),max(o.data.vertices[i].co.z for i in ids),flush=True)
