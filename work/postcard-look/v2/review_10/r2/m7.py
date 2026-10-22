import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sc=bpy.context.scene
play=[o for o in sc.objects if o.type=='MESH' and o.name.startswith(('FAIRWAY','GREEN','TEE_BOX','BUNKER','GREEN_APRON'))]
bv={o.name:BVHTree.FromPolygons([tuple(o.matrix_world@v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons]) for o in play}
pl=[o for o in sc.objects if o.name.startswith('PLANT_') and not (o.hide_viewport or o.hide_render)]
on=[]
for o in pl:
    p=o.matrix_world.translation
    for n,b in bv.items():
        h=b.ray_cast(Vector((p.x,p.y,80)),Vector((0,0,-1)),200)
        if h[0] is not None: on.append((o.name,n,round(h[0].z-p.z,3)))
print("PLANTS over any play mesh footprint:",len(on),on[:8])
import collections
print(collections.Counter(n for _,n,_ in on))
