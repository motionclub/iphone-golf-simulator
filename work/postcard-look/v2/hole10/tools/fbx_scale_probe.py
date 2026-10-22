import bpy, sys
fbx = sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
vals=[]
for o in bpy.data.objects:
    if o.name.startswith(("ROCK_BASALT_A.003","ROCK_WALL_BASALT_A.012")):
        print("PROBE", o.name, [repr(v) for v in o.scale], [repr(round(v,7)) for v in o.matrix_world.to_scale()])
