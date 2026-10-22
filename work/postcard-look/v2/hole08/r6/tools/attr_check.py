import sys, bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
for nm in ("DRESS_PATH_01","DRESS_PATH_02","ROCK_OUTCROP_A.000","TEE_BOX"):
    me=bpy.data.objects[nm].data
    print("ATTR", nm, sorted(a.name for a in me.attributes), len(me.polygons), [m.name for m in me.materials])
