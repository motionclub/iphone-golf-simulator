import bpy
rows=[]
for o in bpy.data.objects:
    if o.type!='MESH': continue
    mats=[m.name if m else None for m in o.material_slots and [s.material for s in o.material_slots]]
    d=o.dimensions
    rows.append((o.name,len(o.data.vertices),round(max(d.x,d.y),1),round(d.z,1),mats))
import collections
pref=collections.defaultdict(list)
for r in rows: pref[r[0].split('_')[0]+'_'+(r[0].split('_')[1] if '_' in r[0] else '')].append(r)
for k,v in sorted(pref.items()):
    print(k,len(v),'maxspan',max(x[2] for x in v),'mats',sorted(set(m for x in v for m in x[4] if m)))
print([r for r in rows if r[2]>40][:30])
