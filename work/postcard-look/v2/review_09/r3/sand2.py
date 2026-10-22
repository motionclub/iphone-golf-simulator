import bpy, numpy as np, random
from mathutils import Vector
from mathutils.bvhtree import BVHTree
PFX=('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER')
V=[];F=[]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith(PFX):
        me=o.data;b=len(V);V+=[o.matrix_world@v.co for v in me.vertices];F+=[[b+i for i in p.vertices] for p in me.polygons]
g=BVHTree.FromPolygons(V,F)
random.seed(1)
for o in bpy.data.objects:
    if not o.name.startswith('DRESS_SAND'): continue
    me=o.data; me.calc_loop_triangles(); mw=o.matrix_world
    ds=[]
    for t in me.loop_triangles:
        P=[mw@me.vertices[i].co for i in t.vertices]
        for k in range(40):
            a,b=random.random(),random.random()
            if a+b>1:a,b=1-a,1-b
            p=P[0]+(P[1]-P[0])*a+(P[2]-P[0])*b
            h=g.ray_cast(Vector((p.x,p.y,p.z+2)),Vector((0,0,-1)),6)
            if h[0] is None: continue
            ds.append(p.z-h[0].z)
    ds=np.array(ds); print(o.name,len(ds),'dz min %.4f max %.4f'%(ds.min(),ds.max()),'below ground',(ds<0).sum(),'<3mm',(ds<0.003).sum())
