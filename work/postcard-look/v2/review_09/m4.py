import bpy
for o in bpy.data.objects:
    if o.type=='MESH' and o.matrix_world.translation.length<1e-6 and o.name.startswith(('PLANT','ROCK','DRESS')):
        print(o.name,o.hide_viewport,o.hide_render,o.hide_get() if False else '',[c.name for c in o.users_collection], tuple(o.dimensions))
import numpy as np
print([c.name for c in bpy.data.collections])
