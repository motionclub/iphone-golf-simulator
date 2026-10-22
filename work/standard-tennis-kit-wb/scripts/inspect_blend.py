import bpy, sys, math
import mathutils
print("=== BLEND:", bpy.data.filepath)
print("Blender", bpy.app.version_string)
sc = bpy.context.scene
print("unit scale", sc.unit_settings.scale_length, sc.unit_settings.system)
for o in sorted(bpy.data.objects, key=lambda o:o.name):
    info = f"{o.name:28s} type={o.type:8s} parent={o.parent.name if o.parent else None} coll={[c.name for c in o.users_collection]}"
    if o.type=='MESH':
        me=o.data
        me.calc_loop_triangles()
        ntri=len(me.loop_triangles)
        vs=[o.matrix_world @ v.co for v in me.vertices]
        if vs:
            mn=[min(v[i] for v in vs) for i in range(3)]
            mx=[max(v[i] for v in vs) for i in range(3)]
        else: mn=mx=[0,0,0]
        info += f" verts={len(me.vertices)} tris={ntri} mats={[m.name if m else None for m in me.materials]} mods={[m.type for m in o.modifiers]}"
        info += f"\n      bbox min={[round(x,4) for x in mn]} max={[round(x,4) for x in mx]}  loc={tuple(round(x,4) for x in o.location)} rot={tuple(round(x,4) for x in o.rotation_euler)} scale={tuple(round(x,4) for x in o.scale)}"
        info += f"\n      shapekeys={[k.name for k in me.shape_keys.key_blocks] if me.shape_keys else None} vgroups={[g.name for g in o.vertex_groups][:10]}"
    print(info)
print("collections:", [c.name for c in bpy.data.collections])
print("materials:", [m.name for m in bpy.data.materials])
print("images:", [i.name for i in bpy.data.images])
