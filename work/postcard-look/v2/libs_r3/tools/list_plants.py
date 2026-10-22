import sys, collections, bpy
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
c = collections.Counter(); fa = {}
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith("PLANT_"):
        base = o.name.split(".")[0]
        c[(base, o.data.name.split(".")[0])] += 1; fa[(base, o.data.name.split(".")[0])] = len(o.data.polygons)
for k, v in sorted(c.items()): print("PL", k, v, "faces", fa[k])
