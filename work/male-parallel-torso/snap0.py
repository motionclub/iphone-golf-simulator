import bpy, numpy as np, pickle
bpy.ops.wm.open_mainfile(filepath='baseline/HeroBase_Male_Silhouette.blend')
for o in bpy.data.objects: print(o.name,o.type,[round(x,3) for x in o.location],o.hide_render)
b=bpy.data.objects['Body_M']; me=b.data
n=len(me.vertices); V=np.empty(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
faces=[list(p.vertices) for p in me.polygons]
np.savez('baseline/mesh.npz',co=V); pickle.dump(faces,open('baseline/faces.pkl','wb'))
print('verts',n,'polys',len(faces),'tris',sum(len(f)-2 for f in faces))
print('vgroups',len(b.vertex_groups),[g.name for g in b.vertex_groups][:60])
print('bounds',V.min(0),V.max(0)); print('mats',[m.name for m in me.materials], 'mods',[m.type for m in b.modifiers])
print('parent',b.parent, 'rot',b.rotation_euler[:],'scale',b.scale[:])
