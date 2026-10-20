"""blender -b <blend> --python inspect_blend.py : list objects/meshes/attributes (read only)"""
import bpy, sys
print("FILE", bpy.data.filepath)
print("scene units", bpy.context.scene.unit_settings.system, bpy.context.scene.unit_settings.scale_length)
for o in bpy.data.objects:
    line = f"OBJ {o.name!r:22} type={o.type:8} parent={o.parent.name if o.parent else None} vis={not o.hide_viewport}/{not o.hide_render} loc={tuple(round(x,4) for x in o.location)} rot={tuple(round(x,4) for x in o.rotation_euler)} scl={tuple(round(x,4) for x in o.scale)}"
    if o.type == 'MESH':
        me = o.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        line += f" | mesh={me.name!r} v={len(me.vertices)} e={len(me.edges)} f={len(me.polygons)} tris={tris} loops={len(me.loops)}"
        line += f" | attrs={[a.name+':'+a.domain+':'+a.data_type for a in me.attributes]}"
        line += f" | uv={[u.name for u in me.uv_layers]} vg={len(o.vertex_groups)} mats={[m.name if m else None for m in me.materials]} mods={[m.type for m in o.modifiers]}"
        line += f" | shapekeys={[k.name for k in me.shape_keys.key_blocks] if me.shape_keys else None}"
    print(line)
print("COLLECTIONS", [(c.name, [o.name for o in c.objects]) for c in bpy.data.collections])
print("MATERIALS", [m.name for m in bpy.data.materials])
print("ARMATURES", [a.name for a in bpy.data.armatures], "IMAGES", [i.name for i in bpy.data.images])
