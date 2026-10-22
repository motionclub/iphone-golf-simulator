import bpy, sys
print("BLENDER", bpy.app.version_string)
for o in bpy.data.objects:
    d = o.data
    info = ''
    if o.type == 'MESH':
        me = d
        info = f'verts={len(me.vertices)} polys={len(me.polygons)} loops={len(me.loops)} uv={[u.name for u in me.uv_layers]} attrs={[a.name for a in me.attributes]} vg={len(o.vertex_groups)} mods={[m.type for m in o.modifiers]} mats={[m.name if m else None for m in me.materials]} shapekeys={[k.name for k in me.shape_keys.key_blocks] if me.shape_keys else None}'
    print(o.name, o.type, tuple(round(x,4) for x in o.location), tuple(round(x,4) for x in o.scale), 'parent=',o.parent.name if o.parent else None, info)
print('collections', [c.name for c in bpy.data.collections])
print('cameras', [c.name for c in bpy.data.cameras], 'lights', [l.name for l in bpy.data.lights])
print('scenes', [(s.name, s.render.engine) for s in bpy.data.scenes])
o = bpy.data.objects.get('Body_M')
if o:
    print('VG names', [g.name for g in o.vertex_groups][:80])
