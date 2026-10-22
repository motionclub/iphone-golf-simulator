import bpy,numpy as np
bpy.ops.wm.open_mainfile(filepath='work/character-female33/Female_Baseline.blend');o=bpy.data.objects['Kit_Top'];P=np.array([v.co for v in o.data.vertices]);adj=[set() for _ in P]
for e in o.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();components=[]
for i in range(len(P)):
 if i in seen:continue
 todo=[i];seen.add(i);ids=[]
 while todo:
  a=todo.pop();ids.append(a)
  for b in adj[a]:
   if b not in seen:seen.add(b);todo.append(b)
 components.append(ids)
for ids in sorted(components,key=len,reverse=True):print(len(ids),P[ids].min(0),P[ids].max(0))
