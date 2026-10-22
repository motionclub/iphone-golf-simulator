import bpy, sys, re, collections
blend = sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.open_mainfile(filepath=blend)
cnt = collections.Counter(); n = collections.Counter()
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    if any(c.name == "ASSET_LIBRARY" for c in o.users_collection) and len(o.users_collection)==1: continue
    me = o.data; me.calc_loop_triangles(); t = len(me.loop_triangles)
    nm = o.name
    key = re.sub(r"\.\d+$", "", nm)
    key = re.sub(r"_\d+(_\d+)?$", "", key)
    grp = key.split("_")[0] + "_" + (key.split("_")[1] if len(key.split("_"))>1 else "")
    cnt[key] += t; n[key] += 1
tot = sum(cnt.values())
for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])[:40]:
    print(f"{k:34s} {n[k]:5d} objs {v:8d} tris")
print("TOTAL", tot)
