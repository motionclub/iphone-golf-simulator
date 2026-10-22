import bpy,numpy as np
c=bpy.data.collections.get("ASSET_LIBRARY")
print("LIB", [ (o.name,o.data.name if o.data else None) for o in c.all_objects][:40] if c else None)
import collections
cnt=collections.Counter()
for o in bpy.data.objects:
    if o.type=="MESH" and o.name.startswith("ROCK_"): cnt[o.name.split(".")[0]+"|"+o.data.name.split(".")[0]]+=1
print("ROCKS", dict(list(cnt.items())[:30]))
