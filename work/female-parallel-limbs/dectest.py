import bpy, numpy as np, time
d=np.load('data/foot_R_raw.npz'); V,F=d['V'],d['F']
print('raw verts',len(V),'faces',len(F),'z hist',np.histogram(V[:,2],bins=[0,0.04,0.08,0.12,0.157,0.2,0.22])[0])
e=np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),1); u,c=np.unique(e,axis=0,return_counts=True); print('edge counts',np.bincount(c))
bpy.ops.wm.read_factory_settings(use_empty=True)
for ratio in (0.5,0.1,0.02,0.005):
    m=bpy.data.meshes.new('raw'); m.from_pydata(V.tolist(),[],F.tolist()); m.update()
    ob=bpy.data.objects.new('raw',m); bpy.context.scene.collection.objects.link(ob)
    mod=ob.modifiers.new('d','DECIMATE'); mod.decimate_type='COLLAPSE'; mod.ratio=ratio
    dg=bpy.context.evaluated_depsgraph_get(); ev=ob.evaluated_get(dg); m2=bpy.data.meshes.new_from_object(ev)
    zs=np.array([v.co.z for v in m2.vertices])
    print(ratio,'->',len(m2.polygons),'faces; verts',len(m2.vertices),'z hist',np.histogram(zs,bins=[0,0.04,0.08,0.12,0.157,0.2,0.22])[0])
