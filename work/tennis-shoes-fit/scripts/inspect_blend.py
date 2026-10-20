import bpy, sys, json, hashlib
import numpy as np
out = []
print("FILE", bpy.data.filepath)
print("collections:")
for c in bpy.data.collections:
    print("  ", c.name, "objs:", [o.name for o in c.objects][:40], "hide_viewport", c.hide_viewport, "hide_render", c.hide_render)
print("scene collection objs:", [o.name for o in bpy.context.scene.collection.objects])
print("objects:")
for o in bpy.data.objects:
    d = o.data
    nv = len(d.vertices) if o.type == 'MESH' else None
    nt = sum(len(p.vertices) - 2 for p in d.polygons) if o.type == 'MESH' else None
    mats = [m.name if m else None for m in d.materials] if o.type == 'MESH' else None
    mw = np.array(o.matrix_world)
    print(f"  {o.name:34s} type={o.type:6s} parent={o.parent.name if o.parent else None} ptype={o.parent_type} data={d.name if d else None} nv={nv} nt={nt} mats={mats} hide={o.hide_viewport}/{o.hide_render}/{o.hide_get() if o.name in bpy.context.view_layer.objects else 'NA'}")
    print(f"      loc={tuple(round(x,6) for x in o.location)} rot={tuple(round(x,6) for x in o.rotation_euler)} scale={tuple(round(x,6) for x in o.scale)} world_is_identity={np.allclose(mw, np.eye(4), atol=1e-9)} colls={[c.name for c in o.users_collection]}")
print("materials:", [(m.name, m.users) for m in bpy.data.materials])
print("meshes:", [(m.name, m.users) for m in bpy.data.meshes])
print("images:", [i.name for i in bpy.data.images])
print("custom props scene:", {k: scene_v for k, scene_v in bpy.context.scene.items()} if hasattr(bpy.context.scene, 'items') else None)
for o in bpy.data.objects:
    if len(o.keys()):
        print("  props", o.name, {k: (o[k] if isinstance(o[k], (int, float, str)) else str(o[k])) for k in o.keys()})
