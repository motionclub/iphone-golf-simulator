import bpy, numpy as np, sys
o=bpy.data.objects['Body_F']; me=o.data
n=len(me.vertices); co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
ne=len(me.edges); ed=np.empty(ne*2,np.int32); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
nf=len(me.polygons); lv=np.empty(len(me.loops),np.int32); me.loops.foreach_get('vertex_index',lv)
ls=np.empty(nf,np.int32); me.polygons.foreach_get('loop_start',ls); lt=np.empty(nf,np.int32); me.polygons.foreach_get('loop_total',lt)
np.savez(sys.argv[sys.argv.index('--')+1],co=co,edges=ed,loop_v=lv,loop_start=ls,loop_total=lt)
print(n,ne,nf, set(lt.tolist()))
