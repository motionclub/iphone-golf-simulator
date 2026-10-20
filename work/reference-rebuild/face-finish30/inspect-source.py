import bpy,pathlib,json,numpy as np
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish30';report={}
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/reference-rebuild/face-finish29/smooth-mouth1/{sex}_OriginalFaceFinish29Smooth1.blend'))
 b=bpy.data.objects['Body'];m=b.data;p=np.array([tuple(v.co)for v in m.vertices]);m.calc_loop_triangles();t=np.array([tuple(x.vertices)for x in m.loop_triangles]);head=(p[:,2]>1.42)&(abs(p[:,0])<.14);edges=np.array([tuple(e.vertices)for e in m.edges]);length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);ids=np.flatnonzero(head[edges].all(axis=1));areas=np.linalg.norm(np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]]),axis=1)/2
 blink=np.any(np.array([np.linalg.norm(np.array([tuple(v.co)for v in k.data])-p,axis=1)>1e-7 for k in m.shape_keys.key_blocks if k.name!='Basis']),axis=0)
 report[sex]={'vertices':len(p),'triangles':len(t),'headEdges':len(ids),'headEdgeLengthMmPercentiles':np.percentile(length[ids]*1000,[50,90,95,99,100]).tolist(),'headEdgesOver10mm':int((length[ids]>.010).sum()),'headMinMax':p[head].min(axis=0).tolist()+p[head].max(axis=0).tolist(),'groups':[g.name for g in b.vertex_groups if 'LOOP' in g.name],'blinkActive':int(blink.sum())}
 np.savez_compressed(O/(sex.lower()+'-baseline.npz'),p=p,t=t,edges=edges,blink=blink)
(O/'inspection.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
