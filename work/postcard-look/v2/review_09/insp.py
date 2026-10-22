import bpy, collections, sys
objs=bpy.data.objects
c=collections.Counter()
for o in objs:
    if o.type!='MESH': c['NONMESH_'+o.type]+=1; continue
    import re
    p=re.sub(r'[._]?\d+$','',o.name)
    p=re.sub(r'_\d+','',p)
    c[p[:24]]+=1
for k,v in sorted(c.items()): print(k,v)
print(len(bpy.data.materials),[m.name for m in bpy.data.materials])
for m in bpy.data.materials: print(m.name, m.users)
