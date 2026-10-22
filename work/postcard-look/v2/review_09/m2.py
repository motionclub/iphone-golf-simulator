import bpy, collections
seen={}
for o in bpy.data.objects:
    if o.type!='MESH': continue
    k=o.data.name
    if k in seen: seen[k][1]+=1; continue
    seen[k]=[len(o.data.polygons),1,o.name,[m.name if m else None for m in o.data.materials]]
for k,(f,n,on,mats) in sorted(seen.items(), key=lambda x:-x[1][0])[:30]: print(f,n,k,on,mats[:3])
