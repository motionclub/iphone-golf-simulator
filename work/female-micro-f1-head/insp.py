import bpy, bmesh, json, sys
import numpy as np
print("BLENDER", bpy.app.version_string)
for o in bpy.data.objects:
    d = {"name":o.name,"type":o.type,"parent":o.parent.name if o.parent else None,
         "loc":list(o.location),"rot":list(o.rotation_euler),"scale":list(o.scale),"hide":o.hide_get()}
    if o.type=='MESH':
        me=o.data
        co=np.empty(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
        d.update(verts=len(me.vertices),edges=len(me.edges),faces=len(me.polygons),
          tris=sum(len(p.vertices)-2 for p in me.polygons),
          vgroups=[g.name for g in o.vertex_groups][:60], mods=[m.type for m in o.modifiers],
          bbox_min=[round(float(x),4) for x in co.min(0)], bbox_max=[round(float(x),4) for x in co.max(0)],
          shapekeys=[k.name for k in me.shape_keys.key_blocks] if me.shape_keys else [],
          mats=[m.name if m else None for m in me.materials],
          uv=[u.name for u in me.uv_layers], attrs=[a.name for a in me.attributes])
        mi=np.empty(len(me.polygons),dtype=np.int32); me.polygons.foreach_get('material_index',mi)
        d['faces_per_mat']={ (me.materials[i].name if me.materials[i] else str(i)):int((mi==i).sum()) for i in np.unique(mi)}
    print(json.dumps(d))
print("IMAGES",[ (i.name,i.size[:],i.packed_file is not None) for i in bpy.data.images])
print("MATERIALS",[m.name for m in bpy.data.materials])
print("COLLECTIONS",[c.name for c in bpy.data.collections])
print("UNIT",bpy.context.scene.unit_settings.system, bpy.context.scene.unit_settings.scale_length)
