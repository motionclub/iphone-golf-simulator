import bpy, sys, collections, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def wv(o):
    M=np.array(o.matrix_world); V=np.array([v.co[:] for v in o.data.vertices]).reshape(-1,3); return (np.c_[V,np.ones(len(V))]@M.T)[:,:3]
solid=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('TERRAIN','ROCK_','DRESS_ARCH','DRESS_BLOCK','FAIRWAY','GREEN','TEE_BOX','BUNKER')) and not o.hide_viewport]
vs=[];fs=[];off=0
for o in solid:
    V=wv(o); vs+=V.tolist(); fs+=[[i+off for i in p.vertices] for p in o.data.polygons]; off+=len(V)
bvh=BVHTree.FromPolygons(vs,fs)
ds=[];far=[]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith('PLANT_VINE'):
        t=o.matrix_world.translation
        if abs(t.x)<1e-6 and abs(t.y)<1e-6: continue
        V=wv(o); top=V[V[:,2].argmax()]
        r=bvh.find_nearest(Vector(top)); d=r[3] if r[0] is not None else 99
        ds.append(d)
        if d>0.5: far.append((o.name,round(d,2)))
ds=np.array(ds); print('vines',len(ds),'top-vertex distance to nearest solid: median %.3f p95 %.3f max %.3f'%(np.median(ds),np.percentile(ds,95),ds.max()),'far>0.5m',len(far),far[:6])
