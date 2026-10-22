import bpy, collections, re
c=collections.Counter()
for o in bpy.data.objects:
    n=re.sub(r'[._]?\d+$','',o.name)
    n=re.sub(r'\.\d+$','',n)
    c[(o.type,n)]+=1
for k,v in sorted(c.items()): print(k,v)
print(len(bpy.data.objects))
for o in bpy.data.objects:
    if o.type=='MESH' and not o.name.startswith(('PLANT','ROCK_','DRESS')) :
        print(o.name,len(o.data.vertices),[m.name for m in o.data.materials if m],o.users_collection[0].name if o.users_collection else None)
