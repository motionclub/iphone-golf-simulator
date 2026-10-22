import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
from collections import Counter
c=Counter()
for o in bpy.data.objects:
    if o.type!='MESH': c['nonmesh:'+o.type]+=1; continue
    import re
    c[re.sub(r'[_.]?\d+$','',o.name)]+=1
for k,v in sorted(c.items()): print(k,v)
for o in bpy.data.objects:
    if o.type=='MESH' and (o.name.startswith(('WATER_SHELF','WATER_OCEAN','DRESS_PATH','TERRAIN','FAIRWAY','GREEN'))):
        print(o.name, len(o.data.vertices), len(o.data.polygons), [m.name if m else None for m in o.data.materials])
