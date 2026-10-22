import bpy,bmesh,numpy as np
from pathlib import Path
w=Path(__file__).resolve().parents[1];o=bpy.data.objects['Golf_Trousers'];o.data.calc_loop_triangles();n=len(o.data.vertices)//2
prior={tuple(sorted(t.vertices)) for t in o.data.loop_triangles if not all(i>=n for i in t.vertices)}
for method in ['BEAUTY','FIXED','FIXED_ALTERNATE','SHORTEST_DIAGONAL','LONGEST_DIAGONAL']:
 bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method=method);now={tuple(sorted(v.index for v in f.verts)) for f in bm.faces if not all(v.index>=n for v in f.verts)}
 delta=prior-now;groin=[t for t in delta if .65<sum(o.data.vertices[i].co.z for i in t)/3<.9 and abs(sum(o.data.vertices[i].co.x for i in t)/3)<.16];print(method,'triDifference',len(delta),'groin',len(groin),flush=True);bm.free()
