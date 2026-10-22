import bpy
sc=bpy.context.scene
so=set(o.name for o in sc.objects)
allo=[o for o in bpy.data.objects]
print("scenes",[s.name for s in bpy.data.scenes],"scene objs",len(so),"data objs",len(allo))
orph=[o for o in allo if o.name not in so]
print("not in scene",len(orph),[o.name for o in orph][:10])
def tris(os): return sum(len(p.vertices)-2 for o in os if o.type=='MESH' for p in o.data.polygons)
print("tris scene",tris([o for o in allo if o.name in so]),"orph",tris(orph))
print("collections",[(c.name,len(c.objects)) for c in bpy.data.collections])
print("hidden",sum(1 for o in sc.objects if o.hide_viewport or o.hide_render))
