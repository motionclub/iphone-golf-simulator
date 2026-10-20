"""blender -b HeroBase_Female.blend --python extract.py -- out.npz   (start-state dump of Body_F)"""
import bpy, numpy as np, sys
out=sys.argv[sys.argv.index('--')+1]
o=bpy.data.objects['Body_F']; me=o.data
me.calc_loop_triangles()
n=len(me.vertices)
co=np.empty(n*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
tri=np.empty(len(me.loop_triangles)*3,dtype=np.int32); me.loop_triangles.foreach_get('vertices',tri); tri=tri.reshape(-1,3)
ed=np.empty(len(me.edges)*2,dtype=np.int32); me.edges.foreach_get('vertices',ed); ed=ed.reshape(-1,2)
npoly=len(me.polygons)
ps=np.empty(npoly,dtype=np.int32); me.polygons.foreach_get('loop_start',ps)
pt=np.empty(npoly,dtype=np.int32); me.polygons.foreach_get('loop_total',pt)
lv=np.empty(len(me.loops),dtype=np.int32); me.loops.foreach_get('vertex_index',lv)
mat=np.empty(npoly,dtype=np.int32); me.polygons.foreach_get('material_index',mat)
np.savez_compressed(out,co=co,tri=tri,edges=ed,poly_start=ps,poly_total=pt,loop_vert=lv,poly_mat=mat)
print("dumped",n,"verts",len(tri),"tris")
