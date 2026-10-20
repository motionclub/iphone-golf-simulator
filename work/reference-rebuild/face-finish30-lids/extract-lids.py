import bpy,bmesh,numpy as np,json,collections
from pathlib import Path
R=Path.cwd();O=R/'work/reference-rebuild/face-finish30-lids';report={}
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/reference-rebuild/face-finish29/smooth-mouth1/{sex}_OriginalFaceFinish29Smooth1.blend'));body=bpy.data.objects['Body'];m=body.data;p=np.array([v.co[:] for v in m.vertices]);bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();edges=[]
 for e in bm.edges:
  if e.is_boundary and all(v.co.y<-.05 and 1.5<v.co.z<1.64 for v in e.verts):edges.append([v.index for v in e.verts])
 bm.free();tri=[]
 m.calc_loop_triangles()
 for t in m.loop_triangles:tri.append(t.vertices[:])
 groups={g.name:[v.index for v in m.vertices if any(w.group==g.index and w.weight>.25 for w in v.groups)] for g in body.vertex_groups if 'eye' in g.name.lower() or 'lid' in g.name.lower()}
 shapes={k.name:np.array([v.co[:] for v in k.data]) for k in m.shape_keys.key_blocks};np.savez_compressed(O/f'{sex.lower()}-lids.npz',**shapes,triangles=np.array(tri),edges=np.array(edges),normals=np.array([v.normal[:] for v in m.vertices]));report[sex]={'vertices':len(p),'edges':len(edges),'groups':groups,'shapes':list(shapes)}
(O/'source-lids.json').write_text(json.dumps(report,indent=2)+'\n')
