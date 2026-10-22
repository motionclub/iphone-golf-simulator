import bpy, json
out = {}
for n in ('objects', 'meshes', 'materials', 'collections', 'images', 'cameras', 'lights', 'node_groups', 'textures', 'worlds', 'armatures', 'actions'):
    out[n] = sorted(x.name for x in getattr(bpy.data, n))
ob = bpy.data.objects
out['_obj_info'] = {o.name: dict(type=o.type, parent=o.parent.name if o.parent else None, loc=[round(v, 6) for v in o.location], rot=[round(v, 6) for v in o.rotation_euler],
                                 scale=[round(v, 6) for v in o.scale], verts=len(o.data.vertices) if o.type == 'MESH' else None,
                                 mods=[m.type for m in o.modifiers], vgroups=len(o.vertex_groups), shapekeys=len(o.data.shape_keys.key_blocks) if o.type == 'MESH' and o.data.shape_keys else 0,
                                 hide=o.hide_get() if hasattr(o, 'hide_get') else None) for o in ob}
print('DBJSON' + json.dumps(out))
