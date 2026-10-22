import bpy, numpy as np, pickle
bpy.ops.wm.open_mainfile(filepath='baseline/HeroBase_Male_Silhouette.blend')
b=bpy.data.objects['Body_M']; me=b.data
n=len(me.vertices); V=np.empty(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
faces=[list(p.vertices) for p in me.polygons]
np.savez('baseline/mesh.npz',co=V); pickle.dump(faces,open('baseline/faces.pkl','wb'))
print('SNAP verts',n,'polys',len(faces),'tris',sum(len(f)-2 for f in faces),'objs',[o.name for o in bpy.data.objects])
