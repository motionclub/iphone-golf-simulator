import bpy
obs=[o for o in bpy.data.objects if o.type=='MESH']
vis=[o for o in obs if not o.hide_viewport and not o.hide_render and o.visible_get()]
t=lambda L:sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in L)
print("all",len(obs),t(obs),"visible",len(vis),t(vis))
hid=[o.name for o in obs if o not in vis]; print(len(hid),hid[:10])
print("in view-layer collections:", [c.name for c in bpy.data.collections])
