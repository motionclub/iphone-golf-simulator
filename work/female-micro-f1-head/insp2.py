import bpy, bmesh, json, sys
import numpy as np
o = bpy.data.objects['Body_F']; me = o.data
V = np.empty(len(me.vertices)*3); me.vertices.foreach_get('co', V); V = V.reshape(-1,3)
nl=len(me.loops); cv=np.empty(nl,np.int64); me.loops.foreach_get('vertex_index',cv)
ls=np.empty(len(me.polygons),np.int64); me.polygons.foreach_get('loop_start',ls)
lt=np.empty(len(me.polygons),np.int64); me.polygons.foreach_get('loop_total',lt)
mi=np.empty(len(me.polygons),np.int32); me.polygons.foreach_get('material_index',mi)
F=[cv[a:a+b] for a,b in zip(ls,lt)]
print('face sizes', {int(k):int((lt==k).sum()) for k in np.unique(lt)})
# z histogram of verts with |x|<0.1 between 1.25 and 1.71
z=V[:,2]
for z0 in np.arange(1.25,1.71,0.01):
    m=(z>=z0)&(z<z0+0.01)
    if m.sum():
        sub=V[m]
        print(f'{z0:.2f} n={m.sum():4d} xrange=({sub[:,0].min():+.3f},{sub[:,0].max():+.3f}) yrange=({sub[:,1].min():+.3f},{sub[:,1].max():+.3f})')
# face material by centroid z bands
cen=np.array([V[f].mean(0) for f in F])
for z0 in np.arange(1.30,1.71,0.02):
    m=(cen[:,2]>=z0)&(cen[:,2]<z0+0.02)&(np.abs(cen[:,0])<0.12)
    print(f'{z0:.2f}', {me.materials[int(k)].name:int((mi[m]==k).sum()) for k in np.unique(mi[m])})
# edge length stats in head region
E=np.empty(len(me.edges)*2,np.int64); me.edges.foreach_get('vertices',E); E=E.reshape(-1,2)
el=np.linalg.norm(V[E[:,0]]-V[E[:,1]],axis=1)
hz=(V[E[:,0],2]>1.44)&(V[E[:,1],2]>1.44)
print('head edges',hz.sum(),'mean mm',el[hz].mean()*1000,'min',el[hz].min()*1000,'max',el[hz].max()*1000)
hf=cen[:,2]>1.44
print('head faces',hf.sum(),'head tris',int(sum(len(F[i])-2 for i in np.where(hf)[0])),'head verts',(z>1.44).sum())
print('boundary edges:', sum(1 for e in me.edges if False))
