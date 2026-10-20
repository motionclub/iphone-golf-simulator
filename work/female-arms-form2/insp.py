import bpy, numpy as np
o=bpy.data.objects['Body_F']; me=o.data
print([ (ob.name,ob.type,len(ob.data.vertices) if ob.type=='MESH' else 0) for ob in bpy.data.objects])
n=len(me.vertices); co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
print(n, co.min(0), co.max(0))
# arm verts: |x|>0.15
for sgn,name in((1,'+x'),(-1,'-x')):
    m=(co[:,0]*sgn>0.14)&(co[:,2]>0.82)&(co[:,2]<1.5)
    print(name,m.sum())
    for z in np.arange(0.85,1.5,0.05):
        mm=m&(abs(co[:,2]-z)<0.0125)
        if mm.sum(): 
            p=co[mm]; print(f"z{z:.2f} n{mm.sum()} x[{p[:,0].min()*sgn:.3f},{p[:,0].max()*sgn:.3f}] y[{p[:,1].min():.3f},{p[:,1].max():.3f}]")
