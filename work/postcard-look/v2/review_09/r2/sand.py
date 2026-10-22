import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
PFX=('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER')
V=[];F=[]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith(PFX):
        me=o.data;mw=o.matrix_world;b=len(V);V+=[mw@v.co for v in me.vertices];F+=[[b+i for i in p.vertices] for p in me.polygons]
g=BVHTree.FromPolygons(V,F)
for o in bpy.data.objects:
    if o.name.startswith('DRESS_SAND'):
        me=o.data; mw=o.matrix_world; ds=[];nobj=0
        for v in me.vertices:
            p=mw@v.co; h=g.ray_cast(Vector((p.x,p.y,p.z+2)),Vector((0,0,-1)),6)
            if h[0] is None: nobj+=1; continue
            ds.append(p.z-h[0].z)
        ds=np.array(ds); print(o.name,len(me.vertices),'noground',nobj,'dz min %.4f max %.4f'%(ds.min(),ds.max()), 'dz<0.002:',(ds<0.002).sum())
# bunker meshes: top mats
for o in bpy.data.objects:
    if o.name.startswith('BUNKER') : print(o.name,[m.name for m in o.data.materials])
# foam / white objs
print([o.name for o in bpy.data.objects if 'FOAM' in o.name.upper() or 'SURF' in o.name.upper()][:5], sum(1 for o in bpy.data.objects if 'SURF' in o.name.upper()))
print('hidden-but-exported check', [o.name for o in bpy.data.objects if o.hide_viewport and o.type=='MESH'][:5], sum(1 for o in bpy.data.objects if o.hide_viewport))
