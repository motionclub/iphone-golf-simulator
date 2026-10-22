import bpy,numpy as np,json,hashlib,shutil
from pathlib import Path
W=Path(__file__).resolve().parent;R=W.parents[1];D=R/'ArtDir/hero/base_lock';P=D/'proof'
source=D/'blender/HeroBase_Male_Silhouette.blend';dest=W/'baseline/HeroBase_Male_Silhouette.blend'
assert not dest.exists()
shutil.copy2(source,dest)
bpy.ops.wm.open_mainfile(filepath=str(source));o=bpy.data.objects['Body_M'];m=o.data;m.calc_loop_triangles()
co=np.array([tuple(v.co) for v in m.vertices]);edges=np.array([tuple(e.vertices) for e in m.edges]);tri=np.array([tuple(t.vertices) for t in m.loop_triangles])
np.savez(W/'baseline/mesh.npz',co=co,edges=edges,tri=tri)
matrix=lambda o:list(sum((list(row) for row in o.matrix_world),[]))
inv={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'connectivity_sha256':hashlib.sha256(json.dumps([list(f.vertices) for f in m.polygons],separators=(',',':')).encode()).hexdigest(),'body_matrix':matrix(o),'nonbody_matrix':{p.name:matrix(p) for p in bpy.data.objects if p.type!='MESH'},'cameras':{p.name:{'scale':p.data.ortho_scale,'props':dict(p.items())} for p in bpy.data.objects if p.type=='CAMERA'}}
(W/'baseline/invariants.json').write_text(json.dumps(inv,indent=2))
for n in ['MALE_FORM_RESULTS.md','MALE_SIL_RESULTS.md','MALE_FORM_D_COMPLETION_AUDIT.md','male-form-d-eye-checks.json']:
 shutil.copy2(P/n,W/'baseline'/('prior-'+n))
for name in ['front','front_left','left','back_left','back','back_right','right','front_right','top']:
 shutil.copy2(P/'male_form_d/head_all_around'/(name+'.png'),W/'baseline'/('head_'+name+'.png'))
print('JAW_STAGE_BASELINE',json.dumps(inv))
