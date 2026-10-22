import bpy,json
from pathlib import Path
rows=[]
for o in bpy.data.objects:
 if o.type=='MESH':rows.append({'name':o.name,'vertices':len(o.data.vertices),'bounds':[[min(v[k] for v in o.bound_box),max(v[k] for v in o.bound_box)] for k in range(3)],'location':list(o.location),'collections':[c.name for c in o.users_collection],'modifiers':[(m.name,m.type) for m in o.modifiers]})
Path('work/reference-rebuild/bundle-objects.json').write_text(json.dumps(rows,indent=2))
print('\n'.join(str(r) for r in rows if ('Head' in r['name'] or 'Stylized' in r['name'])))
print('TEXTS:',[(t.name,t.as_string()[:1000]) for t in bpy.data.texts])
