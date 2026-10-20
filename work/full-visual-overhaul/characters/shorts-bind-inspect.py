import bpy,json,os
from pathlib import Path
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH' or not any(x in o.name.lower() for x in ['bottom','body']):continue
 points=[o.matrix_world@v.co for v in o.data.vertices]
 row={'name':o.name,'verts':len(points),'bounds':[[min(v[k] for v in points),max(v[k] for v in points)] for k in range(3)],'matrix':[list(x) for x in o.matrix_world],'bones':len(o.vertex_groups),'modifiers':[(m.name,m.type) for m in o.modifiers]}
 if 'bottom' in o.name.lower():row['vertices']=[list(v) for v in points];row['weights']=[[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in o.data.vertices]
 rows.append(row)
Path(os.environ['SHORTS_INSPECT_OUT']).write_text(json.dumps(rows))
print([(r['name'],r['bounds']) for r in rows])
