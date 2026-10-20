"""blender -b <blend> --python state_dump.py -- <out.json> : object-level state used to prove what the merge left alone."""
import bpy, sys, json, hashlib, numpy as np
out = sys.argv[sys.argv.index('--') + 1]
res = {'units': [bpy.context.scene.unit_settings.system, bpy.context.scene.unit_settings.scale_length], 'objects': {}, 'materials': sorted(m.name for m in bpy.data.materials), 'images': sorted(i.name for i in bpy.data.images if i.name not in ('Render Result', 'Viewer Node'))}
for o in bpy.data.objects:
    d = dict(type=o.type, loc=[round(x, 7) for x in o.location], rot=[round(x, 7) for x in o.rotation_euler], scale=[round(x, 7) for x in o.scale], hide_viewport=o.hide_viewport, hide_render=o.hide_render,
             parent=o.parent.name if o.parent else None, collections=[c.name for c in o.users_collection], modifiers=[m.type for m in o.modifiers])
    if o.type == 'MESH':
        me = o.data; n = len(me.vertices); co = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', co)
        d.update(mesh=me.name, verts=n, polys=len(me.polygons), co_sha=hashlib.sha256(co.tobytes()).hexdigest(), materials=[m.name if m else None for m in me.materials], vgroups=len(o.vertex_groups),
                 has_custom_normals=bool(me.has_custom_normals), uv_layers=[u.name for u in me.uv_layers])
        if o.name == 'Hair_F':
            lp = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lp); d['hair_topology_sha'] = hashlib.sha256(lp.tobytes()).hexdigest()
    if o.type == 'LIGHT': d['light'] = [o.data.type, round(o.data.energy, 4)]
    res['objects'][o.name] = d
res['body_validate_changed_something'] = bpy.data.objects['Body_F'].data.validate(verbose=False)
json.dump(res, open(out, 'w'), indent=1); print('STATE_DUMP_OK')
