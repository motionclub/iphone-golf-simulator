import bpy
for o in bpy.data.objects:
 if o.type=='MESH' and not o.hide_render:print(o.name,'tris',len(o.data.polygons),'parent',o.parent.name if o.parent else None,o.parent_bone,'hidevp',o.hide_viewport,'mats',[m.name if m else None for m in o.data.materials],flush=True)
