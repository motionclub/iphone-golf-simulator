import bpy,pathlib,numpy as np,json
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish30/forehead-check'
for case,path in [('broad',R/'work/reference-rebuild/face-finish30/Female_OriginalFaceFinish30.blend'),('ears',R/'work/reference-rebuild/face-finish30/ears/Female_OriginalFaceFinish30Ears.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));m=bpy.data.objects['Body'].data;p=np.array([v.co[:]for v in m.vertices]);m.calc_loop_triangles();tri=np.array([t.vertices[:]for t in m.loop_triangles]);normal=np.zeros_like(p);cn=np.array([n.vector[:]for n in m.corner_normals]);
 for li,l in enumerate(m.loops):normal[l.vertex_index]+=cn[li]
 normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-15);np.savez_compressed(O/(case+'.npz'),p=p,t=tri,n=normal)
print('FOREHEAD EXTRACT COMPLETE')
