import bpy, re, collections
cnt=collections.Counter(); n=collections.Counter()
for o in bpy.context.scene.objects:
    if o.type!='MESH' or o.hide_viewport or o.hide_render: continue
    if any(c.name=="ASSET_LIBRARY" for c in o.users_collection): continue
    me=o.data
    t=sum(len(p.vertices)-2 for p in me.polygons)
    nm=re.sub(r"[._]\d+$","",o.name); nm=re.sub(r"_\d+$","",nm)
    key=o.name.split("_")[0]+"_"+(o.name.split("_")[1] if "_" in o.name else "")
    cnt[key]+=t; n[key]+=1
tot=0
for k,v in cnt.most_common(): print(f"{k:24s} {n[k]:5d} objs {v:8d} tris"); tot+=v
print("TOTAL",tot)
