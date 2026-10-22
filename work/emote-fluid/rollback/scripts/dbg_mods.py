import bpy
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        print(ob.name, 'verts', len(ob.data.vertices), 'mods', [(m.type, m.name) for m in ob.modifiers], 'shape keys', [k.name for k in (ob.data.shape_keys.key_blocks if ob.data.shape_keys else [])][:6], 'parent', ob.parent.name if ob.parent else None, 'vgroups', len(ob.vertex_groups))
