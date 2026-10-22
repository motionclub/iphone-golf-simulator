import bpy
for o in bpy.context.scene.objects:
    if o.name.startswith(('LAVA_LIGHT','DRESS_','WATER_')) or o.type=='LIGHT':
        print("OBJ",o.name,o.type,tuple(round(c,1) for c in o.matrix_world.translation),[s.material.name for s in o.material_slots if s.material] if o.type=='MESH' else '')
