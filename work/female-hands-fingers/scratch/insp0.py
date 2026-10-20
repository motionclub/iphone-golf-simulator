import bpy, numpy as np
print("BLENDER", bpy.app.version_string)
for o in bpy.data.objects:
    print("OBJ", o.name, o.type, tuple(round(x,4) for x in o.location), tuple(round(x,4) for x in o.scale), o.parent.name if o.parent else None)
    if o.type=='MESH':
        me=o.data
        print("  verts",len(me.vertices),"edges",len(me.edges),"polys",len(me.polygons),"loops",len(me.loops))
        print("  attrs",[(a.name,a.domain,a.data_type) for a in me.attributes])
        print("  uv",[u.name for u in me.uv_layers],"mats",[m.name if m else None for m in me.materials])
        print("  vgroups",[g.name for g in o.vertex_groups][:40], len(o.vertex_groups))
        print("  mods",[m.type for m in o.modifiers], "shapekeys", me.shape_keys)
        lt=np.zeros(len(me.polygons),np.int32); me.polygons.foreach_get('loop_total',lt)
        print("  sizes",{int(k):int(v) for k,v in zip(*np.unique(lt,return_counts=True))})
        print("  has_custom_normals", me.has_custom_normals)
print("collections",[c.name for c in bpy.data.collections])
print("armatures",[a.name for a in bpy.data.armatures])
