import bpy
from mathutils import Vector
o=bpy.data.objects['Golf_Polo'];adj=[[] for v in o.data.vertices]
for e in o.data.edges:a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set()
for start in range(len(adj)):
 if start in seen:continue
 ids=[];todo=[start];seen.add(start)
 while todo:
  i=todo.pop();ids.append(i)
  for j in adj[i]:
   if j not in seen:seen.add(j);todo.append(j)
 center=sum((o.data.vertices[i].co for i in ids),Vector())/len(ids)
 print('COMPONENT',len(ids),tuple(center),'contains_worst',7555 in ids,7703 in ids,flush=True)
