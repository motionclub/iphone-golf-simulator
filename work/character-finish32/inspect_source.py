import bpy,json
from pathlib import Path
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(r/'Unity/Assets/Resources/Tennis/KitsFitted/Male.fbx'))
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 m=o.data;adj=[[] for _ in m.vertices]
 for e in m.edges:
  a,b=e.vertices;adj[a].append(b);adj[b].append(a)
 groups=[];seen=set()
 for i in range(len(adj)):
  if i in seen:continue
  ids=[];todo=[i];seen.add(i)
  while todo:
   k=todo.pop();ids.append(k)
   for j in adj[k]:
    if j not in seen:seen.add(j);todo.append(j)
  pts=[o.matrix_world@m.vertices[j].co for j in ids]
  groups.append({'count':len(ids),'lo':[min(p[k] for p in pts) for k in range(3)],'hi':[max(p[k] for p in pts) for k in range(3)],'ids':ids})
 groups.sort(key=lambda g:g['count'],reverse=True)
 rows.append({'name':o.name,'vertices':len(m.vertices),'faces':len(m.polygons),'matrix':[list(x) for x in o.matrix_world],'materials':[s.name for s in m.materials],'components':groups})
(w/'source-inspection.json').write_text(json.dumps(rows))
print(json.dumps([{**row,'components':[{k:v for k,v in g.items() if k!='ids'} for g in row['components'][:20]]} for row in rows],indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Baseline.blend'))
