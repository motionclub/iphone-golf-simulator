import bpy, numpy as np, sys
argv=sys.argv[sys.argv.index('--')+1:]
b=bpy.data.objects['Body_M']; me=b.data
n=len(me.vertices); V=np.zeros(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
me.calc_loop_triangles(); T=np.zeros(len(me.loop_triangles)*3,dtype=np.int64); me.loop_triangles.foreach_get('vertices',T); T=T.reshape(-1,3)
polys=[tuple(p.vertices) for p in me.polygons]
import pickle
np.savez(argv[0],V=V,T=T); pickle.dump(polys,open(argv[0].replace('.npz','_polys.pkl'),'wb'))
print('dumped',n,len(T),len(polys), 'mw', [list(r) for r in b.matrix_world])
