import bpy
for n in ('Collider_Racket', 'Racket_Classic', 'Hand_Racket', 'Rig_Hand_R', 'Body_M', 'Body_F', 'Chest_Top'):
    o = bpy.data.objects.get(n)
    if o: print(n, 'type', o.type, 'display', o.display_type, 'hide_vp', o.hide_viewport, 'hide_render', o.hide_render, 'hide_get', o.hide_get(), 'show_in_front', o.show_in_front)
print('collections', {c.name: (c.hide_viewport, c.hide_render) for c in bpy.data.collections})
print('layer collections', {c.name: (c.hide_viewport, c.exclude) for c in bpy.context.view_layer.layer_collection.children})
print('actions', [(a.name, a.use_fake_user) for a in bpy.data.actions])
print('active action', bpy.data.objects['Rig_Hand_R'].animation_data.action.name)
print('materials', sorted(m.name for m in bpy.data.materials if not m.name.startswith('Face_')))
print('orphans: meshes', [m.name for m in bpy.data.meshes if m.users == 0], 'materials', [m.name for m in bpy.data.materials if m.users == 0])
