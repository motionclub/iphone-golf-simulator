import bpy, re, collections
c=collections.Counter(); n=collections.Counter()
for ob in bpy.data.objects:
    if ob.type!='MESH' or "ASSET_LIBRARY" in [x.name for x in ob.users_collection] or ob.name not in bpy.context.scene.objects: continue
    ob.data.calc_loop_triangles(); t=len(ob.data.loop_triangles)
    k=re.sub(r"[_.]?\d+$","",ob.name); k=re.sub(r"[_.]?\d+$","",k)
    k="_".join(k.split("_")[:2]) if k.startswith(("ROCK_","PLANT_","DRESS_")) else k
    c[k]+=t; n[k]+=1
tot=sum(c.values())
print("TOTAL",tot)
for k,v in c.most_common(30): print("TRI %-28s %7d  (%d objs)"%(k,v,n[k]))
