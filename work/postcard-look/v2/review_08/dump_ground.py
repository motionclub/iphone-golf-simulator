import bpy, sys, pickle, numpy as np
out=sys.argv[sys.argv.index('--')+1]
G=['TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER','CART_PATH']
d={}
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith(tuple(G)):
        me=o.data; M=np.array(o.matrix_world)
        V=np.array([v.co[:] for v in me.vertices]); V=(np.c_[V,np.ones(len(V))]@M.T)[:,:3]
        faces=[tuple(p.vertices) for p in me.polygons]
        nrm=np.array([p.normal[:] for p in me.polygons]); nrm=nrm@M[:3,:3].T
        mats=[ (me.materials[p.material_index].name if me.materials and p.material_index<len(me.materials) and me.materials[p.material_index] else None) for p in me.polygons]
        d[o.name]=dict(V=V,faces=faces,nrm=nrm,mats=mats)
pickle.dump(d,open(out,'wb'))
print('dumped',list(d))
