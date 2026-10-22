import bpy, sys, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith("PLANT_") and o.matrix_world.translation.z>7.0:
        print("HIGH", o.name, o.matrix_world.translation.to_tuple(3))
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith(("PLANT_","ROCK_")) and abs(o.matrix_world.translation.x+60)<8 and abs(o.matrix_world.translation.y-100)<12 and o.matrix_world.translation.z>6.8:
        print("NEAR", o.name, o.matrix_world.translation.to_tuple(2))
