import bpy,sys,json
from pathlib import Path
s=sys.argv[-1];o=bpy.data.objects['Golf_Polo'];seen=set();adj=[set() for v in o.data.vertices]
for e in o.data.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
rows=[]
for i in range(len(adj)):
 if i in seen:continue
 stack=[i];seen.add(i);ids=[]
 while stack:
  j=stack.pop();ids.append(j)
  for k in adj[j]:
   if k not in seen:seen.add(k);stack.append(k)
 vs=[o.data.vertices[j].co for j in ids];row=dict(count=len(ids),lo=[min(v[a] for v in vs) for a in range(3)],hi=[max(v[a] for v in vs) for a in range(3)],ids=ids);rows.append(row)
p=Path(__file__).resolve().parents[1]/f'data/top_components_{s}.json';p.write_text(json.dumps(rows))
print([(a['count'],a['lo'],a['hi']) for a in rows if a['count']>20],flush=True)
